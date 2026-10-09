# Arquitectura del Agente TI - TechNova

## Visión General
El Agente TI de TechNova es un sistema de IA autónomo diseñado para resolver consultas técnicas de colaboradores y automatizar la gestión de tickets de soporte técnico de primer nivel.

## Diagrama de Arquitectura

```text
[ Usuario ] 
    │
    ▼
[ Entradas / Prompts ]
    │
    ▼
┌────────────────────────────────────────────────────────┐
│              Flujo Principal del Agente                │
├────────────────────────────────────────────────────────┤
│ 1. Guardrails & Filtro de Alcance (Input Guardrail)   │
│ 2. Recuperación RAG (VectorStore Chroma DB)            │
│ 3. Orquestación LLM (Groq / openai/gpt-oss-120b)       │
│ 4. Verificación de Intención de Herramientas          │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
  [ Respuesta Directa ]    [ Solicitud de Acción ]
  (Consulta / Políticas)                 │
                                         ▼
                             ⚠️ APROBACIÓN HUMANA ⚠️
                            (Punto de Control HITL)
                                         │
                                ┌────────┴────────┐
                                ▼                 ▼
                           [ Aprobado ]      [ Rechazado ]
                                │                 │
                                ▼                 ▼
                       [ Pydantic Tool ]    [ Notificación ]
                     (crear_ticket_soporte)