# Imagen base liviana de Python
FROM python:3.11-slim

# Evitar la generación de archivos .pyc y forzar salida de logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del proyecto
COPY . .

# Exponer el puerto de ejecución (útil si se despliega API/UI)
EXPOSE 8000

# Comando por defecto para ejecutar las pruebas del Quality Gate
CMD ["python", "evals/run_eval.py"]