#!/bin/bash
set -e

echo "=================================================="
echo "🔄 INICIANDO PROCESO REPETIBLE DE DESPLIEGUE (STAGING)"
echo "=================================================="

# 1. Validar variables de entorno
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ Error: La variable GROQ_API_KEY no está definida."
    exit 1
fi

# 2. Ejecutar Quality Gate
echo "🧪 [PASO 1/3] Ejecutando Quality Gate de Evaluación..."
python evals/run_eval.py

# 3. Construir Contenedor Docker
echo "🐳 [PASO 2/3] Construyendo imagen de Docker..."
docker build -t technova-agent:staging .

# 4. Desplegar Contenedor
echo "🚀 [PASO 3/3] Levantando instancia en ambiente de prueba..."
docker stop technova_staging_container || true
docker rm technova_staging_container || true

docker run -d --name technova_staging_container \
  -e GROQ_API_KEY="$GROQ_API_KEY" \
  technova-agent:staging

echo "=================================================="
echo "✅ DESPLIEGUE EN PRUEBA COMPLETADO Y OPERATIVO"
echo "=================================================="