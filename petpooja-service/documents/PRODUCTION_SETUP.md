# Production Environment Setup Guide

## Overview

This guide explains how to configure and deploy the A24 Restaurant Data Pipeline for PetPooja's **PRODUCTION** environment.

## Prerequisites

- Python 3.12+
- PostgreSQL 14+ (Production instance)
- PetPooja Production Account Credentials
- Production server with public IP or domain
- SSL Certificate (for HTTPS)
- Process manager (systemd, supervisor, or PM2)

## Key Differences from Sandbox

| Configuration | Sandbox | Production |
|--------------|---------|------------|
| **Base URL** | AWS API Gateway | `https://api-v2.petpooja.com` |
| **Authentication** | AWS SigV4 (requires AWS credentials) | Standard (app_key, app_secret in body) |
| **Sandbox Enabled** | `true` | `false` |
| **Debug Mode** | `true` | `false` |
| **Log Level** | `DEBUG` | `INFO` or `WARNING` |
| **API Reload** | `true` | `false` |
| **Workers** | 1-4 | 4-8 (based on CPU cores) |
| **Callback URL** | ngrok URL | Production domain with HTTPS |
| **Database** | Local PostgreSQL | Production PostgreSQL (RDS, managed) |
| **CORS Origins** | `*` | Specific domains only |
| **Rate Limiting** | 100 requests/min | 60 requests/min |

## Step 1: Production Database Setup

### Option A: Managed PostgreSQL (Recommended)

Use AWS RDS, Google Cloud SQL, or Azure Database for PostgreSQL.

**Advantages:**
- Automated backups
- High availability
- Automatic scaling
- Monitoring and alerts

### Option B: Self-Hosted PostgreSQL

If using self-hosted PostgreSQL:

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Configure PostgreSQL for production
sudo vim /etc/postgresql/14/main/postgresql.conf

# Set these parameters:
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB

# Enable remote connections (if needed)
listen_addresses = '*'

# Configure pg_hba.conf for secure access
sudo vim /etc/postgresql/14/main/pg_hba.conf

# Add entry for your application server
host    a24_production    a24_user    <app-server-ip>/32    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Create Production Database

```sql
-- Create production database
CREATE DATABASE a24_production;

-- Create dedicated user with strong password
CREATE USER a24_user WITH PASSWORD 'STRONG_PASSWORD_HERE';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE a24_production TO a24_user;

-- Connect to database
\c a24_production

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

## Step 2: Production Environment Configuration

Create `.env` file with production settings:

```bash
# =============================================================================
# Database Configuration (PRODUCTION)
# =============================================================================
POSTGRES_HOST=your-production-db-host.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DB=a24_production
POSTGRES_USER=a24_user
POSTGRES_PASSWORD=your_strong_password_here

# Connection pool settings for production
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30

# =============================================================================
# PetPooja PRODUCTION Configuration
# =============================================================================
# ⚠️ IMPORTANT: Disable sandbox mode for production
PETPOOJA_SANDBOX_ENABLED=false

# Production API URL (NO AWS API Gateway)
PETPOOJA_BASE_URL=https://api-v2.petpooja.com

# Production PetPooja Credentials
# ⚠️ Get these from PetPooja production account
PETPOOJA_APP_KEY=your_production_app_key
PETPOOJA_APP_SECRET=your_production_app_secret
PETPOOJA_ACCESS_TOKEN=your_production_access_token

# Production Restaurant ID (from PetPooja)
PETPOOJA_RESTAURANT_ID=your_restaurant_id
PETPOOJA_MAPPING_CODE=your_mapping_code

# =============================================================================
# AWS Credentials - NOT REQUIRED FOR PRODUCTION
# =============================================================================
# ⚠️ Production API does NOT use AWS SigV4 authentication
# You can leave these empty or remove them
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_REGION=ap-southeast-1

# =============================================================================
# PetPooja API Endpoints (Same as Sandbox)
# =============================================================================
PETPOOJA_SAVE_ORDER_ENDPOINT=/save_order
PETPOOJA_FETCH_MENU_ENDPOINT=/getrestaurantdetails
PETPOOJA_FETCH_RESTAURANT_ENDPOINT=/getrestaurantdetails

# =============================================================================
# Webhook Configuration (PRODUCTION)
# =============================================================================
# ⚠️ MUST be public HTTPS URL
PETPOOJA_CALLBACK_URL=https://api.yourdomain.com/api/webhooks/petpooja/order-status

# Strong webhook security secret
WEBHOOK_SECRET=generate_strong_random_secret_here

# =============================================================================
# Main Backend Integration
# =============================================================================
MAIN_BACKEND_URL=https://backend.yourdomain.com
MAIN_BACKEND_API_TOKEN=your_secure_backend_token

# =============================================================================
# API Server Configuration (PRODUCTION)
# =============================================================================
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=8  # Typically 2-4 × CPU cores
API_RELOAD=false  # ⚠️ Disable auto-reload in production
API_LOG_LEVEL=info  # info or warning for production
DEBUG=false  # ⚠️ Disable debug mode

# =============================================================================
# Application Settings
# =============================================================================
APP_NAME=A24 Restaurant Data Pipeline
APP_VERSION=1.0.0

# =============================================================================
# Logging Configuration (PRODUCTION)
# =============================================================================
LOG_LEVEL=INFO  # ⚠️ Use INFO or WARNING, not DEBUG
LOG_FILE=/var/log/a24-pipeline/petpooja.log

# =============================================================================
# HTTP Client Configuration
# =============================================================================
HTTP_TIMEOUT=30
HTTP_MAX_RETRIES=3
HTTP_RETRY_DELAY=2

# =============================================================================
# Security Settings (PRODUCTION)
# =============================================================================
# ⚠️ Specify allowed origins (NO wildcards)
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Rate limiting (stricter for production)
RATE_LIMIT_PER_MINUTE=60

# Encryption key for sensitive data
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your_fernet_encryption_key_here
```

## Step 3: Server Setup

### 1. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and required packages
sudo apt install python3.12 python3.12-venv python3-pip -y

# Install PostgreSQL client
sudo apt install postgresql-client -y

# Install nginx (for reverse proxy)
sudo apt install nginx -y

# Install supervisor (for process management)
sudo apt install supervisor -y
```

### 2. Create Application Directory

```bash
# Create application directory
sudo mkdir -p /opt/a24-pipeline
sudo chown $USER:$USER /opt/a24-pipeline

# Clone or copy your application
cd /opt/a24-pipeline
git clone <your-repo-url> .

# Or copy files
scp -r /local/path/* user@server:/opt/a24-pipeline/
```

### 3. Setup Virtual Environment

```bash
cd /opt/a24-pipeline

# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Deactivate
deactivate
```

### 4. Create Log Directory

```bash
sudo mkdir -p /var/log/a24-pipeline
sudo chown $USER:$USER /var/log/a24-pipeline
```

## Step 4: Database Migration

```bash
cd /opt/a24-pipeline
source venv/bin/activate

# Run migrations
alembic upgrade head

# Verify tables created
psql -h your-db-host -U a24_user -d a24_production -c "\dt"

deactivate
```

## Step 5: Configure Process Manager

### Option A: Systemd (Recommended)

Create systemd service file:

```bash
sudo nano /etc/systemd/system/a24-pipeline.service
```

Add the following content:

```ini
[Unit]
Description=A24 Restaurant Data Pipeline
After=network.target postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/a24-pipeline
Environment="PATH=/opt/a24-pipeline/venv/bin"
ExecStart=/opt/a24-pipeline/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 8
Restart=always
RestartSec=10
StandardOutput=append:/var/log/a24-pipeline/stdout.log
StandardError=append:/var/log/a24-pipeline/stderr.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/a24-pipeline /opt/a24-pipeline/logs

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable a24-pipeline

# Start service
sudo systemctl start a24-pipeline

# Check status
sudo systemctl status a24-pipeline

# View logs
sudo journalctl -u a24-pipeline -f
```

### Option B: Supervisor

Create supervisor configuration:

```bash
sudo nano /etc/supervisor/conf.d/a24-pipeline.conf
```

Add:

```ini
[program:a24-pipeline]
directory=/opt/a24-pipeline
command=/opt/a24-pipeline/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 8
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/a24-pipeline/app.log
environment=PATH="/opt/a24-pipeline/venv/bin"
```

Enable and start:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start a24-pipeline
sudo supervisorctl status
```

## Step 6: Configure Nginx Reverse Proxy

Create nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/a24-pipeline
```

Add:

```nginx
upstream a24_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logs
    access_log /var/log/nginx/a24-pipeline-access.log;
    error_log /var/log/nginx/a24-pipeline-error.log;

    # Client body size (for file uploads)
    client_max_body_size 10M;

    location / {
        proxy_pass http://a24_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://a24_backend/health;
        access_log off;
    }
}
```

Enable site and restart nginx:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/a24-pipeline /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

## Step 7: Setup SSL Certificate

### Using Let's Encrypt (Free)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

## Step 8: Configure PetPooja Production Dashboard

1. Log in to PetPooja Production Dashboard
2. Go to **Integrations** → **Add New Integration**
3. Configure with PRODUCTION credentials and your domain URL

**Important:**
- Use your production domain (e.g., `https://api.yourdomain.com`)
- Use production app_key, app_secret, and access_token
- Configure webhook callbacks with HTTPS URLs

## Step 9: Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow PostgreSQL (if using same server)
sudo ufw allow 5432/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Step 10: Monitoring & Logging

### Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/a24-pipeline
```

Add:

```
/var/log/a24-pipeline/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload a24-pipeline > /dev/null 2>&1 || true
    endscript
}
```

### Monitor Application

```bash
# Check service status
sudo systemctl status a24-pipeline

# View logs
sudo tail -f /var/log/a24-pipeline/petpooja.log

# Monitor system resources
htop

# Check nginx logs
sudo tail -f /var/log/nginx/a24-pipeline-access.log
```

## Production Checklist

Before going live, verify:

- [ ] `PETPOOJA_SANDBOX_ENABLED=false` in .env
- [ ] Production PetPooja credentials configured
- [ ] `DEBUG=false` in .env
- [ ] `LOG_LEVEL=INFO` or higher
- [ ] `API_RELOAD=false` in .env
- [ ] Database backed up regularly
- [ ] SSL certificate installed and valid
- [ ] Firewall configured properly
- [ ] Process manager (systemd/supervisor) running
- [ ] Nginx reverse proxy configured
- [ ] Log rotation configured
- [ ] PetPooja dashboard configured with production URL
- [ ] All endpoints tested with production credentials
- [ ] Monitoring and alerting setup
- [ ] Error tracking configured (Sentry, etc.)

## Deployment Process

### Initial Deployment

```bash
# 1. Stop any running instance
sudo systemctl stop a24-pipeline

# 2. Pull latest code
cd /opt/a24-pipeline
git pull origin main

# 3. Install/update dependencies
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 4. Run migrations
source venv/bin/activate
alembic upgrade head
deactivate

# 5. Start service
sudo systemctl start a24-pipeline

# 6. Verify
sudo systemctl status a24-pipeline
curl https://api.yourdomain.com/health
```

### Zero-Downtime Deployment

For zero-downtime deployments, use blue-green or rolling deployment strategies with a load balancer.

## Backup Strategy

### Database Backup

```bash
# Create backup script
sudo nano /opt/a24-pipeline/scripts/backup.sh
```

Add:

```bash
#!/bin/bash
BACKUP_DIR="/backup/postgresql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME="a24_production"

# Create backup
pg_dump -h your-db-host -U a24_user -d $DB_NAME | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

Setup cron job:

```bash
# Add to crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/a24-pipeline/scripts/backup.sh
```

## Security Best Practices

1. **Use Strong Passwords**: All database and API credentials
2. **Enable Firewall**: Only allow necessary ports
3. **SSL/TLS**: Always use HTTPS in production
4. **Rate Limiting**: Protect against DDoS attacks
5. **Regular Updates**: Keep OS and packages updated
6. **Monitor Logs**: Watch for suspicious activity
7. **Backup Regularly**: Automate database backups
8. **Secrets Management**: Never commit .env file
9. **Access Control**: Use SSH keys, disable password auth
10. **Audit Trail**: Enable logging for all critical operations

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u a24-pipeline -n 100

# Check service file
sudo systemctl status a24-pipeline

# Verify python path
which python3.12

# Test manually
cd /opt/a24-pipeline
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Database Connection Issues

```bash
# Test database connection
psql -h your-db-host -U a24_user -d a24_production

# Check firewall
sudo ufw status

# Verify credentials in .env
cat /opt/a24-pipeline/.env | grep POSTGRES
```

### PetPooja API Errors

1. Verify `PETPOOJA_SANDBOX_ENABLED=false`
2. Check production credentials are correct
3. Verify restaurant_id and mapping_code
4. Check API logs for detailed error messages

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_orders_restaurant_id ON orders(restaurant_id);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_status ON orders(status);

-- Analyze tables
ANALYZE orders;
ANALYZE restaurants;
ANALYZE menu_items;
```

### Application Optimization

- Increase worker count based on CPU cores
- Enable database connection pooling
- Implement caching (Redis) for frequently accessed data
- Use CDN for static assets
- Enable gzip compression in nginx

## Support

For production issues:
- Check logs: `/var/log/a24-pipeline/petpooja.log`
- System logs: `sudo journalctl -u a24-pipeline`
- Contact PetPooja support: support@petpooja.com
- Review API documentation: `documents/API_REFERENCE.md`
