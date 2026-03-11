class Errors:
    def __init__(self,content):
        self.errors = []  
        self.text=content
    def getText(self):
        return self.text
    def encolar_error(self, error):
        self.errors.append(error)

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
        """Retorna el HTML de la lista de errores sin generar archivos físicos."""
        if not self.errors:
            return "<p style='color: green;'>No se encontraron errores.</p>"

        html = f'<div class="error-section">'
        if nombre_archivo:
            html += f'<h2 style="color: red;">Errores {nombre_archivo.capitalize()}</h2>'
        else:
            html += f'<h2 style="color: red;">Errores</h2>'

        html += '<table class="error-table">'
        html += '<tr><th>#</th><th>Descripción del Error</th></tr>'

        for i, error in enumerate(self.errors, start=1):
            html += f'<tr><td>{i}</td><td>{error}</td></tr>'

        html += '</table></div>'

        return html