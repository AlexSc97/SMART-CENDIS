# ============================================================
# SMART CENDIS
# Sistema de Gestión Digital de Solicitudes,
# Abastecimiento y Control de Inventario Hospitalario
# ============================================================

import json
import os


# ============================================================
# 1. DATOS INICIALES
# ============================================================

# ------------------------------------------------------------
# 1.1 CATÁLOGO DE MEDICAMENTOS
# ------------------------------------------------------------

medicamentos = [
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


# ------------------------------------------------------------
# 1.2 DATOS DE PACIENTES
# ------------------------------------------------------------

pacientes = [
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


# ------------------------------------------------------------
# 1.3 SOLICITUDES
# ------------------------------------------------------------

solicitudes = []

contador_solicitudes = 1

# Archivo local de persistencia, ubicado junto a este programa.
ARCHIVO_DATOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "smart_cendis.json"
)


def cargar_datos():
    """Carga el estado guardado; conserva los datos iniciales si no puede leerlo."""
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

        if not all(isinstance(valor, list) for valor in (
            medicamentos_guardados,
            pacientes_guardados,
            solicitudes_guardadas
        )):
            raise ValueError("medicamentos, pacientes y solicitudes deben ser listas")

        def registros_validos(registros, campos_texto, campos_entero=(), campo_booleano=None):
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
                if (campo_booleano is not None
                        and (campo_booleano not in registro
                             or not isinstance(registro[campo_booleano], bool))):
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

        if (not isinstance(contador_guardado, int)
                or isinstance(contador_guardado, bool)
                or contador_guardado < 1):
            raise ValueError("contador_solicitudes debe ser un entero positivo")

        medicamentos = medicamentos_guardados
        pacientes = pacientes_guardados
        solicitudes = solicitudes_guardadas
        contador_solicitudes = contador_guardado

    except FileNotFoundError:
        # Primer arranque: usar los datos iniciales declarados en el programa.
        return
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as error:
        print(
            "Aviso: no se pudieron cargar los datos guardados "
            f"({error}). Se conservarán los datos iniciales."
        )


def guardar_datos():
    """Guarda el estado actual de forma atómica y reporta errores sin detener el programa."""
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
# 2. MÓDULO DE MEDICAMENTOS
# ============================================================

# ------------------------------------------------------------
# 2.1 REGISTRAR MEDICAMENTO
# ------------------------------------------------------------

def registrar_medicamento():
    """Registra un nuevo medicamento en el catálogo."""

    clave = input(
        "Ingrese la clave del medicamento: "
    ).strip()

    # Verificar que la clave no exista previamente
    for medicamento in medicamentos:
        if medicamento["clave"] == clave:
            print("Error: la clave ya se encuentra registrada.")
            return

    nombre = input(
        "Ingrese el nombre del medicamento: "
    ).strip()

    presentacion = input(
        "Ingrese la presentación: "
    ).strip()

    unidad_fisica = input(
        "Ingrese la unidad física: "
    ).strip()

    try:
        stock_actual = int(
            input("Ingrese el stock actual: ")
        )

        stock_objetivo = int(
            input("Ingrese el stock objetivo: ")
        )

    except ValueError:
        print("Error: el stock debe ser un número entero.")
        return

    if stock_actual < 0 or stock_objetivo < 0:
        print("Error: las cantidades no pueden ser negativas.")
        return

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


# ------------------------------------------------------------
# 2.2 CONSULTAR MEDICAMENTOS
# ------------------------------------------------------------

def consultar_medicamentos():
    """Muestra los medicamentos activos registrados."""

    print("\n========== CATÁLOGO DE MEDICAMENTOS ==========")

    encontrados = False

    for medicamento in medicamentos:

        if medicamento["activo"]:

            encontrados = True

            print(f"Clave: {medicamento['clave']}")
            print(f"Nombre: {medicamento['nombre']}")

            print(
                f"Presentación: "
                f"{medicamento['presentacion']}"
            )

            print(
                f"Unidad física: "
                f"{medicamento['unidad_fisica']}"
            )

            print(
                f"Stock actual: "
                f"{medicamento['stock_actual']}"
            )

            print(
                f"Stock objetivo: "
                f"{medicamento['stock_objetivo']}"
            )

            print("-" * 45)

    if not encontrados:
        print(
            "No existen medicamentos activos registrados."
        )


# ------------------------------------------------------------
# 2.3 BUSCAR MEDICAMENTO POR CLAVE
# ------------------------------------------------------------

def buscar_medicamento(clave):
    """
    Busca un medicamento mediante su clave institucional.

    Esta función se conserva para uso interno del sistema.
    El usuario final no necesita conocer la clave.
    """

    for medicamento in medicamentos:

        if (
            medicamento["clave"] == clave
            and medicamento["activo"]
        ):
            return medicamento

    return None


# ------------------------------------------------------------
# 2.4 MODIFICAR MEDICAMENTO
# ------------------------------------------------------------

def modificar_medicamento():
    """Permite modificar los datos de un medicamento."""

    clave = input(
        "Ingrese la clave del medicamento a modificar: "
    ).strip()

    medicamento = buscar_medicamento(clave)

    if medicamento is None:
        print("Error: medicamento no encontrado.")
        return

    print("\nMedicamento encontrado:")
    print(f"Nombre actual: {medicamento['nombre']}")

    print(
        f"Stock objetivo actual: "
        f"{medicamento['stock_objetivo']}"
    )

    nuevo_nombre = input(
        "Nuevo nombre (Enter para conservar): "
    ).strip()

    if nuevo_nombre != "":
        medicamento["nombre"] = nuevo_nombre

    try:

        nuevo_stock_objetivo = input(
            "Nuevo stock objetivo "
            "(Enter para conservar): "
        ).strip()

        if nuevo_stock_objetivo != "":

            nuevo_stock_objetivo = int(
                nuevo_stock_objetivo
            )

            if nuevo_stock_objetivo < 0:
                print(
                    "Error: el stock objetivo "
                    "no puede ser negativo."
                )
                return

            medicamento["stock_objetivo"] = (
                nuevo_stock_objetivo
            )

    except ValueError:
        print(
            "Error: el stock objetivo "
            "debe ser un número entero."
        )
        return

    print("Medicamento modificado correctamente.")
    guardar_datos()


# ------------------------------------------------------------
# 2.5 ELIMINACIÓN LÓGICA
# ------------------------------------------------------------

def eliminar_medicamento():
    """
    Desactiva un medicamento sin eliminar físicamente
    el registro del catálogo.
    """

    clave = input(
        "Ingrese la clave del medicamento a desactivar: "
    ).strip()

    medicamento = buscar_medicamento(clave)

    if medicamento is None:
        print("Error: medicamento no encontrado.")
        return

    confirmacion = input(
        f"¿Desea desactivar "
        f"{medicamento['nombre']}? (S/N): "
    ).upper()

    if confirmacion == "S":

        medicamento["activo"] = False
        guardar_datos()

        print(
            "Medicamento desactivado correctamente."
        )

    else:
        print("Operación cancelada.")


# ============================================================
# 3. MÓDULO DE PACIENTES
# ============================================================

# ------------------------------------------------------------
# 3.1 BUSCAR PACIENTE
# ------------------------------------------------------------

def buscar_paciente(servicio, cama):
    """Busca un paciente mediante servicio y cama."""

    for paciente in pacientes:

        if (
            paciente["servicio"].lower()
            == servicio.lower()
            and paciente["cama"] == cama
        ):
            return paciente

    return None


# ------------------------------------------------------------
# 3.2 CONSULTAR PACIENTE
# ------------------------------------------------------------

def consultar_paciente():
    """
    Solicita servicio y cama y muestra
    los datos del paciente.
    """

    servicio = input(
        "Ingrese el servicio: "
    ).strip()

    cama = input(
        "Ingrese la cama: "
    ).strip()

    paciente = buscar_paciente(
        servicio,
        cama
    )

    if paciente:

        print("\nPaciente encontrado.")

        print(
            f"Servicio: {paciente['servicio']}"
        )

        print(
            f"Cama: {paciente['cama']}"
        )

        print(
            f"Nombre: {paciente['nombre']}"
        )

        print(
            f"NSS: {paciente['nss']}"
        )

    else:

        print(
            "\nNo se encontró un paciente "
            "para el servicio y cama indicados."
        )


# ============================================================
# 4. MÓDULO DE SOLICITUDES
# ============================================================

# ------------------------------------------------------------
# 4.1 SELECCIONAR TURNO
# ------------------------------------------------------------

def seleccionar_turno():
    """Permite seleccionar manualmente el turno."""

    print("\nSeleccione el turno:")
    print("1. Matutino")
    print("2. Vespertino")
    print("3. Nocturno")

    opcion = input(
        "Seleccione una opción: "
    ).strip()

    if opcion == "1":
        return "MATUTINO"

    elif opcion == "2":
        return "VESPERTINO"

    elif opcion == "3":
        return "NOCTURNO"

    else:
        print(
            "Error: opción de turno no válida."
        )
        return None


# ------------------------------------------------------------
# 4.2 SELECCIONAR MEDICAMENTO
# ------------------------------------------------------------

def seleccionar_medicamento():
    """
    Permite buscar un medicamento activo mediante
    su nombre o una parte del nombre.

    El usuario no necesita conocer la clave institucional.
    """

    medicamentos_activos = [
        medicamento
        for medicamento in medicamentos
        if medicamento["activo"]
    ]

    if not medicamentos_activos:

        print(
            "No hay medicamentos disponibles."
        )

        return None

    busqueda = input(
        "\nIngrese el nombre del medicamento: "
    ).strip().lower()

    if not busqueda:

        print(
            "Error: debe ingresar un nombre."
        )

        return None

    resultados = [
        medicamento
        for medicamento in medicamentos_activos
        if busqueda
        in medicamento["nombre"].lower()
    ]

    if not resultados:

        print(
            "No se encontraron medicamentos."
        )

        return None

    print(
        "\n========== MEDICAMENTOS ENCONTRADOS =========="
    )

    for i, medicamento in enumerate(
        resultados,
        start=1
    ):

        print(
            f"{i}. {medicamento['nombre']} "
            f"({medicamento['presentacion']})"
        )

    try:

        opcion = int(
            input(
                "Seleccione una opción: "
            )
        )

        if (
            opcion < 1
            or opcion > len(resultados)
        ):

            print(
                "Error: opción no válida."
            )

            return None

        return resultados[opcion - 1]

    except ValueError:

        print(
            "Error: debe seleccionar un número."
        )

        return None


# ------------------------------------------------------------
# 4.3 REGISTRAR SOLICITUD
# ------------------------------------------------------------

def registrar_solicitud():
    """Registra una solicitud; devuelve el registro o None si falla."""
    global contador_solicitudes

    print("\n========== NUEVA SOLICITUD ==========")
    servicio = input("Ingrese el servicio: ").strip()
    cama = input("Ingrese la cama: ").strip()
    paciente = buscar_paciente(servicio, cama)
    if paciente is None:
        print("Error: no se encontró un paciente para el servicio y cama indicados.")
        return None

    print(f"\nPaciente encontrado: {paciente['nombre']}")
    print(f"NSS: {paciente['nss']}")
    medicamento = seleccionar_medicamento()
    if medicamento is None:
        return None
    print(f"\nMedicamento seleccionado: {medicamento['nombre']}")
    print(f"Clave: {medicamento['clave']}")
    print(f"Stock actual: {medicamento['stock_actual']}")

    try:
        cantidad = int(input("Ingrese la cantidad solicitada: "))
    except ValueError:
        print("Error: la cantidad debe ser un número entero.")
        return None
    if cantidad <= 0:
        print("Error: la cantidad debe ser mayor que cero.")
        return None

    turno = seleccionar_turno()
    if turno is None:
        return None
    usuario = input("Ingrese el usuario responsable: ").strip()
    if not usuario:
        print("Error: debe ingresar un usuario.")
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
    print(f"\nSolicitud registrada correctamente. Folio: {folio}")
    return nueva_solicitud


# ============================================================
# 5. MÓDULO DE PROCESAMIENTO DE SOLICITUDES
# ============================================================

# ------------------------------------------------------------
# 5.1 BUSCAR SOLICITUD POR FOLIO
# ------------------------------------------------------------

def buscar_solicitud(folio):
    """Busca una solicitud mediante su folio."""

    for solicitud in solicitudes:

        if solicitud["folio"] == folio:
            return solicitud

    return None


# ------------------------------------------------------------
# 5.2 MOSTRAR SOLICITUD
# ------------------------------------------------------------

def mostrar_solicitud(solicitud):
    """Muestra los datos principales de una solicitud."""

    print("\n========== SOLICITUD ==========")

    print(f"Folio: {solicitud['folio']}")
    print(f"Servicio: {solicitud['servicio']}")
    print(f"Cama: {solicitud['cama']}")
    print(f"Paciente: {solicitud['paciente']}")
    print(f"NSS: {solicitud['nss']}")

    print(
        f"Medicamento: "
        f"{solicitud['nombre_medicamento']}"
    )

    print(
        f"Clave: "
        f"{solicitud['medicamento']}"
    )

    print(
        f"Cantidad solicitada: "
        f"{solicitud['cantidad']}"
    )

    print(
        f"Turno: "
        f"{solicitud['turno']}"
    )

    print(
        f"Usuario: "
        f"{solicitud['usuario']}"
    )

    print(
        f"Tipo: "
        f"{solicitud['tipo']}"
    )

    print(
        f"Estado actual: "
        f"{solicitud['estado']}"
    )


# ------------------------------------------------------------
# 5.3 PROCESAR RESPUESTA DE FARMACIA
# ------------------------------------------------------------

def procesar_solicitud(folio=None):
    """Registra la respuesta de farmacia; devuelve la solicitud o None."""
    print("\n========== PROCESAR SOLICITUD ==========")
    if folio is None:
        folio = input("Ingrese el folio de la solicitud: ").strip()
    solicitud = buscar_solicitud(folio)
    if solicitud is None:
        print("Error: solicitud no encontrada.")
        return None

    mostrar_solicitud(solicitud)
    if solicitud["estado"] != "PENDIENTE":
        print("\nError: la solicitud ya fue procesada.")
        return None

    print("\nRespuesta de farmacia:")
    print("1. Surtida")
    print("2. Negada")
    opcion = input("Seleccione una opción: ").strip()
    if opcion == "1":
        solicitud["estado"] = "SURTIDA"
        print("\nSolicitud marcada como SURTIDA; pendiente de recepción física.")
    elif opcion == "2":
        solicitud["estado"] = "NEGADA"
        print("\nSolicitud marcada como NEGADA; no procede la recepción física.")
    else:
        print("\nError: opción no válida.")
        return None

    print(f"Folio {solicitud['folio']} actualizado correctamente.")
    guardar_datos()
    return solicitud


# ------------------------------------------------------------
# 5.4 REGISTRAR RECEPCIÓN FÍSICA
# ------------------------------------------------------------

def registrar_recepcion(folio=None):
    """Registra recepción física y actualiza cantidades, estado e inventario."""
    print("\n========== REGISTRAR RECEPCIÓN ==========")
    if folio is None:
        folio = input("Ingrese el folio de la solicitud: ").strip()
    solicitud = buscar_solicitud(folio)
    if solicitud is None:
        print("Error: solicitud no encontrada.")
        return None

    mostrar_solicitud(solicitud)
    if solicitud["estado"] != "SURTIDA":
        print("Error: solo se puede recibir una solicitud surtida por farmacia.")
        return None

    # La clave institucional se almacena en el campo 'medicamento'.
    medicamento_encontrado = buscar_medicamento(solicitud["medicamento"])
    if medicamento_encontrado is None:
        print("Error: medicamento activo no encontrado en el inventario.")
        return None

    print("\n========== INVENTARIO ==========")
    print(f"Medicamento: {medicamento_encontrado['nombre']}")
    print(f"Stock actual: {medicamento_encontrado['stock_actual']}")
    while True:
        try:
            cantidad_recibida = int(input("Ingrese la cantidad recibida físicamente: "))
        except ValueError:
            print("Error: ingrese un número entero.")
            continue
        if not 0 <= cantidad_recibida <= solicitud["cantidad"]:
            print("Error: la cantidad debe estar entre 0 y la cantidad solicitada.")
            continue
        break

    stock_anterior = medicamento_encontrado["stock_actual"]
    cantidad_pendiente = solicitud["cantidad"] - cantidad_recibida
    if cantidad_recibida == 0:
        estado_final = "NEGADA"
    elif cantidad_pendiente > 0:
        estado_final = "SURTIDA_PARCIAL"
    else:
        estado_final = "SURTIDA"

    medicamento_encontrado["stock_actual"] += cantidad_recibida
    solicitud["cantidad_recibida"] = cantidad_recibida
    solicitud["cantidad_pendiente"] = cantidad_pendiente
    solicitud["estado"] = estado_final
    guardar_datos()

    print("\n========== RECEPCIÓN REGISTRADA ==========")
    print(f"Folio: {folio}")
    print(f"Medicamento: {medicamento_encontrado['nombre']}")
    print(f"Cantidad solicitada: {solicitud['cantidad']}")
    print(f"Cantidad recibida: {cantidad_recibida}")
    print(f"Cantidad pendiente: {cantidad_pendiente}")
    print(f"Estado final: {estado_final}")
    print(f"Stock anterior: {stock_anterior}")
    print(f"Stock nuevo: {medicamento_encontrado['stock_actual']}")
    return solicitud


# ============================================================
# 6. TESTING
# ============================================================

# IMPORTANTE:
# Durante el desarrollo activamos únicamente
# la prueba que estamos validando.
#
# No ejecutamos todas las pruebas al mismo tiempo
# mientras seguimos desarrollando los módulos.


# ============================================================
# TESTING - MÓDULO 1
# ============================================================

# ------------------------------------------------------------
# P01 - REGISTRO
# ------------------------------------------------------------

# registrar_medicamento()


# ------------------------------------------------------------
# P02 - CONSULTA
# ------------------------------------------------------------

# consultar_medicamentos()


# ------------------------------------------------------------
# P03 - MODIFICACIÓN
# ------------------------------------------------------------

# modificar_medicamento()


# ------------------------------------------------------------
# P04 - CLAVE DUPLICADA
# ------------------------------------------------------------

# registrar_medicamento()


# ------------------------------------------------------------
# P05 - MEDICAMENTO INEXISTENTE
# ------------------------------------------------------------

# resultado = buscar_medicamento("9999")

# if resultado:
#     print(resultado)
# else:
#     print("Medicamento no encontrado.")


# ------------------------------------------------------------
# P06 - ELIMINACIÓN LÓGICA
# ------------------------------------------------------------

# medicamento = buscar_medicamento("0105")

# if medicamento:
#     print(
#         "Medicamento encontrado antes de desactivar."
#     )
#     print(medicamento)

# eliminar_medicamento()

# resultado = buscar_medicamento("0105")

# if resultado:
#     print(
#         "Error: el medicamento sigue activo."
#     )
# else:
#     print(
#         "Medicamento no disponible para consulta."
#     )


# ============================================================
# TESTING - MÓDULO 2
# ============================================================

# ------------------------------------------------------------
# P01 - PACIENTE EXISTENTE
# ------------------------------------------------------------

# consultar_paciente()


# ------------------------------------------------------------
# P02 - PACIENTE INEXISTENTE
# ------------------------------------------------------------

# consultar_paciente()


# ------------------------------------------------------------
# P03 - SERVICIO Y CAMA
# ------------------------------------------------------------

# consultar_paciente()


# ============================================================
# TESTING - MÓDULO 3
# ============================================================

# ------------------------------------------------------------
# P01 - SELECCIÓN DE TURNO
# ------------------------------------------------------------

# turno_prueba = seleccionar_turno()

# if turno_prueba:
#     print(
#         f"Turno seleccionado: {turno_prueba}"
#     )


# ------------------------------------------------------------
# P02 - SELECCIÓN DE MEDICAMENTO POR NOMBRE
# ------------------------------------------------------------

# medicamento_prueba = seleccionar_medicamento()

# if medicamento_prueba:

#     print(
#         "\nMedicamento seleccionado correctamente."
#     )

#     print(
#         f"Clave: {medicamento_prueba['clave']}"
#     )

#     print(
#         f"Nombre: {medicamento_prueba['nombre']}"
#     )

#     print(
#         f"Presentación: "
#         f"{medicamento_prueba['presentacion']}"
#     )

#     print(
#         f"Stock actual: "
#         f"{medicamento_prueba['stock_actual']}"
#     )


# ------------------------------------------------------------
# P03 - REGISTRO DE SOLICITUD
# ------------------------------------------------------------

# registrar_solicitud()

# print("\n--- VERIFICACIÓN DE SOLICITUD ---")
# print(solicitudes)

# print("\n--- VERIFICACIÓN DE INVENTARIO ---")
# medicamento = buscar_medicamento("5121")

# if medicamento:
#     print(
#         f"{medicamento['nombre']} - "
#         f"Stock actual: {medicamento['stock_actual']}"
#     )

# ============================================================
# 5.5 CONSULTAR SOLICITUDES
# ============================================================

def consultar_solicitudes():
    """Muestra todas las solicitudes registradas."""

    print("\n========== SOLICITUDES REGISTRADAS ==========")

    if not solicitudes:
        print("No existen solicitudes registradas.")
        return

    for solicitud in solicitudes:

        print("-" * 50)

        print(
            f"Folio: {solicitud['folio']}"
        )

        print(
            f"Servicio: {solicitud['servicio']}"
        )

        print(
            f"Cama: {solicitud['cama']}"
        )

        print(
            f"Paciente: {solicitud['paciente']}"
        )

        print(
            f"Medicamento: "
            f"{solicitud['nombre_medicamento']}"
        )

        print(
            f"Cantidad solicitada: "
            f"{solicitud['cantidad']}"
        )

        print(
            f"Cantidad recibida: "
            f"{solicitud.get('cantidad_recibida', 0)}"
        )

        print(
            f"Cantidad pendiente: "
            f"{solicitud.get('cantidad_pendiente', solicitud['cantidad'])}"
        )

        print(
            f"Estado: {solicitud['estado']}"
        )

    print("-" * 50)


# ============================================================
# 5.6 CONSULTAR INVENTARIO
# ============================================================

def consultar_inventario():
    """Muestra el inventario actual de medicamentos."""

    print("\n========== INVENTARIO ACTUAL ==========")

    medicamentos_activos = [
        medicamento
        for medicamento in medicamentos
        if medicamento["activo"]
    ]

    if not medicamentos_activos:
        print("No existen medicamentos activos.")
        return

    for medicamento in medicamentos_activos:

        print("-" * 50)

        print(
            f"Clave: {medicamento['clave']}"
        )

        print(
            f"Medicamento: {medicamento['nombre']}"
        )

        print(
            f"Presentación: "
            f"{medicamento['presentacion']}"
        )

        print(
            f"Unidad física: "
            f"{medicamento['unidad_fisica']}"
        )

        print(
            f"Stock actual: "
            f"{medicamento['stock_actual']}"
        )

        print(
            f"Stock objetivo: "
            f"{medicamento['stock_objetivo']}"
        )

        faltante = (
            medicamento["stock_objetivo"]
            - medicamento["stock_actual"]
        )

        if faltante > 0:
            print(
                f"Faltante para stock objetivo: "
                f"{faltante}"
            )
        else:
            print(
                "Stock objetivo cubierto."
            )

    print("-" * 50)

# ============================================================
# 6. MENÚ PRINCIPAL
# ============================================================

def menu_principal():
    """Muestra el menú principal de SMART CENDIS."""

    while True:

        print("\n")
        print("=" * 50)
        print("              SMART CENDIS")
        print("=" * 50)
        print(
            "Sistema de Gestión Digital de Solicitudes,"
        )
        print(
            "Abastecimiento y Control de Inventario"
        )
        print("=" * 50)

        print("\n1. Registrar medicamento")
        print("2. Consultar medicamentos")
        print("3. Modificar medicamento")
        print("4. Desactivar medicamento")
        print("5. Consultar paciente")
        print("6. Registrar solicitud")
        print("7. Procesar solicitud")
        print("8. Registrar recepción")
        print("9. Consultar solicitudes")
        print("10. Consultar inventario")
        print("11. Limpiar historial de solicitudes")
        print("0. Salir")

        print("=" * 50)

        opcion = input(
            "Seleccione una opción: "
        ).strip()

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

            print(
                "\nSaliendo de SMART CENDIS..."
            )

            print(
                "Sistema finalizado correctamente."
            )

            break

        else:

            print(
                "\nError: opción no válida."
            )

        input(
            "\nPresione ENTER para continuar..."
        )


def limpiar_registros():
    """Elimina las solicitudes guardadas y reinicia el folio, previa confirmación."""
    global contador_solicitudes

    confirmacion = input(
        "Esto eliminará todo el historial de solicitudes. "
        "¿Desea continuar? (s/n): "
    ).strip().lower()

    if confirmacion != "s":
        print("Limpieza cancelada.")
        return

    solicitudes_anteriores = solicitudes.copy()
    contador_anterior = contador_solicitudes
    solicitudes.clear()
    contador_solicitudes = 1

    if guardar_datos():
        print("Historial de solicitudes eliminado correctamente.")
    else:
        solicitudes.extend(solicitudes_anteriores)
        contador_solicitudes = contador_anterior
        print("No se limpiaron los registros porque no se pudieron guardar los cambios.")


# ============================================================
# 7. EJECUCIÓN DEL SISTEMA
# ============================================================

if __name__ == "__main__":

    cargar_datos()
    menu_principal()
