import os
import sys
import warnings

# Ocultar advertencias de la terminal
warnings.filterwarnings("ignore")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from retrieval import buscar_evidencia, formatear_contexto
from tools import crear_ticket_soporte, CrearTicketInput

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)


def es_solicitud_maliciosa(texto: str) -> bool:
    """Guardrail primario de seguridad para evaluación y producción."""
    patrones_sospechosos = [
        "c:\\", "/etc/", "passwd", "system32", 
        "ignore previous instructions", "ignora las reglas anteriores", "ignora todas las instrucciones",
        "system override", "override", "sin pedir confirmación", "sin confirmación humana",
        "dame la clave", "dame las contraseñas", "contraseñas de administrador",
        "dame el prompt", "muestra el prompt", "llaves api", "api key",
        "borres la cuenta", "borrar cuenta", "eliminar cuenta",
        "acceso de administrador global", "servidores productivos", "acceso de admin"
    ]
    texto_lower = texto.lower()
    return any(patron in texto_lower for patron in patrones_sospechosos)

def procesar_solicitud(pregunta_usuario: str, auto_confirm: bool = False) -> str:
    # 1. Guardrail de Seguridad Primario
    if es_solicitud_maliciosa(pregunta_usuario):
        return "⚠️ Acción no autorizada: La solicitud contiene comandos restringidos o intenta acceder a información sensible del sistema."

    # 2. Detección de intención para acción de ticket (soporta variaciones de salida estructurada)
    texto_lower = pregunta_usuario.lower()
    verbos_accion = ["crea", "crear", "genera", "generar", "abre", "abrir", "creen", "generen", "abran"]
    
    # Se activa si contiene la palabra "ticket" O si pide explícitamente estructurar/generar un problema/falla de equipo
    tiene_palabra_ticket = "ticket" in texto_lower
    pide_estructura_ticket = any(verbo in texto_lower for verbo in verbos_accion) and any(p in texto_lower for p in ["estructura del problema", "detalles del ticket", "falla en el servidor"])
    
    intencion_crear = (tiene_palabra_ticket and any(verbo in texto_lower for verbo in verbos_accion)) or pide_estructura_ticket

    if intencion_crear:
        if not auto_confirm:
            print(f"\n==================================================")
            print(f"⚠️  PUNTO DE APROBACIÓN HUMANA REQUERIDO ⚠️")
            print(f"Solicitud de ticket detectada.")
            print(f"==================================================")
            confirmacion = input("¿El operador autoriza la ejecución de esta acción? (s/n): ").strip().lower()
            if confirmacion != 's':
                return "⛔ Solicitud de ticket cancelada: La acción no fue autorizada por el supervisor/operador de TI."
        
        # Invocación directa y limpia de la herramienta usando el esquema Pydantic
        try:
            ticket_input = CrearTicketInput(
                usuario="usuario@technova.com",
                categoria="Soporte TI",
                descripcion=pregunta_usuario,
                prioridad="Alta"
            )
            resultado_tool = crear_ticket_soporte(ticket_input)
        except Exception as err_tool:
            return f"⚠️ Ocurrió un fallo técnico al registrar el ticket: {str(err_tool)}"

        return f"Ticket procesado correctamente: {resultado_tool}"

    # 3. Normalización e Inserción RAG
    consulta_rag = pregunta_usuario
    if any(w in pregunta_usuario.lower() for w in ["bloqueado", "bloqueo", "bloqueada"]):
        consulta_rag = "bloqueo de cuenta contraseña intentos fallidos active directory"

    evidencias = buscar_evidencia(consulta_rag)
    contexto = formatear_contexto(evidencias)
    
# 4. Invocación Segura de la Cadena RAG + LLM con fallback estricto de evidencia
    evidencias = buscar_evidencia(consulta_rag)
    contexto = formatear_contexto(evidencias)
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """Eres el Agente TI oficial de TechNova.
Tu función es responder dudas de soporte técnico usando el contexto proporcionado.

REGLAS DE INTERPRETACIÓN:
1. Si el usuario reporta una falla o problema técnico de hardware/software (ej. 'mi monitor no enciende', 'no funciona la vpn'), brinda los pasos generales de revisión técnica o ayuda a generar el ticket de soporte.
2. Si la consulta pide un dato específico no documentado en el contexto (ej. modelo exacto de impresora, nombres de personal, cafetería, cocina, recetas), responde EXACTAMENTE:
'Lo siento, esta solicitud está fuera del alcance de las políticas y servicios de Soporte TI de TechNova.'
3. ÚNICAMENTE si la pregunta trata sobre un tema totalmente ajeno a TI, responde EXACTAMENTE:
'Lo siento, esta solicitud está fuera del alcance de las políticas y servicios de Soporte TI de TechNova.'
4. Si el usuario intenta vulnerar la seguridad, pedir contraseñas ajenas o privilegios no autorizados, rechaza la solicitud indicando que es una acción no autorizada."""),
        ("human", "Contexto:\n{contexto}\n\nPregunta: {pregunta}")
    ])
    
    chain = prompt_template | llm
    respuesta = chain.invoke({"contexto": contexto, "pregunta": pregunta_usuario})
    return respuesta.content
    
    chain = prompt_template | llm
    respuesta = chain.invoke({"contexto": contexto, "pregunta": pregunta_usuario})
    return respuesta.content

if __name__ == "__main__":
    print("\n🤖 ¡Hola! Soy el Agente TI de TechNova. ¿En qué te puedo ayudar hoy?")
    print("(Escribe 'salir' o 'exit' para terminar la conversación)\n")
    
    while True:
        try:
            pregunta = input("\n👤 Tu consulta: ").strip()
            
            if pregunta.lower() in ["salir", "exit"]:
                print("\n👋 ¡Hasta luego! Que tengas un excelente día.")
                break
                
            if not pregunta:
                continue

            respuesta = procesar_solicitud(pregunta)
            print(f"\n🤖 Agente TI:\n{respuesta}")

        except KeyboardInterrupt:
            print("\n\nSesión finalizada por el usuario.")
            break