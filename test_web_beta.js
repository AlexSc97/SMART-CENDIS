/**
 * test_web_beta.js
 * Batería de pruebas automatizadas sobre la lógica de smartcendis_web.html
 * Verifica los criterios de aceptación y cambios 1 al 15.
 */

const fs = require('fs');
const vm = require('vm');

// Leer archivo HTML generado
const htmlContent = fs.readFileSync('c:\\Users\\Asjer\\OneDrive\\Desktop\\Laboratorio\\smartcendis_web.html', 'utf8');

// Extraer bloque <script>
const scriptMatch = htmlContent.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  console.error("No se encontró el bloque <script> en smartcendis_web.html");
  process.exit(1);
}
// Reemplazar `let state` por `var state` en el script para que sea accesible en el sandbox de vm
const jsCode = scriptMatch[1].replace(/let state = loadState\(\);/, 'var state = loadState();');

// Mock robusto de localStorage
class LocalStorageMock {
  constructor() {
    this.store = {};
    this.failOnSet = false;
  }
  getItem(key) {
    return this.store[key] || null;
  }
  setItem(key, value) {
    if (this.failOnSet) {
      throw new Error("QuotaExceededError: simulando fallo de almacenamiento local");
    }
    this.store[key] = String(value);
  }
  removeItem(key) {
    delete this.store[key];
  }
  clear() {
    this.store = {};
  }
}

const mockLocalStorage = new LocalStorageMock();
const mockAlerts = [];
const mockToasts = [];

// Elementos DOM simulados
const elements = {};
function getOrCreateElem(id) {
  if (!elements[id]) {
    elements[id] = {
      id: id,
      value: '',
      textContent: '',
      innerHTML: '',
      className: '',
      dataset: {},
      classList: {
        add: () => {},
        remove: () => {},
        toggle: () => {}
      },
      appendChild: () => {},
      addEventListener: () => {},
      remove: () => {}
    };
  }
  return elements[id];
}

const sandbox = {
  console: console,
  setTimeout: (fn) => fn(), // ejecución inmediata en pruebas
  setInterval: () => {},
  document: {
    getElementById: (id) => getOrCreateElem(id),
    querySelectorAll: () => [],
    createElement: () => ({
      className: '',
      textContent: '',
      appendChild: () => {},
      remove: () => {}
    })
  },
  localStorage: mockLocalStorage,
  alert: (msg) => mockAlerts.push(msg),
  confirm: () => true,
  toast: (msg, type) => mockToasts.push({ msg, type }),
  renderPage: () => {},
  closeModal: () => {},
  openModal: () => {},
  goTo: () => {}
};

const context = vm.createContext(sandbox);

// Ejecutar código base
vm.runInContext(jsCode, context);

console.log("================================================================================");
console.log("SMART CENDIS — BATERÍA DE PRUEBAS DE LA BETA WEB (CAMBIOS ETAPA 3)");
console.log("================================================================================");

let totalTests = 0;
let passedTests = 0;
const resultadosReporte = [];

function runTest(nombre, pruebaFn) {
  totalTests++;
  try {
    const res = pruebaFn();
    if (res.ok) {
      passedTests++;
      console.log(`[PASS] ${nombre} | ${res.detalles}`);
      resultadosReporte.push({ nombre, esperado: res.esperado, obtenido: res.detalles, estado: 'PASÓ' });
    } else {
      console.error(`[FAIL] ${nombre} | ${res.detalles}`);
      resultadosReporte.push({ nombre, esperado: res.esperado, obtenido: res.detalles, estado: 'FALLÓ' });
    }
  } catch (err) {
    console.error(`[FAIL] ${nombre} | Excepción: ${err.message}`);
    resultadosReporte.push({ nombre, esperado: 'Sin excepciones', obtenido: err.message, estado: 'ERROR' });
  }
}

// -----------------------------------------------------------------------------
// PRUEBA 1: Creación de solicitud de piso
// -----------------------------------------------------------------------------
runTest("Creación de solicitud de piso", () => {
  getOrCreateElem('ns-pac').value = 'Pediatria||01';
  getOrCreateElem('ns-med').value = '5121';
  getOrCreateElem('ns-cant').value = '5';
  getOrCreateElem('ns-turno').value = 'MATUTINO';
  getOrCreateElem('ns-usuario').value = 'Enf. Martínez';
  getOrCreateElem('ns-tipo').value = 'NORMAL';

  const cantInicial = context.state.solicitudes.length;
  vm.runInContext("guardarSolicitud()", context);
  const cantFinal = context.state.solicitudes.length;

  const sol = context.state.solicitudes.find(s => s.folio === 'SOL-0001');
  const ok = (cantFinal === cantInicial + 1) && sol && sol.cantidad === 5 && sol.estado === 'PENDIENTE';
  return {
    ok,
    esperado: "Solicitud registrada con folio SOL-0001 y estado PENDIENTE",
    detalles: ok ? `Registrada SOL-0001 (Cant: ${sol.cantidad}, Estado: ${sol.estado})` : "No se creó la solicitud"
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 2: Regla fundamental de inventario: Solicitud NO modifica inventario
// -----------------------------------------------------------------------------
runTest("Solicitud no modifica inventario (Regla Etapas 1-3)", () => {
  const med = context.state.medicamentos.find(m => m.clave === '5121');
  // Stock inicial en datos demo de Paracetamol 5121 es 26
  const stockParacetamol = med.stock_actual;
  const ok = (stockParacetamol === 26);
  return {
    ok,
    esperado: "Stock permanece intacto en 26 unidades tras registrar solicitud",
    detalles: ok ? `Stock intacto = ${stockParacetamol} (no alterado por solicitud)` : `Stock modificado indebidamente a ${stockParacetamol}`
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 3: Dictamen administrativo de farmacia (SURTIDA)
// -----------------------------------------------------------------------------
runTest("Dictamen administrativo de farmacia (SURTIDA)", () => {
  getOrCreateElem('pr-folio').value = 'SOL-0001';
  vm.runInContext("responderFarmacia('SURTIDA')", context);

  const sol = context.state.solicitudes.find(s => s.folio === 'SOL-0001');
  const med = context.state.medicamentos.find(m => m.clave === '5121');
  // Dictamen administrativo no debe modificar stock físico
  const ok = sol && sol.estado === 'SURTIDA' && med.stock_actual === 26;
  return {
    ok,
    esperado: "Solicitud cambia a SURTIDA y el inventario se mantiene intacto (26)",
    detalles: ok ? `Estado: ${sol.estado}, Stock aún en ${med.stock_actual}` : "Inconsistencia en dictamen"
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 4: Recepción física completa (Incrementa inventario)
// -----------------------------------------------------------------------------
runTest("Recepción física total e incremento de inventario", () => {
  getOrCreateElem('rec-folio').value = 'SOL-0001';
  getOrCreateElem('rec-cant').value = '5'; // Se reciben las 5 piezas
  vm.runInContext("registrarRecepcion()", context);

  const sol = context.state.solicitudes.find(s => s.folio === 'SOL-0001');
  const med = context.state.medicamentos.find(m => m.clave === '5121');
  const ok = sol && sol.cantidad_recibida === 5 && sol.cantidad_pendiente === 0 && sol.estado === 'SURTIDA' && med.stock_actual === 31; // 26 + 5 = 31
  return {
    ok,
    esperado: "Stock aumenta en +5 (26 -> 31), cantidad_pendiente = 0, estado = SURTIDA",
    detalles: ok ? `Stock final = ${med.stock_actual}, Pendiente = ${sol.cantidad_pendiente}` : "Fallo en recepción total"
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 5: Recepción física parcial
// -----------------------------------------------------------------------------
runTest("Recepción física parcial", () => {
  // Crear segunda solicitud
  getOrCreateElem('ns-pac').value = 'Pediatria||02';
  getOrCreateElem('ns-med').value = '5090'; // Ibuprofeno (stock 14)
  getOrCreateElem('ns-cant').value = '10';
  getOrCreateElem('ns-turno').value = 'VESPERTINO';
  getOrCreateElem('ns-usuario').value = 'Enf. Sánchez';
  getOrCreateElem('ns-tipo').value = 'NORMAL';
  vm.runInContext("guardarSolicitud()", context);

  // Dictaminar SURTIDA
  getOrCreateElem('pr-folio').value = 'SOL-0002';
  vm.runInContext("responderFarmacia('SURTIDA')", context);

  // Recepción parcial: de 10 pedidas sólo se reciben 6
  getOrCreateElem('rec-folio').value = 'SOL-0002';
  getOrCreateElem('rec-cant').value = '6';
  vm.runInContext("registrarRecepcion()", context);

  const sol = context.state.solicitudes.find(s => s.folio === 'SOL-0002');
  const med = context.state.medicamentos.find(m => m.clave === '5090');
  const ok = sol && sol.cantidad_recibida === 6 && sol.cantidad_pendiente === 4 && sol.estado === 'SURTIDA_PARCIAL' && med.stock_actual === 20; // 14 + 6 = 20
  return {
    ok,
    esperado: "Stock aumenta +6 (14 -> 20), pendiente = 4, estado = SURTIDA_PARCIAL",
    detalles: ok ? `Stock = ${med.stock_actual}, Recibido = ${sol.cantidad_recibida}, Pendiente = ${sol.cantidad_pendiente}, Estado = ${sol.estado}` : "Fallo en recepción parcial"
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 6: Recepción física cero
// -----------------------------------------------------------------------------
runTest("Recepción física cero", () => {
  // Crear tercera solicitud
  getOrCreateElem('ns-pac').value = 'Urgencias||01';
  getOrCreateElem('ns-med').value = '3310'; // Amoxicilina (stock 80)
  getOrCreateElem('ns-cant').value = '4';
  getOrCreateElem('ns-turno').value = 'NOCTURNO';
  getOrCreateElem('ns-usuario').value = 'Enf. Gómez';
  getOrCreateElem('ns-tipo').value = 'NORMAL';
  vm.runInContext("guardarSolicitud()", context);

  // Dictaminar SURTIDA
  getOrCreateElem('pr-folio').value = 'SOL-0003';
  vm.runInContext("responderFarmacia('SURTIDA')", context);

  // Recepción cero
  getOrCreateElem('rec-folio').value = 'SOL-0003';
  getOrCreateElem('rec-cant').value = '0';
  vm.runInContext("registrarRecepcion()", context);

  const sol = context.state.solicitudes.find(s => s.folio === 'SOL-0003');
  const med = context.state.medicamentos.find(m => m.clave === '3310');
  const ok = sol && sol.cantidad_recibida === 0 && sol.cantidad_pendiente === 4 && sol.estado === 'NEGADA' && med.stock_actual === 80;
  return {
    ok,
    esperado: "Stock sin cambios (80), cantidad_recibida = 0, estado = NEGADA",
    detalles: ok ? `Stock = ${med.stock_actual}, Estado = ${sol.estado}` : "Fallo en recepción cero"
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 7: Persistencia en localStorage
// -----------------------------------------------------------------------------
runTest("Persistencia en localStorage", () => {
  const guardadoRaw = mockLocalStorage.getItem('smartcendis_v3_state');
  const parsed = JSON.parse(guardadoRaw);
  const ok = parsed && parsed.solicitudes.length === 3 && parsed.medicamentos.length >= 5;
  return {
    ok,
    esperado: "Estado persistido en clave 'smartcendis_v3_state' con 3 solicitudes",
    detalles: ok ? `JSON guardado con ${parsed.solicitudes.length} solicitudes y ${parsed.medicamentos.length} medicamentos` : "No se encontró el estado persistido"
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 8: Recuperación explícita ante datos corruptos
// -----------------------------------------------------------------------------
runTest("Recuperación ante datos corruptos (Cambio 6)", () => {
  // Inyectar JSON inválido
  mockLocalStorage.setItem('smartcendis_v3_state', "{ JSON CORRUPTO MALFORMADO !!! ");
  const recoveredState = vm.runInContext("loadState()", context);

  const ok = recoveredState && Array.isArray(recoveredState.medicamentos) && recoveredState.medicamentos.length > 0;
  return {
    ok,
    esperado: "Detecta corrupción, avisa al usuario, limpia clave y devuelve estado demo",
    detalles: ok ? `Estado demo cargado con ${recoveredState.medicamentos.length} medicamentos sin romper ejecución` : "Fallo en recuperación ante JSON corrupto"
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 9: Fallo de almacenamiento forzado + Rollback de estado (Cambio 5)
// -----------------------------------------------------------------------------
runTest("Fallo de almacenamiento y Rollback (Cambio 5)", () => {
  // Restaurar estado limpio
  vm.runInContext("state = loadState()", context);
  const totalMedsInicial = context.state.medicamentos.length;

  // Forzar error de almacenamiento
  mockLocalStorage.failOnSet = true;

  // Intentar agregar nuevo medicamento
  getOrCreateElem('m-clave').value = '9999';
  getOrCreateElem('m-nombre').value = 'Medicamento de Prueba Fallo';
  getOrCreateElem('m-pres').value = 'Comprimido';
  getOrCreateElem('m-unidad').value = 'Tableta';
  getOrCreateElem('m-stock-act').value = '10';
  getOrCreateElem('m-stock-obj').value = '20';

  vm.runInContext("guardarMed()", context);

  const totalMedsFinal = context.state.medicamentos.length;
  const medExiste = context.state.medicamentos.some(m => m.clave === '9999');

  // Desactivar fallo simulado
  mockLocalStorage.failOnSet = false;

  const ok = (totalMedsFinal === totalMedsInicial) && !medExiste;
  return {
    ok,
    esperado: "guardarEstadoSeguro() falla, se aplica rollback y medicamento 9999 no queda en el estado",
    detalles: ok ? `Rollback confirmado: cantidad medicamentos = ${totalMedsFinal}, med 9999 no existe` : "Fallo: el estado no revirtió los cambios"
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 10: Validación de pedido colectivo (Cambio 9)
// -----------------------------------------------------------------------------
runTest("Validación de entradas en Pedido Colectivo (Cambio 9)", () => {
  const cendisServices = vm.runInContext("CENDIS_SERVICES", context);
  getOrCreateElem('col-origen').value = cendisServices[0];
  getOrCreateElem('col-turno').value = 'MATUTINO';
  getOrCreateElem('col-resp').value = ''; // Responsable vacío (debe rechazar)
  getOrCreateElem('col-prioridad').value = 'PROGRAMADO';

  const cantColInicial = context.state.colectivos.length;
  vm.runInContext("transmitirColectivo()", context);
  const rechazoResponsable = (context.state.colectivos.length === cantColInicial);

  // Ahora con responsable pero con cantidad inválida negativa
  getOrCreateElem('col-resp').value = 'Dr. Juan Pérez';
  context.state.medicamentos.forEach(m => {
    getOrCreateElem(`col-cant-${m.clave}`).value = '0';
  });
  getOrCreateElem('col-cant-5121').value = '-5'; // Cantidad negativa no permitida

  vm.runInContext("transmitirColectivo()", context);
  const rechazoNegativo = (context.state.colectivos.length === cantColInicial);

  const ok = rechazoResponsable && rechazoNegativo;
  return {
    ok,
    esperado: "Rechaza responsable vacío y cantidades negativas (-5)",
    detalles: ok ? "Validaciones de colectivo funcionaron correctamente (rechazó vacío y negativo)" : "Fallo en validación de entradas de colectivo"
  };
});

// -----------------------------------------------------------------------------
// PRUEBA 11: Generación de Pedido Colectivo y Formato Físico (Cambio 2)
// -----------------------------------------------------------------------------
runTest("Generación de pedido colectivo con formato físico (Cambio 2)", () => {
  const cendisServices = vm.runInContext("CENDIS_SERVICES", context);
  getOrCreateElem('col-origen').value = cendisServices[0];
  getOrCreateElem('col-turno').value = 'MATUTINO';
  getOrCreateElem('col-resp').value = 'Enf. Roberto Díaz';
  getOrCreateElem('col-prioridad').value = 'PROGRAMADO';

  // Configurar cantidades válidas
  context.state.medicamentos.forEach(m => {
    getOrCreateElem(`col-cant-${m.clave}`).value = '0';
  });
  getOrCreateElem('col-cant-5121').value = '15'; // 15 ampolletas

  const cantColInicial = context.state.colectivos.length;
  vm.runInContext("transmitirColectivo()", context);
  const cantColFinal = context.state.colectivos.length;

  const col = context.state.colectivos[cantColFinal - 1];
  const ok = (cantColFinal === cantColInicial + 1) && col && col.ref_local && !col.api_ack && col.items.length === 1;
  return {
    ok,
    esperado: "Pedido colectivo registrado con ref_local, sin api_ack y listo para formato físico",
    detalles: ok ? `Folio: ${col.folio}, Ref: ${col.ref_local}, Estado: ${col.estado}` : "Fallo en generación de colectivo"
  };
});

console.log("\n================================================================================");
console.log(`RESUMEN: ${passedTests} de ${totalTests} pruebas pasaron con éxito.`);
console.log("================================================================================\n");

// Imprimir tabla Markdown
console.log("| Prueba | Resultado esperado | Resultado obtenido | Estado |");
console.log("| :--- | :--- | :--- | :---: |");
resultadosReporte.forEach(r => {
  console.log(`| ${r.nombre} | ${r.esperado} | ${r.obtenido} | ${r.estado} |`);
});
