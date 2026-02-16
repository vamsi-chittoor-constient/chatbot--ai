#!/bin/bash
# =============================================================================
# A24 Restaurant Platform - Automated Deploy Script
# =============================================================================
# Usage: ./deploy.sh [branch]
# Example: ./deploy.sh release/voice-multilingual-v1.0
#          ./deploy.sh                    (uses current branch)
# =============================================================================
set -e

COMPOSE_FILE="docker-compose.root.yml"
NGROK_API="http://localhost:4040/api/tunnels"
TIMEOUT=60  # seconds to wait for ngrok

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}  A24 Restaurant Platform - Deploy${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

# -----------------------------------------------------------------------------
# Step 0: Pull branch if specified
# -----------------------------------------------------------------------------
BRANCH="${1:-}"
if [ -n "$BRANCH" ]; then
    echo -e "${YELLOW}[0/5] Pulling branch: ${BRANCH}${NC}"
    git pull origin "$BRANCH"
    git checkout "$BRANCH"
    echo ""
fi

# -----------------------------------------------------------------------------
# Step 1: Force-kill ngrok and app containers (preserve databases)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[1/5] Stopping all application containers...${NC}"

# Force remove ngrok first — must fully die before re-creating
# so ngrok cloud releases the endpoint
docker compose -f "$COMPOSE_FILE" down --remove-orphans --timeout 5 2>/dev/null || true

# Also kill any ngrok running outside Docker (native install)
pkill -f ngrok 2>/dev/null || true

echo "    Waiting for ngrok cloud to release endpoint..."
sleep 5
echo ""

# -----------------------------------------------------------------------------
# Step 2: Start ngrok tunnel FIRST (no dependencies)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[2/5] Starting ngrok tunnel...${NC}"
docker compose -f "$COMPOSE_FILE" up -d ngrok
echo "    Waiting for ngrok to establish tunnel..."

NGROK_URL=""
ELAPSED=0
while [ -z "$NGROK_URL" ] && [ $ELAPSED -lt $TIMEOUT ]; do
    sleep 3
    ELAPSED=$((ELAPSED + 3))

    # Check if ngrok container is still running (might have crashed)
    if ! docker compose -f "$COMPOSE_FILE" ps ngrok --format "{{.State}}" 2>/dev/null | grep -q "running"; then
        echo -e "    ${RED}ngrok container crashed. Checking logs...${NC}"
        docker compose -f "$COMPOSE_FILE" logs ngrok --tail=5
        echo ""
        echo -e "    ${YELLOW}Retrying ngrok...${NC}"
        docker compose -f "$COMPOSE_FILE" up -d ngrok
        sleep 3
        ELAPSED=$((ELAPSED + 3))
    fi

    NGROK_URL=$(curl -s "$NGROK_API" 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    for t in tunnels:
        if t.get('public_url', '').startswith('https://'):
            print(t['public_url'])
            break
except:
    pass
" 2>/dev/null) || true
    if [ -n "$NGROK_URL" ]; then
        break
    fi
    echo "    ...waiting (${ELAPSED}s / ${TIMEOUT}s)"
done

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}ERROR: Failed to get ngrok URL after ${TIMEOUT}s${NC}"
    echo ""
    echo "Common fixes:"
    echo "  1. Another ngrok agent is using your authtoken somewhere else"
    echo "     → Kill it or visit: https://dashboard.ngrok.com/tunnels/agents"
    echo "  2. Check logs: docker compose -f $COMPOSE_FILE logs ngrok --tail=20"
    echo ""
    exit 1
fi

echo -e "    ${GREEN}Tunnel established: ${NGROK_URL}${NC}"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Write NGROK_URL to .env for docker-compose variable substitution
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[3/5] Injecting ngrok URL into environment...${NC}"

# Remove old NGROK_URL line if exists, then append new one
if [ -f .env ]; then
    grep -v '^NGROK_URL=' .env > .env.tmp 2>/dev/null || true
    mv .env.tmp .env
fi
echo "NGROK_URL=${NGROK_URL}" >> .env

echo "    Written to .env: NGROK_URL=${NGROK_URL}"
echo ""

# -----------------------------------------------------------------------------
# Step 4: Build and start all services
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[4/5] Building and starting all services...${NC}"

# Ensure databases are running first
docker compose -f "$COMPOSE_FILE" up -d postgres redis mongodb
echo "    Waiting for databases to be healthy..."
sleep 10

# Build and start application services
docker compose -f "$COMPOSE_FILE" up -d --build chatbot-app petpooja-app whatsapp-bridge

echo "    Waiting for app services to be healthy..."
sleep 15

# Start nginx (depends on app services)
docker compose -f "$COMPOSE_FILE" up -d --build nginx
echo ""

# -----------------------------------------------------------------------------
# Step 5: Health check and summary
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[5/5] Verifying deployment...${NC}"
sleep 5

echo ""
echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}  Service Status${NC}"
echo -e "${CYAN}==========================================${NC}"
docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "  ${CYAN}Ngrok URL:${NC}  ${NGROK_URL}"
echo -e "  ${CYAN}Frontend:${NC}   ${NGROK_URL}"
echo -e "  ${CYAN}API:${NC}        ${NGROK_URL}/api/v1"
echo -e "  ${CYAN}WebSocket:${NC}  wss://${NGROK_URL#https://}/api/v1/chat"
echo -e "  ${CYAN}WhatsApp:${NC}   ${NGROK_URL}/whatsapp/webhook"
echo -e "  ${CYAN}PetPooja:${NC}   ${NGROK_URL}/api/petpooja"
echo -e "  ${CYAN}Ngrok UI:${NC}   http://localhost:4040"
echo ""
echo -e "  ${YELLOW}Razorpay callbacks → ${NGROK_URL}/api/v1/webhook/razorpay${NC}"
echo -e "  ${YELLOW}PetPooja callback  → ${NGROK_URL}/api/petpooja/webhooks/petpooja/order-status${NC}"
echo ""
echo -e "${GREEN}==========================================${NC}"
