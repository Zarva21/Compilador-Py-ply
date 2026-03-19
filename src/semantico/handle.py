import json, os, tempfile
from datetime import datetime

def _save_iteration_state(self):
    temp_dir = tempfile.gettempdir()
    path = os.path.join(temp_dir, "tabla_simbolos_iteracion_historial.json")

    # Cargar historial anterior si existe
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            historial = json.load(f)
    else:
        historial = []

    # Serializar variables globales
    global_serializado = {
        str(k): v["value"] for k, v in self.symbol_table.global_scope.items()
    }

    # Serializar scopes locales
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

    # Guardar entrada en historial
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
            if op == 'cristiano':
                return a + b if type(a) == type(b) else self._op_error(op, a, b)
            if op == 'tchouameni':
                return a - b if self._check_numeric(a, b) else self._op_error(op, a, b)
            if op == 'messi':
                return a * b if self._check_numeric(a, b) else self._op_error(op, a, b)
            if op == 'pepe':
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
            value_eval = None

            # Evaluar expresiones (tuplas) de manera recursiva
            def evaluar_exp(val):
                if isinstance(val, tuple) and len(val) == 3:
                    left, op, right = val
                    left_val = evaluar_exp(left)
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
                    return val()  # Ejecutar funciones como resultado de métodos
                else:
                    return self._get_value(val)

            # Evaluar el valor final
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

            # Asignar en la tabla de símbolos
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

        # Evaluar el valor inicial (literal o variable)
        if isinstance(value, (int, float, bool, str)):
            evaluated_value = value
        elif isinstance(value, tuple) and len(value) == 3:
            # Si es una expresión como (a, '+', b)
            left, op, right = value
            temp = self.intercode_generator.emit_temp(left, op, right)
            evaluated_value = temp
        else:
            evaluated_value = self._get_value(value)

        # Guardar en tabla de símbolos
        self.symbol_table.add_symbol(name, var_type, actual_scope, evaluated_value)
        print(f"Declaración ({actual_scope}): {name} = {evaluated_value}")

        # Generar código intermedio
        if evaluated_value is not None:
            self.intercode_generator.emit(f"{name} = {evaluated_value}")

    return action

def handle_do_while(self, condition_fn, body):
    def action():
        print("Iniciando ciclo DO-WHILE")

        # Crear etiqueta de inicio del ciclo
        start_label = self.intercode_generator.new_label()
        self.intercode_generator.emit(f"//INICIO DO-WHILE")
        self.intercode_generator.emit(f"{start_label}:")

        # Ejecutar el cuerpo del ciclo al menos una vez
        iteration = 0
        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt):
                stmt()
        self.symbol_table.exit_scope()
        self._save_iteration_state()

        # Evaluar la condición una sola vez al final
        condition_result = condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if ({cond_temp}) goto {start_label}")
        self.intercode_generator.emit(f"//FIN DO-WHILE")

    return action

def evaluate_condition_dynamic(self, left, op, right):
    def condition_fn():
        # Obtener valores reales
        left_sym = self.symbol_table.get_symbol(left)
        if left_sym is None:
            self.errors.encolar_error(f"Error: Variable '{left}' no declarada en la condición.")
            condition_fn.temp_result = "0"
            return False

        left_val = left_sym['value']
        right_val = self._get_value(right)

        if left_val is None or right_val is None:
            self.errors.encolar_error("Error: condición con operandos no evaluables.")
            condition_fn.temp_result = "0"
            return False

        # Generar el temporal para código intermedio
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {left} {op} {right}")
        condition_fn.temp_result = temp  # Guardamos el temporal para emitir luego: if !temp goto

        # Evaluación booleana inmediata para el flujo lógico
        try:
            if op == '>':
                return left_val > right_val
            elif op == '<':
                return left_val < right_val
            elif op == '==':
                return left_val == right_val
            elif op == '!=':
                return left_val != right_val
            elif op == '>=':
                return left_val >= right_val
            elif op == '<=':
                return left_val <= right_val
            else:
                self.errors.encolar_error(f"Operador relacional no soportado: {op}")
                return False
        except Exception as e:
            self.errors.encolar_error(f"Error en evaluación de condición: {e}")
            return False

    return condition_fn

def handle_expression(self, left, operator, right):
    def action():
        # Obtener los operandos en forma de texto o temporales
        val1 = left if isinstance(left, (int, float, str)) else self._get_value(left)
        val2 = right if isinstance(right, (int, float, str)) else self._get_value(right)

        # Validación
        if val1 is None or val2 is None:
            self.errors.encolar_error(f"Error: Operación inválida: {left} {operator} {right}")
            return None

        # Crear un temporal y emitir instrucción
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {left} {operator} {right}")

        print(f"Evaluación simbólica: {temp} = {left} {operator} {right}")
        return temp  # Retorna el temporal para su uso posterior
    return action

def handle_for(self, init_stmt, condition_fn, update_stmt, body):
    def action():
        print("Iniciando ciclo FOR")

        # Ejecutar inicialización (ej: x = 0)
        init_stmt()

        # Generar etiquetas
        start_label = self.intercode_generator.new_label()
        body_label = self.intercode_generator.new_label()
        end_label = self.intercode_generator.new_label()

        self.intercode_generator.emit(f"// INICIO FOR")
        self.intercode_generator.emit(f"{start_label}:")

        # Evaluar condición y generar temporal
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

            # Volver a evaluar la condición en cada iteración
            condition_result = condition_fn()
            cond_temp = condition_fn.temp_result
            self.intercode_generator.emit(f"if !({cond_temp}) goto {end_label}")
            self.intercode_generator.emit(f"goto {body_label}")

        # Cierre del ciclo
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit(f"// FIN FOR")

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

        true_label = self.intercode_generator.new_label()
        false_label = self.intercode_generator.new_label()
        end_label = self.intercode_generator.new_label()

        self.intercode_generator.emit("// INICIO IF")

        condition_result = condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if !({cond_temp}) goto {false_label}")
        
        # Bloque IF verdadero
        for stmt in if_body:
            if callable(stmt):
                stmt()
        self.intercode_generator.emit(f"goto {end_label}")

        # Bloque ELSE
        self.intercode_generator.emit(f"{false_label}:")
        if else_body:
            self.intercode_generator.emit("// ELSE")
            for stmt in else_body:
                if callable(stmt):
                    stmt()

        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN IF")

    return action

def handle_method_call(self, name):
    def call_with_scope():
        if name not in self.methods:
            self.errors.encolar_error(f"Error: Método '{name}' no está definido.")
            return

        body = self.methods[name]
        print(f" Ejecutando método '{name}', body = {body}")

        if not isinstance(body, list):
            self.errors.encolar_error(f"Error: El cuerpo del método '{name}' no es una lista.")
            return

        # Generar código intermedio para llamada a método
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = call {name}")

        # Entrar a nuevo ámbito (scope local del método)
        self.symbol_table.enter_scope()
        self.en_funcion = True

        for i, stmt in enumerate(body):
            if not callable(stmt):
                self.errors.encolar_error(f"Error: El elemento {i} del método '{name}' no es ejecutable.")
                continue
            print(f"Ejecutando instrucción {i} del método '{name}'")
            stmt()

        # Salida de ámbito
        self.en_funcion = False
        self.symbol_table.exit_scope()

        return temp  # Devuelve el temporal con el valor de retorno si se necesitara

    return call_with_scope

def handle_method_declaration(self, name, body):
    def flatten(statements):
        flat = []
        for stmt in statements:
            if isinstance(stmt, list):
                flat.extend(flatten(stmt))
            else:
                flat.append(stmt)
        return flat

    def action():
        if not isinstance(name, str):
            self.errors.encolar_error(
                f"Error interno: el nombre del método debe ser string, recibido {type(name)}"
            )
            print(f"Nombre de método inválido: {name}")
            return

        flat_body = flatten(body)
        self.methods[name] = flat_body

        # Emitir inicio de función
        self.intercode_generator.emit(f"function {name}:")

        # Iniciar nuevo ámbito local
        self.symbol_table.enter_scope()
        self.en_funcion = True

        for i, stmt in enumerate(flat_body):
            if callable(stmt):
                print(f"Ejecutando instrucción {i} de '{name}'")
                stmt()

        self.en_funcion = False
        self.symbol_table.exit_scope()

        # Emitir cierre de función
        self.intercode_generator.emit("end")

        print(f"Método '{name}' definido y procesado con código intermedio.")
    return action


def handle_switch(self, var_name, cases, default_body):
    def action():
        print("Iniciando SWITCH con código intermedio")
        print("Verificando estructura de 'cases':")

        processed_cases = []
        for i, case in enumerate(cases):
            print(f"case #{i}: {case} | tipo={type(case)}")

            if not isinstance(case, tuple) or len(case) != 2:
                self.errors.encolar_error(f"Error: el case #{i} no tiene una estructura válida (valor, cuerpo).")
                return

            val, body = case

            try:
                hash(val)
            except TypeError:
                self.errors.encolar_error(f"Error: el valor del case #{i} no es válido para comparación: {val}")
                return

            if not isinstance(body, list):
                body = [body]

            processed_cases.append((val, body))

        print("Casos del switch procesados como tuplas:", processed_cases)

        # Emitir un marcador para que el generador C++ detecte que debe generar un switch real
        self.intercode_generator.emit(f"// SWITCH_START {var_name}")

        for val, body in processed_cases:
            self.intercode_generator.emit(f"// CASE {repr(val)}")
            for stmt in body:
                if callable(stmt):
                    stmt()
            self.intercode_generator.emit("// BREAK")

        self.intercode_generator.emit(f"// DEFAULT")
        if default_body:
            for stmt in default_body:
                if callable(stmt):
                    stmt()

        self.intercode_generator.emit(f"// SWITCH_END")

    return action


def handle_while(self, condition_fn, body):
    def action():
        print("Iniciando ciclo WHILE")

        start_label = self.intercode_generator.new_label()
        body_label = self.intercode_generator.new_label()
        end_label = self.intercode_generator.new_label()

        self.intercode_generator.emit(f"// INICIO WHILE")
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
                condition_result = condition_fn()  # re-evaluar para la siguiente vuelta
        except Exception as e:
            self.errors.encolar_error(f"Error en cuerpo WHILE: {e}")
            print(f"Error en cuerpo WHILE: {e}")

        self.intercode_generator.emit(f"goto {start_label}")
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit(f"// FIN WHILE")

    return action