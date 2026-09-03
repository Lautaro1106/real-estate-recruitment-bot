# Capturas del sistema en funcionamiento

Evidencia visual del flujo completo — desde el primer mensaje de WhatsApp
hasta el registro en el CRM. Todas las capturas usan datos de prueba, no
conversaciones ni candidatos reales.

---

## Flujo de WhatsApp — validaciones y manejo de errores

| | |
|---|---|
| ![Validación de nombre](flujo-whatsapp/bot-error-1.png) | ![Validación de email](flujo-whatsapp/bot-error-2.png) |
| ![Validación de CV](flujo-whatsapp/bot-error-3.png) | ![Validación de opción numérica](flujo-whatsapp/bot-error-4.png) |

Cada entrada inválida (nombre con salto de línea, email mal formado,
respuesta fuera de las opciones numeradas) dispara un mensaje de error
específico y vuelve a pedir el dato — el estado no avanza hasta recibir
una respuesta válida. Ver [ADR-002](../adr/ADR-002-constrained-input-space.md).

![Cancelación del proceso](flujo-whatsapp/cancelar-proceso.png)

El candidato puede cancelar el proceso en cualquier momento escribiendo
"cancelar" — el flujo lo confirma y termina la conversación de forma
explícita.

![CV recibido](flujo-whatsapp/cv-recibido.png)

Confirmación de recepción de CV y continuidad del flujo hacia las
preguntas de calificación.

![Candidato descartado](flujo-whatsapp/candidato-descartado.png)

Mensaje de cierre para un candidato que no califica — sin revelar el
motivo específico inline, ver [ARCHITECTURE.md §1](../ARCHITECTURE.md#1-la-máquina-de-estados).

---

## Concurrencia — mensajes múltiples del mismo candidato

| | | |
|---|---|---|
| ![Concurrencia 1](concurrencia/concurrencia-1.png) | ![Concurrencia 2](concurrencia/concurrencia-2.png) | ![Concurrencia 3](concurrencia/concurrencia-3.png) |
| ![Concurrencia 4](concurrencia/concurrencia-4.png) | ![Concurrencia 5](concurrencia/concurrencia-5.png) | |

Secuencia mostrando cómo el sistema maneja varios mensajes seguidos del
mismo candidato sin duplicar procesamiento ni desordenar respuestas —
resuelto por el microservicio `redis-lock`. Ver
[ADR-003](../adr/ADR-003-message-channel-robustness.md) y
[NOTES.md de redis-lock](../../services/redis-lock/NOTES.md).

---

## CRM (Odoo)

![Vista de pipeline](crm-odoo/vista-pipeline.png)

Pipeline kanban de postulantes por etapa (Primera entrevista,
Descartado, etc.).

![Detalle de candidato](crm-odoo/candidato-detalle.png)

Ficha de un postulante sincronizado automáticamente desde el bot hacia
Odoo como registro `hr.applicant`.

![Evaluación pre-filtro](crm-odoo/evaluacion-prefiltro.png)

Resumen de evaluación generado automáticamente al sincronizar: qué
criterios cumplió el candidato, motivo de descarte si aplica, y una
recomendación de seguimiento con puntuación.

---

## Atención humana

![Derivar con humano](atencion-humana/derivar-con-humano.png)

Derivación a un reclutador humano cuando el flujo no puede resolver un
caso por sí solo.

![Descarte visto desde Chatwoot](atencion-humana/descarte-desde-chatwoot.png)

La misma conversación de descarte, vista desde la interfaz del agente
humano — muestra la asignación de la conversación al equipo de
reclutamiento.

---

## Agendamiento (Cal.com)

![Selección de día y horario](agendamiento/confirmacion-evento.png)

El slot reservado queda registrado en Google Calendar vía integración OAuth2
(ver [ADR-005](../adr/ADR-005-transactional-email-provider.md)).

| | |
|---|---|
| ![Email de confirmación al candidato (parte 1)](agendamiento/mail-candidato-1.png) | ![Email de confirmación al candidato (parte 2)](agendamiento/mail-candidato-2.png) |

La invitación llega vía Google Calendar nativo (integración OAuth2 que
se mantuvo sin cambios — ver ADR-005), no por el proveedor de correo
transaccional (Resend) que maneja las notificaciones propias del bot.
Confirma que el ciclo de agendamiento se cierra de punta a punta.

---

[← Volver al README principal](../../README.md)
