# Restaurant AI Chatbot

AI-powered restaurant assistant using CrewAI + FastAPI.

## Quick Start (EC2/Docker)

```bash
# 1. Clone and enter directory
cd codebase

# 2. Configure environment
cp .env.production .env
nano .env  # Add your OPENAI_API_KEY

# 3. Deploy (one command)
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**Done!** Access at `http://your-ec2-ip/`

## Architecture

```
┌─────────────────────────────────────────┐
│           NGINX (Port 80)               │
│     Frontend + API Proxy + WebSocket    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│        FastAPI App (Port 8000)          │
│         CrewAI Agent + AGUI             │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌────────┐  ┌─────────┐  ┌──────────┐
│Postgres│  │  Redis  │  │ MongoDB  │
│  5432  │  │  6379   │  │  27017   │
└────────┘  └─────────┘  └──────────┘
```

## Folder Structure

```
codebase/
├── docker/              # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx/nginx.conf
├── db/                  # Database initialization
│   ├── init.sql
│   ├── 01-schema.sql
│   └── 02-data.sql
├── frontend/            # Chat UI
│   └── index.html
├── app/                 # FastAPI application
│   ├── api/            # Routes & middleware
│   ├── core/           # Config, DB, Redis, Events
│   ├── features/       # Food ordering, booking, etc.
│   └── services/       # Business logic
├── scripts/             # Deployment scripts
│   └── deploy.sh
├── .env.production      # Environment template
└── requirements.txt
```

## Commands

```bash
# Start
cd docker && docker compose up -d

# View logs
docker compose logs -f app

# Stop
docker compose down

# Rebuild
docker compose down -v && docker compose up -d --build
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `TEST_OTP_CODE` | No | Test OTP (default: 123456) |
| `AUTH_REQUIRED` | No | Enable auth (default: true) |

## API Endpoints

- `GET /` - Health check
- `GET /api/v1/health` - Detailed health
- `WS /ws/chat` - WebSocket chat
- `POST /api/v1/chat/stream` - SSE streaming

## Features

- Real-time chat with AGUI events
- Menu browsing and search
- Cart management
- Order placement (dine-in/takeaway)
- OTP authentication
- Rich UI cards (cart, menu, orders)
- Quick reply buttons
