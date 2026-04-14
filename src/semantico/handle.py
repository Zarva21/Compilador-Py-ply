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
# _evaluate_runtime
#
# Evalúa una expresión diferida en Python para obtener el valor REAL.
# Solo para poblar la tabla — NO emite IR.
#
# FIX 1 — Strings y chars sin comillas:
#   El lexer entrega CHAR_LITERAL como 'x' (con comillas) o a veces como x.
#   Ahora se detecta por el var_type del contexto cuando es string plano.
#
# FIX 2 — Loops:
#   handle_assignment llama a esto con en_funcion_loop=True cuando está
#   dentro de while/for/do-while. En ese caso se devuelve SENTINEL_LOOP
#   para que handle_assignment NO actualice la tabla.
#   Así la variable conserva su valor inicial (el que tenía antes del loop).
# ─────────────────────────────────────────────────────────────────────────────

# Sentinel especial — indica "modificado en loop, no actualizar tabla"
_LOOP_MODIFIED = object()


def _evaluate_runtime(self, val):
    # Tipos Python directos
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val

    # Callable → llamada a función, no evaluable en compile-time
    if callable(val):
        return None

    # Tupla → expresión aritmética diferida → resolver recursivamente
    if isinstance(val, tuple) and len(val) == 3:
        l, op, r = val
        lv = _evaluate_runtime(self, l)
        rv = _evaluate_runtime(self, r)
        # Si algún operando es sentinel de loop, propagar
        if lv is _LOOP_MODIFIED or rv is _LOOP_MODIFIED:
            return _LOOP_MODIFIED
        if lv is None or rv is None:
            return None
        return _apply_operator(self, lv, op, rv)

    # String: puede ser variable, literal o booleano textual
    if isinstance(val, str):
        if val == 'true':
            return True
        if val == 'false':
            return False

        # Literal string con comillas dobles → devolver sin comillas
        if val.startswith('"') and val.endswith('"') and len(val) >= 2:
            return val[1:-1]

        # Literal char con comillas simples → devolver sin comillas
        if val.startswith("'") and val.endswith("'") and len(val) >= 2:
            return val[1:-1]

        # Intentar parsear como número
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass

        # Buscar en tabla de símbolos
        sym = self.symbol_table.get_symbol(val)
        if sym is not None:
            return sym.get('value')

        # FIX: Si llegamos aquí con un string sin comillas que NO está en tabla,
        # puede ser un literal de char/string que el lexer entregó sin comillas.
        # Lo devolvemos tal cual — handle_declaration/assignment lo envolverá.
        return val

    return None


# ─────────────────────────────────────────────────────────────────────────────
# _infer_type
# ─────────────────────────────────────────────────────────────────────────────
def _infer_type(self, val):
    if isinstance(val, bool):
        return 'boofalant'
    if isinstance(val, int):
        return 'entei'
    if isinstance(val, float):
        return 'floatzel'

    if isinstance(val, str):
        sym = self.symbol_table.get_symbol(val)
        if sym is not None:
            return sym['type']

        if val.startswith('"') and val.endswith('"'):
            return 'stantler'

        if val.startswith("'") and val.endswith("'") and len(val) >= 2:
            return 'charizar'

        if val in ('true', 'false'):
            return 'boofalant'

        if val.startswith('t') and val[1:].isdigit():
            return 'unknown'

        try:
            int(val)
            return 'entei'
        except ValueError:
            pass
        try:
            float(val)
            return 'floatzel'
        except ValueError:
            pass

    return 'unknown'


# ─────────────────────────────────────────────────────────────────────────────
# _check_type_compatibility
# ─────────────────────────────────────────────────────────────────────────────
def _check_type_compatibility(self, type_l, op, type_r):
    numeric = {'entei', 'floatzel'}

    if 'unknown' in (type_l, type_r):
        return None

    if type_l == 'stantler' or type_r == 'stantler':
        if type_l == 'stantler' and type_r == 'stantler' and op == '+':
            return None
        other = type_r if type_l == 'stantler' else type_l
        return (
            f"Error semántico: no se puede aplicar '{op}' "
            f"entre 'stantler' y '{other}'. "
            f"Ambos operandos deben ser del mismo tipo."
        )

    if type_l == 'charizar' or type_r == 'charizar':
        if op in ('+', '-', '*', '/'):
            return (
                f"Error semántico: operación aritmética '{op}' "
                f"no permitida con tipo 'charizar'."
            )

    if type_l == 'boofalant' or type_r == 'boofalant':
        if op in ('+', '-', '*', '/'):
            return (
                f"Error semántico: operación aritmética '{op}' "
                f"no permitida con tipo 'boofalant'."
            )

    if type_l in numeric and type_r in numeric:
        return None

    return None


# ─────────────────────────────────────────────────────────────────────────────
# _resolve_ir
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_ir(self, val):
    if isinstance(val, tuple) and len(val) == 3:
        l, op, r = val
        lv = _resolve_ir(self, l)
        rv = _resolve_ir(self, r)

        type_l = _infer_type(self, lv)
        type_r = _infer_type(self, rv)
        error  = _check_type_compatibility(self, type_l, op, type_r)
        if error:
            self.errors.encolar_error(error)
            return '?'

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
        if val in ('true', 'false'):
            return val
        if val.startswith('"') or (val.startswith("'") and val.endswith("'")):
            return val
        if self.symbol_table.get_symbol(val) is not None:
            return val
        return f'"{val}"'
    else:
        return str(val)


# ─────────────────────────────────────────────────────────────────────────────
# _apply_operator
# ─────────────────────────────────────────────────────────────────────────────
def _apply_operator(self, a, op, b):
    try:
        if a is None or b is None:
            return None
        if op == '+':
            if type(a) == type(b):
                return a + b
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                return a + b
            return None
        if op == '-':
            return a - b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
        if op == '*':
            return a * b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
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
# _check_declaration_type
# ─────────────────────────────────────────────────────────────────────────────
def _check_declaration_type(self, name, var_type, value):
    if isinstance(value, tuple):
        return None

    # FIX: validación semántica de charizar (debe ser exactamente 1 carácter)
    # El lexer acepta cs...cs con cualquier contenido.
    # Aquí verificamos la longitud según el tipo declarado.
    if var_type.lower() == 'charizar' and isinstance(value, str):
        contenido = value
        if contenido.startswith("'") and contenido.endswith("'"):
            contenido = contenido[1:-1]
        if len(contenido) != 1:
            return (
                f"Error semántico: variable '{name}' es de tipo 'charizar' "
                f"y solo puede contener exactamente 1 carácter, "
                f"pero se asignó '{contenido}' ({len(contenido)} caracteres). "
                f"¿Quisiste usar 'stantler' para strings?"
            )

    inferred = _infer_type(self, value if not isinstance(value, str) else value)

    # charizar y stantler reciben unknown porque el lexer entrega el contenido
    # sin comillas — _infer_type no puede distinguirlos de un identificador.
    # La validación real de tipo ya se hizo arriba para charizar.
    compatible = {
        'entei':     {'entei'},
        'floatzel':  {'floatzel', 'entei'},
        'charizar':  {'charizar', 'unknown'},
        'stantler':  {'stantler', 'unknown'},
        'boofalant': {'boofalant'},
    }

    allowed = compatible.get(var_type.lower(), set())
    if inferred != 'unknown' and inferred not in allowed:
        return (
            f"Error semántico: no se puede asignar valor de tipo '{inferred}' "
            f"a variable '{name}' declarada como '{var_type}'."
        )
    return None


# ─────────────────────────────────────────────────────────────────────────────
# _normalize_string_value
#
# FIX para el problema de c = x (char/string sin comillas en tabla).
#
# Cuando el lexer entrega un CHAR_LITERAL o STRING_LITERAL, a veces
# el valor llega sin comillas (ej: x en vez de 'x').
# Esta función lo normaliza según el tipo declarado.
# ─────────────────────────────────────────────────────────────────────────────
def _normalize_string_value(var_type, raw_value):
    if not isinstance(raw_value, str):
        return raw_value

    # Si ya tiene comillas, devolverlo limpio (sin comillas)
    if raw_value.startswith('"') and raw_value.endswith('"') and len(raw_value) >= 2:
        return raw_value[1:-1]
    if raw_value.startswith("'") and raw_value.endswith("'") and len(raw_value) >= 2:
        return raw_value[1:-1]

    # Sin comillas → es el valor literal directamente
    # Para charizar y stantler lo devolvemos tal cual (es el char/string)
    if var_type.lower() in ('charizar', 'stantler'):
        return raw_value

    return raw_value


# ─────────────────────────────────────────────────────────────────────────────
# handle_declaration
#
# FIX aplicados:
#   - Usa _normalize_string_value para guardar el valor limpio en tabla
#   - Solo llama update_symbol si _evaluate_runtime no devuelve _LOOP_MODIFIED
# ─────────────────────────────────────────────────────────────────────────────
def handle_declaration(self, name, var_type, scope=None, value=None):
    def action():
        actual_scope = 'local' if self.en_funcion else 'global'

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

        # 1. Registrar en tabla con valor None
        self.symbol_table.add_symbol(name, var_type, actual_scope, None)

        # 2. Emitir IR
        if value is not None:
            if isinstance(value, tuple) and len(value) == 3:
                ir_val = _resolve_ir(self, value)
                if ir_val != '?':
                    error = _check_declaration_type(self, name, var_type, value)
                    if error:
                        self.errors.encolar_error(error)
                        return
                    self.intercode_generator.emit(f"{name} = {ir_val}")
            elif callable(value):
                result = value()
                if result is not None:
                    self.intercode_generator.emit(f"{name} = {result}")
            else:
                error = _check_declaration_type(self, name, var_type, value)
                if error:
                    self.errors.encolar_error(error)
                    return
                ir_value = value
                if var_type.lower() == 'charizar' and isinstance(value, str):
                    if not (value.startswith("'") and value.endswith("'")):
                        ir_value = f"'{value}'"
                self.intercode_generator.emit(f"{name} = {ir_value}")

            # 3. Evaluar valor real y guardar en tabla
            raw = _evaluate_runtime(self, value)

            # Si devuelve el sentinel de loop → no actualizar (conservar None = "sin valor")
            # Pero en declaración nunca estamos dentro de loop todavía, así que
            # este caso no debería darse aquí. Lo dejamos por seguridad.
            if raw is _LOOP_MODIFIED:
                return

            # Normalizar strings/chars para que se vean bien en la tabla
            real_value = _normalize_string_value(var_type, raw)
            self.symbol_table.update_symbol(name, real_value)

    return action


# ─────────────────────────────────────────────────────────────────────────────
# handle_assignment
#
# FIX aplicados:
#   - Si en_loop es True → NO actualizar tabla (conservar valor inicial)
#   - Normalizar strings/chars
# ─────────────────────────────────────────────────────────────────────────────
def handle_assignment(self, name, value):
    def action():
        sym = self.symbol_table.get_symbol(name)
        if sym is None:
            self.errors.encolar_error(f"Error semántico: variable '{name}' no declarada.")
            return

        var_type = sym['type']

        # 1. Emitir IR
        if isinstance(value, tuple) and len(value) == 3:
            ir_val = _resolve_ir(self, value)
            if ir_val == '?':
                return
            self.intercode_generator.emit(f"{name} = {ir_val}")

        elif callable(value):
            result = value()
            if result is not None:
                self.intercode_generator.emit(f"{name} = {result}")

        else:
            error = _check_declaration_type(self, name, var_type, value)
            if error:
                self.errors.encolar_error(error)
                return
            self.intercode_generator.emit(f"{name} = {value}")

        # 2. Actualizar tabla SOLO si NO estamos dentro de un loop
        #    Si en_loop=True → la variable puede cambiar N veces →
        #    conservamos el valor estático conocido antes del loop.
        if getattr(self, 'en_loop', False):
            return   # No tocar la tabla — conservar valor inicial

        raw = _evaluate_runtime(self, value)
        if raw is _LOOP_MODIFIED:
            return

        real_value = _normalize_string_value(var_type, raw)
        self.symbol_table.update_symbol(name, real_value)

    return action


# ─────────────────────────────────────────────────────────────────────────────
# handle_expression_statement
#
# FIX NUEVO — error semántico por expresión sin efecto.
#
# Se llama desde el parser en lugar de dejar pasar la expresión silenciosamente.
# Una expresión es "sin efecto" si no es:
#   - asignación       → ya tiene su propia regla
#   - llamada a función (callable) → tiene efecto
#   - print, return, break → tienen sus propias reglas
#
# Todo lo que llegue aquí como expresión suelta es sin efecto.
# ─────────────────────────────────────────────────────────────────────────────
def handle_expression_statement(self, expr, line=None):
    """
    Detecta si la expresión tiene efecto lateral.
    - callable  → es llamada a función → dejar pasar (emite IR)
    - tuple/literal → operación aritmética suelta → error semántico
    """
    def action():
        # Si es callable es una method_call → tiene efecto
        if callable(expr):
            expr()
            return

        # Cualquier otra expresión suelta (aritmética, literal, variable) → sin efecto
        line_info = f" en línea {line}" if line else ""
        self.errors.encolar_error(
            f"Error semántico: expresión sin efecto{line_info}. "
            f"El resultado de la expresión no se asigna ni utiliza."
        )

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

        type_l = _infer_type(self, left_val)
        type_r = _infer_type(self, right_val)
        if type_l != 'unknown' and type_r != 'unknown' and type_l != type_r:
            numeric = {'entei', 'floatzel'}
            if not (type_l in numeric and type_r in numeric):
                self.errors.encolar_error(
                    f"Error semántico: comparación '{op}' entre tipos "
                    f"incompatibles '{type_l}' y '{type_r}'."
                )

        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {left_val} {op} {right_val}")
        condition_fn.temp_result = temp
        return True

    condition_fn.temp_result = "t_cond"
    return condition_fn


# ─────────────────────────────────────────────────────────────────────────────
# handle_expression
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
# FIX: while/for/do-while activan self.en_loop = True antes de ejecutar el
# cuerpo, y lo restauran al salir. Así handle_assignment sabe que está
# dentro de un loop y no actualiza la tabla.
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

        # FIX: activar en_loop antes de ejecutar el cuerpo
        prev_loop = getattr(self, 'en_loop', False)
        self.en_loop = True

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt): stmt()
        self.symbol_table.exit_scope()

        # Restaurar estado anterior (permite loops anidados)
        self.en_loop = prev_loop

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

        # FIX: activar en_loop
        prev_loop = getattr(self, 'en_loop', False)
        self.en_loop = True

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt): stmt()
        self.symbol_table.exit_scope()

        if callable(update_stmt): update_stmt()

        self.en_loop = prev_loop

        self.intercode_generator.emit(f"goto {start_label}")
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN FOR")

    return action


def handle_do_while(self, condition_fn, body):
    def action():
        start_label = self.intercode_generator.new_label()

        self.intercode_generator.emit("//INICIO DO-WHILE")
        self.intercode_generator.emit(f"{start_label}:")

        # FIX: activar en_loop
        prev_loop = getattr(self, 'en_loop', False)
        self.en_loop = True

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt): stmt()
        self.symbol_table.exit_scope()

        self.en_loop = prev_loop

        condition_fn()
        cond_temp = condition_fn.temp_result
        self.intercode_generator.emit(f"if ({cond_temp}) goto {start_label}")
        self.intercode_generator.emit("//FIN DO-WHILE")

    return action


# ─────────────────────────────────────────────────────────────────────────────
# handle_method_call
# ─────────────────────────────────────────────────────────────────────────────
def handle_method_call(self, name, args=None):
    args = args or []
    print(f" [CALL] Preparando llamada a función '{name}' con argumentos: {args}")
    def call_with_scope():
        if name not in self.methods:
            self.errors.encolar_error(f"Error semántico: función '{name}' no definida.")
            return None

        expected_params = self.methods[name].get('params', [])
        if len(args) != len(expected_params):
            self.errors.encolar_error(
                f"Error semántico: función '{name}' espera {len(expected_params)} "
                f"argumento(s), pero se pasaron {len(args)}."
            )
            return None

        temp = self.intercode_generator.new_temp()

        arg_ir_names = []
        for i, arg in enumerate(args):
            ir_name = _resolve_ir(self, arg)
            param_type, param_name = expected_params[i]
            arg_type = _infer_type(self, ir_name)
            if arg_type != 'unknown' and arg_type != param_type:
                numeric = {'entei', 'floatzel'}
                if not (arg_type in numeric and param_type in numeric):
                    self.errors.encolar_error(
                        f"Error semántico: argumento {i+1} de '{name}' "
                        f"es de tipo '{arg_type}', se esperaba '{param_type}'."
                    )
            arg_ir_names.append(ir_name)

        for arg_name in arg_ir_names:
            self.intercode_generator.emit(f"param {arg_name}")

        args_str = ', '.join(arg_ir_names)
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
        print(f" [FUNC]  Función '{name}' registrada con return_type='{ret_type}' y params={params}")
        self.en_funcion = True

        for param_type, param_name in params:
            self.symbol_table.add_symbol(param_name, param_type, 'local', None)
            print(f" [PARAM]  Variable '{param_name}' ({param_type}) registrada")

        for stmt in flat_body:
            if callable(stmt): stmt()

        self.en_funcion = False
        self.symbol_table.exit_scope()
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