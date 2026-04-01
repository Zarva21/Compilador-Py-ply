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
            scope_dict[str(k)] = {"type": v["type"], "scope": v["scope"], "value": v["value"]}
        local_serializado.append(scope_dict)

    historial.append({
        "timestamp": datetime.now().isoformat(),
        "iteration": len(historial) + 1,
        "tabla": {"global": global_serializado, "local_scopes": local_serializado},
    })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4)


def _apply_operator(self, a, op, b):
    try:
        if a is None or b is None:
            self.errors.encolar_error(f"Error: Operación inválida entre {a} y {b}")
            return None
        if op == '+': return a + b if type(a) == type(b) else self._op_error(op, a, b)
        if op == '-': return a - b if self._check_numeric(a, b) else self._op_error(op, a, b)
        if op == '*': return a * b if self._check_numeric(a, b) else self._op_error(op, a, b)
        if op == '/':
            if b == 0:
                self.errors.encolar_error("Error: División por cero.")
                return None
            return a / b if self._check_numeric(a, b) else self._op_error(op, a, b)
    except Exception as e:
        self.errors.encolar_error(f"Error en operación: {e}")
    self.errors.encolar_error(f"Operador no válido: {op}")
    return None


def _get_value(self, item):
    if isinstance(item, str):
        symbol = self.symbol_table.get_symbol(item)
        if symbol is None:
            return item
        return symbol['value']
    return item


def handle_assignment(self, name, value):
    def action():
        if isinstance(value, tuple) and len(value) == 3:
            left, op, right = value
            temp = self.intercode_generator.new_temp()
            self.intercode_generator.emit(f"{temp} = {left} {op} {right}")
            self.intercode_generator.emit(f"{name} = {temp}")
        elif callable(value):
            result = value()
            if result:
                self.intercode_generator.emit(f"{name} = {result}")
        else:
            self.intercode_generator.emit(f"{name} = {value}")

        sym = self.symbol_table.get_symbol(name)
        if sym is None:
            self.errors.encolar_error(f"Error: Variable '{name}' no declarada.")
            return

        def evaluar(val):
            if isinstance(val, tuple) and len(val) == 3:
                l, op, r = val
                lv = evaluar(l)
                rv = evaluar(r)
                return self._apply_operator(lv, op, rv) if lv is not None and rv is not None else None
            elif callable(val):
                return None
            elif isinstance(val, str):
                s = self.symbol_table.get_symbol(val)
                return s['value'] if s else None
            return val

        real_val = evaluar(value)
        if real_val is not None:
            self.symbol_table.update_symbol(name, real_val)

    return action


def handle_declaration(self, name, var_type, scope=None, value=None):
    def action():
        # ── Determinar scope real ──────────────────────────────────────────
        # La única fuente de verdad confiable es self.en_funcion.
        # scope_stack siempre tiene al menos 1 elemento (el raíz),
        # así que len(scope_stack) > 1 NO distingue global de local — siempre
        # es True después del enter_scope() inicial del parser.
        #
        # Regla:
        #   en_funcion = True  → dentro de una función declarada → local
        #   en_funcion = False → nivel raíz del programa          → global
        actual_scope = 'local' if self.en_funcion else 'global'

        # ── Verificar redeclaración en el scope actual ──
        current = self.symbol_table.current_scope()
        if current is not None and name in current:
            existing_type = current[name].get('type', '?')
            msg = (
                f"Error semántico: variable '{name}' ya declarada como '{existing_type}' en este bloque."
                if existing_type != var_type
                else f"Error semántico: variable '{name}' ya declarada. ¿Quisiste asignar?"
            )
            self.errors.encolar_error(msg)
            return

        # También verificar en global_scope si estamos en global
        if actual_scope == 'global' and name in self.symbol_table.global_scope:
            self.errors.encolar_error(
                f"Error semántico: variable global '{name}' ya declarada."
            )
            return

        # ── Evaluar valor literal para la tabla ──
        def evaluar(val):
            if isinstance(val, (int, float, bool, str)):
                return val
            elif isinstance(val, tuple) and len(val) == 3:
                l, op, r = val
                lv = evaluar(l)
                rv = evaluar(r)
                return self._apply_operator(lv, op, rv) if lv is not None and rv is not None else None
            elif callable(val):
                return None
            return None

        evaluated_value = evaluar(value)
        self.symbol_table.add_symbol(name, var_type, actual_scope, evaluated_value)

        # ── Generar IR ──
        if value is not None:
            if isinstance(value, tuple) and len(value) == 3:
                l, op, r = value
                temp = self.intercode_generator.new_temp()
                self.intercode_generator.emit(f"{temp} = {l} {op} {r}")
                self.intercode_generator.emit(f"{name} = {temp}")
            elif callable(value):
                result = value()
                if result:
                    self.intercode_generator.emit(f"{name} = {result}")
            else:
                ir_value = value
                # FIX char literal: envolver con comillas simples
                if var_type.lower() == 'charizar' and isinstance(value, str):
                    if not (value.startswith("'") and value.endswith("'")):
                        ir_value = f"'{value}'"
                self.intercode_generator.emit(f"{name} = {ir_value}")

    return action


def handle_print(self, value):
    def action():
        if isinstance(value, tuple) and len(value) == 3:
            l, op, r = value
            temp = self.intercode_generator.new_temp()
            self.intercode_generator.emit(f"{temp} = {l} {op} {r}")
            self.intercode_generator.emit(f"cout << {temp} << endl")
        else:
            self.intercode_generator.emit(f"cout << {value} << endl")
    return action


def evaluate_condition_dynamic(self, left, op, right):
    """
    Acepta cualquier expresión en ambos lados — no solo IDENTIFIER.
    left/right pueden ser str o tuple (expr aritmética).
    """
    def condition_fn():
        def resolve(val):
            if isinstance(val, tuple) and len(val) == 3:
                l, o, r = val
                lv = resolve(l)
                rv = resolve(r)
                temp = self.intercode_generator.new_temp()
                self.intercode_generator.emit(f"{temp} = {lv} {o} {rv}")
                return temp
            return val

        left_val  = resolve(left)
        right_val = resolve(right)
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {left_val} {op} {right_val}")
        condition_fn.temp_result = temp
        return True

    condition_fn.temp_result = "t_cond"
    return condition_fn


def handle_expression(self, left, operator, right):
    def action():
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {left} {operator} {right}")
        return temp
    return action


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


def handle_method_call(self, name, args=None):
    args = args or []

    if name not in self.methods:
        self.errors.encolar_error(f"Error: Método '{name}' no está definido.")
        return None

    temp = self.intercode_generator.new_temp()

    arg_ir_names = []

    for arg in args:
        if callable(arg):
            arg = arg()

        if isinstance(arg, tuple):
            l, op, r = arg
            t = self.intercode_generator.new_temp()
            self.intercode_generator.emit(f"{t} = {l} {op} {r}")
            arg_ir_names.append(t)
        else:
            arg_ir_names.append(str(arg))

    for arg_name in arg_ir_names:
        self.intercode_generator.emit(f"param {arg_name}")

    args_str = ', '.join(arg_ir_names)
    self.intercode_generator.emit(f"{temp} = call {name}({args_str})")

    return temp


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
        ret_type    = method_info.get('return_type', 'gardevoir') if isinstance(method_info, dict) else 'gardevoir'
        params      = method_info.get('params', []) if isinstance(method_info, dict) else []

        params_str = ', '.join(f"{t} {n}" for t, n in params)
        self.intercode_generator.emit(f"function {ret_type} {name}({params_str}):")

        self.symbol_table.enter_scope()
        self.en_funcion = True

        for param_type, param_name in params:
            self.symbol_table.add_symbol(param_name, param_type, 'local', None)

        for stmt in flat_body:
            if callable(stmt): stmt()

        self.en_funcion = False
        self.symbol_table.exit_scope()
        self.intercode_generator.emit("end")

    return action


def handle_switch(self, var_name, cases, default_body):
    def action():
        processed_cases = []
        for idx, case in enumerate(cases):
            if not isinstance(case, tuple) or len(case) != 2:
                self.errors.encolar_error(f"Error: case #{idx} inválido.")
                return
            val, case_body = case
            try: hash(val)
            except TypeError:
                self.errors.encolar_error(f"Error: valor case #{idx} no hashable.")
                return
            processed_cases.append((val, case_body if isinstance(case_body, list) else [case_body]))

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