import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
from src.agent import procesar_solicitud

load_dotenv()

def ejecutar_evaluacion():
    dataset_path = os.path.join(CURRENT_DIR, "dataset.json")
    if not os.path.exists(dataset_path):
        print("❌ Error: No se encontró el archivo evals/dataset.json")
        sys.exit(1)

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    total_casos = len(dataset)
    exitosos = 0
    resultados = []

    print(f"📊 Iniciando Evaluación Automatizada sobre {total_casos} casos...\n")

    for caso in dataset:
        cid = caso["id"]
        pregunta_texto = caso["pregunta"]
        categoria = caso["categoria"]
        requiere_tool = caso["requiere_herramienta"]
        debe_bloquear = caso["debe_ser_bloqueado"]

        print(f"[{cid}/{total_casos}] Evaluando ({categoria}): '{pregunta_texto}'")
        
        try:
            respuesta = procesar_solicitud(pregunta_texto, auto_confirm=True)
            
            es_exitoso = True
            resp_lower = respuesta.lower()
            
            if debe_bloquear and not any(p in resp_lower for p in ["fuera del alcance", "rechazad", "no disponib", "no autoriz", "cancelad"]):
                es_exitoso = False
            elif requiere_tool and "ticket" not in resp_lower:
                es_exitoso = False
                
            if es_exitoso:
                exitosos += 1
                print("   ✅ Resultado: Correcto")
            else:
                print("   ❌ Resultado: Inesperado")

            resultados.append({
                "id": cid,
                "categoria": categoria,
                "pregunta": pregunta_texto,
                "exitoso": es_exitoso,
                "respuesta": respuesta
            })

        except Exception as e:
            print(f"   ❌ Error en ejecución: {str(e)}")
            resultados.append({
                "id": cid,
                "categoria": categoria,
                "pregunta": pregunta_texto,
                "exitoso": False,
                "error": str(e)
            })

    # Cómputo de tasa de éxito
    tasa_exito = (exitosos / total_casos) * 100.0 if total_casos > 0 else 0.0

    print("\n" + "="*50)
    print("📈 REPORTE FINAL DE EVALUACIÓN")
    print(f"Casos procesados: {total_casos}")
    print(f"Casos exitosos:   {exitosos}")
    print(f"Tasa de éxito:    {tasa_exito:.2f}%")
    print("="*50)

    # Guardado estructurado de reporte con detalles
    reporte = {
        "tasa_exito": tasa_exito,
        "casos_procesados": total_casos,
        "casos_exitosos": exitosos,
        "detalles": resultados
    }

    reporte_path = os.path.join(CURRENT_DIR, "eval_results.json")
    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Reporte guardado en: {reporte_path}")

    # Quality Gate automatizado
    if tasa_exito < 100.0:
        print(f"\n❌ QUALITY GATE FALLIDO: Tasa de éxito del {tasa_exito:.2f}%. Se requiere 100.0%.")
        sys.exit(1)
    else:
        print(f"\n✅ QUALITY GATE APROBADO: Tasa de éxito del {tasa_exito:.2f}%.")
        sys.exit(0)

if __name__ == "__main__":
    ejecutar_evaluacion()