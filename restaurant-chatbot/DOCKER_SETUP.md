# 🐳 Docker Setup Guide

Complete guide for running the Restaurant AI Chatbot with Docker.

---

## 📦 What's Included

The Docker setup includes:

- **Frontend**: React + Vite + Lottie animations
- **Backend**: FastAPI + CrewAI + Voice Mode
- **PostgreSQL**: Main database (Port 5433)
- **Redis**: Caching + session storage (Port 6379)
- **MongoDB**: Analytics (Port 27017)
- **Nginx**: Reverse proxy + static file serving (Port 80)

---

## 🚀 Quick Start - Production

### Prerequisites

- Docker Desktop installed
- `.env` file configured with API keys

### 1. Start All Services

```bash
cd restaurant-chatbot
docker compose up -d --build
```

This command:
- ✅ Builds backend Docker image
- ✅ Builds frontend with Vite (includes new Lottie animations!)
- ✅ Starts PostgreSQL, Redis, MongoDB
- ✅ Starts Nginx reverse proxy
- ✅ All services run in background

### 2. Access the Application

**Frontend**: http://localhost

**Backend API**: http://localhost/api/v1

**API Docs**: http://localhost/docs

### 3. View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f nginx
docker compose logs -f app
docker compose logs -f postgres
```

### 4. Stop Services

```bash
docker compose down
```

### 5. Stop + Remove Data

```bash
docker compose down -v  # Removes volumes (database data)
```

---

## 🛠️ Development Mode (Hot Reload)

For local development with automatic code reloading:

### 1. Start Development Environment

```bash
docker compose -f docker-compose.dev.yml up
```

This starts:
- **Frontend** on http://localhost:3000 (Vite dev server with HMR)
- **Backend** on http://localhost:8000 (uvicorn with --reload)
- **Databases** on their respective ports

### 2. Code Changes Auto-Reload

- ✅ **Frontend**: Edit files in `frontend/src/` → browser auto-refreshes
- ✅ **Backend**: Edit files in `app/` → server auto-restarts

### 3. Access Services

**Frontend Dev Server**: http://localhost:3000

**Backend API**: http://localhost:8000

**API Docs**: http://localhost:8000/docs

---

## 🏗️ Architecture

### Production Setup (docker-compose.yml)

```
┌─────────────────────────────────────┐
│  Browser (Port 80)                  │
└────────────┬────────────────────────┘
             │
        ┌────▼────┐
        │  Nginx  │  Port 80
        │  ├─ Serves built React frontend
        │  └─ Proxies /api → Backend
        └────┬────┘
             │
        ┌────▼────┐
        │ Backend │  Port 8000
        │ FastAPI │
        └────┬────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼───┐      ┌─────▼──┐      ┌─────▼──┐
│Postgres│      │ Redis  │      │MongoDB │
│  5433  │      │  6379  │      │ 27017  │
└────────┘      └────────┘      └────────┘
```

### Development Setup (docker-compose.dev.yml)

```
┌─────────────────────┐     ┌──────────────────┐
│  Browser :3000      │     │  Browser :8000   │
│  Frontend (Vite HMR)│     │  Backend API     │
└──────────┬──────────┘     └────────┬─────────┘
           │                         │
      ┌────▼────┐              ┌─────▼─────┐
      │Frontend │              │  Backend  │
      │Container│              │ Container │
      │+ Volume │              │ + Volume  │
      │  Mount  │              │   Mount   │
      └─────────┘              └─────┬─────┘
                                     │
                          ┌──────────┴──────────┐
                          │                     │
                     ┌────▼───┐      ┌────▼────┐      ┌─────▼──┐
                     │Postgres│      │  Redis  │      │MongoDB │
                     └────────┘      └─────────┘      └────────┘
```

---

## 📝 Common Commands

### Build Services

```bash
# Build all services
docker compose build

# Build specific service
docker compose build nginx
docker compose build app

# Build without cache (force rebuild)
docker compose build --no-cache
```

### Start/Stop Services

```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d postgres

# Stop all services
docker compose down

# Restart specific service
docker compose restart app
```

### View Status

```bash
# List running containers
docker compose ps

# Check service health
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

### Shell Access

```bash
# Backend shell
docker compose exec app bash

# PostgreSQL shell
docker compose exec postgres psql -U admin -d restaurant_ai

# Redis CLI
docker compose exec redis redis-cli

# MongoDB shell
docker compose exec mongodb mongosh
```

### Database Operations

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U admin restaurant_ai > backup.sql

# Restore PostgreSQL
docker compose exec -T postgres psql -U admin restaurant_ai < backup.sql

# View PostgreSQL logs
docker compose logs -f postgres
```

---

## 🔧 Environment Variables

### Backend (.env)

Required variables (see `.env.example`):

```bash
# OpenAI API Key (Required for AI features)
OPENAI_API_KEY=sk-...

# Database (Auto-configured in Docker)
DATABASE_URL=postgresql+asyncpg://admin:admin123@postgres:5432/restaurant_ai

# Redis (Auto-configured in Docker)
REDIS_URL=redis://redis:6379/0

# MongoDB (Auto-configured in Docker)
MONGODB_CONNECTION_STRING=mongodb://mongodb:27017
```

### Frontend

No environment variables needed! Backend URL is auto-configured via Nginx proxy.

---

## 🐛 Troubleshooting

### "Port already in use"

```bash
# Check what's using the port
netstat -ano | findstr :80
netstat -ano | findstr :8000

# Stop the process or change ports in docker-compose.yml
```

### "Cannot connect to database"

```bash
# Check if PostgreSQL is healthy
docker compose ps postgres

# View logs
docker compose logs postgres

# Restart database
docker compose restart postgres
```

### "Frontend shows 404"

```bash
# Rebuild nginx with frontend
docker compose build nginx
docker compose up -d nginx

# Check nginx logs
docker compose logs nginx
```

### "Backend API not responding"

```bash
# Check backend health
docker compose ps app

# View logs
docker compose logs app

# Restart backend
docker compose restart app
```

### Clear Everything and Start Fresh

```bash
# Stop and remove all containers, networks, volumes
docker compose down -v

# Remove all images
docker system prune -a

# Rebuild everything
docker compose up -d --build
```

---

## 📊 Resource Usage

### Default Limits

- **Backend**: 4 workers, 100 concurrent connections
- **Redis**: 512MB max memory
- **PostgreSQL**: No limit (uses available RAM)
- **MongoDB**: No limit (uses available RAM)

### Monitoring

```bash
# View resource usage
docker stats

# Specific container
docker stats restaurant-app
```

---

## 🔒 Security Notes

### Production Checklist

- ✅ Change default PostgreSQL password in docker-compose.yml
- ✅ Set `ENVIRONMENT=production` in backend
- ✅ Remove `/docs` endpoint in nginx.conf for production
- ✅ Configure `ALLOWED_ORIGINS` to specific domains
- ✅ Use secrets management for API keys
- ✅ Enable HTTPS with SSL certificates

---

## 📚 Additional Resources

- **FastAPI Docs**: http://localhost/docs (when running)
- **Docker Compose Docs**: https://docs.docker.com/compose/
- **Project README**: [README.md](README.md)

---

## 🎉 Features Included

With this Docker setup, you get:

- ✅ **Voice Mode** with Whisper transcription
- ✅ **Hinglish/Tanglish** support (Approaches A & B)
- ✅ **Lottie Animations** (aibot, burger, voicecommunication)
- ✅ **AG-UI Events** (quick replies, payment cards)
- ✅ **CrewAI Agent Orchestration**
- ✅ **Multi-database support** (PostgreSQL, Redis, MongoDB)
- ✅ **WebSocket support** for real-time chat
- ✅ **Production-ready** with Nginx reverse proxy

---

**Need help?** Check logs with `docker compose logs -f` or open an issue!
