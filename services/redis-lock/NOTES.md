# redis-lock — Notas de Diseño

## Propósito del servicio

Resuelve una condición de carrera específica del canal de WhatsApp: los candidatos suelen enviar varios mensajes en rápida sucesión antes de que el primero termine de procesarse. Sin control de concurrencia, dos webhooks paralelos para el mismo número telefónico compiten por escribir el estado del candidato, produciendo respuestas desordenadas o avances de estado duplicados.

El servicio es intencionalmente simple: una instancia única de Redis con TTL corto, sin Redlock ni réplicas. Es la solución más pequeña que elimina la condición de carrera para el volumen real de tráfico.

## Endpoints

### POST /acquire

Adquiere dos bloqueos atómicos antes de que el orquestador procese un mensaje:

- **Bloqueo por `message_id`**: previene que un webhook duplicado (reintento de red o de plataforma) ejecute la máquina de estados dos veces para el mismo mensaje.
- **Bloqueo por `phone_number`**: previene que dos mensajes consecutivos del mismo candidato se procesen en paralelo y compitan por el estado.

Ambos bloqueos se intentan juntos. Si alguno falla (ya existe), se libera el que sí se adquirió para no dejar estado sucio, y se devuelve 423 indicando que el mensaje debe descartarse.

**Decisión de diseño — fail open ante caída de Redis:** si Redis no responde, el endpoint devuelve `acquired: true` de todas formas, con un campo `warning`. El criterio es que una caída de Redis no debe detener el flujo principal del bot: la condición de carrera es infrecuente y el impacto de procesarla sin lock es menor al de interrumpir el servicio por completo.

### POST /release

Libera solo el bloqueo por `phone_number` al confirmar la entrega del mensaje saliente. El bloqueo por `message_id` no se libera manualmente: se deja expirar con su TTL. Esto es deliberado — `message_id` actúa como protección contra duplicados tardíos y no debe liberarse antes de que el TTL garantice que el reintento ya no llegará.

### GET /health

Confirma que el proceso está vivo y que Redis responde. No requiere autenticación. Devuelve el estado de la conexión a Redis, no solo el del proceso Flask.

## Autenticación interna

Todos los endpoints de escritura requieren un token en el header `X-Internal-Token`. Si la variable de entorno no está configurada, el servicio rechaza todas las solicitudes por diseño (fail secure), en lugar de operar sin autenticación.
