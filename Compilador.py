from ply import lex, yacc
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import re

# ----------------------------
# Configuración de rutas
# ----------------------------
RUTA_SALIDA_ALTERNATIVA = r"D:\VisualStudioCode\Compilador"

# ----------------------------
# Analizador Léxico 
# ----------------------------

# Palabras reservadas del lenguaje 
reserved = {
    'Inicio': 'PALABRA_RESERVADA_INICIO',
    'Fin': 'PALABRA_RESERVADA_FIN',
    'ImprimirNumero': 'PALABRA_RESERVADA_IMPRIMIR_NUMERO',
    'ImprimirCadena': 'PALABRA_RESERVADA_IMPRIMIR_CADENA',
    'ImprimirBoleano': 'PALABRA_RESERVADA_IMPRIMIR_BOLEANO',
    'LeerNumero': 'PALABRA_RESERVADA_LEER_NUMERO',
    'LeerCadena': 'PALABRA_RESERVADA_LEER_CADENA',
    'LeerBoleano': 'PALABRA_RESERVADA_LEER_BOLEANO',
    'Si': 'PALABRA_RESERVADA_SI',
    'Entonces': 'PALABRA_RESERVADA_ENTONCES',
    'Sino': 'PALABRA_RESERVADA_SINO',
    'Mientras': 'PALABRA_RESERVADA_MIENTRAS',
    'Hacer': 'PALABRA_RESERVADA_HACER',
    'Verdadero': 'PALABRA_RESERVADA_VERDADERO',
    'Falso': 'PALABRA_RESERVADA_FALSO'
}

# Tipos de datos
tipos_dato = {
    'Cadena': 'TIPO_DATO',
    'Entero': 'TIPO_DATO',
    'Boleano': 'TIPO_DATO'
}

# Lista de tokens
tokens = [
    'ERROR_IDENTIFICADOR',
    'ERROR_IDENTIFICADOR_NUM',
    'PROGRAMA',         
    'IDENTIFICADOR',    # Nombres de variables/funciones
    'CONSTANTE',        # Números enteros
    'TEXTO',            # Cadenas entre comillas
    'TEXTO_MAL_FORMADO', # Texto con comillas no cerradas
    'CARACTER',         # Caracteres entre comillas simples
    'PAREN_IZQ',        # (
    'PAREN_DER',        # )
    'SUMA',             # +
    'RESTA',            # -
    'MULTIPLICACION',   # *
    'DIVISION',         # /
    'IGUAL',            # =
    'COMA',             # ,
    'PuntoYComa',       # ;
    'DosPuntos',        # :
    'COMILLA_IZQ',      # “ o "
    'COMILLA_DER',      # ” o "
    'ERROR_LEXICO'     # Para símbolos no permitidos
] + list(reserved.values()) + list(set(tipos_dato.values()))

errores_lexicos = []

# Expresiones regulares para símbolos simples
t_IGUAL = r'='
t_PAREN_IZQ = r'\('
t_PAREN_DER = r'\)'
t_SUMA = r'\+'
t_RESTA = r'-'
t_MULTIPLICACION = r'\*'
t_DIVISION = r'/'
t_ignore = ' \t'  # Espacios y tabs se ignoran

def t_COMILLA_IZQ(t):
    r'[“"]'
    return t

def t_COMILLA_DER(t):
    r'[”"]'
    return t

def t_DosPuntos(t):
    r':'
    return t

def t_PuntoYComa(t):
    r';'
    return t

def t_COMA(t):
    r','
    return t

def t_PROGRAMA(t):
    r'Script'
    t.type = 'PROGRAMA'
    return t

def t_ERROR_IDENTIFICADOR_OPERADOR(t):
    r'[\+/][a-zA-Z_][a-zA-Z0-9_]|[a-zA-Z_][a-zA-Z0-9_][\+/]'
    errores_lexicos.append({
        'line': t.lineno,
        'value': t.value,
        'type': 'ERROR_IDENTIFICADOR'
    })
    t.type = 'ERROR_IDENTIFICADOR'
    return t

def t_ERROR_IDENTIFICADOR_NUM(t):
    r'\d+[a-zA-Z_]+[a-zA-Z0-9_]*'
    errores_lexicos.append({
        'line': t.lineno,
        'value': t.value,
        'type': 'ERROR_IDENTIFICADOR'
    })
    return t

def t_IDENTIFICADOR(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*(\b|$)'
    if any(ord(c) > 127 or not c.isalnum() and c != '_' for c in t.value):
        t.type = 'ERROR_IDENTIFICADOR'
        errores_lexicos.append({
            'line': t.lineno,
            'value': t.value,
            'type': t.type
        })
    elif t.value in reserved:
        t.type = reserved[t.value]
    elif t.value in tipos_dato:
        t.type = tipos_dato[t.value]
    else:
        t.type = 'IDENTIFICADOR'
    return t

def t_TEXTO(t):
    r'[“"][^“”"]*[”"]'
    t.value = t.value[1:-1]  # Elimina las comillas
    return t

def t_error(t):
    remaining = t.lexer.lexdata[t.lexer.lexpos:]
    end = 0
    
    # Verificar si es una comilla no cerrada
    if t.value in ['"', '“']:
        while end < len(remaining) and remaining[end] not in ['"', '”', '\n']:
            end += 1
        
        if end >= len(remaining) or remaining[end] in ['\n']:
            t.type = 'TEXTO_MAL_FORMADO'
            t.value = t.value + remaining[:end]
            t.lexer.lexpos += end
            errores_lexicos.append({
                'line': t.lineno,
                'value': t.value,
                'type': t.type
            })
            return t
    
    # Manejo de otros errores léxicos
    while end < len(remaining) and not remaining[end].isspace() and remaining[end] not in '()=+-*/"“”':
        end += 1
    
    invalid = remaining[:end]
    t.lexer.lexpos += end
    
    errores_lexicos.append({
        'line': t.lineno,
        'value': invalid,
        'type': 'ERROR_LEXICO'
    })
    
    t.type = 'ERROR_LEXICO'
    t.value = invalid
    return t

def t_CONSTANTE(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_COMENTARIO(t):
    r'--.*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Construir el lexer
lexer = lex.lex()

# ----------------------------
# Analizador Sintáctico
# ----------------------------

# Nodos del árbol sintáctico
class Nodo:
    def __init__(self, tipo, hijos=None, valor=None):
        self.tipo = tipo
        self.hijos = hijos if hijos is not None else []
        self.valor = valor

    def __repr__(self):
        return f"{self.tipo}({self.valor})" if self.valor else self.tipo

# Reglas de precedencia
precedence = (
    ('left', 'SUMA', 'RESTA'),
    ('left', 'MULTIPLICACION', 'DIVISION'),
)

# Gramática
def p_programa(p):
    '''programa : PROGRAMA DosPuntos bloque
               | expresion PuntoYComa
               | asignacion'''
    if len(p) == 4:  # Caso: Script: Inicio...Fin
        p[0] = Nodo('PROGRAMA', [p[3]])
    else:  # Caso: expresión suelta o asignación
        p[0] = p[1]

def p_bloque(p):
    '''bloque : PALABRA_RESERVADA_INICIO instrucciones PALABRA_RESERVADA_FIN
              | instrucciones'''
    if len(p) == 4:
        p[0] = Nodo('BLOQUE', [p[2]])
    else:
        p[0] = Nodo('BLOQUE', [p[1]])

def p_instrucciones(p):
    '''instrucciones : instruccion
                    | instrucciones instruccion'''
    if len(p) == 2:
        p[0] = Nodo('INSTRUCCIONES', [p[1]])
    else:
        p[0] = Nodo('INSTRUCCIONES', [p[1], p[2]])

def p_instruccion(p):
    '''instruccion : asignacion
                  | expresion PuntoYComa'''
    p[0] = p[1]

def p_asignacion(p):
    '''asignacion : IDENTIFICADOR IGUAL expresion PuntoYComa
                 | IDENTIFICADOR IGUAL expresion'''  # Sin punto y coma
    p[0] = Nodo('ASIGNACION', [Nodo('ID', valor=p[1]), p[3]])

def p_expresion_binaria(p):
    '''expresion : expresion SUMA expresion
                | expresion RESTA expresion
                | expresion MULTIPLICACION expresion
                | expresion DIVISION expresion'''
    p[0] = Nodo(p[2], [p[1], p[3]])

def p_expresion_parentesis(p):
    'expresion : PAREN_IZQ expresion PAREN_DER'
    p[0] = p[2]

def p_expresion_identificador(p):
    'expresion : IDENTIFICADOR'
    p[0] = Nodo('ID', valor=p[1])

def p_expresion_numero(p):
    'expresion : CONSTANTE'
    p[0] = Nodo('NUMERO', valor=p[1])

def p_error(p):
    if p:
        raise SyntaxError(f"Error de sintaxis en token '{p.value}' (línea {p.lineno})")
    else:
        raise SyntaxError("Error de sintaxis: entrada incompleta")

# Construir el parser
parser = yacc.yacc()

# ----------------------------
# Funciones para generación de archivos
# ----------------------------

def generar_archivo_tok(tokens_analizados, output_dir):
    ruta_completa = os.path.join(output_dir, 'progfte.tok')
    with open(ruta_completa, 'w', encoding='utf-8') as f:
        for token in tokens_analizados:
            if token['type'] not in ['COMENTARIO']:
                if token['type'] == 'TEXTO_MAL_FORMADO':
                    line = f"Renglón: {token['line']:<7} Lexema: {token['value']:<15} Token: {token['type']} (Falta comilla de cierre)\n"
                else:
                    line = f"Renglón: {token['line']:<7} Lexema: {token['value']:<15} Token: {token['type']}\n"
                f.write(line)

def generar_archivo_tab(tokens_analizados, output_dir):
    token_codes = {
        'PROGRAMA': 100,
        'TIPO_DATO': 200,
        'IDENTIFICADOR': 300,
        'CONSTANTE': 400,
        'PALABRA_RESERVADA_INICIO': 1,
        'PALABRA_RESERVADA_FIN': 2,
        'PALABRA_RESERVADA_IMPRIMIR_NUMERO': 10,
        'PALABRA_RESERVADA_IMPRIMIR_CADENA': 11,
        'PALABRA_RESERVADA_IMPRIMIR_BOLEANO': 12,
        'PALABRA_RESERVADA_LEER_NUMERO': 13,
        'PALABRA_RESERVADA_LEER_CADENA': 14,
        'PALABRA_RESERVADA_LEER_BOLEANO': 15,
        'PAREN_IZQ': 50,
        'PAREN_DER': 51,
        'SUMA': 60,
        'RESTA': 61,
        'MULTIPLICACION': 62,
        'DIVISION': 63,
        'IGUAL': 70,
        'COMA': 80,
        'PuntoYComa': 81,
        'DosPuntos': 82,
        'TEXTO': 500,
        'COMILLA_IZQ': 83,
        'COMILLA_DER': 84
    }
    
    ruta_completa = os.path.join(output_dir, 'progfte.tab')
    with open(ruta_completa, 'w', encoding='utf-8') as f:
        f.write("{:<8} {:<20} {:<50} {:<15}\n".format(
            "No", "Lexema", "Token", "Referencia"))
        f.write("-"*93 + "\n")
        
        simbolos = []
        fin_encontrado = False
        for token in tokens_analizados:
            if token['type'] == 'PALABRA_RESERVADA_FIN':
                simbolos.append(token)
                fin_encontrado = True
                break
                
            if not token['type'].startswith('ERROR_') and token['type'] not in ['COMENTARIO', 'TEXTO_MAL_FORMADO']:
                simbolos.append(token)
        
        for i, simbolo in enumerate(simbolos, 1):
            f.write("{:<8} {:<20} {:<50} {:<15}\n".format(
                i,
                simbolo['value'],
                simbolo['type'],
                token_codes.get(simbolo['type'], 999)))

def generar_depuracion(tokens_analizados, output_dir):
    depurado = []
    i = 0
    n = len(tokens_analizados)
    fin_encontrado = False

    while i < n and not fin_encontrado:
        token = tokens_analizados[i]

        if token['type'] == 'PALABRA_RESERVADA_FIN':
            fin_encontrado = True
            depurado.append('Fin')
            break

        if token['type'] == 'COMENTARIO':
            i += 1
            continue

        if token['type'] == 'COMA':
            depurado.append(',')
        elif (
            i + 2 < n and
            tokens_analizados[i]['type'] == 'IDENTIFICADOR' and
            tokens_analizados[i+1]['type'] in ['IGUAL', 'ASIGNACION'] and
            tokens_analizados[i+2]['type'] in ['NUMERO', 'IDENTIFICADOR', 'PARENTESIS_IZQ']
        ):
            depurado.append(
                f"{tokens_analizados[i]['value']}{tokens_analizados[i+1]['value']}{tokens_analizados[i+2]['value']}"
            )
            i += 3
            continue
        else:
            depurado.append(str(token['value']))

        i += 1

    with open(os.path.join(output_dir, 'progfte.dep'), 'w', encoding='utf-8') as f:
        f.write(''.join(depurado))

def generar_arbol_sintactico(arbol, output_dir):
    # Diccionario para mostrar los operadores exactos
    mostrar_operadores = {
        'SUMA': '+',
        'RESTA': '-',
        'MULTIPLICACION': '*',
        'DIVISION': '/',
        'ASIGNACION': '='
    }
    
    def _generar_texto(nodo, nivel=0):
        # Caso especial para asignaciones
        if nodo.tipo == 'ASIGNACION':
            texto = "  " * nivel + "ASIGNACION\n"
            texto += "  " * (nivel + 1) + f"ID({nodo.hijos[0].valor})\n"
            texto += "  " * (nivel + 1) + f"{mostrar_operadores.get(nodo.tipo, nodo.tipo)}\n"
            texto += _generar_texto(nodo.hijos[1], nivel + 1)
            return texto
        
        # Caso para operaciones binarias
        if nodo.tipo in ['SUMA', 'RESTA', 'MULTIPLICACION', 'DIVISION']:
            texto = "  " * nivel + f"{mostrar_operadores.get(nodo.tipo, nodo.tipo)}\n"
            for hijo in nodo.hijos:
                texto += _generar_texto(hijo, nivel + 1)
            return texto
        
        # Caso base para identificadores y números
        texto = "  " * nivel + f"{nodo.tipo}({nodo.valor})\n" if nodo.valor else "  " * nivel + f"{nodo.tipo}\n"
        for hijo in nodo.hijos:
            texto += _generar_texto(hijo, nivel + 1)
        return texto
    
    ruta_completa = os.path.join(output_dir, 'progfte.arb')
    with open(ruta_completa, 'w', encoding='utf-8') as f:
        f.write(_generar_texto(arbol))

def analizar_archivo(file_path):
    global errores_lexicos
    errores_lexicos = []
    
    try:
        # Determinar la ruta de salida
        try:
            output_dir = os.path.dirname(file_path)
            if not os.path.exists(output_dir) or not os.access(output_dir, os.W_OK):
                raise Exception("Sin permisos en directorio origen")
        except:
            output_dir = RUTA_SALIDA_ALTERNATIVA
            os.makedirs(output_dir, exist_ok=True)
            messagebox.showwarning(
                "Aviso", 
                f"No se pudo guardar en el directorio original. \nLos archivos se guardarán en: {output_dir}"
            )

        with open(file_path, 'r', encoding='utf-8') as f:
            contenido = f.read().strip()  # Elimina espacios en blanco al inicio/final

        # Preprocesamiento para aceptar expresiones sueltas
        if not contenido.startswith("Script"):
            # Si no empieza con Script, lo envolvemos en la estructura mínima
            contenido_wrapped = f"Script:\nInicio\n{contenido}\nFin"
            try:
                # Primero intentamos parsear como expresión suelta envuelta
                lexer.input(contenido_wrapped)
                arbol = parser.parse(contenido_wrapped, lexer=lexer, tracking=True)
            except SyntaxError:
                # Si falla, probamos parsear directamente
                lexer.input(contenido)
                arbol = parser.parse(contenido, lexer=lexer, tracking=True)
        else:
            # Contenido ya tiene estructura Script completa
            lexer.input(contenido)
            arbol = parser.parse(contenido, lexer=lexer, tracking=True)

        # Recolectar tokens para archivos .tok y .tab (usando el contenido original)
        lexer.input(contenido)
        tokens_analizados = []
        while True:
            tok = lexer.token()
            if not tok: 
                break
            tokens_analizados.append({
                'type': tok.type,
                'value': tok.value,
                'line': tok.lineno
            })

        # Generar todos los archivos de salida
        generar_archivo_tok(tokens_analizados, output_dir)
        generar_archivo_tab(tokens_analizados, output_dir)
        generar_depuracion(tokens_analizados, output_dir)
        generar_arbol_sintactico(arbol, output_dir)

        return True, f"Análisis completado. Archivos guardados en: {output_dir}"

    except SyntaxError as e:
        # Capturar errores sintácticos específicos con información de línea
        error_msg = f"Error de sintaxis: {str(e)}"
        if hasattr(e, 'lineno') and hasattr(e, 'text'):
            error_msg += f"\nLínea {e.lineno}: {e.text.strip() if e.text else ''}"
        return False, error_msg

    except Exception as e:
        # Capturar otros errores inesperados
        error_msg = f"Error inesperado: {str(e)}"
        # Agregar información de línea si está disponible
        if hasattr(e, 'lineno') and hasattr(e, 'text'):
            error_msg += f"\nLínea {e.lineno}: {e.text.strip() if e.text else ''}"
        return False, error_msg
# ----------------------------
# Interfaz Gráfica
# ----------------------------

def main():
    root = tk.Tk()
    root.title("Analizador Léxico y Sintáctico")
    root.geometry("650x350")
    root.configure(bg="#f0f0f0")

    estilo = {
        "font": ("Arial", 12),
        "bg": "#f0f0f0",
        "padx": 10,
        "pady": 5
    }

    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(expand=True, fill=tk.BOTH, padx=25, pady=25)

    tk.Label(main_frame, text="Analizador Léxico y Sintáctico", 
            font=("Arial", 18, "bold"), bg="#f0f0f0", fg="#333").pack(pady=(0, 20))

    content_frame = tk.Frame(main_frame, bg="#f0f0f0")
    content_frame.pack(fill=tk.BOTH, expand=True)

    left_panel = tk.Frame(content_frame, bg="#f0f0f0")
    left_panel.pack(side=tk.LEFT, fill=tk.Y)

    try:
        img = Image.new('RGB', (150, 150), color='white')
        img_tk = ImageTk.PhotoImage(img)
        img_label = tk.Label(left_panel, image=img_tk, bg="#f0f0f0")
        img_label.image = img_tk
        img_label.pack(padx=10)
    except:
        pass

    right_panel = tk.Frame(content_frame, bg="#f0f0f0")
    right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    tk.Label(right_panel, text="Seleccione archivo fuente (.txt):", **estilo).pack(anchor=tk.W)

    btn_frame = tk.Frame(right_panel, bg="#f0f0f0")
    btn_frame.pack(fill=tk.X, pady=10)

    btn = tk.Button(btn_frame, text="Analizar Archivo", 
                   command=lambda: procesar_archivo(),
                   font=("Arial", 12, "bold"), 
                   bg="#4CAF50", fg="white",
                   padx=20, pady=8)
    btn.pack()

    global status_label
    status_label = tk.Label(right_panel, text="", font=("Arial", 11), 
                          bg="#f0f0f0", fg="green", wraplength=400)
    status_label.pack(anchor=tk.W, pady=(20, 0))

    def procesar_archivo():
        file_path = filedialog.askopenfilename(filetypes=[("Archivos texto", "*.txt")])
        if not file_path:
            return

        success, message = analizar_archivo(file_path)
        
        if success:
            status_label.config(text=f"✓ {message}", fg="green")
        else:
            status_label.config(text=f"✗ {message}", fg="red")

    root.mainloop()

if __name__ == "__main__":
    main()