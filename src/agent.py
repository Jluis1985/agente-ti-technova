import warnings
import os
import sys
import logging
from dotenv import load_dotenv

# Ocultar advertencias de la terminal
warnings.filterwarnings("ignore")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ==============================================================================
# CONFIGURACIÓN DEL LOGGER OPERATIVO (OBSERVABILIDAD DEDICADA A ARCHIVO)
# ==============================================================================
# 1. Configurar manejador exclusivo para el archivo de logs
file_handler = logging.FileHandler("agente_operacion.log", encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
)

# 2. Configurar logger del agente
logger = logging.getLogger("TechNovaAgent")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# 3. Silenciar logs HTTP externos (httpx) para evitar ruido de peticiones de red
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from retrieval import buscar_evidencia, formatear_contexto
from tools import crear_ticket_soporte, CrearTicketInput

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
    """Procesa la solicitud rastreando el flujo operativo completo en agente_operacion.log"""
    logger.info(f"📥 [NUEVA SOLICITUD] Recibida: '{pregunta_usuario}'")

    # 1. Guardrail de Seguridad Primario
    if es_solicitud_maliciosa(pregunta_usuario):
        logger.warning(f"⚠️ [GUARDRAIL TRIGGER] Intento de inyección o acción no autorizada detectada.")
        return "⚠️ Acción no autorizada: La solicitud contiene comandos restringidos o intenta acceder a información sensible del sistema."

    # 2. Detección de intención para acción de ticket (Tools & HITL)
    texto_lower = pregunta_usuario.lower()
    verbos_accion = ["crea", "crear", "genera", "generar", "abre", "abrir", "creen", "generen", "abran"]
    
    tiene_palabra_ticket = "ticket" in texto_lower
    pide_estructura_ticket = any(verbo in texto_lower for verbo in verbos_accion) and any(p in texto_lower for p in ["estructura del problema", "detalles del ticket", "falla en el servidor"])
    
    intencion_crear = (tiene_palabra_ticket and any(verbo in texto_lower for verbo in verbos_accion)) or pide_estructura_ticket

    if intencion_crear:
        logger.info("🛠️ [TOOL INTENT] Solicitud requiere ejecución de herramienta 'crear_ticket'.")
        logger.warning("⚠️ [HITL TRIGGER] Interrupción generada. Se requiere Aprobación Humana (HITL).")
        
# Detección de auto-confirmación o entorno CI (GitHub Actions)
        modo_ci = os.getenv("CI") == "true" or os.getenv("AUTO_APPROVE") == "true"

        if not auto_confirm and not modo_ci:
            print(f"\n==================================================")
            print(f"⚠️  PUNTO DE APROBACIÓN HUMANA REQUERIDO ⚠️")
            print(f"Solicitud de ticket detectada.")
            print(f"==================================================")
            logger.info("👤 [HITL WAITING] Esperando confirmación manual del usuario/supervisor...")
            confirmacion = input("¿El operador autoriza la ejecución de esta acción? (s/n): ").strip().lower()
            if confirmacion != 's':
                logger.warning("❌ [HITL REJECTED] Operación cancelada por el usuario o supervisión.")
                return "⛔ Solicitud de ticket cancelada: La acción no fue autorizada por el supervisor/operador de TI."
            logger.info("✅ [HITL APPROVED] Operación autorizada por el usuario/supervisor.")
        else:
            logger.info("👤 [HITL EVALUATION] Aprobación simulada por entorno de pruebas / CI.")
            
        # Invocación directa y limpia de la herramienta usando el esquema Pydantic
        try:
            logger.info("🛠️ [TOOL EXECUTION] Ejecutando herramienta 'crear_ticket_soporte' con esquema Pydantic...")
            ticket_input = CrearTicketInput(
                usuario="usuario@technova.com",
                categoria="Soporte TI",
                descripcion=pregunta_usuario,
                prioridad="Alta"
            )
            resultado_tool = crear_ticket_soporte(ticket_input)
            logger.info("✅ [TOOL SUCCESS] Ticket registrado exitosamente.")
        except Exception as err_tool:
            logger.error(f"❌ [TOOL ERROR] Fallo técnico al registrar ticket: {str(err_tool)}")
            return f"⚠️ Ocurrió un fallo técnico al registrar el ticket: {str(err_tool)}"

        return f"Ticket procesado correctamente: {resultado_tool}"

    # 3. Normalización e Inserción RAG
    consulta_rag = pregunta_usuario
    if any(w in pregunta_usuario.lower() for w in ["bloqueado", "bloqueo", "bloqueada"]):
        consulta_rag = "bloqueo de cuenta contraseña intentos fallidos active directory"

    logger.info(f"🔍 [RETRIEVAL] Consultando base de vectores para: '{consulta_rag}'")
    evidencias = buscar_evidencia(consulta_rag)
    contexto = formatear_contexto(evidencias)
    logger.info(f"📚 [RETRIEVAL] Contexto recuperado y formateado con éxito.")

    # 4. Invocación Segura de la Cadena RAG + LLM
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
    
    logger.info("🤖 [LLM CALL] Invocando modelo Groq...")
    chain = prompt_template | llm
    respuesta = chain.invoke({"contexto": contexto, "pregunta": pregunta_usuario})
    logger.info("💡 [LLM RESPONSE] Respuesta del modelo recibida con éxito.")
    
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