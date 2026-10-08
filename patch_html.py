#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_html.py  —  Parcheo quirurgico de smartcendis_web.html
Lee la copia original (index.html), aplica todos los cambios documentados
y escribe el resultado en smartcendis_web.html (UTF-8).

CAMBIOS APLICADOS:
  1  - Versión Web Beta (en lugar de v3.1)
  2  - Eliminar referencias a API/transmisión real
  3  - "Sistema en Línea" → "Demo operativa"
  4  - guardarEstadoSeguro() centralizada con try/catch
  5  - Rollback en operaciones críticas
  6  - loadState() con recuperación explícita ante datos corruptos
  9  - Validaciones reforzadas en pedido colectivo
  15 - Documentar limitaciones de la beta en comentarios JS y sidebar
"""

import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC  = r"c:\Users\Asjer\OneDrive\Desktop\Laboratorio\index.html"
DEST = r"c:\Users\Asjer\OneDrive\Desktop\Laboratorio\smartcendis_web.html"

with open(SRC, encoding="utf-8") as f:
    content = f.read()

print(f"Archivo fuente: {SRC}")
print(f"Longitud inicial: {len(content)} chars\n")

errors = []

def patch(label, old, new, allow_missing=False):
    global content
    if old in content:
        content = content.replace(old, new)
        print(f"[OK] {label}")
    elif allow_missing:
        print(f"[WARN] {label} - ya aplicado o no encontrado (omitido)")
    else:
        print(f"[ERROR] {label}")
        errors.append(label)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 1 y 15: Versión e info de demo en el sidebar footer
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C1/15: Footer sidebar: SMART CENDIS — Web Beta e info demo",
    '''    <div class="px-5 py-4 border-t border-[#cbd5e1] bg-[#f8fafc]">
      <p class="text-xs font-semibold text-[#0f172a]">SMART CENDIS v3.1</p>
      <p class="text-xs text-[#64748b]">Etapa 3 — Auditoría & Colectivos</p>
    </div>''',
    '''    <div class="px-5 py-4 border-t border-[#cbd5e1] bg-[#f8fafc]">
      <p class="text-xs font-semibold text-[#0f172a]">SMART CENDIS — Web Beta</p>
      <p class="text-xs text-[#64748b]">Interfaz gráfica de demostración · Etapa 3</p>
      <p class="text-[10px] text-[#94a3b8] mt-1.5 leading-tight">🟢 Demo operativa · localStorage<br>Núcleo Python v3.0.0 separado</p>
    </div>'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 3: "Sistema en Línea" → "Demo operativa"
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C3: Indicador 'Sistema en Línea' → 'Demo operativa'",
    'title="Sistema en Línea"',
    'title="🟢 Demo operativa — Modo demostración local (localStorage)"'
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: badges – lenguaje API → lenguaje honesto
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C2: Badge TRANSMITIDO → Registrado para Farmacia",
    "TRANSMITIDO:                ['badge-purple', '📡 Transmitido a Farmacia'],",
    "TRANSMITIDO:                ['badge-purple', '📋 Registrado para Farmacia'],"
)

patch(
    "C2: Badge ENVIADO_FARMACIA → Preparado para Farmacia",
    "ENVIADO_FARMACIA:           ['badge-purple', '📡 En Cola de Farmacia'],",
    "ENVIADO_FARMACIA:           ['badge-purple', '📋 Preparado para Farmacia'],"
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: botón "Transmitir y Generar Formato Oficial"
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C2: Botón 'Transmitir y Generar' → 'Registrar Pedido y Generar'",
    "Transmitir y Generar Formato Oficial",
    "Registrar Pedido y Generar Formato Oficial"
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: api_ack → ref_local en el objeto nuevoColectivo
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C2: campo api_ack → ref_local",
    "api_ack: `ACK-HTTP200-${Math.random().toString(36).substring(2, 9).toUpperCase()}`",
    "ref_local: `REG-LOCAL-${Math.random().toString(36).substring(2, 9).toUpperCase()}`"
)

# (Nota: El toast de transmitirColectivo se actualiza junto con el rollback en C5)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: Estado del pedido en formato colectivo — "Transmitido Electrónicamente"
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C2: Texto 'Transmitido Electrónicamente' en formato imprimible",
    "<span class=\"font-bold text-purple-700\">Transmitido Electrónicamente</span>",
    "<span class=\"font-bold text-purple-700\">Registrado — Formato físico listo para Farmacia Central</span>"
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: Etiqueta "Transmisión API:" en cabecera del formato imprimible
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C2: Etiqueta 'Transmisión API:' → 'Ref. Registro Local:'",
    "<strong class=\"text-[#475569]\">Transmisión API:</strong> <span class=\"font-mono text-emerald-700 font-bold\">${col.api_ack}</span>",
    "<strong class=\"text-[#475569]\">Ref. Registro Local:</strong> <span class=\"font-mono text-emerald-700 font-bold\">${col.ref_local}</span>"
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: Aviso normativo del formato colectivo — eliminar "transmitido a la cola"
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C2: Aviso normativo — eliminar referencia a cola de Farmacia",
    "Este pedido colectivo ha sido registrado exitosamente en el sistema digital y transmitido a la cola de Farmacia Central. Sin embargo, conforme a la normativa hospitalaria vigente, <strong>debe IMPRIMIRSE este formato físico y presentarse con firmas autógrafas ante la ventanilla de Farmacia Central</strong> para la dispensación física de los insumos.",
    "Este pedido colectivo ha sido registrado exitosamente en el sistema local. Conforme a la normativa hospitalaria vigente, <strong>debe IMPRIMIRSE este formato físico y presentarse con firmas autógrafas ante la ventanilla de Farmacia Central</strong> para la dispensación física de los insumos. <em>Nota: La integración API con Farmacia Central está prevista como evolución futura del sistema.</em>"
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: Botón "API Payload (JSON)" → "Ver Datos Locales (JSON)"
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C2: Botón 'API Payload (JSON)' → 'Ver Datos Locales (JSON)'",
    "API Payload (JSON)",
    "Ver Datos Locales (JSON)"
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: Alert en verPayloadJson — eliminar lenguaje API ficticio
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C2: Alert de verPayloadJson — lenguaje API ficticio → honesto",
    "alert(`PAYLOAD API INSTITUCIONAL (Simulada):\\n\\nPOST /api/v1/farmacia/pedidos-colectivos\\n` + JSON.stringify(col, null, 2));",
    "alert(`REGISTRO LOCAL DEL PEDIDO COLECTIVO (formato JSON):\\n\\nNota: Esta es la representación interna de la beta.\\nLa integración API con Farmacia Central es una evolución futura.\\n\\n` + JSON.stringify(col, null, 2));"
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIOS 4, 5, 6: Reemplazar bloque de persistencia completo
# ─────────────────────────────────────────────────────────────────────────────

OLD_PERSISTENCE = '''let state = loadState();

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (!parsed.colectivos) parsed.colectivos = [];
      if (!parsed.contador_colectivos) parsed.contador_colectivos = 1;
      return parsed;
    }
  } catch(e) {}
  return JSON.parse(JSON.stringify(INITIAL_STATE));
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function resetData() {
  if (!confirm(\'¿Reiniciar todos los datos al estado institucional de prueba?\')) return;
  state = JSON.parse(JSON.stringify(INITIAL_STATE));
  saveState();
  toast(\'Datos reiniciados correctamente.\', \'success\');
  renderPage(currentPage);
}'''

NEW_PERSISTENCE = '''// ──────────────────────────────────────────────────
//  PERSISTENCIA ROBUSTA — Cambios 4, 5, 6 (Etapa 3)
//  Filosofía idéntica al núcleo Python v3.0.0:
//  - Recuperación explícita ante datos corruptos
//  - guardarEstadoSeguro() con try/catch centralizado
//  - Rollback ante fallo de almacenamiento
// ──────────────────────────────────────────────────

/**
 * CAMBIO 6: Carga el estado desde localStorage con recuperación explícita.
 * Si los datos están corruptos o la estructura es inválida, informa al usuario
 * y carga el estado demo en lugar de fallar silenciosamente.
 */
function loadState() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    // Primera ejecución — no hay datos previos, es normal
    return JSON.parse(JSON.stringify(INITIAL_STATE));
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch(e) {
    // CAMBIO 6: Datos corruptos detectados — informar y cargar estado demo
    console.warn(\'[SMART CENDIS] localStorage con datos inválidos. Se carga estado demo.\', e);
    setTimeout(() => {
      toast(\'⚠ No fue posible recuperar los datos locales. Se cargó el estado de demostración.\', \'error\');
    }, 600);
    localStorage.removeItem(STORAGE_KEY);
    return JSON.parse(JSON.stringify(INITIAL_STATE));
  }
  // CAMBIO 6: Validar estructura mínima requerida
  if (!parsed || typeof parsed !== \'object\' ||
      !Array.isArray(parsed.medicamentos) ||
      !Array.isArray(parsed.solicitudes)) {
    console.warn(\'[SMART CENDIS] Estructura de datos inválida. Se carga estado demo.\');
    setTimeout(() => {
      toast(\'⚠ Estructura de datos local inválida. Se cargó el estado de demostración.\', \'error\');
    }, 600);
    localStorage.removeItem(STORAGE_KEY);
    return JSON.parse(JSON.stringify(INITIAL_STATE));
  }
  // Migración de campos faltantes (compatibilidad hacia adelante)
  if (!parsed.colectivos)           parsed.colectivos = [];
  if (!parsed.contador_colectivos)  parsed.contador_colectivos = 1;
  if (!parsed.pacientes)            parsed.pacientes = JSON.parse(JSON.stringify(INITIAL_STATE.pacientes));
  return parsed;
}

let state = loadState();

/**
 * CAMBIO 4: Función centralizada de persistencia con manejo de excepciones.
 * Sustituye el uso directo de localStorage.setItem() en toda la aplicación.
 * @returns {boolean} true si el guardado fue exitoso, false si ocurrió un error.
 */
function guardarEstadoSeguro() {
  try {
    const json = JSON.stringify(state);
    localStorage.setItem(STORAGE_KEY, json);
    return true;
  } catch(e) {
    console.error(\'[SMART CENDIS] Error al guardar estado en localStorage:\', e);
    toast(\'⚠ Error al guardar los datos. Los cambios no fueron persistidos.\', \'error\');
    return false;
  }
}

// Alias de compatibilidad — saveState() delega a guardarEstadoSeguro()
function saveState() {
  return guardarEstadoSeguro();
}

function resetData() {
  if (!confirm(\'¿Reiniciar todos los datos al estado de demostración?\')) return;
  // CAMBIO 5: Rollback si falla el guardado
  const anterior = JSON.stringify(state);
  state = JSON.parse(JSON.stringify(INITIAL_STATE));
  if (!guardarEstadoSeguro()) {
    state = JSON.parse(anterior);
    toast(\'No se pudo reiniciar. El estado anterior fue restaurado.\', \'error\');
    return;
  }
  toast(\'Datos reiniciados al estado de demostración.\', \'success\');
  renderPage(currentPage);
}'''

patch("C4/5/6: Bloque de persistencia robusta", OLD_PERSISTENCE, NEW_PERSISTENCE)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 5: Rollback en guardarSolicitud()
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C5: Rollback en guardarSolicitud()",
    '''  state.solicitudes.push({
    folio, servicio: pac.servicio, cama: pac.cama,
    paciente: pac.nombre, nss: pac.nss,
    medicamento: med.clave, nombre_medicamento: med.nombre,
    cantidad: parseInt(cant), cantidad_recibida: 0, cantidad_pendiente: parseInt(cant),
    turno, usuario, tipo, estado: 'PENDIENTE'
  });
  saveState(); closeModal(); renderPage('solicitudes');
  toast(`Solicitud de piso ${folio} registrada en CENDIS.`, 'success');
}''',
    '''  // CAMBIO 5: Guardar estado anterior para rollback
  const estadoAnteriorSol = JSON.stringify(state);
  state.solicitudes.push({
    folio, servicio: pac.servicio, cama: pac.cama,
    paciente: pac.nombre, nss: pac.nss,
    medicamento: med.clave, nombre_medicamento: med.nombre,
    cantidad: parseInt(cant), cantidad_recibida: 0, cantidad_pendiente: parseInt(cant),
    turno, usuario, tipo, estado: 'PENDIENTE'
  });
  if (!guardarEstadoSeguro()) {
    // CAMBIO 5: Rollback — la solicitud NO queda registrada
    state = JSON.parse(estadoAnteriorSol);
    toast('Error al persistir la solicitud. Operación revertida.', 'error');
    return;
  }
  closeModal(); renderPage('solicitudes');
  toast(`Solicitud de piso ${folio} registrada en CENDIS.`, 'success');
}'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 5: Rollback en guardarMed()
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C5: Rollback en guardarMed()",
    '''  state.medicamentos.push({ clave, nombre, presentacion: pres, unidad_fisica: unidad,
    stock_actual: parseInt(stockAct), stock_objetivo: parseInt(stockObj), activo: true });
  saveState(); closeModal(); renderPage('medicamentos');
  toast('Medicamento registrado en catálogo correctamente.', 'success');
}''',
    '''  // CAMBIO 5: Guardar estado anterior para rollback
  const estadoAnteriorMed = JSON.stringify(state);
  state.medicamentos.push({ clave, nombre, presentacion: pres, unidad_fisica: unidad,
    stock_actual: parseInt(stockAct), stock_objetivo: parseInt(stockObj), activo: true });
  if (!guardarEstadoSeguro()) {
    state = JSON.parse(estadoAnteriorMed);
    toast('Error al registrar medicamento. Operación revertida.', 'error');
    return;
  }
  closeModal(); renderPage('medicamentos');
  toast('Medicamento registrado en catálogo correctamente.', 'success');
}'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 5: Rollback en guardarEdicion()
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C5: Rollback en guardarEdicion()",
    '''  const m = state.medicamentos.find(x => x.clave === clave);
  m.nombre = nombre; m.stock_objetivo = parseInt(stock);
  saveState(); closeModal(); renderPage('medicamentos');
  toast('Medicamento actualizado exitosamente.', 'success');
}''',
    '''  const m = state.medicamentos.find(x => x.clave === clave);
  // CAMBIO 5: Guardar estado anterior para rollback
  const estadoAnteriorEdit = JSON.stringify(state);
  m.nombre = nombre; m.stock_objetivo = parseInt(stock);
  if (!guardarEstadoSeguro()) {
    state = JSON.parse(estadoAnteriorEdit);
    toast('Error al modificar medicamento. Operación revertida.', 'error');
    return;
  }
  closeModal(); renderPage('medicamentos');
  toast('Medicamento actualizado exitosamente.', 'success');
}'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 5: Rollback en desactivarMed()
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C5: Rollback en desactivarMed()",
    '''  if (!confirm(`¿Confirmar baja lógica de "${m.nombre}"?`)) return;
  m.activo = false;
  saveState(); renderPage('medicamentos');
  toast('Medicamento desactivado del catálogo.', 'info');
}''',
    '''  if (!confirm(`¿Confirmar baja lógica de "${m.nombre}"?`)) return;
  // CAMBIO 5: Rollback si falla el guardado
  const estadoAnteriorDesact = JSON.stringify(state);
  m.activo = false;
  if (!guardarEstadoSeguro()) {
    state = JSON.parse(estadoAnteriorDesact);
    toast('Error al desactivar medicamento. Operación revertida.', 'error');
    return;
  }
  renderPage('medicamentos');
  toast('Medicamento desactivado del catálogo.', 'info');
}'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 5: Rollback en activarMed()
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C5: Rollback en activarMed()",
    '''  const m = state.medicamentos.find(x => x.clave === clave);
  m.activo = true;
  saveState(); renderPage('medicamentos');
  toast('Medicamento reactivado.', 'success');
}''',
    '''  const m = state.medicamentos.find(x => x.clave === clave);
  // CAMBIO 5: Rollback si falla el guardado
  const estadoAnteriorActiv = JSON.stringify(state);
  m.activo = true;
  if (!guardarEstadoSeguro()) {
    state = JSON.parse(estadoAnteriorActiv);
    toast('Error al activar medicamento. Operación revertida.', 'error');
    return;
  }
  renderPage('medicamentos');
  toast('Medicamento reactivado.', 'success');
}'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 5: Rollback en responderFarmacia() (dictamen)
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C5: Rollback en responderFarmacia()",
    '''  sol.estado = respuesta;
  saveState(); renderPage('procesar');
  toast(`Solicitud ${folio} actualizada como ${respuesta}.`, respuesta === 'SURTIDA' ? 'success' : 'error');
}''',
    '''  // CAMBIO 5: Rollback si falla el guardado del dictamen
  const estadoAnteriorResp = JSON.stringify(state);
  sol.estado = respuesta;
  if (!guardarEstadoSeguro()) {
    state = JSON.parse(estadoAnteriorResp);
    toast('Error al guardar el dictamen. Operación revertida.', 'error');
    return;
  }
  renderPage('procesar');
  toast(`Solicitud ${folio} dictaminada como ${respuesta}.`, respuesta === 'SURTIDA' ? 'success' : 'error');
}'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 5/7/8: Rollback en registrarRecepcion() — operación crítica de inventario
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C5/7/8: Rollback en registrarRecepcion() — inventario sólo cambia con recepción física confirmada",
    '''  const pendiente = sol.cantidad - recibido;
  sol.cantidad_recibida  = recibido;
  sol.cantidad_pendiente = pendiente;
  sol.estado = recibido === 0 ? 'NEGADA' : pendiente > 0 ? 'SURTIDA_PARCIAL' : 'SURTIDA';
  if (med) med.stock_actual += recibido;
  saveState(); renderPage('recepcion');
  toast(`Recepción registrada (${sol.estado}). Stock actualizado.`, 'success');
}''',
    '''  // CAMBIO 5: Guardar estado ANTES de modificar inventario (operación crítica)
  // CAMBIO 7/8: Solo la recepción física modifica el inventario — nunca la solicitud
  const estadoAnteriorRec = JSON.stringify(state);
  const pendiente = sol.cantidad - recibido;
  sol.cantidad_recibida  = recibido;
  sol.cantidad_pendiente = pendiente;
  sol.estado = recibido === 0 ? 'NEGADA' : pendiente > 0 ? 'SURTIDA_PARCIAL' : 'SURTIDA';
  if (med) med.stock_actual += recibido;   // Inventario actualizado SOLO por recepción física
  if (!guardarEstadoSeguro()) {
    // CAMBIO 5: Rollback completo — el inventario NO queda modificado parcialmente
    state = JSON.parse(estadoAnteriorRec);
    toast('Error al guardar la recepción. El inventario NO fue modificado (rollback aplicado).', 'error');
    return;
  }
  renderPage('recepcion');
  toast(`Recepción física registrada (${sol.estado}). Stock CENDIS actualizado.`, 'success');
}'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 5: Rollback en transmitirColectivo()
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C5: Rollback en transmitirColectivo()",
    '''  state.colectivos.push(nuevoColectivo);
  saveState();

  toast(`Pedido Colectivo ${folio} transmitido vía API a Farmacia Central.`, 'success');

  // Mostrar el formato oficial impreso/visualizable
  verFormatoColectivo(folio);
}''',
    '''  // CAMBIO 5: Guardar estado anterior para rollback
  const estadoAnteriorCol = JSON.stringify(state);
  state.colectivos.push(nuevoColectivo);
  if (!guardarEstadoSeguro()) {
    state = JSON.parse(estadoAnteriorCol);
    toast('Error al registrar el pedido colectivo. Operación revertida.', 'error');
    return;
  }
  toast(`Pedido Colectivo ${folio} registrado. Formato físico listo para Farmacia Central.`, 'success');
  // Mostrar el formato oficial impreso/visualizable
  verFormatoColectivo(folio);
}'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 9: Validaciones reforzadas en transmitirColectivo()
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C9: Validaciones reforzadas del pedido colectivo (responsable, turno, prioridad, cantidades)",
    '''  if (!resp || resp.length < 3) {
    toast('Ingrese el nombre del responsable de CENDIS.', 'error');
    return;
  }

  // Recolectar items
  const items = [];
  state.medicamentos.filter(m => m.activo).forEach(m => {
    const input = document.getElementById(`col-cant-${m.clave}`);
    const cant = parseInt(input?.value || '0');
    if (cant > 0) {
      items.push({''',
    '''  // CAMBIO 9: Validaciones reforzadas del pedido colectivo
  if (!resp || resp.trim().length < 2) {
    toast('El nombre del responsable es obligatorio.', 'error');
    document.getElementById('col-resp')?.classList.add('error');
    return;
  }
  if (!RE.usuario.test(resp)) {
    toast('El nombre del responsable tiene un formato inválido.', 'error');
    document.getElementById('col-resp')?.classList.add('error');
    return;
  }
  const turnosValidos    = ['MATUTINO', 'VESPERTINO', 'NOCTURNO'];
  const prioridadesValidas = ['PROGRAMADO', 'CRITICO', 'URGENTE'];
  if (!turnosValidos.includes(turno)) {
    toast('Turno seleccionado inválido.', 'error'); return;
  }
  if (!prioridadesValidas.includes(prioridad)) {
    toast('Prioridad seleccionada inválida.', 'error'); return;
  }

  // CAMBIO 9: Recolectar items con validación de cantidades (enteros >= 0)
  const items = [];
  let cantidadInvalida = false;
  state.medicamentos.filter(m => m.activo).forEach(m => {
    const input = document.getElementById(`col-cant-${m.clave}`);
    const rawVal = (input?.value ?? '0').trim();
    if (!RE.cantidadGe0.test(rawVal)) {
      cantidadInvalida = true;
      input?.classList.add('error');
      return;
    }
    const cant = parseInt(rawVal);
    if (cant > 0) {
      items.push({'''
)

patch(
    "C9: Verificación de cantidadInvalida antes de continuar con el colectivo",
    '''  if (items.length === 0) {
    toast('Debe solicitar al menos una unidad de algún medicamento.', 'error');
    return;
  }''',
    '''  // CAMBIO 9: Verificar si alguna cantidad fue rechazada por formato inválido
  if (cantidadInvalida) {
    toast('Corrija las cantidades marcadas en rojo (deben ser enteros ≥ 0).', 'error');
    return;
  }
  if (items.length === 0) {
    toast('Debe solicitar al menos una unidad de algún medicamento.', 'error');
    return;
  }'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 15: Documentar limitaciones como comentario en JS antes de la inicialización
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "C15: Documentación de limitaciones de la beta en el código JS",
    '''// ──────────────────────────────────────────────────
//  INICIALIZACIÓN
// ──────────────────────────────────────────────────
goTo('dashboard');''',
    '''// ──────────────────────────────────────────────────
//  LIMITACIONES ACTUALES DE LA BETA WEB (Cambio 15)
//  Estas limitaciones son decisiones de alcance,
//  no fallas del sistema.
// ──────────────────────────────────────────────────
/*
 * SMART CENDIS — Web Beta · Limitaciones declaradas:
 *
 * 1. La beta utiliza localStorage del navegador (no base de datos real).
 * 2. No existe backend institucional ni servidor de aplicación.
 * 3. No existe conexión con sistemas IMSS ni con sistemas institucionales.
 * 4. No existe API real con Farmacia Central
 *    (prevista como evolución futura — Etapa 1 del proyecto).
 * 5. Los datos utilizados son datos de prueba/demostración,
 *    no datos reales de pacientes.
 * 6. La integración con sistemas institucionales está planteada
 *    para una futura etapa de evolución (definida en Etapa 1).
 * 7. El formato físico es el mecanismo de comunicación con Farmacia
 *    establecido para la primera versión del sistema (Etapa 1).
 * 8. Esta interfaz web es un PROTOTIPO COMPLEMENTARIO al núcleo Python v3.0.0;
 *    no lo reemplaza. Ambos respetan las mismas reglas de negocio:
 *    - La solicitud NO modifica el inventario.
 *    - Solo la recepción física actualiza el stock CENDIS.
 *    - La respuesta de Farmacia y la recepción física son pasos separados.
 */

// ──────────────────────────────────────────────────
//  INICIALIZACIÓN
// ──────────────────────────────────────────────────
goTo('dashboard');'''
)

# ─────────────────────────────────────────────────────────────────────────────
# CORRECCIÓN DE ESTABILIDAD: Unificar attachEvents y eliminar recursión infinita
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "Estabilidad: Unificar attachEvents para procesar y recepcion",
    '''function attachEvents(page) {
  if (page === 'procesar') {
    const sel = document.getElementById('pr-folio');
    if (sel) {
      sel.addEventListener('change', previsualizarSolicitud);
      previsualizarSolicitud();
    }
  }
}''',
    '''function attachEvents(page) {
  if (page === 'procesar') {
    const sel = document.getElementById('pr-folio');
    if (sel) {
      sel.addEventListener('change', previsualizarSolicitud);
      previsualizarSolicitud();
    }
  } else if (page === 'recepcion') {
    attachRecepcionEvents();
  }
}'''
)

patch(
    "Estabilidad: Eliminar sobrescritura recursiva de attachEvents",
    '''// Vinculación de eventos al renderizar
const _origAttach = attachEvents;
function attachEvents(page) {
  _origAttach(page);
  if (page === 'recepcion') attachRecepcionEvents();
}''',
    '''// Nota: Eventos unificados en attachEvents() sin recursión'''
)

# ─────────────────────────────────────────────────────────────────────────────
# Verificación y escritura final
# ─────────────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"[WARN] Se encontraron {len(errors)} errores. Revisa antes de guardar:")
    for e in errors:
        print(f"   [ERROR] {e}")
    print("\nNo se guardó el archivo.")
    sys.exit(1)

# Validar que el archivo sigue siendo UTF-8 válido
try:
    content.encode('utf-8')
    print("[OK] Contenido válido como UTF-8")
except UnicodeEncodeError as e:
    print(f"[ERROR] Error de codificación: {e}")
    sys.exit(1)

with open(DEST, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n[OK] Archivo guardado: {DEST}")
print(f"  Longitud final: {len(content)} chars")
print()
print("=" * 60)
print("PARCHEO COMPLETADO EXITOSAMENTE")
print("=" * 60)
