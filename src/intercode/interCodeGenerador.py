class interCodeGenerator:
    def __init__(self):
        self.temp_counter      = 0
        self.label_counter     = 0
        self.code              = []
        self.condition_counter = {}
        self.conditions        = {}

    def new_temp(self):
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp

    def emit(self, instruction):
        print(f"[EMIT] {instruction}")
        self.code.append(instruction)

    def get_code(self):
        return self.code

    def new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def generate_while(self):
        # ... emite etiquetas y condición ...
        self.emit(f"// INICIO WHILE")
        self.emit(f"{label_inicio}:")
        self.emit(f"t{n} = {cond_left} {op} {cond_right}")
        self.emit(f"if !(t{n}) goto {label_fin}")

        # ← AQUÍ está el fix: iterar hasta lc, no una sola instrucción
        while self.current_token != 'lc':
            self.generate_statement()   # procesa cada instrucción del bloque

        self.consume('lc')
        self.emit(f"goto {label_inicio}")
        self.emit(f"{label_fin}:")
        self.emit(f"// FIN WHILE")

    def get_cond_index(self, base_name='cond'):
        if base_name not in self.condition_counter:
            self.condition_counter[base_name] = 0
        index = self.condition_counter[base_name]
        self.condition_counter[base_name] += 1
        return index

    def register_condition(self, cond_name, fn=None):
        self.conditions[cond_name] = fn