import ply.yacc as yacc
from src.sintactico.errorsParser import p_error
from src.semantico.handle import handle_expression_statement


class Parser:
    def __init__(self, lexer, sintactic_errors, semantic_handler):
        self.lexer    = lexer
        self.errors   = sintactic_errors
        self.semantic = semantic_handler
        self.tokens   = lexer.tokens
        self.parser   = yacc.yacc(module=self, debug=False, write_tables=False)

    precedence = (
        ('nonassoc', 'GT', 'LT', 'RELOP'),
        ('left', 'MAS', 'MENOS'),
        ('left', 'MUL', 'DIV'),
    )

    # ── Programa ──────────────────────────────

    def p_program(self, p):
        '''program : statement
                   | program statement'''
        if len(p) == 2:
            p[0] = [p[1]] if p[1] is not None else []
        else:
            list1 = p[1] if isinstance(p[1], list) else []
            list2 = [p[2]] if p[2] is not None else []
            p[0] = list1 + list2

    def p_program_empty(self, p):
        'program : '
        p[0] = []

    # ── Statement ─────────────────────────────

    def p_statement(self, p):
        '''statement : function_declaration
                     | declaration
                     | assignment
                     | while_loop
                     | do_while_loop
                     | for_loop
                     | if_statement
                     | switch_statement
                     | method_call SEMICOLON
                     | break_statement
                     | return_statement
                     | print_statement'''
        p[0] = p[1] if p[1] is not None else (lambda: None)

    # ── Print ─────────────────────────────────

    def p_print_statement(self, p):
        '''print_statement : PIKACHU LPAREN expression RPAREN SEMICOLON
                           | PIKACHU STRING_LITERAL SEMICOLON'''
        if len(p) == 6:
            p[0] = self.semantic.handle_print(p[3])
        else:
            val = self.semantic.handle_factor(p[2])
            p[0] = self.semantic.handle_print(val)

    def p_print_error(self, p):
        'print_statement : PIKACHU IDENTIFIER SEMICOLON'
        fila = self.errors.find_line(p.slice[2])
        col  = self.errors.find_column(p.slice[2])
        self.errors.encolar_error(
            f"Error sintáctico: 'pikachu' mal formado en fila {fila}, col {col}. "
            f"Sintaxis correcta: pikachu ps expresion pc pyc"
        )
        p[0] = None

    # ── Declaraciones ─────────────────────────

    def p_declaration(self, p):
        '''declaration : ENTEI IDENTIFIER SEMICOLON
                       | ENTEI IDENTIFIER EQUALS expression SEMICOLON
                       | FLOATZEL IDENTIFIER SEMICOLON
                       | FLOATZEL IDENTIFIER EQUALS expression SEMICOLON
                       | CHARIZAR IDENTIFIER SEMICOLON
                       | CHARIZAR IDENTIFIER EQUALS expression SEMICOLON
                       | BOOFALANT IDENTIFIER SEMICOLON
                       | BOOFALANT IDENTIFIER EQUALS expression SEMICOLON
                       | STANTLER IDENTIFIER SEMICOLON
                       | STANTLER IDENTIFIER EQUALS expression SEMICOLON'''
        
        identifier = p[2]
        value      = p[4] if len(p) > 4 else None
        type_      = p[1]
        p[0] = self.semantic.handle_declaration(identifier, type_, value=value)

    def p_declaration_no_semicolon(self, p):
        '''declaration_no_semicolon : ENTEI IDENTIFIER EQUALS expression
                                    | FLOATZEL IDENTIFIER EQUALS expression
                                    | CHARIZAR IDENTIFIER EQUALS expression
                                    | BOOFALANT IDENTIFIER EQUALS expression
                                    | STANTLER IDENTIFIER EQUALS expression'''
        
        identifier = p[2]
        value      = p[4]
        type_      = p[1]
        p[0] = self.semantic.handle_declaration(identifier, type_, value=value)
        

    # ── Asignación ────────────────────────────

    def p_assignment(self, p):
        'assignment : IDENTIFIER EQUALS expression SEMICOLON'
        p[0] = self.semantic.handle_assignment(p[1], p[3])

    def p_assignment_no_semicolon(self, p):
        'assignment_no_semicolon : IDENTIFIER EQUALS expression'
        p[0] = self.semantic.handle_assignment(p[1], p[3])

    # ── Ciclos ────────────────────────────────

    def p_for_init(self, p):
        '''for_init : declaration_no_semicolon
                    | assignment_no_semicolon'''
        p[0] = p[1]

    def p_for_loop(self, p):
        'for_loop : FORRETRES LPAREN for_init SEMICOLON expression SEMICOLON assignment_no_semicolon RPAREN LBRACE program RBRACE'
        init = p[3]; expression = p[5]; update = p[7]
        body = p[10] if isinstance(p[10], list) else []
    
        p[0] = self.semantic.handle_for(init, expression, update, body)

    def p_do_while_loop(self, p):
        'do_while_loop : DODUO LBRACE program RBRACE WAILORD LPAREN expression RPAREN SEMICOLON'
        body      = p[3] if isinstance(p[3], list) else []
        expression = p[7]
        
        p[0] = self.semantic.handle_do_while(expression, body)

    def p_while_loop(self, p):
        'while_loop : WAILORD LPAREN expression RPAREN LBRACE program RBRACE'
        body      = p[6] if isinstance(p[6], list) else []
        expression = p[3]
       
        p[0] = self.semantic.handle_while(expression, body)

    # ── If / else ─────────────────────────────

    def p_if_statement(self, p):
        '''if_statement : EVEE LPAREN expression RPAREN LBRACE program RBRACE
                        | EVEE LPAREN expression RPAREN LBRACE program RBRACE EKANS LBRACE program RBRACE'''
        expression = p[3]
        if_body   = p[6]
        else_body = p[10] if len(p) > 8 else []
        p[0] = self.semantic.handle_if(expression, if_body, else_body)

    # ── Switch ────────────────────────────────

    def p_switch_statement(self, p):
        '''switch_statement : SWELLO LPAREN IDENTIFIER RPAREN LBRACE cases default_case RBRACE
                            | SWELLO LPAREN IDENTIFIER RPAREN LBRACE cases RBRACE'''
        default = p[7] if len(p) == 9 else []
        cases   = p[6]
        p[0] = self.semantic.handle_switch(p[3], cases, default)

    def p_cases(self, p):
        '''cases : cases case
                | case'''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

    def p_case(self, p):
        'case : KECLEON value COLON program'
        body = p[4] if isinstance(p[4], list) else [p[4]]
        p[0] = (p[2], body)

    def p_default_case(self, p):
        '''default_case : DEOXYS COLON program
                        | empty'''
        if len(p) > 2:
            p[0] = p[3] if isinstance(p[3], list) else [p[3]]
        else:
            p[0] = []

    def p_value(self, p):
        '''value : NUMBER
                 | STRING_LITERAL
                 | CHAR_LITERAL
                 | BOOLEAN_LITERAL'''
        p[0] = p[1]

    # ── Break / Return ────────────────────────

    def p_break_statement(self, p):
        'break_statement : BRELOOM SEMICOLON'
        p[0] = self.semantic.handle_break()

    def p_return_statement(self, p):
        'return_statement : RAIKOU expression SEMICOLON'
        value = p[2]
        def do_return():
            self.semantic.handle_return(value)()
        p[0] = do_return

    # ── Expresiones ───────────────────────────

    def p_expression(self, p):
        '''expression : expression MAS term
                    | expression MENOS term
                    | expression GT term
                    | expression LT term
                    | expression RELOP term'''
        p[0] = (p[1], p[2], p[3])

    def p_expression_term(self, p):
        'expression : term'
        p[0] = p[1]

    def p_term(self, p):
        '''term : term MUL factor
                | term DIV factor'''
        p[0] = (p[1], p[2], p[3])

    def p_term_factor(self, p):
        'term : factor'
        p[0] = p[1]

    def p_factor(self, p):
        '''factor : NUMBER
                  | IDENTIFIER
                  | STRING_LITERAL
                  | CHAR_LITERAL
                  | BOOLEAN_LITERAL
                  | LPAREN expression RPAREN
                  | method_call'''
        if len(p) == 4:
            p[0] = p[2]
        elif len(p) == 2 and callable(p[1]):
            p[0] = p[1]
        else:
            p[0] = self.semantic.handle_factor(p[1])

    # ── Funciones ─────────────────────────────

    def p_function_declaration(self, p):
        '''function_declaration : SUICUNE type IDENTIFIER LPAREN params RPAREN LBRACE program RBRACE
                                | SUICUNE type IDENTIFIER LPAREN RPAREN LBRACE program RBRACE
                                | GARDEVOIR IDENTIFIER LPAREN params RPAREN LBRACE program RBRACE
                                | GARDEVOIR IDENTIFIER LPAREN RPAREN LBRACE program RBRACE'''

        token_type = p.slice[1].type

        if token_type == 'GARDEVOIR':
            name        = p[2]
            return_type = 'gardevoir'
            if len(p) == 9:
                params = p[4]
                body   = p[7]
            else:
                params = []
                body   = p[6]
        else:
            name        = p[3]
            return_type = p[2]
            if len(p) == 10:
                params = p[5]
                body   = p[8]
            else:
                params = []
                body   = p[7]

        self.semantic.register_function(name, return_type, params, body)

        def define():
            self.semantic.execute_function_declaration(name)

        p[0] = define

    # ── Parámetros ────────────────────────────

    def p_params(self, p):
        '''params : param
                  | params COMMA param'''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    def p_param(self, p):
        '''param : ENTEI IDENTIFIER
                 | FLOATZEL IDENTIFIER
                 | CHARIZAR IDENTIFIER
                 | BOOFALANT IDENTIFIER
                 | STANTLER IDENTIFIER'''
        p[0] = (p[1], p[2])

    # ── Llamada a función ─────────────────────

    def p_method_call(self, p):
        '''method_call : IDENTIFIER LPAREN args RPAREN
                       | IDENTIFIER LPAREN RPAREN'''
        method_name = p[1]
        args        = p[3] if len(p) == 5 else []
        p[0] = self.semantic.handle_method_call(method_name, args)

    def p_args(self, p):
        '''args : expression
                | args COMMA expression'''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]

    # ── Tipos ─────────────────────────────────

    def p_type(self, p):
        '''type : ENTEI
                | FLOATZEL
                | CHARIZAR
                | BOOFALANT
                | GARDEVOIR'''
        p[0] = p[1]

    def p_empty(self, p):
        'empty :'
        p[0] = []

    # ── Statement con expresión suelta ────────

    def p_statement_expr(self, p):
        'statement : expression SEMICOLON'
        # Obtener línea aproximada del token SEMICOLON
        try:
            line = p.slice[2].lineno
        except Exception:
            line = None
        p[0] = handle_expression_statement(self.semantic, p[1], line)

    # ── Error ─────────────────────────────────

    def p_error(self, p):
        if p is None:
            self.errors.encolar_error(
                "Error sintáctico: final inesperado del archivo. "
                "¿Falta cerrar una llave '}' o completar una instrucción?"
            )
            return
        try:
            p_error(self, p)
        except Exception as e:
            print("Error al llamar al metodo p_error:", e)

    # ── Parse ─────────────────────────────────

    def parse(self, data, execute=True):
        self.lexer.lexer.input(data)
        parsed = self.parser.parse(data, lexer=self.lexer.lexer)
        print("Parsing completado.")

        if execute and parsed:
            print("Ejecutando AST...")
            

            for stmt in parsed:
                if callable(stmt):
                    stmt()

            self.semantic.symbol_table.guardar_snapshot_final()
            

        return parsed