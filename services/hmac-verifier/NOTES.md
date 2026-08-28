# hmac-verifier — Notas de Diseño

## Propósito del servicio

Verifica que los webhooks entrantes provengan efectivamente de las fuentes esperadas antes de que el orquestador los procese. Sin esta validación, cualquier actor externo podría enviar eventos falsos al endpoint y ejecutar transiciones de estado en el bot.

El servicio expone un endpoint por cada fuente de webhooks que requiere verificación. Cada fuente tiene un esquema de firma distinto, por lo que la verificación es específica por origen y no genérica.

## Endpoints

### POST /verify

Verifica webhooks provenientes del servicio de agendamiento. El mecanismo es HMAC-SHA256 sobre el cuerpo del request.

**Detalle relevante de implementación:** el cuerpo se re-serializa con separadores compactos antes de calcular la firma. Esto garantiza que el hash sea consistente independientemente de cómo el cliente haya formateado el JSON original (espacios, orden de claves, etc.), igualando el comportamiento del firmante.

### POST /verify/chatwoot

Verifica webhooks provenientes de la capa de mensajería (el intermediario que gestiona el canal de WhatsApp). El esquema de firma incluye un timestamp en el mensaje a firmar (`timestamp.body`), lo que agrega protección contra ataques de replay además de verificar la autenticidad del origen.

### GET /health

Confirma que el proceso está disponible. No tiene dependencias externas: devuelve `ok` si el proceso responde.

## Por qué existe como servicio separado

La verificación de firmas es lógica de seguridad perimetral, no lógica de negocio. Extraerla del orquestador permite actualizarla, auditarla y testearla de forma independiente, sin tocar los flujos de calificación. También hace explícita la frontera: todo lo que cruza el perímetro pasa por aquí primero.
