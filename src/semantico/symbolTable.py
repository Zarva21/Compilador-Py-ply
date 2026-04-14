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
                print(f" [GLOBAL] Variable '{name}' ({type_}) registrada")
        else:
            current = self.current_scope()
            if current is None:
                print(f" Error: No hay contexto local para declarar '{name}'.")
                return
            if name in current:
                print(f" Error: Variable local '{name}' ya declarada en este ámbito.")
            else:
                current[name] = {'type': type_, 'scope': 'local', 'value': value}
                print(f" [LOCAL]  Variable '{name}' ({type_}) registrada")

    def update_symbol(self, name, value):
        for scope in reversed(self.scope_stack):
            if name in scope:
                scope[name]['value'] = value
                return True
        if name in self.global_scope:
            self.global_scope[name]['value'] = value
            return True
        print(f"Error: La variable '{name}' no ha sido declarada.")
        return False

    def get_symbol(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        if name in self.global_scope:
            return self.global_scope[name]
        # No imprimir error aquí — _resolve_ir consulta get_symbol para distinguir
        # variables de string literals. Un None silencioso es la respuesta correcta.
        return None

    def guardar_snapshot_final(self):
        """Congela estado completo. Llamar justo antes del exit_scope() final."""
        self.final_snapshot = {
            'global_scope': copy.deepcopy(self.global_scope),
            'scope_stack':  copy.deepcopy(self.scope_stack),
        }

    def to_flat_dict(self):
        """Solo globales para ccodeGen (necesita los tipos)."""
        result = {}
        for name, info in self.global_scope.items():
            result[name] = {"type": info["type"], "value": info.get("value")}
        return result

    def toHtml(self):
        """
        Tabla HTML de símbolos.
        Muestra el valor real evaluado estáticamente por _evaluate_runtime.
        Si la variable no tiene valor (loop, función, sin inicialización) → "—"
        Si el valor fue evaluado pero es None explícito              → "?"
        """
        html = """
        <style>
            .sym-table { width:100%; border-collapse:collapse; font-size:0.9rem; }
            .sym-table th { background:#2c3e50; color:white; padding:9px 14px; text-align:left; }
            .sym-table td { padding:9px 14px; border-bottom:1px solid #eee; }
            .sym-table tr:hover td { background:#f9f9f9; }
            .scope-global { color:#1a5276; font-weight:600; }
            .scope-local  { color:#117a65; font-weight:600; }
            .val-none     { color:#aaa; font-style:italic; }
            .val-dynamic  { color:#e67e22; font-style:italic; }
            .val-real     { color:#1a5276; font-weight:500; font-family: monospace; }
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
            # valor = None  → variable sin inicialización o no evaluable
            # valor = False → booleano falso (distinto de None)
            if valor is None:
                return '<span class="val-dynamic">?</span>'
            if isinstance(valor, bool):
                return f'<span class="val-real">{"true" if valor else "false"}</span>'
            if isinstance(valor, str):
                # Mostrar strings con comillas para que quede claro el tipo
                return f'<span class="val-real">"{valor}"</span>'
            # int, float
            return f'<span class="val-real">{valor}</span>'

        for identifier, data in global_data.items():
            html += (
                f"<tr>"
                f"<td>{identifier}</td>"
                f"<td>{data['type']}</td>"
                f"<td><span class='scope-global'>global</span></td>"
                f"<td>{_display(data.get('value'))}</td>"
                f"</tr>"
            )

        for scope in scopes_local:
            for identifier, data in scope.items():
                ambito = data.get('scope', 'local')
                html += (
                    f"<tr>"
                    f"<td>{identifier}</td>"
                    f"<td>{data['type']}</td>"
                    f"<td><span class='scope-local'>{ambito}</span></td>"
                    f"<td>{_display(data.get('value'))}</td>"
                    f"</tr>"
                )

        html += "</table>"
        return html