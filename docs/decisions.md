# Registro de Decisiones de Arquitectura (ADR)

## ADR-001: Selección del Proveedor de LLM (Groq API)

* **Estatus:** Aprobado
* **Contexto:** Inicialmente se consideraron proveedores como OpenAI y Anthropic. Sin embargo, el entorno requería alta velocidad de inferencia, costo cero para desarrollo/evaluación y baja latencia en llamadas repetitivas.
* **Decisión:** Se seleccionó **Groq** utilizando el modelo **`openai/gpt-oss-120b`**.
* **Consecuencias:**
  * **Calidad:** Excelente razonamiento estructurado para la detección de intenciones y generación de respuestas fundamentadas.
  * **Latencia:** Respuestas por debajo de 1 segundo por llamada.
  * **Costo:** Cero costo de ejecución en la infraestructura de prueba de Groq.

---

## ADR-002: Estrategia RAG y Base de Datos Vectorial

* **Estatus:** Aprobado
* **Contexto:** Se requiere responder preguntas basándose estrictamente en políticas corporativas internas de TechNova para evitar alucinaciones.
* **Decisión:** Implementar **Chroma DB** como VectorStore persistente local con la estrategia de recuperación top-k (`k=3`).
* **Consecuencias:**
  * Respuestas 100% fundamentadas con evidencia recuperada.
  * Independencia de bases de datos remotas durante el testing.

---

## ADR-003: Punto de Aprobación Humana (Human-in-the-Loop)

* **Estatus:** Aprobado
* **Contexto:** La ejecución desatendida de herramientas de negocio (creación de tickets) puede generar registros duplicados o no autorizados.
* **Decisión:** Requerir aprobación explícita mediante consola (`s/n`) o parámetro de confirmación antes de la llamada a la función `crear_ticket_soporte`.
* **Consecuencias:**
  * Garantía de seguridad operacional.
  * Cumplimiento del requisito crítico de la evaluación del proyecto.