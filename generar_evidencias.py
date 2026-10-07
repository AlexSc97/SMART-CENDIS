"""
Script de generacion de evidencias individuales para SMART CENDIS Etapa 3.
Ejecutar: python -X utf8 generar_evidencias.py
"""
import sys
import io
import os
import json
from contextlib import redirect_stdout
from unittest.mock import patch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smartCendis_v3 as sc

EV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evidencias")
JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smart_cendis.json")
os.makedirs(EV, exist_ok=True)


def reset():
    sc.medicamentos[:] = [
        {"clave": "5121", "nombre": "Paracetamol 1 g",
         "presentacion": "Solucion inyectable", "unidad_fisica": "Ampolleta",
         "stock_actual": 26, "stock_objetivo": 30, "activo": True}
    ]
    sc.pacientes[:] = [
        {"servicio": "Pediatria", "cama": "01",
         "nombre": "Paciente de prueba 001", "nss": "00000000001"},
        {"servicio": "Medicina Interna", "cama": "01",
         "nombre": "Paciente de prueba 003", "nss": "00000000003"},
        {"servicio": "Urgencias", "cama": "01",
         "nombre": "Paciente de prueba 004", "nss": "00000000004"},
    ]
    sc.solicitudes.clear()
    sc.contador_solicitudes = 1
    for p in [JSON_PATH, JSON_PATH + ".tmp"]:
        if os.path.exists(p):
            os.remove(p)


def run(func, inputs):
    """Ejecuta func con entradas simuladas y captura stdout."""
    out = io.StringIO()
    it = iter(inputs)
    with redirect_stdout(out):
        with patch("builtins.input", side_effect=lambda p="": next(it, "")):
            try:
                func()
            except StopIteration:
                pass
    return out.getvalue()


def guardar_ev(nombre, titulo, contenido):
    path = os.path.join(EV, nombre)
    with open(path, "w", encoding="utf-8") as f:
        f.write(titulo + "\n")
        f.write("=" * 60 + "\n")
        f.write(contenido)
    print(f"  [OK] {nombre}")


# ------------------------------------------------------------------
# EV-02: Clave invalida rechazada por RE_CLAVE_MED
# ------------------------------------------------------------------
reset()
txt = run(sc.registrar_medicamento, ["123", "ABCD", "", "9999"])
guardar_ev(
    "EV-02_clave_invalida_regex.txt",
    "EVIDENCIA 02 - Clave invalida rechazada por RE_CLAVE_MED",
    f"Entradas probadas: '123' / 'ABCD' / '' (todas invalidas)\n\n{txt}"
)

# ------------------------------------------------------------------
# EV-03: Folio con formato incorrecto rechazado por RE_FOLIO
# ------------------------------------------------------------------
reset()
txt = run(sc.procesar_solicitud, ["000001", "SOL-12"])
guardar_ev(
    "EV-03_folio_invalido_regex.txt",
    "EVIDENCIA 03 - Folio sin prefijo SOL- rechazado por RE_FOLIO",
    f"Entrada: '000001' (sin prefijo SOL-)\nEntrada: 'SOL-12' (menos de 4 digitos)\n\n{txt}"
)

# ------------------------------------------------------------------
# EV-04: Flujo completo solicitud -> SURTIDA -> Recepcion total
# ------------------------------------------------------------------
reset()
sc.guardar_datos()
txt1 = run(sc.registrar_solicitud,
           ["Pediatria", "01", "parace", "1", "5", "1", "Enf Lopez", "1"])
txt2 = run(sc.procesar_solicitud, ["SOL-0001", "1"])
txt3 = run(sc.registrar_recepcion, ["SOL-0001", "5"])
guardar_ev(
    "EV-04_flujo_completo.txt",
    "EVIDENCIA 04 - Flujo completo: Solicitud -> Proceso -> Recepcion",
    (
        "PASO 1: Registrar solicitud\n" + txt1 + "\n" +
        "PASO 2: Procesar (farmacia surte)\n" + txt2 + "\n" +
        "PASO 3: Recepcion total (5 unidades)\n" + txt3
    )
)

# ------------------------------------------------------------------
# EV-05: JSON corrupto conserva datos iniciales
# ------------------------------------------------------------------
reset()
with open(JSON_PATH, "w", encoding="utf-8") as f:
    f.write("{CORRUPTO_NO_ES_JSON}")
out = io.StringIO()
with redirect_stdout(out):
    sc.cargar_datos()
clave_inicial = sc.medicamentos[0]["clave"]
guardar_ev(
    "EV-05_json_corrupto.txt",
    "EVIDENCIA 05 - JSON corrupto conserva datos iniciales",
    (
        f"Contenido del archivo: {{CORRUPTO_NO_ES_JSON}}\n\n"
        f"{out.getvalue()}\n"
        f"Medicamentos en memoria: {len(sc.medicamentos)}\n"
        f"Clave del primer medicamento: {clave_inicial} (dato inicial)\n"
    )
)

# ------------------------------------------------------------------
# EV-06: Recepcion parcial -> estado SURTIDA_PARCIAL
# ------------------------------------------------------------------
reset()
sc.solicitudes.append({
    "folio": "SOL-0001", "servicio": "Urgencias", "cama": "01",
    "paciente": "Paciente de prueba 004", "nss": "00000000004",
    "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
    "cantidad": 10, "cantidad_recibida": 0, "cantidad_pendiente": 10,
    "turno": "NOCTURNO", "usuario": "Dr Martinez",
    "tipo": "URGENCIA", "estado": "SURTIDA"
})
sc.contador_solicitudes = 2
sc.guardar_datos()
txt = run(sc.registrar_recepcion, ["SOL-0001", "6"])
guardar_ev(
    "EV-06_recepcion_parcial.txt",
    "EVIDENCIA 06 - Recepcion parcial -> estado SURTIDA_PARCIAL",
    f"Cantidad solicitada: 10 | Cantidad recibida: 6 | Pendiente: 4\n\n{txt}"
)

# ------------------------------------------------------------------
# EV-07: Contador atrasado se corrige automaticamente al cargar
# ------------------------------------------------------------------
reset()
data = {
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
    "contador_solicitudes": 3  # atrasado: folio max es 5
}
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
out = io.StringIO()
with redirect_stdout(out):
    sc.cargar_datos()
guardar_ev(
    "EV-07_contador_corregido.txt",
    "EVIDENCIA 07 - Contador atrasado se corrige al cargar datos",
    (
        f"Folio maximo en JSON: SOL-0005 (numero 5)\n"
        f"Contador guardado: 3 (atrasado — deberia ser > 5)\n\n"
        f"{out.getvalue()}\n"
        f"Contador resultante en memoria: {sc.contador_solicitudes} "
        f"(esperado: 6)\n"
    )
)

# ------------------------------------------------------------------
# EV-08: Estado invalido en JSON es rechazado
# ------------------------------------------------------------------
reset()
data2 = {
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
    json.dump(data2, f, ensure_ascii=False, indent=4)
out = io.StringIO()
with redirect_stdout(out):
    sc.cargar_datos()
guardar_ev(
    "EV-08_estado_invalido_json.txt",
    "EVIDENCIA 08 - Estado invalido en JSON rechazado al cargar",
    (
        f"Estado en JSON: 'ESTADO_DESCONOCIDO' (no pertenece al conjunto valido)\n\n"
        f"{out.getvalue()}\n"
        f"Solicitudes en memoria tras carga: {len(sc.solicitudes)} "
        f"(esperado: 0 — datos iniciales)\n"
    )
)

# ------------------------------------------------------------------
# EV-09: Desactivacion de medicamento
# ------------------------------------------------------------------
reset()
txt = run(sc.eliminar_medicamento, ["5121", "S"])
guardar_ev(
    "EV-09_desactivar_medicamento.txt",
    "EVIDENCIA 09 - Desactivacion logica de medicamento",
    f"Clave: 5121 | Confirmacion: S\n\n{txt}"
)

# ------------------------------------------------------------------
# EV-10: Limpiar historial con confirmacion y sin confirmacion
# ------------------------------------------------------------------
reset()
sc.solicitudes.append({
    "folio": "SOL-0001", "servicio": "Pediatria", "cama": "01",
    "paciente": "T", "nss": "0", "medicamento": "5121",
    "nombre_medicamento": "P", "cantidad": 1,
    "cantidad_recibida": 0, "cantidad_pendiente": 1,
    "turno": "MATUTINO", "usuario": "T",
    "tipo": "NORMAL", "estado": "PENDIENTE"
})
sc.contador_solicitudes = 2
sc.guardar_datos()
txt_confirm = run(sc.limpiar_registros, ["s"])
txt_cancel = run(sc.limpiar_registros, ["n"])
guardar_ev(
    "EV-10_limpiar_historial.txt",
    "EVIDENCIA 10 - Limpiar historial (confirmado y cancelado)",
    (
        "--- Con confirmacion 's' ---\n" + txt_confirm + "\n"
        "--- Con cancelacion 'n' ---\n" + txt_cancel
    )
)

print("\nTodas las evidencias generadas en:", EV)
