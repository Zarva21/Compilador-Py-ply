import os
import copy


class SymbolTable:
    def __init__(self):
        self.global_scope = {}
        self.scope_stack  = [{}]
        self.closed_scopes = []

    def enter_scope(self):
        self.scope_stack.append({})
        print("Nuevo ámbito local creado.")

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            closed = copy.deepcopy(self.scope_stack[-1])
            self.closed_scopes.append(closed)
            self.scope_stack.pop()
            print("Ámbito local cerrado.")
        else:
            print("Advertencia: No se puede salir del ámbito global.")

    def current_scope(self):
        return self.scope_stack[-1] if self.scope_stack else None

    def add_symbol(self, name, type_, scope, value=None):
        """
        Registra una variable en el scope correspondiente.

        FIX: ahora retorna True si se registró correctamente, False si ya existía.
        Antes solo hacía print y seguía — eso causaba que handle_declaration
        emitiera IR incluso después de detectar una redeclaración.

        handle_declaration usa este retorno para abortar el emit si es False.
        """
        if scope == 'global':
            if name in self.global_scope:
                # No hacer print aquí — el error semántico lo reporta handle_declaration
                return False
            self.global_scope[name] = {'type': type_, 'scope': 'global', 'value': value, 'kind': 'variable'}
            print(f" [GLOBAL] Variable '{name}' ({type_}) registrada")
            return True
        else:
            current = self.current_scope()
            if current is None:
                print(f" Error: No hay contexto local para declarar '{name}'.")
                return False
            if name in current:
                # No hacer print aquí — el error semántico lo reporta handle_declaration
                return False
            current[name] = {'type': type_, 'scope': 'local', 'value': value, 'kind': 'variable'}
            print(f" [LOCAL]  Variable '{name}' ({type_}) registrada")
            return True

    def add_array_symbol(self, name, type_, scope, size, value=None):
        data = {
            'type': type_,
            'scope': scope,
            'value': value,
            'kind': 'array',
            'size': size,
        }
        if scope == 'global':
            if name in self.global_scope:
                return False
            self.global_scope[name] = data
            print(f" [GLOBAL] Arreglo '{name}' ({type_}[{size}]) registrado")
            return True

        current = self.current_scope()
        if current is None or name in current:
            return False
        current[name] = data
        print(f" [LOCAL]  Arreglo '{name}' ({type_}[{size}]) registrado")
        return True

    def add_struct_instance(self, name, struct_type, scope, fields):
        data = {
            'type': struct_type,
            'scope': scope,
            'value': fields,
            'kind': 'struct_instance',
            'fields': fields,
        }
        if scope == 'global':
            if name in self.global_scope:
                return False
            self.global_scope[name] = data
            print(f" [GLOBAL] Struct '{name}' ({struct_type}) registrado")
            return True

        current = self.current_scope()
        if current is None or name in current:
            return False
        current[name] = data
        print(f" [LOCAL]  Struct '{name}' ({struct_type}) registrado")
        return True

    def update_struct_field(self, name, field, value):
        sym = self.get_symbol(name)
        if sym is None or sym.get('kind') != 'struct_instance':
            return False
        fields = sym.setdefault('fields', {})
        if field in fields:
            fields[field]['value'] = value
        sym['value'] = fields
        return True

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
        return None

    def guardar_snapshot_final(self):
        self.final_snapshot = {
            'global_scope': copy.deepcopy(self.global_scope),
            'scope_stack':  copy.deepcopy(self.scope_stack),
            'closed_scopes': copy.deepcopy(self.closed_scopes),
        }

    def to_flat_dict(self):
        """
        Devuelve globales + locales cerrados para ccodeGen.
        Así puede conocer el tipo real de variables declaradas en bloques.
        """
        result = {}

        # Globales
        for name, info in self.global_scope.items():
            result[name] = {
                "type": info["type"],
                "value": info.get("value"),
                "scope": info.get("scope", "global"),
                "kind": info.get("kind", "variable"),
                "size": info.get("size"),
                "fields": info.get("fields"),
            }

        # Locales aún activos
        for scope in self.scope_stack:
            for name, info in scope.items():
                if name not in result:
                    result[name] = {
                        "type": info["type"],
                        "value": info.get("value"),
                        "scope": info.get("scope", "local"),
                        "kind": info.get("kind", "variable"),
                        "size": info.get("size"),
                        "fields": info.get("fields"),
                    }

        # Locales cerrados
        if hasattr(self, "closed_scopes"):
            for scope in self.closed_scopes:
                for name, info in scope.items():
                    if name not in result:
                        result[name] = {
                            "type": info["type"],
                            "value": info.get("value"),
                            "scope": info.get("scope", "local"),
                            "kind": info.get("kind", "variable"),
                            "size": info.get("size"),
                            "fields": info.get("fields"),
                        }

        return result

    def toHtml(self):
        """
        Tabla HTML de símbolos.
        Muestra el valor real evaluado estáticamente por _evaluate_runtime.
        Si la variable no tiene valor (loop, función, sin inicialización) -> "?"
        """
        html = """
        <style>
            .sym-table { width:100%; border-collapse:collapse; font-size:0.9rem; }
            .sym-table th { background:#2c3e50; color:white; padding:9px 14px; text-align:left; }
            .sym-table td { padding:9px 14px; border-bottom:1px solid #eee; }
            .sym-table tr:hover td { background:#f9f9f9; }
            .scope-global { color:#1a5276; font-weight:600; }
            .scope-local  { color:#117a65; font-weight:600; }
            .val-dynamic  { color:#e67e22; font-style:italic; }
            .val-real     { color:#1a5276; font-weight:500; font-family: monospace; }
        </style>
        <table class="sym-table">
            <tr><th>Nombre</th><th>Tipo</th><th>Ámbito</th><th>Valor</th></tr>
        """

        if hasattr(self, 'final_snapshot'):
            global_data  = self.final_snapshot['global_scope']
            scopes_local = self.final_snapshot['scope_stack']
            closed_scopes  = self.final_snapshot.get('closed_scopes', [])
        else:
            global_data  = self.global_scope
            scopes_local = self.scope_stack
            closed_scopes  = self.closed_scopes    

        def _display(valor, tipo=None):
            if valor is None:
                return '<span class="val-dynamic">?</span>'
            if isinstance(valor, bool):
                return f'<span class="val-real">{"true" if valor else "false"}</span>'
            if isinstance(valor, str):
                if tipo and tipo.lower() == 'charizar':
                    return f'<span class="val-real">\'{valor}\'</span>'
                return f'<span class="val-real">"{valor}"</span>'
            if isinstance(valor, list):
                return f'<span class="val-real">[{", ".join(map(str, valor))}]</span>'
            if isinstance(valor, dict):
                parts = []
                for key, item in valor.items():
                    val = item.get('value') if isinstance(item, dict) else item
                    parts.append(f"{key}:{'?' if val is None else val}")
                return f'<span class="val-real">{{{", ".join(parts)}}}</span>'
            return f'<span class="val-real">{valor}</span>'

        for identifier, data in global_data.items():
            html += (
                f"<tr>"
                f"<td>{identifier}</td>"
                f"<td>{data['type']}</td>"
                f"<td><span class='scope-global'>global</span></td>"
                f"<td>{_display(data.get('value'), data.get('type'))}</td>"
                f"</tr>"
            )

        for scope in scopes_local:
            for identifier, data in scope.items():
                if data.get('scope') == 'local':
                    html += (
                        f"<tr>"
                        f"<td>{identifier}</td>"
                        f"<td>{data['type']}</td>"
                        f"<td><span class='scope-local'>local</span></td>"
                        f"<td>{_display(data.get('value'), data.get('type'))}</td>"
                        f"</tr>"
                    )

        # scopes cerrados
        for scope in closed_scopes:
            for identifier, data in scope.items():
                html += (
                    f"<tr>"
                    f"<td>{identifier}</td>"
                    f"<td>{data['type']}</td>"
                    f"<td><span class='scope-local'>local (cerrado)</span></td>"
                    f"<td>{_display(data.get('value'), data.get('type'))}</td>"
                    f"</tr>"
                )

        html += "</table>"
        return html
