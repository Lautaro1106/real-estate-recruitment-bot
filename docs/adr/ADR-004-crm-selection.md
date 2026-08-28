# ADR-004: Selección de CRM — Iteración hacia una solución nativa de reclutamiento

**Estado:** Aceptado (adoptado tras dos evaluaciones previas)
**Contexto:** Necesidad de visibilidad del pipeline y seguimiento de candidatos post-entrevista, externo al bot de WhatsApp

---

## Contexto

Una vez que un candidato supera la etapa de evaluación en WhatsApp, el seguimiento posterior (resultado de entrevistas, estado de ofertas, contacto futuro) excede el alcance de una máquina de estados conversacional y corresponde a un sistema de gestión de relaciones (CRM) orientado a procesos de selección.

La selección final fue el resultado de tres iteraciones sucesivas, donde cada alternativa evidenció requerimientos no cubiertos por la anterior.

## Alternativas Evaluadas (en orden cronológico)

**1. Zoho Recruit — descartado antes del despliegue.**
La sobrecarga de configuración y administración resultaba desproporcionada para la etapa inicial del proyecto, no justificando el costo de mantenimiento frente al valor aportado en ese momento.

**2. HubSpot CRM (nivel gratuito) — seleccionado, utilizado y posteriormente reemplazado.**
Presentaba ventajas operativas inmediatas: sin infraestructura que administrar, nodo nativo de integración en n8n y un pipeline visual adaptable a un embudo de reclutamiento. Operó satisfactoriamente durante una primera etapa.

Limitaciones observadas: el modelo de datos de la plataforma está orientado a ventas y no a contratación. Aunque es posible mapear candidatos a contactos y negocios, la incorporación de nuevas funciones requería adaptaciones forzadas, y la automatización de seguimiento a postulantes se encontraba restringida a planes de pago.

**3. Odoo (Community, autohospedado) — seleccionado.**
Dispone de un módulo de reclutamiento diseñado de forma nativa para este flujo, e incluye automatizaciones de seguimiento sin costos de suscripción adicionales. Se optó por la modalidad autohospedada para preservar la soberanía de los datos y mantener consistencia con el resto de la infraestructura autohospedada basada en Docker.

## Sobre el proceso iterativo de selección

Las herramientas iniciales podrían haberse adaptado con mayor esfuerzo de configuración; no obstante, con un sistema en producción y candidatos activos, se priorizó migrar hacia una plataforma con soporte nativo para el dominio del problema antes que forzar herramientas desalineadas con el caso de uso.

## Decisión

Adoptar Odoo 17 Community en modalidad autohospedada como CRM principal para la gestión de candidatos post-evaluación. Los datos se sincronizan desde el flujo de WhatsApp mediante su API REST una vez alcanzada la etapa correspondiente.

## Consecuencias

**Aceptadas:**
- La lógica de gestión de estados y seguimiento a postulantes es administrada de forma nativa por Odoo, simplificando significativamente los flujos de sincronización en n8n.
- Se asumió el costo temporal de haber implementado y descartado dos integraciones previas hasta dar con la herramienta adecuada.

**Compromiso actual:**
- Tras haber asumido el costo de migración en dos oportunidades, la plataforma actual se considera definitiva salvo requerimientos de cambio de orden mayor.
