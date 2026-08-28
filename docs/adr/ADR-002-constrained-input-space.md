# ADR-002: Espacio de entrada acotado frente a procesamiento de texto libre

**Estado:** Aceptado
**Contexto:** Bot de selección de candidatos por WhatsApp, máquina de estados determinista (ver ADR-001)

---

## Contexto

El flujo de calificación formula un conjunto fijo de preguntas categóricas —disponibilidad, modelo de compensación, respaldo financiero, zona geográfica, etc.— donde cada respuesta corresponde a una opción dentro de un conjunto cerrado de valores de negocio. El sistema debe persistir dicha respuesta con precisión y evaluarla contra reglas de calificación fijas, con tolerancia cero a ambigüedades: una interpretación errónea compromete la calidad del dato y el cumplimiento del proceso.

El requerimiento arquitectónico central radica en que **el espacio de respuestas posibles en cada paso sea reducido y enumerable**, independientemente del componente de interfaz utilizado para materializarlo. Los botones interactivos constituyeron la primera implementación de esta restricción, no el objetivo en sí mismo.

## Decisión

Acotar el espacio de respuestas en cada paso de calificación a un conjunto cerrado de entradas válidas, tratando el mecanismo concreto de entrada (botones interactivos, opciones numéricas por texto, etc.) como un detalle de implementación sustituible sin alterar la garantía funcional.

**Implementación inicial:** Botones interactivos de WhatsApp. El candidato presiona una opción y la plataforma retorna un `button_reply_id` unívoco, eliminando ambigüedades de procesamiento.

**Modificación por cambio de plataforma:** La arquitectura incorporó posteriormente una capa de atención humana entre la API de WhatsApp y el bot. Dicha capa no preservaba el `button_reply_id`, aplanando las respuestas a texto plano. Si bien el mecanismo original dejó de operar, el requerimiento de mantener un espacio de entrada acotado permaneció invariable.

**Resolución:** Se reemplazaron los botones por opciones numéricas en texto plano ("Responde con el número de tu opción: 1️⃣ ... 2️⃣ ... 3️⃣ ..."), acompañadas de una validación estricta: si la respuesta no coincide con los dígitos esperados, se emite un mensaje de error predefinido solicitando reingresar la opción. Esto restituye la misma garantía técnica: el mensaje coincide con un valor esperado o no avanza el estado.

## Relevancia como principio de diseño

Formular el requerimiento como "reducir la entropía de la entrada del usuario" en lugar de "utilizar botones" otorgó resiliencia al sistema frente a cambios de infraestructura externos. Una definición técnica rígida hubiera requerido rediseñar el flujo ante la pérdida de soporte de botones interactivos; al abstraer el principio de diseño, la solución se limitó a un reemplazo de mecanismo sin alterar la lógica de evaluación, el esquema de datos ni las reglas de negocio.

## Detalle de implementación: traducción en el borde

Las respuestas numéricas ("1", "2", "3") se transforman a su valor semántico de negocio (ej. `full_time`, `part_time`, `hours_only`) en la misma sentencia de persistencia en base de datos (`CASE` en SQL), en lugar de almacenarse como dígitos crudos para su interpretación diferida.

Esto evita que particularidades de la interfaz se propaguen al resto de los componentes (calificación, sincronización con CRM, reportes), los cuales operan exclusivamente sobre valores semánticos estables. Ante futuros cambios en los canales de entrada, únicamente se adapta la capa de traducción en el borde.

**Compromiso asumido:** Esta traducción se declara por cada pregunta en su respectiva consulta. Para cinco preguntas categóricas, este enfoque mantiene cada consulta autocontenida y de bajo costo de mantenimiento. Si el volumen de preguntas creciera significativamente, se justificaría abstraer la lógica en una tabla o función de mapeo compartida.

## Limitación conocida

No existe escalamiento automático a un operador humano tras intentos consecutivos de respuesta inválida. El sistema solicita reintentar la entrada sin un límite estricto de iteraciones; la derivación a un reclutador ocurre cuando el usuario expresa explícitamente una solicitud de asistencia humana reconocida por el sistema.

Este comportamiento fue identificado en la etapa de diseño y se mantuvo postergado al no observarse fricción operativa en producción que justificara complejizar el flujo de control. Queda documentado como una mejora pendiente y no como una funcionalidad cerrada.

## Incidente en producción: campo de texto libre sin validar

El principio de entrada acotada se diseñó originalmente para las preguntas categóricas, pero no se aplicó inicialmente a los campos de texto libre (como el nombre del candidato).

Esto derivó en un incidente en producción cuando una entrada con caracteres no previstos provocó un fallo en la construcción de los mensajes de salida posteriores, bloqueando el avance del estado del candidato.

### Resolución

Se adoptaron dos decisiones correctivas a nivel de arquitectura:
1. **Validación estructural de texto libre:** Se extendió el principio de este ADR al campo de nombre mediante validaciones de formato (rechazo de entradas multilínea, límites de longitud y filtrado de repeticiones del propio prompt), aplicando el patrón estándar de rechazo y repetición de la pregunta.
2. **Construcción segura de payloads:** Se revisaron y endurecieron todas las salidas del sistema hacia APIs externas para garantizar la serialización estructurada de cualquier valor interpolado, eliminando la fragilidad ante entradas arbitrarias.

## Consecuencias

**Aceptadas:**
- El bot no procesa lenguaje libre en los pasos de calificación: cada respuesta se valida contra un conjunto cerrado antes de avanzar.
- Incorporar una nueva opción requiere actualizar el texto de la pregunta, la regla de validación y la lógica de mapeo correspondiente.

**Pendiente:**
- Límite estricto de reintentos con derivación automática a operador ante fallos de validación reiterados.

**Resuelto:**
- Validación estructural en campos de texto libre (nombre) y serialización estructurada y segura en todas las comunicaciones salientes.

**Fuera de alcance:**
- Centralización del mapeo de opciones numéricas a valores semánticos en una capa unificada, justificable únicamente ante un incremento sustancial en la cantidad de preguntas.
