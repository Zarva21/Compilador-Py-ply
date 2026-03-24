SINTAXIS_CORRECTA = {
    'PIKACHU':   'pikachu( expresion );',
    'EVEE':      'evee ( condicion ) { ... }',
    'EKANS':     '} ekans {',
    'FORRETRES': 'forretres ( init ; condicion ; update ) { ... }',
    'WAILORD':   'wailord ( condicion ) { ... }',
    'DODUO':     'doduo { ... } wailord ( condicion );',
    'SWELLO':    'swello ( identificador ) { kecleon valor: ... }',
    'KECLEON':   'kecleon valor : instrucciones',
    'SUICUNE':   'suicune tipoDato nombreFuncion() { ... }',
    'RAIKOU':    'raikou expresion ;',
    'BRELOOM':   'breloom ;',
    'ENTEI':     'entei nombreVariable = valor ;',
    'FLOATZEL':  'floatzel nombreVariable = valor ;',
    'CHARIZAR':  'charizar nombreVariable = valor ;',
    'BOOFALANT': 'boofalant nombreVariable = valor ;',
    'STANTLER':  'stantler nombreVariable = valor ;',
    'GARDEVOIR': 'gardevoir nombreFuncion() { ... }',
}

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

            # ── 14. Paréntesis y llaves ──
            elif p.type == 'LBRACE':
                self.errors.encolar_error(
                    f"Error sintáctico: '{{' sin estructura válida anterior "
                    f"en fila {row}, col {col}."
                )

            elif p.type == 'RBRACE':
                self.errors.encolar_error(
                    f"Error sintáctico: '}}' sin apertura correspondiente "
                    f"en fila {row}, col {col}."
                )

            elif p.type == 'LPAREN':
                self.errors.encolar_error(
                    f"Error sintáctico: '(' inesperado o sin cierre "
                    f"en fila {row}, col {col}."
                )

            elif p.type == 'RPAREN':
                self.errors.encolar_error(
                    f"Error sintáctico: ')' sin apertura correspondiente "
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
                
                # Buscar hacia atrás la última línea con contenido real (no vacía ni comentario)
                linea_anterior = ''
                for i in range(row - 2, -1, -1):
                    candidata = lineas[i].strip()
                    if candidata and not candidata.startswith('#') and not candidata.startswith('/*'):
                        linea_anterior = candidata
                        num_linea = i + 1
                        break
                
                if linea_anterior and not linea_anterior.endswith(';') \
                and not linea_anterior.endswith('{') \
                and not linea_anterior.endswith('}'):
                    self.errors.encolar_error(
                        f"Error sintáctico: falta ';' al final de la línea {num_linea}. "
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
                self.errors.encolar_error(
                    f"Error sintáctico: ';' inesperado en fila {row}, col {col}. "
                    f"¿Sobra un ';' o falta completar la instrucción?"
                )

            # ── Fallback ──
            else:
                self.errors.encolar_error(
                    f"Error sintáctico: token inesperado '{token}' "
                    f"en fila {row}, col {col}."
                )

        except Exception as e:
            self.errors.encolar_error(
                f"Error interno al analizar token inesperado: {str(e)}"
            )

    else:
        self.errors.encolar_error(
            "Error sintáctico: final inesperado del archivo. "
            "¿Falta cerrar una llave '}' o completar una instrucción?"
        )