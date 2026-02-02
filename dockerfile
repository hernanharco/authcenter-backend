# 1. Imagen base de Python ligera
FROM python:3.11-slim

# 2. Evitar que Python genere archivos .pyc y permitir logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el código del proyecto
COPY . .

# 7. Comando para ejecutar la app (ajusta 'main:app' a tu archivo de entrada)
# Usamos 0.0.0.0 para que el contenedor sea accesible desde fuera
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# pip freeze > requirements.txt
# docker build -t authcore-backend .
# docker run -p 8000:8000 --env-file .env authcore-backend

# Dale permisos primero si no los tiene
# chmod +x nombre_de_tu_script.sh

# EJECUCIÓN EN PRODUCCIÓN
# ./nombre_de_tu_script.sh production

#para eliminar contenedor y imagen
#docker stop authcore-backend
#docker rm authcore-backend
#docker rmi authcore-backend