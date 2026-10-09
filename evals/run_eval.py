import json
import os
import sys
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
from src.agent import procesar_solicitud

load_dotenv()

# ==============================================================================
# CONTROL DE VERSIONES DEL PROYECTO
# ==============================================================================
VERSIONES = {
    "modelo_llm": "groq/openai/gpt-oss-120b (v1.0)",
    "prompt_sistema": "v2.1-technova-guardrails",
    "base_conocimiento_rag": "chromadb-v1.2-docs-ti",
    "dataset_evaluacion": "dataset-v2.0-20-casos"
}

# Costos estimados Groq (en USD por 1,000 tokens)
PRECIO_INPUT_POR_1K = 0.0001
PRECIO_OUTPUT_POR_1K = 0.0002

def estimar_tokens_y_costo(texto_entrada: str, texto_salida: str):
    """Calcula una estimación de tokens y costo financiero aproximado."""
    tokens_input = max(1, len(texto_entrada) // 4)
    tokens_output = max(1, len(texto_salida) // 4)
    total_tokens = tokens_input + tokens_output

    costo_input = (tokens_input / 1000) * PRECIO_INPUT_POR_1K
    costo_output = (tokens_output / 1000) * PRECIO_OUTPUT_POR_1K
    costo_total = costo_input + costo_output

    return total_tokens, tokens_input, tokens_output, round(costo_total, 8)

def ejecutar_evaluacion():
    dataset_path = os.path.join(CURRENT_DIR, "dataset.json")
    if not os.path.exists(dataset_path):
        print("❌ Error: No se encontró el archivo evals/dataset.json")
        sys.exit(1)

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    total_casos = len(dataset)
    exitosos = 0
    errores_conteo = 0
    resultados = []

    latencia_total = 0.0
    tokens_acumulados = 0
    costo_acumulado = 0.0

    print(f"📊 Iniciando Evaluación Automatizada sobre {total_casos} casos...\n")

    for caso in dataset:
        cid = caso["id"]
        pregunta_texto = caso["pregunta"]
        categoria = caso["categoria"]
        requiere_tool = caso["requiere_herramienta"]
        debe_bloquear = caso["debe_ser_bloqueado"]

        print(f"[{cid}/{total_casos}] Evaluando ({categoria}): '{pregunta_texto}'")
        
        tiempo_inicio = time.time()
        try:
            respuesta = procesar_solicitud(pregunta_texto, auto_confirm=True)
            tiempo_fin = time.time()
            
            latencia_caso = round(tiempo_fin - tiempo_inicio, 3)
            latencia_total += latencia_caso

            # Estimación de métricas de tokens y costo
            tokens_tot, t_in, t_out, costo_caso = estimar_tokens_y_costo(pregunta_texto, respuesta)
            tokens_acumulados += tokens_tot
            costo_acumulado += costo_caso

            es_exitoso = True
            resp_lower = respuesta.lower()
            
            if debe_bloquear and not any(p in resp_lower for p in ["fuera del alcance", "rechazad", "no disponib", "no autoriz", "cancelad"]):
                es_exitoso = False
            elif requiere_tool and "ticket" not in resp_lower:
                es_exitoso = False
                
            if es_exitoso:
                exitosos += 1
                print(f"   ✅ Correcto | Latencia: {latencia_caso}s | Tokens: {tokens_tot}")
            else:
                errores_conteo += 1
                print(f"   ❌ Inesperado | Latencia: {latencia_caso}s | Tokens: {tokens_tot}")

            resultados.append({
                "id": cid,
                "categoria": categoria,
                "pregunta": pregunta_texto,
                "exitoso": es_exitoso,
                "latencia_segundos": latencia_caso,
                "tokens_estimados": tokens_tot,
                "costo_estimado_usd": f"{costo_caso:.8f}",
                "respuesta": respuesta
            })

        except Exception as e:
            tiempo_fin = time.time()
            latencia_caso = round(tiempo_fin - tiempo_inicio, 3)
            errores_conteo += 1
            print(f"   ❌ Error en ejecución ({latencia_caso}s): {str(e)}")
            resultados.append({
                "id": cid,
                "categoria": categoria,
                "pregunta": pregunta_texto,
                "exitoso": False,
                "latencia_segundos": latencia_caso,
                "error": str(e)
            })

    # Cómputo global de métricas
    tasa_exito = (exitosos / total_casos) * 100.0 if total_casos > 0 else 0.0
    latencia_promedio = round(latencia_total / total_casos, 3) if total_casos > 0 else 0.0

    print("\n" + "="*50)
    print("📈 REPORTE FINAL DE EVALUACIÓN OPERATIVA")
    print(f"Casos procesados:    {total_casos}")
    print(f"Casos exitosos:      {exitosos}")
    print(f"Errores detectados:  {errores_conteo}")
    print(f"Tasa de éxito:       {tasa_exito:.2f}%")
    print(f"Latencia promedio:   {latencia_promedio} s/caso")
    print(f"Tokens totales:      {tokens_acumulados}")
    print(f"Costo estimado:      ${costo_acumulado:.6f} USD")
    print("="*50)

    # Estructura del reporte JSON final con metadatos requeridos por la rúbrica
    reporte_completo = {
        "versionado": VERSIONES,
        "metricas_globales": {
            "tasa_exito_porcentaje": tasa_exito,
            "casos_procesados": total_casos,
            "casos_exitosos": exitosos,
            "total_errores": errores_conteo,
            "latencia_promedio_segundos": latencia_promedio,
            "latencia_total_segundos": round(latencia_total, 3),
            "tokens_totales_estimados": tokens_acumulados,
            "costo_total_estimado_usd": f"{costo_acumulado:.8f}"
        },
        "detalles": resultados
    }

    reporte_path = os.path.join(CURRENT_DIR, "eval_results.json")
    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(reporte_completo, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Reporte detallado guardado en: {reporte_path}")

    # Control de Calidad automatizado (Quality Gate)
    if tasa_exito < 100.0:
        print(f"\n❌ QUALITY GATE FALLIDO: Tasa de éxito del {tasa_exito:.2f}%. Se requiere 100.0%.")
        sys.exit(1)
    else:
        print(f"\n✅ QUALITY GATE APROBADO: Tasa de éxito del {tasa_exito:.2f}%.")
        sys.exit(0)

if __name__ == "__main__":
    ejecutar_evaluacion()