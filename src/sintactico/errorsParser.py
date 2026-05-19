SINTAXIS_CORRECTA = {
    'PIKACHU':   'pikachu ps expresion pc pyc',
    'EVEE':      'evee ps condicion pc ls ... lc',
    'EKANS':     'lc ekans ls',
    'FORRETRES': 'forretres ps init pyc condicion pyc update pc ls ... lc',
    'WAILORD':   'wailord ps condicion pc ls ... lc',
    'DODUO':     'doduo ls ... lc wailord ps condicion pc pyc',
    'SWELLO':    'swello ps identificador pc ls kecleon valor dp ... lc',
    'KECLEON':   'kecleon valor dp instrucciones',
    'SUICUNE':   'suicune tipoDato nombreFuncion ps pc ls ... lc',
    'RAIKOU':    'raikou expresion pyc',
    'BRELOOM':   'breloom pyc',
    'ENTEI':     'entei nombreVariable as valor pyc',
    'FLOATZEL':  'floatzel nombreVariable as valor pyc',
    'CHARIZAR':  'charizar nombreVariable as valor pyc',
    'BOOFALANT': 'boofalant nombreVariable as valor pyc',
    'STANTLER':  'stantler nombreVariable as valor pyc',
    'GARDEVOIR': 'gardevoir nombreFuncion ps pc ls ... lc',
}


def _sync_after_error(self, p):
    if p is not None and p.type not in {'SEMICOLON', 'RBRACE'}:
        while True:
            tok = self.lexer.lexer.token()
            if tok is None or tok.type in {'SEMICOLON', 'RBRACE'}:
                break
    self.parser.errok()
    return None

def p_error(self, p):
    if p:
        try:
            col   = self.errors.find_column(p)
            row   = self.errors.find_line(p)
            token = p.value.lower() if isinstance(p.value, str) else str(p.value)

            # ── Verificar si ya fue reportado como error léxico ──
            ya_reportado = any(f"'{p.value}'" in err for err in self.errors.errors)
            if ya_reportado and p.type == 'IDENTIFIER':
                self.parser.errok()
                return

            # ── 1. IF mal formado ──
            if p.type == 'EVEE':
                self.errors.encolar_error(
                    f"Error sintáctico: se esperaba '(' después de 'evee' (if) "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['EVEE']}"
                )

            # ── 2. ELSE mal ubicado ──
            elif p.type == 'EKANS':
                self.errors.encolar_error(
                    f"Error sintáctico: 'ekans' (else) fuera de lugar "
                    f"en fila {row}, col {col}. "
                    f"¿Falta cerrar correctamente el bloque anterior? "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['EKANS']}"
                )

            # ── 3. FOR mal formado ──
            elif p.type == 'FORRETRES':
                self.errors.encolar_error(
                    f"Error sintáctico: 'forretres' (for) mal formado "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['FORRETRES']}"
                )

            # ── 4. WHILE mal formado ──
            elif p.type == 'WAILORD':
                self.errors.encolar_error(
                    f"Error sintáctico: 'wailord' (while) mal formado "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['WAILORD']}"
                )

            # ── 5. DO-WHILE mal formado ──
            elif p.type == 'DODUO':
                self.errors.encolar_error(
                    f"Error sintáctico: 'doduo' (do) mal formado "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['DODUO']}"
                )

            # ── 6. SWITCH mal formado ──
            elif p.type == 'SWELLO':
                self.errors.encolar_error(
                    f"Error sintáctico: 'swello' (switch) mal formado "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['SWELLO']}"
                )

            # ── 7. CASE sin : ──
            elif p.type == 'KECLEON':
                self.errors.encolar_error(
                    f"Error sintáctico: falta ':' después de 'kecleon' (case) "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['KECLEON']}"
                )

            # ── 8. DEFAULT mal ubicado ──
            elif p.type == 'DEOXYS':
                self.errors.encolar_error(
                    f"Error sintáctico: 'deoxys' (default) debe ir al final del switch "
                    f"en fila {row}, col {col}."
                )

            # ── 9. BREAK fuera de ciclo ──
            elif p.type == 'BRELOOM':
                self.errors.encolar_error(
                    f"Error sintáctico: 'breloom' (break) fuera de un ciclo o switch "
                    f"en fila {row}, col {col}."
                )

            # ── 10. PRINT mal formado ──
            elif p.type == 'PIKACHU':
                self.errors.encolar_error(
                    f"Error sintáctico: 'pikachu' (print) mal formado "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['PIKACHU']}"
                )

            # ── 11. FUNCIÓN mal formada ──
            elif p.type == 'SUICUNE':
                self.errors.encolar_error(
                    f"Error sintáctico: declaración de función 'suicune' mal formada "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['SUICUNE']}"
                )

            # ── 12. RETURN mal formado ──
            elif p.type == 'RAIKOU':
                self.errors.encolar_error(
                    f"Error sintáctico: 'raikou' (return) mal formado "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {SINTAXIS_CORRECTA['RAIKOU']}"
                )

            # ── 13. Tipo sin identificador ──
            elif p.type in {'ENTEI', 'FLOATZEL', 'CHARIZAR', 'BOOFALANT', 'STANTLER', 'GARDEVOIR'}:
                sintaxis = SINTAXIS_CORRECTA.get(p.type, '')
                self.errors.encolar_error(
                    f"Error sintáctico: después del tipo '{token}' se esperaba un identificador "
                    f"en fila {row}, col {col}. "
                    f"Sintaxis correcta: {sintaxis}"
                )

            # ── 14. Llaves ──
            elif p.type == 'LBRACE':
                # Revisar si viene después de evee/wailord/forretres sin paréntesis
                texto = self.errors.getText()
                lineas = texto.split('\n')
                linea_actual = lineas[row - 1].strip() if row <= len(lineas) else ''

                estructuras = ['evee', 'wailord', 'forretres', 'doduo', 'swello']
                estructura_detectada = next(
                    (e for e in estructuras if linea_actual.startswith(e)), None
                )

                if estructura_detectada and 'ps' not in linea_actual:
                    sint = SINTAXIS_CORRECTA.get(estructura_detectada.upper(), '')
                    self.errors.encolar_error(
                        f"Error sintáctico: '{estructura_detectada}' sin paréntesis 'ps'/'pc' "
                        f"en fila {row}, col {col}. "
                        f"Sintaxis correcta: {sint}"
                    )
                else:
                    self.errors.encolar_error(
                        f"Error sintáctico: 'ls' sin estructura válida anterior "
                        f"en fila {row}, col {col}."
                    )

            elif p.type == 'RBRACE':
                self.errors.encolar_error(
                    f"Error sintáctico: 'lc' sin apertura correspondiente "
                    f"en fila {row}, col {col}."
                )

            elif p.type == 'LPAREN':
                self.errors.encolar_error(
                    f"Error sintáctico: 'ps' inesperado o sin cierre 'pc' "
                    f"en fila {row}, col {col}."
                )

            elif p.type == 'RPAREN':
                self.errors.encolar_error(
                    f"Error sintáctico: 'pc' sin apertura correspondiente 'ps' "
                    f"en fila {row}, col {col}."
                )

            # ── 15. Número inesperado ──
            elif p.type == 'NUMBER':
                self.errors.encolar_error(
                    f"Error sintáctico: número inesperado '{p.value}' "
                    f"en fila {row}, col {col}. "
                    f"¿Falta un operador o un ';'?"
                )

            # ── 16. Identificador inesperado ──
            elif p.type == 'IDENTIFIER':
                texto = self.errors.getText()
                lineas = texto.split('\n')

                # Verificar si la línea ACTUAL empieza con evee sin paréntesis
                linea_actual = lineas[row - 1].strip() if row <= len(lineas) else ''
                estructuras_sin_paren = ['evee', 'wailord', 'forretres', 'doduo', 'swello']
                estructura_detectada = next(
                    (e for e in estructuras_sin_paren if linea_actual.startswith(e)), None
                )

                if estructura_detectada and '(' not in linea_actual:
                    sint = SINTAXIS_CORRECTA.get(estructura_detectada.upper(), '')
                    self.errors.encolar_error(
                        f"Error sintáctico: '{estructura_detectada}' sin paréntesis "
                        f"en fila {row}, col {col}. "
                        f"Sintaxis correcta: {sint}"
                    )
                else:
                    # Buscar hacia atrás la última línea con contenido real
                    linea_anterior = ''
                    num_linea = row - 1
                    for i in range(row - 2, -1, -1):
                        candidata = lineas[i].strip()
                        if candidata \
                        and not candidata.startswith('cm') \
                        and not candidata.startswith('icm') \
                        and not candidata.startswith('fcm'):
                            linea_anterior = candidata
                            num_linea = i + 1
                            break

                    if linea_anterior \
                    and not linea_anterior.endswith('pyc') \
                    and not linea_anterior.endswith('ls') \
                    and not linea_anterior.endswith('lc'):
                        self.errors.encolar_error(
                            f"Error sintáctico: falta 'pyc' al final de la línea {num_linea}, {col}. "
                            f"Línea problemática: '{linea_anterior}'"
                        )
                    else:
                        self.errors.encolar_error(
                            f"Error sintáctico: identificador inesperado '{p.value}' "
                            f"en fila {row}, col {col}. "
                            f"¿Falta un ';', un tipo de dato, o se cerró mal un bloque?"
                        )

            # ── 17. Punto y coma inesperado ──
            elif p.type == 'SEMICOLON':
                # Revisar si viene después de un bloque lc — es el caso "evee (...) ls...lc pyc"
                texto = self.errors.getText()
                lineas = texto.split('\n')
                linea_actual = lineas[row - 1].strip() if row <= len(lineas) else ''

                if linea_actual == 'lc pyc' or linea_actual == 'lc':
                    self.errors.encolar_error(
                        f"Error sintáctico: 'pyc' después de 'lc' en fila {row}, col {col}. "
                        f"Los bloques no llevan 'pyc' al final."
                    )
                else:
                    self.errors.encolar_error(
                        f"Error sintáctico: 'pyc' inesperado en fila {row}, col {col}. "
                        f"¿Sobra un 'pyc' o falta completar la instrucción?"
                    )

            # ── 18. RELOP inesperado ──
            elif p.type == 'RELOP':
                texto = self.errors.getText()
                lineas = texto.split('\n')
                linea_actual = lineas[row - 1].strip() if row <= len(lineas) else ''

                estructuras = ['evee', 'wailord', 'forretres']
                estructura_detectada = next(
                    (e for e in estructuras if linea_actual.startswith(e)), None
                )

                if estructura_detectada and 'ps' not in linea_actual:
                    sint = SINTAXIS_CORRECTA.get(estructura_detectada.upper(), '')
                    self.errors.encolar_error(
                        f"Error sintáctico: '{estructura_detectada}' sin paréntesis 'ps'/'pc' "
                        f"en fila {row}, col {col}. "
                        f"Sintaxis correcta: {sint}"
                    )
                else:
                    self.errors.encolar_error(
                        f"Error sintáctico: operador relacional '{p.value}' inesperado "
                        f"en fila {row}, col {col}."
                    )

            # ── Fallback ──
            else:
                self.errors.encolar_error(
                    f"Error sintáctico: token inesperado '{token}' "
                    f"en fila {row}, col {col}."
                )

            return _sync_after_error(self, p)

        except Exception as e:
            self.errors.encolar_error(
                f"Error interno al analizar token inesperado: {str(e)}"
            )
            self.parser.errok()
            return None

    else:
        self.errors.encolar_error(
            "Error sintactico: final inesperado del archivo. "
            "Falta cerrar un bloque 'lc' o completar una instruccion?"
        )
        self.parser.errok()
        return None
