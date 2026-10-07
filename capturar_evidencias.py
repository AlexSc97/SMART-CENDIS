"""
capturar_evidencias.py
Genera capturas de pantalla PNG para cada prueba de SMART CENDIS Etapa 3.
Usa Pillow para renderizar la salida de terminal en imágenes de alta calidad.

Ejecutar: python -X utf8 capturar_evidencias.py
"""

import sys
import io
import os
import json
from contextlib import redirect_stdout
from unittest.mock import patch
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
EV_DIR    = os.path.join(BASE_DIR, "evidencias")
JSON_PATH = os.path.join(BASE_DIR, "smart_cendis.json")
os.makedirs(EV_DIR, exist_ok=True)

sys.path.insert(0, BASE_DIR)
import smartCendis_v3 as sc


# ──────────────────────────────────────────────
#  CONFIGURACIÓN VISUAL DE LAS CAPTURAS
# ──────────────────────────────────────────────
BG_COLOR     = (18, 18, 18)      # fondo negro oscuro
FG_COLOR     = (204, 204, 204)   # texto gris claro
OK_COLOR     = (80, 200, 120)    # verde — PASS / éxito
ERR_COLOR    = (255, 95, 87)     # rojo — error / rechazo
TITLE_COLOR  = (90, 180, 255)    # azul — títulos de sección
PROMPT_COLOR = (255, 215, 0)     # amarillo — prompts del sistema
SHADOW_COLOR = (0, 0, 0, 160)

PAD_X        = 40
PAD_Y        = 40
LINE_HEIGHT  = 26
FONT_SIZE    = 18
TITLE_SIZE   = 20
HEADER_H     = 90   # altura del banner superior


def _get_font(size=FONT_SIZE, bold=False):
    """Intenta cargar Consolas o Courier New; fallback a default."""
    candidates_bold  = ["consolab.ttf", "courbd.ttf", "DejaVuSansMono-Bold.ttf"]
    candidates_plain = ["consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"]
    candidates = candidates_bold if bold else candidates_plain
    for name in candidates:
        for folder in [r"C:\Windows\Fonts", "/usr/share/fonts/truetype/dejavu",
                       "/System/Library/Fonts"]:
            path = os.path.join(folder, name)
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
    return ImageFont.load_default()


FONT       = _get_font(FONT_SIZE)
FONT_BOLD  = _get_font(FONT_SIZE, bold=True)
FONT_TITLE = _get_font(TITLE_SIZE, bold=True)


def _line_color(line: str) -> tuple:
    """Elige el color de la línea según su contenido."""
    low = line.lower()
    if any(k in low for k in ("error:", "rechazad", "invalido", "inválido",
                               "no se encontr", "fail", "cancelad",
                               "no puede", "no se pudo")):
        return ERR_COLOR
    if any(k in low for k in ("correctamente", "registrad", "pass ✓",
                               "surtida", "desactivad", "eliminado",
                               "encontrado", "stock nuevo")):
        return OK_COLOR
    if any(k in low for k in ("====", "----", "paso ", "grupo ",
                               "evidencia", "aviso:")):
        return TITLE_COLOR
    if any(k in low for k in ("ingrese", "seleccione", "presione",
                               "¿desea", "nuevo ", "esto eliminará")):
        return PROMPT_COLOR
    return FG_COLOR


def captura_png(filename: str, titulo: str, subtitulo: str,
                cuerpo: str, badge: str = ""):
    """
    Genera una imagen PNG estilo terminal con el contenido dado.

    Parámetros
    ----------
    filename  : nombre del archivo de salida (sin ruta).
    titulo    : título principal (primera línea del banner).
    subtitulo : descripción breve del escenario.
    cuerpo    : texto de salida del programa.
    badge     : etiqueta opcional: 'PASS', 'FAIL' o ''.
    """
    lines = cuerpo.strip().splitlines()

    # Calcular dimensiones
    max_chars = max((len(l) for l in lines), default=60)
    width     = max(860, PAD_X * 2 + max_chars * 11)
    height    = HEADER_H + PAD_Y + len(lines) * LINE_HEIGHT + PAD_Y * 2

    img  = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # ── Banner superior ──────────────────────────────────────
    draw.rectangle([(0, 0), (width, HEADER_H)], fill=(28, 28, 40))
    # Puntos de tráfico (macOS style)
    for cx, color in [(24, (255, 95, 87)), (50, (255, 188, 66)),
                      (76, (40, 201, 113))]:
        draw.ellipse([(cx - 8, 18), (cx + 8, 34)], fill=color)
    # Título
    draw.text((110, 10), "SMART CENDIS — Etapa 3", font=FONT_TITLE,
              fill=(90, 180, 255))
    draw.text((110, 36), titulo, font=FONT_BOLD, fill=(220, 220, 220))
    draw.text((110, 62), subtitulo, font=FONT, fill=(160, 160, 160))

    # Badge PASS / FAIL
    if badge:
        bcolor = OK_COLOR if badge == "PASS" else ERR_COLOR
        bw = 80
        draw.rectangle([(width - bw - 20, 22), (width - 20, 68)],
                        fill=bcolor, outline=bcolor)
        draw.text((width - bw - 10, 32), badge, font=FONT_BOLD, fill=(0, 0, 0))

    # ── Línea divisora ───────────────────────────────────────
    draw.line([(0, HEADER_H), (width, HEADER_H)], fill=(60, 60, 80), width=2)

    # ── Cuerpo del texto ─────────────────────────────────────
    y = HEADER_H + PAD_Y
    for line in lines:
        color = _line_color(line)
        draw.text((PAD_X, y), line, font=FONT, fill=color)
        y += LINE_HEIGHT

    # ── Pie de página ─────────────────────────────────────────
    draw.line([(0, height - 30), (width, height - 30)],
              fill=(60, 60, 80), width=1)
    draw.text((PAD_X, height - 24),
              f"Laboratorio SMART CENDIS  |  {filename}",
              font=FONT, fill=(80, 80, 100))

    out_path = os.path.join(EV_DIR, filename)
    img.save(out_path, "PNG", optimize=True)
    print(f"  [PNG] {filename}  ({width}x{height}px)")


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def reset():
    sc.medicamentos[:] = [
        {"clave": "5121", "nombre": "Paracetamol 1 g",
         "presentacion": "Solucion inyectable", "unidad_fisica": "Ampolleta",
         "stock_actual": 26, "stock_objetivo": 30, "activo": True}
    ]
    sc.pacientes[:] = [
        {"servicio": "Pediatria",        "cama": "01",
         "nombre": "Paciente de prueba 001", "nss": "00000000001"},
        {"servicio": "Pediatria",        "cama": "02",
         "nombre": "Paciente de prueba 002", "nss": "00000000002"},
        {"servicio": "Medicina Interna", "cama": "01",
         "nombre": "Paciente de prueba 003", "nss": "00000000003"},
        {"servicio": "Urgencias",        "cama": "01",
         "nombre": "Paciente de prueba 004", "nss": "00000000004"},
    ]
    sc.solicitudes.clear()
    sc.contador_solicitudes = 1
    for p in [JSON_PATH, JSON_PATH + ".tmp"]:
        if os.path.exists(p):
            os.remove(p)


def run(func, inputs):
    out = io.StringIO()
    it  = iter(inputs)
    with redirect_stdout(out):
        with patch("builtins.input",
                   side_effect=lambda p="": next(it, "")):
            try:
                func()
            except StopIteration:
                pass
    return out.getvalue()


def sol_surtida(folio, cantidad, servicio="Pediatria", cama="01",
                paciente="Paciente de prueba 001", nss="00000000001"):
    """Inyecta una solicitud SURTIDA directamente en memoria."""
    sc.solicitudes.append({
        "folio": folio, "servicio": servicio, "cama": cama,
        "paciente": paciente, "nss": nss,
        "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
        "cantidad": cantidad, "cantidad_recibida": 0,
        "cantidad_pendiente": cantidad,
        "turno": "MATUTINO", "usuario": "Enf Lopez",
        "tipo": "NORMAL", "estado": "SURTIDA"
    })
    sc.contador_solicitudes = int(folio.split("-")[1]) + 1
    sc.guardar_datos()


def sol_pendiente(folio, cantidad):
    sc.solicitudes.append({
        "folio": folio, "servicio": "Pediatria", "cama": "01",
        "paciente": "Paciente de prueba 001", "nss": "00000000001",
        "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
        "cantidad": cantidad, "cantidad_recibida": 0,
        "cantidad_pendiente": cantidad,
        "turno": "MATUTINO", "usuario": "Enf Lopez",
        "tipo": "NORMAL", "estado": "PENDIENTE"
    })
    sc.contador_solicitudes = int(folio.split("-")[1]) + 1
    sc.guardar_datos()


# ══════════════════════════════════════════════
#  GRUPO A — VALIDACIONES DE FORMATO (REGEX)
# ══════════════════════════════════════════════

print("\n=== GRUPO A — Validaciones de formato (regex) ===")

# A-01: Clave con 3 dígitos rechazada
reset()
txt = run(sc.registrar_medicamento, ["123", "456", "789", "0000"])
captura_png("A-01_clave_3_digitos.png",
            "A-01 — Clave con 3 dígitos rechazada",
            "RE_CLAVE_MED exige exactamente 4 dígitos",
            f"Entrada: '123'  (3 dígitos — formato inválido)\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-02: Clave con letras rechazada
reset()
txt = run(sc.registrar_medicamento, ["ABCD", "XYZ1", "aaaa", "0000"])
captura_png("A-02_clave_con_letras.png",
            "A-02 — Clave con letras rechazada",
            "RE_CLAVE_MED solo acepta dígitos (0-9)",
            f"Entrada: 'ABCD'  (letras — formato inválido)\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-03: Nombre vacío rechazado
reset()
txt = run(sc.registrar_medicamento, ["5999", "", "x", ""])
captura_png("A-03_nombre_vacio.png",
            "A-03 — Nombre vacío rechazado",
            "RE_NOMBRE_MED exige al menos 2 caracteres",
            f"Clave válida: '5999' → Nombre vacío ''\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-04: Stock negativo rechazado
reset()
txt = run(sc.registrar_medicamento,
          ["5999", "Ibuprofeno 400 mg", "Comprimido", "Tableta", "-5"])
captura_png("A-04_stock_negativo.png",
            "A-04 — Stock negativo rechazado por RE_STOCK",
            "RE_STOCK acepta solo enteros ≥ 0",
            f"Entrada stock: '-5'  (negativo — formato inválido)\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-05: Folio sin prefijo SOL-
reset()
txt = run(sc.procesar_solicitud, ["000001", "001234", "sol1234"])
captura_png("A-05_folio_sin_prefijo.png",
            "A-05 — Folio sin prefijo SOL- rechazado",
            "RE_FOLIO exige SOL-NNNN (≥4 dígitos)",
            f"Entradas: '000001', '001234', 'sol1234'  (sin prefijo correcto)\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-06: Folio con menos de 4 dígitos
reset()
txt = run(sc.procesar_solicitud, ["SOL-1", "SOL-12", "SOL-123"])
captura_png("A-06_folio_pocos_digitos.png",
            "A-06 — Folio SOL-12 rechazado (< 4 dígitos)",
            "RE_FOLIO requiere al menos 4 dígitos tras SOL-",
            f"Entradas: 'SOL-1', 'SOL-12', 'SOL-123'\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-07: Servicio con dígitos rechazado
reset()
txt = run(sc.consultar_paciente, ["Pediatria2", "3Urgencias", "123"])
captura_png("A-07_servicio_con_digitos.png",
            "A-07 — Servicio con dígitos rechazado",
            "RE_SERVICIO solo acepta letras y espacios",
            f"Entradas: 'Pediatria2', '3Urgencias', '123'\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-08: Cama con letras rechazada
reset()
txt = run(sc.consultar_paciente, ["Pediatria", "A1", "B2", "cama"])
captura_png("A-08_cama_con_letras.png",
            "A-08 — Cama con letras rechazada",
            "RE_CAMA acepta solo 1–4 dígitos",
            f"Servicio válido: 'Pediatria' → Cama: 'A1', 'B2', 'cama'\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-09: Turno fuera de rango
reset()
txt = run(sc.seleccionar_turno, ["4", "5", "0", "9"])
captura_png("A-09_turno_invalido.png",
            "A-09 — Opción de turno fuera de rango rechazada",
            "RE_TURNO_OPC acepta solo 1, 2 o 3",
            f"Entradas: '4', '5', '0', '9'\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-10: Usuario vacío
reset()
sc.guardar_datos()
txt = run(sc.registrar_solicitud,
          ["Pediatria", "01", "parace", "1", "5", "1", "", "", ""])
captura_png("A-10_usuario_vacio.png",
            "A-10 — Usuario vacío rechazado",
            "RE_USUARIO exige al menos 2 caracteres",
            f"Servicio/cama/medicamento válidos → Usuario: '' (vacío)\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-11: Opción menú fuera de rango
reset()
txt = run(lambda: sc.leer_con_patron(
    "Seleccione una opción: ", sc.RE_MENU,
    "ingrese un número entre 0 y 11"),
    ["12", "99", "-1", "abc"])
captura_png("A-11_menu_fuera_de_rango.png",
            "A-11 — Opción de menú fuera de rango rechazada",
            "RE_MENU acepta solo 0–11",
            f"Entradas: '12', '99', '-1', 'abc'\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-12: Confirmación inválida al desactivar
reset()
txt = run(sc.eliminar_medicamento, ["5121", "X", "Y", "Z"])
captura_png("A-12_confirmacion_invalida.png",
            "A-12 — Confirmación 'X' en desactivar rechazada",
            "RE_CONFIRMACION_DESACTIVAR acepta solo S/s/N/n",
            f"Clave válida: 5121 → Confirmación: 'X', 'Y', 'Z'\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-13: Cantidad solicitada = 0
reset()
sc.guardar_datos()
txt = run(sc.registrar_solicitud,
          ["Pediatria", "01", "parace", "1", "0"])
captura_png("A-13_cantidad_cero.png",
            "A-13 — Cantidad solicitada 0 rechazada por regex",
            "RE_CANTIDAD_POS exige entero ≥ 1",
            f"Entradas hasta cantidad: '0'  (cero — inválido)\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")

# A-14: Cantidad recibida con texto
reset()
sol_surtida("SOL-0001", 5)
txt = run(sc.registrar_recepcion, ["SOL-0001", "diez", "cinco", "dos"])
captura_png("A-14_cantidad_texto.png",
            "A-14 — Cantidad recibida 'diez' rechazada",
            "RE_CANTIDAD_GE0 exige entero; rechaza texto",
            f"Folio SOL-0001 (SURTIDA) → Cantidad: 'diez', 'cinco', 'dos'\n\n{txt}",
            badge="PASS" if "formato inválido" in txt.lower() else "FAIL")


# ══════════════════════════════════════════════
#  GRUPO B — FLUJO FUNCIONAL
# ══════════════════════════════════════════════

print("\n=== GRUPO B — Flujo funcional ===")

# B-01: Registro de medicamento válido
reset()
txt = run(sc.registrar_medicamento,
          ["5200", "Amoxicilina 500 mg", "Capsula", "Capsula", "100", "120"])
captura_png("B-01_registro_medicamento.png",
            "B-01 — Registro de medicamento válido",
            "Clave: 5200 | Amoxicilina 500 mg | Stock: 100/120",
            txt, badge="PASS" if "registrado correctamente" in txt.lower() else "FAIL")

# B-02: Clave duplicada
reset()
txt = run(sc.registrar_medicamento,
          ["5121", "Paracetamol 2 g", "Comprimido", "Tableta", "10", "15"])
captura_png("B-02_clave_duplicada.png",
            "B-02 — Clave duplicada rechazada",
            "La clave 5121 ya existe en el catálogo",
            txt, badge="PASS" if "ya se encuentra registrada" in txt.lower() else "FAIL")

# B-03: Paciente existente
reset()
txt = run(sc.consultar_paciente, ["Pediatria", "01"])
captura_png("B-03_paciente_existente.png",
            "B-03 — Consulta de paciente existente",
            "Servicio: Pediatria | Cama: 01",
            txt, badge="PASS" if "paciente encontrado" in txt.lower() else "FAIL")

# B-04: Paciente inexistente
reset()
txt = run(sc.consultar_paciente, ["Traumatologia", "05"])
captura_png("B-04_paciente_inexistente.png",
            "B-04 — Consulta de paciente inexistente",
            "Servicio: Traumatologia | Cama: 05 (no registrado)",
            txt, badge="PASS" if "no se encontr" in txt.lower() else "FAIL")

# B-05: Registrar solicitud completa
reset()
sc.guardar_datos()
txt = run(sc.registrar_solicitud,
          ["Pediatria", "01", "parace", "1", "5", "1", "Enf Lopez", "1"])
captura_png("B-05_registrar_solicitud.png",
            "B-05 — Solicitud registrada correctamente",
            "Paciente: Pediatria/01 | Medicamento: Paracetamol | Cantidad: 5",
            txt, badge="PASS" if "registrada correctamente" in txt.lower() else "FAIL")

# B-06, B-07, B-08: Turnos
for opc, nombre, badge_id in [("1", "MATUTINO", "B-06"),
                               ("2", "VESPERTINO", "B-07"),
                               ("3", "NOCTURNO", "B-08")]:
    reset()
    txt = run(lambda o=opc: print(sc.seleccionar_turno()), [opc])
    captura_png(f"{badge_id}_turno_{nombre.lower()}.png",
                f"{badge_id} — Turno {nombre} seleccionado",
                f"Opción: {opc} → Turno = {nombre}",
                txt, badge="PASS" if nombre in txt.upper() else "FAIL")

# B-09: PENDIENTE → SURTIDA
reset()
sol_pendiente("SOL-0001", 5)
txt = run(sc.procesar_solicitud, ["SOL-0001", "1"])
captura_png("B-09_solicitud_surtida.png",
            "B-09 — Solicitud PENDIENTE → SURTIDA",
            "Farmacia responde: Surtida",
            txt, badge="PASS" if "surtida" in txt.lower() else "FAIL")

# B-10: Recepción total
reset()
sol_surtida("SOL-0001", 5)
stock_antes = sc.medicamentos[0]["stock_actual"]
txt = run(sc.registrar_recepcion, ["SOL-0001", "5"])
captura_png("B-10_recepcion_total.png",
            "B-10 — Recepción total actualiza stock",
            f"Stock antes: {stock_antes} → Stock esperado: {stock_antes + 5}",
            txt, badge="PASS" if f"stock nuevo: {stock_antes + 5}" in txt.lower() else "FAIL")

# B-11: Recepción parcial → SURTIDA_PARCIAL
reset()
sc.solicitudes.append({
    "folio": "SOL-0002", "servicio": "Urgencias", "cama": "01",
    "paciente": "Paciente de prueba 004", "nss": "00000000004",
    "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
    "cantidad": 10, "cantidad_recibida": 0, "cantidad_pendiente": 10,
    "turno": "NOCTURNO", "usuario": "Dr Martinez",
    "tipo": "URGENCIA", "estado": "SURTIDA"
})
sc.contador_solicitudes = 3
sc.guardar_datos()
txt = run(sc.registrar_recepcion, ["SOL-0002", "6"])
captura_png("B-11_recepcion_parcial.png",
            "B-11 — Recepción parcial → SURTIDA_PARCIAL",
            "Solicitado: 10 | Recibido: 6 | Pendiente: 4",
            txt, badge="PASS" if "surtida_parcial" in txt.lower() else "FAIL")

# B-12: NEGADA no se puede recibir
reset()
sc.solicitudes.append({
    "folio": "SOL-0003", "servicio": "Pediatria", "cama": "02",
    "paciente": "Paciente de prueba 002", "nss": "00000000002",
    "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
    "cantidad": 3, "cantidad_recibida": 0, "cantidad_pendiente": 3,
    "turno": "VESPERTINO", "usuario": "Enf Rios",
    "tipo": "NORMAL", "estado": "NEGADA"
})
sc.contador_solicitudes = 4
sc.guardar_datos()
txt = run(sc.registrar_recepcion, ["SOL-0003"])
captura_png("B-12_recepcion_negada.png",
            "B-12 — Recepción de solicitud NEGADA rechazada",
            "Solo se puede recibir una solicitud SURTIDA",
            txt, badge="PASS" if "solo se puede recibir" in txt.lower() else "FAIL")

# B-13: Modificar medicamento
reset()
txt = run(sc.modificar_medicamento, ["5121", "Paracetamol 1 g - EFG", "35"])
captura_png("B-13_modificar_medicamento.png",
            "B-13 — Modificación de medicamento",
            "Nuevo nombre: Paracetamol 1 g - EFG | Nuevo stock objetivo: 35",
            txt, badge="PASS" if "modificado correctamente" in txt.lower() else "FAIL")

# B-14: Desactivar medicamento
reset()
txt = run(sc.eliminar_medicamento, ["5121", "S"])
captura_png("B-14_desactivar_medicamento.png",
            "B-14 — Desactivación lógica de medicamento",
            "Clave: 5121 | Confirmación: S",
            txt, badge="PASS" if "desactivado correctamente" in txt.lower() else "FAIL")

# B-15: Medicamento desactivado no aparece
reset()
sc.medicamentos[0]["activo"] = False
txt = run(sc.seleccionar_medicamento, [])
captura_png("B-15_medicamento_desactivado.png",
            "B-15 — Medicamento desactivado no aparece en búsqueda",
            "Activo=False → catálogo vacío para el usuario",
            txt, badge="PASS" if "no hay medicamentos" in txt.lower() else "FAIL")

# B-16: Limpiar historial confirmado
reset()
sol_pendiente("SOL-0001", 2)
txt = run(sc.limpiar_registros, ["s"])
captura_png("B-16_limpiar_historial_confirmado.png",
            "B-16 — Limpiar historial (confirmado con 's')",
            "Historial eliminado y contador reiniciado",
            txt, badge="PASS" if "eliminado correctamente" in txt.lower() else "FAIL")

# B-17: Limpiar historial cancelado
reset()
txt = run(sc.limpiar_registros, ["n"])
captura_png("B-17_limpiar_historial_cancelado.png",
            "B-17 — Limpieza cancelada con 'n'",
            "Respuesta 'n' → operación abortada",
            txt, badge="PASS" if "cancelada" in txt.lower() else "FAIL")

# B-18: Consultar inventario
reset()
txt = run(sc.consultar_inventario, [])
captura_png("B-18_consultar_inventario.png",
            "B-18 — Consultar inventario con medicamento activo",
            "Muestra stock actual, objetivo y faltante",
            txt, badge="PASS" if "paracetamol" in txt.lower() else "FAIL")

# B-19: Flujo completo integrado
reset()
sc.guardar_datos()
txt_sol = run(sc.registrar_solicitud,
              ["Medicina Interna", "01", "parace", "1", "3", "1", "Dr Torres", "1"])
txt_proc = run(sc.procesar_solicitud, ["SOL-0001", "1"])
stock_antes = sc.medicamentos[0]["stock_actual"]
txt_rec  = run(sc.registrar_recepcion, ["SOL-0001", "3"])
cuerpo = ("─── PASO 1: Registrar solicitud ───\n" + txt_sol +
          "\n─── PASO 2: Procesar (farmacia surte) ───\n" + txt_proc +
          "\n─── PASO 3: Registrar recepción total (3 uds) ───\n" + txt_rec)
captura_png("B-19_flujo_completo.png",
            "B-19 — Flujo completo: Solicitud → SURTIDA → Recepción",
            "Medicina Interna/01 | Paracetamol x3 | Dr Torres | NORMAL",
            cuerpo,
            badge="PASS" if f"stock nuevo: {stock_antes + 3}" in txt_rec.lower() else "FAIL")


# ══════════════════════════════════════════════
#  GRUPO C — ROBUSTEZ Y PERSISTENCIA
# ══════════════════════════════════════════════

print("\n=== GRUPO C — Robustez y persistencia ===")

# C-01: JSON corrupto
reset()
with open(JSON_PATH, "w", encoding="utf-8") as f:
    f.write("{CORRUPTO_NO_ES_JSON}")
out = io.StringIO()
with redirect_stdout(out):
    sc.cargar_datos()
aviso = out.getvalue()
ok_c01 = sc.medicamentos[0]["clave"] == "5121"
cuerpo = (
    "Contenido del archivo JSON:\n"
    "  {CORRUPTO_NO_ES_JSON}\n\n"
    f"{aviso}\n"
    f"Medicamentos en memoria : {len(sc.medicamentos)}\n"
    f"Clave primer medicamento: {sc.medicamentos[0]['clave']} (dato inicial)\n"
)
captura_png("C-01_json_corrupto.png",
            "C-01 — JSON corrupto conserva datos iniciales",
            "cargar_datos() avisa y mantiene los datos del programa",
            cuerpo, badge="PASS" if ok_c01 else "FAIL")
reset()

# C-02: Sin archivo JSON
reset()
out = io.StringIO()
with redirect_stdout(out):
    sc.cargar_datos()
ok_c02 = len(sc.medicamentos) == 1 and sc.contador_solicitudes == 1
captura_png("C-02_sin_archivo_json.png",
            "C-02 — Sin archivo JSON: arranque limpio",
            "FileNotFoundError manejado; datos iniciales en memoria",
            f"Medicamentos : {len(sc.medicamentos)}\n"
            f"Contador     : {sc.contador_solicitudes}\n"
            f"Solicitudes  : {len(sc.solicitudes)}\n\n"
            f"{out.getvalue() or '(sin aviso — primer arranque normal)'}",
            badge="PASS" if ok_c02 else "FAIL")

# C-03: guardar_datos retorna True
reset()
ok_c03 = sc.guardar_datos() is True
captura_png("C-03_guardar_retorna_true.png",
            "C-03 — guardar_datos() retorna True en condiciones normales",
            "Escritura atómica vía archivo temporal + os.replace",
            f"Resultado de guardar_datos() : {ok_c03}\n"
            f"Archivo creado               : {os.path.exists(JSON_PATH)}\n",
            badge="PASS" if ok_c03 else "FAIL")

# C-04: Persistencia entre sesiones
reset()
sol_pendiente("SOL-0001", 7)
# Simular nueva sesión
sc.medicamentos.clear()
sc.solicitudes.clear()
sc.contador_solicitudes = 1
sc.cargar_datos()
ok_c04 = (len(sc.solicitudes) == 1
          and sc.solicitudes[0]["folio"] == "SOL-0001"
          and sc.contador_solicitudes == 2)
captura_png("C-04_persistencia_entre_sesiones.png",
            "C-04 — Persistencia entre sesiones",
            "guardar_datos() → reiniciar variables → cargar_datos()",
            f"Solicitudes cargadas : {len(sc.solicitudes)}\n"
            f"Folio recuperado     : {sc.solicitudes[0]['folio'] if sc.solicitudes else 'N/A'}\n"
            f"Contador recuperado  : {sc.contador_solicitudes}\n",
            badge="PASS" if ok_c04 else "FAIL")
reset()

# C-05: Estado inválido en JSON
reset()
datos_malos = {
    "medicamentos": sc.medicamentos,
    "pacientes": sc.pacientes,
    "solicitudes": [{
        "folio": "SOL-0001", "servicio": "Pediatria", "cama": "01",
        "paciente": "T", "nss": "0", "medicamento": "5121",
        "nombre_medicamento": "P", "cantidad": 3,
        "cantidad_recibida": 0, "cantidad_pendiente": 3,
        "turno": "MATUTINO", "usuario": "T",
        "tipo": "NORMAL", "estado": "ESTADO_DESCONOCIDO"
    }],
    "contador_solicitudes": 2
}
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(datos_malos, f, ensure_ascii=False, indent=4)
out = io.StringIO()
with redirect_stdout(out):
    sc.cargar_datos()
ok_c05 = len(sc.solicitudes) == 0
captura_png("C-05_estado_invalido_json.png",
            "C-05 — Estado inválido en JSON rechazado",
            "Estado 'ESTADO_DESCONOCIDO' no pertenece al conjunto válido",
            f"Estado en JSON : 'ESTADO_DESCONOCIDO'\n\n{out.getvalue()}\n"
            f"Solicitudes en memoria tras carga: {len(sc.solicitudes)} (esperado: 0)",
            badge="PASS" if ok_c05 else "FAIL")
reset()

# C-06: Stock negativo en JSON
reset()
datos_neg = {
    "medicamentos": [{
        "clave": "5121", "nombre": "Paracetamol 1 g",
        "presentacion": "Sol iny", "unidad_fisica": "Ampolleta",
        "stock_actual": -5, "stock_objetivo": 30, "activo": True
    }],
    "pacientes": sc.pacientes,
    "solicitudes": [],
    "contador_solicitudes": 1
}
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(datos_neg, f, ensure_ascii=False, indent=4)
out = io.StringIO()
with redirect_stdout(out):
    sc.cargar_datos()
ok_c06 = sc.medicamentos[0]["stock_actual"] == 26
captura_png("C-06_stock_negativo_json.png",
            "C-06 — Stock negativo en JSON rechazado al cargar",
            "Medicamento con stock_actual=-5 invalida la carga",
            f"stock_actual en JSON : -5\n\n{out.getvalue()}\n"
            f"stock_actual en memoria: {sc.medicamentos[0]['stock_actual']} (dato inicial=26)",
            badge="PASS" if ok_c06 else "FAIL")
reset()


# ══════════════════════════════════════════════
#  GRUPO D — CONTADOR Y FOLIOS
# ══════════════════════════════════════════════

print("\n=== GRUPO D — Contador y folios ===")

# D-01: Contador atrasado corregido
reset()
datos = {
    "medicamentos": sc.medicamentos,
    "pacientes": sc.pacientes,
    "solicitudes": [{
        "folio": "SOL-0005", "servicio": "Urgencias", "cama": "01",
        "paciente": "T", "nss": "0", "medicamento": "5121",
        "nombre_medicamento": "P", "cantidad": 1,
        "cantidad_recibida": 0, "cantidad_pendiente": 1,
        "turno": "MATUTINO", "usuario": "T",
        "tipo": "NORMAL", "estado": "PENDIENTE"
    }],
    "contador_solicitudes": 3
}
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=4)
out = io.StringIO()
with redirect_stdout(out):
    sc.cargar_datos()
ok_d01 = sc.contador_solicitudes == 6
captura_png("D-01_contador_atrasado.png",
            "D-01 — Contador atrasado se corrige al cargar",
            "Folio máx: SOL-0005 (5) | Contador en JSON: 3 → debe quedar 6",
            f"Contador en JSON      : 3\n"
            f"Folio máximo guardado : SOL-0005 (número 5)\n\n"
            f"{out.getvalue()}\n"
            f"Contador resultante   : {sc.contador_solicitudes} (esperado: 6)",
            badge="PASS" if ok_d01 else "FAIL")
reset()

# D-02: Secuencia de folios
reset()
sol_pendiente("SOL-0001", 5)
sig = f"SOL-{sc.contador_solicitudes:04d}"
ok_d02 = sig == "SOL-0002"
captura_png("D-02_secuencia_folios.png",
            "D-02 — Secuencia correcta de folios",
            "Tras SOL-0001, el siguiente folio debe ser SOL-0002",
            f"Folio registrado : SOL-0001\n"
            f"Contador actual  : {sc.contador_solicitudes}\n"
            f"Próximo folio    : {sig}",
            badge="PASS" if ok_d02 else "FAIL")

# D-03: Folio SOL-10000 (sin límite)
reset()
sc.contador_solicitudes = 10000
folio_sig = f"SOL-{sc.contador_solicitudes:04d}"
ok_d03 = folio_sig == "SOL-10000"
captura_png("D-03_folio_10000.png",
            "D-03 — Folio SOL-10000 válido (sin límite superior)",
            "El sistema no impone un máximo al número de folio",
            f"Contador       : 10000\n"
            f"Folio generado : {folio_sig}\n"
            f"RE_FOLIO match : {bool(sc.RE_FOLIO.fullmatch(folio_sig))}",
            badge="PASS" if ok_d03 else "FAIL")

# D-04: RE_FOLIO acepta SOL-10000
ok_d04 = bool(sc.RE_FOLIO.fullmatch("SOL-10000"))
captura_png("D-04_re_folio_acepta_10000.png",
            "D-04 — RE_FOLIO acepta SOL-10000",
            "Patrón: ^SOL-\\d{4,}$",
            f"re.fullmatch(RE_FOLIO, 'SOL-10000') → {ok_d04}",
            badge="PASS" if ok_d04 else "FAIL")

# D-05: RE_FOLIO rechaza SOL-12
ok_d05 = not bool(sc.RE_FOLIO.fullmatch("SOL-12"))
captura_png("D-05_re_folio_rechaza_12.png",
            "D-05 — RE_FOLIO rechaza SOL-12 (< 4 dígitos)",
            "Mínimo 4 dígitos requeridos tras SOL-",
            f"re.fullmatch(RE_FOLIO, 'SOL-12') → {not ok_d05}\n"
            f"Rechazado correctamente: {ok_d05}",
            badge="PASS" if ok_d05 else "FAIL")


# ──────────────────────────────────────────────
#  RESUMEN FINAL
# ──────────────────────────────────────────────

pngs = [f for f in os.listdir(EV_DIR) if f.endswith(".png")]
print(f"\n{'='*60}")
print(f"  Capturas PNG generadas: {len(pngs)}")
print(f"  Directorio: {EV_DIR}")
print(f"{'='*60}")
