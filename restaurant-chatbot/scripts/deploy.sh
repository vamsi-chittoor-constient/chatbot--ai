#!/bin/bash
# =============================================================================
# Restaurant AI - One-Command Deployment Script
# =============================================================================
# Usage:
#   chmod +x scripts/deploy.sh
#   ./scripts/deploy.sh
# =============================================================================

set -e

echo "=========================================="
echo "  Restaurant AI - Deployment Script"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env and add your OPENAI_API_KEY${NC}"
        echo "Then run this script again."
        exit 1
    else
        echo -e "${RED}Error: Neither .env nor .env.example found${NC}"
        exit 1
    fi
fi

# Check for OPENAI_API_KEY
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo -e "${RED}Error: OPENAI_API_KEY not set in .env${NC}"
    echo "Please add your OpenAI API key to .env"
    exit 1
fi

echo -e "${GREEN}Environment check passed${NC}"

# Navigate to docker directory
cd docker

echo ""
echo "Building and starting services..."
echo "================================="

# Build and start services
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

echo ""
echo "Waiting for services to be healthy..."
echo "======================================"

# Wait for services
sleep 10

# Check service status
echo ""
echo "Service Status:"
echo "==============="

if docker compose version &> /dev/null; then
    docker compose ps
else
    docker-compose ps
fi

# Get public IP
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo "localhost")

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Access your application:"
echo "  - Frontend:  http://${PUBLIC_IP}/"
echo "  - API:       http://${PUBLIC_IP}/api/v1/"
echo "  - API Docs:  http://${PUBLIC_IP}/docs"
echo "  - Health:    http://${PUBLIC_IP}/api/v1/health"
echo ""
echo "Useful commands:"
echo "  - View logs:     cd docker && docker compose logs -f app"
echo "  - Stop:          cd docker && docker compose down"
echo "  - Restart:       cd docker && docker compose restart"
echo "  - Full rebuild:  cd docker && docker compose down -v && docker compose up -d --build"
echo ""
