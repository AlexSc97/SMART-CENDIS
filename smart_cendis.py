# ============================================================
# SMART CENDIS
# Sistema de Gestión Digital de Solicitudes,
# Abastecimiento y Control de Inventario Hospitalario
# ============================================================

import json
import os
from typing import Any, Dict, List, Optional


# ============================================================
# 1. CONFIGURACIÓN, PERSISTENCIA Y DATOS INICIALES
# ============================================================

# Archivo local de persistencia, ubicado junto al script.
ARCHIVO_DATOS: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "smart_cendis.json"
)

# Catálogo inicial de medicamentos
medicamentos: List[Dict[str, Any]] = [
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

# Censo inicial de pacientes de prueba
pacientes: List[Dict[str, str]] = [
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

# Lista histórica de solicitudes y contador de folios
solicitudes: List[Dict[str, Any]] = []
contador_solicitudes: int = 1


def cargar_datos() -> None:
    """
    Carga el estado guardado desde el archivo JSON de persistencia.
    Si el archivo no existe o contiene un formato inválido, conserva los datos iniciales.
    """
    global medicamentos, pacientes, solicitudes, contador_solicitudes

    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, dict):
            raise ValueError("la raíz del archivo debe ser un objeto JSON")

        medicamentos_guardados = datos.get("medicamentos")
        pacientes_guardados = datos.get("pacientes")
        solicitudes_guardadas = datos.get("solicitudes")
        contador_guardado = datos.get("contador_solicitudes")

        if not all(isinstance(v, list) for v in (
            medicamentos_guardados,
            pacientes_guardados,
            solicitudes_guardadas
        )):
            raise ValueError("medicamentos, pacientes y solicitudes deben ser listas")

        def registros_validos(
            registros: list,
            campos_texto: tuple,
            campos_entero: tuple = (),
            campo_booleano: Optional[str] = None
        ) -> bool:
            for registro in registros:
                if not isinstance(registro, dict):
                    return False
                if any(campo not in registro for campo in campos_texto):
                    return False
                if any(not isinstance(registro[campo], str) for campo in campos_texto):
                    return False
                if any(
                    campo not in registro
                    or not isinstance(registro[campo], int)
                    or isinstance(registro[campo], bool)
                    for campo in campos_entero
                ):
                    return False
                if (
                    campo_booleano is not None
                    and (campo_booleano not in registro
                         or not isinstance(registro[campo_booleano], bool))
                ):
                    return False
            return True

        if not registros_validos(
            medicamentos_guardados,
            ("clave", "nombre", "presentacion", "unidad_fisica"),
            ("stock_actual", "stock_objetivo"),
            "activo"
        ):
            raise ValueError("el catálogo de medicamentos tiene registros inválidos")

        if not registros_validos(
            pacientes_guardados,
            ("servicio", "cama", "nombre", "nss")
        ):
            raise ValueError("el catálogo de pacientes tiene registros inválidos")

        if not registros_validos(
            solicitudes_guardadas,
            ("folio", "servicio", "cama", "paciente", "nss", "medicamento",
             "nombre_medicamento", "turno", "usuario", "tipo", "estado"),
            ("cantidad", "cantidad_recibida", "cantidad_pendiente")
        ):
            raise ValueError("el historial de solicitudes tiene registros inválidos")

        if (
            not isinstance(contador_guardado, int)
            or isinstance(contador_guardado, bool)
            or contador_guardado < 1
        ):
            raise ValueError("contador_solicitudes debe ser un entero positivo")

        medicamentos = medicamentos_guardados
        pacientes = pacientes_guardados
        solicitudes = solicitudes_guardadas
        contador_solicitudes = contador_guardado

    except FileNotFoundError:
        # Primer arranque: se usan los datos iniciales predeterminados.
        return
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as error:
        print(
            f"Aviso: no se pudieron cargar los datos guardados ({error}). "
            "Se conservarán los datos iniciales."
        )


def guardar_datos() -> bool:
    """
    Guarda el estado actual del sistema de forma atómica en smart_cendis.json.
    Retorna True si la operación fue exitosa, False en caso de error.
    """
    archivo_temporal = f"{ARCHIVO_DATOS}.tmp"
    datos = {
        "medicamentos": medicamentos,
        "pacientes": pacientes,
        "solicitudes": solicitudes,
        "contador_solicitudes": contador_solicitudes
    }

    try:
        with open(archivo_temporal, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=4)
            archivo.write("\n")
        os.replace(archivo_temporal, ARCHIVO_DATOS)
        return True
    except (OSError, TypeError, ValueError) as error:
        print(f"Aviso: no se pudieron guardar los datos ({error}).")
        try:
            if os.path.exists(archivo_temporal):
                os.remove(archivo_temporal)
        except OSError:
            pass
        return False


# ============================================================
# 2. MÓDULO DE MEDICAMENTOS (CATÁLOGO E INVENTARIO)
# ============================================================

def buscar_medicamento(clave: str) -> Optional[Dict[str, Any]]:
    """
    Busca un medicamento activo mediante su clave institucional.
    Retorna el diccionario del medicamento o None si no existe o está inactivo.
    """
    for medicamento in medicamentos:
        if medicamento["clave"] == clave and medicamento["activo"]:
            return medicamento
    return None


def registrar_medicamento() -> Optional[Dict[str, Any]]:
    """Registra un nuevo medicamento en el catálogo."""
    print("\n========== REGISTRAR MEDICAMENTO ==========")
    clave = input("Ingrese la clave del medicamento: ").strip()

    if not clave:
        print("Error: la clave no puede estar vacía.")
        return None

    # Verificar que la clave no exista previamente
    for med in medicamentos:
        if med["clave"] == clave:
            print("Error: la clave ya se encuentra registrada.")
            return None

    nombre = input("Ingrese el nombre del medicamento: ").strip()
    if not nombre:
        print("Error: el nombre no puede estar vacío.")
        return None

    presentacion = input("Ingrese la presentación: ").strip()
    unidad_fisica = input("Ingrese la unidad física: ").strip()

    try:
        stock_actual = int(input("Ingrese el stock actual: "))
        stock_objetivo = int(input("Ingrese el stock objetivo: "))
    except ValueError:
        print("Error: el stock debe ser un número entero.")
        return None

    if stock_actual < 0 or stock_objetivo < 0:
        print("Error: las cantidades no pueden ser negativas.")
        return None

    nuevo_medicamento = {
        "clave": clave,
        "nombre": nombre,
        "presentacion": presentacion,
        "unidad_fisica": unidad_fisica,
        "stock_actual": stock_actual,
        "stock_objetivo": stock_objetivo,
        "activo": True
    }

    medicamentos.append(nuevo_medicamento)
    guardar_datos()
    print("Medicamento registrado correctamente.")
    return nuevo_medicamento


def consultar_medicamentos() -> None:
    """Muestra todos los medicamentos activos registrados en el catálogo."""
    print("\n========== CATÁLOGO DE MEDICAMENTOS ==========")
    encontrados = False

    for medicamento in medicamentos:
        if medicamento["activo"]:
            encontrados = True
            print(f"Clave:          {medicamento['clave']}")
            print(f"Nombre:         {medicamento['nombre']}")
            print(f"Presentación:   {medicamento['presentacion']}")
            print(f"Unidad física:  {medicamento['unidad_fisica']}")
            print(f"Stock actual:   {medicamento['stock_actual']}")
            print(f"Stock objetivo: {medicamento['stock_objetivo']}")
            print("-" * 45)

    if not encontrados:
        print("No existen medicamentos activos registrados.")


def modificar_medicamento() -> bool:
    """Permite modificar el nombre y stock objetivo de un medicamento activo."""
    print("\n========== MODIFICAR MEDICAMENTO ==========")
    clave = input("Ingrese la clave del medicamento a modificar: ").strip()

    medicamento = buscar_medicamento(clave)
    if medicamento is None:
        print("Error: medicamento no encontrado o inactivo.")
        return False

    print("\nMedicamento encontrado:")
    print(f"Nombre actual:         {medicamento['nombre']}")
    print(f"Stock objetivo actual: {medicamento['stock_objetivo']}")

    nuevo_nombre = input("Nuevo nombre (Enter para conservar): ").strip()
    if nuevo_nombre != "":
        medicamento["nombre"] = nuevo_nombre

    nuevo_stock_input = input("Nuevo stock objetivo (Enter para conservar): ").strip()
    if nuevo_stock_input != "":
        try:
            nuevo_stock_objetivo = int(nuevo_stock_input)
            if nuevo_stock_objetivo < 0:
                print("Error: el stock objetivo no puede ser negativo.")
                return False
            medicamento["stock_objetivo"] = nuevo_stock_objetivo
        except ValueError:
            print("Error: el stock objetivo debe ser un número entero.")
            return False

    guardar_datos()
    print("Medicamento modificado correctamente.")
    return True


def eliminar_medicamento() -> bool:
    """
    Desactiva un medicamento de forma lógica (activo = False)
    sin destruir el registro histórico del catálogo.
    """
    print("\n========== DESACTIVAR MEDICAMENTO ==========")
    clave = input("Ingrese la clave del medicamento a desactivar: ").strip()

    medicamento = buscar_medicamento(clave)
    if medicamento is None:
        print("Error: medicamento no encontrado o ya inactivo.")
        return False

    confirmacion = input(
        f"¿Desea desactivar '{medicamento['nombre']}'? (S/N): "
    ).strip().upper()

    if confirmacion == "S":
        medicamento["activo"] = False
        guardar_datos()
        print("Medicamento desactivado correctamente.")
        return True
    else:
        print("Operación cancelada.")
        return False


# ============================================================
# 3. MÓDULO DE PACIENTES
# ============================================================

def buscar_paciente(servicio: str, cama: str) -> Optional[Dict[str, str]]:
    """Busca un paciente mediante el nombre del servicio y número de cama."""
    for paciente in pacientes:
        if (
            paciente["servicio"].strip().lower() == servicio.strip().lower()
            and paciente["cama"].strip() == cama.strip()
        ):
            return paciente
    return None


def consultar_paciente() -> Optional[Dict[str, str]]:
    """Solicita servicio y cama, mostrando los datos del paciente si existe."""
    print("\n========== CONSULTAR PACIENTE ==========")
    servicio = input("Ingrese el servicio: ").strip()
    cama = input("Ingrese la cama: ").strip()

    paciente = buscar_paciente(servicio, cama)
    if paciente:
        print("\nPaciente encontrado:")
        print(f"Servicio: {paciente['servicio']}")
        print(f"Cama:     {paciente['cama']}")
        print(f"Nombre:   {paciente['nombre']}")
        print(f"NSS:      {paciente['nss']}")
        return paciente
    else:
        print("\nNo se encontró un paciente para el servicio y cama indicados.")
        return None


# ============================================================
# 4. MÓDULO DE SOLICITUDES DE MEDICAMENTOS
# ============================================================

def seleccionar_turno() -> Optional[str]:
    """Permite seleccionar manualmente el turno de trabajo hospitalario."""
    print("\nSeleccione el turno:")
    print("1. Matutino")
    print("2. Vespertino")
    print("3. Nocturno")

    opcion = input("Seleccione una opción: ").strip()
    if opcion == "1":
        return "MATUTINO"
    elif opcion == "2":
        return "VESPERTINO"
    elif opcion == "3":
        return "NOCTURNO"
    else:
        print("Error: opción de turno no válida.")
        return None


def seleccionar_medicamento() -> Optional[Dict[str, Any]]:
    """
    Permite buscar un medicamento activo por coincidencia de nombre.
    Facilita que el personal solicite medicamentos sin memorizar claves numéricas.
    """
    medicamentos_activos = [m for m in medicamentos if m["activo"]]
    if not medicamentos_activos:
        print("No hay medicamentos disponibles en el catálogo.")
        return None

    busqueda = input("\nIngrese el nombre o parte del medicamento: ").strip().lower()
    if not busqueda:
        print("Error: debe ingresar un término de búsqueda.")
        return None

    resultados = [
        m for m in medicamentos_activos
        if busqueda in m["nombre"].lower()
    ]

    if not resultados:
        print("No se encontraron medicamentos activos con ese nombre.")
        return None

    print("\n========== MEDICAMENTOS ENCONTRADOS ==========")
    for i, med in enumerate(resultados, start=1):
        print(f"{i}. {med['nombre']} ({med['presentacion']}) - Stock: {med['stock_actual']}")

    try:
        opcion = int(input("Seleccione una opción: "))
        if opcion < 1 or opcion > len(resultados):
            print("Error: opción fuera de rango.")
            return None
        return resultados[opcion - 1]
    except ValueError:
        print("Error: debe ingresar un número válido.")
        return None


def registrar_solicitud() -> Optional[Dict[str, Any]]:
    """
    Registra una nueva solicitud de medicamento para un paciente y cama.
    Genera un folio consecutivo único (ej. SOL-0001) y almacena el registro.
    """
    global contador_solicitudes

    print("\n========== NUEVA SOLICITUD DE MEDICAMENTO ==========")
    servicio = input("Ingrese el servicio: ").strip()
    cama = input("Ingrese la cama: ").strip()

    paciente = buscar_paciente(servicio, cama)
    if paciente is None:
        print("Error: no se encontró un paciente para el servicio y cama indicados.")
        return None

    print(f"\nPaciente asignado: {paciente['nombre']}")
    print(f"NSS:               {paciente['nss']}")

    medicamento = seleccionar_medicamento()
    if medicamento is None:
        return None

    print(f"\nMedicamento seleccionado: {medicamento['nombre']}")
    print(f"Clave institucional:      {medicamento['clave']}")
    print(f"Stock actual en piso:     {medicamento['stock_actual']}")

    try:
        cantidad = int(input("Ingrese la cantidad solicitada: "))
    except ValueError:
        print("Error: la cantidad debe ser un número entero.")
        return None

    if cantidad <= 0:
        print("Error: la cantidad solicitada debe ser mayor a cero.")
        return None

    turno = seleccionar_turno()
    if turno is None:
        return None

    usuario = input("Ingrese el usuario/personal responsable: ").strip()
    if not usuario:
        print("Error: debe ingresar el usuario responsable.")
        return None

    print("\nTipo de solicitud:")
    print("1. Normal")
    print("2. Urgencia")
    tipo_opcion = input("Seleccione una opción: ").strip()
    if tipo_opcion == "1":
        tipo = "NORMAL"
    elif tipo_opcion == "2":
        tipo = "URGENCIA"
    else:
        print("Error: tipo de solicitud no válido.")
        return None

    folio = f"SOL-{contador_solicitudes:04d}"
    nueva_solicitud = {
        "folio": folio,
        "servicio": paciente["servicio"],
        "cama": paciente["cama"],
        "paciente": paciente["nombre"],
        "nss": paciente["nss"],
        "medicamento": medicamento["clave"],
        "nombre_medicamento": medicamento["nombre"],
        "cantidad": cantidad,
        "cantidad_recibida": 0,
        "cantidad_pendiente": cantidad,
        "turno": turno,
        "usuario": usuario,
        "tipo": tipo,
        "estado": "PENDIENTE"
    }

    solicitudes.append(nueva_solicitud)
    contador_solicitudes += 1
    guardar_datos()

    print(f"\nSolicitud registrada correctamente.")
    print(f"Folio generado: {folio}")
    return nueva_solicitud


# ============================================================
# 5. MÓDULO DE PROCESAMIENTO Y RECEPCIÓN FÍSICA
# ============================================================

def buscar_solicitud(folio: str) -> Optional[Dict[str, Any]]:
    """Busca una solicitud mediante su folio único institucional."""
    folio_normalizado = folio.strip().upper()
    for solicitud in solicitudes:
        if solicitud["folio"].upper() == folio_normalizado:
            return solicitud
    return None


def mostrar_solicitud(solicitud: Dict[str, Any]) -> None:
    """Imprime el detalle de una solicitud en pantalla."""
    print("\n========== DETALLE DE SOLICITUD ==========")
    print(f"Folio:               {solicitud['folio']}")
    print(f"Servicio:            {solicitud['servicio']}")
    print(f"Cama:                {solicitud['cama']}")
    print(f"Paciente:            {solicitud['paciente']}")
    print(f"NSS:                 {solicitud['nss']}")
    print(f"Clave Medicamento:   {solicitud['medicamento']}")
    print(f"Medicamento:         {solicitud['nombre_medicamento']}")
    print(f"Cantidad Solicitada: {solicitud['cantidad']}")
    print(f"Cantidad Recibida:   {solicitud.get('cantidad_recibida', 0)}")
    print(f"Cantidad Pendiente:  {solicitud.get('cantidad_pendiente', solicitud['cantidad'])}")
    print(f"Turno:               {solicitud['turno']}")
    print(f"Usuario:             {solicitud['usuario']}")
    print(f"Tipo:                {solicitud['tipo']}")
    print(f"Estado:              {solicitud['estado']}")


def procesar_solicitud(folio: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Registra el dictamen o respuesta emitida por la farmacia central (SURTIDA o NEGADA).
    Solo las solicitudes en estado PENDIENTE pueden ser procesadas.
    """
    print("\n========== PROCESAR SOLICITUD EN FARMACIA ==========")
    if folio is None:
        folio = input("Ingrese el folio de la solicitud: ").strip()

    solicitud = buscar_solicitud(folio)
    if solicitud is None:
        print("Error: solicitud no encontrada.")
        return None

    mostrar_solicitud(solicitud)
    if solicitud["estado"] != "PENDIENTE":
        print(f"\nError: la solicitud no está pendiente (estado actual: {solicitud['estado']}).")
        return None

    print("\nDictamen de Farmacia Central:")
    print("1. Surtida (disponible para entrega)")
    print("2. Negada (sin existencia en farmacia)")
    opcion = input("Seleccione una opción: ").strip()

    if opcion == "1":
        solicitud["estado"] = "SURTIDA"
        print("\nSolicitud marcada como SURTIDA. Proceda a registrar la recepción física.")
    elif opcion == "2":
        solicitud["estado"] = "NEGADA"
        solicitud["cantidad_recibida"] = 0
        solicitud["cantidad_pendiente"] = solicitud["cantidad"]
        print("\nSolicitud marcada como NEGADA. No procede recepción física.")
    else:
        print("\nError: opción no válida.")
        return None

    guardar_datos()
    print(f"Folio {solicitud['folio']} actualizado correctamente.")
    return solicitud


def registrar_recepcion(folio: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Registra la recepción física del medicamento en el servicio/piso.
    Actualiza la cantidad recibida, pendiente, estado final e incrementa el stock disponible.
    """
    print("\n========== REGISTRAR RECEPCIÓN FÍSICA ==========")
    if folio is None:
        folio = input("Ingrese el folio de la solicitud: ").strip()

    solicitud = buscar_solicitud(folio)
    if solicitud is None:
        print("Error: solicitud no encontrada.")
        return None

    mostrar_solicitud(solicitud)
    if solicitud["estado"] != "SURTIDA":
        print(
            f"Error: solo se puede registrar recepción física de solicitudes SURTIDAS por farmacia "
            f"(estado actual: {solicitud['estado']})."
        )
        return None

    medicamento = buscar_medicamento(solicitud["medicamento"])
    if medicamento is None:
        print("Error: el medicamento de la solicitud no existe o está inactivo en el catálogo.")
        return None

    print("\n--- Control de Inventario ---")
    print(f"Medicamento:  {medicamento['nombre']}")
    print(f"Stock actual: {medicamento['stock_actual']}")

    while True:
        try:
            cantidad_recibida = int(input("Ingrese la cantidad recibida físicamente: "))
        except ValueError:
            print("Error: ingrese un número entero.")
            continue

        if not (0 <= cantidad_recibida <= solicitud["cantidad"]):
            print(f"Error: la cantidad recibida debe ser entre 0 y {solicitud['cantidad']}.")
            continue
        break

    stock_anterior = medicamento["stock_actual"]
    cantidad_pendiente = solicitud["cantidad"] - cantidad_recibida

    if cantidad_recibida == 0:
        estado_final = "NEGADA"
    elif cantidad_pendiente > 0:
        estado_final = "SURTIDA_PARCIAL"
    else:
        estado_final = "SURTIDA"

    # Actualizar stock físico del piso e información de la solicitud
    medicamento["stock_actual"] += cantidad_recibida
    solicitud["cantidad_recibida"] = cantidad_recibida
    solicitud["cantidad_pendiente"] = cantidad_pendiente
    solicitud["estado"] = estado_final

    guardar_datos()

    print("\n========== RECEPCIÓN REGISTRADA EXITOSAMENTE ==========")
    print(f"Folio:               {solicitud['folio']}")
    print(f"Medicamento:         {medicamento['nombre']}")
    print(f"Cantidad solicitada: {solicitud['cantidad']}")
    print(f"Cantidad recibida:   {cantidad_recibida}")
    print(f"Cantidad pendiente:  {cantidad_pendiente}")
    print(f"Estado final:        {estado_final}")
    print(f"Stock anterior:      {stock_anterior}")
    print(f"Nuevo stock en piso: {medicamento['stock_actual']}")

    return solicitud


# ============================================================
# 6. MÓDULO DE CONSULTAS Y REPORTES
# ============================================================

def consultar_solicitudes() -> None:
    """Muestra el reporte histórico de todas las solicitudes registradas."""
    print("\n========== HISTORIAL DE SOLICITUDES ==========")

    if not solicitudes:
        print("No existen solicitudes registradas en el sistema.")
        return

    for sol in solicitudes:
        print("-" * 50)
        print(f"Folio:               {sol['folio']}")
        print(f"Servicio / Cama:     {sol['servicio']} - Cama {sol['cama']}")
        print(f"Paciente:            {sol['paciente']} (NSS: {sol['nss']})")
        print(f"Medicamento:         {sol['nombre_medicamento']} [Clave {sol['medicamento']}]")
        print(f"Cantidad Solicitada: {sol['cantidad']}")
        print(f"Cantidad Recibida:   {sol.get('cantidad_recibida', 0)}")
        print(f"Cantidad Pendiente:  {sol.get('cantidad_pendiente', sol['cantidad'])}")
        print(f"Turno / Usuario:     {sol['turno']} / {sol['usuario']}")
        print(f"Tipo / Estado:       {sol['tipo']} | {sol['estado']}")

    print("-" * 50)


def consultar_inventario() -> None:
    """
    Muestra el inventario actual de medicamentos activos,
    calculando faltantes respecto al stock objetivo.
    """
    print("\n========== INVENTARIO ACTUAL DE MEDICAMENTOS ==========")

    medicamentos_activos = [m for m in medicamentos if m["activo"]]
    if not medicamentos_activos:
        print("No existen medicamentos activos en el inventario.")
        return

    for med in medicamentos_activos:
        print("-" * 50)
        print(f"Clave:          {med['clave']}")
        print(f"Medicamento:    {med['nombre']}")
        print(f"Presentación:   {med['presentacion']} ({med['unidad_fisica']})")
        print(f"Stock Actual:   {med['stock_actual']}")
        print(f"Stock Objetivo: {med['stock_objetivo']}")

        faltante = med["stock_objetivo"] - med["stock_actual"]
        if faltante > 0:
            print(f"Status:         Faltante de {faltante} unidades para stock objetivo.")
        else:
            print("Status:         Stock objetivo cubierto.")

    print("-" * 50)


# ============================================================
# 7. MÓDULO DE MANTENIMIENTO Y ADMINISTRACIÓN
# ============================================================

def limpiar_registros() -> bool:
    """
    Elimina las solicitudes guardadas y reinicia el folio institucional,
    requiriendo confirmación explícita del usuario.
    """
    print("\n========== LIMPIEZA DE HISTORIAL DE SOLICITUDES ==========")
    confirmacion = input(
        "ADVERTENCIA: Esta acción eliminará todo el historial de solicitudes y reiniciará el folio a SOL-0001.\n"
        "¿Desea continuar? (S/N): "
    ).strip().upper()

    if confirmacion != "S":
        print("Operación cancelada por el usuario.")
        return False

    solicitudes_anteriores = solicitudes.copy()
    contador_anterior = contador_solicitudes

    solicitudes.clear()
    contador_solicitudes = 1

    if guardar_datos():
        print("Historial de solicitudes eliminado y contador reiniciado correctamente.")
        return True
    else:
        # Revertir cambios en memoria si falla el guardado atómico
        solicitudes.extend(solicitudes_anteriores)
        contador_solicitudes = contador_anterior
        print("No se pudo completar la limpieza debido a un error de escritura.")
        return False


# ============================================================
# 8. MENÚ PRINCIPAL E INTERFAZ CLI
# ============================================================

def menu_principal() -> None:
    """Muestra el menú interactivo principal de SMART CENDIS."""
    while True:
        print("\n" + "=" * 55)
        print("                    SMART CENDIS")
        print("=" * 55)
        print("   Sistema de Gestión Digital de Solicitudes,")
        print("     Abastecimiento y Control de Inventario")
        print("=" * 55)
        print(" 1. Registrar medicamento en catálogo")
        print(" 2. Consultar catálogo de medicamentos")
        print(" 3. Modificar datos de medicamento")
        print(" 4. Desactivar medicamento (baja lógica)")
        print(" 5. Consultar datos de paciente por servicio/cama")
        print(" 6. Registrar nueva solicitud de medicamento")
        print(" 7. Procesar solicitud en farmacia (Surtida / Negada)")
        print(" 8. Registrar recepción física y actualizar stock")
        print(" 9. Consultar historial de solicitudes")
        print("10. Consultar inventario y niveles de stock")
        print("11. Limpiar historial de solicitudes")
        print(" 0. Salir")
        print("=" * 55)

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            registrar_medicamento()
        elif opcion == "2":
            consultar_medicamentos()
        elif opcion == "3":
            modificar_medicamento()
        elif opcion == "4":
            eliminar_medicamento()
        elif opcion == "5":
            consultar_paciente()
        elif opcion == "6":
            registrar_solicitud()
        elif opcion == "7":
            procesar_solicitud()
        elif opcion == "8":
            registrar_recepcion()
        elif opcion == "9":
            consultar_solicitudes()
        elif opcion == "10":
            consultar_inventario()
        elif opcion == "11":
            limpiar_registros()
        elif opcion == "0":
            print("\nSaliendo de SMART CENDIS...")
            print("Sistema finalizado correctamente.")
            break
        else:
            print("\nError: opción no válida. Seleccione un número del menú.")

        input("\nPresione ENTER para continuar...")


# ============================================================
# 9. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    cargar_datos()
    menu_principal()
