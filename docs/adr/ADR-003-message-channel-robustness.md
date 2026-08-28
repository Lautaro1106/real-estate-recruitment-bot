# ADR-003: Robustez en el canal de mensajería — Manejo de ecos, duplicados y fallos parciales

**Estado:** Aceptado
**Contexto:** Bot de selección de candidatos por WhatsApp con mensajes canalizados a través de una capa de atención humana previa a la API de mensajería

---

## Contexto

Los mensajes entrantes no provienen de forma directa de la API de mensajería, sino que atraviesan una capa intermedia que gestiona la intervención de agentes humanos (ver ADR-001). Esta arquitectura introduce tres modos de falla que un flujo básico de procesamiento no resuelve adecuadamente:

1. Entrega múltiple de un mismo webhook por reintentos de red o de plataforma.
2. Coexistencia de mensajes emitidos por agentes humanos y respuestas de candidatos dentro del mismo flujo de eventos.
3. Desincronización del estado interno si ocurre un fallo durante el envío de la respuesta al candidato.

Cada escenario responde a causas independientes y se resuelve mediante mecanismos modulares específicos, evitando un bloque genérico de captura de errores que oculte el origen de eventuales fallas.

## 1. Filtrado de ecos del agente

**Problema:** La plataforma emite un único flujo de webhooks para ambas direcciones de la conversación. Sin un filtrado previo, los mensajes enviados por reclutadores humanos (o durante pruebas técnicas) ingresarían al flujo de evaluación, interpretándose erróneamente como respuestas del postulante.

**Decisión:** Filtrar por la dirección del evento (entrante vs. saliente) como primer paso de procesamiento, descartando inmediatamente cualquier mensaje no originado por el candidato.

**Compromiso:** Se depende de la correcta clasificación de dirección por parte de la plataforma externa.

## 2. Idempotencia mediante identificador de mensaje

**Problema:** Cualquier integración basada en webhooks está expuesta a recibir eventos duplicados. Sin control de idempotencia, una entrega duplicada reejecuta la máquina de estados para una misma respuesta, provocando repetición de preguntas o doble procesamiento.

**Alternativa descartada:** Asumir entrega exactamente una vez (*exactly-once*) confiando en los acuses de recibo —descartada, dado que retardos en el acuse pueden provocar reintentos concurrentes de la plataforma externa—.

**Decisión:** Registrar cada mensaje entrante por su identificador externo único mediante un patrón de inserción condicional (*insert-if-not-present*) antes de ejecutar lógica de negocio. Si el identificador ya fue procesado, la ejecución finaliza sin alterar el estado.

## 3. Ordenamiento: confirmación de entrega previa al avance de estado

**Problema:** Si el sistema actualiza el estado del candidato antes de verificar la entrega efectiva del mensaje saliente, una falla de red deja el estado interno adelantado respecto a lo que el candidato recibió, desfasando las respuestas posteriores.

**Alternativa descartada:** Persistir primero y revertir (*rollback*) ante fallas —descartada, debido a que el avance de estado opera mediante escrituras independientes y no transacciones atómicas distribuidas—.

**Decisión:** Emitir el mensaje saliente en primera instancia y persistir el avance de estado únicamente tras recibir confirmación de entrega exitosa. Si el envío falla, se deriva al flujo de control de errores.

**Limitación conocida:** un fallo en el envío saliente puede mantener al candidato en el paso actual sin una vía de avance automático si el mensaje subsiguiente no resuelve la transición (alineado con la limitación documentada en ADR-002 sobre escalamiento automático).

## 4. Tiempos de espera explícitos y reintentos acotados ante fallos transitorios

**Problema:** Las llamadas HTTP hacia servicios externos o internos carecían originalmente de límites de tiempo explícitos (*timeouts*). En un motor de orquestación con colas compartidas, una llamada bloqueada indefinidamente detiene los procesos encolados posteriores, transformando una degradación puntual en una indisponibilidad general.

**Decisión:** Configurar tiempos de espera explícitos en cada llamada HTTP saliente según la naturaleza del destino (ventanas mayores para APIs externas de mensajería y ventanas estrictas para microservicios internos en la misma red), complementadas con reintentos acotados y retroceso corto (*backoff*) ante fallas transitorias de red o respuestas 5xx puntuales.

**Nota sobre verificación en auditoría:** Esta salvaguarda figuró inicialmente como implementada en reportes de diseño, pero una auditoría directa sobre el código en ejecución reveló la ausencia de la configuración de reintentos en los flujos activos. Fue reincorporada y verificada contra los archivos reales de configuración antes de darse por completada, reforzando la regla de validar siempre contra el estado operativo del sistema y no sobre resúmenes documentales.

## Consecuencias

**Aceptadas:**
- Cuatro mecanismos independientes para modos de falla específicos en lugar de un manejador genérico, facilitando la identificación precisa de errores.
- Los primeros tres mecanismos asumen la validez de los metadatos suministrados por la plataforma (dirección e identificador de mensaje). El cuarto (tiempos de espera y reintentos) opera de forma autónoma protegiendo la disponibilidad del orquestador.

**Limitación conocida:**
- La validación de payloads entrantes es un área de mejora continua, priorizada según evidencia real de impacto en producción.

**Relacionado pero fuera de alcance:**
- El control de concurrencia para mensajes simultáneos de un mismo candidato (condición de carrera) se gestiona mediante un microservicio de bloqueo independiente documentado por separado.
