# Compilador Pokémon — Documento de Estudio Detallado

> Proyecto de Compiladores — Semestre 7  
> Implementado en Python con la librería **PLY** (Python Lex-Yacc)

---

## Tabla de Contenidos

1. [Visión General](#1-visión-general)
2. [El Lenguaje Pokémon](#2-el-lenguaje-pokémon)
3. [Arquitectura del Compilador](#3-arquitectura-del-compilador)
4. [Fase 1 — Análisis Léxico](#4-fase-1--análisis-léxico-lexerpy)
5. [Fase 2 — Análisis Sintáctico](#5-fase-2--análisis-sintáctico-parserpy)
6. [Fase 3 — Análisis Semántico](#6-fase-3--análisis-semántico)
7. [Fase 4 — Generación de Código Intermedio](#7-fase-4--generación-de-código-intermedio)
8. [Fase 5 — Optimización](#8-fase-5--optimización)
9. [Fase 6 — Generación de Código C++](#9-fase-6--generación-de-código-c)
10. [Manejo de Errores](#10-manejo-de-errores)
11. [Reporte HTML](#11-reporte-html)
12. [Flujo Completo de Ejecución](#12-flujo-completo-de-ejecución)
13. [Ejemplo Completo Anotado](#13-ejemplo-completo-anotado)

---

## 1. Visión General

El proyecto implementa un **compilador completo** para un lenguaje de programación inventado cuyas palabras reservadas son nombres de Pokémon. El compilador traduce código fuente escrito en este lenguaje a código C++ válido, pasando por todas las fases clásicas de compilación.

### ¿Por qué PLY?

PLY es la implementación Python de las herramientas clásicas `lex` y `yacc` de UNIX. Permite:
- Definir tokens con expresiones regulares (`lex`).
- Definir gramáticas con producciones BNF (`yacc`), usando el algoritmo LALR(1) internamente.

### Estructura de carpetas

```
Compilador-Py-ply/
├── main.py                     # Punto de entrada, orquesta el pipeline
├── servidor.py                 # Servidor web (alternativo)
├── src/
│   ├── lexer/lexer.py          # Analizador léxico
│   ├── sintactico/
│   │   ├── parser.py           # Analizador sintáctico
│   │   └── errorsParser.py     # Mensajes de error sintáctico enriquecidos
│   ├── semantico/
│   │   ├── semantic.py         # Fachada del análisis semántico
│   │   ├── handle.py           # Implementación de todas las acciones semánticas
│   │   └── symbolTable.py      # Tabla de símbolos con scopes
│   ├── intercode/
│   │   ├── interCodeGenerador.py  # Generador de código intermedio (IR)
│   │   └── optimize.py            # Optimizador del IR
│   ├── codeGen/codeGen.py      # Generador de código C++
│   └── Extras/errores.py       # Clase de errores y reporte HTML
├── txtPrueba/                  # Archivos de prueba en lenguaje Pokémon
└── reportes/                   # Reportes HTML generados
```

---

## 2. El Lenguaje Pokémon

El lenguaje tiene una **correspondencia directa** con C++/Java, pero con nombres de Pokémon como palabras clave. Todos los símbolos de puntuación también son palabras.

### 2.1 Tipos de datos

| Pokémon      | Tipo equivalente | Ejemplo                        |
|--------------|-----------------|--------------------------------|
| `entei`      | `int`           | `entei x as 5 pyc`             |
| `floatzel`   | `float`         | `floatzel pi as 3.14 pyc`      |
| `charizar`   | `char`          | `charizar letra as csAcs pyc`  |
| `stantler`   | `string`        | `stantler nombre as cdHolacd pyc` |
| `boofalant`  | `bool`          | `boofalant flag as true pyc`   |
| `gardevoir`  | `void`          | *(solo en funciones void)*     |

### 2.2 Palabras reservadas de control

| Pokémon      | Equivalente | Uso                          |
|--------------|------------|------------------------------|
| `evee`       | `if`       | Condicional                  |
| `ekans`      | `else`     | Alternativa del if           |
| `wailord`    | `while`    | Ciclo while                  |
| `forretres`  | `for`      | Ciclo for                    |
| `doduo`      | `do`       | Inicio do-while              |
| `swello`     | `switch`   | Switch                       |
| `kecleon`    | `case`     | Case del switch              |
| `deoxys`     | `default`  | Default del switch           |
| `breloom`    | `break`    | Break                        |
| `raikou`     | `return`   | Return                       |
| `suicune`    | `function` | Declaración de función con retorno |
| `gardevoir`  | `void`     | Función sin retorno          |
| `pikachu`    | `print`    | Imprimir                     |

### 2.3 Símbolos como palabras

Todos los símbolos de puntuación se escriben como palabras de dos letras:

| Palabra | Símbolo | Significado              |
|---------|---------|--------------------------|
| `as`    | `=`     | Asignación               |
| `pyc`   | `;`     | Punto y coma             |
| `ls`    | `{`     | Llave abierta            |
| `lc`    | `}`     | Llave cerrada            |
| `ps`    | `(`     | Paréntesis abierto       |
| `pc`    | `)`     | Paréntesis cerrado       |
| `ma`    | `>`     | Mayor que                |
| `me`    | `<`     | Menor que                |
| `su`    | `+`     | Suma                     |
| `re`    | `-`     | Resta                    |
| `mu`    | `*`     | Multiplicación           |
| `di`    | `/`     | División                 |
| `co`    | `,`     | Coma                     |
| `dp`    | `:`     | Dos puntos               |
| `ig`    | `==`    | Igual a                  |
| `ni`    | `!=`    | Diferente de             |
| `mei`   | `<=`    | Menor o igual            |
| `mai`   | `>=`    | Mayor o igual            |

### 2.4 Literales especiales

| Literal         | Sintaxis              | Ejemplo              |
|-----------------|-----------------------|----------------------|
| String          | Entre `cd...cd`       | `cdHola mundocd`     |
| Char            | Entre `cs...cs`       | `csAcs`              |
| Comentario      | Inicia con `cm`       | `cm esto es comentario` |
| Comentario bloque | Entre `icm...fcm`  | `icm bloque fcm`     |
| Booleano        | `true` / `false`      | `boofalant b as true pyc` |

### 2.5 Ejemplo de programa completo

```
cm Función que calcula el cuadrado
suicune entei cuadrado ps entei n pc ls
    raikou n mu n pyc
lc

entei contador as 0 pyc

wailord ps contador me 5 pc ls
    entei valor as cuadrado ps contador pc pyc
    
    swello ps valor pc ls
        kecleon 0 dp
            pikachu ps valor pc pyc
            breloom pyc
        kecleon 1 dp
            pikachu ps valor pc pyc
            breloom pyc
        deoxys dp
            pikachu ps valor pc pyc
            breloom pyc
    lc
    
    contador as contador su 1 pyc
lc
```

---

## 3. Arquitectura del Compilador

El pipeline sigue las **6 fases clásicas** de compilación:

```
Código fuente (lenguaje Pokémon)
        │
        ▼
┌──────────────────┐
│  Análisis Léxico │  → Tokens + Errores léxicos
│   (lexer.py)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│ Análisis Sintáctico  │  → AST implícito (lambdas) + Errores sintácticos
│   (parser.py)        │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Análisis Semántico  │  → Tabla de símbolos + Errores semánticos
│ (semantic.py/handle) │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Generación de Código Inter. │  → IR de 3 direcciones
│  (interCodeGenerador.py)     │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────┐
│  Optimización    │  → IR optimizado
│  (optimize.py)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│  Generación C++      │  → Archivo .cpp
│  (codeGen.py)        │
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│  Reporte HTML        │  → reportes/reporte_X.html
│  (main.py + errores) │
└──────────────────────┘
```

**Punto clave**: El compilador usa un enfoque de **AST como funciones lambda**. El parser construye acciones semánticas que devuelven funciones (`lambda`/closures). Luego `main.py` las ejecuta en orden, generando el IR de forma "interpretada".

---

## 4. Fase 1 — Análisis Léxico (`lexer.py`)

### 4.1 ¿Qué hace?

Convierte el texto fuente en una secuencia de **tokens**. Cada token tiene: tipo, valor, fila y columna.

### 4.2 Cómo funciona PLY Lex

PLY escanea el texto buscando coincidencias con reglas definidas como métodos (`t_NOMBRE`) o strings (`t_NOMBRE = r'...'`). Las reglas son expresiones regulares.

### 4.3 Tokens definidos

El lexer define dos categorías:

**Tokens base** (lista `tokens`):
```
NUMBER, IDENTIFIER, EQUALS, SEMICOLON, LBRACE, RBRACE,
LPAREN, RPAREN, GT, LT, DOT, COMMA, RELOP,
STRING_LITERAL, CHAR_LITERAL, COLON,
MAS, MENOS, MUL, DIV
```

**Palabras reservadas** (diccionario `reserved`): Todo lo que no es un token base. Cuando el lexer encuentra un `IDENTIFIER`, revisa si está en este diccionario y cambia su tipo. Por ejemplo, `wailord` → tipo `WAILORD`.

### 4.4 Reglas importantes

**Comentarios** (se ignoran, no generan tokens):
```python
def t_COMMENT_SINGLELINE(self, t):
    r'cm.*'          # Todo lo que sigue a 'cm' en la misma línea
    pass             # No retorna nada = token ignorado

def t_COMMENT_MULTILINE(self, t):
    r'icm(.|\n)*?fcm'  # Entre icm y fcm, incluyendo saltos de línea
    t.lexer.lineno += t.value.count('\n')
    pass
```

**Strings** (entre `cd...cd`):
```python
def t_STRING_LITERAL(self, t):
    r'cd[^\n]*?cd'
    t.value = t.value[2:-2]  # Quita los dos 'cd' delimitadores
    return t
```

**Chars** (entre `cs...cs`):
```python
def t_CHAR_LITERAL(self, t):
    r'cs(.*?)cs'
    t.value = t.value[2:-2]  # Quita 'cs' de apertura y cierre
    return t
```

**Números** (enteros y decimales):
```python
def t_NUMBER(self, t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t
```

**Identificadores y palabras reservadas** — la regla más importante:
```python
def t_IDENTIFIER(self, t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = self.reserved.get(t.value, 'IDENTIFIER')
    # Si no está en reserved → es IDENTIFIER (variable)
    # Si está en reserved → toma ese tipo (ej: WAILORD)
    ...
    return t
```

### 4.5 Sistema de sugerencias léxicas (Levenshtein)

El lexer implementa **corrección de errores léxicos** con dos estrategias:

1. **Tabla directa** (`SUGERENCIAS_LEXICAS`): mapea palabras de otros lenguajes a su equivalente Pokémon.
   - `int` → sugiere `entei`
   - `if` → sugiere `evee`
   - `while` → sugiere `wailord`

2. **Distancia de Levenshtein**: para errores tipográficos, calcula qué tan parecida es la palabra mal escrita a las palabras reservadas, con un umbral de 2 cambios.

```python
def distancia_levenshtein(s1, s2):
    # Programación dinámica O(m*n)
    # dp[i][j] = ediciones mínimas para convertir s1[:i] en s2[:j]
    dp[i][j] = dp[i-1][j-1]               # si son iguales
    dp[i][j] = 1 + min(insertar, borrar, sustituir)  # si no
```

Si el usuario escribe `wailrd` (umbral ≤ 2), el lexer sugiere `wailord`.

### 4.6 Cálculo de posición (fila/columna)

```python
def get_pos(self, t):
    lexdata = self.lexer.lexdata
    fila = lexdata[:t.lexpos].count('\n') + 1
    last_newline = lexdata.rfind('\n', 0, t.lexpos)
    columna = t.lexpos + 1 if last_newline < 0 else t.lexpos - last_newline
    return fila, columna
```

### 4.7 Deduplicación de errores

El lexer mantiene un `set` de errores ya reportados para no duplicar mensajes si el mismo problema aparece varias veces:
```python
def encolar_error_unico(self, msg):
    if msg not in self.reported_errors:
        self.reported_errors.add(msg)
        self.errors.encolar_error(msg)
```

---

## 5. Fase 2 — Análisis Sintáctico (`parser.py`)

### 5.1 ¿Qué hace?

Toma la secuencia de tokens y verifica que sigan la **gramática del lenguaje** (BNF). Si son correctos, construye el AST implícito. Si no, reporta errores sintácticos detallados.

### 5.2 Cómo funciona PLY Yacc

PLY genera un parser LALR(1) a partir de métodos `p_nombre`. Cada método tiene:
- Un docstring con la producción BNF
- Código Python que ejecuta cuando se reduce esa producción

```python
def p_while_loop(self, p):
    'while_loop : WAILORD LPAREN condition RPAREN LBRACE program RBRACE'
    #              p[0]    p[1]   p[2]      p[3]   p[4]    p[5]   p[6]    p[7]
    body = p[6]
    condition = p[3]
    p[0] = self.semantic.handle_while(condition, body)  # retorna una lambda
```

### 5.3 Precedencia de operadores

```python
precedence = (
    ('left', 'MAS', 'MENOS'),  # + y - tienen menor precedencia
    ('left', 'MUL', 'DIV'),    # * y / tienen mayor precedencia
)
```

### 5.4 Gramática completa (producciones clave)

**Programa**: secuencia de statements
```
program : statement
        | program statement
        | (vacío)
```

**Statement**: cualquier instrucción válida
```
statement : function_declaration | declaration | assignment
          | while_loop | do_while_loop | for_loop
          | if_statement | switch_statement
          | method_call SEMICOLON | break_statement
          | return_statement | print_statement
```

**Declaración de variable**:
```
declaration : ENTEI IDENTIFIER SEMICOLON
            | ENTEI IDENTIFIER EQUALS expression SEMICOLON
            | FLOATZEL ... | CHARIZAR ... | BOOFALANT ... | STANTLER ...
```

**Ciclos**:
```
for_loop   : FORRETRES LPAREN for_init SEMICOLON condition SEMICOLON
             assignment_no_semicolon RPAREN LBRACE program RBRACE
while_loop : WAILORD LPAREN condition RPAREN LBRACE program RBRACE
do_while   : DODUO LBRACE program RBRACE WAILORD LPAREN condition RPAREN SEMICOLON
```

**Condicional**:
```
if_statement : EVEE LPAREN condition RPAREN LBRACE program RBRACE
             | EVEE LPAREN condition RPAREN LBRACE program RBRACE EKANS LBRACE program RBRACE
condition    : expression RELOP expression
             | expression GT expression
             | expression LT expression
```

**Switch**:
```
switch_statement : SWELLO LPAREN IDENTIFIER RPAREN LBRACE cases default_case RBRACE
cases           : cases case | case
case            : KECLEON value COLON program
default_case    : DEOXYS COLON program | empty
```

**Funciones**:
```
function_declaration : SUICUNE type IDENTIFIER LPAREN params RPAREN LBRACE program RBRACE
                     | GARDEVOIR IDENTIFIER LPAREN params RPAREN LBRACE program RBRACE
params               : param | params COMMA param
param                : ENTEI IDENTIFIER | FLOATZEL IDENTIFIER | ...
method_call          : IDENTIFIER LPAREN args RPAREN | IDENTIFIER LPAREN RPAREN
```

**Expresiones** (con precedencia):
```
expression : expression MAS term | expression MENOS term | term
term       : term MUL factor | term DIV factor | factor
factor     : NUMBER | IDENTIFIER | STRING_LITERAL | CHAR_LITERAL
           | BOOLEAN_LITERAL | LPAREN expression RPAREN | method_call
```

### 5.5 AST como funciones (enfoque del proyecto)

En lugar de construir un árbol de objetos, el parser hace que cada producción devuelva una **función/closure** que realiza la acción semántica:

```python
def p_assignment(self, p):
    'assignment : IDENTIFIER EQUALS expression SEMICOLON'
    p[0] = self.semantic.handle_assignment(p[1], p[3])
    #      └── devuelve una lambda que se ejecutará después
```

Luego en `main.py`:
```python
for stmt in parsed:
    if callable(stmt):
        stmt()  # ejecuta cada lambda en orden
```

Esto permite que la **verificación semántica y la generación de IR** ocurran durante la ejecución del AST, no durante el parsing.

### 5.6 Manejo de errores sintácticos enriquecidos

`errorsParser.py` define una función `p_error` con ~18 casos específicos. Cuando el parser encuentra un token inesperado, en lugar de un mensaje genérico, genera un mensaje adaptado:

- Si el token es `WAILORD` (while) mal formado → muestra la sintaxis correcta
- Si falta `pyc` al final de una línea → sugiere dónde ponerlo
- Si hay un `lc` sin apertura correspondiente → lo dice explícitamente
- Si el token ya fue reportado como error léxico → lo ignora (no duplicar)

---

## 6. Fase 3 — Análisis Semántico

### 6.1 Estructura: Fachada + Implementación

El análisis semántico está dividido en dos archivos:

- **`semantic.py`**: Es la **fachada** (Facade pattern). Recibe llamadas del parser y las delega a `handle.py`. También mantiene el estado global (`methods`, `en_funcion`, `en_loop`).
- **`handle.py`**: Contiene la **implementación real** de todas las acciones semánticas.

### 6.2 Tabla de Símbolos (`symbolTable.py`)

Implementa scopes anidados con una **pila de diccionarios**:

```
scope_stack = [
    { "x": {type: "entei", value: 5, scope: "local"} },  ← scope actual
    { "y": {type: "floatzel", value: 3.14, scope: "local"} }  ← scope padre
]
global_scope = { "contador": {type: "entei", value: 0, scope: "global"} }
```

**Operaciones clave**:

| Método          | Qué hace                                           |
|-----------------|----------------------------------------------------|
| `enter_scope()` | Agrega un diccionario vacío a la pila              |
| `exit_scope()`  | Saca el tope de la pila, guarda en `closed_scopes` |
| `add_symbol()`  | Agrega variable al scope actual o global. Retorna `False` si ya existe |
| `update_symbol()` | Busca la variable de adentro hacia afuera (lexical scoping) |
| `get_symbol()`  | Busca la variable con la misma estrategia          |

**Snapshots**: Al finalizar el análisis, `guardar_snapshot_final()` guarda el estado completo para mostrarlo en el reporte HTML.

**`to_flat_dict()`**: Combina globales + locales activos + locales cerrados en un diccionario plano. Lo usa el generador de C++ para conocer los tipos de todas las variables.

### 6.3 Acciones semánticas en `handle.py`

#### `handle_declaration` — Declarar variable

```
1. Detectar si es scope global o local
2. Intentar registrar en la tabla de símbolos
   - Si ya existe → error semántico
3. Si tiene valor inicial:
   a. Si es una expresión (tupla) → resolver con _resolve_ir()
   b. Verificar compatibilidad de tipos → _check_declaration_type()
   c. Emitir instrucción IR: "nombre = valor"
4. Evaluar el valor real con _evaluate_runtime() y guardarlo en la tabla
```

#### `handle_assignment` — Asignar variable

```
1. Buscar la variable en la tabla → error si no existe
2. Verificar compatibilidad de tipos
3. Emitir IR: "nombre = valor"
4. Si NO estamos en un loop → actualizar la tabla con el nuevo valor
   Si SÍ estamos en un loop → NO actualizar (el valor puede cambiar N veces)
```

#### `_resolve_ir` — Resolver expresión a IR

Esta función convierte expresiones (posiblemente anidadas como tuplas) a instrucciones IR:

```python
# Para una expresión como (("x", "+", 3), "*", 2):
# Genera:
#   t0 = x + 3
#   t1 = t0 * 2
# y retorna "t1"
```

Si la expresión es una tupla `(izq, op, der)`:
1. Resuelve recursivamente izq → temp_left
2. Resuelve recursivamente der → temp_right
3. Verifica compatibilidad de tipos
4. Emite `tN = temp_left op temp_right`
5. Retorna `tN`

#### `_evaluate_runtime` — Evaluar valor en tiempo de compilación

Intenta calcular el valor real de una expresión **estáticamente** (en tiempo de compilación), para mostrarlo en la tabla de símbolos:

- `5` → `5` (número directo)
- `("x", "+", 3)` → busca el valor de `x` en la tabla, lo suma a `3`
- Variable de loop → retorna sentinel `_LOOP_MODIFIED` (valor dinámico, no calculable)
- Función callable → retorna `None` (no se puede evaluar estáticamente)

#### `_check_type_compatibility` — Verificar tipos en operaciones

Valida que no se mezclen tipos incompatibles:
- `stantler + stantler` → OK (concatenación de strings)
- `stantler + entei` → Error semántico
- `charizar + entei` → Error (aritmética no permitida con chars)
- `boofalant * floatzel` → Error (aritmética no permitida con booleanos)
- `entei + floatzel` → OK (promoción numérica)

#### Estructuras de control — generación de IR con etiquetas

**If-else** genera:
```
// INICIO IF
tN = condicion
if !(tN) goto L_false
  ... cuerpo if ...
goto L_end
L_false:
// ELSE
  ... cuerpo else ...
L_end:
// FIN IF
```

**While** genera:
```
// INICIO WHILE
L_start:
tN = condicion
if !(tN) goto L_end
  ... cuerpo ...
goto L_start
L_end:
// FIN WHILE
```

**For** genera:
```
inicialización
// INICIO FOR
L_start:
tN = condicion
if !(tN) goto L_end
  ... cuerpo ...
actualización
goto L_start
L_end:
// FIN FOR
```

**Do-while** genera:
```
//INICIO DO-WHILE
L_start:
  ... cuerpo ...
tN = condicion
if (tN) goto L_start   ← nota: condición positiva, no negada
//FIN DO-WHILE
```

**Switch** genera:
```
// SWITCH_START nombre_variable
// CASE valor1
  ... instrucciones ...
// BREAK
// CASE valor2
  ...
// BREAK
// DEFAULT
  ...
// SWITCH_END
```

#### Funciones — `handle_method_declaration`

```
1. Emitir "function tipo_retorno nombre(params):"
2. enter_scope() — crear scope local
3. Registrar parámetros en la tabla de símbolos
4. Ejecutar el cuerpo (lista de lambdas)
5. exit_scope()
6. Emitir "end"
```

#### Llamada a función — `handle_method_call`

```
1. Verificar que la función exista en self.methods
2. Verificar que el número de argumentos coincida
3. Para cada argumento:
   a. Resolver su IR con _resolve_ir()
   b. Verificar tipo contra el parámetro esperado
   c. Emitir "param nombre_arg"
4. Emitir "tN = call nombre(args)"
5. Retornar tN (el temporal con el resultado)
```

---

## 7. Fase 4 — Generación de Código Intermedio

### 7.1 Qué es el IR (Intermediate Representation)

El compilador genera **código de tres direcciones** (3-address code). Cada instrucción tiene la forma:
```
resultado = operando1 operador operando2
```

Los **temporales** (`t0`, `t1`, `t2`, ...) son variables intermedias que no existen en el código fuente.

### 7.2 `interCodeGenerator` — Clase generadora

```python
class interCodeGenerator:
    def new_temp(self):    # genera t0, t1, t2...
    def new_label(self):   # genera L0, L1, L2...
    def emit(self, instr): # agrega instrucción a self.code
    def get_code(self):    # retorna la lista de instrucciones
```

### 7.3 Ejemplo de IR generado

Para el código:
```
entei x as 5 pyc
entei y as x su 3 pyc
pikachu ps y pc pyc
```

Se genera:
```
x = 5
t0 = x + 3
y = t0
cout << y << endl
```

Para un while:
```
wailord ps x me 10 pc ls
    x as x su 1 pyc
lc
```

Genera:
```
// INICIO WHILE
L0:
t0 = x < 10
if !(t0) goto L1
x = x + 1
goto L0
L1:
// FIN WHILE
```

---

## 8. Fase 5 — Optimización (`optimize.py`)

La clase `Optimize` aplica **7 pasadas de optimización** sobre el IR:

### 8.1 `remove_redundant_temporaries` — Colapsar temporales redundantes

Elimina el patrón:
```
t0 = a + b
x  = t0
```
Convirtiéndolo en:
```
x = a + b
```
**Excepción**: nunca colapsa si la línea contiene `call` (llamadas a función tienen efectos secundarios).

### 8.2 `simplify_trivial_operations` — Eliminar operaciones triviales

```
x = a + 0  →  x = a
x = a - 0  →  x = a
x = a * 1  →  x = a
x = a / 1  →  x = a
```

### 8.3 `optimize_conditionals` — Simplificar condiciones

Transforma el patrón de 3 líneas:
```
if cond goto L_true
goto L_false
```
En una sola:
```
if !(cond) goto L_false
```

### 8.4 `remove_unreachable_labels` — Eliminar etiquetas inalcanzables

Elimina etiquetas que vienen inmediatamente después de un `goto` (nunca se alcanza el salto siguiente).

### 8.5 `optimize_goto_chains` — Eliminar cadenas de gotos

Si `goto L1` y `L1:` tiene `goto L2`, reemplaza por `goto L2` directamente.

### 8.6 `remove_unused_temporaries` — Eliminar temporales sin uso

Si `t0` se calcula pero nunca se usa en ninguna otra instrucción, se elimina.
**Excepción**: nunca elimina líneas con `call`.

### 8.7 `optimize_redundant_for_conditions` — Optimizar condiciones de for

Detecta y elimina la evaluación doble de la condición del `for` que puede ocurrir en el IR generado.

---

## 9. Fase 6 — Generación de Código C++ (`codeGen.py`)

### 9.1 ¿Qué hace?

Toma el IR optimizado y lo traduce a **código C++ válido** y compilable.

### 9.2 Separación funciones / main

```python
def generate(self):
    func_ir = []   # instrucciones de funciones
    main_ir = []   # instrucciones del programa principal
    
    for line in self.ir:
        if line.startswith('function ') and line.endswith(':'):
            in_func = True
        elif line == 'end' and in_func:
            in_func = False
        if in_func: func_ir.append(line)
        else: main_ir.append(line)
```

Las funciones se generan **antes** del `main()`.

### 9.3 Estructura del C++ generado

```cpp
#include <iostream>
#include <string>
using namespace std;

// Funciones declaradas primero
int cuadrado(int n) {
    return n * n;
}

int main() {
    // Declaraciones de variables de la tabla de símbolos
    int contador;
    
    // Traducción del IR principal
    contador = 0;
    while (contador < 5) {
        int valor = cuadrado(contador);
        switch (valor) {
            case 0:
                cout << valor << endl;
                break;
            // ...
        }
        contador = contador + 1;
    }
    return 0;
}
```

### 9.4 Mapeo de tipos

```python
TIPOS = {
    'entei':     'int',
    'floatzel':  'float',
    'charizar':  'char',
    'boofalant': 'bool',
    'stantler':  'string',
    'gardevoir': 'void',
}
```

### 9.5 Mapeo de operadores

```python
OPS = {
    'su': '+',  're': '-',  'mu': '*',  'di': '/',
    'ig': '==', 'ni': '!=', 'me': '<',  'ma': '>',
    'mei': '<=', 'mai': '>='
}
```

### 9.6 Reconstrucción de estructuras de control

El generador C++ usa los **comentarios estructurales** del IR (`// INICIO IF`, `// FIN WHILE`, etc.) como marcadores para reconstruir las llaves de C++. Mantiene una **pila de bloques abiertos** (`open_blocks`) para saber cuándo cerrar cada `}`.

- `// INICIO IF` → prepara el siguiente `if !(cond)` para abrir un bloque
- `// FIN IF` → cierra con `}`
- `// ELSE` → `} else {`
- `//INICIO DO-WHILE` → abre `do {`
- `// CASE valor` → `case valor:`
- `// BREAK` → `break;`

### 9.7 Manejo de funciones en C++

Para cada función en el IR:
```
function entei cuadrado(entei n):   →   int cuadrado(int n) {
    raikou n mu n                   →       return n * n;
end                                 →   }
```

Los `raikou` se traducen a `return`, los `param` se ignoran (son solo documentativos en el IR), y los `goto` no se emiten (la estructura la manejan los comentarios).

---

## 10. Manejo de Errores

### 10.1 Clase `Errors` (`errores.py`)

Centraliza todos los errores del compilador. Cada error se almacena como un diccionario:
```python
{
    'tipo': 'Léxico' | 'Sintáctico' | 'Semántico' | 'Advertencia',
    'descripcion': '...',
    'fila': '5',
    'col': '12'
}
```

La clase extrae automáticamente fila y columna del mensaje de error con regex:
```python
re.search(r'fila (\d+)[,\s]+(y\s+)?col(?:umna)?\s*(\d+)', error)
```

### 10.2 Tres instancias de `Errors`

El compilador usa **dos instancias separadas**:
- `lex_errors` → errores del análisis léxico
- `parse_errors` → errores del análisis sintáctico y semántico

Esto permite mostrarlos en secciones separadas del reporte HTML.

### 10.3 Condición de errores

```python
hay_errores = bool(lex_errors.errors or parse_errors.errors)
```

Si `hay_errores = True`:
- NO se genera código intermedio optimizado
- NO se genera C++
- NO se muestra la tabla de símbolos
- El reporte HTML muestra las secciones de código deshabilitadas

### 10.4 Tipos de errores detectados

| Fase     | Tipo de error               | Ejemplo                                     |
|----------|-----------------------------|---------------------------------------------|
| Léxico   | Carácter no reconocido      | `@` → "carácter no reconocido '@'"         |
| Léxico   | String no cerrado           | `cdHola` → "cadena no cerrada, ¿falta 'cd'?" |
| Léxico   | Sugerencia ortográfica      | `wailrd` → "¿Quisiste escribir 'wailord'?"  |
| Sintáctico | Token inesperado           | `pikachu y pyc` → muestra sintaxis correcta |
| Sintáctico | Final inesperado           | "¿Falta cerrar una llave 'lc'?"            |
| Semántico | Variable no declarada      | `x as 5 pyc` sin declarar x               |
| Semántico | Redeclaración              | Declarar misma variable dos veces          |
| Semántico | Tipo incompatible          | Asignar string a entei                     |
| Semántico | Función no definida        | Llamar función que no existe               |
| Semántico | Argumentos incorrectos     | Pasar 2 args a función que espera 1       |
| Semántico | División por cero          | `x di 0`                                   |
| Semántico | Expresión sin efecto       | `x su y pyc` sin asignar el resultado     |

---

## 11. Reporte HTML

El reporte HTML (`main.py`) combina todos los resultados en un documento visual con:

1. **Tabla de Tokens**: todos los tokens encontrados con tipo, valor, fila y columna.
2. **Errores Léxicos**: tabla con tipo, descripción, fila y columna.
3. **Errores Sintácticos**: igual que los léxicos.
4. **Código Intermedio**: el IR generado, con números de línea, en fondo oscuro tipo editor.
5. **Código C++ Generado**: igual que el IR pero en C++.
6. **Tabla de Símbolos**: nombre, tipo, ámbito (global/local/local cerrado) y valor final.

Si hay errores, las secciones de código y tabla de símbolos muestran un mensaje en rojo en lugar del contenido.

Los reportes se guardan en `reportes/reporte_NombreArchivo.html`.

---

## 12. Flujo Completo de Ejecución

```python
# main.py — función analizar()

# 1. Leer el archivo
contenido = open(ruta).read()

# 2. Análisis léxico
lex_errors = Errors(contenido)
lexer = Lexer(lex_errors)
tokens = lexer.tokenize(contenido)  # retorna lista de (tipo, valor, fila, col)

# 3. Inicializar módulos semánticos y de IR
sym_table = SymbolTable()
codegen = interCodeGenerator()
parse_errors = Errors(contenido)
semantic = Semantic(sym_table, parse_errors, lexer, codegen)

# 4. Análisis sintáctico + semántico
parser = Parser(lexer, parse_errors, semantic)
parsed = parser.parse(contenido, execute=True)
# execute=True → ejecuta las lambdas del AST inmediatamente
# Durante la ejecución se generan IR y se llena la tabla de símbolos

# 5. Verificar errores
hay_errores = bool(lex_errors.errors or parse_errors.errors)

if not hay_errores:
    # 6. Optimizar IR
    semantic.optimize_intermediate_code()
    intercode = codegen.get_code()
    
    # 7. Generar C++
    sym_flat = sym_table.to_flat_dict()
    gen = ccodeGen(intercode, sym_flat)
    gen.generate()
    cpp_code = gen.get_cpp_code()
    
    # 8. Guardar archivo .cpp
    open(f"{nombre_base}.cpp", "w").write(cpp_code)
    
    # 9. Tabla de símbolos HTML
    sym_html = sym_table.toHtml()

# 10. Generar reporte HTML
html = generar_html(tokens, lex_errors, parse_errors, intercode, cpp_code, sym_html, ...)
open(f"reportes/reporte_{nombre_base}.html", "w").write(html)
```

---

## 13. Ejemplo Completo Anotado

### Código fuente (lenguaje Pokémon)

```
entei contador as 0 pyc

suicune entei cuadrado ps entei n pc ls
    raikou n mu n pyc
lc

wailord ps contador me 5 pc ls
    entei valor as cuadrado ps contador pc pyc
    contador as contador su 1 pyc
lc
```

### Tokens generados (selección)

| # | Tipo      | Valor      | Fila | Col |
|---|-----------|------------|------|-----|
| 1 | ENTEI     | entei      | 1    | 1   |
| 2 | IDENTIFIER| contador   | 1    | 7   |
| 3 | EQUALS    | as         | 1    | 16  |
| 4 | NUMBER    | 0          | 1    | 19  |
| 5 | SEMICOLON | pyc        | 1    | 21  |
| 6 | SUICUNE   | suicune    | 3    | 1   |
| 7 | ENTEI     | entei      | 3    | 9   |
| 8 | IDENTIFIER| cuadrado   | 3    | 15  |
...

### Código Intermedio generado (antes de optimizar)

```
contador = 0
function entei  cuadrado(entei n):
t0 = n * n
raikou t0
end
// INICIO WHILE
L0:
t1 = contador < 5
if !(t1) goto L1
param contador
t2 = call cuadrado(contador)
valor = t2
t3 = contador + 1
contador = t3
goto L0
L1:
// FIN WHILE
```

### Código Intermedio optimizado (después)

```
contador = 0
function entei  cuadrado(entei n):
raikou n * n
end
// INICIO WHILE
L0:
t1 = contador < 5
if !(t1) goto L1
param contador
t2 = call cuadrado(contador)
valor = t2
contador = contador + 1
goto L0
L1:
// FIN WHILE
```

Optimizaciones aplicadas:
- `t0 = n * n; raikou t0` → colapsa a `raikou n * n` (redundant temporaries)
- `t3 = contador + 1; contador = t3` → colapsa a `contador = contador + 1`

### Código C++ generado

```cpp
#include <iostream>
#include <string>
using namespace std;

int cuadrado(int n) {
    return n * n;
}

int main() {
    int contador;
    
    contador = 0;
    while (contador < 5) {
        int valor = cuadrado(contador);
        contador = contador + 1;
    }
    return 0;
}
```

### Tabla de Símbolos (HTML)

| Nombre   | Tipo   | Ámbito | Valor |
|----------|--------|--------|-------|
| contador | entei  | global | 0     |
| n        | entei  | local (cerrado) | ? |
| valor    | entei  | local (cerrado) | ? |

> `?` = valor dinámico (depende del loop, no calculable en tiempo de compilación)

---

## Resumen de Conceptos Clave para la Presentación

| Concepto | Implementación en el proyecto |
|----------|-------------------------------|
| **Lexer** | PLY Lex con reglas `t_*`, palabras reservadas en dict `reserved` |
| **Parser** | PLY Yacc LALR(1), gramática en métodos `p_*` |
| **AST** | Implícito como funciones lambda/closures |
| **Scoping** | Pila de diccionarios con `enter_scope()`/`exit_scope()` |
| **Tipos** | Verificación en `_check_type_compatibility()` y `_check_declaration_type()` |
| **IR** | Código de 3 direcciones con temporales `tN` y etiquetas `LN` |
| **Optimización** | 7 pasadas sobre lista de strings del IR |
| **Generación** | Traducción directa IR → C++ con mapeo de palabras clave |
| **Errores** | Sugerencias por Levenshtein (léxico), mensajes contextuales por token (sintáctico) |
| **Reporte** | HTML generado programáticamente con toda la información del análisis |
