class ccodeGen:
    """
    Generador de código C++ para el compilador Pokémon.
    Recibe el código intermedio (lista de strings) y la tabla de símbolos.
    """

    TIPOS = {
        'entei':     'int',
        'floatzel':  'float',
        'charizar':  'char',
        'boofalant': 'bool',
        'stantler':  'string',
        'gardevoir': 'void',
    }

    def __init__(self, ir, symbol_table=None):
        self.ir = ir
        self.symbol_table = symbol_table or {}
        self.cpp_code = []
        self.indent_level = 2
        self.temp_conditions = {}
        self.label_to_index = {}
        self._next_is_while  = False   # flag: el próximo if !( es un while
        self._next_is_for    = False   # flag: el próximo if !( es un for
        self._next_is_dowhile = False  # flag: el próximo if ( es un do-while

        for idx, line in enumerate(self.ir):
            stripped = line.strip()
            if stripped.endswith(':') and not stripped.startswith('//'):
                label = stripped[:-1].strip()
                self.label_to_index[label] = idx

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────

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

    def _translate_expr(self, expr):
        expr = expr.strip()

        if expr.startswith('pikachu(') and expr.endswith(')'):
            inner = expr[len('pikachu('):-1].strip()
            if not inner.startswith('"') and not inner.replace('.', '', 1).isdigit():
                sym = self.symbol_table.get(inner, {})
                if sym.get('type', '').lower() == 'stantler':
                    inner = f'"{inner}"'
            return f'cout << {inner} << endl'

        if expr.startswith('call '):
            return expr.replace('call ', '', 1).strip() + '()'

        if expr.startswith('raikou '):
            val = expr[len('raikou '):].strip()
            return f'return {val}'

        if '=' in expr and not expr.startswith('if'):
            left, right = map(str.strip, expr.split('=', 1))
            right = self._add_string_quotes(left, right)
            return f'{left} = {right}'

        return expr

    # ─────────────────────────────────────────
    # Generación principal
    # ─────────────────────────────────────────

    def generate(self):
        open_blocks = []
        in_function = False

        # ── Paso 1: extraer temporales de condición ──
        filtered_ir = []
        for line in self.ir:
            stripped = line.strip()
            if ('=' in stripped
                    and not stripped.startswith('if')
                    and not stripped.startswith('goto')
                    and not stripped.endswith(':')
                    and not stripped.startswith('//')):
                left, right = map(str.strip, stripped.split('=', 1))
                rel_ops = ['<', '>', '==', '!=', '<=', '>=']
                if left.startswith('t') and left[1:].isdigit() and any(op in right for op in rel_ops):
                    self.temp_conditions[left] = right
                    continue
            filtered_ir.append(stripped)

        # ── Cabecera ──
        self.cpp_code = [
            '#include <iostream>',
            '#include <string>',
            'using namespace std;',
            '',
            'int main() {',
        ]

        # ── Declarar variables desde tabla de símbolos ──
        for var_name, info in sorted(self.symbol_table.items()):
            cpp_t = self.TIPOS.get(info.get('type', '').lower(), 'auto')
            self.cpp_code.append(f'    {cpp_t} {var_name};')

        self.cpp_code.append('')

        # ── Paso 2: recorrer IR filtrado ──
        i = 0
        while i < len(filtered_ir):
            line = filtered_ir[i]

            # ── Comentarios de estructura ──
            if line.startswith('//'):
                tag = line.strip()

                if tag == '// INICIO IF':
                    self._next_is_while  = False
                    self._next_is_for    = False
                    i += 1
                    continue

                elif tag == '// FIN IF':
                    if open_blocks:
                        block = open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}}  // fin {block}')
                    i += 1
                    continue

                elif tag == '// ELSE':
                    if open_blocks and open_blocks[-1] == 'if':
                        open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}} else {{')
                        self.indent_level += 1
                        open_blocks.append('else')
                    i += 1
                    continue

                elif tag == '// INICIO WHILE':
                    self._next_is_while = True
                    self._next_is_for   = False
                    i += 1
                    continue

                elif tag == '// FIN WHILE':
                    if open_blocks:
                        open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}}  // fin while')
                    self._next_is_while = False
                    i += 1
                    continue

                elif tag == '// INICIO FOR':
                    self._next_is_for   = True
                    self._next_is_while = False
                    i += 1
                    continue

                elif tag == '// FIN FOR':
                    if open_blocks:
                        open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}}  // fin for')
                    self._next_is_for = False
                    i += 1
                    continue

                elif tag.startswith('// SWITCH_START'):
                    var = tag.split('SWITCH_START')[1].strip()
                    self.cpp_code.append(f'{self._indent()}switch ({var}) {{')
                    self.indent_level += 1
                    open_blocks.append('switch')
                    i += 1
                    continue

                elif tag.startswith('// CASE'):
                    val = tag.split('CASE')[1].strip()
                    self.indent_level -= 1
                    self.cpp_code.append(f'{self._indent()}case {val}:')
                    self.indent_level += 1
                    i += 1
                    continue

                elif tag == '// BREAK':
                    self.cpp_code.append(f'{self._indent()}break;')
                    i += 1
                    continue

                elif tag == '// DEFAULT':
                    self.indent_level -= 1
                    self.cpp_code.append(f'{self._indent()}default:')
                    self.indent_level += 1
                    i += 1
                    continue

                elif tag == '// SWITCH_END':
                    if open_blocks and open_blocks[-1] == 'switch':
                        open_blocks.pop()
                        self.indent_level -= 1
                        self.cpp_code.append(f'{self._indent()}}}  // fin switch')
                    i += 1
                    continue

                elif tag == '//INICIO DO-WHILE':
                    self.cpp_code.append(f'{self._indent()}do {{')
                    self.indent_level += 1
                    open_blocks.append('do')
                    self._next_is_dowhile = True
                    i += 1
                    continue

                elif tag == '//FIN DO-WHILE':
                    self._next_is_dowhile = False
                    i += 1
                    continue

                else:
                    i += 1
                    continue

            # ── Etiquetas — ignorar ──
            if line.endswith(':') and not line.startswith('if'):
                i += 1
                continue

            # ── Declaración de función ──
            if line.startswith('function ') and line.endswith(':'):
                fname    = line[len('function '):-1].strip()
                ret_type = self._cpp_type(fname) or 'void'
                self.cpp_code.append('    return 0;')
                self.cpp_code.append('}')
                self.cpp_code.append('')
                self.cpp_code.append(f'{ret_type} {fname}() {{')
                self.indent_level = 1
                open_blocks.append('function')
                in_function = True
                i += 1
                continue

            # ── end (cierre de función) ──
            if line in ('end', 'end;'):
                if open_blocks and open_blocks[-1] == 'function':
                    open_blocks.pop()
                    self.indent_level -= 1
                    self.cpp_code.append(f'}}  // fin función')
                    in_function = False
                i += 1
                continue

            # ── if !(cond) goto label ──
            if line.startswith('if !('):
                cond_raw  = line[5:line.index(') goto')].strip()
                target    = line.split('goto')[1].strip()
                cond_real = self.temp_conditions.get(cond_raw, cond_raw)

                if self._next_is_while:
                    # Es un while — confirmado por // INICIO WHILE
                    self.cpp_code.append(f'{self._indent()}while ({cond_real}) {{')
                    open_blocks.append('while')
                    self._next_is_while = False

                elif self._next_is_for:
                    # Es un for — confirmado por // INICIO FOR
                    self.cpp_code.append(f'{self._indent()}while ({cond_real}) {{')
                    open_blocks.append('for')
                    self._next_is_for = False

                else:
                    # Es un if — usar dirección del goto como fallback
                    target_idx = self.label_to_index.get(target, i + 1)
                    if target_idx > i:
                        self.cpp_code.append(f'{self._indent()}if ({cond_real}) {{')
                        open_blocks.append('if')
                    else:
                        self.cpp_code.append(f'{self._indent()}while ({cond_real}) {{')
                        open_blocks.append('while')

                self.indent_level += 1
                i += 1
                continue

            # ── if (cond) goto label (do-while) ──
            if line.startswith('if ('):
                cond_raw  = line[4:line.index(') goto')].strip()
                cond_real = self.temp_conditions.get(cond_raw, cond_raw)
                if open_blocks and open_blocks[-1] == 'do':
                    open_blocks.pop()
                    self.indent_level -= 1
                    self.cpp_code.append(f'{self._indent()}}} while ({cond_real});')
                i += 1
                continue

            # ── goto ──
            if line.startswith('goto'):
                target     = line.split('goto')[1].strip()
                target_idx = self.label_to_index.get(target, i + 1)
                if target_idx < i and open_blocks:
                    block = open_blocks.pop()
                    self.indent_level -= 1
                    self.cpp_code.append(f'{self._indent()}}}  // fin {block}')
                i += 1
                continue

            # ── cout (pikachu ya traducido en IR) ──
            if line.startswith('cout'):
                self.cpp_code.append(f'{self._indent()}{line};')
                i += 1
                continue

            # ── Asignaciones ──
            if '=' in line and not line.startswith('if'):
                left, right = map(str.strip, line.split('=', 1))

                # Saltar temporales de condición
                if left.startswith('t') and left[1:].isdigit() and left in self.temp_conditions:
                    i += 1
                    continue

                # Fix shadowing: si tipo global es string pero el valor es numérico
                global_info = self.symbol_table.get(left, {})
                global_cpp  = self.TIPOS.get(global_info.get('type', '').lower(), 'auto')
                is_numeric  = False
                try:
                    float(right.strip('"'))
                    is_numeric = True
                except ValueError:
                    pass

                if global_cpp == 'string' and is_numeric and not right.startswith('"'):
                    # Shadowing — renombrar variable local
                    self.cpp_code.append(f'{self._indent()}int {left}_local = {right};')
                    i += 1
                    continue

                right = self._add_string_quotes(left, right)
                self.cpp_code.append(f'{self._indent()}{left} = {right};')
                i += 1
                continue

            # ── call función ──
            if line.startswith('call ') or (line.endswith('()') and '=' not in line):
                self.cpp_code.append(f'{self._indent()}{self._translate_expr(line)};')
                i += 1
                continue

            # ── raikou (return) ──
            if line.startswith('raikou '):
                val = line[len('raikou '):].strip()
                self.cpp_code.append(f'{self._indent()}return {val};')
                i += 1
                continue

            # ── Línea genérica ──
            translated = self._translate_expr(line)
            if translated:
                self.cpp_code.append(f'{self._indent()}{translated};')
            i += 1

        # ── Cerrar bloques abiertos ──
        while open_blocks:
            open_blocks.pop()
            self.indent_level -= 1
            self.cpp_code.append(f'{self._indent()}}}')

        # ── Cerrar main ──
        self.cpp_code.append('    return 0;')
        self.cpp_code.append('}')

    def get_cpp_code(self):
        return '\n'.join(self.cpp_code)