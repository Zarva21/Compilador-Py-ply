import os
import copy


class SymbolTable:
    def __init__(self):
        self.global_scope = {}
        self.scope_stack  = [{}]

    def enter_scope(self):
        self.scope_stack.append({})
        print("Nuevo ámbito local creado.")

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
            print("Ámbito local cerrado.")
        else:
            print("Advertencia: No se puede salir del ámbito global.")

    def current_scope(self):
        return self.scope_stack[-1] if self.scope_stack else None

    def add_symbol(self, name, type_, scope, value=None):
        if scope == 'global':
            if name in self.global_scope:
                print(f"Error: Variable global '{name}' ya declarada.")
            else:
                self.global_scope[name] = {'type': type_, 'scope': 'global', 'value': value}
                print(f" [GLOBAL] Variable '{name}' añadida con valor '{value}'")
        else:
            current = self.current_scope()
            if current is None:
                print(f" Error: No hay contexto local para declarar '{name}'.")
                return
            if name in current:
                print(f" Error: Variable local '{name}' ya declarada en este ámbito.")
            else:
                current[name] = {'type': type_, 'scope': 'local', 'value': value}
                print(f" [LOCAL] Variable '{name}' añadida con valor '{value}'")

    def update_symbol(self, name, value):
        for scope in reversed(self.scope_stack):
            if name in scope:
                scope[name]['value'] = value
                print(f" Actualizado local '{name}' a {value}")
                return True
        if name in self.global_scope:
            self.global_scope[name]['value'] = value
            print(f"Actualizado global '{name}' a {value}")
            return True
        print(f"Error: La variable '{name}' no ha sido declarada.")
        return False

    def get_symbol(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                print(f" Valor local de '{name}': {scope[name]['value']}")
                return scope[name]
        if name in self.global_scope:
            print(f" Valor global de '{name}': {self.global_scope[name]['value']}")
            return self.global_scope[name]
        print(f" Error: La variable '{name}' no ha sido declarada.")
        return None

    def guardar_snapshot_final(self):
        self.final_snapshot = {
            'global_scope': copy.deepcopy(self.global_scope),
            'scope_stack':  copy.deepcopy(self.scope_stack),
        }

    def to_flat_dict(self):
        """Solo variables globales para ccodeGen."""
        result = {}
        for name, info in self.global_scope.items():
            result[name] = {"type": info["type"], "value": info.get("value")}
        return result

    def toHtml(self):
        """HTML de la tabla — solo variables globales, valor limpio."""
        html = """
        <style>
            .sym-table { width:100%; border-collapse:collapse; font-size:0.9rem; }
            .sym-table th { background:#2c3e50; color:white; padding:9px 14px; text-align:left; }
            .sym-table td { padding:9px 14px; border-bottom:1px solid #eee; }
            .sym-table tr:hover td { background:#f9f9f9; }
        </style>
        <table class="sym-table">
            <tr><th>Nombre</th><th>Tipo</th><th>Ámbito</th><th>Valor</th></tr>
        """

        for identifier, data in self.global_scope.items():
            valor = data['value']

            # Limpiar valores temporales (tX) — son resultados de runtime
            if isinstance(valor, str) and valor.startswith('t') and valor[1:].isdigit():
                valor_display = '(calculado en runtime)'
            elif valor is None:
                valor_display = '—'
            else:
                valor_display = valor

            html += (
                f"<tr>"
                f"<td>{identifier}</td>"
                f"<td>{data['type']}</td>"
                f"<td>global</td>"
                f"<td>{valor_display}</td>"
                f"</tr>"
            )

        html += "</table>"
        return html