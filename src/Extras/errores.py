import re
class Errors:
    def __init__(self,content):
        self.errors = []  
        self.text=content

    def getText(self):
        return self.text
    
    def encolar_error(self, error):
        if isinstance(error, dict):
            self.errors.append(error)
            return

        fila, col = None, None

        # Buscar "fila X, col Y" o "fila X y columna Y"
        match = re.search(r'fila (\d+)[,\s]+(y\s+)?col(?:umna)?\s*(\d+)', error)
        if match:
            fila, col = match.group(1), match.group(3)
        else:
            # Buscar solo "fila X" sin columna
            match = re.search(r'fila (\d+)', error)
            if match:
                fila = match.group(1)
                col = '-'

        # Determinar tipo
        if 'léxico' in error.lower():
            tipo = 'Léxico'
        elif 'sintáctico' in error.lower():
            tipo = 'Sintáctico'
        elif 'advertencia' in error.lower():
            tipo = 'Advertencia'
        else:
            tipo = 'Error'

        # Limpiar descripción
        descripcion = re.sub(r'\s*en (la )?fila \d+[\s,]*(y\s*)?(col(umna)?\s*\d+)?\.?', '', error).strip()
        descripcion = re.sub(r'^(Error (léxico|sintáctico)|Advertencia):\s*', '', descripcion, flags=re.IGNORECASE).strip()

        self.errors.append({
            'tipo': tipo,
            'descripcion': descripcion,
            'fila': fila or '-',
            'col': col or '-'
        })

    def find_line(self, token):
        """Encuentra la fila (número de línea) de un token en el texto de entrada"""
        line_count = self.getText().count('\n', 0, token.lexpos)
        return line_count + 1
    
    def find_column(self,  token):
        """Encuentra la columna de un token en el texto de entrada"""
        last_newline = self.getText().rfind('\n', 0, token.lexpos)
        if last_newline == -1:
            return token.lexpos + 1  
        
        column = token.lexpos - last_newline
        
        return column


    def errorHtml(self, nombre_archivo=None):
        if not self.errors:
            return "<p style='color: green;'>No se encontraron errores.</p>"

        html = f'<div class="error-section">'
        if nombre_archivo:
            html += f'<h2 style="color: red;">Errores {nombre_archivo.capitalize()}</h2>'
        else:
            html += '<h2 style="color: red;">Errores</h2>'

        html += '<table class="error-table">'
        html += '<tr><th>#</th><th>Tipo</th><th>Descripción</th><th>Fila</th><th>Columna</th></tr>'

        for i, error in enumerate(self.errors, start=1):
            if isinstance(error, dict):
                html += (
                    f"<tr>"
                    f"<td>{i}</td>"
                    f"<td>{error.get('tipo', '-')}</td>"
                    f"<td>{error.get('descripcion', '-')}</td>"
                    f"<td>{error.get('fila', '-')}</td>"
                    f"<td>{error.get('col', '-')}</td>"
                    f"</tr>\n"
                )
            else:
                html += f"<tr><td>{i}</td><td>-</td><td>{error}</td><td>-</td><td>-</td></tr>\n"

        html += '</table></div>'
        return html