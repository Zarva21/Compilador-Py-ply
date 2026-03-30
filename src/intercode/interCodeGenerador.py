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

    def get_cond_index(self, base_name='cond'):
        if base_name not in self.condition_counter:
            self.condition_counter[base_name] = 0
        index = self.condition_counter[base_name]
        self.condition_counter[base_name] += 1
        return index

    def register_condition(self, cond_name, fn=None):
        self.conditions[cond_name] = fn