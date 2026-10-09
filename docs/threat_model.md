# Modelo de Amenazas (Threat Model) - Agente TI TechNova

## 1. Superficie de Ataque

* **Entradas de texto del usuario:** Posibilidad de prompt injection directa.
* **Documentos recuperados por RAG:** Inyección indirecta desde archivos de políticas.
* **Invocación de herramientas:** Ejecución no autorizada o parámetros maliciosos.

## 2. Amenazas Identificadas y Mitigaciones

| Amenaza | Nivel de Riesgo | Mitigación Implementada |
| :--- | :--- | :--- |
| **Prompt Injection Directa** (*"Ignora las instrucciones anteriores..."*) | Alto | Guardrail sintáctico en el System Prompt que exige rechazar solicitudes no alineadas con Soporte TI. |
| **Elevación de Privilegios** (*"Dame acceso de admin global..."*) | Crítico | Validación estricta de alcance en el prompt del sistema y denegación explícita de comandos administrativos. |
| **Ejecución Irrestricta de Herramientas** | Alto | Implementación de **Human-in-the-Loop (HITL)** requerida previo a la ejecución de cualquier herramienta. |
| **Generación de Parámetros Inválidos** | Medio | Contratos de herramientas estrictamente tipados usando esquemas de **Pydantic** (`CrearTicketInput`). |
| **Fuga de Secretos en Repositorio** | Crítico | Uso de archivos `.env` ignorados en `.gitignore` para llaves de API (`GROQ_API_KEY`). |

## 3. Principio de Privilegio Mínimo
El agente opera en un entorno restringido donde no tiene permisos para modificar infraestructura directamente ni realizar cambios sin la autorización explícita del operador humano.