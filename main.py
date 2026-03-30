import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.Extras.errores import Errors
from src.lexer.lexer import Lexer
from src.sintactico.parser import Parser

# ──────────────────────────────────────────────
# Generador del reporte HTML
# ──────────────────────────────────────────────

def generar_tabla_tokens(tokens, filas_tokens):
    if not tokens:
        return "<p class='no-errors'>No se encontraron tokens.</p>"
    return (
        "<table>"
        "<tr><th>#</th><th>Tipo</th><th>Valor</th><th>Línea</th><th>Columna</th></tr>"
        f"{filas_tokens}"
        "</table>"
    )


def generar_seccion_codigo(codigo):
    """Genera un bloque de código con estilo oscuro."""
    if not codigo:
        return "<p style='color:green;font-style:italic;'>No hay código generado.</p>"
    lineas = ""
    for i, linea in enumerate(codigo, start=1):
        linea_escaped = linea.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        lineas += (
            f"<tr>"
            f"<td style='color:#999;user-select:none;padding-right:16px;width:40px'>{i}</td>"
            f"<td>{linea_escaped}</td>"
            f"</tr>\n"
        )
    return f"""
    <div style='background:#1e1e1e;border-radius:8px;padding:20px;overflow-x:auto;'>
        <table style='width:100%;border-collapse:collapse;
                      font-family:monospace;font-size:0.85rem;color:#d4d4d4;'>
            {lineas}
        </table>
    </div>"""


def generar_html(tokens, lex_errors_html, parse_errors_html,
                 intercode, cpp_code, sym_table_html,
                 archivo_fuente, hay_errores):

    # Filas de tokens
    filas_tokens = ""
    for i, tok in enumerate(tokens, start=1):
        tipo, valor, fila, col = tok
        valor_escaped = str(valor).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        filas_tokens += (
            f"<tr><td>{i}</td><td>{tipo}</td>"
            f"<td>{valor_escaped}</td><td>{fila}</td><td>{col}</td></tr>\n"
        )

    # Secciones de código solo si no hay errores
    if not hay_errores:
        seccion_intercode = f"""
    <div class="section">
        <h2 class="ok"> Código Intermedio</h2>
        {generar_seccion_codigo(intercode)}
    </div>"""

        seccion_cpp = f"""
    <div class="section">
        <h2 class="ok"> Código C++ Generado</h2>
        {generar_seccion_codigo(cpp_code)}aja
    </div>"""

        seccion_tabla = f"""
    <div class="section">
        <h2 class="ok"> Tabla de Símbolos</h2>
        {sym_table_html if sym_table_html else
         "<p style='color:green;font-style:italic;'>Tabla vacía.</p>"}
    </div>"""
    else:
        msg = "<p style='color:#e74c3c;font-style:italic;'>No disponible — corrige los errores primero.</p>"
        seccion_intercode = f'<div class="section"><h2 class="err"> Código Intermedio</h2>{msg}</div>'
        seccion_cpp       = f'<div class="section"><h2 class="err"> Código C++ Generado</h2>{msg}</div>'
        seccion_tabla     = ""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte – {archivo_fuente}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: #f4f6f9;
            color: #333;
            padding: 30px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 8px;
            color: #2c3e50;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 0.9rem;
        }}
        .section {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            padding: 24px;
            margin-bottom: 28px;
        }}
        .section h2 {{
            font-size: 1.2rem;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid #eee;
        }}
        .section h2.ok  {{ color: #27ae60; }}
        .section h2.err {{ color: #e74c3c; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        th {{
            background: #2c3e50;
            color: white;
            padding: 10px 14px;
            text-align: left;
        }}
        td {{
            padding: 9px 14px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover td {{ background: #f9f9f9; }}
        .no-errors {{ color: #27ae60; font-style: italic; }}
        .error-section h2 {{ color: #e74c3c; font-size: 1.1rem; margin-bottom: 12px; }}
        .error-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        .error-table th {{ background: #c0392b; color: white; padding: 9px 14px; text-align: left; }}
        .error-table td {{ padding: 9px 14px; border-bottom: 1px solid #fdd; }}
        .error-table tr:hover td {{ background: #fff5f5; }}
    </style>
</head>
<body>

    <h1> Reporte del Compilador Pokémon</h1>
    <p class="subtitle">Archivo analizado: <strong>{archivo_fuente}</strong></p>

    <div class="section">
        <h2 class="ok"> Análisis Léxico – Tokens encontrados</h2>
        {generar_tabla_tokens(tokens, filas_tokens)}
    </div>

    <div class="section">
        <h2 class="err"> Errores Léxicos</h2>
        {lex_errors_html}
    </div>

    <div class="section">
        <h2 class="err"> Errores Sintácticos</h2>
        {parse_errors_html}
    </div>

    {seccion_intercode}
    {seccion_cpp}
    {seccion_tabla}

</body>
</html>
"""
    return html


# ──────────────────────────────────────────────
# Menú principal de consola
# ──────────────────────────────────────────────

def menu():
    print("=" * 50)
    print("   Compilador Pokémon – Menú Principal")
    print("=" * 50)

    while True:
        print("\nOpciones:")
        print("  [1] Analizar un archivo")
        print("  [2] Salir")
        opcion = input("\nElige una opción: ").strip()

        if opcion == "1":
            analizar()
        elif opcion == "2":
            print("\nCerrando el compilador.")
            break
        else:
            print("Opción no válida, intenta de nuevo.")


def analizar():
    ruta = input("\nIngresa la ruta del archivo a analizar: ").strip()

    if not os.path.isfile(ruta):
        print(f"No se encontró el archivo: '{ruta}'")
        return

    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()

    nombre = os.path.basename(ruta)
    print(f"\nAnalizando: {nombre} ...")

    # ── Análisis léxico ──
    lex_errors = Errors(contenido)
    lexer      = Lexer(lex_errors)
    tokens     = lexer.tokenize(contenido)
    print(f"   Tokens encontrados: {len(tokens)}")

    # ── Análisis sintáctico + semántico ──
    parse_errors = Errors(contenido)
    intercode    = []
    cpp_code     = []
    sym_html     = ""

    try:
        from src.semantico.semantic import Semantic
        from src.semantico.symbolTable import SymbolTable
        from src.intercode.interCodeGenerador import interCodeGenerator
        from src.codeGen.codeGen import ccodeGen

        sym_table = SymbolTable()
        codegen   = interCodeGenerator()
        semantic  = Semantic(sym_table, parse_errors, lexer, codegen)

        parser = Parser(lexer, parse_errors, semantic)
        parser.parse(contenido, execute=True)

        hay_errores = bool(lex_errors.errors or parse_errors.errors)

        if not hay_errores:
            # Optimizar
            semantic.optimize_intermediate_code()
            intercode = codegen.get_code()

            # Generar C++
            sym_flat = sym_table.to_flat_dict()
            gen = ccodeGen(intercode, sym_flat)
            gen.generate()
            cpp_code = gen.get_cpp_code().splitlines()

            # Guardar .cpp
            nombre_base = os.path.splitext(nombre)[0]
            cpp_path = f"{nombre_base}.cpp"
            with open(cpp_path, "w", encoding="utf-8") as f:
                f.write(gen.get_cpp_code())
            print(f"   Código C++ guardado: {cpp_path}")

            # Tabla de símbolos
            sym_html = sym_table.toHtml()
        else:
            intercode = codegen.get_code()

    except ImportError as e:
        print(f"   Semántica no disponible ({e}), usando modo básico...")
        semantic = _DummySemantic()
        parser   = Parser(lexer, parse_errors, semantic)
        parser.parse(contenido, execute=False)
        hay_errores = bool(lex_errors.errors or parse_errors.errors)

    # ── Generar HTML ──
    lex_html   = lex_errors.errorHtml("Léxicos")
    parse_html = parse_errors.errorHtml("Sintácticos")
    html = generar_html(
        tokens, lex_html, parse_html,
        intercode, cpp_code, sym_html,
        nombre, hay_errores
    )

    nombre_base = os.path.splitext(nombre)[0]
    salida = f"reporte_{nombre_base}.html"
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"   Errores léxicos:     {len(lex_errors.errors)}")
    print(f"   Errores sintácticos: {len(parse_errors.errors)}")
    print(f"\nReporte generado: {salida}")
    if not hay_errores:
        print("¡Análisis completado sin errores!")

    print(f"IR recibido por ccodeGen ({len(intercode)} líneas):")
    for l in intercode:
        print(f"  '{l}'")
# ──────────────────────────────────────────────
# Handler semántico mínimo (placeholder)
# ──────────────────────────────────────────────

class _DummySemantic:
    class _SymTable:
        scope_stack = []
        def enter_scope(self): pass
        def exit_scope(self): pass

    def __init__(self):
        self.symbol_table = self._SymTable()

    def _noop(self, *a, **kw):
        return lambda: None

    handle_print              = _noop
    handle_assignment         = _noop
    handle_declaration        = _noop
    handle_for                = _noop
    handle_do_while           = _noop
    handle_if                 = _noop
    handle_switch             = _noop
    handle_break              = _noop
    handle_return             = _noop
    handle_method_declaration = _noop
    handle_method_call        = _noop
    handle_while              = _noop
    handle_factor             = lambda self, v: v

    def evaluate_condition_dynamic(self, *a, **kw):
        return lambda: False


# ──────────────────────────────────────────────
if __name__ == "__main__":
    menu()