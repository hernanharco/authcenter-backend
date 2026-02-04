#!/bin/bash

# --- Definición de Colores ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color (Reset)
BOLD='\033[1m'

# --- Iconos Estéticos ---
CHECK="✅"
INFO="ℹ️"
ROCKET="🚀"
GEAR="⚙️"
WARN="⚠️"
DOCKER="🐳"
CLEAN="🧹"
BUILD="🏗️"

# 1. Cargar variables desde el .env
if [ -f .env ]; then
    TITLE_BACKEND=$(grep TITLE_BACKEND .env | cut -d '=' -f2)
else
    echo -e "${RED}${WARN} ERROR:${NC} No se encontró el archivo .env"
    exit 1
fi

# 2. Preparar nombres (Docker exige minúsculas)
TITLE_LOWERCASE=${TITLE_BACKEND,,}
IMAGE_NAME="ima_${TITLE_LOWERCASE}"
CONTAINER_NAME="cont_${TITLE_LOWERCASE}"

MODE=$(echo "${1:-development}" | tr '[:upper:]' '[:lower:]')

echo -e "${BLUE}${BOLD}=========================================${NC}"
echo -e "${BLUE}${BOLD}    ${ROCKET} ${TITLE_BACKEND} MANAGER        ${NC}"
echo -e "${BLUE}${BOLD}=========================================${NC}"

# 3. Lógica por Entorno
if [ "$MODE" == "production" ]; then
    ENV_TAG="production"
    PORT=8001
    EXEC_CMD="gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8001"
    
    echo -e "${GREEN}${DOCKER} MODO:${NC} ${BOLD}PRODUCCIÓN${NC}"
    echo -e "${BLUE}${BUILD} Construyendo imagen:${NC} ${IMAGE_NAME}..."
    
    # Construcción con seguro de fallos
    docker build -t ${IMAGE_NAME}:latest . || { echo -e "${RED}${WARN} Falló el build${NC}"; exit 1; }

    echo -e "${YELLOW}${CLEAN} Limpiando contenedores previos...${NC}"
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true

    echo -e "${GREEN}${ROCKET} Lanzando contenedor desacoplado...${NC}"
    docker run -d \
      --name ${CONTAINER_NAME} \
      -p ${PORT}:8001 \
      --env-file .env \
      -e ENVIRONMENT=$ENV_TAG \
      ${IMAGE_NAME}:latest $EXEC_CMD

else
    ENV_TAG="development"
    PORT=8000
    
    echo -e "${YELLOW}${GEAR} MODO:${NC} ${BOLD}DESARROLLO LOCAL${NC}"
    
    # Limpieza de puerto 8000 (Local)
    echo -e "${BLUE}${CLEAN} Liberando puerto ${PORT}...${NC}"
    fuser -k -9 ${PORT}/tcp 2>/dev/null
    sleep 1

    echo -e "${GREEN}${INFO} Iniciando FastAPI con auto-reload...${NC}"
    ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --reload
fi

echo -e "${BLUE}${BOLD}=========================================${NC}"
echo -e "${GREEN}${CHECK} ¡PROCESO FINALIZADO CON ÉXITO!${NC}"
echo -e "${INFO} Contenedor: ${BLUE}${CONTAINER_NAME}${NC}"
echo -e "${INFO} Puerto: ${BLUE}${PORT}${NC}"
echo -e "${BLUE}${BOLD}=========================================${NC}"