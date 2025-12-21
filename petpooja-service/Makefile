.PHONY: help build up down restart logs ps clean migrate backup restore test shell db-shell health

# Default target
help:
	@echo "A24 Restaurant Data Pipeline - Docker Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - View logs (all services)"
	@echo "  make logs-app      - View application logs"
	@echo "  make logs-db       - View database logs"
	@echo "  make ps            - Show running containers"
	@echo "  make clean         - Remove containers, networks, and volumes"
	@echo "  make migrate       - Run database migrations"
	@echo "  make backup        - Backup database"
	@echo "  make restore       - Restore database from backup"
	@echo "  make shell         - Access application shell"
	@echo "  make db-shell      - Access PostgreSQL shell"
	@echo "  make health        - Check service health"
	@echo "  make test          - Run tests"
	@echo ""
	@echo "Development commands:"
	@echo "  make dev           - Start in development mode"
	@echo "  make dev-down      - Stop development services"
	@echo ""
	@echo "Production commands:"
	@echo "  make prod          - Start in production mode"
	@echo "  make prod-down     - Stop production services"

# Build Docker images
build:
	docker-compose build

# Start services (default)
up:
	docker-compose up -d
	@echo "Services started. API available at: http://localhost:8001"
	@echo "API documentation: http://localhost:8001/docs"

# Start services in development mode
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "Development services started with hot-reload enabled"
	@echo "API available at: http://localhost:8001"

# Start services in production mode
prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production services started"
	@echo "API available at: http://localhost:8001"

# Stop services
down:
	docker-compose down

# Stop development services
dev-down:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Stop production services
prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

# View application logs only
logs-app:
	docker-compose logs -f app

# View database logs only
logs-db:
	docker-compose logs -f postgres

# Show container status
ps:
	docker-compose ps

# Clean up containers, networks, and volumes
clean:
	@echo "WARNING: This will remove all containers, networks, and volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker system prune -f; \
	fi

# Run database migrations
migrate:
	docker-compose exec app alembic upgrade head

# Access application shell
shell:
	docker-compose exec app bash

# Access PostgreSQL shell
db-shell:
	docker-compose exec postgres psql -U postgres -d a24_restaurant_dev

# Check service health
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8001/health || echo "API health check failed"
	@docker-compose exec postgres pg_isready || echo "Database health check failed"

# Backup database
backup:
	@mkdir -p backups
	docker-compose exec postgres pg_dump -U postgres a24_restaurant_dev > backups/backup-$(shell date +%Y%m%d-%H%M%S).sql
	@echo "Database backed up to backups/backup-$(shell date +%Y%m%d-%H%M%S).sql"

# Restore database (usage: make restore FILE=backups/backup-20240101-120000.sql)
restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify backup file. Usage: make restore FILE=backups/backup-20240101-120000.sql"; \
		exit 1; \
	fi
	cat $(FILE) | docker-compose exec -T postgres psql -U postgres -d a24_restaurant_dev
	@echo "Database restored from $(FILE)"

# Run tests
test:
	docker-compose exec app pytest -v

# Generate encryption key
generate-key:
	@docker-compose exec app python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Start with PgAdmin
pgadmin:
	docker-compose --profile tools up -d
	@echo "PgAdmin available at: http://localhost:5050"

# Rebuild and restart
rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "Services rebuilt and restarted"

# View resource usage
stats:
	docker stats
