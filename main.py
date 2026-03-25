import os
import sys

# ──────────────────────────────────────────────
# Ajuste de path para que funcione desde raíz
# ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.Extras.errores import Errors          
from src.lexer.lexer import Lexer            
from src.sintactico.parser import Parser      


# Generador del reporte HTML


def generar_tabla_tokens(tokens, filas_tokens):
    if not tokens:
        return "<p class='no-errors'>No se encontraron tokens.</p>"
    return f"<table><tr><th>Tipo</th><th>Valor</th></tr>{filas_tokens}</table>"


def generar_html(tokens, lex_errors_html, parse_errors_html, archivo_fuente):
    """Genera el HTML completo del reporte."""

    # Filas de la tabla de tokens
    filas_tokens = ""
    for tipo, valor in tokens:
        filas_tokens += f"<tr><td>{tipo}</td><td>{valor}</td></tr>\n"

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
        .badge-ok  {{ color: #27ae60; font-weight: bold; }}
        .badge-err {{ color: #e74c3c; font-weight: bold; }}
        .no-errors {{ color: #27ae60; font-style: italic; }}

        /* Estilos heredados de tu clase Errors */
        .error-section h2 {{ color: #e74c3c; font-size: 1.1rem; margin-bottom: 12px; }}
        .error-table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        .error-table th {{ background: #c0392b; color: white; padding: 9px 14px; text-align: left; }}
        .error-table td {{ padding: 9px 14px; border-bottom: 1px solid #fdd; }}
        .error-table tr:hover td {{ background: #fff5f5; }}
    </style>
</head>
<body>

    <h1> Reporte del Compilador</h1>
    <p class="subtitle">Archivo analizado: <strong>{archivo_fuente}</strong></p>

    <!-- ── TOKENS ── -->
    <div class="section">
        <h2 class="ok"> Análisis Léxico – Tokens encontrados</h2>
        {generar_tabla_tokens(tokens, filas_tokens)}
    </div>

    <!-- ── ERRORES LÉXICOS ── -->
    <div class="section">
        <h2 class="err"> Errores Léxicos</h2>
        {lex_errors_html}
    </div>

    <!-- ── ERRORES SINTÁCTICOS ── -->
    <div class="section">
        <h2 class="err"> Errores Sintácticos</h2>
        {parse_errors_html}
    </div>

</body>
</html>
"""
    return html



# Menú principal de consola


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

# ──────────────────────────────────────────────
# Función principal de análisis
# Aquí se orquesta todo el proceso: léxico, sintáctico y generación de HTML
# Se mantiene simple para que el menú sea claro y el código modular

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
    lex_errors   = Errors(contenido)
    lexer        = Lexer(lex_errors)
    tokens       = lexer.tokenize(contenido)

    print(f"   Tokens encontrados: {len(tokens)}")

    # ── Análisis sintáctico ──
    parse_errors = Errors(contenido)

    try:
        # Importación tardía para evitar errores si no existe semántica
        from src.semantico.semantic import SemanticHandler   # ajusta el import si es distinto
        semantic = SemanticHandler(parse_errors)
    except ImportError:
        # Semántica aún no disponible, usar dummy
        semantic = _DummySemantic()

    parser = Parser(lexer, parse_errors, semantic)
    parser.parse(contenido, execute=False)   # execute=False evita correr el AST sin semántica real

    # ── Generar HTML ──
    lex_html   = lex_errors.errorHtml("Léxicos")
    parse_html = parse_errors.errorHtml("Sintácticos")
    html       = generar_html(tokens, lex_html, parse_html, nombre)

    # ── Guardar HTML ──
    nombre_base   = os.path.splitext(nombre)[0]
    salida        = f"reporte_{nombre_base}.html"
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)



    total_errores = len(lex_errors.errors) + len(parse_errors.errors)
    print(f"   Errores léxicos:     {len(lex_errors.errors)}")
    print(f"   Errores sintácticos: {len(parse_errors.errors)}")
    print(f"\nReporte generado: {salida}")
    if total_errores == 0:
        print("¡Análisis completado sin errores!")


# ──────────────────────────────────────────────
# Handler semántico mínimo (placeholder) 
# Se usa cuando la semántica aún no está lista
# ──────────────────────────────────────────────

class _DummySemantic:
    """Implementación vacía para que el parser no explote sin semántica real."""

    class _SymTable:
        scope_stack = []
        def enter_scope(self): pass
        def exit_scope(self): pass

    def __init__(self):
        self.symbol_table = self._SymTable()

    def _noop(self, *a, **kw):
        return lambda: None

    handle_print             = _noop
    handle_assignment        = _noop
    handle_declaration       = _noop
    handle_for               = _noop
    handle_do_while          = _noop
    handle_if                = _noop
    handle_switch            = _noop
    handle_break             = _noop
    handle_return            = _noop
    handle_method_declaration= _noop
    handle_method_call       = _noop
    handle_factor            = lambda self, v: v
    handle_while            = _noop

    def evaluate_condition_dynamic(self, *a, **kw):
        return lambda: False


# ──────────────────────────────────────────────
# Punto de entrada
    
if __name__ == "__main__":
    menu()