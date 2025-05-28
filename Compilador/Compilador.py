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
    'Inicio': 'INICIO',
    'Fin': 'FIN',
    'impcad': 'IMPCAD',
    'leerdig': 'LEERDIG',
    'int': 'INT',
    'Cad': 'CAD',
    'Bool': 'BOOL',
}

# Lista de tokens
tokens = [
    'IDENTIFICADOR',
    'CONSTANTE',
    'TEXTO',
    'PAREN_IZQ',
    'PAREN_DER',
    'SUMA',
    'RESTA',
    'MULTIPLICACION',
    'DIVISION',
    'IGUAL',
    'COMA',
    'PUNTOYCOMA',
    'DOSPUNTOS',
    'COMILLA_IZQ',
    'COMILLA_DER',
    'ASIGNACION',
] + list(reserved.values())

# Expresiones regulares para tokens
t_ignore = ' \t'
t_SUMA = r'\+'
t_RESTA = r'-'
t_MULTIPLICACION = r'\*'
t_DIVISION = r'/'
t_IGUAL = r'='
t_PAREN_IZQ = r'\('
t_PAREN_DER = r'\)'
t_COMA = r','
t_PUNTOYCOMA = r';'
t_DOSPUNTOS = r':'
t_ASIGNACION = r':='

def t_COMILLA_IZQ(t):
    r'[“"]'
    return t

def t_COMILLA_DER(t):
    r'[”"]'
    return t

# Añade esto al inicio de tu archivo (con las demás declaraciones globales)
errores_lexicos = []

def t_TEXTO(t):
    r'["“][^"”]*["”]'
    # Verificar balanceo de comillas
    if (t.value[0] == '"' and t.value[-1] != '"') or \
       (t.value[0] == '“' and t.value[-1] != '”'):
        t.type = 'TEXTO_MAL_FORMADO'
        errores_lexicos.append({
            'line': t.lineno,
            'value': t.value,
            'type': t.type,
            'msg': 'Comilla de cierre faltante'
        })
    else:
        t.value = t.value[1:-1]  # Eliminar comillas exteriores
    return t

def t_IDENTIFICADOR(t):
    r'[a-zA-Z_áéíóúÁÉÍÓÚñÑ][a-zA-Z0-9_áéíóúÁÉÍÓÚñÑ]*'
    t.type = reserved.get(t.value, 'IDENTIFICADOR')
    return t

def t_CONSTANTE(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}' en línea {t.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()

# ----------------------------
# Analizador Sintáctico
# ----------------------------

class Nodo:
    def __init__(self, tipo, hijos=None, valor=None):
        self.tipo = tipo
        self.hijos = hijos if hijos is not None else []
        self.valor = valor

    def __repr__(self):
        return f"{self.tipo}({self.valor})" if self.valor else self.tipo

precedence = (
    ('left', 'SUMA', 'RESTA'),
    ('left', 'MULTIPLICACION', 'DIVISION'),
)

def p_programa(p):
    '''programa : encabezado declaraciones bloque'''
    p[0] = Nodo('PROGRAMA', [p[1], p[2], p[3]])

def p_encabezado(p):
    '''encabezado : IDENTIFICADOR IDENTIFICADOR'''
    p[0] = Nodo('ENCABEZADO', [Nodo('NOMBRE_LENGUAJE', valor=p[1]), 
                              Nodo('EJEMPLO', valor=p[2])])

def p_declaraciones(p):
    '''declaraciones : declaracion
                    | declaraciones declaracion'''
    if len(p) == 2:
        p[0] = Nodo('DECLARACIONES', [p[1]])
    else:
        p[0] = Nodo('DECLARACIONES', [p[1], p[2]])

def p_declaracion(p):
    '''declaracion : tipo lista_ids PUNTOYCOMA
                  | tipo IDENTIFICADOR IGUAL expresion PUNTOYCOMA'''
    if len(p) == 4:
        p[0] = Nodo('DECLARACION', [p[1], p[2]])
    else:
        p[0] = Nodo('DECLARACION_CON_INICIALIZACION', [
            p[1],
            Nodo('ID', valor=p[2]),
            p[4]
        ])

def p_lista_ids(p):
    '''lista_ids : IDENTIFICADOR
                | lista_ids COMA IDENTIFICADOR'''
    if len(p) == 2:
        p[0] = Nodo('LISTA_IDS', [Nodo('ID', valor=p[1])])
    else:
        p[0] = p[1]
        p[0].hijos.append(Nodo('ID', valor=p[3]))

def p_tipo(p):
    '''tipo : INT
           | CAD
           | BOOL'''
    p[0] = Nodo('TIPO', valor=p[1])

def p_bloque(p):
    '''bloque : INICIO instrucciones FIN'''
    p[0] = Nodo('BLOQUE', [p[2]])

def p_instrucciones(p):
    '''instrucciones : instruccion
                    | instrucciones instruccion'''
    if len(p) == 2:
        p[0] = Nodo('INSTRUCCIONES', [p[1]])
    else:
        p[0] = Nodo('INSTRUCCIONES', [p[1], p[2]])

def p_instruccion(p):
    '''instruccion : declaracion
                  | asignacion
                  | impresion
                  | lectura
                  | expresion PUNTOYCOMA'''
    p[0] = p[1]

def p_impresion(p):
    '''impresion : IMPCAD PAREN_IZQ TEXTO PAREN_DER PUNTOYCOMA
                | IMPCAD PAREN_IZQ IDENTIFICADOR PAREN_DER PUNTOYCOMA'''
    if p[3].type == 'TEXTO':
        p[0] = Nodo('IMPRIMIR', [Nodo('TEXTO', valor=p[3])])
    else:
        p[0] = Nodo('IMPRIMIR', [Nodo('ID', valor=p[3])])

def p_lectura(p):
    '''lectura : LEERDIG PAREN_IZQ IDENTIFICADOR PAREN_DER PUNTOYCOMA'''
    p[0] = Nodo('LEER', [Nodo('ID', valor=p[3])])

def p_asignacion(p):
    '''asignacion : IDENTIFICADOR ASIGNACION expresion PUNTOYCOMA
                 | IDENTIFICADOR IGUAL expresion PUNTOYCOMA'''
    p[0] = Nodo('ASIGNACION', [
        Nodo('ID', valor=p[1]),
        p[3]
    ])

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
        error_msg = f"Error de sintaxis en línea {p.lineno}:\n"
        error_msg += f"Token inesperado: '{p.value}' (tipo: {p.type})\n"
        
        # Mostrar contexto
        if hasattr(p, 'lexer'):
            data = p.lexer.lexdata
            lines = data.split('\n')
            if 0 <= p.lineno-1 < len(lines):
                error_msg += f"Línea completa: {lines[p.lineno-1]}\n"
                error_msg += " " * (p.lexpos - lines[p.lineno-1][:p.lexpos].count('\n')) + "^\n"
        
        error_msg += "Se esperaba: texto entre comillas o identificador"
        raise SyntaxError(error_msg)
    else:
        raise SyntaxError("Error de sintaxis al final del archivo")

def p_impresion(p):
    '''impresion : IMPCAD PAREN_IZQ contenido_impresion PAREN_DER PUNTOYCOMA'''
    p[0] = Nodo('IMPRIMIR', [p[3]])

def p_contenido_impresion(p):
    '''contenido_impresion : TEXTO
                          | IDENTIFICADOR'''
    p[0] = Nodo('CONTENIDO', valor=p[1])


parser = yacc.yacc()

# ----------------------------
# Funciones para generación de archivos
# ----------------------------

def generar_archivo_tok(tokens_analizados, output_dir):
    ruta_completa = os.path.join(output_dir, 'progfte.tok')
    with open(ruta_completa, 'w', encoding='utf-8') as f:
        for token in tokens_analizados:
            line = f"Renglón: {token['line']:<7} Lexema: {token['value']:<15} Token: {token['type']}\n"
            f.write(line)

def generar_archivo_tab(tokens_analizados, output_dir):
    token_codes = {
        'IDENTIFICADOR': 300,
        'CONSTANTE': 400,
        'INICIO': 1,
        'FIN': 2,
        'IMPCAD': 11,
        'LEERDIG': 13,
        'PAREN_IZQ': 50,
        'PAREN_DER': 51,
        'SUMA': 60,
        'RESTA': 61,
        'MULTIPLICACION': 62,
        'DIVISION': 63,
        'IGUAL': 70,
        'COMA': 80,
        'PUNTOYCOMA': 81,
        'DOSPUNTOS': 82,
        'TEXTO': 500,
        'COMILLA_IZQ': 83,
        'COMILLA_DER': 84,
        'INT': 201,
        'CAD': 202,
        'BOOL': 203,
        'ASIGNACION': 90
    }
    
    ruta_completa = os.path.join(output_dir, 'progfte.tab')
    with open(ruta_completa, 'w', encoding='utf-8') as f:
        f.write("{:<8} {:<20} {:<50} {:<15}\n".format(
            "No", "Lexema", "Token", "Referencia"))
        f.write("-"*93 + "\n")
        for i, token in enumerate(tokens_analizados, 1):
            f.write("{:<8} {:<20} {:<50} {:<15}\n".format(
                i, token['value'], token['type'], token_codes.get(token['type'], 999)))

def generar_arbol_sintactico(arbol, output_dir):
    def _generar_texto(nodo, nivel=0):
        texto = "  "*nivel + f"{nodo.tipo}"
        if nodo.valor is not None:
            texto += f": {nodo.valor}"
        texto += "\n"
        for hijo in nodo.hijos:
            texto += _generar_texto(hijo, nivel+1)
        return texto

    with open(os.path.join(output_dir, 'progfte.arb'), 'w', encoding='utf-8') as f:
        f.write(_generar_texto(arbol))

def analizar_archivo(file_path):
    try:
        output_dir = RUTA_SALIDA_ALTERNATIVA
        os.makedirs(output_dir, exist_ok=True)

        with open(file_path, 'r', encoding='utf-8') as f:
            contenido = f.read()

        # Preprocesamiento para limpiar el archivo
        lineas = []
        for linea in contenido.split('\n'):
            # Eliminar comentarios
            if '--' in linea:
                linea = linea.split('--')[0]
            # Eliminar líneas con @ y #
            if not re.search(r'[@#]', linea):
                lineas.append(linea.strip())
        contenido = '\n'.join(lineas)

        # Asegurar estructura básica
        if 'Inicio' not in contenido:
            contenido = 'Inicio\n' + contenido
        if 'Fin' not in contenido:
            contenido += '\nFin'

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

        arbol = parser.parse(contenido, lexer=lexer)

        generar_archivo_tok(tokens_analizados, output_dir)
        generar_archivo_tab(tokens_analizados, output_dir)
        generar_arbol_sintactico(arbol, output_dir)

        return True, f"Análisis completado. Archivos guardados en: {output_dir}"

    except Exception as e:
        return False, f"Error: {str(e)}"

# ----------------------------
# Interfaz Gráfica
# ----------------------------

def main():
    root = tk.Tk()
    root.title("Analizador Léxico y Sintáctico")
    root.geometry("650x350")
    root.configure(bg="#f0f0f0")

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

    tk.Label(right_panel, text="Seleccione archivo fuente (.txt):", 
            font=("Arial", 12), bg="#f0f0f0").pack(anchor=tk.W)

    btn_frame = tk.Frame(right_panel, bg="#f0f0f0")
    btn_frame.pack(fill=tk.X, pady=10)

    btn = tk.Button(btn_frame, text="Analizar Archivo", 
                   command=lambda: procesar_archivo(),
                   font=("Arial", 12, "bold"), 
                   bg="#4CAF50", fg="white",
                   padx=20, pady=8)
    btn.pack()

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