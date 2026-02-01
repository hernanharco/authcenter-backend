#!/bin/bash

# Colores para mensajes bonitos
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Iniciando automatización de AuthCore Backend...${NC}"

# 1. Actualizar dependencias localmente
echo -e "${BLUE}📦 Actualizando requirements.txt...${NC}"
pip freeze > requirements.txt

# 2. Construir la imagen de Docker
echo -e "${BLUE}🏗️ Construyendo imagen de Docker...${NC}"
docker build -t authcore-backend .

# 3. Detener contenedores viejos si existen
echo -e "${BLUE}🛑 Deteniendo contenedores antiguos...${NC}"
docker stop authcore-container 2>/dev/null || true
docker rm authcore-container 2>/dev/null || true

# 4. Correr el nuevo contenedor
echo -e "${GREEN}🏃 Corriendo nuevo contenedor en puerto 8000...${NC}"
docker run -d \
  --name authcore-container \
  -p 8000:8000 \
  --env-file .env \
  authcore-backend

echo -e "${GREEN}✅ ¡Todo listo! Tu API está volando en http://localhost:8000${NC}"