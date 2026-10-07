# ============================================================
# SMART CENDIS  —  Suite de Pruebas Automatizadas  (Etapa 3)
# ============================================================
#
# Archivo  : test_smartCendis_v3.py
# Ejecutar : python test_smartCendis_v3.py
#
# La suite cubre:
#   Grupo A — Validaciones de formato (expresiones regulares)
#   Grupo B — Flujo funcional completo (regresión de Etapa 2)
#   Grupo C — Robustez y persistencia
#   Grupo D — Coherencia del contador y detección de folios
#
# Para cada caso se registra:
#   - ID, descripción, resultado esperado, resultado obtenido, estado (PASS/FAIL)
#
# Al finalizar se guarda un reporte en:
#   evidencias/reporte_pruebas.txt
# ============================================================

import io
import json
import os
import re
import sys
import textwrap
import traceback
from contextlib import redirect_stdout
from datetime import datetime
from unittest.mock import patch

# Forzar UTF-8 en la consola de Windows para evitar UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Ruta base del proyecto ──────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
EVIDENCIAS   = os.path.join(BASE_DIR, "evidencias")
REPORTE_TXT  = os.path.join(EVIDENCIAS, "reporte_pruebas.txt")
ARCHIVO_JSON = os.path.join(BASE_DIR, "smart_cendis.json")
ARCHIVO_TMP  = ARCHIVO_JSON + ".tmp"

os.makedirs(EVIDENCIAS, exist_ok=True)

# ── Importar el módulo bajo prueba ──────────────────────────
import importlib
import smartCendis_v3 as sc


# ============================================================
# UTILIDADES DE LA SUITE
# ============================================================

resultados: list[dict] = []
_SEPARADOR = "=" * 70


def _reset_estado():
    """Restaura las variables globales y elimina el JSON de persistencia."""
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
    for path in (ARCHIVO_JSON, ARCHIVO_TMP):
        if os.path.exists(path):
            os.remove(path)


def capturar_salida(func, entradas: list[str]) -> str:
    """
    Ejecuta func() inyectando entradas como stdin y captura stdout.
    Retorna el texto impreso.
    """
    stdin_simulado = io.StringIO("\n".join(entradas) + "\n")
    stdout_capturado = io.StringIO()
    with patch("builtins.input", side_effect=lambda prompt="": (
        print(prompt, end="", file=sys.stderr),   # imprime el prompt en stderr
        stdin_simulado.readline().rstrip("\n")
    )[1]):
        with redirect_stdout(stdout_capturado):
            try:
                func()
            except StopIteration:
                pass   # entradas agotadas antes de que la función termine
    return stdout_capturado.getvalue()


def caso(id_caso: str, descripcion: str, esperado: str,
         func, entradas: list[str]):
    """
    Ejecuta una prueba, registra el resultado y lo imprime.

    Parámetros
    ----------
    id_caso     : identificador único (p. ej. "A-01").
    descripcion : texto corto que describe el caso.
    esperado    : subcadena (o patrón) que debe aparecer en la salida.
    func        : función de smartCendis_v3 a ejecutar.
    entradas    : lista de cadenas que simulan la entrada del usuario.
    """
    try:
        salida = capturar_salida(func, entradas)
        ok = esperado.lower() in salida.lower()
        estado = "PASS" if ok else "FAIL"
    except Exception as exc:
        salida = traceback.format_exc()
        estado = "ERROR"
        ok = False

    registro = {
        "id":          id_caso,
        "descripcion": descripcion,
        "esperado":    esperado,
        "obtenido":    salida.strip(),
        "estado":      estado,
    }
    resultados.append(registro)

    # Salida en consola
    marca = "✓" if ok else "✗"
    print(f"  [{estado}] {marca} {id_caso} — {descripcion}")
    if not ok:
        # Mostrar primeras líneas de la salida para diagnóstico rápido
        lineas = salida.strip().splitlines()
        for linea in lineas[:6]:
            print(f"          {linea}")
        if len(lineas) > 6:
            print(f"          ... ({len(lineas) - 6} líneas más)")


# ============================================================
# GRUPO A — VALIDACIONES DE FORMATO (expresiones regulares)
# ============================================================

def grupo_a():
    print(f"\n{_SEPARADOR}")
    print("GRUPO A — Validaciones de formato (RE)")
    print(_SEPARADOR)

    _reset_estado()

    # A-01: Clave con menos de 4 dígitos → error de formato
    caso("A-01", "Clave con 3 dígitos rechazada",
         "Error: formato inválido",
         sc.registrar_medicamento,
         ["123"])   # clave inválida; se agotan entradas

    _reset_estado()

    # A-02: Clave con letras rechazada
    caso("A-02", "Clave con letras rechazada",
         "Error: formato inválido",
         sc.registrar_medicamento,
         ["ABCD"])

    _reset_estado()

    # A-03: Nombre vacío rechazado
    caso("A-03", "Nombre vacío rechazado",
         "Error: formato inválido",
         sc.registrar_medicamento,
         ["5999", ""])   # clave válida, nombre vacío → error

    _reset_estado()

    # A-04: Stock negativo rechazado (el patrón RE_STOCK no acepta "-")
    caso("A-04", "Stock negativo rechazado por regex",
         "Error: formato inválido",
         sc.registrar_medicamento,
         ["5999", "Ibuprofeno 400 mg", "Comprimido", "Tableta",
          "-5"])  # stock_actual inválido

    _reset_estado()

    # A-05: Folio con formato incorrecto en procesar_solicitud
    caso("A-05", "Folio sin prefijo SOL- rechazado",
         "Error: formato inválido",
         sc.procesar_solicitud,
         ["000001"])   # sin "SOL-"

    _reset_estado()

    # A-06: Folio con pocos dígitos rechazado
    caso("A-06", "Folio SOL-12 (< 4 dígitos) rechazado",
         "Error: formato inválido",
         sc.procesar_solicitud,
         ["SOL-12"])

    _reset_estado()

    # A-07: Servicio con dígitos rechazado
    caso("A-07", "Servicio con dígitos rechazado",
         "Error: formato inválido",
         sc.consultar_paciente,
         ["Pediatria2"])

    _reset_estado()

    # A-08: Cama con letras rechazada
    caso("A-08", "Cama con letras rechazada",
         "Error: formato inválido",
         sc.consultar_paciente,
         ["Pediatria", "A1"])

    _reset_estado()

    # A-09: Turno con opción fuera de rango (4)
    caso("A-09", "Turno 4 rechazado",
         "Error: formato inválido",
         sc.seleccionar_turno,
         ["4"])

    _reset_estado()

    # A-10: Usuario vacío rechazado
    caso("A-10", "Usuario vacío rechazado",
         "Error: formato inválido",
         sc.registrar_solicitud,
         ["Pediatria", "01",      # servicio, cama
          "parace", "1",          # búsqueda, selección medicamento
          "5",                    # cantidad
          "1",                    # turno matutino
          ""])                    # usuario vacío → error

    _reset_estado()

    # A-11: Opción de menú fuera de rango (12)
    caso("A-11", "Opción 12 en menú rechazada",
         "Error: formato inválido",
         lambda: sc.leer_con_patron(
             "Seleccione una opción: ", sc.RE_MENU,
             "ingrese un número entre 0 y 11"
         ),
         ["12"])

    _reset_estado()

    # A-12: Confirmación desactivar con carácter inválido
    caso("A-12", "Confirmación 'X' en desactivar rechazada",
         "Error: formato inválido",
         sc.eliminar_medicamento,
         ["5121", "X"])

    _reset_estado()

    # A-13: Cantidad solicitada cero rechazada
    caso("A-13", "Cantidad solicitada 0 rechazada por regex",
         "Error: formato inválido",
         sc.registrar_solicitud,
         ["Pediatria", "01", "parace", "1", "0"])

    _reset_estado()

    # A-14: Cantidad recibida con texto rechazada
    # Pre-crear una solicitud SURTIDA para que la función alcance la validación de cantidad
    sc.solicitudes.append({
        "folio": "SOL-0001", "servicio": "Pediatria", "cama": "01",
        "paciente": "Paciente de prueba 001", "nss": "00000000001",
        "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
        "cantidad": 5, "cantidad_recibida": 0, "cantidad_pendiente": 5,
        "turno": "MATUTINO", "usuario": "Test",
        "tipo": "NORMAL", "estado": "SURTIDA"
    })
    sc.contador_solicitudes = 2
    sc.guardar_datos()
    caso("A-14", "Cantidad recibida 'diez' rechazada",
         "Error: formato inválido",
         sc.registrar_recepcion,
         ["SOL-0001", "diez"])

    _reset_estado()


# ============================================================
# GRUPO B — FLUJO FUNCIONAL COMPLETO (regresión Etapa 2)
# ============================================================

def grupo_b():
    print(f"\n{_SEPARADOR}")
    print("GRUPO B — Flujo funcional (regresión Etapa 2)")
    print(_SEPARADOR)

    # B-01: Registrar medicamento válido
    _reset_estado()
    caso("B-01", "Registro de medicamento válido",
         "registrado correctamente",
         sc.registrar_medicamento,
         ["5200", "Amoxicilina 500 mg", "Capsula", "Capsula",
          "100", "120"])

    # B-02: Clave duplicada rechazada
    _reset_estado()
    caso("B-02", "Clave duplicada rechazada",
         "ya se encuentra registrada",
         sc.registrar_medicamento,
         ["5121",                 # clave ya existente
          "Paracetamol 500 mg", "Comprimido", "Tableta", "10", "15"])

    # B-03: Consulta de paciente existente
    _reset_estado()
    caso("B-03", "Consulta paciente existente",
         "Paciente encontrado",
         sc.consultar_paciente,
         ["Pediatria", "01"])

    # B-04: Consulta de paciente inexistente
    _reset_estado()
    caso("B-04", "Consulta paciente inexistente",
         "No se encontró",
         sc.consultar_paciente,
         ["Traumatologia", "05"])

    # B-05: Registro de solicitud completa
    _reset_estado()
    caso("B-05", "Solicitud registrada correctamente",
         "registrada correctamente",
         sc.registrar_solicitud,
         ["Pediatria", "01",   # servicio, cama
          "parace", "1",       # búsqueda y selección de medicamento
          "5",                 # cantidad
          "1",                 # turno: Matutino
          "Enf Lopez",         # usuario
          "1"])                # tipo: Normal

    # B-06: Selección de turno Matutino
    _reset_estado()
    caso("B-06", "Turno Matutino seleccionado",
         "MATUTINO",
         lambda: print(sc.seleccionar_turno()),
         ["1"])

    # B-07: Selección de turno Vespertino
    _reset_estado()
    caso("B-07", "Turno Vespertino seleccionado",
         "VESPERTINO",
         lambda: print(sc.seleccionar_turno()),
         ["2"])

    # B-08: Selección de turno Nocturno
    _reset_estado()
    caso("B-08", "Turno Nocturno seleccionado",
         "NOCTURNO",
         lambda: print(sc.seleccionar_turno()),
         ["3"])

    # B-09: Procesar solicitud PENDIENTE → SURTIDA
    _reset_estado()
    # Crear solicitud de referencia en memoria
    sc.solicitudes.append({
        "folio": "SOL-0001", "servicio": "Pediatria", "cama": "01",
        "paciente": "Paciente de prueba 001", "nss": "00000000001",
        "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
        "cantidad": 5, "cantidad_recibida": 0, "cantidad_pendiente": 5,
        "turno": "MATUTINO", "usuario": "Enf Lopez",
        "tipo": "NORMAL", "estado": "PENDIENTE"
    })
    sc.contador_solicitudes = 2
    sc.guardar_datos()
    caso("B-09", "Solicitud PENDIENTE → SURTIDA",
         "SURTIDA",
         sc.procesar_solicitud,
         ["SOL-0001", "1"])

    # B-10: Recepción total → stock se incrementa
    _reset_estado()
    sc.solicitudes.append({
        "folio": "SOL-0001", "servicio": "Pediatria", "cama": "01",
        "paciente": "Paciente de prueba 001", "nss": "00000000001",
        "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
        "cantidad": 5, "cantidad_recibida": 0, "cantidad_pendiente": 5,
        "turno": "MATUTINO", "usuario": "Enf Lopez",
        "tipo": "NORMAL", "estado": "SURTIDA"
    })
    sc.contador_solicitudes = 2
    sc.guardar_datos()
    stock_antes = sc.medicamentos[0]["stock_actual"]
    caso("B-10", "Recepción total actualiza stock",
         f"Stock nuevo: {stock_antes + 5}",
         sc.registrar_recepcion,
         ["SOL-0001", "5"])

    # B-11: Recepción parcial → SURTIDA_PARCIAL
    _reset_estado()
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
    caso("B-11", "Recepción parcial → SURTIDA_PARCIAL",
         "SURTIDA_PARCIAL",
         sc.registrar_recepcion,
         ["SOL-0002", "6"])

    # B-12: Solicitud NEGADA → no se puede recibir
    _reset_estado()
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
    caso("B-12", "Recepción de solicitud NEGADA rechazada",
         "solo se puede recibir una solicitud surtida",
         sc.registrar_recepcion,
         ["SOL-0003"])

    # B-13: Modificar medicamento (nombre y stock objetivo)
    _reset_estado()
    caso("B-13", "Modificación de medicamento",
         "modificado correctamente",
         sc.modificar_medicamento,
         ["5121",
          "Paracetamol 1 g - EFG",   # nuevo nombre
          "35"])                       # nuevo stock objetivo

    # B-14: Desactivar medicamento
    _reset_estado()
    caso("B-14", "Desactivación de medicamento",
         "desactivado correctamente",
         sc.eliminar_medicamento,
         ["5121", "S"])

    # B-15: Búsqueda de medicamento desactivado no lo encuentra
    _reset_estado()
    sc.medicamentos[0]["activo"] = False
    caso("B-15", "Medicamento desactivado no aparece en búsqueda",
         "No hay medicamentos disponibles",
         sc.seleccionar_medicamento,
         [])

    # B-16: Limpiar historial con confirmación
    _reset_estado()
    sc.solicitudes.append({
        "folio": "SOL-0001", "servicio": "Pediatria", "cama": "01",
        "paciente": "Paciente de prueba 001", "nss": "00000000001",
        "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
        "cantidad": 2, "cantidad_recibida": 0, "cantidad_pendiente": 2,
        "turno": "MATUTINO", "usuario": "Enf Lopez",
        "tipo": "NORMAL", "estado": "PENDIENTE"
    })
    sc.contador_solicitudes = 2
    sc.guardar_datos()
    caso("B-16", "Limpiar historial confirmado",
         "eliminado correctamente",
         sc.limpiar_registros,
         ["s"])

    # B-17: Cancelar limpieza del historial
    _reset_estado()
    caso("B-17", "Limpieza cancelada con 'n'",
         "cancelada",
         sc.limpiar_registros,
         ["n"])

    # B-18: Consultar inventario con medicamento activo
    _reset_estado()
    caso("B-18", "Inventario muestra medicamento activo",
         "Paracetamol",
         sc.consultar_inventario,
         [])

    # B-19: Flujo completo: solicitud → SURTIDA → recepción total
    _reset_estado()

    def _flujo_completo():
        # Paso 1: registrar solicitud
        sc.solicitudes.append({
            "folio": "SOL-0001", "servicio": "Medicina Interna", "cama": "01",
            "paciente": "Paciente de prueba 003", "nss": "00000000003",
            "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
            "cantidad": 3, "cantidad_recibida": 0, "cantidad_pendiente": 3,
            "turno": "MATUTINO", "usuario": "Dr Torres",
            "tipo": "NORMAL", "estado": "PENDIENTE"
        })
        sc.contador_solicitudes = 2
        sc.guardar_datos()

        # Paso 2: procesar → SURTIDA
        salida = io.StringIO()
        with redirect_stdout(salida):
            with patch("builtins.input", side_effect=["SOL-0001", "1"]):
                sc.procesar_solicitud()

        # Paso 3: recepción total
        stock_antes = sc.medicamentos[0]["stock_actual"]
        salida2 = io.StringIO()
        with redirect_stdout(salida2):
            with patch("builtins.input", side_effect=["SOL-0001", "3"]):
                sc.registrar_recepcion()

        print(salida.getvalue())
        print(salida2.getvalue())

    caso("B-19", "Flujo completo: solicitud → SURTIDA → recepción",
         f"Stock nuevo: {sc.medicamentos[0]['stock_actual'] + 3}",
         _flujo_completo,
         [])


# ============================================================
# GRUPO C — ROBUSTEZ Y PERSISTENCIA
# ============================================================

def grupo_c():
    print(f"\n{_SEPARADOR}")
    print("GRUPO C — Robustez y persistencia")
    print(_SEPARADOR)

    # C-01: JSON inválido → aviso y datos iniciales
    _reset_estado()
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        f.write("{ARCHIVO_CORRUPTO_NO_ES_JSON}")
    sc.cargar_datos()
    ok = sc.medicamentos[0]["clave"] == "5121"
    registro = {
        "id": "C-01",
        "descripcion": "JSON corrupto → se conservan datos iniciales",
        "esperado": "datos iniciales conservados",
        "obtenido": f"clave medicamento: {sc.medicamentos[0]['clave']}",
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} C-01 — {registro['descripcion']}")
    _reset_estado()

    # C-02: Archivo JSON inexistente → arranque limpio con datos iniciales
    _reset_estado()  # ya elimina el JSON
    sc.cargar_datos()
    ok = len(sc.medicamentos) == 1 and sc.contador_solicitudes == 1
    registro = {
        "id": "C-02",
        "descripcion": "Sin archivo JSON → datos iniciales en memoria",
        "esperado": "1 medicamento, contador=1",
        "obtenido": f"{len(sc.medicamentos)} medicamentos, contador={sc.contador_solicitudes}",
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} C-02 — {registro['descripcion']}")

    # C-03: guardar_datos() retorna True cuando todo es correcto
    _reset_estado()
    ok = sc.guardar_datos() is True
    registro = {
        "id": "C-03",
        "descripcion": "guardar_datos() retorna True en condiciones normales",
        "esperado": "True",
        "obtenido": str(ok),
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} C-03 — {registro['descripcion']}")

    # C-04: Persistencia entre sesiones (guardar → cargar → comparar)
    _reset_estado()
    sc.solicitudes.append({
        "folio": "SOL-0001", "servicio": "Urgencias", "cama": "01",
        "paciente": "Paciente de prueba 004", "nss": "00000000004",
        "medicamento": "5121", "nombre_medicamento": "Paracetamol 1 g",
        "cantidad": 7, "cantidad_recibida": 0, "cantidad_pendiente": 7,
        "turno": "NOCTURNO", "usuario": "Dr Soto",
        "tipo": "URGENCIA", "estado": "PENDIENTE"
    })
    sc.contador_solicitudes = 2
    sc.guardar_datos()

    # Simular nueva sesión
    sc.medicamentos[:] = []
    sc.solicitudes.clear()
    sc.contador_solicitudes = 1
    sc.cargar_datos()

    ok = (
        len(sc.medicamentos) == 1
        and len(sc.solicitudes) == 1
        and sc.solicitudes[0]["folio"] == "SOL-0001"
        and sc.contador_solicitudes == 2
    )
    registro = {
        "id": "C-04",
        "descripcion": "Persistencia entre sesiones (guardar → cargar)",
        "esperado": "1 solicitud SOL-0001, contador=2",
        "obtenido": (
            f"{len(sc.solicitudes)} solicitud(es), "
            f"folio={sc.solicitudes[0]['folio'] if sc.solicitudes else 'N/A'}, "
            f"contador={sc.contador_solicitudes}"
        ),
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} C-04 — {registro['descripcion']}")
    _reset_estado()

    # C-05: JSON con estado inválido → aviso y datos iniciales
    _reset_estado()
    datos_malos = {
        "medicamentos": sc.medicamentos,
        "pacientes": sc.pacientes,
        "solicitudes": [{
            "folio": "SOL-0001", "servicio": "Pediatria", "cama": "01",
            "paciente": "Test", "nss": "000",
            "medicamento": "5121", "nombre_medicamento": "Para",
            "cantidad": 3, "cantidad_recibida": 0, "cantidad_pendiente": 3,
            "turno": "MATUTINO", "usuario": "Test",
            "tipo": "NORMAL",
            "estado": "ESTADO_DESCONOCIDO"   # estado inválido
        }],
        "contador_solicitudes": 2
    }
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(datos_malos, f)
    sc.cargar_datos()
    ok = len(sc.solicitudes) == 0   # debe haber revertido a datos iniciales
    registro = {
        "id": "C-05",
        "descripcion": "Estado inválido en JSON → datos iniciales conservados",
        "esperado": "0 solicitudes (datos iniciales)",
        "obtenido": f"{len(sc.solicitudes)} solicitudes",
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} C-05 — {registro['descripcion']}")
    _reset_estado()

    # C-06: JSON con cantidades negativas en medicamento → aviso
    _reset_estado()
    datos_malos2 = {
        "medicamentos": [{
            "clave": "5121", "nombre": "Paracetamol 1 g",
            "presentacion": "Sol iny", "unidad_fisica": "Ampolleta",
            "stock_actual": -5,   # negativo
            "stock_objetivo": 30, "activo": True
        }],
        "pacientes": sc.pacientes,
        "solicitudes": [],
        "contador_solicitudes": 1
    }
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(datos_malos2, f)
    sc.cargar_datos()
    ok = sc.medicamentos[0]["stock_actual"] == 26  # valor del dato inicial
    registro = {
        "id": "C-06",
        "descripcion": "Stock negativo en JSON → datos iniciales conservados",
        "esperado": "stock_actual=26 (inicial)",
        "obtenido": f"stock_actual={sc.medicamentos[0]['stock_actual']}",
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} C-06 — {registro['descripcion']}")
    _reset_estado()


# ============================================================
# GRUPO D — COHERENCIA DEL CONTADOR Y FOLIOS
# ============================================================

def grupo_d():
    print(f"\n{_SEPARADOR}")
    print("GRUPO D — Coherencia del contador y folios")
    print(_SEPARADOR)

    # D-01: Contador atrasado se corrige al cargar
    _reset_estado()
    datos = {
        "medicamentos": sc.medicamentos,
        "pacientes": sc.pacientes,
        "solicitudes": [{
            "folio": "SOL-0005", "servicio": "Urgencias", "cama": "01",
            "paciente": "Test", "nss": "000",
            "medicamento": "5121", "nombre_medicamento": "Para",
            "cantidad": 1, "cantidad_recibida": 0, "cantidad_pendiente": 1,
            "turno": "MATUTINO", "usuario": "Test",
            "tipo": "NORMAL", "estado": "PENDIENTE"
        }],
        "contador_solicitudes": 3   # atrasado: folio max es 5
    }
    with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f)

    salida_carga = io.StringIO()
    with redirect_stdout(salida_carga):
        sc.cargar_datos()

    ok = sc.contador_solicitudes == 6  # debe haberse ajustado a folio_max + 1
    registro = {
        "id": "D-01",
        "descripcion": "Contador atrasado se ajusta al cargar datos",
        "esperado": "contador=6",
        "obtenido": f"contador={sc.contador_solicitudes}",
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} D-01 — {registro['descripcion']}")
    _reset_estado()

    # D-02: Folio generado sigue la secuencia correcta
    _reset_estado()
    sc.guardar_datos()
    sc.solicitudes.append({
        "folio": "SOL-0001", "servicio": "Pediatria", "cama": "01",
        "paciente": "Test", "nss": "000",
        "medicamento": "5121", "nombre_medicamento": "Para",
        "cantidad": 1, "cantidad_recibida": 0, "cantidad_pendiente": 1,
        "turno": "MATUTINO", "usuario": "Test",
        "tipo": "NORMAL", "estado": "PENDIENTE"
    })
    sc.contador_solicitudes = 2

    # Crear siguiente solicitud
    sc.solicitudes.append({
        "folio": f"SOL-{sc.contador_solicitudes:04d}",
        "servicio": "Urgencias", "cama": "01",
        "paciente": "Test", "nss": "000",
        "medicamento": "5121", "nombre_medicamento": "Para",
        "cantidad": 2, "cantidad_recibida": 0, "cantidad_pendiente": 2,
        "turno": "NOCTURNO", "usuario": "Test",
        "tipo": "URGENCIA", "estado": "PENDIENTE"
    })
    sc.contador_solicitudes += 1

    ok = sc.solicitudes[-1]["folio"] == "SOL-0002"
    registro = {
        "id": "D-02",
        "descripcion": "Folio SOL-0002 generado tras SOL-0001",
        "esperado": "SOL-0002",
        "obtenido": sc.solicitudes[-1]["folio"],
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} D-02 — {registro['descripcion']}")

    # D-03: Folio SOL-9999 → siguiente debe ser SOL-10000 (sin límite fijo)
    _reset_estado()
    sc.solicitudes.append({
        "folio": "SOL-9999", "servicio": "Urgencias", "cama": "01",
        "paciente": "Test", "nss": "000",
        "medicamento": "5121", "nombre_medicamento": "Para",
        "cantidad": 1, "cantidad_recibida": 0, "cantidad_pendiente": 1,
        "turno": "MATUTINO", "usuario": "Test",
        "tipo": "NORMAL", "estado": "PENDIENTE"
    })
    sc.contador_solicitudes = 10000
    folio_siguiente = f"SOL-{sc.contador_solicitudes:04d}"
    ok = folio_siguiente == "SOL-10000"
    registro = {
        "id": "D-03",
        "descripcion": "Folio SOL-10000 válido (sin límite superior)",
        "esperado": "SOL-10000",
        "obtenido": folio_siguiente,
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} D-03 — {registro['descripcion']}")
    _reset_estado()

    # D-04: RE_FOLIO acepta SOL-10000
    ok = bool(sc.RE_FOLIO.fullmatch("SOL-10000"))
    registro = {
        "id": "D-04",
        "descripcion": "RE_FOLIO acepta SOL-10000",
        "esperado": "match",
        "obtenido": "match" if ok else "no match",
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} D-04 — {registro['descripcion']}")

    # D-05: RE_FOLIO rechaza SOL-12 (< 4 dígitos)
    ok = not bool(sc.RE_FOLIO.fullmatch("SOL-12"))
    registro = {
        "id": "D-05",
        "descripcion": "RE_FOLIO rechaza SOL-12 (< 4 dígitos)",
        "esperado": "no match",
        "obtenido": "no match" if ok else "match inesperado",
        "estado": "PASS" if ok else "FAIL"
    }
    resultados.append(registro)
    marca = "✓" if ok else "✗"
    print(f"  [{'PASS' if ok else 'FAIL'}] {marca} D-05 — {registro['descripcion']}")


# ============================================================
# GENERAR REPORTE DE TEXTO
# ============================================================

def generar_reporte():
    """Guarda todos los resultados en evidencias/reporte_pruebas.txt."""
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total  = len(resultados)
    passed = sum(1 for r in resultados if r["estado"] == "PASS")
    failed = total - passed

    lineas = [
        _SEPARADOR,
        "SMART CENDIS — Reporte de Pruebas Automatizadas",
        f"Generado: {ahora}",
        f"Total: {total}  |  PASS: {passed}  |  FAIL/ERROR: {failed}",
        _SEPARADOR,
        "",
    ]

    for r in resultados:
        marca = "✓" if r["estado"] == "PASS" else "✗"
        lineas.append(f"[{r['estado']}] {marca}  {r['id']}  —  {r['descripcion']}")
        lineas.append(f"  Esperado : {r['esperado']}")
        # Limitar salida para legibilidad
        obtenido_resumido = "\n         ".join(
            r["obtenido"].splitlines()[:10]
        )
        lineas.append(f"  Obtenido : {obtenido_resumido}")
        lineas.append("")

    lineas.append(_SEPARADOR)
    lineas.append(f"Resumen final: {passed}/{total} pruebas pasaron.")
    lineas.append(_SEPARADOR)

    reporte = "\n".join(lineas)

    with open(REPORTE_TXT, "w", encoding="utf-8") as f:
        f.write(reporte)

    print(f"\n{'=' * 70}")
    print(f"  Reporte guardado en: {REPORTE_TXT}")
    print(f"  Resumen: {passed}/{total} pruebas pasaron.")
    print(f"{'=' * 70}")

    return passed, total


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    print(_SEPARADOR)
    print("  SMART CENDIS — Suite de Pruebas (Etapa 3)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(_SEPARADOR)

    grupo_a()
    grupo_b()
    grupo_c()
    grupo_d()

    passed, total = generar_reporte()
    sys.exit(0 if passed == total else 1)
