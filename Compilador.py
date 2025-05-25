from ply import lex
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import re

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
    'ERROR_LEXICO'     # Para símbolos no permitidos
] + list(reserved.values()) + list(set(tipos_dato.values()))

errores_lexicos = []

# Expresiones regulares para símbolos simplesq
t_IGUAL = r'='
t_PAREN_IZQ = r'\('
t_PAREN_DER = r'\)'
t_SUMA = r'\+'
t_RESTA = r'-'
t_MULTIPLICACION = r'\*'
t_DIVISION = r'/'
t_ignore = ' \t'  # Espacios y tabs se ignoran


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
    r'[\+/][a-zA-Z_][a-zA-Z0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*[\+/]'
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

def t_error(t):
    remaining = t.lexer.lexdata[t.lexer.lexpos:]
    end = 0
    while end < len(remaining) and not remaining[end].isspace() and remaining[end] not in '()=+-*/"':
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

def t_TEXTO(t):
    r'\".*?\"'
    t.value = t.value[1:-1]
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
# Funciones para generación de archivos
# ----------------------------

def generar_archivo_tok(tokens_analizados):
    with open('progfte.tok', 'w', encoding='utf-8') as f:
        # Escribir tokens válidos
        for token in tokens_analizados:
            if token['type'] not in ['COMENTARIO']:
                line = f"Renglón: {token['line']:<7} Lexema: {token['value']:<15} Token: {token['type']}\n"
                f.write(line)

def generar_archivo_tab(tokens_analizados):
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
        'TEXTO': 500
    }
    
    with open('progfte.tab', 'w', encoding='utf-8') as f:
        f.write("{:<8} {:<20} {:<50} {:<15}\n".format(
            "No", "Lexema", "Token", "Referencia"))
        f.write("-"*93 + "\n")
        
        # Procesar tokens válidos hasta Fin
        simbolos = []
        fin_encontrado = False
        for token in tokens_analizados:
            if token['type'] == 'PALABRA_RESERVADA_FIN':
                simbolos.append(token)
                fin_encontrado = True
                break
                
            # Excluye TODOS los errores y comentarios
            if not token['type'].startswith('ERROR_') and token['type'] not in ['COMENTARIO']:
                simbolos.append(token)
        
        # Escribir todos los símbolos en orden
        for i, simbolo in enumerate(simbolos, 1):
            f.write("{:<8} {:<20} {:<50} {:<15}\n".format(
                i,
                simbolo['value'],
                simbolo['type'],
                token_codes.get(simbolo['type'], 999)))

def generar_depuracion(tokens_analizados):
    depurado = []
    i = 0
    n = len(tokens_analizados)
    fin_encontrado = False

    while i < n and not fin_encontrado:
        token = tokens_analizados[i]

        # Detecta FIN
        if token['type'] == 'PALABRA_RESERVADA_FIN':
            fin_encontrado = True
            depurado.append('Fin')
            break

        # Ignora comentarios
        if token['type'] == 'COMENTARIO':
            i += 1
            continue

        # Comas sin espacio
        if token['type'] == 'COMA':
            depurado.append(',')
        # Detecta asignaciones tipo "a := 5"
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
            # Añade cualquier otro token tal cual, sin espacios
            depurado.append(str(token['value']))

        i += 1

    # Junta todo sin espacios
    return ''.join(depurado)

def analizar_archivo(file_path):
    global errores_lexicos
    errores_lexicos = []  # Reiniciar lista de errores
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            contenido = f.readlines()
            
        lexer.input(''.join(contenido))
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
        
        # Generar archivos
        generar_archivo_tok(tokens_analizados)
        generar_archivo_tab(tokens_analizados)
        
        depuracion = generar_depuracion(tokens_analizados)
        with open('progfte.dep', 'w', encoding='utf-8') as f:
            f.write(depuracion)
        
        return True, "Análisis completado con éxito"
    
    except Exception as e:
        return False, f"Error durante el análisis: {str(e)}"

# ----------------------------
# Interfaz Gráfica
# ----------------------------

def main():
    root = tk.Tk()
    root.title("Analizador Léxico")
    root.geometry("650x350")
    root.configure(bg="#f0f0f0")

    # Configuración de estilo
    estilo = {
        "font": ("Arial", 12),
        "bg": "#f0f0f0",
        "padx": 10,
        "pady": 5
    }

    # Marco principal
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(expand=True, fill=tk.BOTH, padx=25, pady=25)

    # Título
    tk.Label(main_frame, text="Analizador Léxico", 
            font=("Arial", 18, "bold"), bg="#f0f0f0", fg="#333").pack(pady=(0, 20))

    # Contenedor
    content_frame = tk.Frame(main_frame, bg="#f0f0f0")
    content_frame.pack(fill=tk.BOTH, expand=True)

    # Panel izquierdo (imagen)
    left_panel = tk.Frame(content_frame, bg="#f0f0f0")
    left_panel.pack(side=tk.LEFT, fill=tk.Y)

    try:
        img = Image.new('RGB', (150, 150), color='white')  # Imagen dummy
        img_tk = ImageTk.PhotoImage(img)
        img_label = tk.Label(left_panel, image=img_tk, bg="#f0f0f0")
        img_label.image = img_tk
        img_label.pack(padx=10)
    except:
        pass

    # Panel derecho
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

    # Estado
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
            status_label.config(text=f"✓ {message}\nArchivo: {file_path}", fg="green")
        else:
            status_label.config(text=f"✗ {message}", fg="red")

    root.mainloop()

if __name__ == "__main__":
    main()