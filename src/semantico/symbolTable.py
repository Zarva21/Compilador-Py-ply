import os
import copy

class SymbolTable:
    def __init__(self):
        self.global_scope = {}
        self.scope_stack = [{}]
        self.final_snapshot = None  # snapshot persistente para la tabla final
        self.closed_scopes = []  # Guarda solo ámbitos locales cerrados

    def enter_scope(self):
        self.scope_stack.append({})
        print("Nuevo ámbito local creado.")

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            closed = self.scope_stack.pop()
            if closed:  # Solo guardar si el ámbito tiene variables
                self.closed_scopes.append(closed)
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
        elif scope == 'local':
            current = self.current_scope()
            if current is None:
                print(f" Error: No hay un contexto local activo para declarar '{name}'.")
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
        """Copia el estado final de la tabla para graficar después de cerrar ámbitos"""
        self.final_snapshot = {
            'global_scope': copy.deepcopy(self.global_scope),
            'scope_stack': copy.deepcopy(self.scope_stack)
        }
    #Sirve únicamente en el código ccodeGen.py
    def to_flat_dict(self):
        result = {}

        # Agregar variables globales
        for name, info in self.global_scope.items():
            result[name] = {"type": info["type"], "value": info.get("value", None)}

        # Agregar variables locales (último stack + cerrados)
        for scope in self.scope_stack + self.closed_scopes:
            for name, info in scope.items():
                if name not in result:
                    result[name] = {"type": info["type"], "value": info.get("value", None)}

        return result
    def toHtml(self):
        html = '''
        <html>
        <head>
            <title>Tabla de Símbolos</title>
            <link rel="stylesheet" href="./css/styles.css">
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #333; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Tabla de Símbolos</h1>
            <table>
                <tr>
                    <th>Nombre</th>
                    <th>Tipo</th>
                    <th>Ámbito</th>
                    <th>Valor</th>
                </tr>
        '''

        seen = set()  

        for identifier, data in self.global_scope.items():
            clave = (identifier, 'global')
            if clave not in seen:
                seen.add(clave)
                html += f"<tr><td>{identifier}</td><td>{data['type']}</td><td>global</td><td>{data['value']}</td></tr>"

        # Variables locales (stack actual + ámbitos cerrados)
        for scope in self.scope_stack + self.closed_scopes:
            for identifier, data in scope.items():
                clave = (identifier, 'local')
                if clave not in seen:
                    seen.add(clave)
                    html += f"<tr><td>{identifier}</td><td>{data['type']}</td><td>local</td><td>{data['value']}</td></tr>"

        html += '''
            </table>
        </body>
        </html>
        '''

        os.makedirs('templates', exist_ok=True)
        file_path = os.path.join('templates', 'symbol_table.html')
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(html)

        return html