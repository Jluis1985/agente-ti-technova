# 📖 Documentación de Observabilidad, Limitaciones y Operación

## 1. Limitaciones Conocidas
* **Dependencia de Proveedor LLM (Groq API):** El rendimiento del agente está sujeto a la disponibilidad, límites de tasa (*rate limits*) y latencia de la infraestructura de Groq.
* **Modelo RAG Estático:** La base de conocimiento basada en ChromaDB no se actualiza en tiempo real; requiere volver a ejecutar el proceso de ingesta cuando se modifican las políticas de TI.
* **Aprobación HITL en CI:** La auto-aprobación en el pipeline de CI/CD simula la confirmación humana mediante variables de entorno (`CI="true"`), lo cual valida la lógica pero no sustituye la interfaz de usuario final para operadores en producción.

## 2. Riesgos Operativos y Mitigación
| Riesgo | Impacto | Estrategia de Mitigación |
| :--- | :--- | :--- |
| **Agotamiento de cuota de API (Groq)** | Alto | Fallback programado o notificación de alerta mediante logs en `agente_operacion.log`. |
| **Inyección de Prompts Complejos** | Medio | Guardrail primario `es_solicitud_maliciosa()` y validación previa de entrada antes de invocar al LLM. |
| **Acciones destructivas no autorizadas** | Alto | Punto de interrupción Human-In-The-Loop (HITL) obligatorio para la creación/modificación de tickets. |

## 3. Estrategia de Reversión (Rollback)
En caso de detectar fallos en el ambiente de prueba o producción tras un nuevo despliegue:

1. **Reversión de Código y Git:**
   ```bash
   git revert HEAD
   git push origin main