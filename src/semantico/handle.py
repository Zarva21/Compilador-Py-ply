import json, os, tempfile
from datetime import datetime


def _save_iteration_state(self):
    temp_dir = tempfile.gettempdir()
    path = os.path.join(temp_dir, "tabla_simbolos_iteracion_historial.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            historial = json.load(f)
    else:
        historial = []

    global_serializado = {
        str(k): v["value"] for k, v in self.symbol_table.global_scope.items()
    }
    local_serializado = []
    for scope in self.symbol_table.scope_stack:
        scope_dict = {}
        for k, v in scope.items():
            scope_dict[str(k)] = {
                "type":  v["type"],
                "scope": v["scope"],
                "value": v["value"],
            }
        local_serializado.append(scope_dict)

    historial.append({
        "timestamp": datetime.now().isoformat(),
        "iteration": len(historial) + 1,
        "tabla": {"global": global_serializado, "local_scopes": local_serializado},
    })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4)


# ─────────────────────────────────────────────────────────────────────────────
# _resolve_ir
#
# Convierte cualquier valor diferido a su nombre en el IR.
# Es el único punto donde se emiten instrucciones para expresiones.
#
#   str          → nombre de variable o literal (se usa tal cual)
#   int/float    → literal numérico como string
#   bool         → "true" / "false"
#   tuple(l,o,r) → emite "tN = l o r" y devuelve "tN"
#   callable     → lo ejecuta (method_call diferido) y devuelve el temporal
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_ir(self, val):
    if isinstance(val, tuple) and len(val) == 3:
        l, op, r = val
        lv = _resolve_ir(self, l)
        rv = _resolve_ir(self, r)
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {lv} {op} {rv}")
        return temp
    elif callable(val):
        result = val()
        return str(result) if result is not None else '?'
    elif isinstance(val, bool):
        return 'true' if val else 'false'
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, str):
        # Distinguir variable de literal string:
        #   - existe en tabla → variable → usar tal cual
        #   - no existe       → literal  → envolver con comillas
        # get_symbol no imprime error (ver symboltable.py)
        if val in ('true', 'false'):
            return val
        if val.startswith('"') or (val.startswith("'") and val.endswith("'")):
            return val      # ya tiene comillas, no doble-envolver
        if self.symbol_table.get_symbol(val) is not None:
            return val      # es nombre de variable declarada
        return f'"{val}"'   # es string literal sin comillas
    else:
        return str(val)


# ─────────────────────────────────────────────────────────────────────────────
# _apply_operator  (solo para errores semánticos estáticos, no runtime)
# ─────────────────────────────────────────────────────────────────────────────
def _apply_operator(self, a, op, b):
    try:
        if a is None or b is None:
            return None
        if op == '+': return a + b if type(a) == type(b) else None
        if op == '-': return a - b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
        if op == '*': return a * b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
        if op == '/':
            if b == 0:
                self.errors.encolar_error("Error semántico: división por cero.")
                return None
            return a / b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
    except Exception:
        pass
    return None


def _get_value(self, item):
    if isinstance(item, str):
        symbol = self.symbol_table.get_symbol(item)
        if symbol is None:
            return item
        return symbol['value']
    return item


# ─────────────────────────────────────────────────────────────────────────────
# handle_declaration
#
# Responsabilidades:
#   1. Registrar la variable en la tabla (tipo + scope, valor = None)
#   2. Emitir IR de inicialización si hay valor
#
# NO evalúa el valor runtime — eso es trabajo del programa compilado.
# ─────────────────────────────────────────────────────────────────────────────
def handle_declaration(self, name, var_type, scope=None, value=None):
    def action():
        actual_scope = 'local' if self.en_funcion else 'global'

        # Verificar redeclaración en scope actual
        current = self.symbol_table.current_scope()
        if current is not None and name in current:
            existing_type = current[name].get('type', '?')
            msg = (
                f"Error semántico: variable '{name}' ya declarada como "
                f"'{existing_type}' en este bloque."
                if existing_type != var_type
                else f"Error semántico: variable '{name}' ya declarada. ¿Quisiste asignar?"
            )
            self.errors.encolar_error(msg)
            return

        # Registrar en tabla — valor None (el valor lo calcula el programa en runtime)
        self.symbol_table.add_symbol(name, var_type, actual_scope, None)

        # Emitir IR de inicialización
        if value is not None:
            if isinstance(value, tuple) and len(value) == 3:
                ir_val = _resolve_ir(self, value)
                self.intercode_generator.emit(f"{name} = {ir_val}")
            elif callable(value):
                result = value()
                if result is not None:
                    self.intercode_generator.emit(f"{name} = {result}")
            else:
                ir_value = value
                if var_type.lower() == 'charizar' and isinstance(value, str):
                    if not (value.startswith("'") and value.endswith("'")):
                        ir_value = f"'{value}'"
                self.intercode_generator.emit(f"{name} = {ir_value}")

    return action


# ─────────────────────────────────────────────────────────────────────────────
# handle_assignment
#
# Solo emite IR. No actualiza tabla — el valor runtime no es tarea del compilador.
# ─────────────────────────────────────────────────────────────────────────────
def handle_assignment(self, name, value):
    def action():
        # Verificar que la variable existe
        sym = self.symbol_table.get_symbol(name)
        if sym is None:
            self.errors.encolar_error(f"Error semántico: variable '{name}' no declarada.")
            return

        # Emitir IR
        if isinstance(value, tuple) and len(value) == 3:
            ir_val = _resolve_ir(self, value)
            self.intercode_generator.emit(f"{name} = {ir_val}")
        elif callable(value):
            result = value()
            if result is not None:
                self.intercode_generator.emit(f"{name} = {result}")
        else:
            self.intercode_generator.emit(f"{name} = {value}")

    return action


# ─────────────────────────────────────────────────────────────────────────────
# handle_print
# ─────────────────────────────────────────────────────────────────────────────
def handle_print(self, value):
    def action():
        ir_val = _resolve_ir(self, value)
        self.intercode_generator.emit(f"cout << {ir_val} << endl")
    return action


# ─────────────────────────────────────────────────────────────────────────────
# evaluate_condition_dynamic
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_condition_dynamic(self, left, op, right):
    def condition_fn():
        left_val  = _resolve_ir(self, left)
        right_val = _resolve_ir(self, right)
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {left_val} {op} {right_val}")
        condition_fn.temp_result = temp
        return True

    condition_fn.temp_result = "t_cond"
    return condition_fn


# ─────────────────────────────────────────────────────────────────────────────
# handle_expression  (delegación desde semantic.py)
# ─────────────────────────────────────────────────────────────────────────────
def handle_expression(self, left, operator, right):
    def action():
        lv   = _resolve_ir(self, left)
        rv   = _resolve_ir(self, right)
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {lv} {operator} {rv}")
        return temp
    return action


# ─────────────────────────────────────────────────────────────────────────────
# Estructuras de control
# ─────────────────────────────────────────────────────────────────────────────
def handle_if(self, condition_fn, if_body, else_body):
    def action():
        false_label = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()

        self.intercode_generator.emit("// INICIO IF")
        condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if !({cond_temp}) goto {false_label}")

        self.symbol_table.enter_scope()
        for stmt in if_body:
            if callable(stmt): stmt()
        self.symbol_table.exit_scope()
        self.intercode_generator.emit(f"goto {end_label}")

        self.intercode_generator.emit(f"{false_label}:")
        if else_body:
            self.intercode_generator.emit("// ELSE")
            self.symbol_table.enter_scope()
            for stmt in else_body:
                if callable(stmt): stmt()
            self.symbol_table.exit_scope()

        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN IF")

    return action


def handle_while(self, condition_fn, body):
    def action():
        start_label = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()

        self.intercode_generator.emit("// INICIO WHILE")
        self.intercode_generator.emit(f"{start_label}:")
        condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if !({cond_temp}) goto {end_label}")

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt): stmt()
        self.symbol_table.exit_scope()

        self.intercode_generator.emit(f"goto {start_label}")
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN WHILE")

    return action


def handle_for(self, init_stmt, condition_fn, update_stmt, body):
    def action():
        start_label = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()

        if callable(init_stmt): init_stmt()

        self.intercode_generator.emit("// INICIO FOR")
        self.intercode_generator.emit(f"{start_label}:")
        condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if !({cond_temp}) goto {end_label}")

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt): stmt()
        self.symbol_table.exit_scope()

        if callable(update_stmt): update_stmt()

        self.intercode_generator.emit(f"goto {start_label}")
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN FOR")

    return action


def handle_do_while(self, condition_fn, body):
    def action():
        start_label = self.intercode_generator.new_label()

        self.intercode_generator.emit("//INICIO DO-WHILE")
        self.intercode_generator.emit(f"{start_label}:")

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt): stmt()
        self.symbol_table.exit_scope()

        condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if ({cond_temp}) goto {start_label}")
        self.intercode_generator.emit("//FIN DO-WHILE")

    return action


# ─────────────────────────────────────────────────────────────────────────────
# handle_method_call
#
# Diferido: NO emite IR durante el parse.
# Se ejecuta cuando el callable padre lo invoca en tiempo de ejecución del AST.
# Esto garantiza:
#   - Todas las funciones ya registradas (recursión OK)
#   - IR en orden correcto
#   - Argumentos resueltos en el momento correcto
# ─────────────────────────────────────────────────────────────────────────────
def handle_method_call(self, name, args=None):
    args = args or []
    print(f" [CALL] Preparando llamada a función '{name}' con argumentos: {args}")
    def call_with_scope():
        if name not in self.methods:
            self.errors.encolar_error(f"Error semántico: función '{name}' no definida.")
            return None

        temp = self.intercode_generator.new_temp()

        arg_ir_names = []
        for arg in args:
            ir_name = _resolve_ir(self, arg)
            arg_ir_names.append(ir_name)

        for arg_name in arg_ir_names:
            self.intercode_generator.emit(f"param {arg_name}")

        args_str = ', '.join(arg_ir_names)
        # quitar esto
        print(f" [CALL] Llamada a función '{name}' con argumentos IR resueltos: {args_str}")
        self.intercode_generator.emit(f"{temp} = call {name}({args_str})")

        return temp

    return call_with_scope


# ─────────────────────────────────────────────────────────────────────────────
# handle_method_declaration
# ─────────────────────────────────────────────────────────────────────────────
def handle_method_declaration(self, name, body):
    def flatten(stmts):
        flat = []
        for s in stmts:
            flat.extend(flatten(s)) if isinstance(s, list) else flat.append(s)
        return flat

    def action():
        flat_body = flatten(body)
        if name in self.methods and isinstance(self.methods[name], dict):
            self.methods[name]['body'] = flat_body

        method_info = self.methods.get(name, {})
        ret_type = method_info.get('return_type', 'gardevoir') if isinstance(method_info, dict) else 'gardevoir'
        params   = method_info.get('params', [])               if isinstance(method_info, dict) else []

        params_str = ', '.join(f"{t} {n}" for t, n in params)
        self.intercode_generator.emit(f"function {ret_type}  {name}({params_str}):")

        self.symbol_table.enter_scope()
        # quitar esto
        print(f" [FUNC]  Función '{name}' registrada con return_type='{ret_type}' y params={params}")
        self.en_funcion = True

        for param_type, param_name in params:
            self.symbol_table.add_symbol(param_name, param_type, 'local', None)
            # quitar esto
            print(f" [PARAM]  Variable '{param_name}' ({param_type}) registrada")

        for stmt in flat_body:
            if callable(stmt): stmt()

        self.en_funcion = False
        self.symbol_table.exit_scope()
        # quitar esto
        print(f" [END FUNC] Fin de función '{name}'")
        self.intercode_generator.emit("end")

    return action


# ─────────────────────────────────────────────────────────────────────────────
# handle_switch
# ─────────────────────────────────────────────────────────────────────────────
def handle_switch(self, var_name, cases, default_body):
    def action():
        processed_cases = []
        for idx, case in enumerate(cases):
            if not isinstance(case, tuple) or len(case) != 2:
                self.errors.encolar_error(f"Error: case #{idx} inválido.")
                return
            val, case_body = case
            try:
                hash(val)
            except TypeError:
                self.errors.encolar_error(f"Error: valor case #{idx} no hashable.")
                return
            processed_cases.append(
                (val, case_body if isinstance(case_body, list) else [case_body])
            )

        self.intercode_generator.emit(f"// SWITCH_START {var_name}")
        for val, case_body in processed_cases:
            self.intercode_generator.emit(f"// CASE {repr(val)}")
            for stmt in case_body:
                if callable(stmt): stmt()
            self.intercode_generator.emit("// BREAK")

        self.intercode_generator.emit("// DEFAULT")
        if default_body:
            for stmt in default_body:
                if callable(stmt): stmt()
        self.intercode_generator.emit("// SWITCH_END")

    return action