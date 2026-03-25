import ply.lex as lex

# Implementación del Lexer con sugerencias léxicas usando Levenshtein para palabras reservadas mal escritas.
def distancia_levenshtein(s1, s2):
    """Calcula qué tan diferentes son dos palabras (menor = más parecidas)."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    return dp[m][n]

def sugerir_palabra_reservada(palabra, reservadas, umbral=3):
    """Devuelve la palabra reservada más cercana si está dentro del umbral."""
    mejor = None
    menor_dist = umbral + 1
    for reservada in reservadas:
        dist = distancia_levenshtein(palabra.lower(), reservada)
        if dist < menor_dist:
            menor_dist = dist
            mejor = reservada
    return mejor if menor_dist <= umbral else None



#Se indica para cada token
class Lexer:

    


    
    SUGERENCIAS_LEXICAS = {
    'int':      'entei',
    'float':    'floatzel',
    'string':   'charizar',
    'bool':     'boofalant',
    'char':     'stantler',
    'if':       'evee',
    'else':     'ekans',
    'for':      'forretres',
    'while':    'wailord',
    'do':       'doduo',
    'switch':   'swello',
    'case':     'kecleon',
    'default':  'deoxys',
    'break':    'breloom',
    'print':    'pikachu',
    'return':   'raikou',
    'function': 'suicune',
    'void':     'gardevoir',
    'println':  'pikachu',
    'printf':   'pikachu',
    'cout':     'pikachu',
}



    tokens = [
        'NUMBER', 'IDENTIFIER', 'EQUALS', 'SEMICOLON', 'LBRACE', 'RBRACE',
        'LPAREN', 'RPAREN', 'GT', 'LT', 'DOT', 'COMMA', 
        'RELOP', 'STRING_LITERAL', 'CHAR_LITERAL', 'COLON',

        'MAS', 'MENOS', 'MUL', 'DIV'
    ]

    reserved = {
        #Ejemplo, aqui se pone la lista de palabras reservadas 
        
        'entei': 'ENTEI',
        'floatzel': 'FLOATZEL',
        'Charizar' :'CHARIZAR',
        'boofalant':'BOOFALANT',
        'stantler' : 'STANTLER', 
        'evee' : 'EVEE',
        'ekans' : 'EKANS',
        'wailord' : 'WAILORD',
        'doduo' : 'DODUO',
        'forretres' : 'FORRETRES',
        'swello' : 'SWELLO',
        'kecleon' : 'KECLEON',
        'deoxys' : 'DEOXYS',
        'breloom' : 'BRELOOM',
        'pikachu': 'PIKACHU',
        'raikou' : 'RAIKOU',
        'suicune': 'SUICUNE',
        'gardevoir' : 'GARDEVOIR'
        
        }
    
    #Ahora pues hay que especificar los tokens 
    tokens += list(reserved.values())

    t_COLON = r':'
    t_RELOP = r'==|!=|<|>|<=|>='
    
    t_MAS = r'\+'
    t_MENOS = r'-'
    t_MUL = r'\*'
    t_DIV = r'/'
    
    t_EQUALS = r'='
    t_SEMICOLON = r';'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_GT = r'>'
    t_LT = r'<'
    t_DOT = r'\.'
    t_COMMA = r','
    


    #Es para espacios y tabs
    t_ignore = ' \t'

#Especificar los Tokens


    def tokenize(self, data):
        self.lexer.input(data)
        tokens = []
        for tok in self.lexer:
            fila, col = self.get_pos(tok)
            tokens.append((tok.type, tok.value, fila, col))
        return tokens

    #Ejecutar el lexer
    def __init__(self, errors):
        self.errors = errors
        self.reported_errors = set()
        self.lexer = lex.lex(module=self)

    def tokenize(self, data):
        self.lexer.input(data)
        tokens = [(tok.type, tok.value) for tok in self.lexer]
        return tokens



    #Revisa para las palabras reservadas
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        t.type = self.reserved.get(t.value, 'IDENTIFIER')

        if t.type == 'IDENTIFIER':
            # Primero revisa si es una palabra de otro lenguaje (int, if, etc.)
            sugerencia = self.SUGERENCIAS_LEXICAS.get(t.value.lower())
            
            # Si no, usa Levenshtein para ver si se parece a una palabra reservada
            if not sugerencia:
                sugerencia = sugerir_palabra_reservada(t.value, self.reserved.keys(), umbral=2)
            
            if sugerencia:
                fila, col = self.get_pos(t)
                self.encolar_error_unico(
                    f"Error léxico: '{t.value}' no reconocido en fila {fila}, col {col}. "
                    f"¿Quisiste escribir '{sugerencia}'?"
                )

        return t

    #Comentarios 
    def t_COMMENT_SINGLELINE(self,t):
        r'\#.*'
        pass

    def t_COMMENT_MULTILINE(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')
        pass



    #Numeros 
    def t_NUMBER(self, t):
        r'\d+(\.\d+)?'
        t.value = float(t.value) if '.' in t.value else int(t.value)
        return t

        #Linea de numeros 
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)



    #Errores

        #manejo de errores 
    def get_pos(self, t):
        fila = t.lexer.lexdata[:t.lexpos].count('\n') + 1
        last_newline = t.lexer.lexdata.rfind('\n', 0, t.lexpos)
        columna = t.lexpos + 1 if last_newline < 0 else t.lexpos - last_newline
        return fila, columna

    def encolar_error_unico(self, msg):
        if msg not in self.reported_errors:
            self.reported_errors.add(msg)
            self.errors.encolar_error(msg)

        #Error Lexico
    def t_error(self, t):
        fila, col = self.get_pos(t)
        self.encolar_error_unico(f"Error léxico: carácter no reconocido '{t.value[0]}' en la fila {fila} y columna {col}.")
        t.lexer.skip(1)

    def get_current_token(self):
        return self.lexer.token()

        #Poner un Error 
    def set_error(self, error, position):
        token = self.get_current_token()
        fila, col = self.get_pos(token)
        self.encolar_error_unico(f"Error léxico: '{error}' en la fila {fila} y columna {col}")

    #Reglas

    def t_STRING_LITERAL(self, t):
        r'"([^"\n\\]|\\.)*("?)'
        # Verificar si cerró correctamente
        if not t.value.endswith('"') or t.value.count('"') < 2:
            fila, col = self.get_pos(t)
            self.encolar_error_unico(
                f"Error léxico: cadena no cerrada en fila {fila}, col {col}. "
                f"¿Olvidaste el '\"' de cierre?"
            )
            # Saltar hasta fin de línea
            while t.lexer.lexpos < len(t.lexer.lexdata) and t.lexer.lexdata[t.lexer.lexpos] != '\n':
                t.lexer.lexpos += 1
            return None  # No retornar token, era inválido
        
        # Cadena válida — quitar las comillas
        t.value = t.value[1:-1]
        if t.value.strip() == "":
            fila, col = self.get_pos(t)
            self.encolar_error_unico(f"Advertencia: cadena vacía en fila {fila}, columna {col}.")
        return t

    def t_CHAR_LITERAL_UNCLOSED(self, t):
        r"'([^\\'\n]|\\.)*$"
        fila, col = self.get_pos(t)
        self.encolar_error_unico(f"Error léxico: carácter no cerrado en la fila {fila} y columna {col}.")
        t.lexer.skip(1)

    def t_CHAR_LITERAL(self, t):
        r"'(.*?)'"
        contenido = t.value[1:-1]
        if len(contenido) != 1:
            fila, col = self.get_pos(t)
            self.encolar_error_unico(f"Error léxico: carácter inválido '{t.value}' en fila {fila}, columna {col}.")
            return None
        t.value = contenido
        return t
    
