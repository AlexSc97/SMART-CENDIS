"""
Pruebas Unitarias Automatizadas para SMART CENDIS
=================================================
Valida la lógica de negocio de los módulos de Medicamentos, Pacientes,
Solicitudes, Dictamen de Farmacia, Recepción Física y Persistencia Atómica.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import smart_cendis


class TestSmartCendis(unittest.TestCase):

    def setUp(self):
        """Prepara un entorno aislado con archivo temporal y datos iniciales limpios."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()

        smart_cendis.ARCHIVO_DATOS = self.temp_file.name
        smart_cendis.medicamentos = [
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
        smart_cendis.pacientes = [
            {
                "servicio": "Pediatria",
                "cama": "01",
                "nombre": "Paciente de prueba 001",
                "nss": "00000000001"
            },
            {
                "servicio": "Urgencias",
                "cama": "01",
                "nombre": "Paciente de prueba 004",
                "nss": "00000000004"
            }
        ]
        smart_cendis.solicitudes = []
        smart_cendis.contador_solicitudes = 1

    def tearDown(self):
        """Limpia los archivos temporales generados durante las pruebas."""
        for path in [self.temp_file.name, f"{self.temp_file.name}.tmp"]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    # ------------------------------------------------------------
    # PRUEBAS DEL MÓDULO 1: MEDICAMENTOS
    # ------------------------------------------------------------

    def test_buscar_medicamento_existente(self):
        """Debe retornar el diccionario del medicamento si existe y está activo."""
        med = smart_cendis.buscar_medicamento("5121")
        self.assertIsNotNone(med)
        self.assertEqual(med["nombre"], "Paracetamol 1 g")

    def test_buscar_medicamento_inexistente(self):
        """Debe retornar None si la clave no existe."""
        med = smart_cendis.buscar_medicamento("9999")
        self.assertIsNone(med)

    @patch("builtins.input", side_effect=["0104", "Ibuprofeno 400 mg", "Tabletas", "Caja", "50", "100"])
    def test_registrar_medicamento_exitoso(self, mock_input):
        """Debe registrar un nuevo medicamento y agregarlo al catálogo."""
        nuevo = smart_cendis.registrar_medicamento()
        self.assertIsNotNone(nuevo)
        self.assertEqual(nuevo["clave"], "0104")
        self.assertEqual(smart_cendis.buscar_medicamento("0104")["nombre"], "Ibuprofeno 400 mg")

    @patch("builtins.input", side_effect=["5121"])
    def test_registrar_medicamento_clave_duplicada(self, mock_input):
        """No debe permitir registrar un medicamento con una clave que ya existe."""
        resultado = smart_cendis.registrar_medicamento()
        self.assertIsNone(resultado)

    @patch("builtins.input", side_effect=["5121", "Paracetamol 1 g Solucion", "35"])
    def test_modificar_medicamento_exitoso(self, mock_input):
        """Debe modificar el nombre y stock objetivo del medicamento indicado."""
        exito = smart_cendis.modificar_medicamento()
        self.assertTrue(exito)
        med = smart_cendis.buscar_medicamento("5121")
        self.assertEqual(med["nombre"], "Paracetamol 1 g Solucion")
        self.assertEqual(med["stock_objetivo"], 35)

    @patch("builtins.input", side_effect=["5121", "S"])
    def test_eliminar_medicamento_logico(self, mock_input):
        """Debe desactivar lógicamente el medicamento (activo = False)."""
        exito = smart_cendis.eliminar_medicamento()
        self.assertTrue(exito)
        self.assertIsNone(smart_cendis.buscar_medicamento("5121"))
        # El registro aún existe en memoria pero con activo=False
        registro_inactivo = [m for m in smart_cendis.medicamentos if m["clave"] == "5121"][0]
        self.assertFalse(registro_inactivo["activo"])

    # ------------------------------------------------------------
    # PRUEBAS DEL MÓDULO 2: PACIENTES
    # ------------------------------------------------------------

    def test_buscar_paciente_existente(self):
        """Debe localizar al paciente por servicio (case-insensitive) y cama."""
        paciente = smart_cendis.buscar_paciente("pediatria", "01")
        self.assertIsNotNone(paciente)
        self.assertEqual(paciente["nombre"], "Paciente de prueba 001")

    def test_buscar_paciente_inexistente(self):
        """Debe retornar None si la combinación de servicio y cama no existe."""
        paciente = smart_cendis.buscar_paciente("Cirugia", "99")
        self.assertIsNone(paciente)

    # ------------------------------------------------------------
    # PRUEBAS DEL MÓDULO 3: SOLICITUDES
    # ------------------------------------------------------------

    @patch("builtins.input", side_effect=["Pediatria", "01", "Paracetamol", "1", "5", "1", "Enf. Gonzalez", "1"])
    def test_registrar_solicitud_exitosa(self, mock_input):
        """Debe registrar una solicitud con folio consecutivo, estado PENDIENTE y cantidades calculadas."""
        sol = smart_cendis.registrar_solicitud()
        self.assertIsNotNone(sol)
        self.assertEqual(sol["folio"], "SOL-0001")
        self.assertEqual(sol["estado"], "PENDIENTE")
        self.assertEqual(sol["cantidad"], 5)
        self.assertEqual(sol["cantidad_pendiente"], 5)
        self.assertEqual(sol["cantidad_recibida"], 0)
        self.assertEqual(sol["tipo"], "NORMAL")
        self.assertEqual(smart_cendis.contador_solicitudes, 2)

    # ------------------------------------------------------------
    # PRUEBAS DEL MÓDULO 4: PROCESAMIENTO Y RECEPCIÓN FÍSICA
    # ------------------------------------------------------------

    @patch("builtins.input", side_effect=["1"])  # 1 = Surtida
    def test_procesar_solicitud_surtida_farmacia(self, mock_input):
        """Farmacia marca la solicitud como SURTIDA lista para entrega."""
        smart_cendis.solicitudes.append({
            "folio": "SOL-0001",
            "servicio": "Pediatria",
            "cama": "01",
            "paciente": "Paciente de prueba 001",
            "nss": "00000000001",
            "medicamento": "5121",
            "nombre_medicamento": "Paracetamol 1 g",
            "cantidad": 10,
            "cantidad_recibida": 0,
            "cantidad_pendiente": 10,
            "turno": "MATUTINO",
            "usuario": "Enfermeria",
            "tipo": "NORMAL",
            "estado": "PENDIENTE"
        })

        sol = smart_cendis.procesar_solicitud("SOL-0001")
        self.assertIsNotNone(sol)
        self.assertEqual(sol["estado"], "SURTIDA")

    @patch("builtins.input", side_effect=["7"])  # Recibe 7 de 10
    def test_registrar_recepcion_parcial(self, mock_input):
        """Recepción física menor a lo solicitado resulta en SURTIDA_PARCIAL e incrementa el stock."""
        smart_cendis.solicitudes.append({
            "folio": "SOL-0001",
            "servicio": "Pediatria",
            "cama": "01",
            "paciente": "Paciente de prueba 001",
            "nss": "00000000001",
            "medicamento": "5121",
            "nombre_medicamento": "Paracetamol 1 g",
            "cantidad": 10,
            "cantidad_recibida": 0,
            "cantidad_pendiente": 10,
            "turno": "MATUTINO",
            "usuario": "Enfermeria",
            "tipo": "NORMAL",
            "estado": "SURTIDA"
        })

        stock_inicial = smart_cendis.buscar_medicamento("5121")["stock_actual"]
        sol = smart_cendis.registrar_recepcion("SOL-0001")

        self.assertIsNotNone(sol)
        self.assertEqual(sol["estado"], "SURTIDA_PARCIAL")
        self.assertEqual(sol["cantidad_recibida"], 7)
        self.assertEqual(sol["cantidad_pendiente"], 3)
        self.assertEqual(
            smart_cendis.buscar_medicamento("5121")["stock_actual"],
            stock_inicial + 7
        )

    # ------------------------------------------------------------
    # PRUEBAS DEL MÓDULO 5: PERSISTENCIA ATÓMICA
    # ------------------------------------------------------------

    def test_guardar_y_cargar_datos(self):
        """Verifica que el estado se serialice en JSON y se pueda reconstruir fielmente."""
        smart_cendis.solicitudes = [{
            "folio": "SOL-0001",
            "servicio": "Pediatria",
            "cama": "01",
            "paciente": "Paciente de prueba 001",
            "nss": "00000000001",
            "medicamento": "5121",
            "nombre_medicamento": "Paracetamol 1 g",
            "cantidad": 4,
            "cantidad_recibida": 4,
            "cantidad_pendiente": 0,
            "turno": "MATUTINO",
            "usuario": "Enf. Test",
            "tipo": "NORMAL",
            "estado": "SURTIDA"
        }]
        smart_cendis.contador_solicitudes = 2

        guardado = smart_cendis.guardar_datos()
        self.assertTrue(guardado)

        # Modificar variables en memoria para asegurar que se recargan del archivo
        smart_cendis.solicitudes = []
        smart_cendis.contador_solicitudes = 1

        smart_cendis.cargar_datos()
        self.assertEqual(len(smart_cendis.solicitudes), 1)
        self.assertEqual(smart_cendis.solicitudes[0]["folio"], "SOL-0001")
        self.assertEqual(smart_cendis.contador_solicitudes, 2)


if __name__ == "__main__":
    unittest.main()
