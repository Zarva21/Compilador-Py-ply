import os
import sys
import threading
from flask import Flask, request, jsonify, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

from src.Extras.errores import Errors
from src.lexer.lexer import Lexer
from src.sintactico.parser import Parser

app = Flask(__name__)
_lock = threading.Lock()  # PLY tiene estado global; serializar análisis


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'interfaz.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(force=True, silent=True) or {}
    codigo = data.get('codigo', '')

    with _lock:
        return _run_analysis(codigo)


def _run_analysis(codigo):
    # ── Análisis léxico ──
    lex_errors = Errors(codigo)
    lexer = Lexer(lex_errors)
    tokens_raw = lexer.tokenize(codigo)

    tokens_list = []
    for i, tok in enumerate(tokens_raw, 1):
        tipo, valor, fila, col = tok
        tokens_list.append({
            'index': i,
            'tipo': str(tipo),
            'valor': str(valor),
            'fila': fila,
            'col': col,
        })

    # ── Análisis sintáctico + semántico ──
    parse_errors = Errors(codigo)
    intercode = []
    cpp_code = []
    sym_html = ''
    hay_errores = False

    try:
        from src.semantico.semantic import Semantic
        from src.semantico.symbolTable import SymbolTable
        from src.intercode.interCodeGenerador import interCodeGenerator
        from src.codeGen.codeGen import ccodeGen

        sym_table = SymbolTable()
        codegen = interCodeGenerator()
        semantic = Semantic(sym_table, parse_errors, lexer, codegen)
        parser = Parser(lexer, parse_errors, semantic)
        parser.parse(codigo, execute=True)

        hay_errores = bool(lex_errors.errors or parse_errors.errors)

        if not hay_errores:
            semantic.optimize_intermediate_code()
            intercode = codegen.get_code()
            sym_flat = sym_table.to_flat_dict()
            gen = ccodeGen(intercode, sym_flat)
            gen.generate()
            cpp_code = gen.get_cpp_code().splitlines()
            sym_html = sym_table.toHtml()
        else:
            try:
                intercode = codegen.get_code()
            except Exception:
                pass

    except Exception as exc:
        hay_errores = True
        parse_errors.encolar_error({
            'tipo': 'Error Interno',
            'descripcion': str(exc),
            'fila': '-',
            'col': '-',
        })

    return jsonify({
        'tokens': tokens_list,
        'lex_errors': lex_errors.errors,
        'parse_errors': parse_errors.errors,
        'sym_html': sym_html,
        'intercode': intercode,
        'cpp_code': cpp_code,
        'hay_errores': hay_errores,
    })


if __name__ == '__main__':
    RED = '\033[91m'
    YEL = '\033[93m'
    GRY = '\033[90m'
    RST = '\033[0m'
    print(f'{RED}{"=" * 52}{RST}')
    print(f'{RED}   Compilador Pokémon — Servidor Web{RST}')
    print(f'{RED}{"=" * 52}{RST}')
    print(f'{YEL}  Abre en tu navegador: http://localhost:5000{RST}')
    print(f'{GRY}  Presiona Ctrl+C para detener el servidor{RST}\n')
    app.run(debug=False, port=5000, host='127.0.0.1', threaded=True)
