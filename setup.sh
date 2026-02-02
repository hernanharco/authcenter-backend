#!/bin/bash

# Colores para la terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Determinar el modo y convertir a minúsculas para evitar errores (Ej: Prod -> production)
MODE=$(echo "${1:-development}" | tr '[:upper:]' '[:lower:]')

echo -e "${BLUE}🚀 Iniciando AuthCore Backend en modo: ${GREEN}${MODE}${NC}"

# 1. Configurar variables y comando de ejecución según el modo
if [ "$MODE" == "production" ]; then
    ENV_TAG="production"
    DEBUG_VAL="false"
    PORT=8000
    # En producción usamos Gunicorn para mayor estabilidad y múltiples procesos
    EXEC_CMD="gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000"
else
    ENV_TAG="development"
    DEBUG_VAL="true"
    PORT=8000
    # En desarrollo usamos uvicorn con --reload para ver cambios en vivo
    EXEC_CMD="uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
fi

# 2. Sincronizar dependencias (Recuerda estar en tu venv si lo haces local)
echo -e "${BLUE}📦 Sincronizando dependencias en requirements.txt...${NC}"
pip freeze > requirements.txt

# 3. Construir la imagen (Docker usará el caché si el requirements no cambió)
echo -e "${BLUE}🏗️ Construyendo imagen de Docker...${NC}"
docker build -t authcore-backend .

# 4. Limpieza de contenedores previos para evitar conflictos de nombre
echo -e "${BLUE}🛑 Limpiando contenedores antiguos...${NC}"
docker stop authcore-backend 2>/dev/null || true
docker rm authcore-backend 2>/dev/null || true

# 5. Ejecución con INYECCIÓN DE VARIABLES 💉
# Pasamos $EXEC_CMD al final para sobrescribir el CMD del Dockerfile
echo -e "${GREEN}🏃 Corriendo contenedor en puerto ${PORT}...${NC}"
docker run -d \
  --name authcore-backend \
  -p ${PORT}:8000 \
  --env-file .env \
  -e ENVIRONMENT=$ENV_TAG \
  -e DEBUG=$DEBUG_VAL \
  authcore-backend $EXEC_CMD

echo -e "${GREEN}✅ ¡SaaS Modular Activo!${NC}"
echo -e "Modo: ${BLUE}$ENV_TAG${NC} | Puerto: ${BLUE}$PORT${NC}"
echo -e "Comando: ${BLUE}$EXEC_CMD${NC}"