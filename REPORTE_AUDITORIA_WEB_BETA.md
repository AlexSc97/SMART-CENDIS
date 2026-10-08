# SMART CENDIS — Reporte de Auditoría Técnica y Fortalecimiento de la Interfaz Web Beta (Etapa 3)

**Proyecto Integrador:** SMART CENDIS: Sistema de Gestión Digital de Solicitudes, Abastecimiento y Control de Inventario Hospitalario  
**Materia:** Lógica y Programación Estructurada  
**Autor:** Alejandro Sánchez  
**Repositorio Oficial:** [https://github.com/AlexSc97/SMART-CENDIS.git](https://github.com/AlexSc97/SMART-CENDIS.git)  
**Fecha:** Octubre 2026  
**Documento:** Reporte Técnico de Auditoría, Refactorización Quirúrgica y Validación de la Versión Web Beta  

---

## 1. Contexto General y Objetivos de la Intervención

El proyecto **SMART CENDIS** cuenta con una base metodológica y técnica distribuida en tres etapas consolidadas:

1. **Etapa 1:** Análisis exhaustivo de la problemática hospitalaria, levantamiento de requerimientos, definición de reglas de negocio, diseño de flujos operativos y formulación de pseudocódigo. Se estipuló formalmente que la primera versión del sistema utiliza **formatos físicos impresos con firmas autógrafas** como mecanismo normativo de comunicación con Farmacia Central, reservando la interconexión mediante API como una evolución tecnológica futura.
2. **Etapa 2:** Prototipo funcional desarrollado en Python, con persistencia basada en archivos JSON estructurados, validaciones lógicas, gestión de solicitudes de piso, dictamen administrativo y recepción física con actualización estricta de existencias en botiquín (CENDIS).
3. **Etapa 3:** Versión robusta del núcleo Python (`smartCendis_v3.py`) fortalecida con validación estricta por expresiones regulares (RegEx), persistencia atómica con mecanismo de **rollback ante fallos de E/S**, pruebas funcionales automatizadas y trazabilidad de errores.
4. **Interfaz Web Beta (`smartcendis_web.html` / `index.html`):** Prototipo gráfico interactivo desarrollado para evidenciar visualmente la evolución del sistema hacia una interfaz gráfica de usuario (GUI) amigable, orientada a servicios de enfermería y personal de botiquín hospitalario.

### Objetivo Principal de la Auditoría
Efectuar una **intervención quirúrgica** sobre el prototipo web para:
* Alinear su comportamiento con las reglas de negocio de las Etapas 1, 2 y 3.
* Eliminar cualquier simulación engañosa de servicios inexistentes (como acuses HTTP ficticios de API).
* Implementar persistencia robusta y reversión de estado (*rollback*) en `localStorage`.
* Salvaguardar la integridad de las reglas operativas de inventario.
* Mantener 100% inalterado el diseño visual, paleta de colores, maquetación institucional y datos de prueba.

---

## 2. Mapa Conceptual de la Arquitectura

```
                              SMART CENDIS
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
        Núcleo Python                              Web Beta
        v3.0.0 (Formal)                    Interfaz Demostrativa
              │                                         │
       JSON persistente                           localStorage
      Regex sanitización                        Regex sanitización
     Rollback ante fallos                      Rollback ante fallos
       Pruebas unitarias                         Suite test_web_beta
              │                                         │
              └────────────────────┬────────────────────┘
                                   │
                       MISMAS REGLAS DE NEGOCIO
                                   │
             ┌─────────────────────┼─────────────────────┐
             ▼                     ▼                     ▼
     1. Solicitud de Piso   2. Dictamen Farmacia   3. Recepción Física
       (Piso → CENDIS)         (Administrativo)     (Ingreso a botiquín)
             │                     │                     │
      [NO modifica stock]   [NO modifica stock]    [INCREMENTA STOCK]
             └─────────────────────┬─────────────────────┘
                                   ▼
                        INVENTARIO CENDIS REAL
```

---

## 3. Detalle de Cambios Quirúrgicos Realizados

### Cambio 1: Identidad y Jerarquía de la Versión Web
* **Situación Previa:** Se mostraba la etiqueta `SMART CENDIS v3.1` y subtítulo de auditoría.
* **Problema Técnico/Académico:** Podía interpretarse erróneamente como una versión superior o un reemplazo formal del núcleo en Python (v3.0.0).
* **Solución Aplicada:** Se actualizó a:
  * Título: `SMART CENDIS — Web Beta`
  * Subtítulo: `Interfaz gráfica de demostración · Etapa 3`
  * Nota de alcance: `🟢 Demo operativa · localStorage · Núcleo Python v3.0.0 separado`.
* **Justificación:** Honestidad de catálogo documental. La interfaz web es complementaria, no sustitutiva.

### Cambio 2: Supresión de Afirmaciones Ficticias de "API"
* **Situación Previa:** Botones y mensajes decían "Transmitir vía API a Farmacia Central", generaban folios `ACK-HTTP200-XXXX` y mostraban "En Cola de Farmacia".
* **Problema Técnico/Académico:** Inconsistencia con la Etapa 1, donde se estableció que la comunicación normativa con Farmacia es mediante formato físico impreso.
* **Solución Aplicada:**
  * Botón: `Registrar Pedido y Generar Formato Oficial`.
  * Mensaje Toast: `Pedido Colectivo [folio] registrado. Formato físico listo para Farmacia Central.`
  * Acuse: Reemplazo de `api_ack` ficticio por identificador de registro local `ref_local: REG-LOCAL-XXXX`.
  * Formato Oficial: Se añadió la leyenda regulatoria explícita: *“Nota: La integración API con Farmacia Central está prevista como evolución futura del sistema.”*
  * Botón de inspección: Reemplazado de "API Payload (JSON)" a "Ver Datos Locales (JSON)".
  * Badges: `Transmitido a Farmacia` $\rightarrow$ `Registrado para Farmacia`.

### Cambio 3: Indicador de Disponibilidad Honesto
* **Situación Previa:** Indicador superior marcaba `Sistema en Línea`.
* **Problema Técnico/Académico:** Sugería la existencia de un servidor o backend en la nube en ejecución continua.
* **Solución Aplicada:** Cambiado a:
  * `🟢 Demo operativa — Modo demostración local (localStorage)`
* **Justificación:** Transparencia técnica sobre la naturaleza local de la sesión en el navegador.

### Cambio 4: Persistencia Segura y Centralizada (`guardarEstadoSeguro`)
* **Situación Previa:** Cada módulo invocaba directamente `localStorage.setItem(STORAGE_KEY, JSON.stringify(state))` sin captura de excepciones.
* **Problema Técnico/Académico:** Si el navegador bloqueaba el almacenamiento por cuota (`QuotaExceededError`) o políticas de privacidad, la aplicación fallaba de forma imprevista y corrupta.
* **Solución Aplicada:** Se implementó la función centralizada:
  ```javascript
  function guardarEstadoSeguro() {
    try {
      const json = JSON.stringify(state);
      localStorage.setItem(STORAGE_KEY, json);
      return true;
    } catch(e) {
      console.error('[SMART CENDIS] Error al guardar estado en localStorage:', e);
      toast('⚠ Error al guardar los datos. Los cambios no fueron persistidos.', 'error');
      return false;
    }
  }
  ```
  La función `saveState()` delega ahora directamente a `guardarEstadoSeguro()`.

### Cambio 5: Implementación de Rollback en Operaciones Críticas
* **Situación Previa:** Si ocurría un error durante el guardado local, las estructuras en memoria (`state`) ya habían sido alteradas, dejando el sistema en un estado incongruente respecto al medio de persistencia.
* **Solución Aplicada:** En todas las operaciones críticas de mutación de datos se aplica el patrón de reversión:
  1. Clonación de respaldo: `const estadoAnterior = JSON.stringify(state);`
  2. Mutación del estado en memoria.
  3. Verificación de persistencia: `if (!guardarEstadoSeguro()) { state = JSON.parse(estadoAnterior); ... return; }`
* **Módulos Protegidos con Rollback:**
  * Alta de solicitudes de piso (`guardarSolicitud`).
  * Alta de medicamentos en catálogo (`guardarMed`).
  * Modificación de metas de medicamentos (`guardarEdicion`).
  * Baja lógica de medicamentos (`desactivarMed`).
  * Reactivación de medicamentos (`activarMed`).
  * Dictamen administrativo de farmacia (`responderFarmacia`).
  * Recepción física en piso con modificación de inventario (`registrarRecepcion`).
  * Emisión de requisiciones colectivas (`transmitirColectivo`).
  * Reinicio a datos demo (`resetData`).

### Cambio 6: Recuperación Explícita ante Datos Corruptos
* **Situación Previa:** `loadState()` tenía un `try/catch` vacío que ante cualquier JSON corrupto cargaba los datos demo de forma silenciosa, ocultando la anomalía.
* **Solución Aplicada:** Se dotó a `loadState()` de:
  * Detección de errores sintácticos de JSON con registro en consola.
  * Notificación visual diferida mediante toast: `⚠ No fue posible recuperar los datos locales. Se cargó el estado de demostración.`
  * Validación de estructura mínima requerida (presencia de arreglos de medicamentos y solicitudes).
  * Limpieza profiláctica de la clave corrupta con `localStorage.removeItem(STORAGE_KEY)`.

### Cambios 7 y 8: Blindaje de las Reglas Fundamentales de Negocio
* **Regla 1 (Solicitud $\neq$ Inventario):** La función `guardarSolicitud()` **bajo ninguna circunstancia descuenta ni suma existencias físicas**. El inventario CENDIS permanece 100% inalterado al crear un requerimiento.
* **Regla 2 (Dictamen $\neq$ Recepción Física):** La función `responderFarmacia()` sólo modifica el estado administrativo (`SURTIDA` o `NEGADA`). **No incrementa ni reduce existencias**.
* **Regla 3 (Recepción Física = Movimiento Real):** La función `registrarRecepcion()` es la **única** autorizada para modificar `stock_actual` del medicamento, y lo hace estrictamente por la cantidad verificada físicamente (`recibido`).
  * Si se reciben todas las unidades solicitadas: estado `SURTIDA`, `pendiente = 0`.
  * Si se recibe una fracción: estado `SURTIDA_PARCIAL`, `pendiente = sol.cantidad - recibido`.
  * Si se reciben 0 unidades: estado `NEGADA`, `pendiente = sol.cantidad`.

### Cambio 9: Validación Rigurosa de Entradas en Pedidos Colectivos
* **Situación Previa:** El formulario de pedido colectivo permitía campos con texto insuficiente y no validaba que los insumos ingresados fueran números enteros no negativos.
* **Solución Aplicada:**
  * Validación de responsable con expresión regular `RE.usuario.test(resp)`.
  * Lista blanca estricta para turnos (`['MATUTINO', 'VESPERTINO', 'NOCTURNO']`).
  * Lista blanca estricta para prioridades (`['PROGRAMADO', 'CRITICO', 'URGENTE']`).
  * Comprobación en cada insumo con `RE.cantidadGe0.test(rawVal)` para rechazar números negativos (`-5`), valores con punto decimal (`1.5`) o cadenas alfanuméricas (`abc`).
  * Requerimiento obligatorio de al menos 1 unidad solicitada en total.

### Cambio 10: Preservación Absoluta del Diseño Visual
* Se conservaron intactos todos los tokens CSS: Slate-100 (`#f1f5f9`), Sky-600 (`#0284c7`), fondos opacos de modales al 100% (`bg-[#ffffff]`), tablas `sc-table`, tarjetas KPI de estadísticas, barras de progreso de stock y diseño de impresión (`@media print`).

### Cambio 11: Delimitación Estricta de Alcance (Sin Funcionalidades Ajenas)
* Se evitó deliberadamente la introducción de librerías externas, Firebase, MySQL, Node.js como backend en ejecución, APIs externas o sistemas de autenticación ficticios.

### Corrección Adicional de Estabilidad Detectada en Auditoría (Hoisting Bug)
* **Hallazgo:** En el código original existía una doble declaración de `function attachEvents(page)`. En la segunda ocurrencia se hacía `const _origAttach = attachEvents; function attachEvents(page) { _origAttach(page); ... }`. Debido al *hoisting* de JavaScript, `_origAttach` se asignaba a la misma función recursiva, provocando un desbordamiento de pila (`RangeError: Maximum call stack size exceeded`) al navegar entre pantallas.
* **Solución Quirúrgica:** Se consolidó una única función `attachEvents(page)` limpia que atiende de forma directa tanto la vista de dictamen (`procesar`) como la de recepción física (`recepcion`), eliminando toda recursión.

### Cambio 15: Declaración Explícita de Limitaciones del Sistema
* Se integró en el código fuente JavaScript y en el pie del menú lateral la ficha técnica con las 8 limitaciones de alcance declaradas para la versión beta.

---

## 4. Matriz de Pruebas y Resultados de Verificación

Se desarrolló y ejecutó la batería automatizada `test_web_beta.js` simulando el entorno DOM y el motor `localStorage` con fallos controlados.

| # | Prueba Ejecutada | Criterio / Regla Evaluada | Resultado Obtenido | Veredicto |
| :---: | :--- | :--- | :--- | :---: |
| **01** | Creación de solicitud de piso | Registro con folio correlativo `SOL-0001` y estado `PENDIENTE`. | Registrada SOL-0001 (Cant: 5, Estado: PENDIENTE). | **PASÓ** |
| **02** | Solicitud no modifica inventario | Las existencias físicas de botiquín no deben variar al solicitar. | Stock de Paracetamol intacto en 26 unidades. | **PASÓ** |
| **03** | Dictamen de farmacia (SURTIDA) | Resolución administrativa no altera existencias físicas. | Estado pasa a SURTIDA, stock CENDIS permanece en 26. | **PASÓ** |
| **04** | Recepción física total | El inventario incrementa en $+5$ (26 $\rightarrow$ 31), `pendiente = 0`. | Stock actualizado a 31 unidades, remanente en 0. | **PASÓ** |
| **05** | Recepción física parcial | Recepción de 6 de 10 unidades: stock $+6$ (14 $\rightarrow$ 20), `pendiente = 4`. | Stock en 20, estado `SURTIDA_PARCIAL`, pendiente en 4. | **PASÓ** |
| **06** | Recepción física en cero | Recepción de 0 unidades: stock sin cambio, estado `NEGADA`. | Stock intacto en 80 unidades, estado `NEGADA`. | **PASÓ** |
| **07** | Persistencia en localStorage | Sobrevivencia de la estructura completa en JSON válido. | Clave `smartcendis_v3_state` serializada con 3 solicitudes. | **PASÓ** |
| **08** | Recuperación ante datos corruptos | Inyección de JSON malformado no quiebra la aplicación. | Detecta corrupción, notifica al usuario y carga demo profiláctico. | **PASÓ** |
| **09** | Fallo de almacenamiento + Rollback | Forzado de `QuotaExceededError`: el estado debe revertirse. | Rollback confirmado: el medicamento no quedó registrado. | **PASÓ** |
| **10** | Validación en Pedido Colectivo | Rechazo de responsable vacío y cantidades negativas (`-5`). | Formulario rechazó entradas con error visual y toast. | **PASÓ** |
| **11** | Generación de Pedido Colectivo | Registro local con `ref_local`, sin `api_ack` y listo para imprimir. | Folio `COL-2026-0001`, Ref `REG-LOCAL-XXXX`, estado formal. | **PASÓ** |

**Resultado Global:** **11 de 11 pruebas superadas satisfactoriamente (100% de efectividad).**

---

## 5. Funcionalidades Deliberadamente NO Modificadas

Para preservar la estabilidad y la familiaridad operativa del sistema, las siguientes funcionalidades se mantuvieron exactamente como fueron concebidas:

1. **Diseño Visual e Identidad Institucional:** Tipografía, paleta de colores azul clínico (`#0284c7`), fondos grises limpios (`#f1f5f9`), distribución del Sidebar y cabecera con reloj dinámico en tiempo real.
2. **Dashboard Operativo:** Las 4 tarjetas KPI (Medicamentos Activos, Solicitudes Pendientes, Pedidos Colectivos y Alertas de Stock Crítico $<30\%$) y las barras porcentuales de cobertura.
3. **Módulo de Censo de Pacientes:** Búsqueda reactiva por servicio clínico y número de cama, así como tabla estática del censo de demostración.
4. **Módulo de Catálogo de Medicamentos:** Tablas con claves oficiales de 4 dígitos, presentaciones comerciales, unidades de medida y stock objetivo.
5. **Formato Oficial de Requisición Colectiva para Impresión:** La vista modal con membrete institucional, tabla de insumos requeridos y los tres cuadros normativos de firmas autógrafas (*Solicita CENDIS*, *Autoriza Jefatura* y *Surtido por Farmacia Central*) con compatibilidad completa con `@media print`.

---

## 6. Lista Oficial de Limitaciones Actuales (Decisiones de Alcance)

Estas características constituyen delimitaciones metodológicas conscientes para la entrega de la Etapa 3:

1. **Persistencia Basada en Navegador:** La versión web se almacena en el `localStorage` del cliente. Los datos persisten entre recargas en el mismo equipo, pero no se comparten entre navegadores distintos.
2. **Ausencia de Servidor de Backend:** No existe un servidor central Node.js, Python Flask/Django ni base de datos MySQL/PostgreSQL gestionando concurrencia multiusuario.
3. **Sin Conexión Institucional IMSS:** No existe vinculación directa con el Expediente Clínico Electrónico (ECE) ni con los sistemas centrales del Instituto.
4. **Sin Integración por API con Farmacia Central:** La sincronización con el almacén general se realiza mediante **formato físico impreso**, según el requerimiento de la Etapa 1.
5. **Datos de Demostración:** Todos los registros de pacientes y consumos son ficticios y concebidos para fines estrictamente académicos.
6. **Complementariedad con el Núcleo Python:** La web es un prototipo visual demostrativo; el procesamiento formal con regex avanzadas y suites de pruebas unitarias reside en el núcleo Python v3.0.0.

---

## 7. Confirmación Final de Integridad

> **Declaración de Conformidad:** Se certifica que en esta intervención no se incorporaron APIs simuladas, acuses HTTP ficticios, frameworks adicionales ni dependencias externas innecesarias. El sistema opera de manera honesta, transparente, técnicamente robusta y en total concordancia con la documentación de las Etapas 1, 2 y 3 de SMART CENDIS.
