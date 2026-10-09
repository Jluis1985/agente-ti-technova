import sys
from pydantic import BaseModel, Field
from typing import Optional

# 1. Esquema Pydantic para validar los entrada de la herramienta (Contrato Tipado)
class CrearTicketInput(BaseModel):
    usuario: str = Field(description="Nombre o correo del usuario que solicita el ticket.")
    categoria: str = Field(description="Categoría del problema (ej. 'Contraseñas', 'Hardware', 'Software', 'Acceso VPN').")
    descripcion: str = Field(description="Detalle o resumen claro del problema reportado.")
    prioridad: str = Field(default="Media", description="Prioridad asignada: 'Baja', 'Media', 'Alta' o 'Crítica'.")

# 2. Función de Aprobación Humana (Human-in-the-Loop)
def solicitar_aprobacion_humana(accion: str, detalles: dict) -> bool:
    """
    Detiene la ejecución para solicitar confirmación explícita en consola.
    """
    print("\n" + "="*50)
    print("⚠️  PUNTO DE APROBACIÓN HUMANA REQUERIDO ⚠️")
    print(f"Acción a realizar: {accion}")
    print("Detalles del ticket:")
    for clave, valor in detalles.items():
        print(f"  - {clave.capitalize()}: {valor}")
    print("="*50)
    
    respuesta = input("\n¿Autorizas la ejecución de esta acción? (s/n): ").strip().lower()
    return respuesta in ["s", "si", "sí", "y", "yes"]

# 3. Herramienta principal de la aplicación
def crear_ticket_soporte(params: CrearTicketInput) -> str:
    """
    Crea un ticket en el sistema de Soporte TI previa aprobación humana.
    """
    detalles = params.model_dump()
    
    # Evaluar si la acción requiere aprobación (ej. prioridad Alta/Crítica o creación de ticket)
    aprobado = solicitar_aprobacion_humana("Crear Ticket de Soporte TI", detalles)
    
    if not aprobado:
        return "❌ OPERACIÓN CANCELADA: El usuario/supervisión rechazó la aprobación humana."
    
    # Simulación de creación de ticket exitosa (puedes conectar un API real de Jira/Zendesk si quisieras)
    id_ticket = "TK-90821"
    return f"✅ TICKET CREADO CON ÉXITO: ID {id_ticket}. Asignado a Soporte TI (Nivel 1) con prioridad {params.prioridad}."

# Prueba local rápida
if __name__ == "__main__":
    print("🧪 Probando herramienta de creación de ticket...")
    
    # Datos de prueba
    datos_prueba = CrearTicketInput(
        usuario="empleado@technova.com",
        categoria="Contraseñas",
        descripcion="Bloqueo de cuenta por rebasar intentos fallidos.",
        prioridad="Alta"
    )
    
    resultado = crear_ticket_soporte(datos_prueba)
    print("\nResultado:")
    print(resultado)