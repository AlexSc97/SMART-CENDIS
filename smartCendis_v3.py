# ============================================================
# SMART CENDIS  –  Etapa 3
# Sistema de Gestión Digital de Solicitudes,
# Abastecimiento y Control de Inventario Hospitalario
# ============================================================
#
# Versión: 3.0.0
# Etapa  : 3 — Validación con expresiones regulares,
#               manejo robusto de persistencia y
#               suite de pruebas automatizadas.
#
# Cambios respecto a la versión de Etapa 2 (smartCendis_limpio.py):
#   [REG-01] Módulo centralizado de patrones y funciones de validación
#            con re.fullmatch.  Todas las capturas del usuario pasan
#            por al menos un patrón antes de continuar.
#   [PER-01] Las operaciones mutables verifican el resultado de
#            guardar_datos() y revierten los cambios en memoria cuando
#            el guardado falla, siguiendo el patrón que ya usaba
#            limpiar_registros().
#   [PER-02] cargar_datos() valida la coherencia del contador frente
#            a los folios existentes y detecta estados o cantidades
#            incompatibles.
#   [VAL-01] La confirmación de desactivación normaliza espacios antes
#            de comparar (alineado con limpiar_registros).
#   [VAL-02] El folio de la solicitud sigue el patrón SOL-NNNN sin
#            límite superior, para no impedir la secuencia natural.
# ============================================================

import json
import os
import re


# ============================================================
# 0. MÓDULO DE VALIDACIÓN  [REG-01]
# ============================================================
# Contiene todos los patrones y las funciones auxiliares que
# validan la entrada del usuario antes de procesarla.
#
# Convenciones de nomenclatura:
#   RE_<CAMPO> : patrón compilado para ese campo.
#   validar_<campo>(texto) -> str | None
#       Devuelve la cadena normalizada si el formato es válido,
#       o None si no coincide con el patrón.
# ============================================================

# ------------------------------------------------------------
# 0.1  PATRONES COMPILADOS
# ------------------------------------------------------------

# Menú principal: dígito(s) entre 0 y 11
RE_MENU = re.compile(r"^(?:10|11|[0-9])$")

# Clave institucional de medicamento: 4 dígitos (formato del catálogo IMSS).
# Si en el futuro se aceptan otros formatos, ampliar aquí sin tocar el resto
# del código.
RE_CLAVE_MED = re.compile(r"^\d{4}$")

# Nombre de medicamento: letras, dígitos, espacios y algunos caracteres
# especiales (paréntesis, punto, coma, porcentaje, barra, guión).
# Mínimo 2 caracteres, máximo 120.
RE_NOMBRE_MED = re.compile(r"^[\w\s\(\)\.\,\%\/\-áéíóúüñÁÉÍÓÚÜÑ]{2,120}$")

# Presentación farmacéutica: misma familia que el nombre.
RE_PRESENTACION = re.compile(r"^[\w\s\(\)\.\,\%\/\-áéíóúüñÁÉÍÓÚÜÑ]{2,80}$")

# Unidad física: letras y espacios, 2–40 caracteres.
RE_UNIDAD = re.compile(r"^[A-Za-záéíóúüñÁÉÍÓÚÜÑ][A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]{1,39}$")

# Stock (entero ≥ 0): cadena que representa un número entero no negativo.
RE_STOCK = re.compile(r"^(0|[1-9]\d*)$")

# Servicio hospitalario: letras, espacios, hasta 60 caracteres.
RE_SERVICIO = re.compile(r"^[A-Za-záéíóúüñÁÉÍÓÚÜÑ][A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]{1,59}$")

# Cama: 1–4 dígitos (p. ej. "01", "1", "304").
RE_CAMA = re.compile(r"^\d{1,4}$")

# Búsqueda libre de medicamento: mínimo 1 carácter imprimible, máximo 60.
RE_BUSQUEDA = re.compile(r"^[\w\s\.\-áéíóúüñÁÉÍÓÚÜÑ]{1,60}$")

# Selección de resultado de lista (dígito positivo, sin límite superior
# fijo; el límite lo aplica la lógica de negocio).
RE_SELECCION = re.compile(r"^[1-9]\d*$")

# Cantidad solicitada o recibida: entero positivo (≥ 1 para solicitudes;
# ≥ 0 para recepciones — el rango lo impone la lógica de negocio).
RE_CANTIDAD_POS = re.compile(r"^[1-9]\d*$")      # cantidad solicitada (≥1)
RE_CANTIDAD_GE0 = re.compile(r"^(0|[1-9]\d*)$")  # cantidad recibida   (≥0)

# Turno: una opción del menú 1–3.
RE_TURNO_OPC = re.compile(r"^[1-3]$")

# Usuario responsable: letras, dígitos, espacios y algunos signos.
RE_USUARIO = re.compile(r"^[\w\s\.\-áéíóúüñÁÉÍÓÚÜÑ]{2,60}$")

# Tipo de solicitud: opción 1 o 2.
RE_TIPO_OPC = re.compile(r"^[12]$")

# Folio de solicitud: SOL- seguido de ≥4 dígitos.
RE_FOLIO = re.compile(r"^SOL-\d{4,}$")

# Respuesta de farmacia: opción 1 o 2.
RE_FARMACIA_OPC = re.compile(r"^[12]$")

# Confirmaciones simples: s o n (mayúsculas o minúsculas).
RE_CONFIRMACION_SN = re.compile(r"^[SsNn]$")

# Confirmación de desactivación: S o N (la función acepta s/n y normaliza).
RE_CONFIRMACION_DESACTIVAR = re.compile(r"^[SsNn]$")


# ------------------------------------------------------------
# 0.2  FUNCIONES DE VALIDACIÓN GENÉRICAS
# ------------------------------------------------------------

def validar_patron(texto: str, patron: re.Pattern, descripcion: str):
    """
    Aplica patron a texto.
    Retorna texto.strip() si coincide; imprime un error y retorna None si no.

    Parámetros
    ----------
    texto       : cadena capturada del usuario (ya con .strip() aplicado).
    patron      : expresión regular compilada.
    descripcion : mensaje de error legible para el usuario.
    """
    valor = texto.strip()
    if patron.fullmatch(valor):
        return valor
    print(f"Error: formato inválido — {descripcion}.")
    return None


def leer_con_patron(prompt: str, patron: re.Pattern, descripcion: str,
                    intentos: int = 3):
    """
    Muestra prompt, lee la entrada y valida con patron.
    Reintenta hasta `intentos` veces y retorna la cadena válida o None.

    Parámetros
    ----------
    prompt      : texto que se muestra al usuario.
    patron      : expresión regular compilada.
    descripcion : descripción del formato esperado (para el mensaje de error).
    intentos    : número máximo de reintentos antes de abortar.
    """
    for _ in range(intentos):
        entrada = input(prompt).strip()
        resultado = validar_patron(entrada, patron, descripcion)
        if resultado is not None:
            return resultado
    print("Demasiados intentos. Operación cancelada.")
    return None


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
# 1.3 SOLICITUDES Y CONTADOR
# ------------------------------------------------------------

solicitudes = []

contador_solicitudes = 1

# Ruta del archivo de persistencia (junto al programa).
ARCHIVO_DATOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "smart_cendis.json"
)


# ============================================================
# 2. PERSISTENCIA
# ============================================================

def _folio_a_numero(folio: str) -> int:
    """
    Extrae el número entero de un folio con formato SOL-NNNN.
    Retorna 0 si el folio no tiene el formato esperado.
    """
    m = RE_FOLIO.fullmatch(folio)
    if m:
        return int(folio[4:])
    return 0


def cargar_datos():
    """
    Carga el estado guardado desde ARCHIVO_DATOS.

    Validaciones realizadas:
      - La raíz del JSON debe ser un objeto.
      - medicamentos, pacientes y solicitudes deben ser listas.
      - Cada registro de medicamento, paciente y solicitud debe tener
        los campos requeridos con los tipos correctos.
      - contador_solicitudes debe ser un entero positivo mayor que
        el folio máximo almacenado  [PER-02].
      - Los estados de las solicitudes deben pertenecer al conjunto
        válido  [PER-02].
      - Las cantidades de las solicitudes deben ser no negativas  [PER-02].

    Si no puede leer o validar el archivo, conserva los datos iniciales
    y avisa al usuario.
    """
    global medicamentos, pacientes, solicitudes, contador_solicitudes

    try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, dict):
            raise ValueError("la raíz del archivo debe ser un objeto JSON")

        medicamentos_guardados  = datos.get("medicamentos")
        pacientes_guardados     = datos.get("pacientes")
        solicitudes_guardadas   = datos.get("solicitudes")
        contador_guardado       = datos.get("contador_solicitudes")

        # ── Tipo de las colecciones ────────────────────────────────
        if not all(isinstance(v, list) for v in (
            medicamentos_guardados,
            pacientes_guardados,
            solicitudes_guardadas
        )):
            raise ValueError(
                "medicamentos, pacientes y solicitudes deben ser listas"
            )

        # ── Validador interno de campos ────────────────────────────
        def registros_validos(registros, campos_texto,
                              campos_entero=(), campo_booleano=None):
            for r in registros:
                if not isinstance(r, dict):
                    return False
                for campo in campos_texto:
                    if campo not in r or not isinstance(r[campo], str):
                        return False
                for campo in campos_entero:
                    if (campo not in r
                            or not isinstance(r[campo], int)
                            or isinstance(r[campo], bool)):
                        return False
                if (campo_booleano is not None
                        and (campo_booleano not in r
                             or not isinstance(r[campo_booleano], bool))):
                    return False
            return True

        if not registros_validos(
            medicamentos_guardados,
            ("clave", "nombre", "presentacion", "unidad_fisica"),
            ("stock_actual", "stock_objetivo"),
            "activo"
        ):
            raise ValueError(
                "el catálogo de medicamentos tiene registros inválidos"
            )

        # Las cantidades de medicamentos no deben ser negativas  [PER-02]
        for med in medicamentos_guardados:
            if med["stock_actual"] < 0 or med["stock_objetivo"] < 0:
                raise ValueError(
                    f"medicamento {med.get('clave','?')} tiene stock negativo"
                )

        if not registros_validos(
            pacientes_guardados,
            ("servicio", "cama", "nombre", "nss")
        ):
            raise ValueError(
                "el catálogo de pacientes tiene registros inválidos"
            )

        if not registros_validos(
            solicitudes_guardadas,
            ("folio", "servicio", "cama", "paciente", "nss",
             "medicamento", "nombre_medicamento", "turno", "usuario",
             "tipo", "estado"),
            ("cantidad", "cantidad_recibida", "cantidad_pendiente")
        ):
            raise ValueError(
                "el historial de solicitudes tiene registros inválidos"
            )

        # Estados válidos  [PER-02]
        estados_validos = {
            "PENDIENTE", "SURTIDA", "NEGADA", "SURTIDA_PARCIAL"
        }
        for sol in solicitudes_guardadas:
            if sol["estado"] not in estados_validos:
                raise ValueError(
                    f"estado desconocido en solicitud {sol.get('folio','?')}: "
                    f"{sol['estado']}"
                )
            # Cantidades no negativas  [PER-02]
            if (sol["cantidad"] <= 0
                    or sol["cantidad_recibida"] < 0
                    or sol["cantidad_pendiente"] < 0):
                raise ValueError(
                    f"cantidades incoherentes en solicitud "
                    f"{sol.get('folio','?')}"
                )

        # Coherencia del contador con los folios existentes  [PER-02]
        if (not isinstance(contador_guardado, int)
                or isinstance(contador_guardado, bool)
                or contador_guardado < 1):
            raise ValueError(
                "contador_solicitudes debe ser un entero positivo"
            )

        folio_max = max(
            (_folio_a_numero(s["folio"]) for s in solicitudes_guardadas),
            default=0
        )
        if contador_guardado <= folio_max:
            # El contador no supera el folio más alto: se corrige en lugar
            # de abortar para no perder datos válidos.
            contador_corregido = folio_max + 1
            print(
                f"Aviso: contador ({contador_guardado}) no supera el folio "
                f"máximo ({folio_max}). Se ajusta a {contador_corregido}."
            )
            contador_guardado = contador_corregido

        medicamentos       = medicamentos_guardados
        pacientes          = pacientes_guardados
        solicitudes        = solicitudes_guardadas
        contador_solicitudes = contador_guardado

    except FileNotFoundError:
        # Primer arranque: usar los datos iniciales del programa.
        return
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as error:
        print(
            "Aviso: no se pudieron cargar los datos guardados "
            f"({error}). Se conservarán los datos iniciales."
        )


def guardar_datos() -> bool:
    """
    Persiste el estado actual de forma atómica.

    Utiliza un archivo temporal y os.replace para garantizar que el archivo
    principal nunca quede a medio escribir.

    Retorna True si el guardado fue exitoso, False en caso contrario.
    El llamador debe verificar el resultado y revertir cambios si es False.
    """
    archivo_temporal = f"{ARCHIVO_DATOS}.tmp"
    datos = {
        "medicamentos":        medicamentos,
        "pacientes":           pacientes,
        "solicitudes":         solicitudes,
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
# 3. MÓDULO DE MEDICAMENTOS
# ============================================================

# ------------------------------------------------------------
# 3.1 REGISTRAR MEDICAMENTO
# ------------------------------------------------------------

def registrar_medicamento():
    """
    Registra un nuevo medicamento en el catálogo.

    Validaciones de formato [REG-01]:
      - Clave   : RE_CLAVE_MED   (4 dígitos).
      - Nombre  : RE_NOMBRE_MED  (2–120 caracteres alfanuméricos y especiales).
      - Presentación: RE_PRESENTACION (2–80 caracteres).
      - Unidad física: RE_UNIDAD (2–40 letras y espacios).
      - Stock actual / objetivo: RE_STOCK (entero ≥ 0).

    Validaciones de negocio:
      - La clave no debe estar ya registrada.

    Persistencia [PER-01]:
      - Si guardar_datos() retorna False, el medicamento se elimina de la
        lista en memoria para evitar un estado divergente.
    """

    clave = leer_con_patron(
        "Ingrese la clave del medicamento (4 dígitos): ",
        RE_CLAVE_MED,
        "la clave debe tener exactamente 4 dígitos"
    )
    if clave is None:
        return

    # Validación de negocio: clave duplicada
    for med in medicamentos:
        if med["clave"] == clave:
            print("Error: la clave ya se encuentra registrada.")
            return

    nombre = leer_con_patron(
        "Ingrese el nombre del medicamento: ",
        RE_NOMBRE_MED,
        "nombre inválido (2–120 caracteres; letras, dígitos y signos básicos)"
    )
    if nombre is None:
        return

    presentacion = leer_con_patron(
        "Ingrese la presentación: ",
        RE_PRESENTACION,
        "presentación inválida (2–80 caracteres)"
    )
    if presentacion is None:
        return

    unidad_fisica = leer_con_patron(
        "Ingrese la unidad física: ",
        RE_UNIDAD,
        "unidad inválida (2–40 letras y espacios)"
    )
    if unidad_fisica is None:
        return

    stock_actual_str = leer_con_patron(
        "Ingrese el stock actual: ",
        RE_STOCK,
        "el stock debe ser un número entero no negativo"
    )
    if stock_actual_str is None:
        return
    stock_actual = int(stock_actual_str)

    stock_objetivo_str = leer_con_patron(
        "Ingrese el stock objetivo: ",
        RE_STOCK,
        "el stock objetivo debe ser un número entero no negativo"
    )
    if stock_objetivo_str is None:
        return
    stock_objetivo = int(stock_objetivo_str)

    nuevo_medicamento = {
        "clave":          clave,
        "nombre":         nombre,
        "presentacion":   presentacion,
        "unidad_fisica":  unidad_fisica,
        "stock_actual":   stock_actual,
        "stock_objetivo": stock_objetivo,
        "activo":         True
    }

    medicamentos.append(nuevo_medicamento)

    # [PER-01] Revertir si el guardado falla
    if not guardar_datos():
        medicamentos.remove(nuevo_medicamento)
        print("Error: el medicamento no se registró porque el guardado falló.")
        return

    print("Medicamento registrado correctamente.")


# ------------------------------------------------------------
# 3.2 CONSULTAR MEDICAMENTOS
# ------------------------------------------------------------

def consultar_medicamentos():
    """Muestra todos los medicamentos activos registrados en el catálogo."""

    print("\n========== CATÁLOGO DE MEDICAMENTOS ==========")

    encontrados = False

    for medicamento in medicamentos:
        if medicamento["activo"]:
            encontrados = True
            print(f"Clave: {medicamento['clave']}")
            print(f"Nombre: {medicamento['nombre']}")
            print(f"Presentación: {medicamento['presentacion']}")
            print(f"Unidad física: {medicamento['unidad_fisica']}")
            print(f"Stock actual: {medicamento['stock_actual']}")
            print(f"Stock objetivo: {medicamento['stock_objetivo']}")
            print("-" * 45)

    if not encontrados:
        print("No existen medicamentos activos registrados.")


# ------------------------------------------------------------
# 3.3 BUSCAR MEDICAMENTO POR CLAVE (uso interno)
# ------------------------------------------------------------

def buscar_medicamento(clave: str):
    """
    Busca un medicamento activo por su clave institucional.

    Esta función es de uso interno; el usuario final no necesita conocer
    la clave directamente.

    Retorna el diccionario del medicamento o None si no existe o está
    desactivado.
    """
    for medicamento in medicamentos:
        if medicamento["clave"] == clave and medicamento["activo"]:
            return medicamento
    return None


# ------------------------------------------------------------
# 3.4 MODIFICAR MEDICAMENTO
# ------------------------------------------------------------

def modificar_medicamento():
    """
    Modifica el nombre o el stock objetivo de un medicamento activo.

    Validaciones de formato [REG-01]:
      - Clave            : RE_CLAVE_MED.
      - Nuevo nombre     : RE_NOMBRE_MED   (solo si el usuario ingresa algo).
      - Nuevo stock obj. : RE_STOCK        (solo si el usuario ingresa algo).

    Persistencia [PER-01]:
      - Si guardar_datos() retorna False, se restauran los valores previos.
    """

    clave = leer_con_patron(
        "Ingrese la clave del medicamento a modificar (4 dígitos): ",
        RE_CLAVE_MED,
        "la clave debe tener exactamente 4 dígitos"
    )
    if clave is None:
        return

    medicamento = buscar_medicamento(clave)
    if medicamento is None:
        print("Error: medicamento no encontrado.")
        return

    print("\nMedicamento encontrado:")
    print(f"  Nombre actual      : {medicamento['nombre']}")
    print(f"  Stock objetivo actual: {medicamento['stock_objetivo']}")

    # ── Guardar valores anteriores para revertir si el guardado falla ──
    nombre_anterior         = medicamento["nombre"]
    stock_objetivo_anterior = medicamento["stock_objetivo"]

    # Nombre (opcional)
    nuevo_nombre_raw = input("Nuevo nombre (Enter para conservar): ").strip()
    if nuevo_nombre_raw != "":
        nuevo_nombre = validar_patron(
            nuevo_nombre_raw, RE_NOMBRE_MED,
            "nombre inválido (2–120 caracteres)"
        )
        if nuevo_nombre is None:
            return
        medicamento["nombre"] = nuevo_nombre

    # Stock objetivo (opcional)
    nuevo_stock_raw = input(
        "Nuevo stock objetivo (Enter para conservar): "
    ).strip()
    if nuevo_stock_raw != "":
        nuevo_stock_str = validar_patron(
            nuevo_stock_raw, RE_STOCK,
            "el stock objetivo debe ser un número entero no negativo"
        )
        if nuevo_stock_str is None:
            # Revertir cambio de nombre si ya se realizó
            medicamento["nombre"] = nombre_anterior
            return
        medicamento["stock_objetivo"] = int(nuevo_stock_str)

    # [PER-01] Revertir si el guardado falla
    if not guardar_datos():
        medicamento["nombre"]         = nombre_anterior
        medicamento["stock_objetivo"] = stock_objetivo_anterior
        print("Error: los cambios no se guardaron. Se restauraron los valores anteriores.")
        return

    print("Medicamento modificado correctamente.")


# ------------------------------------------------------------
# 3.5 DESACTIVAR MEDICAMENTO (eliminación lógica)
# ------------------------------------------------------------

def eliminar_medicamento():
    """
    Desactiva un medicamento sin eliminar físicamente el registro.

    Validaciones de formato [REG-01]:
      - Clave         : RE_CLAVE_MED.
      - Confirmación  : RE_CONFIRMACION_DESACTIVAR (S/s/N/n).
                        Se normaliza a mayúsculas y se eliminan espacios
                        antes de comparar  [VAL-01].

    Persistencia [PER-01]:
      - Si guardar_datos() retorna False, el campo activo se restaura a True.
    """

    clave = leer_con_patron(
        "Ingrese la clave del medicamento a desactivar (4 dígitos): ",
        RE_CLAVE_MED,
        "la clave debe tener exactamente 4 dígitos"
    )
    if clave is None:
        return

    medicamento = buscar_medicamento(clave)
    if medicamento is None:
        print("Error: medicamento no encontrado.")
        return

    confirmacion_raw = leer_con_patron(
        f"¿Desea desactivar {medicamento['nombre']}? (S/N): ",
        RE_CONFIRMACION_DESACTIVAR,
        "responda S o N"
    )
    if confirmacion_raw is None:
        return

    # [VAL-01] Normalizar: eliminar espacios y convertir a mayúsculas
    confirmacion = confirmacion_raw.strip().upper()

    if confirmacion == "S":
        medicamento["activo"] = False

        # [PER-01] Revertir si el guardado falla
        if not guardar_datos():
            medicamento["activo"] = True
            print("Error: no se pudo guardar. El medicamento sigue activo.")
            return

        print("Medicamento desactivado correctamente.")
    else:
        print("Operación cancelada.")


# ============================================================
# 4. MÓDULO DE PACIENTES
# ============================================================

# ------------------------------------------------------------
# 4.1 BUSCAR PACIENTE (uso interno)
# ------------------------------------------------------------

def buscar_paciente(servicio: str, cama: str):
    """
    Busca un paciente por servicio y cama (comparación sin distinción
    de mayúsculas en el servicio).

    Retorna el diccionario del paciente o None si no se encuentra.
    """
    for paciente in pacientes:
        if (paciente["servicio"].lower() == servicio.lower()
                and paciente["cama"] == cama):
            return paciente
    return None


# ------------------------------------------------------------
# 4.2 CONSULTAR PACIENTE
# ------------------------------------------------------------

def consultar_paciente():
    """
    Solicita servicio y cama, y muestra los datos del paciente.

    Validaciones de formato [REG-01]:
      - Servicio : RE_SERVICIO.
      - Cama     : RE_CAMA.
    """

    servicio = leer_con_patron(
        "Ingrese el servicio: ",
        RE_SERVICIO,
        "servicio inválido (letras y espacios, 2–60 caracteres)"
    )
    if servicio is None:
        return

    cama = leer_con_patron(
        "Ingrese la cama: ",
        RE_CAMA,
        "cama inválida (1–4 dígitos)"
    )
    if cama is None:
        return

    paciente = buscar_paciente(servicio, cama)

    if paciente:
        print("\nPaciente encontrado.")
        print(f"Servicio: {paciente['servicio']}")
        print(f"Cama: {paciente['cama']}")
        print(f"Nombre: {paciente['nombre']}")
        print(f"NSS: {paciente['nss']}")
    else:
        print(
            "\nNo se encontró un paciente "
            "para el servicio y cama indicados."
        )


# ============================================================
# 5. MÓDULO DE SOLICITUDES
# ============================================================

# ------------------------------------------------------------
# 5.1 SELECCIONAR TURNO
# ------------------------------------------------------------

def seleccionar_turno():
    """
    Permite seleccionar manualmente el turno activo.

    Validaciones de formato [REG-01]:
      - Opción: RE_TURNO_OPC (1, 2 o 3).

    Retorna la cadena del turno ("MATUTINO", "VESPERTINO" o "NOCTURNO")
    o None si la opción no es válida.
    """

    print("\nSeleccione el turno:")
    print("1. Matutino")
    print("2. Vespertino")
    print("3. Nocturno")

    opcion = leer_con_patron(
        "Seleccione una opción: ",
        RE_TURNO_OPC,
        "ingrese 1, 2 o 3"
    )
    if opcion is None:
        return None

    turnos = {"1": "MATUTINO", "2": "VESPERTINO", "3": "NOCTURNO"}
    return turnos[opcion]


# ------------------------------------------------------------
# 5.2 SELECCIONAR MEDICAMENTO POR NOMBRE
# ------------------------------------------------------------

def seleccionar_medicamento():
    """
    Permite buscar un medicamento activo por nombre o parte del nombre.

    El usuario no necesita conocer la clave institucional; la búsqueda
    es parcial e insensible a mayúsculas.

    Validaciones de formato [REG-01]:
      - Búsqueda  : RE_BUSQUEDA   (1–60 caracteres imprimibles).
      - Selección : RE_SELECCION  (número positivo dentro del rango mostrado).

    Retorna el diccionario del medicamento seleccionado o None si falla.
    """

    medicamentos_activos = [m for m in medicamentos if m["activo"]]

    if not medicamentos_activos:
        print("No hay medicamentos disponibles.")
        return None

    busqueda = leer_con_patron(
        "\nIngrese el nombre del medicamento: ",
        RE_BUSQUEDA,
        "la búsqueda debe tener entre 1 y 60 caracteres"
    )
    if busqueda is None:
        return None

    resultados = [
        m for m in medicamentos_activos
        if busqueda.lower() in m["nombre"].lower()
    ]

    if not resultados:
        print("No se encontraron medicamentos.")
        return None

    print("\n========== MEDICAMENTOS ENCONTRADOS ==========")
    for i, m in enumerate(resultados, start=1):
        print(f"{i}. {m['nombre']} ({m['presentacion']})")

    seleccion_str = leer_con_patron(
        "Seleccione una opción: ",
        RE_SELECCION,
        "ingrese un número positivo"
    )
    if seleccion_str is None:
        return None

    seleccion = int(seleccion_str)
    if seleccion > len(resultados):
        print("Error: opción fuera de rango.")
        return None

    return resultados[seleccion - 1]


# ------------------------------------------------------------
# 5.3 REGISTRAR SOLICITUD
# ------------------------------------------------------------

def registrar_solicitud():
    """
    Registra una nueva solicitud de medicamento.

    Flujo:
      1. Valida servicio y cama; busca al paciente.
      2. El usuario selecciona el medicamento por nombre.
      3. Valida la cantidad solicitada (entero ≥ 1).
      4. Selecciona el turno.
      5. Valida el usuario responsable.
      6. Selecciona el tipo (Normal / Urgencia).
      7. Genera el folio, crea el registro y persiste.

    Validaciones de formato [REG-01]: RE_SERVICIO, RE_CAMA, RE_BUSQUEDA,
      RE_SELECCION, RE_CANTIDAD_POS, RE_TURNO_OPC, RE_USUARIO, RE_TIPO_OPC.

    Persistencia [PER-01]:
      - Si guardar_datos() falla, la solicitud se elimina de la lista y el
        contador se decrementa antes de retornar None.

    Retorna el registro creado o None si algún paso falla.
    """
    global contador_solicitudes

    print("\n========== NUEVA SOLICITUD ==========")

    servicio = leer_con_patron(
        "Ingrese el servicio: ",
        RE_SERVICIO,
        "servicio inválido (letras y espacios, 2–60 caracteres)"
    )
    if servicio is None:
        return None

    cama = leer_con_patron(
        "Ingrese la cama: ",
        RE_CAMA,
        "cama inválida (1–4 dígitos)"
    )
    if cama is None:
        return None

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

    cantidad_str = leer_con_patron(
        "Ingrese la cantidad solicitada: ",
        RE_CANTIDAD_POS,
        "la cantidad debe ser un número entero mayor que cero"
    )
    if cantidad_str is None:
        return None
    cantidad = int(cantidad_str)

    turno = seleccionar_turno()
    if turno is None:
        return None

    usuario = leer_con_patron(
        "Ingrese el usuario responsable: ",
        RE_USUARIO,
        "usuario inválido (2–60 caracteres alfanuméricos)"
    )
    if usuario is None:
        return None

    print("\nTipo de solicitud:")
    print("1. Normal")
    print("2. Urgencia")
    tipo_opcion = leer_con_patron(
        "Seleccione una opción: ",
        RE_TIPO_OPC,
        "ingrese 1 (Normal) o 2 (Urgencia)"
    )
    if tipo_opcion is None:
        return None
    tipo = "NORMAL" if tipo_opcion == "1" else "URGENCIA"

    folio = f"SOL-{contador_solicitudes:04d}"
    nueva_solicitud = {
        "folio":             folio,
        "servicio":          paciente["servicio"],
        "cama":              paciente["cama"],
        "paciente":          paciente["nombre"],
        "nss":               paciente["nss"],
        "medicamento":       medicamento["clave"],
        "nombre_medicamento": medicamento["nombre"],
        "cantidad":           cantidad,
        "cantidad_recibida":  0,
        "cantidad_pendiente": cantidad,
        "turno":             turno,
        "usuario":           usuario,
        "tipo":              tipo,
        "estado":            "PENDIENTE"
    }

    solicitudes.append(nueva_solicitud)
    contador_solicitudes += 1

    # [PER-01] Revertir si el guardado falla
    if not guardar_datos():
        solicitudes.remove(nueva_solicitud)
        contador_solicitudes -= 1
        print("Error: la solicitud no se registró porque el guardado falló.")
        return None

    print(f"\nSolicitud registrada correctamente. Folio: {folio}")
    return nueva_solicitud


# ============================================================
# 6. MÓDULO DE PROCESAMIENTO
# ============================================================

# ------------------------------------------------------------
# 6.1 BUSCAR SOLICITUD POR FOLIO (uso interno)
# ------------------------------------------------------------

def buscar_solicitud(folio: str):
    """
    Busca una solicitud por su folio.

    Retorna el diccionario de la solicitud o None si no existe.
    """
    for sol in solicitudes:
        if sol["folio"] == folio:
            return sol
    return None


# ------------------------------------------------------------
# 6.2 MOSTRAR SOLICITUD
# ------------------------------------------------------------

def mostrar_solicitud(solicitud: dict):
    """Imprime los campos principales de una solicitud."""

    print("\n========== SOLICITUD ==========")
    print(f"Folio: {solicitud['folio']}")
    print(f"Servicio: {solicitud['servicio']}")
    print(f"Cama: {solicitud['cama']}")
    print(f"Paciente: {solicitud['paciente']}")
    print(f"NSS: {solicitud['nss']}")
    print(f"Medicamento: {solicitud['nombre_medicamento']}")
    print(f"Clave: {solicitud['medicamento']}")
    print(f"Cantidad solicitada: {solicitud['cantidad']}")
    print(f"Turno: {solicitud['turno']}")
    print(f"Usuario: {solicitud['usuario']}")
    print(f"Tipo: {solicitud['tipo']}")
    print(f"Estado actual: {solicitud['estado']}")


# ------------------------------------------------------------
# 6.3 PROCESAR RESPUESTA DE FARMACIA
# ------------------------------------------------------------

def procesar_solicitud(folio=None):
    """
    Registra la respuesta de farmacia a una solicitud PENDIENTE.

    Validaciones de formato [REG-01]:
      - Folio  : RE_FOLIO         (SOL- seguido de ≥4 dígitos).
      - Opción : RE_FARMACIA_OPC  (1 = Surtida, 2 = Negada).

    Validaciones de negocio:
      - La solicitud debe existir y estar en estado PENDIENTE.

    Persistencia [PER-01]:
      - Si guardar_datos() falla, el estado se restaura a "PENDIENTE".

    Retorna la solicitud actualizada o None si algún paso falla.
    """
    print("\n========== PROCESAR SOLICITUD ==========")

    if folio is None:
        folio = leer_con_patron(
            "Ingrese el folio de la solicitud: ",
            RE_FOLIO,
            "el folio debe tener el formato SOL-NNNN (al menos 4 dígitos)"
        )
        if folio is None:
            return None

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

    opcion = leer_con_patron(
        "Seleccione una opción: ",
        RE_FARMACIA_OPC,
        "ingrese 1 (Surtida) o 2 (Negada)"
    )
    if opcion is None:
        return None

    estado_anterior = solicitud["estado"]

    if opcion == "1":
        solicitud["estado"] = "SURTIDA"
        print("\nSolicitud marcada como SURTIDA; pendiente de recepción física.")
    else:
        solicitud["estado"] = "NEGADA"
        print("\nSolicitud marcada como NEGADA; no procede la recepción física.")

    # [PER-01] Revertir si el guardado falla
    if not guardar_datos():
        solicitud["estado"] = estado_anterior
        print("Error: el estado no se guardó. Se restauró el estado anterior.")
        return None

    print(f"Folio {solicitud['folio']} actualizado correctamente.")
    return solicitud


# ------------------------------------------------------------
# 6.4 REGISTRAR RECEPCIÓN FÍSICA
# ------------------------------------------------------------

def registrar_recepcion(folio=None):
    """
    Registra la recepción física de medicamentos de una solicitud SURTIDA.

    Flujo:
      1. Busca la solicitud por folio.
      2. Verifica que su estado sea SURTIDA.
      3. Localiza el medicamento en el inventario.
      4. Solicita la cantidad recibida (0 ≤ x ≤ cantidad solicitada).
      5. Actualiza stock, cantidades y estado.
      6. Persiste con reversión ante fallo.

    Validaciones de formato [REG-01]:
      - Folio            : RE_FOLIO.
      - Cantidad recibida: RE_CANTIDAD_GE0 + rango de negocio.

    Persistencia [PER-01]:
      - Si guardar_datos() falla se restauran los valores del medicamento
        y de la solicitud antes de retornar None.

    Retorna la solicitud actualizada o None si algún paso falla.
    """
    print("\n========== REGISTRAR RECEPCIÓN ==========")

    if folio is None:
        folio = leer_con_patron(
            "Ingrese el folio de la solicitud: ",
            RE_FOLIO,
            "el folio debe tener el formato SOL-NNNN (al menos 4 dígitos)"
        )
        if folio is None:
            return None

    solicitud = buscar_solicitud(folio)
    if solicitud is None:
        print("Error: solicitud no encontrada.")
        return None

    mostrar_solicitud(solicitud)

    if solicitud["estado"] != "SURTIDA":
        print("Error: solo se puede recibir una solicitud surtida por farmacia.")
        return None

    medicamento_encontrado = buscar_medicamento(solicitud["medicamento"])
    if medicamento_encontrado is None:
        print("Error: medicamento activo no encontrado en el inventario.")
        return None

    print("\n========== INVENTARIO ==========")
    print(f"Medicamento: {medicamento_encontrado['nombre']}")
    print(f"Stock actual: {medicamento_encontrado['stock_actual']}")

    # Validación de cantidad recibida con reintentos
    cantidad_recibida = None
    for _ in range(3):
        cantidad_raw = leer_con_patron(
            "Ingrese la cantidad recibida físicamente: ",
            RE_CANTIDAD_GE0,
            "ingrese un número entero no negativo"
        )
        if cantidad_raw is None:
            return None
        valor = int(cantidad_raw)
        if not (0 <= valor <= solicitud["cantidad"]):
            print(
                f"Error: la cantidad debe estar entre 0 y "
                f"{solicitud['cantidad']}."
            )
            continue
        cantidad_recibida = valor
        break

    if cantidad_recibida is None:
        print("Demasiados intentos. Operación cancelada.")
        return None

    # ── Guardar valores anteriores para revertir si el guardado falla ──
    stock_anterior             = medicamento_encontrado["stock_actual"]
    cantidad_recibida_anterior = solicitud["cantidad_recibida"]
    cantidad_pendiente_anterior = solicitud["cantidad_pendiente"]
    estado_anterior            = solicitud["estado"]

    cantidad_pendiente = solicitud["cantidad"] - cantidad_recibida
    if cantidad_recibida == 0:
        estado_final = "NEGADA"
    elif cantidad_pendiente > 0:
        estado_final = "SURTIDA_PARCIAL"
    else:
        estado_final = "SURTIDA"

    medicamento_encontrado["stock_actual"] += cantidad_recibida
    solicitud["cantidad_recibida"]  = cantidad_recibida
    solicitud["cantidad_pendiente"] = cantidad_pendiente
    solicitud["estado"]             = estado_final

    # [PER-01] Revertir si el guardado falla
    if not guardar_datos():
        medicamento_encontrado["stock_actual"] = stock_anterior
        solicitud["cantidad_recibida"]  = cantidad_recibida_anterior
        solicitud["cantidad_pendiente"] = cantidad_pendiente_anterior
        solicitud["estado"]             = estado_anterior
        print(
            "Error: la recepción no se guardó. "
            "Se restauraron los valores anteriores."
        )
        return None

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
# 7. MÓDULO DE CONSULTAS
# ============================================================

# ------------------------------------------------------------
# 7.1 CONSULTAR SOLICITUDES
# ------------------------------------------------------------

def consultar_solicitudes():
    """Muestra todas las solicitudes registradas con sus estados."""

    print("\n========== SOLICITUDES REGISTRADAS ==========")

    if not solicitudes:
        print("No existen solicitudes registradas.")
        return

    for sol in solicitudes:
        print("-" * 50)
        print(f"Folio: {sol['folio']}")
        print(f"Servicio: {sol['servicio']}")
        print(f"Cama: {sol['cama']}")
        print(f"Paciente: {sol['paciente']}")
        print(f"Medicamento: {sol['nombre_medicamento']}")
        print(f"Cantidad solicitada: {sol['cantidad']}")
        print(f"Cantidad recibida: {sol.get('cantidad_recibida', 0)}")
        print(f"Cantidad pendiente: {sol.get('cantidad_pendiente', sol['cantidad'])}")
        print(f"Estado: {sol['estado']}")

    print("-" * 50)


# ------------------------------------------------------------
# 7.2 CONSULTAR INVENTARIO
# ------------------------------------------------------------

def consultar_inventario():
    """Muestra el inventario actual de medicamentos activos."""

    print("\n========== INVENTARIO ACTUAL ==========")

    medicamentos_activos = [m for m in medicamentos if m["activo"]]

    if not medicamentos_activos:
        print("No existen medicamentos activos.")
        return

    for m in medicamentos_activos:
        print("-" * 50)
        print(f"Clave: {m['clave']}")
        print(f"Medicamento: {m['nombre']}")
        print(f"Presentación: {m['presentacion']}")
        print(f"Unidad física: {m['unidad_fisica']}")
        print(f"Stock actual: {m['stock_actual']}")
        print(f"Stock objetivo: {m['stock_objetivo']}")
        faltante = m["stock_objetivo"] - m["stock_actual"]
        if faltante > 0:
            print(f"Faltante para stock objetivo: {faltante}")
        else:
            print("Stock objetivo cubierto.")

    print("-" * 50)


# ============================================================
# 8. UTILIDADES
# ============================================================

def limpiar_registros():
    """
    Elimina todas las solicitudes y reinicia el contador, previa confirmación.

    Validaciones de formato [REG-01]:
      - Confirmación: RE_CONFIRMACION_SN (s/n).

    Persistencia [PER-01]:
      - Sigue el patrón de reversión original: si el guardado falla,
        se restauran la lista y el contador.
    """
    global contador_solicitudes

    confirmacion = leer_con_patron(
        "Esto eliminará todo el historial de solicitudes. "
        "¿Desea continuar? (s/n): ",
        RE_CONFIRMACION_SN,
        "responda s o n"
    )
    if confirmacion is None:
        return

    if confirmacion.lower() != "s":
        print("Limpieza cancelada.")
        return

    solicitudes_anteriores = solicitudes.copy()
    contador_anterior      = contador_solicitudes
    solicitudes.clear()
    contador_solicitudes = 1

    if guardar_datos():
        print("Historial de solicitudes eliminado correctamente.")
    else:
        solicitudes.extend(solicitudes_anteriores)
        contador_solicitudes = contador_anterior
        print(
            "No se limpiaron los registros porque no se pudieron "
            "guardar los cambios."
        )


# ============================================================
# 9. MENÚ PRINCIPAL
# ============================================================

def menu_principal():
    """
    Presenta el menú interactivo de SMART CENDIS y despacha las opciones.

    Validaciones de formato [REG-01]:
      - Opción del menú: RE_MENU (0–11).
    """

    while True:

        print("\n")
        print("=" * 50)
        print("              SMART CENDIS")
        print("=" * 50)
        print("Sistema de Gestión Digital de Solicitudes,")
        print("Abastecimiento y Control de Inventario")
        print("=" * 50)
        print("\n 1. Registrar medicamento")
        print(" 2. Consultar medicamentos")
        print(" 3. Modificar medicamento")
        print(" 4. Desactivar medicamento")
        print(" 5. Consultar paciente")
        print(" 6. Registrar solicitud")
        print(" 7. Procesar solicitud")
        print(" 8. Registrar recepción")
        print(" 9. Consultar solicitudes")
        print("10. Consultar inventario")
        print("11. Limpiar historial de solicitudes")
        print(" 0. Salir")
        print("=" * 50)

        opcion = leer_con_patron(
            "Seleccione una opción: ",
            RE_MENU,
            "ingrese un número entre 0 y 11"
        )

        if opcion is None:
            # leer_con_patron ya imprimió el error; volver al menú.
            input("\nPresione ENTER para continuar...")
            continue

        acciones = {
            "1":  registrar_medicamento,
            "2":  consultar_medicamentos,
            "3":  modificar_medicamento,
            "4":  eliminar_medicamento,
            "5":  consultar_paciente,
            "6":  registrar_solicitud,
            "7":  procesar_solicitud,
            "8":  registrar_recepcion,
            "9":  consultar_solicitudes,
            "10": consultar_inventario,
            "11": limpiar_registros,
        }

        if opcion == "0":
            print("\nSaliendo de SMART CENDIS...")
            print("Sistema finalizado correctamente.")
            break

        accion = acciones.get(opcion)
        if accion:
            accion()

        input("\nPresione ENTER para continuar...")


# ============================================================
# 10. EJECUCIÓN DEL SISTEMA
# ============================================================

if __name__ == "__main__":
    cargar_datos()
    menu_principal()
