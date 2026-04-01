class Optimize:
    def __init__(self, ir):
        self.ir = ir

    def remove_end_statements(self):
        # NO eliminar 'end' — son cierres de función necesarios
        pass

    def remove_redundant_temporaries(self):
        """
        Colapsa patrones:
            t0 = a + b
            x  = t0
        en:
            x = a + b

        NUNCA colapsar si la línea contiene 'call' — las llamadas
        deben mantenerse separadas para que codegen las procese bien.
        """
        optimized_ir = []
        i = 0
        while i < len(self.ir):
            line      = self.ir[i].strip()
            next_line = self.ir[i + 1].strip() if i + 1 < len(self.ir) else ''

            if '=' in line and '=' in next_line:
                left1, expr1 = line.split('=', 1)
                left2, expr2 = next_line.split('=', 1)

                is_call      = 'call ' in expr1          # t0 = call func(...)
                is_used_next = expr2.strip() == left1.strip()

                if is_used_next and not is_call:
                    # colapsar: reemplazar t0 con la expresión directamente
                    optimized_ir.append(f"{left2.strip()} = {expr1.strip()}")
                    i += 2
                    continue

            optimized_ir.append(line)
            i += 1
        self.ir = optimized_ir

    def simplify_trivial_operations(self):
        optimized_ir = []
        for line in self.ir:
            if '+ 0' in line or '- 0' in line:
                left, expr = line.split('=', 1)
                parts = expr.strip().split()
                if len(parts) == 3 and parts[2] == '0':
                    optimized_ir.append(f"{left.strip()} = {parts[0]}")
                    continue
            if '* 1' in line or '/ 1' in line:
                left, expr = line.split('=', 1)
                parts = expr.strip().split()
                if len(parts) == 3 and parts[2] == '1':
                    optimized_ir.append(f"{left.strip()} = {parts[0]}")
                    continue
            optimized_ir.append(line)
        self.ir = optimized_ir

    def optimize_conditionals(self):
        optimized_ir = []
        i = 0
        while i < len(self.ir):
            if i + 2 < len(self.ir):
                line_if    = self.ir[i].strip()
                line_goto  = self.ir[i + 1].strip()
                line_label = self.ir[i + 2].strip()

                if (line_if.startswith('if')
                        and line_goto.startswith('goto')
                        and line_label.endswith(':')):
                    cond        = line_if[2:].split('goto')[0].strip()
                    false_label = line_goto.split('goto')[1].strip()
                    optimized_ir.append(f"if !({cond}) goto {false_label}")
                    i += 2
                    continue

            optimized_ir.append(self.ir[i])
            i += 1
        self.ir = optimized_ir

    def remove_unreachable_labels(self):
        optimized_ir  = []
        last_was_goto = False
        for line in self.ir:
            if last_was_goto and line.endswith(':'):
                continue
            optimized_ir.append(line)
            last_was_goto = line.strip().startswith('goto')
        self.ir = optimized_ir

    def optimize_goto_chains(self):
        label_to_target = {}
        for i in range(len(self.ir) - 1):
            line      = self.ir[i].strip()
            next_line = self.ir[i + 1].strip()
            if line.endswith(':') and next_line.startswith('goto'):
                label               = line[:-1].strip()
                target              = next_line.split('goto')[1].strip()
                label_to_target[label] = target

        optimized_ir = []
        for line in self.ir:
            if line.startswith('goto'):
                dest = line.split('goto')[1].strip()
                while dest in label_to_target:
                    dest = label_to_target[dest]
                optimized_ir.append(f"goto {dest}")
            else:
                optimized_ir.append(line)
        self.ir = optimized_ir

    def optimize_redundant_for_conditions(self):
        optimized_ir = []
        i = 0
        while i < len(self.ir):
            if (i + 5 < len(self.ir)
                    and '=' in self.ir[i]
                    and self.ir[i + 1].strip().startswith('if !(')
                    and self.ir[i + 2].strip().endswith(':')
                    and '=' in self.ir[i + 3]
                    and self.ir[i + 4].strip().startswith('if !(')
                    and self.ir[i + 5].strip().startswith('goto')):

                first_temp  = self.ir[i].split('=')[0].strip()
                second_temp = self.ir[i + 3].split('=')[0].strip()
                first_goto  = self.ir[i + 1].split('goto')[1].strip()
                second_goto = self.ir[i + 4].split('goto')[1].strip()
                loop_back   = self.ir[i + 5].split('goto')[1].strip()

                if (first_goto == second_goto
                        and loop_back == self.ir[i + 2].strip()[:-1]):
                    optimized_ir.extend(self.ir[i:i + 3])
                    optimized_ir.append(self.ir[i + 3 + 1])
                    optimized_ir.append(f"goto {loop_back}")
                    i += 6
                    continue

            optimized_ir.append(self.ir[i])
            i += 1
        self.ir = optimized_ir

    def remove_unused_temporaries(self):
        """
        Elimina temporales aritméticos que no se usan en ninguna otra línea.

        REGLA CRÍTICA: nunca eliminar líneas que contengan 'call'.
        Las llamadas a función tienen efectos secundarios (prints, asignaciones,
        modificaciones de estado) aunque su resultado temporal no se use después.
        """
        # Recopilar todos los temporales que aparecen en el lado derecho
        used = set()
        for line in self.ir:
            parts = line.replace(';', '').replace('(', ' ').replace(')', ' ').split()
            for part in parts[1:]:   # ignorar el primer token (left side)
                if part.startswith('t') and part[1:].isdigit():
                    used.add(part)

        optimized_ir = []
        for line in self.ir:
            if '=' in line:
                left = line.split('=')[0].strip()
                right = line.split('=', 1)[1].strip()

                is_unused_temp = (
                    left.startswith('t')
                    and left[1:].isdigit()
                    and left not in used
                )
                has_call = 'call ' in right   # NUNCA eliminar líneas con call

                if is_unused_temp and not has_call:
                    continue  # eliminar solo temporales aritméticos sin uso

            optimized_ir.append(line)
        self.ir = optimized_ir

    def optimize(self):
        print("Iniciando optimización...")
        self.remove_end_statements()
        self.remove_redundant_temporaries()
        self.simplify_trivial_operations()
        self.optimize_conditionals()
        self.remove_unreachable_labels()
        self.optimize_goto_chains()
        self.remove_unused_temporaries()
        self.optimize_redundant_for_conditions()
        print("Optimización completada.")

    def get_optimized_ir(self):
        return self.ir