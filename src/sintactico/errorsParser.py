def p_error(self, p):
    
    # Manejo de errores de sintaxis con sugerencias específicas para cada tipo de error común.
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
}




    if p:
        try:
            col = self.errors.find_column(p)
            row = self.errors.find_line(p)
            token = p.value.lower() if isinstance(p.value, str) else str(p.value)

            # 1 IF mal formado
            if p.type == 'EVEE':
                self.errors.encolar_error(
                    f"Error: se esperaba '(' después de EVEE (if) en fila {row}, col {col}."
                )

            # 2 ELSE mal ubicado
            elif p.type == 'EKANS':
                self.errors.encolar_error(
                    f"Error: EKANS (else) fuera de lugar en fila {row}, col {col}. "
                    f"¿Falta cerrar correctamente el bloque anterior?"
                )

            # 3 FOR mal formado
            elif p.type == 'FORRETRES':
                self.errors.encolar_error(
                    f"Error: FORRETRES (for) mal formado en fila {row}, col {col}. "
                    f"¿Faltan los ';' o los paréntesis?"
                )

            # 4 SWITCH mal formado
            elif p.type == 'SWELLO':
                self.errors.encolar_error(
                    f"Error: SWELLO (switch) mal formado en fila {row}, col {col}."
                )

            # 5 CASE sin :
            elif p.type == 'KECLEON':
                self.errors.encolar_error(
                    f"Error: falta ':' después del KECLEON (case) en fila {row}, col {col}."
                )

            # 6 DEFAULT mal ubicado
            elif p.type == 'DEOXYS':
                self.errors.encolar_error(
                    f"Error: DEOXYS (default) debe ir al final del switch en fila {row}, col {col}."
                )

            # 7 BREAK fuera de ciclo
            elif p.type == 'BRELOOM':
                self.errors.encolar_error(
                    f"Error: BRELOOM (break) fuera de un ciclo o switch en fila {row}, col {col}."
                )

            # 8 PRINT mal formado
            elif p.type == 'PIKACHU':
                self.errors.encolar_error(
                    f"Error: PIKACHU (print) mal formado en fila {row}, col {col}. "
                    f"¿Faltan paréntesis o punto y coma?"
                )

            # 9 FUNCTION mal formada
            elif p.type == 'SUICUNE':
                self.errors.encolar_error(
                    f"Error: declaración de función SUICUNE mal formada en fila {row}, col {col}."
                )

            # 10 Tipo sin identificador
            elif p.type in {'ENTEI', 'FLOATZEL', 'CHARIZAR', 'BOOFALANT', 'STANTLER', 'GARDEVOIR'}:
                self.errors.encolar_error(
                    f"Error: después del tipo '{token}' se esperaba un identificador en fila {row}, col {col}."
                )

            # 11 Paréntesis y llaves
            elif p.type == 'LBRACE':
                self.errors.encolar_error(
                    f"Error: '{{' sin estructura válida anterior en fila {row}, col {col}."
                )
            # 12 Llave de cierre sin apertura
            elif p.type == 'RBRACE':
                self.errors.encolar_error(
                    f"Error: '}}' sin apertura correspondiente en fila {row}, col {col}."
                )
            # 13 Paréntesis sin cierre o apertura
            elif p.type == 'LPAREN':
                self.errors.encolar_error(
                    f"Error: '(' sin cierre en fila {row}, col {col}."
                )

            #14 Paréntesis de cierre sin apertura
            elif p.type == 'RPAREN':
                self.errors.encolar_error(
                    f"Error: ')' sin apertura en fila {row}, col {col}."
                )

            # 15 Símbolo inesperado
            elif p.type == 'NUMBER':
                self.errors.encolar_error(
                    f"Error: número inesperado '{p.value}' en fila {row}, col {col}."
                )

            # 14 Identificador inesperado
            elif p.type == 'IDENTIFIER':
                self.errors.encolar_error(
                    f"Error: identificador inesperado '{p.value}' en fila {row}, col {col}. "
                    f"¿Falta un ';' o se cerró mal un bloque?"
                )

            # Ejemplo para PIKACHU:
            elif p.type == 'PIKACHU':
                sintaxis = SINTAXIS_CORRECTA.get('PIKACHU', '')
                self.errors.encolar_error(
                    f"Error: PIKACHU (print) mal formado en fila {row}, col {col}. "
                    f"Sintaxis correcta: {sintaxis}"
                )

            # Ejemplo para tipos (ENTEI, FLOATZEL, etc.):
            elif p.type in {'ENTEI', 'FLOATZEL', 'CHARIZAR', 'BOOFALANT', 'STANTLER', 'GARDEVOIR'}:
                sintaxis = SINTAXIS_CORRECTA.get(p.type.upper(), '')
                self.errors.encolar_error(
                    f"Error: después del tipo '{token}' se esperaba un identificador "
                    f"en fila {row}, col {col}. Sintaxis correcta: {sintaxis}"
                )


            #  Fallback
            else:
                self.errors.encolar_error(
                    f"Error de sintaxis en '{token}' en fila {row}, col {col}."


                )




        except Exception as e:
            self.errors.encolar_error(
                "Error interno analizando token inesperado: " + str(e)
            )

    else:
        self.errors.encolar_error(
            "Error de sintaxis: final inesperado del archivo. "
            "¿Falta cerrar una llave '}' o completar una instrucción?"
        )