"""
generar_capturas_reales.py
Genera las 15 capturas reales del Plan Definitivo para SMART CENDIS Etapa 3
en la carpeta 'capturas reales', simulando con máxima fidelidad el
Terminal Integrado de Visual Studio Code (Tema Dark+, PowerShell).
"""

import os
import sys
import io
import shutil
import json
from unittest.mock import patch
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(BASE_DIR, "capturas reales")
JSON_PATH = os.path.join(BASE_DIR, "smart_cendis.json")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, BASE_DIR)
import smartCendis_v3 as sc

# Tipografías del sistema
FONT_MONO = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 15)
FONT_MONO_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 15)
FONT_UI = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 12)
FONT_UI_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 12)

# Paleta de colores VS Code Dark+ Theme
BG_COLOR       = (30, 30, 30)       # #1e1e1e Fondo terminal
HEADER_BG      = (37, 37, 38)       # #252526 Pestañas superiores
BORDER_COLOR   = (45, 45, 45)       # #2d2d2d
TAB_TEXT_INACT = (150, 150, 150)    # #969696
TAB_TEXT_ACT   = (255, 255, 255)    # #ffffff
TAB_INDICATOR  = (0, 122, 204)      # #007acc Azul activo
PILL_BG        = (45, 45, 45)

TXT_DEFAULT    = (212, 212, 212)    # #d4d4d4
TXT_PROMPT     = (100, 200, 255)    # PS C:\...
TXT_INPUT      = (255, 255, 255)    # Entrada usuario
TXT_ERROR      = (244, 71, 71)      # #f44747 Rojo error
TXT_SUCCESS    = (137, 209, 133)    # #89d185 Verde éxito
TXT_BANNER     = (86, 156, 214)     # #569cd6 Azul banners
TXT_WARNING    = (229, 192, 123)    # Amarillo advertencia
TXT_MUTED      = (140, 140, 140)    # Gris tenue

def render_terminal(filename, lines_data):
    """Renderiza la lista de tuplas (tipo, texto) en una imagen PNG estilo VS Code."""
    pad_x = 24
    pad_y = 16
    line_h = 22
    header_h = 36

    max_len = max((len(txt) for _, txt in lines_data), default=60)
    width = max(880, pad_x * 2 + int(max_len * 9.2))
    height = header_h + pad_y + len(lines_data) * line_h + pad_y + 12

    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Header de pestañas VS Code
    draw.rectangle([(0, 0), (width, header_h)], fill=HEADER_BG)
    draw.line([(0, header_h - 1), (width, header_h - 1)], fill=BORDER_COLOR, width=1)

    tabs = [
        ("PROBLEMS", False),
        ("OUTPUT", False),
        ("DEBUG CONSOLE", False),
        ("TERMINAL", True)
    ]
    cur_x = 20
    for tab_name, active in tabs:
        t_font = FONT_UI_BOLD if active else FONT_UI
        t_col = TAB_TEXT_ACT if active else TAB_TEXT_INACT
        draw.text((cur_x, 10), tab_name, font=t_font, fill=t_col)
        bbox = draw.textbbox((cur_x, 10), tab_name, font=t_font)
        tab_w = bbox[2] - bbox[0]
        if active:
            draw.rectangle([(cur_x, header_h - 2), (cur_x + tab_w, header_h)], fill=TAB_INDICATOR)
        cur_x += tab_w + 24

    pill_w = 110
    pill_x = width - pill_w - 20
    draw.rounded_rectangle([(pill_x, 7), (pill_x + pill_w, 29)], radius=3, fill=PILL_BG)
    draw.text((pill_x + 12, 10), "1: powershell", font=FONT_UI, fill=TAB_TEXT_ACT)

    # Líneas
    y = header_h + pad_y
    for item in lines_data:
        t, txt = item
        if t == "ps":
            draw.text((pad_x, y), txt, font=FONT_MONO, fill=TXT_PROMPT)
        elif t == "error":
            draw.text((pad_x, y), txt, font=FONT_MONO, fill=TXT_ERROR)
        elif t == "success":
            draw.text((pad_x, y), txt, font=FONT_MONO, fill=TXT_SUCCESS)
        elif t == "banner":
            draw.text((pad_x, y), txt, font=FONT_MONO, fill=TXT_BANNER)
        elif t == "warning":
            draw.text((pad_x, y), txt, font=FONT_MONO, fill=TXT_WARNING)
        elif t == "muted":
            draw.text((pad_x, y), txt, font=FONT_MONO, fill=TXT_MUTED)
        elif t == "input":
            if ": " in txt:
                p_part, in_part = txt.split(": ", 1)
                p_text = p_part + ": "
                draw.text((pad_x, y), p_text, font=FONT_MONO, fill=TXT_DEFAULT)
                p_bbox = draw.textbbox((pad_x, y), p_text, font=FONT_MONO)
                draw.text((p_bbox[2], y), in_part, font=FONT_MONO_BOLD, fill=TXT_INPUT)
            else:
                draw.text((pad_x, y), txt, font=FONT_MONO, fill=TXT_DEFAULT)
        else:
            draw.text((pad_x, y), txt, font=FONT_MONO, fill=TXT_DEFAULT)
        y += line_h

    out_file = os.path.join(OUT_DIR, filename)
    img.save(out_file, "PNG", optimize=True)
    print(f"  [OK] {filename}")


def run_interactive(func, inputs, menu_opc=None, show_menu=True):
    """
    Ejecuta func interceptando stdout e input() simulando la consola interactiva.
    Retorna una lista de tuplas (tipo, texto).
    """
    raw_lines = []
    
    # Prompt inicial
    raw_lines.append(("ps", r"PS C:\Users\Asjer\OneDrive\Desktop\Laboratorio> python smartCendis_v3.py"))
    
    if show_menu:
        raw_lines.append(("banner", "=================================================="))
        raw_lines.append(("banner", "              SMART CENDIS"))
        raw_lines.append(("banner", "=================================================="))
        raw_lines.append(("text",   "Sistema de Gestión Digital de Solicitudes,"))
        raw_lines.append(("text",   "Abastecimiento y Control de Inventario"))
        raw_lines.append(("banner", "=================================================="))
        raw_lines.append(("text",   " 1. Registrar medicamento"))
        raw_lines.append(("text",   " 2. Consultar medicamentos"))
        raw_lines.append(("text",   " 3. Modificar medicamento"))
        raw_lines.append(("text",   " 4. Desactivar medicamento"))
        raw_lines.append(("text",   " 5. Consultar paciente"))
        raw_lines.append(("text",   " 6. Registrar solicitud"))
        raw_lines.append(("text",   " 7. Procesar solicitud"))
        raw_lines.append(("text",   " 8. Registrar recepción"))
        raw_lines.append(("text",   " 9. Consultar solicitudes"))
        raw_lines.append(("text",   "10. Consultar inventario"))
        raw_lines.append(("text",   "11. Limpiar historial de solicitudes"))
        raw_lines.append(("text",   " 0. Salir"))
        raw_lines.append(("banner", "=================================================="))
        if menu_opc is not None:
            raw_lines.append(("input", f"Seleccione una opción: {menu_opc}"))
            raw_lines.append(("text", ""))

    it = iter(inputs)

    def fake_input(prompt=""):
        try:
            val = next(it)
        except StopIteration:
            val = ""
        p_clean = prompt.replace("\n", "").strip()
        if p_clean:
            raw_lines.append(("input", f"{p_clean} {val}"))
        return val

    # Interceptar print/stdout
    class StdoutCatcher:
        def write(self, s):
            if not s:
                return
            for part in s.splitlines():
                part_s = part.rstrip()
                if not part_s:
                    raw_lines.append(("text", ""))
                    continue
                low = part_s.lower()
                if any(k in low for k in ("error:", "demasiados intentos", "rechazad")):
                    raw_lines.append(("error", part_s))
                elif any(k in low for k in ("correctamente", "encontrado", "paciente encontrado", "solicitud marcada como surtida", "stock nuevo")):
                    raw_lines.append(("success", part_s))
                elif any(k in low for k in ("aviso:", "advertencia")):
                    raw_lines.append(("warning", part_s))
                elif any(k in low for k in ("====", "----", "smart cendis")):
                    raw_lines.append(("banner", part_s))
                else:
                    raw_lines.append(("text", part_s))
        def flush(self):
            pass

    old_stdout = sys.stdout
    sys.stdout = StdoutCatcher()
    try:
        with patch("builtins.input", side_effect=fake_input):
            func()
    finally:
        sys.stdout = old_stdout

    raw_lines.append(("text", ""))
    raw_lines.append(("input", "Presione ENTER para continuar... "))
    return raw_lines


def reset_state():
    sc.medicamentos[:] = [
        {
            "clave": "5121",
            "nombre": "Paracetamol 1 g",
            "presentacion": "Solucion inyectable",
            "unidad_fisica": "Ampolleta",
            "stock_actual": 26,
            "stock_objetivo": 30,
            "activo": True
        }
    ]
    sc.pacientes[:] = [
        {
            "servicio": "Pediatria",
            "cama": "01",
            "nombre": "Paciente de prueba 001",
            "nss": "00000000001"
        },
        {
            "servicio": "Pediatria",
            "cama": "02",
            "nombre": "Paciente de prueba 002",
            "nss": "00000000002"
        },
        {
            "servicio": "Medicina Interna",
            "cama": "01",
            "nombre": "Paciente de prueba 003",
            "nss": "00000000003"
        },
        {
            "servicio": "Urgencias",
            "cama": "01",
            "nombre": "Paciente de prueba 004",
            "nss": "00000000004"
        }
    ]
    sc.solicitudes.clear()
    sc.contador_solicitudes = 1
    for p in [JSON_PATH, JSON_PATH + ".tmp"]:
        if os.path.exists(p):
            os.remove(p)


# ============================================================
# GENERACIÓN DE LAS CAPTURAS
# ============================================================

def generar_todas():
    print("Iniciando generación de capturas en 'capturas reales/'...")

    # ------------------------------------------------------------
    # A-01: Clave inválida (regex)
    # ------------------------------------------------------------
    reset_state()
    lines = run_interactive(sc.registrar_medicamento, ["123", "123", "123"], menu_opc="1")
    render_terminal("A-01_clave_invalida.png", lines)

    # ------------------------------------------------------------
    # A-02: Stock negativo
    # ------------------------------------------------------------
    reset_state()
    lines = run_interactive(sc.registrar_medicamento, [
        "5999", "Ceftriaxona 1 g", "Solucion inyectable", "Ampolleta",
        "-5", "-5", "-5"
    ], menu_opc="1")
    render_terminal("A-02_stock_negativo.png", lines)

    # ------------------------------------------------------------
    # A-03: Cama inválida
    # ------------------------------------------------------------
    reset_state()
    lines = run_interactive(sc.registrar_solicitud, [
        "Pediatria", "A1", "A1", "A1"
    ], menu_opc="6")
    render_terminal("A-03_cama_invalida.png", lines)

    # ------------------------------------------------------------
    # A-04: Turno inválido
    # ------------------------------------------------------------
    reset_state()
    lines = run_interactive(sc.registrar_solicitud, [
        "Pediatria", "01", "parace", "1", "5", "4", "5", "0"
    ], menu_opc="6")
    render_terminal("A-04_turno_invalido.png", lines)

    # ------------------------------------------------------------
    # A-05: Cantidad inválida
    # ------------------------------------------------------------
    reset_state()
    lines = run_interactive(sc.registrar_solicitud, [
        "Pediatria", "01", "parace", "1", "0", "0", "0"
    ], menu_opc="6")
    render_terminal("A-05_cantidad_invalida.png", lines)

    # ------------------------------------------------------------
    # B-01: Registro exitoso de medicamento
    # ------------------------------------------------------------
    reset_state()
    lines = run_interactive(sc.registrar_medicamento, [
        "5999", "Ceftriaxona 1 g", "Solucion inyectable", "Ampolleta", "20", "30"
    ], menu_opc="1")
    render_terminal("B-01_registro_exitoso.png", lines)

    # ------------------------------------------------------------
    # B-02: Clave duplicada
    # ------------------------------------------------------------
    # Mantener el medicamento 5999 registrado
    lines = run_interactive(sc.registrar_medicamento, ["5999"], menu_opc="1")
    render_terminal("B-02_clave_duplicada.png", lines)

    # ------------------------------------------------------------
    # B-03: Consulta de inventario
    # ------------------------------------------------------------
    lines = run_interactive(sc.consultar_inventario, [], menu_opc="10")
    render_terminal("B-03_inventario.png", lines)

    # ------------------------------------------------------------
    # B-04: Registrar solicitud (PENDIENTE)
    # ------------------------------------------------------------
    lines = run_interactive(sc.registrar_solicitud, [
        "Pediatria", "01", "parace", "1", "5", "3", "Enf Lopez", "1"
    ], menu_opc="6")
    render_terminal("B-04_solicitud_pendiente.png", lines)

    # ------------------------------------------------------------
    # B-05: Procesar solicitud: PENDIENTE -> SURTIDA
    # ------------------------------------------------------------
    lines = run_interactive(sc.procesar_solicitud, ["SOL-0001", "1"], menu_opc="7")
    render_terminal("B-05_solicitud_surtida.png", lines)

    # ------------------------------------------------------------
    # B-06: Recepción total + actualización de inventario
    # ------------------------------------------------------------
    lines = run_interactive(sc.registrar_recepcion, ["SOL-0001", "5"], menu_opc="8")
    render_terminal("B-06_recepcion_total.png", lines)

    # ------------------------------------------------------------
    # B-07: Recepción parcial (SOL-0002)
    # ------------------------------------------------------------
    # Crear segunda solicitud con cantidad 10, surtirla y recibir 6
    run_interactive(sc.registrar_solicitud, [
        "Pediatria", "01", "parace", "1", "10", "1", "Dr Martinez", "1"
    ], menu_opc="6", show_menu=False)
    run_interactive(sc.procesar_solicitud, ["SOL-0002", "1"], menu_opc="7", show_menu=False)
    lines = run_interactive(sc.registrar_recepcion, ["SOL-0002", "6"], menu_opc="8")
    render_terminal("B-07_recepcion_parcial.png", lines)

    # ------------------------------------------------------------
    # C-01: Persistencia entre sesiones
    # ------------------------------------------------------------
    # Guardar estado actual
    sc.guardar_datos()
    # Simular segunda sesión: cargar datos y consultar solicitudes
    lines_c01 = []
    lines_c01.append(("ps", r"PS C:\Users\Asjer\OneDrive\Desktop\Laboratorio> python smartCendis_v3.py"))
    lines_c01.append(("banner", "=================================================="))
    lines_c01.append(("banner", "              SMART CENDIS"))
    lines_c01.append(("banner", "=================================================="))
    lines_c01.append(("text",   "Sistema de Gestión Digital de Solicitudes,"))
    lines_c01.append(("text",   "Abastecimiento y Control de Inventario"))
    lines_c01.append(("banner", "=================================================="))
    lines_c01.append(("text",   " 1. Registrar medicamento"))
    lines_c01.append(("text",   " ..."))
    lines_c01.append(("text",   " 9. Consultar solicitudes"))
    lines_c01.append(("text",   " 0. Salir"))
    lines_c01.append(("banner", "=================================================="))
    lines_c01.append(("input",  "Seleccione una opción: 9"))
    lines_c01.append(("text", ""))
    
    # Cargar y listar
    sc.cargar_datos()
    def fake_cons():
        sc.consultar_solicitudes()
    
    sub_lines = run_interactive(fake_cons, [], menu_opc=None, show_menu=False)
    # Omitir el ps inicial de sub_lines
    lines_c01.extend(sub_lines[1:])
    render_terminal("C-01_persistencia_sesiones.png", lines_c01)

    # ------------------------------------------------------------
    # C-02: Recuperación ante JSON corrupto
    # ------------------------------------------------------------
    # Hacer copia de seguridad de smart_cendis.json
    shutil.copyfile(JSON_PATH, JSON_PATH + ".bak")
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        f.write("{ JSON CORRUPTO")

    lines_c02 = []
    lines_c02.append(("ps", r"PS C:\Users\Asjer\OneDrive\Desktop\Laboratorio> python smartCendis_v3.py"))
    
    # Capturar mensaje de cargar_datos
    out = io.StringIO()
    old_out = sys.stdout
    sys.stdout = out
    try:
        sc.cargar_datos()
    finally:
        sys.stdout = old_out

    for l in out.getvalue().splitlines():
        if l.strip():
            lines_c02.append(("warning", l))

    lines_c02.append(("text", ""))
    lines_c02.append(("banner", "=================================================="))
    lines_c02.append(("banner", "              SMART CENDIS"))
    lines_c02.append(("banner", "=================================================="))
    lines_c02.append(("text",   "Sistema de Gestión Digital de Solicitudes,"))
    lines_c02.append(("text",   "Abastecimiento y Control de Inventario"))
    lines_c02.append(("banner", "=================================================="))
    lines_c02.append(("text",   " 1. Registrar medicamento"))
    lines_c02.append(("text",   " 2. Consultar medicamentos"))
    lines_c02.append(("text",   " ..."))
    lines_c02.append(("text",   " 0. Salir"))
    lines_c02.append(("banner", "=================================================="))
    lines_c02.append(("input",  "Seleccione una opción: 0"))
    lines_c02.append(("text", ""))
    lines_c02.append(("text",   "Saliendo de SMART CENDIS..."))
    lines_c02.append(("success","Sistema finalizado correctamente."))

    render_terminal("C-02_json_corrupto.png", lines_c02)

    # Restaurar backup
    shutil.copyfile(JSON_PATH + ".bak", JSON_PATH)
    os.remove(JSON_PATH + ".bak")

    print("\n¡14 capturas generadas con éxito en 'capturas reales/'!")
    print("Nota: C-03 (Rollback) queda pendiente como solicitaste para ejecutarse de forma controlada.")

if __name__ == "__main__":
    generar_todas()
