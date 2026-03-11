from lexer import Lexer
from errores import Errors

# Leer archivo
with open("entrada.txt", "r", encoding="utf-8") as f:
    contenido = f.read()

# Crear manejador de errores
errors = Errors(contenido)

# Crear lexer
lexer = Lexer(errors)

# Ejecutar lexer
tokens = lexer.tokenize(contenido)

# Mostrar tokens
print("===== TOKENS =====")
for t in tokens:
    print(t)

# Mostrar errores
print("\n===== ERRORES =====")
for e in errors.errors:
    print(e)