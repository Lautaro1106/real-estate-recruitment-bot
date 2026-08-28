# ADR-001: Máquina de estados determinista frente a conversación basada en LLM

**Estado:** Aceptado
**Contexto:** Bot de selección de candidatos por WhatsApp para un proceso de calificación regulado

---

## Contexto

La función principal del bot consiste en evaluar postulantes a agentes inmobiliarios frente a un conjunto cerrado de criterios de elegibilidad —disponibilidad, modelo de compensación, respaldo financiero, rango de edad y zona geográfica—, generando una decisión de calificación o rechazo reproducible. No se trata de un asistente conversacional abierto; el conjunto de intenciones a procesar en cada paso es reducido, conocido de antemano y estable a lo largo del tiempo.

La decisión técnica fundamental no residía en la elección del framework de chatbot, sino en determinar si el motor conversacional debía ser **un LLM que interprete el lenguaje libre del candidato** o **una máquina de estados que valide valores conocidos contra reglas explícitas**. Ambos enfoques presentan modos de falla dispares, y el dominio del problema no tolera la variabilidad inherente a un modelo de lenguaje.

## Factores de Decisión

- **Auditabilidad.** Todo descarte debe ser explicable y reproducible a posteriori: las mismas entradas deben generar idéntico resultado en cualquier momento, con motivos trazables a reglas específicas y no a inferencias estadísticas de un modelo.
- **Espacio de intenciones acotado.** Cada pregunta del flujo admite un conjunto pequeño y enumerable de respuestas válidas. No se requiere procesamiento de lenguaje abierto, asemejándose más a un formulario estructurado que a una charla abierta.
- **Costo y confiabilidad a escala.** Una máquina de estados no genera costos de inferencia por mensaje ni introduce riesgo de desvío de comportamiento (*drift*) entre candidatos. Una solución basada en LLM añadiría costos recurrentes y variabilidad sin aportar ventajas funcionales a un proceso de filtrado estricto.

## Alternativas Evaluadas

| Enfoque | Motivo de descarte |
|---|---|
| Conversación basada 100% en LLM (el modelo determina transiciones de estado a partir de texto libre) | No reproducible: una misma respuesta puede interpretarse de forma distinta en ejecuciones sucesivas. Imposibilidad de auditar formalmente la causa exacta de un descarte. Costo recurrente por mensaje sin beneficio para un espacio de intenciones acotado. |
| Enfoque híbrido (LLM para texto libre, determinista para el resto) | Evaluado y descartado para la v1: incorporaba superficie no determinista a un pipeline auditable a cambio de una ganancia marginal de experiencia de usuario, ya que los campos abiertos (ej. motivos de cambio de carrera) no inciden en la puntuación. |
| Máquina de estados determinista (seleccionada) | Cada transición es una regla explícita y verificable sobre datos estructurados. Sin llamadas a modelos, sin desvíos y con total reproducibilidad. |

## Decisión

Implementar el flujo de calificación como una máquina de estados determinista: el paso actual y las respuestas previas determinan unívocamente la siguiente pregunta, y la puntuación final resulta de una función fija sobre los valores almacenados, excluyendo la inferencia de modelos en la ruta de evaluación.

*La estrategia para acotar el espacio de respuestas se documenta de forma independiente en el ADR-002.*

## Cuándo deja de ser la decisión adecuada

Este diseño es válido mientras el espacio de intenciones por paso se mantenga reducido y el vocabulario del dominio sea predecible. Deberá reconsiderarse si el flujo exigiera evaluar respuestas abiertas relevantes para la calificación, o si la cantidad de tipos de preguntas creciera hasta un punto donde el mantenimiento manual de transiciones supere la complejidad de un motor más flexible.

## Revisión de una hipótesis inicial: complejidad de integración

Al momento de adoptar esta decisión, se estableció informalmente un umbral de cuatro integraciones de API fuertemente acopladas en un único orquestador como señal de alerta para migrar hacia un backend personalizado. El sistema superó posteriormente dicho umbral, coordinando actualmente el canal de mensajería, la derivación a operadores, la base de datos principal, el almacenamiento de archivos, el servicio de agendamiento y el CRM (seis puntos de integración).

Al reevaluar la arquitectura, el orquestador ha demostrado sostener la carga operativamente debido a que cada integración opera como una llamada punto a punto aislada y no como lógica interdependiente compleja. El umbral cualitativo original fue útil como punto de control preventivo, aunque su valor cuantitativo resultó conservador. La práctica recomendada consiste en establecer revisiones periódicas de las premisas de escala en lugar de tratarlas como reglas estáticas.

## Consecuencias

**Aceptadas:**
- Ausencia de interpretación de lenguaje libre en el proceso de calificación: cada respuesta se valida contra un conjunto cerrado de valores (mecanismo detallado en ADR-002).
- El descarte es definitivo dentro de una conversación activa, sin reingreso automático tras ser rechazado.
- La lógica reside en la configuración de los flujos de trabajo en lugar de código de aplicación, priorizando auditabilidad y costo operativo sobre flexibilidad conversacional.

**Explícitamente fuera de alcance para esta decisión:** Mecanismos de restricción de entrada en la interfaz (ADR-002), selección de CRM y entrega de correos transaccionales.
