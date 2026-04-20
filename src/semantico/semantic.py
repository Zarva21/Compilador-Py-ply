from src.intercode.optimize import Optimize
from src.semantico.handle import handle_declaration
from src.semantico.handle import handle_assignment
from src.semantico.handle import handle_expression
from src.semantico.handle import handle_expression_statement   # ← nuevo
from src.semantico.handle import handle_print
from src.semantico.handle import _get_value
from src.semantico.handle import _apply_operator
from src.semantico.handle import _evaluate_runtime
from src.semantico.handle import evaluate_condition_dynamic
from src.semantico.handle import handle_for
from src.semantico.handle import handle_do_while
from src.semantico.handle import handle_while
from src.semantico.handle import handle_method_declaration
from src.semantico.handle import handle_method_call
from src.semantico.handle import handle_if
from src.semantico.handle import handle_switch
from src.semantico.handle import _save_iteration_state
from src.semantico.handle import _resolve_ir


class Semantic:
    def __init__(self, symbol_table, errors, lexer, interCodeGenerator):
        self.symbol_table        = symbol_table
        self.errors              = errors
        self.lexer               = lexer
        self.methods             = {}
        self.intercode_generator = interCodeGenerator
        self.en_funcion          = False
        self.en_loop             = False   # FIX: flag para detectar contexto de loop

    # ── Registro inmediato de función ─────────────────────────────────────
    def register_function(self, name, return_type, params, body):
        self.methods[name] = {
            'return_type': return_type,
            'params':      params or [],
            'body':        body,
        }
        print(f"[REGISTRO] Función '{name}' registrada con params={params}")

    def execute_function_declaration(self, name):
        if name not in self.methods:
            return
        info = self.methods[name]
        handle_method_declaration(self, name, info['body'])()

    # ── Delegación a handle.py ────────────────────────────────────────────

    def handle_declaration(self, name, var_type, value=None):
        return handle_declaration(self, name, var_type, value)

    def handle_assignment(self, name, value):
        return handle_assignment(self, name, value)

    def handle_expression(self, left, operator, right):
        return handle_expression(self, left, operator, right)

    def handle_term(self, left, operator, right):
        return self.handle_expression(left, operator, right)

    def handle_factor(self, value):
        return value

    def handle_print(self, value):
        return handle_print(self, value)

    def _get_value(self, item):
        return _get_value(self, item)

    def _apply_operator(self, a, op, b):
        return _apply_operator(self, a, op, b)

    def _evaluate_runtime(self, val):
        return _evaluate_runtime(self, val)

    def _check_numeric(self, a, b):
        return isinstance(a, (int, float)) and isinstance(b, (int, float))

    def _op_error(self, op, a, b):
        self.errors.encolar_error(
            f"No se puede aplicar '{op}' entre {type(a).__name__} y {type(b).__name__}"
        )
        return None

    def evaluate_condition_dynamic(self, left, op, right):
        return evaluate_condition_dynamic(self, left, op, right)

    def handle_for(self, init_stmt, condition_fn, update_stmt, body):
        return handle_for(self, init_stmt, condition_fn, update_stmt, body)

    def handle_do_while(self, condition_fn, body):
        return handle_do_while(self, condition_fn, body)

    def handle_while(self, condition_fn, body):
        return handle_while(self, condition_fn, body)

    def handle_method_declaration(self, name, return_type, body, params=None):
        self.register_function(name, return_type, params or [], body)
        return handle_method_declaration(self, name, body)

    def handle_method_call(self, name, args=None):
        return handle_method_call(self, name, args or [])

    def handle_if(self, condition_fn, if_body, else_body):
        return handle_if(self, condition_fn, if_body, else_body)

    def handle_switch(self, var_name, cases, default_body):
        return handle_switch(self, var_name, cases, default_body)

    def handle_break(self):
        def action():
            self.intercode_generator.emit("goto END_SWITCH_LABEL")
        return action

    def handle_return(self, value):
        def action():
            ir_val = _resolve_ir(self, value)
            self.intercode_generator.emit(f"raikou {ir_val}")
        return action

    def getInterCode(self):
        return self.intercode_generator.code

    def optimize_intermediate_code(self):
        print("Ejecutando optimización del código intermedio...")
        optimizer = Optimize(self.intercode_generator.code)
        optimizer.optimize()
        self.intercode_generator.code = optimizer.get_optimized_ir()
        print("Código intermedio optimizado.")

    def _save_iteration_state(self):
        _save_iteration_state(self)