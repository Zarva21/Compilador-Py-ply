import re


TIPOS_DATO = ('entei', 'floatzel', 'charizar', 'boofalant', 'stantler')


def limpiar_declaraciones_incompletas(codigo, errores, errores_lexicos=None):
    lineas_limpias = []
    patron_tipo = re.compile(r'^(entei|floatzel|charizar|boofalant|stantler)\b')
    lineas_con_error_lexico = set()

    if errores_lexicos is not None:
        for error in getattr(errores_lexicos, 'errors', []):
            if isinstance(error, dict):
                try:
                    lineas_con_error_lexico.add(int(error.get('fila')))
                except (TypeError, ValueError):
                    pass

    for numero, linea in enumerate(codigo.splitlines(), start=1):
        stripped = linea.strip()
        match = patron_tipo.match(stripped)

        if not match:
            lineas_limpias.append(linea)
            continue

        tipo = match.group(1)
        partes = stripped.split()
        incompleta = False
        detalle = ""

        if len(partes) == 1:
            incompleta = True
            detalle = "falta el identificador"
        elif len(partes) >= 3 and partes[2] == 'as' and 'pyc' not in partes[3:]:
            incompleta = True
            detalle = "falta el valor despues de 'as' y el cierre 'pyc'"
        elif not stripped.endswith('pyc'):
            incompleta = True
            detalle = "falta el cierre 'pyc'"

        if incompleta:
            col = linea.find(tipo) + 1
            if numero not in lineas_con_error_lexico:
                errores.encolar_error(
                    f"Error sintáctico: declaración incompleta de tipo '{tipo}' en fila {numero}, col {col}. "
                    f"{detalle}. Sintaxis correcta: {tipo} nombreVariable pyc "
                    f"o {tipo} nombreVariable as expresion pyc"
                )
            lineas_limpias.append(" " * len(linea))
        else:
            lineas_limpias.append(linea)

    return "\n".join(lineas_limpias)
