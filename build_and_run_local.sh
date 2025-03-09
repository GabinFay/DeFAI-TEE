#!/bin/bash

# Build and Run Local Script for Flare Berkeley
# This script builds the Docker container and runs it locally for testing

set -e  # Exit on any error

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="flare-berkeley"
CONTAINER_NAME="flare-berkeley-local"
STREAMLIT_PORT=8501  # Default Streamlit port inside container
HTTP_PORT=80         # HTTP port
HTTPS_PORT=443       # HTTPS port

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found. Please create one based on .env.template${NC}"
    exit 1
fi

echo -e "${GREEN}=== Building Docker Image ===${NC}"
docker build -t ${IMAGE_NAME} .

echo -e "${GREEN}=== Stopping any existing container ===${NC}"
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

echo -e "${GREEN}=== Running Container Locally ===${NC}"
echo -e "${YELLOW}The application will be available at:${NC}"
echo -e "${YELLOW}- HTTP: http://localhost:${HTTP_PORT}${NC}"
echo -e "${YELLOW}- HTTPS: https://localhost:${HTTPS_PORT} (self-signed certificate warning expected)${NC}"

# Run the container with environment variables from .env file
# Map both HTTP and HTTPS ports
docker run --name ${CONTAINER_NAME} \
    -p ${HTTP_PORT}:80 \
    -p ${HTTPS_PORT}:443 \
    -p ${STREAMLIT_PORT}:8501 \
    --env-file .env \
    --env SIMULATE_ATTESTATION=true \
    -v $(pwd):/app \
    -d \
    ${IMAGE_NAME}

echo -e "${GREEN}=== Container is running! ===${NC}"
echo -e "To view logs: ${YELLOW}docker logs -f ${CONTAINER_NAME}${NC}"
echo -e "To stop: ${YELLOW}docker stop ${CONTAINER_NAME}${NC}"
echo -e ""
echo -e "${GREEN}=== Access URLs ===${NC}"
echo -e "1. ${YELLOW}http://localhost:${HTTP_PORT}${NC} - Should redirect to HTTPS"
echo -e "2. ${YELLOW}https://localhost:${HTTPS_PORT}${NC} - Main application (with certificate warning)"
echo -e "3. ${YELLOW}http://localhost:${STREAMLIT_PORT}${NC} - Direct Streamlit access (if nginx proxy fails)"

# Follow logs
echo -e "${GREEN}=== Showing container logs (Ctrl+C to exit logs) ===${NC}"
docker logs -f ${CONTAINER_NAME} 