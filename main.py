from src.lexer.lexer import Lexer
from src.sintactico.parser import Parser
from src.Extras.errores import Errors
from src.semantico.symbolTable import SymbolTable
from src.semantico.semantic import Semantic
from src.intercode.interCodeGenerator import interCodeGenerator

# Leer archivo
with open("entrada.txt", "r", encoding="utf-8") as f:
    codigo = f.read()

# Crear objetos reales del proyecto
symbol_table = SymbolTable()
errors = Errors(codigo)
inter_code_generator = interCodeGenerator()

lexer = Lexer(errors)
semantic = Semantic(symbol_table, errors, lexer, inter_code_generator)

parser = Parser(lexer, errors, semantic)

# 🔥 SOLO SINTÁCTICO
parser.parse(codigo, execute=False)

# Mostrar errores
if errors.errors:
    print("\nErrores encontrados:")
    for e in errors.errors:
        print(e)
else:
    print("\nNo hay errores sintácticos.")