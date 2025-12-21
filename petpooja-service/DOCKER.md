# Docker Deployment Guide

This guide explains how to deploy the A24 Restaurant Data Pipeline as a containerized microservice using Docker.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Docker Services](#docker-services)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- At least 2GB of free RAM
- 5GB of free disk space

## Quick Start

### 1. Clone and Navigate to Project

```bash
cd a24-data-pipeline
```

### 2. Configure Environment

Copy the Docker environment template:

```bash
cp .env.docker .env
```

Edit `.env` and configure your settings:

```bash
# Required: Database credentials
POSTGRES_PASSWORD=your_secure_password

# Required: PetPooja API credentials
PETPOOJA_APP_KEY=your_app_key
PETPOOJA_APP_SECRET=your_app_secret
PETPOOJA_ACCESS_TOKEN=your_access_token

# Required: Encryption key for credentials
ENCRYPTION_KEY=your_fernet_encryption_key
```

**Generate Encryption Key:**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Build and Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Verify Deployment

```bash
# Check API health
curl http://localhost:8001/health

# View API documentation
# Open browser: http://localhost:8001/docs
```

## Configuration

### Environment Variables

All configuration is managed through the `.env` file. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | Database host | `postgres` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_DB` | Database name | `a24_restaurant_dev` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | **Required** |
| `API_PORT` | API server port | `8001` |
| `PETPOOJA_APP_KEY` | PetPooja app key | **Required** |
| `PETPOOJA_APP_SECRET` | PetPooja app secret | **Required** |
| `PETPOOJA_ACCESS_TOKEN` | PetPooja access token | **Required** |
| `ENCRYPTION_KEY` | Fernet encryption key | **Required** |

### Port Mapping

Default ports exposed by services:

- **API**: `8001` → Application API
- **PostgreSQL**: `5432` → Database
- **PgAdmin**: `5050` → Database management UI (optional)

## Docker Services

### 1. Application (`app`)

FastAPI microservice for PetPooja integration.

- **Image**: Built from `Dockerfile`
- **Port**: `8001`
- **Health Check**: `http://localhost:8001/health`
- **Auto-restart**: Yes

### 2. PostgreSQL (`postgres`)

Database for storing restaurant data, menus, and orders.

- **Image**: `postgres:15-alpine`
- **Port**: `5432`
- **Data Persistence**: `a24-postgres-data` volume
- **Auto-restart**: Yes

### 3. PgAdmin (`pgadmin`) - Optional

Web-based database management tool.

- **Image**: `dpage/pgadmin4:latest`
- **Port**: `5050`
- **Access**: `http://localhost:5050`

**Enable PgAdmin:**

```bash
docker-compose --profile tools up -d
```

## Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Stop and remove all containers, networks, volumes
docker-compose down -v
```

### Logs and Monitoring

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs -f app
docker-compose logs -f postgres

# View last 100 lines
docker-compose logs --tail=100
```

### Database Operations

```bash
# Run database migrations
docker-compose exec app alembic upgrade head

# Access PostgreSQL CLI
docker-compose exec postgres psql -U postgres -d a24_restaurant_dev

# Create database backup
docker-compose exec postgres pg_dump -U postgres a24_restaurant_dev > backup.sql

# Restore database backup
cat backup.sql | docker-compose exec -T postgres psql -U postgres -d a24_restaurant_dev
```

### Application Management

```bash
# Access application shell
docker-compose exec app bash

# Run Python commands
docker-compose exec app python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# View running processes
docker-compose exec app ps aux

# Check disk usage
docker-compose exec app df -h
```

### Rebuild and Update

```bash
# Rebuild application image
docker-compose build app

# Rebuild with no cache
docker-compose build --no-cache app

# Pull latest base images and rebuild
docker-compose pull
docker-compose up -d --build
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs app

# Check container health
docker inspect a24-api | grep -A 10 Health
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
docker-compose exec postgres pg_isready

# Check database connectivity
docker-compose exec app psql -h postgres -U postgres -d a24_restaurant_dev -c "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up -d
```

### Port Already in Use

```bash
# Change port in .env file
API_PORT=8002

# Restart services
docker-compose down
docker-compose up -d
```

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove application image
docker rmi a24-data-pipeline-app

# Start fresh
docker-compose up -d --build
```

## Production Deployment

### Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong `ENCRYPTION_KEY`
- [ ] Set `DEBUG=false`
- [ ] Configure proper `ALLOWED_ORIGINS`
- [ ] Use environment-specific `.env` file
- [ ] Enable SSL/TLS for database connections
- [ ] Set up proper logging and monitoring
- [ ] Configure backup strategy
- [ ] Use secrets management (e.g., Docker Secrets, Vault)

### Production Configuration

```bash
# .env.production
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourdomain.com
POSTGRES_PASSWORD=strong_random_password
ENCRYPTION_KEY=production_encryption_key
```

### Using with Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Scaling with Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml a24

# Scale application
docker service scale a24_app=3

# View services
docker service ls
```

### Health Monitoring

```bash
# Check API health
curl http://localhost:8001/health

# Monitor container health
docker-compose ps
docker inspect a24-api | grep -A 10 Health

# View resource usage
docker stats
```

## Advanced Configuration

### Custom Network

Create a custom Docker network for integration with other services:

```bash
docker network create a24-network
```

Update `docker-compose.yml` to use external network:

```yaml
networks:
  a24-network:
    external: true
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect a24-postgres-data

# Backup volume
docker run --rm -v a24-postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v a24-postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres-backup.tar.gz -C /data
```

### Environment-Specific Compose Files

```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: See `README.md` and `RESTAURANT_ONBOARDING.md`
