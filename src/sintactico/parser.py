import ply.yacc as yacc
from src.sintactic.errorsParser import p_error

class Parser: 
    def __init__(self,lexer,sintactic_errors, semantic_handler):

        self.lexer = lexer
        self.errors = sintactic_errors
        self.semantic = semantic_handler
        self.tokens = lexer.tokens
        self.parser = yacc.yacc(module=self, debug=False, write_tables=False)
               
        precedence = (
        ('left', 'MAS', 'MENOS'),
        ('left', 'MUL', 'DIV'),
    )
        
    #Manejador de Statement, de E y de 1 o mas, siendo acumulados en listas y acada una asignadole stmt1 stmt2 y asi 

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

    def p_statement(self, p):
        '''statement : method_declaration
                    | declaration
                    | assignment
                    | while_loop
                    | do_while_loop
                    | for_loop
                    | if_statement
                    | method_call SEMICOLON
                    | expression SEMICOLON
                    | break_statement
                    | print_statement'''
        p[0] = p[1] if p[1] is not None else (lambda: None)  



    #Reglas para cada uno de las opciones 
    #Reconociendo los tockens y su orden, dandole casos donde que tiene que hacer para cada uno


    def p_print_statement(self, p):
        'print_statement : PIKACHU LPAREN expression RPAREN SEMICOLON'
        p[0] = self.semantic.handle_print(p[3])

    def p_for_init(self, p):
        '''for_init : declaration_no_semicolon
                    | assignment_no_semicolon'''
        p[0] = p[1]

    def p_assignment_no_semicolon(self, p):
        'assignment_no_semicolon : IDENTIFIER EQUALS expression'
        p[0] = self.semantic.handle_assignment(p[1], p[3])


    #Tener que hacer declaraciones en el cual uno sea en caso para uso en for, ya que tiene sus pripios ; y luego tener para si lo normal de declaracion de variables

    def p_declaration_no_semicolon(self, p):
        '''declaration_no_semicolon : ENTEI IDENTIFIER EQUALS expression
                                    | FLOATZEL IDENTIFIER EQUALS expression
                                    | CHARIZAR IDENTIFIER EQUALS expression
                                    | BOOFALANT IDENTIFIER EQUALS expression
                                    | STANTLER IDENTIFIER EQUALS expression'''
        
        scope = 'global' if not self.semantic.symbol_table.scope_stack else 'local'
        identifier = p[2]
        value = p[4]
        type_ = p[1]
        p[0] = self.semantic.handle_declaration(identifier, type_, scope, value)


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
        scope = 'global' if not self.semantic.symbol_table.scope_stack else 'local'
        identifier = p[2]
        value = p[4] if len(p) > 4 else None
        type_ = p[1]
        p[0] = self.semantic.handle_declaration(identifier, type_, scope, value)

    #Condicionales
    #Ciclos


    def p_for_loop(self, p):
        'for_loop : FORRETRES LPAREN for_init SEMICOLON condition SEMICOLON assignment_no_semicolon RPAREN LBRACE program RBRACE'
        init = p[3]
        condition = p[5]
        update = p[7]
        body = p[10] if isinstance(p[10], list) else []

        if not callable(condition):
            self.errors.encolar_error(" La condición del for no es válida.")
            p[0] = lambda: None
            return

        p[0] = self.semantic.handle_for(init, condition, update, body)


    def p_do_while_loop(self, p):
        'do_while_loop : WAILORD LBRACE program RBRACE WALKER LPAREN condition RPAREN SEMICOLON'
        body = p[3] if isinstance(p[3], list) else []
        condition = p[7]

        if not callable(condition):
            self.errors.encolar_error(" La condición del do-while no es válida.")
            p[0] = lambda: None
            return

        p[0] = self.semantic.handle_do_while(condition, body)

    #IF

    def p_if_statement(self, p):
        '''if_statement : EVEE LPAREN condition RPAREN LBRACE program RBRACE
                        | EVEE LPAREN condition RPAREN LBRACE program RBRACE ROBBEN LBRACE program RBRACE'''
        condition = p[3]
        if_body = p[6]
        else_body = p[10] if len(p) > 8 else []

        def scoped_if():
            self.semantic.symbol_table.enter_scope()
            action = self.semantic.handle_if(condition, if_body, else_body)
            action()
            self.semantic.symbol_table.exit_scope()

        p[0] = scoped_if

    def p_condition(self, p):
        'condition : IDENTIFIER RELOP expression'
        print(f" Condición construida: {p[1]} {p[2]} {p[3]}")
        p[0] = self.semantic.evaluate_condition_dynamic(p[1], p[2], p[3])

    #switch

    def p_switch_statement(self, p):
        'statement : FORLAN LPAREN IDENTIFIER RPAREN LBRACE cases default_case RBRACE'
        print(f"Valor recibido para var_name en switch: {p[3]} | tipo: {type(p[3])}")
        p[0] = self.semantic.handle_switch(p[3], p[6], p[7])

    def p_empty(self, p):
        'empty :'
        p[0] = []

    #case

    def p_cases(self, p):
        '''cases : case
                | cases case'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

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
                 | CHAR_LITERAL'''
        p[0] = p[1]

    #break

    def p_break_statement(self, p):
        'break_statement : BRELOOM SEMICOLON'
        p[0] = self.semantic.handle_break()
    def p_error(self, p):
        try:
            p_error(self, p)
        except Exception as e:
            print("Error al llamar al metodo p_error:", e)




    #Operadores de +-*/


    def p_expression(self, p):
        '''expression : expression MAS term
                      | expression MENOS term
                      | term'''
        if len(p) == 4:
            p[0] = (p[1], p[2], p[3])
        else:
            p[0] = p[1]

    def p_term(self, p):
        '''term : term MUL factor
                | term DIV factor
                | factor'''
        if len(p) == 4:
            p[0] = (p[1], p[2], p[3])
        else:
            p[0] = p[1]



    def p_factor(self, p):
        '''factor : NUMBER
                | IDENTIFIER
                | STRING_LITERAL
                | CHAR_LITERAL'''
        print(f" Factor detectado: {p[1]}")
        p[0] = self.semantic.handle_factor(p[1])


    #Metodo

    def p_factor_method_call(self, p):
        'factor : method_call'
        p[0] = p[1]  # esto es una función callable, no se debe pasar por handle_factor

    def p_method_declaration(self, p):
        'method_declaration : IDENTIFIER LPAREN RPAREN LBRACE program RBRACE'

        method_name = p[1]
        method_body = p[5]

        def define():
            print(f"Definiendo método '{method_name}' (tipo: {type(method_name)})")
            print(f"Body del método (tipo: {type(method_body)}): {method_body}")
            self.semantic.handle_method_declaration(method_name, method_body)()

        p[0] = define

    def p_method_call(self, p):
        'method_call : IDENTIFIER LPAREN RPAREN'

        method_name = p[1]
        if not isinstance(method_name, str):
            self.errors.encolar_error(f"Error: nombre de método inválido: {method_name} (tipo: {type(method_name)})")
            p[0] = lambda: None
            return

        def call_with_scope():
            self.semantic.symbol_table.enter_scope()
            action = self.semantic.handle_method_call(method_name)
            action()
            self.semantic.symbol_table.exit_scope()

        p[0] = call_with_scope


    #Funciones


    





    def parse(self, data):
        self.lexer.lexer.input(data)
        parsed = self.parser.parse(data, lexer=self.lexer.lexer)
        print(" Parsing completado. Ejecutando AST...")
        self.semantic.symbol_table.enter_scope()
        if parsed:
            for stmt in parsed:
                print(f"STMT Desde el parser:{stmt}")
                if callable(stmt):
                    stmt()
        self.semantic.symbol_table.guardar_snapshot_final()
        self.semantic.symbol_table.toHtml()
        self.semantic.symbol_table.exit_scope()
        return parsed
