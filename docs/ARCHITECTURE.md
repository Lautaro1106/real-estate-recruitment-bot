# Arquitectura

Desglose completo de la máquina de estados, el pipeline de flujos activo, el modelo de datos y los límites operativos del sistema — redactado como documento de diseño general y no como referencia interna exhaustiva.

---

## 1. La Máquina de Estados

El flujo de calificación consiste en una secuencia de estados discretos (`current_step`), donde cada uno espera un tipo específico de entrada y avanza únicamente tras recibir una respuesta válida. No existen ramificaciones basadas en interpretación de intenciones; las transiciones se ejecutan exclusivamente sobre datos estructurados almacenados (número de paso, indicador de estado, respuesta guardada).

**Estructura del flujo, en orden:**

1. Captura de nombre (con validación estructural — ver [ADR-002](adr/ADR-002-constrained-input-space.md))
2. Captura de correo electrónico (validado mediante expresión regular)
3. Carga de CV (archivo adjunto o alternativa explícita de "no disponible")
4–7. Conjunto fijo de preguntas de calificación categóricas (disponibilidad horaria, expectativas de compensación, respaldo financiero, elegibilidad geográfica, con una repregunta condicional para una región específica) — validadas contra un conjunto cerrado de opciones numéricas, ver [ADR-002](adr/ADR-002-constrained-input-space.md)
8. Calificación — función determinista basada en las respuestas almacenadas, sin inferencia de modelos de lenguaje (ver [ADR-001](adr/ADR-001-deterministic-state-machine.md))
9. Envío de enlace de agendamiento (candidato calificado) o mensaje de cierre (candidato descartado, sin detallar el motivo específico en el mensaje — ver más abajo)

**Un detalle no evidente pero relevante: los números de paso son identificadores de estado, no índices secuenciales.** Una pregunta incorporada posteriormente al diseño original (validación de rango de edad) se ubicó con un identificador numérico no correlativo respecto a sus pasos adyacentes, evitando reconfigurar todas las referencias posteriores en el motor de flujos. La lección de diseño es general: en una máquina de estados modelada como un grafo de nodos discretos, el *identificador* de un estado y su *posición* en el flujo son conceptos distintos; acoplarlos genera fricción innecesaria ante cambios en el flujo.

**El motivo de descarte se omite intencionalmente ante el candidato por defecto.** El postulante recibe un mensaje de cierre cordial y genérico. Si solicita explícitamente una explicación, dicha consulta se detecta y se deriva a un reclutador humano en lugar de ser respondida por el bot. El sistema permite que una persona comunique la causa con contexto, pero no genera explicaciones automáticas. Se trata de una decisión de producto y no de una limitación técnica: una regla determinista puede generar el motivo de inmediato, pero su entrega directa y automatizada conlleva un perfil de riesgo operativo diferente al de la comunicación humana.

---

## 2. Pipeline de Flujos Activo

Existen cinco flujos activos en producción. Un sexto flujo (monitor de expiración de tokens) fue dado de baja tras migrar a credenciales de larga duración; se menciona como antecedente de diseño.

| Flujo | Responsabilidad | Escrituras en base de datos |
|---|---|---|
| **Motor principal del bot** | Ejecuta la máquina de estados descrita anteriormente de punta a punta | `candidates`, `message_log`, `events` |
| **Procesador de webhooks de agendamiento** | Procesa eventos de reserva, reagendamiento y cancelación desde la plataforma de citas, actualiza el estado del candidato y envía confirmaciones | `candidates`, `events` |
| **Mantenimiento de BD** | Ejecuta tareas programadas de anonimización y limpieza de datos (ver [ADR-006](adr/ADR-006-auditability-pii-retention.md)) | `candidates`, `message_log`, `error_log` |
| **Manejador de errores** | Desactiva el bot ante fallas de un candidato, notifica al postulante y al equipo de selección, y registra el error | `candidates`, `error_log`, `events` |
| **Sincronización con CRM** | Envía candidatos calificados o descartados al CRM como registros estructurados con un resumen formateado de evaluación | CRM externo |

Cada flujo posee una responsabilidad delimitada y se comunica con los demás a través de la base de datos y llamadas internas vía webhook, evitando estados compartidos en memoria.

---

## 3. Concurrencia y Ordenamiento de Mensajes

El motor principal cuenta con tres mecanismos independientes de protección frente a contingencias propias de una arquitectura orientada a webhooks, garantizando diagnósticos precisos ante eventuales fallas. El detalle completo se encuentra en [ADR-003](adr/ADR-003-message-channel-robustness.md).

- **Filtrado de ecos** — previene que mensajes emitidos por operadores humanos en el mismo canal sean interpretados como respuestas del candidato.
- **Idempotencia** — evita que la entrega duplicada de un mismo webhook (por reintentos de red o de plataforma) reejecute la máquina de estados.
- **Confirmación de entrega previa al avance de estado** — el estado persiste únicamente tras verificar el envío exitoso del mensaje saliente, impidiendo que el estado interno se desincronice respecto a lo recibido por el usuario.

**La concurrencia entre mensajes consecutivos de un mismo candidato** (envío de múltiples mensajes en rápida sucesión antes de completar el procesamiento del primero) constituye un problema independiente, resuelto mediante un bloqueo distribuido adquirido al inicio de la ejecución y liberado tras confirmar la entrega de la respuesta. Se trata de un mecanismo dimensionado específicamente para el volumen real de la aplicación (instancia única, TTL breve), sin sobreingeniería innecesaria.

---

## 4. Modelo de Datos (Resumen)

El registro del candidato constituye el estado central. Las respuestas de calificación se almacenan en un documento estructurado JSON en lugar de columnas individuales por pregunta —un criterio adecuado para el volumen actual de preguntas (ver análisis de compensaciones en [ADR-002](adr/ADR-002-constrained-input-space.md))—.

**Campos principales del candidato:** número de teléfono (clave de sesión), paso actual, estado, nombre, correo electrónico, referencia de CV, documento JSON de respuestas, motivo de descarte (columna dedicada para consultas directas), contador de reintentos, marca temporal de última interacción, contador de reagendamientos y fuente de campaña obtenida en el primer contacto.

**Estructuras auxiliares de auditoría:** se implementan dos tablas independientes del registro principal (ver [ADR-006](adr/ADR-006-auditability-pii-retention.md)): una tabla desacoplada de eventos para telemetría que preserva métricas tras la anonimización del candidato, y una tabla de errores filtrada que excluye deliberadamente datos personales (PII) en los registros de fallas.

---

## 5. Configuración

Las variables de entorno se organizan en categorías claras: credenciales de mensajería, credenciales de la plataforma de citas, credenciales del CRM, tokens de autenticación interna (para los microservicios de bloqueo y verificación de firmas) y direcciones de notificación interna. Todas se cargan al inicio de cada flujo en un nodo centralizado de configuración y se propagan downstream, evitando accesos dispersos a `$env` que degraden la legibilidad del flujo.

---

## 6. Límites Operativos del Sistema

Se documentan explícitamente los límites conocidos del sistema para mantener visibilidad sobre las decisiones de diseño adoptadas:

- **Sin escalamiento automático ante reintentos fallidos sucesivos.** El flujo actual no limita los reintentos de validación ni fuerza una derivación automática a un operador humano tras N intentos erróneos; el traspaso a un operador depende de la detección explícita de intención por parte del usuario. Ver [ADR-002](adr/ADR-002-constrained-input-space.md).
- **Validación de payloads entrantes.** La validación de payloads entrantes es un área de mejora continua, priorizada según evidencia real de impacto en producción.
- **Protección de datos entre tipos de registro.** El nivel de protección de datos difiere según el tipo de registro, y se está evaluando homogeneizarlo; el detalle se documenta internamente, no publicado aquí.
- **Criterio de anonimización unificado por antigüedad sin distinción de resultado.** Los registros de candidatos descartados y calificados siguen actualmente una misma ventana temporal de anonimización, posponiendo una política de retención diferenciada por ciclo de vida. Ver [ADR-006](adr/ADR-006-auditability-pii-retention.md).

Estos puntos representan decisiones de alcance deliberadas, postergadas en función del impacto operativo real frente a otras prioridades del sistema.

## Documentación Relacionada

- [Registros de Decisiones de Arquitectura (ADRs)](adr/) — fundamentación técnica de las decisiones de diseño adoptadas en producción
- [Microservicio de Bloqueo Distribuido (`redis-lock`)](../services/redis-lock/) — implementación en Python/Flask del control de concurrencia · [Notas de diseño](../services/redis-lock/NOTES.md)
- [Microservicio Validador HMAC (`hmac-verifier`)](../services/hmac-verifier/) — implementación de verificación de firmas en webhooks · [Notas de diseño](../services/hmac-verifier/NOTES.md)
