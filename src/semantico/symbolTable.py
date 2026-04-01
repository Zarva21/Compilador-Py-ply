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
        """Congela el estado completo. Llamar justo antes del exit_scope() final."""
        self.final_snapshot = {
            'global_scope': copy.deepcopy(self.global_scope),
            'scope_stack':  copy.deepcopy(self.scope_stack),
        }

    def to_flat_dict(self):
        """Solo globales para ccodeGen."""
        result = {}
        for name, info in self.global_scope.items():
            result[name] = {"type": info["type"], "value": info.get("value")}
        return result

    def toHtml(self):
        """Tabla HTML completa: globales + locales."""
        html = """
        <style>
            .sym-table { width:100%; border-collapse:collapse; font-size:0.9rem; }
            .sym-table th { background:#2c3e50; color:white; padding:9px 14px; text-align:left; }
            .sym-table td { padding:9px 14px; border-bottom:1px solid #eee; }
            .sym-table tr:hover td { background:#f9f9f9; }
            .scope-global { color:#1a5276; font-weight:600; }
            .scope-local  { color:#117a65; font-weight:600; }
        </style>
        <table class="sym-table">
            <tr><th>Nombre</th><th>Tipo</th><th>Ámbito</th><th>Valor</th></tr>
        """

        if hasattr(self, 'final_snapshot'):
            global_data  = self.final_snapshot['global_scope']
            scopes_local = self.final_snapshot['scope_stack']
        else:
            global_data  = self.global_scope
            scopes_local = self.scope_stack

        def _display(valor):
            if isinstance(valor, str) and valor.startswith('t') and valor[1:].isdigit():
                return '(calculado en runtime)'
            return '—' if valor is None else valor

        for identifier, data in global_data.items():
            html += (
                f"<tr><td>{identifier}</td><td>{data['type']}</td>"
                f"<td><span class='scope-global'>global</span></td>"
                f"<td>{_display(data['value'])}</td></tr>"
            )

        for scope in scopes_local:
            for identifier, data in scope.items():
                ambito = data.get('scope', 'local')
                html += (
                    f"<tr><td>{identifier}</td><td>{data['type']}</td>"
                    f"<td><span class='scope-local'>{ambito}</span></td>"
                    f"<td>{_display(data['value'])}</td></tr>"
                )

        html += "</table>"
        return html