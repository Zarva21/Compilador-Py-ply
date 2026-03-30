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
                "type": v["type"],
                "scope": v["scope"],
                "value": v["value"]
            }
        local_serializado.append(scope_dict)

    historial.append({
        "timestamp": datetime.now().isoformat(),
        "iteration": len(historial) + 1,
        "tabla": {
            "global": global_serializado,
            "local_scopes": local_serializado
        }
    })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4)


def _apply_operator(self, a, op, b):
    try:
        if a is None or b is None:
            self.errors.encolar_error(f"Error: Operación inválida entre {a} y {b}")
            return None
        if op == '+':
            return a + b if type(a) == type(b) else self._op_error(op, a, b)
        if op == '-':
            return a - b if self._check_numeric(a, b) else self._op_error(op, a, b)
        if op == '*':
            return a * b if self._check_numeric(a, b) else self._op_error(op, a, b)
        if op == '/':
            if b == 0:
                self.errors.encolar_error("Error: División por cero.")
                return None
            return a / b if self._check_numeric(a, b) else self._op_error(op, a, b)
    except Exception as e:
        self.errors.encolar_error(f"Error en operación: {e}")
    self.errors.encolar_error(f"Operador no válido: {op}")
    return None


def handle_assignment(self, name, value):
    def action():
        print(f"Recibido en asignación para '{name}': {value}")
        try:
            def evaluar_exp(val):
                if isinstance(val, tuple) and len(val) == 3:
                    left, op, right = val
                    left_val  = evaluar_exp(left)
                    right_val = evaluar_exp(right)
                    if left_val is None or right_val is None:
                        self.errors.encolar_error(
                            f"Error: No se puede operar porque '{left}' o '{right}' es None."
                        )
                        return None
                    result = self._apply_operator(left_val, op, right_val)
                    print(f"Evaluación: {left_val} {op} {right_val} = {result}")
                    return result
                elif callable(val):
                    return val()
                else:
                    return self._get_value(val)

            value_eval = evaluar_exp(value)

            if value_eval is None:
                self.errors.encolar_error(f"Error: Asignación a '{name}' fallida por valor inválido.")
                return

            # Generar código intermedio
            if isinstance(value, tuple) and len(value) == 3:
                left, op, right = value
                temp = self.intercode_generator.new_temp()
                self.intercode_generator.emit(f"{temp} = {left} {op} {right}")
                self.intercode_generator.emit(f"{name} = {temp}")
            else:
                self.intercode_generator.emit(f"{name} = {value}")

            # Asignar en tabla de símbolos
            if self.symbol_table.get_symbol(name) is not None:
                self.symbol_table.update_symbol(name, value_eval)
                print(f"Asignación: {name} = {value_eval}")
            else:
                self.errors.encolar_error(f"Error: Variable '{name}' no declarada.")

        except Exception as e:
            self.errors.encolar_error(f"Error al asignar a '{name}': {e}")
            print(f"Error general al asignar a '{name}': {e}")

    return action


def handle_declaration(self, name, var_type, scope=None, value=None):
    def action():
        actual_scope = 'local' if self.en_funcion else 'global'

        # ── Verificar redeclaración SOLO en scope actual ──
        current = self.symbol_table.current_scope()

        if current is not None and name in current:
            existing_type = current[name].get('type', '?')
            if existing_type != var_type:
                self.errors.encolar_error(
                    f"Error semántico: variable '{name}' ya fue declarada como "
                    f"'{existing_type}' en este bloque."
                )
            else:
                self.errors.encolar_error(
                    f"Error semántico: variable '{name}' ya fue declarada en este bloque. "
                    f"¿Quisiste hacer una asignación?"
                )
            return

        # ── Evaluar valor inicial ──
        if isinstance(value, (int, float, bool, str)):
            evaluated_value = value
        elif isinstance(value, tuple) and len(value) == 3:
            left, op, right = value
            temp = self.intercode_generator.new_temp()
            self.intercode_generator.emit(f"{temp} = {left} {op} {right}")
            evaluated_value = temp
        else:
            evaluated_value = self._get_value(value)

        # Guardar en tabla
        self.symbol_table.add_symbol(name, var_type, actual_scope, evaluated_value)

        if evaluated_value is not None:
            self.intercode_generator.emit(f"{name} = {evaluated_value}")

    return action


def handle_print(self, value):
    def action():
        if isinstance(value, str):
            self.intercode_generator.emit(f"cout << {value} << endl")
        else:
            self.intercode_generator.emit(f"cout << {value} << endl")
    return action


def handle_do_while(self, condition_fn, body):
    def action():
        print("Iniciando ciclo DO-WHILE")

        start_label = self.intercode_generator.new_label()
        self.intercode_generator.emit("//INICIO DO-WHILE")
        self.intercode_generator.emit(f"{start_label}:")

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt):
                stmt()
        self.symbol_table.exit_scope()
        self._save_iteration_state()

        condition_result = condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if ({cond_temp}) goto {start_label}")
        self.intercode_generator.emit("//FIN DO-WHILE")

    return action


def evaluate_condition_dynamic(self, left, op, right):
    def condition_fn():
        left_sym = self.symbol_table.get_symbol(left)
        if left_sym is None:
            self.errors.encolar_error(f"Error: Variable '{left}' no declarada en la condición.")
            condition_fn.temp_result = "0"
            return False

        left_val  = left_sym['value']
        right_val = self._get_value(right)

        if left_val is None or right_val is None:
            self.errors.encolar_error("Error: condición con operandos no evaluables.")
            condition_fn.temp_result = "0"
            return False

        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {left} {op} {right}")
        condition_fn.temp_result = temp

        try:
            if op == '>':  return left_val > right_val
            if op == '<':  return left_val < right_val
            if op == '==': return left_val == right_val
            if op == '!=': return left_val != right_val
            if op == '>=': return left_val >= right_val
            if op == '<=': return left_val <= right_val
            self.errors.encolar_error(f"Operador relacional no soportado: {op}")
            return False
        except Exception as e:
            self.errors.encolar_error(f"Error en evaluación de condición: {e}")
            return False

    return condition_fn


def handle_expression(self, left, operator, right):
    def action():
        val1 = left  if isinstance(left,  (int, float, str)) else self._get_value(left)
        val2 = right if isinstance(right, (int, float, str)) else self._get_value(right)

        if val1 is None or val2 is None:
            self.errors.encolar_error(f"Error: Operación inválida: {left} {operator} {right}")
            return None

        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {left} {operator} {right}")
        print(f"Evaluación simbólica: {temp} = {left} {operator} {right}")
        return temp
    return action


def handle_for(self, init_stmt, condition_fn, update_stmt, body):
    def action():
        print("Iniciando ciclo FOR")
        init_stmt()

        start_label = self.intercode_generator.new_label()
        body_label  = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()

        self.intercode_generator.emit("// INICIO FOR")
        self.intercode_generator.emit(f"{start_label}:")

        condition_result = condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if !({cond_temp}) goto {end_label}")
        self.intercode_generator.emit(f"{body_label}:")

        iteration = 0
        while condition_result:
            iteration += 1
            print(f"Iteración #{iteration} del FOR")
            self.symbol_table.enter_scope()
            for stmt in body:
                if callable(stmt):
                    stmt()
            self.symbol_table.exit_scope()
            update_stmt()
            self._save_iteration_state()

            condition_result = condition_fn()
            cond_temp = condition_fn.temp_result
            self.intercode_generator.emit(f"if !({cond_temp}) goto {end_label}")
            self.intercode_generator.emit(f"goto {body_label}")

        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN FOR")

    return action


def _get_value(self, item):
    if isinstance(item, str):
        symbol = self.symbol_table.get_symbol(item)
        if symbol is None:
            self.errors.encolar_error(f"Error: Variable '{item}' no ha sido declarada.")
            return None
        return symbol['value']
    return item


def handle_if(self, condition_fn, if_body, else_body):
    def action():
        print("Iniciando IF con código intermedio")

        false_label = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()

        self.intercode_generator.emit("// INICIO IF")

        condition_result = condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if !({cond_temp}) goto {false_label}")

        # ───── BLOQUE IF ─────
        self.symbol_table.enter_scope()  

        for stmt in if_body:
            if callable(stmt):
                stmt()

        self.symbol_table.exit_scope()   

        self.intercode_generator.emit(f"goto {end_label}")

        # ───── BLOQUE ELSE ─────
        self.intercode_generator.emit(f"{false_label}:")

        if else_body:
            self.intercode_generator.emit("// ELSE")

            self.symbol_table.enter_scope()   

            for stmt in else_body:
                if callable(stmt):
                    stmt()

            self.symbol_table.exit_scope()   

        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN IF")

    return action


def handle_method_call(self, name, args=None):
    args = args or []
    print("Métodos registrados actualmente:", self.methods)
    def call_with_scope():
        if name not in self.methods:
            self.errors.encolar_error(f"Error: Método '{name}' no está definido.")
            return

        method_info = self.methods[name]
        # Soporta tanto dict {params, body} como lista directa (compatibilidad)
        if isinstance(method_info, dict):
            body   = method_info.get('body', [])
            params = method_info.get('params', [])
        else:
            body   = method_info
            params = []

        if not isinstance(body, list):
            self.errors.encolar_error(f"Error: El cuerpo del método '{name}' no es una lista.")
            return

        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = call {name}")

        self.symbol_table.enter_scope()
        self.en_funcion = True

        # Registrar argumentos como variables locales según parámetros declarados
        for idx, (param_type, param_name) in enumerate(params):
            if idx < len(args):
                # Evaluar el argumento
                arg_val = args[idx]
                if isinstance(arg_val, tuple) and len(arg_val) == 3:
                    # Es una expresión — evaluarla
                    left, op, right = arg_val
                    lv = self._get_value(left)
                    rv = self._get_value(right)
                    arg_val = self._apply_operator(lv, op, rv)
                elif isinstance(arg_val, str):
                    sym = self.symbol_table.get_symbol(arg_val)
                    arg_val = sym['value'] if sym else arg_val

                self.symbol_table.add_symbol(param_name, param_type, 'local', arg_val)
                self.intercode_generator.emit(f"{param_name} = {arg_val}")
            else:
                # Argumento faltante — declarar con None
                self.symbol_table.add_symbol(param_name, param_type, 'local', None)
                self.errors.encolar_error(
                    f"Advertencia: falta argumento '{param_name}' en llamada a '{name}'."
                )

        for idx, stmt in enumerate(body):
            if not callable(stmt):
                self.errors.encolar_error(
                    f"Error: El elemento {idx} del método '{name}' no es ejecutable."
                )
                continue
            stmt()

        self.en_funcion = False
        self.symbol_table.exit_scope()
        return temp

    return call_with_scope()


def handle_method_declaration(self, name, body):

    def action():

        if not isinstance(name, str):
            self.errors.encolar_error(
                f"Error interno: el nombre del método debe ser string, recibido {type(name)}"
            )
            return

        

        self.intercode_generator.emit(f"function {name}:")
        self.intercode_generator.emit("end")

        print(f"Método '{name}' registrado correctamente.")

    return action


def handle_switch(self, var_name, cases, default_body):
    def action():
        print("Iniciando SWITCH con código intermedio")

        processed_cases = []
        for idx, case in enumerate(cases):
            if not isinstance(case, tuple) or len(case) != 2:
                self.errors.encolar_error(
                    f"Error: el case #{idx} no tiene estructura válida (valor, cuerpo)."
                )
                return

            val, case_body = case
            try:
                hash(val)
            except TypeError:
                self.errors.encolar_error(
                    f"Error: el valor del case #{idx} no es válido para comparación: {val}"
                )
                return

            if not isinstance(case_body, list):
                case_body = [case_body]
            processed_cases.append((val, case_body))

        self.intercode_generator.emit(f"// SWITCH_START {var_name}")

        for val, case_body in processed_cases:
            self.intercode_generator.emit(f"// CASE {repr(val)}")
            for stmt in case_body:
                if callable(stmt):
                    stmt()
            self.intercode_generator.emit("// BREAK")

        self.intercode_generator.emit("// DEFAULT")
        if default_body:
            for stmt in default_body:
                if callable(stmt):
                    stmt()

        self.intercode_generator.emit("// SWITCH_END")

    return action


def handle_while(self, condition_fn, body):
    def action():
        print("Iniciando ciclo WHILE")

        start_label = self.intercode_generator.new_label()
        body_label  = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()

        self.intercode_generator.emit("// INICIO WHILE")
        self.intercode_generator.emit(f"{start_label}:")

        condition_result = condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if !({cond_temp}) goto {end_label}")
        self.intercode_generator.emit(f"{body_label}:")

        iteration = 0
        try:
            while condition_result:
                iteration += 1
                print(f"Iteración #{iteration} del WHILE")
                self.symbol_table.enter_scope()
                for stmt in body:
                    if callable(stmt):
                        stmt()
                self.symbol_table.exit_scope()
                self._save_iteration_state()
                condition_result = condition_fn()
        except Exception as e:
            self.errors.encolar_error(f"Error en cuerpo WHILE: {e}")
            print(f"Error en cuerpo WHILE: {e}")

        self.intercode_generator.emit(f"goto {start_label}")
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN WHILE")

    return action