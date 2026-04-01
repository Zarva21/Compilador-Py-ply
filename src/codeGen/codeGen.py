class ccodeGen:
    TIPOS = {
        'entei':     'int',
        'floatzel':  'float',
        'charizar':  'char',
        'boofalant': 'bool',
        'stantler':  'string',
        'gardevoir': 'void',
    }

    def __init__(self, ir, symbol_table=None):
        self.ir               = ir
        self.symbol_table     = symbol_table or {}
        self.cpp_code         = []
        self.indent_level     = 2
        self.temp_conditions  = {}
        self.label_to_index   = {}
        self._next_is_while   = False
        self._next_is_for     = False
        self._next_is_dowhile = False
        self._declared_vars   = set()  # variables ya declaradas en main

        # FIX 3: estado de variables locales por función
        self._func_params = set()
        self._func_locals = set()

        for idx, line in enumerate(self.ir):
            stripped = line.strip()
            if stripped.endswith(':') and not stripped.startswith('//'):
                label = stripped[:-1].strip()
                self.label_to_index[label] = idx

    def _indent(self):
        return '    ' * self.indent_level

    def _cpp_type(self, var_name):
        info = self.symbol_table.get(var_name, {})
        tipo = info.get('type', 'auto')
        return self.TIPOS.get(tipo.lower(), 'auto')

    def _add_string_quotes(self, var_name, right):
        cpp_t = self._cpp_type(var_name)
        if cpp_t == 'string' and not right.startswith('"'):
            try:
                float(right)
            except ValueError:
                return f'"{right}"'
        return right

    def _parse_function_header(self, line):
        """Parsea 'function entei cuadrado(entei n):' → (ret_cpp, fname, params_cpp)"""
        content = line[len('function '):]
        if content.endswith(':'):
            content = content[:-1].strip()

        parts = content.split(None, 1)
        if len(parts) < 2:
            return None

        ret_raw = parts[0].strip()
        rest    = parts[1].strip()
        ret_cpp = self.TIPOS.get(ret_raw.lower(), 'void')

        paren_open  = rest.find('(')
        paren_close = rest.rfind(')')
        if paren_open == -1:
            return None

        fname      = rest[:paren_open].strip()
        params_raw = rest[paren_open+1:paren_close].strip()

        params_cpp = ''
        if params_raw:
            param_list = []
            for param in params_raw.split(','):
                param   = param.strip()
                p_parts = param.split()
                if len(p_parts) == 2:
                    p_cpp = self.TIPOS.get(p_parts[0].lower(), 'auto')
                    param_list.append(f'{p_cpp} {p_parts[1]}')
                else:
                    param_list.append(param)
            params_cpp = ', '.join(param_list)

        return ret_cpp, fname, params_cpp

    def generate(self):
        # ── Separar IR en funciones y main ──
        func_ir = []
        main_ir = []
        in_func = False

        for line in self.ir:
            stripped = line.strip()
            if stripped.startswith('function ') and stripped.endswith(':'):
                in_func = True
                func_ir.append(stripped)
            elif stripped == 'end' and in_func:
                func_ir.append(stripped)
                in_func = False
            elif in_func:
                func_ir.append(stripped)
            else:
                main_ir.append(stripped)

        # ── Extraer temporales de condición del main ──
        filtered_main = []
        for line in main_ir:
            if ('=' in line
                    and not line.startswith('if')
                    and not line.startswith('goto')
                    and not line.endswith(':')
                    and not line.startswith('//')):
                left, right = map(str.strip, line.split('=', 1))
                rel_ops = ['<', '>', '==', '!=', '<=', '>=']
                if left.startswith('t') and left[1:].isdigit() and any(op in right for op in rel_ops):
                    self.temp_conditions[left] = right
                    continue
            filtered_main.append(line)

        # ── También extraer temporales de condición de funciones ──
        for line in func_ir:
            if ('=' in line
                    and not line.startswith('if')
                    and not line.startswith('goto')
                    and not line.endswith(':')
                    and not line.startswith('//')):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    left, right = map(str.strip, parts)
                    rel_ops = ['<', '>', '==', '!=', '<=', '>=']
                    if left.startswith('t') and left[1:].isdigit() and any(op in right for op in rel_ops):
                        self.temp_conditions[left] = right

        # ── Generar funciones C++ ──
        func_cpp = self._generate_functions(func_ir)

        # ── Cabecera ──
        self.cpp_code = [
            '#include <iostream>',
            '#include <string>',
            'using namespace std;',
            '',
        ]

        if func_cpp:
            self.cpp_code.extend(func_cpp)
            self.cpp_code.append('')

        # ── main ──
        self.cpp_code.append('int main() {')

        # Declarar variables globales (solo una vez)
        for var_name, info in sorted(self.symbol_table.items()):
            cpp_t = self.TIPOS.get(info.get('type', '').lower(), 'auto')
            self.cpp_code.append(f'    {cpp_t} {var_name};')
            self._declared_vars.add(var_name)
        self.cpp_code.append('')

        # ── Procesar main IR ──
        open_blocks = []
        self._process_ir(filtered_main, open_blocks)

        while open_blocks:
            open_blocks.pop()
            self.indent_level -= 1
            self.cpp_code.append(f'{self._indent()}}}')

        self.cpp_code.append('    return 0;')
        self.cpp_code.append('}')

    def _generate_functions(self, func_ir):
        result = []
        i      = 0
        indent = 1
        func_temp_conditions = {}

        # Pre-extraer temporales de condición de funciones
        for line in func_ir:
            if ('=' in line
                    and not line.startswith('if')
                    and not line.startswith('goto')
                    and not line.endswith(':')
                    and not line.startswith('//')):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    left, right = map(str.strip, parts)
                    rel_ops = ['<', '>', '==', '!=', '<=', '>=']
                    if left.startswith('t') and left[1:].isdigit() and any(op in right for op in rel_ops):
                        func_temp_conditions[left] = right

        while i < len(func_ir):
            line = func_ir[i]

            if line.startswith('function ') and line.endswith(':'):
                parsed = self._parse_function_header(line)
                if parsed:
                    ret_cpp, fname, params_cpp = parsed
                    result.append(f'{ret_cpp} {fname}({params_cpp}) {{')
                    # FIX 3: resetear tracking de parámetros y locales por función
                    self._func_params = set()
                    self._func_locals = set()
                    if params_cpp:
                        for param in params_cpp.split(','):
                            param = param.strip()
                            if param:
                                param_name = param.split()[-1]
                                self._func_params.add(param_name)
                else:
                    fname = line[len('function '):-1].strip()
                    result.append(f'void {fname}() {{')
                    self._func_params = set()
                    self._func_locals = set()
                indent = 1
                i += 1
                continue

            if line == 'end':
                result.append('}')
                result.append('')
                # FIX 3: limpiar al salir de función
                self._func_params = set()
                self._func_locals = set()
                i += 1
                continue

            # Saltar temporales de condición
            if ('=' in line
                    and not line.startswith('if')
                    and not line.startswith('goto')
                    and not line.endswith(':')
                    and not line.startswith('//')):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    left, right = map(str.strip, parts)
                    rel_ops = ['<', '>', '==', '!=', '<=', '>=']
                    if left.startswith('t') and left[1:].isdigit() and any(op in right for op in rel_ops):
                        i += 1
                        continue

            prefix = '    ' * indent
            translated = self._translate_func_line(line, func_temp_conditions)
            if translated is not None:
                result.append(f'{prefix}{translated}')
            i += 1

        return result

    def _translate_func_line(self, line, temp_conds):
        if line.endswith(':') and not line.startswith('if'):
            return None
        if line.startswith('//') or line.startswith('param '):
            return None
        if line.startswith('goto'):
            return None
        if line.startswith('raikou '):
            return f'return {line[len("raikou "):].strip()};'
        if line.startswith('cout'):
            return f'{line};'
        if '= call ' in line:
            left, right = line.split('= call ', 1)
            return f'auto {left.strip()} = {right.strip()};'
        if line.startswith('call '):
            return f'{line[5:].strip()};'
        if line.startswith('if !('):
            cond_raw  = line[5:line.index(') goto')].strip()
            cond_real = temp_conds.get(cond_raw, cond_raw)
            return f'if ({cond_real}) {{'
        if '=' in line and not line.startswith('if'):
            left, right = map(str.strip, line.split('=', 1))

            # Saltar temporales de condición ya procesados
            if left.startswith('t') and left[1:].isdigit() and left in temp_conds:
                return None

            # Temporales de expresión → auto
            if left.startswith('t') and left[1:].isdigit():
                return f'auto {left} = {right};'

            # FIX 3 + 4: declarar variable local si es nueva en esta función
            if left not in self._func_params and left not in self._func_locals:
                self._func_locals.add(left)
                # FIX 4: intentar inferir tipo desde symbol_table (globales),
                # si no se encuentra usar 'auto' — válido en C++11 y superior
                cpp_type = self._cpp_type(left)
                return f'{cpp_type} {left} = {right};'

            # Variable ya declarada → solo asignar
            return f'{left} = {right};'

        return f'{line};'

    def _process_ir(self, filtered_ir, open_blocks):
        i = 0
        while i < len(filtered_ir):
            line = filtered_ir[i]

            if line.startswith('//'):
                tag = line.strip()

                if tag == '// INICIO IF':
                    self._next_is_while = False
                    self._next_is_for   = False
                    i += 1; continue

                elif tag == '// FIN IF':
                    if open_blocks:
                        block = open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}}  // fin {block}')
                    i += 1; continue

                elif tag == '// ELSE':
                    if open_blocks and open_blocks[-1] == 'if':
                        open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}} else {{')
                        self.indent_level += 1
                        open_blocks.append('else')
                    i += 1; continue

                elif tag == '// INICIO WHILE':
                    self._next_is_while = True
                    self._next_is_for   = False
                    i += 1; continue

                elif tag == '// FIN WHILE':
                    if open_blocks:
                        open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}}  // fin while')
                    self._next_is_while = False
                    i += 1; continue

                elif tag == '// INICIO FOR':
                    self._next_is_for   = True
                    self._next_is_while = False
                    i += 1; continue

                elif tag == '// FIN FOR':
                    if open_blocks:
                        open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}}  // fin for')
                    self._next_is_for = False
                    i += 1; continue

                elif tag.startswith('// SWITCH_START'):
                    var = tag.split('SWITCH_START')[1].strip()
                    self.cpp_code.append(f'{self._indent()}switch ({var}) {{')
                    self.indent_level += 1
                    open_blocks.append('switch')
                    i += 1; continue

                elif tag.startswith('// CASE'):
                    val = tag.split('CASE')[1].strip()
                    self.indent_level -= 1
                    self.cpp_code.append(f'{self._indent()}case {val}:')
                    self.indent_level += 1
                    i += 1; continue

                elif tag == '// BREAK':
                    self.cpp_code.append(f'{self._indent()}break;')
                    i += 1; continue

                elif tag == '// DEFAULT':
                    self.indent_level -= 1
                    self.cpp_code.append(f'{self._indent()}default:')
                    self.indent_level += 1
                    i += 1; continue

                elif tag == '// SWITCH_END':
                    if open_blocks and open_blocks[-1] == 'switch':
                        open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}}  // fin switch')
                    i += 1; continue

                elif tag == '//INICIO DO-WHILE':
                    self.cpp_code.append(f'{self._indent()}do {{')
                    self.indent_level += 1
                    open_blocks.append('do')
                    i += 1; continue

                elif tag == '//FIN DO-WHILE':
                    i += 1; continue

                else:
                    i += 1; continue

            # Etiquetas
            if line.endswith(':') and not line.startswith('if'):
                i += 1; continue

            # param
            if line.startswith('param '):
                i += 1; continue

            # if !(cond) goto
            if line.startswith('if !('):
                cond_raw  = line[5:line.index(') goto')].strip()
                target    = line.split('goto')[1].strip()
                cond_real = self.temp_conditions.get(cond_raw, cond_raw)

                if self._next_is_while:
                    self.cpp_code.append(f'{self._indent()}while ({cond_real}) {{')
                    open_blocks.append('while')
                    self._next_is_while = False
                elif self._next_is_for:
                    self.cpp_code.append(f'{self._indent()}while ({cond_real}) {{')
                    open_blocks.append('for')
                    self._next_is_for = False
                else:
                    target_idx = self.label_to_index.get(target, i + 1)
                    if target_idx > i:
                        self.cpp_code.append(f'{self._indent()}if ({cond_real}) {{')
                        open_blocks.append('if')
                    else:
                        self.cpp_code.append(f'{self._indent()}while ({cond_real}) {{')
                        open_blocks.append('while')
                self.indent_level += 1
                i += 1; continue

            # if (cond) goto (do-while)
            if line.startswith('if ('):
                cond_raw  = line[4:line.index(') goto')].strip()
                cond_real = self.temp_conditions.get(cond_raw, cond_raw)
                if open_blocks and open_blocks[-1] == 'do':
                    open_blocks.pop()
                    self.indent_level -= 1
                    self.cpp_code.append(f'{self._indent()}}} while ({cond_real});')
                i += 1; continue

            # goto
            if line.startswith('goto'):
                target     = line.split('goto')[1].strip()
                target_idx = self.label_to_index.get(target, i + 1)
                if target_idx < i and open_blocks:
                    block = open_blocks.pop()
                    self.indent_level -= 1
                    self.cpp_code.append(f'{self._indent()}}}  // fin {block}')
                i += 1; continue

            # cout
            if line.startswith('cout'):
                self.cpp_code.append(f'{self._indent()}{line};')
                i += 1; continue

            # raikou
            if line.startswith('raikou '):
                val = line[len('raikou '):].strip()
                self.cpp_code.append(f'{self._indent()}return {val};')
                i += 1; continue

            # call con asignación — NO redeclarar si ya existe
            if '= call ' in line:
                left, right = line.split('= call ', 1)
                left  = left.strip()
                right = right.strip()
                if left in self._declared_vars:
                    self.cpp_code.append(f'{self._indent()}{left} = {right};')
                else:
                    self.cpp_code.append(f'{self._indent()}auto {left} = {right};')
                i += 1; continue

            # call sin asignación
            if line.startswith('call '):
                self.cpp_code.append(f'{self._indent()}{line[5:].strip()};')
                i += 1; continue

            # Asignaciones
            if '=' in line and not line.startswith('if'):
                left, right = map(str.strip, line.split('=', 1))

                # Saltar temporales de condición
                if left.startswith('t') and left[1:].isdigit() and left in self.temp_conditions:
                    i += 1; continue

                # Temporales de expresión → auto
                if left.startswith('t') and left[1:].isdigit():
                    self.cpp_code.append(f'{self._indent()}auto {left} = {right};')
                    i += 1; continue

                # Variables normales
                right = self._add_string_quotes(left, right)
                self.cpp_code.append(f'{self._indent()}{left} = {right};')
                i += 1; continue

            # Línea genérica
            self.cpp_code.append(f'{self._indent()}{line};')
            i += 1

    def get_cpp_code(self):
        return '\n'.join(self.cpp_code)