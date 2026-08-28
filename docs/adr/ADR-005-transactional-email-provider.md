# ADR-005: Correo transaccional mediante proveedor dedicado, desacoplado de cuentas interactivas

**Estado:** Aceptado
**Contexto:** Envío automatizado de confirmaciones y notificaciones de entrevistas desde el servicio de agendamiento autohospedado

---

## Contexto

El servicio de agendamiento emite notificaciones y confirmaciones automáticas por correo electrónico a candidatos y reclutadores ante cada reserva. Inicialmente se configuró el envío a través de una cuenta de Gmail vía SMTP con OAuth2, como mecanismo inicial para habilitar el servicio sin desplegar infraestructura adicional.

## Problema

Google revocaba periódicamente las credenciales SMTP de la cuenta forzando el restablecimiento de contraseñas, lo que interrumpía el envío de correos sin advertencia previa. La falla se detectaba de manera reactiva ante reportes de candidatos que no recibían su confirmación.

## Causa Raíz

El tráfico SMTP automatizado y constante emitido desde la IP de un centro de datos a través de una cuenta interactiva de uso personal activa las heurísticas de seguridad de Google contra accesos no autorizados. Al restablecerse la contraseña de la cuenta, las claves de aplicación asociadas quedan invalidadas de forma inmediata.

**Principio de diseño:** Una cuenta de correo personal e interactiva no debe emplearse como canal transaccional de un servidor. Ambos escenarios responden a modelos de seguridad opuestos: uno detecta patrones anómalos de inicio de sesión humano, mientras que el otro genera tráfico constante y programático. Un proveedor transaccional dedicado autentica mediante claves de API estáticas vinculadas a un dominio, sin verse afectado por heurísticas de ubicación o cambio de dispositivo.

## Decisión

Desacoplar el envío transaccional de la cuenta interactiva. La integración con Google Calendar (OAuth2) se mantiene exclusivamente para la sincronización de agendas y generación de enlaces de videollamada. El envío de correos transaccionales se migró a un proveedor especializado (Resend) utilizando un subdominio autenticado con registros DKIM/SPF, dirigiendo las respuestas de los usuarios a la casilla real del reclutador mediante la cabecera `Reply-To`.

## Consecuencias

**Aceptadas:**
- Se eliminaron las interrupciones recurrentes por revocación preventiva de credenciales.
- Se mejoró la entregabilidad al operar con un dominio verificado mediante DKIM/SPF, evitando clasificaciones erróneas como spam.
- Se desacopló la identidad del remitente del enrutamiento de respuestas: los candidatos reciben notificaciones desde un dominio institucional y las respuestas ingresan a la bandeja de entrada del operador humano sin requerir sesiones activas.

**En curso:**
- Requiere monitorear la vigencia de la clave de API y el consumo de envíos respecto a los límites del plan contratado.

**Preguntas abiertas al momento de la migración:**
- Monitoreo de compatibilidad en clientes de correo al combinar nombres visibles con direcciones estructuradas en el remitente.
- Verificación del procesamiento de la cabecera `Reply-To` en el motor de correo de la plataforma de agendamiento.
