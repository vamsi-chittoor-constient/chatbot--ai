# A24 Restaurant Platform

Microservices-based restaurant management platform with AI chatbot and PetPooja POS integration.

## Architecture

```
┌─────────────────────────────────────────┐
│         NGINX (Port 80)                 │
│    Single Entry Point / Load Balancer   │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐   ┌──────────────────┐
│  Chatbot    │   │ PetPooja Service │
│ (Port 8000) │   │   (Port 8001)    │
└──────┬──────┘   └────────┬─────────┘
       │                   │
       └─────────┬─────────┘
                 ▼
    ┌────────────────────────┐
    │  PostgreSQL (Shared)   │
    │  Redis (Shared)        │
    │  MongoDB (Shared)      │
    └────────────────────────┘
```

## Project Structure

```
Order-v1-codebase-2/
├── restaurant-chatbot/        # AI Chatbot Service
│   ├── app/                   # FastAPI application
│   ├── db/                    # Database schemas
│   ├── docker/                # Docker configs
│   ├── .env                   # Chatbot environment
│   └── docker-compose.yml     # Standalone compose
│
├── petpooja-service/          # PetPooja Integration
│   ├── app/                   # FastAPI application
│   ├── documents/             # API documentation
│   ├── .env                   # PetPooja environment
│   └── docker-compose.yml     # Standalone compose
│
├── docker-compose.root.yml    # 🔥 Root orchestrator
├── nginx.conf                 # Reverse proxy config
└── README.md                  # This file
```

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- OpenAI API key
- PetPooja credentials (optional for testing)

### 1. Reorganize Folder Structure (First Time Only)

If you still have the old nested structure, run:

```bash
# Navigate to project root
cd Order-v1-codebase-2

# Fix nested structure
mv a24-data-pipeline/a24-data-pipeline petpooja-service
rmdir a24-data-pipeline

# Rename main app (optional but recommended)
mv codebase restaurant-chatbot
```

### 2. Configure Environment Variables

```bash
# Copy environment templates
cp restaurant-chatbot/.env.example restaurant-chatbot/.env
cp petpooja-service/.env.example petpooja-service/.env

# Edit with your credentials
nano restaurant-chatbot/.env  # Add OPENAI_API_KEY
nano petpooja-service/.env    # Add PetPooja credentials
```

**Required Variables:**

**restaurant-chatbot/.env:**
```bash
OPENAI_API_KEY=sk-...
MAIN_BACKEND_API_TOKEN=your-secure-token-here
```

**petpooja-service/.env:**
```bash
# PetPooja Sandbox
PETPOOJA_SANDBOX_ENABLED=true
PETPOOJA_SANDBOX_BASE_URL=https://...amazonaws.com/V1
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret

# Security
MAIN_BACKEND_API_TOKEN=your-secure-token-here  # MUST match chatbot token
WEBHOOK_SECRET=your-webhook-secret
ENCRYPTION_KEY=your-fernet-key
```

### 3. Start All Services

```bash
# Start entire platform
docker compose -f docker-compose.root.yml up -d

# Check status
docker compose -f docker-compose.root.yml ps

# View logs
docker compose -f docker-compose.root.yml logs -f
```

### 4. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **Main App** | http://localhost | Frontend & Chatbot |
| **Chatbot API** | http://localhost/api/v1/ | Main API |
| **PetPooja API** | http://localhost/api/petpooja/ | Integration API |
| **Chatbot Docs** | http://localhost/api/v1/docs | Swagger UI |
| **PetPooja Docs** | http://localhost/api/petpooja/docs | Swagger UI |
| **Health Check** | http://localhost/health | Aggregate health |

## Service Communication

### From Chatbot to PetPooja Service

```python
import httpx

# Inside chatbot app
async def push_order_to_pos(order_id: str, restaurant_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://petpooja-app:8001/api/orders/push-to-pos",
            json={
                "order_id": order_id,
                "restaurant_id": restaurant_id
            },
            headers={
                "Authorization": f"Bearer {settings.PETPOOJA_SERVICE_TOKEN}"
            }
        )
        return response.json()
```

### From Frontend (via NGINX)

```javascript
// Place order to PetPooja
fetch('/api/petpooja/orders/push-to-pos', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-token',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    order_id: '123e4567-e89b-12d3-a456-426614174000',
    restaurant_id: '123e4567-e89b-12d3-a456-426614174001'
  })
})
```

## Development

### Run Services Independently

**Chatbot only:**
```bash
cd restaurant-chatbot
docker compose up -d
# Access at http://localhost:80
```

**PetPooja service only:**
```bash
cd petpooja-service
docker compose up -d
# Access at http://localhost:8001
```

### Run Without Docker

**Chatbot:**
```bash
cd restaurant-chatbot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**PetPooja:**
```bash
cd petpooja-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Common Commands

```bash
# Start all services
docker compose -f docker-compose.root.yml up -d

# Stop all services
docker compose -f docker-compose.root.yml down

# Rebuild and restart
docker compose -f docker-compose.root.yml up -d --build

# View logs (all services)
docker compose -f docker-compose.root.yml logs -f

# View logs (specific service)
docker compose -f docker-compose.root.yml logs -f chatbot-app
docker compose -f docker-compose.root.yml logs -f petpooja-app

# Scale PetPooja service
docker compose -f docker-compose.root.yml up -d --scale petpooja-app=3

# Restart specific service
docker compose -f docker-compose.root.yml restart petpooja-app

# Access database
docker exec -it a24-postgres psql -U admin -d restaurant_ai

# Access Redis
docker exec -it a24-redis redis-cli

# Clean everything (WARNING: Deletes data)
docker compose -f docker-compose.root.yml down -v
```

## Monitoring & Debugging

### Check Service Health

```bash
# Overall health
curl http://localhost/health

# Chatbot health
curl http://localhost/api/v1/health

# PetPooja health
curl http://localhost/api/petpooja/health
```

### Database Access

```bash
# PostgreSQL
docker exec -it a24-postgres psql -U admin -d restaurant_ai

# View tables
\dt

# Check PetPooja integration config
SELECT * FROM integration_config_table;
```

### View Logs

```bash
# Application logs
docker compose -f docker-compose.root.yml logs -f chatbot-app
docker compose -f docker-compose.root.yml logs -f petpooja-app

# NGINX logs
docker compose -f docker-compose.root.yml logs -f nginx

# Database logs
docker compose -f docker-compose.root.yml logs -f postgres
```

## Production Deployment

### 1. Update Environment Variables

```bash
# Set production mode
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=WARNING

# Use production PetPooja API
PETPOOJA_SANDBOX_ENABLED=false
PETPOOJA_BASE_URL=https://api-v2.petpooja.com
```

### 2. Configure SSL

Add SSL certificates to NGINX config:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of config
}
```

### 3. Security Checklist

- [ ] Change default database passwords
- [ ] Use strong `MAIN_BACKEND_API_TOKEN`
- [ ] Generate secure `WEBHOOK_SECRET`
- [ ] Generate `ENCRYPTION_KEY` (Fernet key)
- [ ] Configure firewall (only expose port 80/443)
- [ ] Enable log rotation
- [ ] Set up database backups
- [ ] Configure CORS properly (no wildcards)

## Troubleshooting

### Service won't start

```bash
# Check if ports are in use
netstat -an | grep 8000
netstat -an | grep 8001

# View detailed error logs
docker compose -f docker-compose.root.yml logs petpooja-app
```

### Database connection errors

```bash
# Check if PostgreSQL is running
docker compose -f docker-compose.root.yml ps postgres

# Test connection
docker exec -it a24-postgres pg_isready -U admin
```

### PetPooja API errors

```bash
# Check credentials
docker compose -f docker-compose.root.yml exec petpooja-app env | grep PETPOOJA

# Test API directly
curl -X POST http://localhost/api/petpooja/orders/push-to-pos \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"order_id":"test","restaurant_id":"test"}'
```

## Documentation

- **Chatbot Documentation:** [restaurant-chatbot/README.md](restaurant-chatbot/README.md)
- **PetPooja Documentation:** [petpooja-service/README.md](petpooja-service/README.md)
- **PetPooja API Reference:** [petpooja-service/documents/API_REFERENCE.md](petpooja-service/documents/API_REFERENCE.md)
- **System Flow:** [petpooja-service/documents/SYSTEM_FLOW.md](petpooja-service/documents/SYSTEM_FLOW.md)

## Support

- **Chatbot Issues:** See restaurant-chatbot/README.md
- **PetPooja Integration:** See petpooja-service/README.md
- **PetPooja Support:** support@petpooja.com

## Version

- **Platform Version:** 1.0.0
- **Chatbot Service:** 1.0.0
- **PetPooja Service:** 1.0.0

---

**Built with:** FastAPI • PostgreSQL • Redis • MongoDB • Docker • NGINX
