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
# ─────────────────────────────────────────────────────────────────────────────

# Sentinel especial — indica "modificado en loop, no actualizar tabla"
_LOOP_MODIFIED = object()


def make_literal(tipo, valor):
    return {'kind': 'literal', 'type': tipo, 'value': valor}


def _is_literal(val):
    return isinstance(val, dict) and val.get('kind') == 'literal'


def make_array_access(name, index):
    return {'kind': 'array_access', 'name': name, 'index': index}


def _is_array_access(val):
    return isinstance(val, dict) and val.get('kind') == 'array_access'


def make_field_access(name, field):
    return {'kind': 'field_access', 'name': name, 'field': field}


def _is_field_access(val):
    return isinstance(val, dict) and val.get('kind') == 'field_access'


BASIC_TYPES = {'entei', 'floatzel', 'charizar', 'boofalant', 'stantler'}


def _param_parts(param):
    if isinstance(param, dict):
        return param.get('type'), param.get('name'), bool(param.get('is_ref'))
    if isinstance(param, (tuple, list)) and len(param) == 3:
        return param[0], param[1], bool(param[2])
    if isinstance(param, (tuple, list)) and len(param) == 2:
        return param[0], param[1], False
    return 'unknown', '?', False


def _runtime_env_value(self, name):
    for env in reversed(getattr(self, 'partial_eval_env_stack', [])):
        if name in env:
            return env[name]
    return None


def _has_runtime_env_value(self, name):
    return any(name in env for env in getattr(self, 'partial_eval_env_stack', []))


def _literal_to_ir(val):
    tipo = val.get('type')
    valor = val.get('value')
    if tipo == 'stantler':
        return f'"{valor}"'
    if tipo == 'charizar':
        return f"'{valor}'"
    if tipo == 'boofalant':
        return 'true' if valor else 'false'
    return str(valor)


def _pos_suffix(self, name):
    get_position = getattr(self, 'get_position', None)
    pos = get_position(name) if callable(get_position) else None
    if pos:
        return f" en fila {pos[0]}, col {pos[1]}"
    return ""


def _ir_op(op):
    return {
        'su': '+',
        're': '-',
        'mu': '*',
        'di': '/',
        'mo': '%',
        'andor': '&&',
        'oror': '||',
        'not': '!',
        'ma': '>',
        'me': '<',
        'mai': '>=',
        'mei': '<=',
        'ig': '==',
        'ni': '!=',
    }.get(op, op)


def _evaluate_runtime(self, val):
    if _is_literal(val):
        return val.get('value')

    if isinstance(val, TypedCall):
        return val.evaluate_runtime()

    if _is_array_access(val):
        sym = self.symbol_table.get_symbol(val['name'])
        if sym is None or sym.get('kind') != 'array':
            return None
        values = sym.get('value')
        index = _evaluate_runtime(self, val['index'])
        if not isinstance(values, list) or not isinstance(index, int):
            return None
        if 0 <= index < len(values):
            return values[index]
        return None

    if _is_field_access(val):
        sym = self.symbol_table.get_symbol(val['name'])
        if sym is None or sym.get('kind') != 'struct_instance':
            return None
        field_data = sym.get('fields', {}).get(val['field'])
        if isinstance(field_data, dict):
            return field_data.get('value')
        return None

    # Tipos Python directos
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val

    # Callable -> llamada a función, no evaluable en compile-time
    if callable(val):
        return None

    # Tupla -> expresión aritmética diferida -> resolver recursivamente
    if isinstance(val, tuple) and len(val) == 3:
        l, op, r = val
        lv = _evaluate_runtime(self, l)
        rv = _evaluate_runtime(self, r)

        if lv is _LOOP_MODIFIED or rv is _LOOP_MODIFIED:
            return _LOOP_MODIFIED
        if lv is None or rv is None:
            return None

        # Operadores relacionales
        if op == 'ma':
            return lv > rv
        if op == 'me':
            return lv < rv
        if op == 'ig':
            return lv == rv
        if op == 'ni':
            return lv != rv
        if op == 'mai':
            return lv >= rv
        if op == 'mei':
            return lv <= rv

        # Operadores aritméticos
        if op == 'andor':
            return (lv and rv) if isinstance(lv, bool) and isinstance(rv, bool) else None
        if op == 'oror':
            return (lv or rv) if isinstance(lv, bool) and isinstance(rv, bool) else None

        return _apply_operator(self, lv, op, rv)

    if isinstance(val, tuple) and len(val) == 2 and val[0] == 'not':
        operand = _evaluate_runtime(self, val[1])
        if operand is _LOOP_MODIFIED:
            return _LOOP_MODIFIED
        if operand is None:
            return None
        return not operand if isinstance(operand, bool) else None

    # String: puede ser variable, literal o booleano textual
    if isinstance(val, str):
        if val == 'true':
            return True
        if val == 'false':
            return False

        # Literal string con comillas dobles -> devolver sin comillas
        if val.startswith('"') and val.endswith('"') and len(val) >= 2:
            return val[1:-1]

        # Literal char con comillas simples -> devolver sin comillas
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
        if _has_runtime_env_value(self, val):
            return _runtime_env_value(self, val)

        sym = self.symbol_table.get_symbol(val)
        if sym is not None:
            return sym.get('value')

        
        return val

    return None

class TypedCall:
    def __init__(self, fn, return_type, name, runtime_fn=None):
        self.fn = fn
        self.return_type = return_type
        self.name = name
        self.runtime_fn = runtime_fn

    def __call__(self):
        return self.fn()

    def evaluate_runtime(self):
        if callable(self.runtime_fn):
            return self.runtime_fn()
        return None
    

# ─────────────────────────────────────────────────────────────────────────────
# _infer_type
# ─────────────────────────────────────────────────────────────────────────────
def _infer_type(self, val):
    if _is_literal(val):
        return val.get('type', 'unknown')

    if _is_array_access(val):
        sym = self.symbol_table.get_symbol(val['name'])
        if sym is not None and sym.get('kind') == 'array':
            return sym.get('type', 'unknown')
        return 'unknown'

    if _is_field_access(val):
        sym = self.symbol_table.get_symbol(val['name'])
        if sym is None or sym.get('kind') != 'struct_instance':
            return 'unknown'
        struct_type = sym.get('type')
        fields = getattr(self, 'struct_types', {}).get(struct_type, {})
        return fields.get(val['field'], 'unknown')
    
    if isinstance(val, TypedCall):
        return val.return_type

    if isinstance(val, tuple) and len(val) == 3:
        l, op, r = val

        relational_ops = {'ma', 'me', 'mai', 'mei', 'ig', 'ni'}
        logical_ops = {'andor', 'oror', '&&', '||'}
        arithmetic_ops = {'+', '-', '*', '/', '%', 'su', 're', 'mu', 'di', 'mo'}

        if op in relational_ops:
            return 'boofalant'

        if op in logical_ops:
            return 'boofalant'

        if op in arithmetic_ops:
            lt = _infer_type(self, l)
            rt = _infer_type(self, r)

            if op in ('mo', '%'):
                if lt == 'entei' and rt == 'entei':
                    return 'entei'
                return 'unknown'

            if lt == 'floatzel' or rt == 'floatzel':
                return 'floatzel'
            if lt == 'entei' and rt == 'entei':
                return 'entei'

        return 'unknown'

    if isinstance(val, tuple) and len(val) == 2 and val[0] == 'not':
        return 'boofalant'

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
# validate_boolean_expression
# ─────────────────────────────────────────────────────────────────────────────

def validate_boolean_expression(self, expr):
    inferred = _infer_type(self, expr)

    if inferred == 'unknown':
        return True

    if inferred != 'boofalant':
        self.errors.encolar_error(
            f"Error semántico: la condición debe ser de tipo 'boofalant', no '{inferred}'."
        )
        return False

    return True



# ─────────────────────────────────────────────────────────────────────────────
# _check_type_compatibility
# ─────────────────────────────────────────────────────────────────────────────
def _check_type_compatibility(self, type_l, op, type_r):
    numeric = {'entei', 'floatzel'}
    op_norm = {
        'su': '+', 're': '-', 'mu': '*', 'di': '/', 'mo': '%',
        'andor': '&&', 'oror': '||',
    }.get(op, op)

    if 'unknown' in (type_l, type_r):
        return None

    if op_norm in ('&&', '||'):
        if type_l == 'boofalant' and type_r == 'boofalant':
            return None
        return (
            f"Error semántico: operador '{op}' solo permite operandos 'boofalant'. "
            f"Se encontró '{type_l}' y '{type_r}'."
        )

    if type_l == 'stantler' or type_r == 'stantler':
        if type_l == 'stantler' and type_r == 'stantler' and op_norm == '+':
            return None
        other = type_r if type_l == 'stantler' else type_l
        return (
            f"Error semántico: no se puede aplicar '{op}' "
            f"entre 'stantler' y '{other}'. "
            f"Ambos operandos deben ser del mismo tipo."
        )

    if op_norm == '%':
        if type_l == 'entei' and type_r == 'entei':
            return None
        return (
            f"Error semántico: operador 'mo' (%) solo permite operandos 'entei'. "
            f"Se encontró '{type_l}' y '{type_r}'."
        )

    if type_l == 'charizar' or type_r == 'charizar':
        if op_norm in ('+', '-', '*', '/', '%'):
            return (
                f"Error semántico: operación aritmética '{op}' "
                f"no permitida con tipo 'charizar'."
            )

    if type_l == 'boofalant' or type_r == 'boofalant':
        if op_norm in ('+', '-', '*', '/', '%'):
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
    if _is_literal(val):
        return _literal_to_ir(val)

    if _is_array_access(val):
        name = val['name']
        index_expr = val['index']
        sym = self.symbol_table.get_symbol(name)
        if sym is None:
            self.errors.encolar_error(f"Error semántico: arreglo '{name}' no declarado{_pos_suffix(self, name)}.")
            return '?'
        if sym.get('kind') != 'array':
            self.errors.encolar_error(f"Error semántico: '{name}' no es un arreglo{_pos_suffix(self, name)}.")
            return '?'

        index_type = _infer_type(self, index_expr)
        if index_type != 'unknown' and index_type != 'entei':
            self.errors.encolar_error(
                f"Error semántico: el índice de '{name}' debe ser 'entei', no '{index_type}'{_pos_suffix(self, name)}."
            )
            return '?'

        index_value = _evaluate_runtime(self, index_expr)
        size = sym.get('size')
        if isinstance(index_value, int) and isinstance(size, int) and not (0 <= index_value < size):
            self.errors.encolar_error(
                f"Error semántico: índice {index_value} fuera de rango para arreglo '{name}' de tamaño {size}{_pos_suffix(self, name)}."
            )
            return '?'

        index_ir = _resolve_ir(self, index_expr)
        if index_ir == '?':
            return '?'
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {name}[{index_ir}]")
        return temp

    if _is_field_access(val):
        name = val['name']
        field = val['field']
        sym = self.symbol_table.get_symbol(name)
        if sym is None:
            self.errors.encolar_error(f"Error semántico: variable struct '{name}' no declarada{_pos_suffix(self, name)}.")
            return '?'
        if sym.get('kind') != 'struct_instance':
            self.errors.encolar_error(f"Error semántico: '{name}' no es una instancia de struct{_pos_suffix(self, name)}.")
            return '?'
        struct_type = sym.get('type')
        fields = getattr(self, 'struct_types', {}).get(struct_type, {})
        if field not in fields:
            self.errors.encolar_error(
                f"Error semántico: campo '{field}' no existe en struct '{struct_type}'{_pos_suffix(self, name)}."
            )
            return '?'
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {name}.{field}")
        return temp

    if isinstance(val, tuple) and len(val) == 3:
        l, op, r = val
        lv = _resolve_ir(self, l)
        rv = _resolve_ir(self, r)

        type_l = _infer_type(self, l)
        type_r = _infer_type(self, r)
        error  = _check_type_compatibility(self, type_l, op, type_r)
        if error:
            self.errors.encolar_error(error)
            return '?'

        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = {lv} {_ir_op(op)} {rv}")
        return temp

    if isinstance(val, tuple) and len(val) == 2 and val[0] == 'not':
        operand = val[1]
        operand_type = _infer_type(self, operand)
        if operand_type != 'unknown' and operand_type != 'boofalant':
            self.errors.encolar_error(
                f"Error semántico: operador 'not' solo permite operandos 'boofalant'. "
                f"Se encontró '{operand_type}'."
            )
            return '?'

        ir_val = _resolve_ir(self, operand)
        if ir_val == '?':
            return '?'
        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = !{ir_val}")
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
        try:
            int(val)
            return val
        except ValueError:
            pass
        try:
            float(val)
            return val
        except ValueError:
            pass
        self.errors.encolar_error(f"Error semántico: variable '{val}' no declarada{_pos_suffix(self, val)}.")
        return '?'
    else:
        return str(val)


# ─────────────────────────────────────────────────────────────────────────────
# _apply_operator
# ─────────────────────────────────────────────────────────────────────────────
def _apply_operator(self, a, op, b):
    try:
        op = {
            'su': '+', 're': '-', 'mu': '*', 'di': '/', 'mo': '%',
            'andor': '&&', 'oror': '||',
        }.get(op, op)
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
        if op == '%':
            if b == 0:
                self.errors.encolar_error("Error semántico: módulo por cero.")
                return None
            return a % b if isinstance(a, int) and isinstance(b, int) else None
        if op == '&&':
            return (a and b) if isinstance(a, bool) and isinstance(b, bool) else None
        if op == '||':
            return (a or b) if isinstance(a, bool) and isinstance(b, bool) else None
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

    if isinstance(value, str) and self.symbol_table.get_symbol(value) is None:
        return f"Error semántico: variable '{value}' no declarada{_pos_suffix(self, value)}."

    if var_type.lower() == 'charizar' and isinstance(value, str):
        contenido = value
        if contenido.startswith("'") and contenido.endswith("'"):
            contenido = contenido[1:-1]
        if len(contenido) != 1:
            return (
                f"Error semántico: variable '{name}' es de tipo 'charizar' "
                f"y solo puede contener exactamente 1 carácter, "
                f"pero se asignó '{contenido}' ({len(contenido)} caracteres). "
                f"¿Quisiste usar 'stantler' para strings?{_pos_suffix(self, name)}"
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
            f"a variable '{name}' declarada como '{var_type}'{_pos_suffix(self, name)}."
        )
    return None


# ─────────────────────────────────────────────────────────────────────────────
# _normalize_string_value
# ─────────────────────────────────────────────────────────────────────────────
def _normalize_string_value(var_type, raw_value):
    if not isinstance(raw_value, str):
        return raw_value

    # Si ya tiene comillas, devolverlo limpio (sin comillas)
    if raw_value.startswith('"') and raw_value.endswith('"') and len(raw_value) >= 2:
        return raw_value[1:-1]
    if raw_value.startswith("'") and raw_value.endswith("'") and len(raw_value) >= 2:
        return raw_value[1:-1]

   
    # Para charizar y stantler lo devolvemos tal cual (es el char/string)
    if var_type.lower() in ('charizar', 'stantler'):
        return raw_value

    return raw_value


# ─────────────────────────────────────────────────────────────────────────────
# handle_declaration
# ─────────────────────────────────────────────────────────────────────────────
def handle_declaration(self, name, var_type,value=None):
    def action():
        # Detectar scope REAL
        is_global = len(self.symbol_table.scope_stack) == 1
        actual_scope = 'global' if is_global else 'local'

        registered = self.symbol_table.add_symbol(name, var_type, actual_scope, None)
        if not registered:
            existing = self.symbol_table.get_symbol(name)
            existing_type = existing.get('type', '?') if existing else '?'

            if existing_type != var_type:
                self.errors.encolar_error(
                    f"Error semántico: variable '{name}' ya declarada como "
                    f"'{existing_type}' en este ámbito. No se puede redeclarar como '{var_type}'."
                )
            else:
                self.errors.encolar_error(
                    f"Error semántico: variable '{name}' ya declarada. ¿Quisiste asignar?"
                )
            return

        # 2. Emitir IR
        if value is not None:
            if isinstance(value, tuple) or _is_array_access(value) or _is_field_access(value):
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

                if _is_literal(value):
                    ir_value = _literal_to_ir(value)
                elif isinstance(value, bool):
                    ir_value = 'true' if value else 'false'

                elif isinstance(value, str):
                    if var_type.lower() == 'charizar':
                        if not (value.startswith("'") and value.endswith("'")):
                            ir_value = f"'{value}'"
                    elif var_type.lower() == 'stantler':
                        if not (value.startswith('"') and value.endswith('"')):
                            ir_value = f'"{value}"'

                self.intercode_generator.emit(f"{name} = {ir_value}")

            # 3. Evaluar valor real y guardar en tabla
            raw = _evaluate_runtime(self, value)

            # Si devuelve el sentinel de loop -> no actualizar (conservar None = "sin valor")
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
# ─────────────────────────────────────────────────────────────────────────────
def handle_assignment(self, name, value):
    def action():
        sym = self.symbol_table.get_symbol(name)
        if sym is None:
            self.errors.encolar_error(f"Error semántico: variable '{name}' no declarada{_pos_suffix(self, name)}.")
            return

        var_type = sym['type']

        # 1. Emitir IR
        if isinstance(value, tuple) or _is_array_access(value) or _is_field_access(value):
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

            ir_value = value

            if _is_literal(value):
                ir_value = _literal_to_ir(value)
            elif isinstance(value, bool):
                ir_value = 'true' if value else 'false'

            elif isinstance(value, str):
                if var_type.lower() == 'charizar':
                    if not (value.startswith("'") and value.endswith("'")):
                        ir_value = f"'{value}'"
                elif var_type.lower() == 'stantler':
                    if not (value.startswith('"') and value.endswith('"')):
                        ir_value = f'"{value}"'

            self.intercode_generator.emit(f"{name} = {ir_value}")

        # 2. Actualizar tabla SOLO si NO estamos dentro de un loop
        #    Si en_loop=True -> la variable puede cambiar N veces ->
        #    conservamos el valor estático conocido antes del loop.
        if getattr(self, 'en_loop', False):
            self.symbol_table.update_symbol(name, None)
            return

        raw = _evaluate_runtime(self, value)
        if raw is _LOOP_MODIFIED:
            return

        if raw is not None:
            real_value = _normalize_string_value(var_type, raw)
            self.symbol_table.update_symbol(name, real_value)

    return action


# ─────────────────────────────────────────────────────────────────────────────
# handle_expression_statement
# ─────────────────────────────────────────────────────────────────────────────
def _format_array_value_for_ir(self, value):
    if _is_literal(value):
        return _literal_to_ir(value)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, tuple) or _is_array_access(value):
        return _resolve_ir(self, value)
    if isinstance(value, str):
        sym = self.symbol_table.get_symbol(value)
        if sym is not None:
            return value
        return f'"{value}"'
    return str(value)


def _format_value_for_ir(self, value):
    if _is_literal(value):
        return _literal_to_ir(value)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, tuple) or _is_array_access(value) or _is_field_access(value):
        return _resolve_ir(self, value)
    if isinstance(value, str):
        sym = self.symbol_table.get_symbol(value)
        if sym is not None:
            return value
        return f'"{value}"'
    return str(value)


def _normalize_array_runtime_value(var_type, value):
    raw = value.get('value') if _is_literal(value) else value
    return _normalize_string_value(var_type, raw)


def handle_struct_declaration(self, name, fields):
    def action():
        if name in getattr(self, 'struct_types', {}):
            self.errors.encolar_error(f"Error semántico: estructura '{name}' ya declarada{_pos_suffix(self, name)}.")
            return

        allowed = {'entei', 'floatzel', 'charizar', 'boofalant', 'stantler'}
        field_map = {}
        for field_type, field_name in fields:
            if field_type not in allowed:
                self.errors.encolar_error(
                    f"Error semántico: campo '{field_name}' usa tipo no permitido '{field_type}' en estructura '{name}'."
                )
                return
            if field_name in field_map:
                self.errors.encolar_error(
                    f"Error semántico: campo duplicado '{field_name}' en estructura '{name}'."
                )
                return
            field_map[field_name] = field_type

        self.struct_types[name] = field_map
        self.intercode_generator.emit(f"struct {name}")
        for field_name, field_type in field_map.items():
            self.intercode_generator.emit(f"field {name} {field_name} {field_type}")

    return action


def handle_struct_instance_declaration(self, struct_name, var_name):
    def action():
        if struct_name not in getattr(self, 'struct_types', {}):
            self.errors.encolar_error(f"Error semántico: estructura '{struct_name}' no declarada{_pos_suffix(self, struct_name)}.")
            return

        fields = {
            field: {'type': field_type, 'value': None}
            for field, field_type in self.struct_types[struct_name].items()
        }
        actual_scope = 'global' if len(self.symbol_table.scope_stack) == 1 else 'local'
        registered = self.symbol_table.add_struct_instance(var_name, struct_name, actual_scope, fields)
        if not registered:
            self.errors.encolar_error(f"Error semántico: variable '{var_name}' ya declarada. ¿Quisiste asignar?")
            return

        self.intercode_generator.emit(f"{var_name} = new {struct_name}")

    return action


def handle_field_assignment(self, var_name, field_name, value):
    def action():
        sym = self.symbol_table.get_symbol(var_name)
        if sym is None:
            self.errors.encolar_error(f"Error semántico: variable struct '{var_name}' no declarada{_pos_suffix(self, var_name)}.")
            return
        if sym.get('kind') != 'struct_instance':
            self.errors.encolar_error(f"Error semántico: '{var_name}' no es una instancia de struct{_pos_suffix(self, var_name)}.")
            return

        struct_type = sym.get('type')
        fields = getattr(self, 'struct_types', {}).get(struct_type, {})
        if field_name not in fields:
            self.errors.encolar_error(
                f"Error semántico: campo '{field_name}' no existe en struct '{struct_type}'{_pos_suffix(self, var_name)}."
            )
            return

        field_type = fields[field_name]
        error = _check_declaration_type(self, f"{var_name}.{field_name}", field_type, value)
        if error:
            self.errors.encolar_error(error)
            return

        value_ir = _format_value_for_ir(self, value)
        if value_ir == '?':
            return
        self.intercode_generator.emit(f"{var_name}.{field_name} = {value_ir}")

        raw = _evaluate_runtime(self, value)
        if raw is not None:
            self.symbol_table.update_struct_field(
                var_name,
                field_name,
                _normalize_string_value(field_type, raw),
            )

    return action


def handle_array_declaration(self, name, var_type, size_expr, values=None):
    def action():
        size_type = _infer_type(self, size_expr)
        if size_type != 'unknown' and size_type != 'entei':
            self.errors.encolar_error(
                f"Error semántico: el tamaño del arreglo '{name}' debe ser 'entei', no '{size_type}'{_pos_suffix(self, name)}."
            )
            return

        size_value = _evaluate_runtime(self, size_expr)
        if isinstance(size_value, int) and size_value <= 0:
            self.errors.encolar_error(
                f"Error semántico: el tamaño del arreglo '{name}' debe ser mayor que 0{_pos_suffix(self, name)}."
            )
            return

        actual_scope = 'global' if len(self.symbol_table.scope_stack) == 1 else 'local'
        initial_values = None if values is None else []
        registered = self.symbol_table.add_array_symbol(
            name, var_type, actual_scope, size_value if isinstance(size_value, int) else None, initial_values
        )
        if not registered:
            self.errors.encolar_error(f"Error semántico: variable '{name}' ya declarada. ¿Quisiste asignar?")
            return

        ir_values = []
        if values is not None:
            if isinstance(size_value, int) and len(values) > size_value:
                self.errors.encolar_error(
                    f"Error semántico: arreglo '{name}' tiene tamaño {size_value}, pero recibió {len(values)} valor(es)."
                )
                return

            normalized = []
            for value in values:
                error = _check_declaration_type(self, name, var_type, value)
                if error:
                    self.errors.encolar_error(error)
                    return
                ir_val = _format_array_value_for_ir(self, value)
                if ir_val == '?':
                    return
                ir_values.append(ir_val)
                normalized.append(_normalize_array_runtime_value(var_type, value))
            self.symbol_table.update_symbol(name, normalized)

        size_ir = _resolve_ir(self, size_expr)
        if size_ir == '?':
            return
        self.intercode_generator.emit(f"array {name} size {size_ir}")
        if values is not None:
            self.intercode_generator.emit(f"array_init {name} {', '.join(ir_values)}")

    return action


def handle_array_assignment(self, name, index_expr, value):
    def action():
        sym = self.symbol_table.get_symbol(name)
        if sym is None:
            self.errors.encolar_error(f"Error semántico: arreglo '{name}' no declarado{_pos_suffix(self, name)}.")
            return
        if sym.get('kind') != 'array':
            self.errors.encolar_error(f"Error semántico: '{name}' no es un arreglo{_pos_suffix(self, name)}.")
            return

        index_type = _infer_type(self, index_expr)
        if index_type != 'unknown' and index_type != 'entei':
            self.errors.encolar_error(
                f"Error semántico: el índice de '{name}' debe ser 'entei', no '{index_type}'{_pos_suffix(self, name)}."
            )
            return

        index_value = _evaluate_runtime(self, index_expr)
        size = sym.get('size')
        if isinstance(index_value, int) and isinstance(size, int) and not (0 <= index_value < size):
            self.errors.encolar_error(
                f"Error semántico: índice {index_value} fuera de rango para arreglo '{name}' de tamaño {size}{_pos_suffix(self, name)}."
            )
            return

        error = _check_declaration_type(self, name, sym.get('type'), value)
        if error:
            self.errors.encolar_error(error)
            return

        index_ir = _resolve_ir(self, index_expr)
        value_ir = _format_array_value_for_ir(self, value)
        if index_ir == '?' or value_ir == '?':
            return

        self.intercode_generator.emit(f"{name}[{index_ir}] = {value_ir}")

        values = sym.get('value')
        if not getattr(self, 'en_loop', False) and isinstance(values, list) and isinstance(index_value, int):
            while len(values) <= index_value:
                values.append(None)
            values[index_value] = _normalize_array_runtime_value(sym.get('type'), value)
            self.symbol_table.update_symbol(name, values)

    return action


def handle_input(self, name):
    def action():
        sym = self.symbol_table.get_symbol(name)
        if sym is None:
            self.errors.encolar_error(
                f"Error semántico: variable '{name}' no declarada{_pos_suffix(self, name)}."
            )
            return

        if name in getattr(self, 'methods', {}):
            self.errors.encolar_error(
                f"Error semántico: '{name}' es una función y no puede recibir entrada con psyduck."
            )
            return

        self.symbol_table.update_symbol(name, None)
        self.intercode_generator.emit(f"cin >> {name}")

    return action


def handle_increment(self, name, delta=1):
    def action():
        sym = self.symbol_table.get_symbol(name)
        if sym is None:
            self.errors.encolar_error(
                f"Error semántico: variable '{name}' no declarada{_pos_suffix(self, name)}."
            )
            return

        var_type = sym.get('type')
        if var_type not in ('entei', 'floatzel'):
            self.errors.encolar_error(
                f"Error semántico: incremento/decremento solo permite variables numéricas. "
                f"'{name}' es '{var_type}'{_pos_suffix(self, name)}."
            )
            return

        op = '+' if delta >= 0 else '-'
        self.intercode_generator.emit(f"{name} = {name} {op} 1")

        if getattr(self, 'en_loop', False):
            self.symbol_table.update_symbol(name, None)
            return

        current = sym.get('value')
        if isinstance(current, (int, float)):
            self.symbol_table.update_symbol(name, current + delta)

    return action


def handle_expression_statement(self, expr, line=None):
    """
    Detecta si la expresión tiene efecto lateral.
    - callable  -> es llamada a función -> dejar pasar (emite IR)
    - tuple/literal -> operación aritmética suelta -> error semántico
    """
    def action():
        # Si es callable es una method_call -> tiene efecto
        if callable(expr):
            expr()
            return

        # Cualquier otra expresión suelta (aritmética, literal, variable) -> sin efecto
        line_info = f" en fila {line}, col 1" if line else ""
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
# evaluate_condition_dynamic quitar
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
        self.intercode_generator.emit(f"{temp} = {left_val} {_ir_op(op)} {right_val}")
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
        self.intercode_generator.emit(f"{temp} = {lv} {_ir_op(operator)} {rv}")
        return temp
    return action


# ─────────────────────────────────────────────────────────────────────────────
# Estructuras de control
# ─────────────────────────────────────────────────────────────────────────────
def handle_if(self, condition_expr, if_body, else_body):
    def action():
        false_label = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()

        self.intercode_generator.emit("// INICIO IF")

        cond_temp = _resolve_ir(self, condition_expr)
        if cond_temp == '?':
            return

        if not validate_boolean_expression(self, condition_expr):
            return

        self.intercode_generator.emit(f"if !({cond_temp}) goto {false_label}")

        self.symbol_table.enter_scope()
        for stmt in if_body:
            if callable(stmt):
                stmt()
        self.symbol_table.exit_scope()

        self.intercode_generator.emit(f"goto {end_label}")
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


def handle_while(self, condition_expr, body):
    def action():
        start_label = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()

        self.intercode_generator.emit("// INICIO WHILE")
        self.intercode_generator.emit(f"{start_label}:")

        cond_temp = _resolve_ir(self, condition_expr)
        if cond_temp == '?':
            return

        if not validate_boolean_expression(self, condition_expr):
            return

        self.intercode_generator.emit(f"if !({cond_temp}) goto {end_label}")

        prev_loop = getattr(self, 'en_loop', False)
        self.en_loop = True

        self.push_break_context(end_label)
        self.push_continue_context(start_label)

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt):
                stmt()
        self.symbol_table.exit_scope()

        self.pop_continue_context()
        self.pop_break_context()

        self.en_loop = prev_loop

        self.intercode_generator.emit(f"goto {start_label}")
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN WHILE")

    return action


def handle_for(self, init_stmt, condition_expr, update_stmt, body):
    def action():
        start_label = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()
        continue_label = self.intercode_generator.new_label()

        if callable(init_stmt):
            init_stmt()

        self.intercode_generator.emit("// INICIO FOR")
        self.intercode_generator.emit(f"{start_label}:")

        cond_temp = _resolve_ir(self, condition_expr)
        if cond_temp == '?':
            return

        if not validate_boolean_expression(self, condition_expr):
            return

        self.intercode_generator.emit(f"if !({cond_temp}) goto {end_label}")

        prev_loop = getattr(self, 'en_loop', False)
        self.en_loop = True

        self.push_break_context(end_label)
        self.push_continue_context(continue_label)

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt):
                stmt()
        self.symbol_table.exit_scope()

        self.intercode_generator.emit("// CONTINUE_LABEL")
        self.intercode_generator.emit(f"{continue_label}:")

        if callable(update_stmt):
            update_stmt()

        self.pop_continue_context()
        self.pop_break_context()

        self.en_loop = prev_loop

        self.intercode_generator.emit(f"goto {start_label}")
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN FOR")

    return action


def handle_do_while(self, condition_expr, body):
    def action():
        start_label = self.intercode_generator.new_label()
        end_label   = self.intercode_generator.new_label()

        self.intercode_generator.emit("// INICIO DO-WHILE")
        self.intercode_generator.emit(f"{start_label}:")

        prev_loop = getattr(self, 'en_loop', False)
        self.en_loop = True

        self.push_break_context(end_label)
        self.push_continue_context(start_label)

        self.symbol_table.enter_scope()
        for stmt in body:
            if callable(stmt):
                stmt()
        self.symbol_table.exit_scope()

        self.pop_continue_context()
        self.pop_break_context()

        self.en_loop = prev_loop

        cond_temp = _resolve_ir(self, condition_expr)
        if cond_temp == '?':
            return

        if not validate_boolean_expression(self, condition_expr):
            return

        self.intercode_generator.emit(f"if ({cond_temp}) goto {start_label}")
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// FIN DO-WHILE")

    return action


# ─────────────────────────────────────────────────────────────────────────────
# handle_method_call
# ─────────────────────────────────────────────────────────────────────────────
def _flatten_statements(stmts):
    flat = []
    for stmt in stmts or []:
        if isinstance(stmt, list):
            flat.extend(_flatten_statements(stmt))
        else:
            flat.append(stmt)
    return flat


def _validate_ref_argument(self, fn_name, index, param_type, arg):
    if _is_literal(arg) or isinstance(arg, (int, float, bool)):
        self.errors.encolar_error(
            f"Error semántico: No se puede pasar un literal como argumento ref en la función '{fn_name}'."
        )
        return False

    if isinstance(arg, tuple) or _is_array_access(arg) or _is_field_access(arg) or isinstance(arg, TypedCall) or callable(arg):
        self.errors.encolar_error(
            f"Error semántico: No se puede pasar una expresión como argumento ref en la función '{fn_name}'."
        )
        return False

    if not isinstance(arg, str):
        self.errors.encolar_error(
            f"Error semántico: No se puede pasar una expresión como argumento ref en la función '{fn_name}'."
        )
        return False

    sym = self.symbol_table.get_symbol(arg)
    if sym is None:
        self.errors.encolar_error(
            f"Error semántico: variable '{arg}' no declarada para argumento ref {index} de '{fn_name}'{_pos_suffix(self, arg)}."
        )
        return False

    if sym.get('kind') != 'variable':
        self.errors.encolar_error(
            f"Error semántico: argumento ref {index} de '{fn_name}' debe ser una variable básica, no '{sym.get('kind')}'."
        )
        return False

    if sym.get('type') != param_type:
        self.errors.encolar_error(
            f"Error semántico: argumento ref {index} de '{fn_name}' es de tipo '{sym.get('type')}', se esperaba '{param_type}'."
        )
        return False

    return True


def _evaluate_simple_function_call(self, name, args):
    methods = getattr(self, 'methods', {})
    if name not in methods:
        return None
    if name in getattr(self, 'partial_eval_call_stack', []):
        return None

    method_info = methods.get(name, {})
    if not isinstance(method_info, dict):
        return None
    if method_info.get('return_type') == 'gardevoir':
        return None

    params = method_info.get('params', []) or []
    if len(params) != len(args):
        return None

    env = {}
    for param, arg in zip(params, args):
        param_type, param_name, is_ref = _param_parts(param)
        if is_ref:
            return None
        value = _evaluate_runtime(self, arg)
        if value is None or value is _LOOP_MODIFIED:
            return None
        arg_type = _infer_type(self, arg)
        if arg_type != 'unknown' and arg_type != param_type:
            numeric = {'entei', 'floatzel'}
            if not (arg_type in numeric and param_type in numeric):
                return None
        env[param_name] = value

    body = _flatten_statements(method_info.get('body', []))
    if any(getattr(stmt, '_stmt_kind', None) == 'loop' for stmt in body):
        return None

    return_stmts = [stmt for stmt in body if getattr(stmt, '_stmt_kind', None) == 'return']
    if len(return_stmts) != 1 or len(body) != 1:
        return None

    return_expr = getattr(return_stmts[0], '_return_value', None)
    self.partial_eval_call_stack.append(name)
    self.partial_eval_env_stack.append(env)
    try:
        return _evaluate_runtime(self, return_expr)
    finally:
        self.partial_eval_env_stack.pop()
        self.partial_eval_call_stack.pop()


def handle_method_call(self, name, args=None):
    args = args or []
    print(f" [CALL] Preparando llamada a funcion '{name}' con argumentos: {args}")

    def call_with_scope():
        if name not in self.methods:
            self.errors.encolar_error(f"Error semantico: funcion '{name}' no definida.")
            return None

        expected_params = self.methods[name].get('params', [])
        if len(args) != len(expected_params):
            self.errors.encolar_error(
                f"Error semantico: funcion '{name}' espera {len(expected_params)} "
                f"argumento(s), pero se pasaron {len(args)}."
            )
            return None

        arg_ir_names = []
        for i, arg in enumerate(args):
            param_type, _, is_ref = _param_parts(expected_params[i])
            if is_ref and not _validate_ref_argument(self, name, i + 1, param_type, arg):
                return None

            arg_type = _infer_type(self, arg)
            if not is_ref and arg_type != 'unknown' and arg_type != param_type:
                numeric = {'entei', 'floatzel'}
                if not (arg_type in numeric and param_type in numeric):
                    self.errors.encolar_error(
                        f"Error semantico: argumento {i+1} de '{name}' "
                        f"es de tipo '{arg_type}', se esperaba '{param_type}'."
                    )
                    return None

            ir_name = _resolve_ir(self, arg)
            if ir_name == '?':
                return None
            arg_ir_names.append(ir_name)

        for i, arg_name in enumerate(arg_ir_names):
            _, _, is_ref = _param_parts(expected_params[i])
            op = 'param_ref' if is_ref else 'param'
            self.intercode_generator.emit(f"{op} {arg_name}")

        args_str = ', '.join(arg_ir_names)
        ret_type = self.methods.get(name, {}).get('return_type', 'unknown')
        if ret_type == 'gardevoir':
            self.intercode_generator.emit(f"call {name}({args_str})")
            return None

        temp = self.intercode_generator.new_temp()
        self.intercode_generator.emit(f"{temp} = call {name}({args_str})")
        return temp

    ret_type = self.methods.get(name, {}).get('return_type', 'unknown')
    return TypedCall(
        call_with_scope,
        ret_type,
        name,
        runtime_fn=lambda: _evaluate_simple_function_call(self, name, args),
    )


def handle_method_declaration(self, name, body):
    def flatten(stmts):
        flat = []
        for s in stmts:
            if isinstance(s, list):
                flat.extend(flatten(s))
            else:
                flat.append(s)
        return flat

    def action():
        flat_body = flatten(body)
        if name in self.methods and isinstance(self.methods[name], dict):
            self.methods[name]['body'] = flat_body

        method_info = self.methods.get(name, {})
        ret_type = method_info.get('return_type', 'gardevoir') if isinstance(method_info, dict) else 'gardevoir'
        params   = method_info.get('params', []) if isinstance(method_info, dict) else []

        self.current_function = name
        self.current_return_type = ret_type
        self.current_function_has_return = False

        params_str = ', '.join(
            f"{'ref ' if is_ref else ''}{param_type} {param_name}"
            for param_type, param_name, is_ref in (_param_parts(p) for p in params)
        )
        self.intercode_generator.emit(f"function {ret_type}  {name}({params_str}):")

        self.symbol_table.enter_scope()
        print(f" [FUNC]  Función '{name}' registrada con return_type='{ret_type}' y params={params}")
        self.en_funcion = True

        for param_type, param_name, _ in (_param_parts(p) for p in params):
            self.symbol_table.add_symbol(param_name, param_type, 'local', None)
            print(f" [PARAM]  Variable '{param_name}' ({param_type}) registrada")

        for stmt in flat_body:
            if callable(stmt):
                stmt()

        if ret_type != 'gardevoir' and not self.current_function_has_return:
            self.errors.encolar_error(
                f"Error semántico: la función '{name}' debe retornar un valor de tipo '{ret_type}'."
            )

        self.en_funcion = False
        self.symbol_table.exit_scope()
        print(f" [END FUNC] Fin de función '{name}'")
        self.intercode_generator.emit("end")

        self.current_function = None
        self.current_return_type = None
        self.current_function_has_return = False

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

        end_label = self.intercode_generator.new_label()
        self.push_break_context(end_label)

        self.intercode_generator.emit(f"// SWITCH_START {var_name}")
        for val, case_body in processed_cases:
            self.intercode_generator.emit(f"// CASE {repr(val)}")
            for stmt in case_body:
                if callable(stmt):
                    stmt()

        self.intercode_generator.emit("// DEFAULT")
        if default_body:
            for stmt in default_body:
                if callable(stmt):
                    stmt()

        self.pop_break_context()
        self.intercode_generator.emit(f"{end_label}:")
        self.intercode_generator.emit("// SWITCH_END")

    return action

def _evaluate_static(self, expr):
    if isinstance(expr, tuple) and len(expr) == 3:
        l, op, r = expr

        l_val = _evaluate_static(self, l)
        r_val = _evaluate_static(self, r)

        if l_val is None or r_val is None:
            return None

        if op == 'ma': return l_val > r_val
        if op == 'me': return l_val < r_val
        if op == 'ig': return l_val == r_val
        if op == 'ni': return l_val != r_val
        if op == 'mai': return l_val >= r_val
        if op == 'mei': return l_val <= r_val

        if op in ['su', '+']: return l_val + r_val
        if op in ['re', '-']: return l_val - r_val
        if op in ['mu', '*']: return l_val * r_val
        if op in ['di', '/']: return l_val / r_val

    elif isinstance(expr, (int, float, bool)):
        return expr

    elif isinstance(expr, str):
        symbol = self.symbol_table.get_symbol(expr)
        if symbol:
            return symbol.get('value')

    return None
