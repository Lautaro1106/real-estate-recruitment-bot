# ADR-006: Auditabilidad, límites de PII y retención de datos

**Estado:** Aceptado
**Contexto:** Requerimientos emergentes de observabilidad y privacidad al consolidarse el sistema en producción con tráfico continuo de candidatos

---

## Contexto

La operación continua del sistema evidenció tres necesidades no contempladas en el diseño inicial:

1. **Telemetría sin sobrecargar el registro transaccional.** La medición de avance de candidatos por paso resulta esencial para reportes analíticos, pero registrarla mediante actualizaciones sucesivas sobre la tabla principal de candidatos degrada el rendimiento y la trazabilidad.
2. **Persistencia de registros de errores.** Inicialmente, los errores solo eran visibles en la interfaz del orquestador, sujeta a retención rotativa. Ante reportes diferidos de candidatos, las trazas de ejecución ya habían expirado.
3. **Obligaciones de retención de datos.** El resguardo indefinido de conversaciones e información personal está sujeto a normativas de protección de datos personales, que exigen límites temporales justificados para el almacenamiento de datos sensibles.

## Decisiones

### 1. Tabla desacoplada de eventos y telemetría

Se implementó una tabla independiente que registra hitos discretos (creación de candidato, paso completado, descarte, agendamiento de entrevista) como filas inmutables vinculadas al registro del candidato, en lugar de mutar el estado de la tabla principal.

**Fundamentación técnica:** Mantiene la tabla transaccional enfocada en el *estado actual*, proveyendo un historial desacoplado para consultas analíticas. La clave foránea hacia el candidato admite valores nulos por diseño: al eliminarse o anonimizarse los datos personales del candidato, se desvincula la referencia conservando los registros de eventos para métricas agregadas.

### 2. Registro de errores con límite estricto de PII

Los errores se persisten en una tabla dedicada en paralelo a las alertas emitidas al equipo de soporte, bajo dos restricciones fundamentales:

- **Filtrado previo a la persistencia:** No se almacena el payload completo de los webhooks; los números telefónicos y datos identificatorios se excluyen de los registros de error. El log de errores es infraestructura diagnóstica y no debe constituir una réplica desprotegida de datos personales.
- **Consultas parametrizadas en todo escenario:** Previene fallos en la propia rutina de registro provocados por caracteres especiales o comillas presentes en mensajes de error o entradas de usuarios.

El nivel de protección de datos difiere según el tipo de registro, y se está evaluando homogeneizarlo; el detalle se documenta internamente, no publicado aquí.

### 3. Cronograma de retención y anonimización de datos

Un proceso mensual programado ejecuta tareas de depuración en base a la antigüedad y el estado del registro:

- **Anonimización de candidatos:** Registros con antigüedad superior a un año (en estados descartado, entrevista confirmada, entrevista pendiente o completado) son anonimizados en una única pasada, eliminando nombre, correo electrónico, referencia de CV y datos identificatorios, preservando la fila y su resultado para fines estadísticos.
- **Eliminación definitiva:** Registros inactivos por más de seis meses en estados inconclusos (interrumpido, cancelado o expirado) se eliminan de forma permanente.
- **Depuración diferenciada de logs:** Los registros de mensajes se conservan por un año, mientras que los registros de errores se depuran tras 90 días, reflejando la menor vida útil requerida para el diagnóstico de fallas.

**Limitación conocida:** la regla de anonimización aplica el mismo criterio temporal independientemente del resultado final del candidato (descartado o con proceso completo). Queda pendiente evaluar si ambos estados justifican políticas de retención diferenciadas.

## Consecuencias

**Aceptadas:**
- Las consultas analíticas no interfieren con el estado transaccional ni se corrompen ante la anonimización de datos personales.
- El diagnóstico de errores es persistente sin duplicar almacenamiento de PII no supervisado.
- El cronograma de retención responde a criterios formales de protección de datos, facilitando su adaptación ante cambios normativos.

**Compromisos asumidos:**
- Mayor cantidad de componentes a mantener (tabla de eventos, tabla de errores filtrada y flujos de depuración programados).
- Criterios de retención agrupados por antigüedad en lugar de reglas individualizadas por resultado del proceso.
- El nivel de protección de datos difiere según el tipo de registro, y se está evaluando homogeneizarlo; el detalle se documenta internamente, no publicado aquí.
