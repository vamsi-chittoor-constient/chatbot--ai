# AWS EC2 Deployment Guide
## Restaurant AI Chatbot - Production Deployment

This guide covers deploying the Restaurant AI Chatbot to AWS EC2 for production use with 20-100 concurrent users.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS EC2 Instance Setup](#aws-ec2-instance-setup)
3. [Connect to EC2](#connect-to-ec2)
4. [Install System Dependencies](#install-system-dependencies)
5. [Setup PostgreSQL Database](#setup-postgresql-database)
6. [Setup Redis Cache](#setup-redis-cache)
7. [Upload Application Code](#upload-application-code)
8. [Configure Python Environment](#configure-python-environment)
9. [Environment Configuration](#environment-configuration)
10. [Database Migrations](#database-migrations)
11. [Systemd Service Setup](#systemd-service-setup)
12. [Nginx Reverse Proxy](#nginx-reverse-proxy)
13. [SSL/HTTPS Setup](#sslhttps-setup-optional)
14. [Testing the Deployment](#testing-the-deployment)
15. [Monitoring & Logs](#monitoring--logs)
16. [Troubleshooting](#troubleshooting)
17. [Cost Estimate](#cost-estimate)

---

## Prerequisites

Before starting, ensure you have:

- [ ] AWS Account with EC2 access
- [ ] OpenAI API Key (get from https://platform.openai.com/api-keys)
- [ ] SSH client (built into Windows 10+, Mac, Linux)
- [ ] Your application code (this codebase)

---

## AWS EC2 Instance Setup

### Step 1: Launch EC2 Instance

1. Log into AWS Console → EC2 → **Launch Instance**

2. **Configure Instance:**

   | Setting | Value |
   |---------|-------|
   | Name | `restaurant-ai-chatbot` |
   | AMI | Ubuntu Server 22.04 LTS (64-bit x86) |
   | Instance Type | `t3.medium` (20 users) or `t3.large` (100 users) |
   | Key Pair | Create new → Download `.pem` file → Save securely! |

3. **Network Settings (Security Group):**

   Click "Edit" and add these rules:

   | Type | Port | Source | Description |
   |------|------|--------|-------------|
   | SSH | 22 | My IP | SSH access |
   | HTTP | 80 | 0.0.0.0/0 | Web traffic |
   | HTTPS | 443 | 0.0.0.0/0 | Secure web traffic |
   | Custom TCP | 8000 | 0.0.0.0/0 | API (testing only) |

4. **Storage:**
   - Size: `20 GB`
   - Type: `gp3`

5. Click **Launch Instance**

### Step 2: Allocate Elastic IP (Recommended)

1. EC2 → Elastic IPs → **Allocate Elastic IP address**
2. Select the new IP → Actions → **Associate Elastic IP address**
3. Select your instance → Associate

> This gives you a permanent IP that doesn't change when instance restarts.

---

## Connect to EC2

### Windows (PowerShell)

```powershell
# Navigate to where your .pem file is
cd C:\Users\YourName\Downloads

# Connect (replace with your values)
ssh -i "your-key.pem" ubuntu@YOUR_EC2_PUBLIC_IP
```

### Mac/Linux

```bash
# Set permissions (one time)
chmod 400 your-key.pem

# Connect
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### If connection fails:

```bash
# Check security group allows SSH from your IP
# Check instance is running
# Check you're using correct username (ubuntu for Ubuntu AMI)
```

---

## Install System Dependencies

Run these commands on EC2:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL 15
sudo apt install -y postgresql postgresql-contrib

# Install Redis
sudo apt install -y redis-server

# Install Nginx
sudo apt install -y nginx

# Install build tools (for Python packages)
sudo apt install -y build-essential libpq-dev

# Install git
sudo apt install -y git

# Verify installations
python3.11 --version  # Should show 3.11.x
psql --version        # Should show 15.x
redis-server --version # Should show 7.x
nginx -v              # Should show 1.x
```

---

## Setup PostgreSQL Database

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

In PostgreSQL prompt:

```sql
-- Create user (change password!)
CREATE USER admin WITH PASSWORD 'YourSecurePassword123!';

-- Create database
CREATE DATABASE resturant_ai OWNER admin;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE resturant_ai TO admin;

-- Allow connections
ALTER USER admin CREATEDB;

-- Exit
\q
```

### Configure PostgreSQL for local connections:

```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Find this line:
# local   all             all                                     peer

# Change 'peer' to 'md5':
# local   all             all                                     md5

# Save and exit (Ctrl+X, Y, Enter)

# Restart PostgreSQL
sudo systemctl restart postgresql

# Test connection
psql -U admin -d resturant_ai -h localhost
# Enter password when prompted
# Type \q to exit
```

---

## Setup Redis Cache

```bash
# Redis should already be running, but let's configure it
sudo nano /etc/redis/redis.conf

# Find and change these settings:
# maxmemory 256mb
# maxmemory-policy allkeys-lru

# Save and restart
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping
# Should return: PONG
```

---

## Upload Application Code

### Option A: Using Git (Recommended)

```bash
# On EC2
cd /home/ubuntu

# If you have a git repository:
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### Option B: Using SCP (Direct Upload)

On your **local Windows machine**:

```powershell
# Create archive of codebase
cd C:\Users\HP\Downloads\Order-v1-codebase
tar -czvf codebase.tar.gz codebase

# Upload to EC2
scp -i "your-key.pem" codebase.tar.gz ubuntu@YOUR_EC2_IP:/home/ubuntu/
```

On **EC2**:

```bash
# Extract
cd /home/ubuntu
tar -xzvf codebase.tar.gz
cd codebase

# Remove archive to save space
rm ../codebase.tar.gz
```

---

## Configure Python Environment

```bash
cd /home/ubuntu/codebase

# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# This may take 5-10 minutes
```

### If you get errors:

```bash
# For psycopg2 errors:
sudo apt install -y libpq-dev python3.11-dev

# For numpy/scipy errors:
sudo apt install -y gfortran libopenblas-dev

# Then retry:
pip install -r requirements.txt
```

---

## Environment Configuration

Create the `.env` file:

```bash
nano /home/ubuntu/codebase/.env
```

Paste and customize:

```env
# =============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# =============================================================================

# Application
APP_NAME=Restaurant AI Assistant
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# =============================================================================
# DATABASE - PostgreSQL
# =============================================================================
DATABASE_URL=postgresql+asyncpg://admin:YourSecurePassword123!@localhost:5432/resturant_ai
DB_HOST=localhost
DB_PORT=5432
DB_NAME=resturant_ai
DB_USER=admin
DB_PASSWORD=YourSecurePassword123!

# =============================================================================
# REDIS
# =============================================================================
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# =============================================================================
# OPENAI API - REQUIRED
# =============================================================================
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_API_KEY_HERE

# Models
AGENT_MODEL=gpt-4o-mini
INTENT_CLASSIFICATION_MODEL=gpt-4o
ENTITY_EXTRACTION_MODEL=gpt-4o-mini

# =============================================================================
# SECURITY
# =============================================================================
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-64-character-random-string-here

# =============================================================================
# API CONFIGURATION
# =============================================================================
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=https://yourdomain.com
ALLOWED_ORIGINS=*

# =============================================================================
# TESTING MODE
# =============================================================================
# Set to false for production with real SMS OTP
TEST_OTP_ENABLED=true
TEST_OTP_CODE=123456
AUTH_REQUIRED=true

# =============================================================================
# CACHING
# =============================================================================
ENABLE_RESPONSE_CACHING=true
ENABLE_USER_SESSION_CACHE=true
ENABLE_INVENTORY_CACHE=true

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL=INFO

# =============================================================================
# OPTIONAL - Payment (Razorpay)
# =============================================================================
# RAZORPAY_KEY_ID=your_razorpay_key
# RAZORPAY_KEY_SECRET=your_razorpay_secret

# =============================================================================
# OPTIONAL - SMS (MSG91)
# =============================================================================
# MSG91_API_KEY=your_msg91_key
# MSG91_SENDER_ID=RESTAI
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Generate SECRET_KEY:

```bash
python3.11 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and paste into .env as SECRET_KEY
```

---

## Database Migrations

```bash
cd /home/ubuntu/codebase
source venv/bin/activate

# Run migrations
alembic upgrade head

# Verify tables were created
psql -U admin -d resturant_ai -h localhost -c "\dt"
```

You should see tables like:
- users
- sessions
- menu_items
- orders
- etc.

---

## Systemd Service Setup

Create a systemd service for auto-start and management:

```bash
sudo nano /etc/systemd/system/restaurant-ai.service
```

Paste:

```ini
[Unit]
Description=Restaurant AI Chatbot API
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/codebase
Environment="PATH=/home/ubuntu/codebase/venv/bin:/usr/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/ubuntu/codebase/venv/bin/python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

Save and enable:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable restaurant-ai

# Start the service
sudo systemctl start restaurant-ai

# Check status
sudo systemctl status restaurant-ai
```

Expected output:
```
● restaurant-ai.service - Restaurant AI Chatbot API
     Loaded: loaded (/etc/systemd/system/restaurant-ai.service; enabled)
     Active: active (running) since ...
```

---

## Nginx Reverse Proxy

### Create Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/restaurant-ai
```

Paste:

```nginx
upstream restaurant_api {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name YOUR_DOMAIN_OR_IP;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/restaurant-ai-access.log;
    error_log /var/log/nginx/restaurant-ai-error.log;

    # API endpoints
    location / {
        proxy_pass http://restaurant_api;
        proxy_http_version 1.1;

        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;

        # Buffering
        proxy_buffering off;
        proxy_buffer_size 4k;
    }

    # Health check endpoint (no logging)
    location /api/v1/health {
        proxy_pass http://restaurant_api;
        access_log off;
    }
}
```

Replace `YOUR_DOMAIN_OR_IP` with your EC2 public IP or domain name.

### Enable the site:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/restaurant-ai /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Expected output:
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## SSL/HTTPS Setup (Optional)

For production with a domain name, use Let's Encrypt for free SSL:

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)

# Auto-renewal is set up automatically
# Test renewal:
sudo certbot renew --dry-run
```

---

## Testing the Deployment

### 1. Check services are running:

```bash
# Check all services
sudo systemctl status restaurant-ai
sudo systemctl status postgresql
sudo systemctl status redis-server
sudo systemctl status nginx
```

### 2. Test API endpoints:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# From outside (use your EC2 IP)
curl http://YOUR_EC2_IP/api/v1/health
```

### 3. Access Swagger docs:

Open in browser:
```
http://YOUR_EC2_IP/docs
```

### 4. Test chat endpoint:

```bash
curl -X POST http://YOUR_EC2_IP/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hi",
    "session_id": "test-123",
    "device_id": "device-456"
  }'
```

---

## Monitoring & Logs

### View application logs:

```bash
# Live logs
sudo journalctl -u restaurant-ai -f

# Last 100 lines
sudo journalctl -u restaurant-ai -n 100

# Logs from today
sudo journalctl -u restaurant-ai --since today
```

### View Nginx logs:

```bash
# Access logs
sudo tail -f /var/log/nginx/restaurant-ai-access.log

# Error logs
sudo tail -f /var/log/nginx/restaurant-ai-error.log
```

### System monitoring:

```bash
# CPU and memory
htop

# Disk usage
df -h

# Database connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Redis info
redis-cli info stats
```

---

## Troubleshooting

### Service won't start:

```bash
# Check logs for errors
sudo journalctl -u restaurant-ai -n 50 --no-pager

# Common issues:
# - Wrong path in service file
# - Missing .env file
# - Database connection error
# - Port already in use
```

### Database connection error:

```bash
# Test database connection
psql -U admin -d resturant_ai -h localhost

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check pg_hba.conf allows md5 authentication
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -v "^#"
```

### Redis connection error:

```bash
# Test Redis
redis-cli ping

# Check Redis is running
sudo systemctl status redis-server
```

### Nginx 502 Bad Gateway:

```bash
# Check if backend is running
curl http://localhost:8000/api/v1/health

# Check Nginx error logs
sudo tail -20 /var/log/nginx/restaurant-ai-error.log

# Restart services
sudo systemctl restart restaurant-ai
sudo systemctl restart nginx
```

### Permission denied errors:

```bash
# Fix ownership
sudo chown -R ubuntu:ubuntu /home/ubuntu/codebase

# Fix .env permissions
chmod 600 /home/ubuntu/codebase/.env
```

---

## Cost Estimate

### Monthly costs for 20-100 concurrent users:

| Resource | Specification | Monthly Cost |
|----------|---------------|--------------|
| EC2 Instance | t3.medium (2 vCPU, 4GB RAM) | ~$30 |
| EC2 Instance | t3.large (2 vCPU, 8GB RAM) | ~$60 |
| EBS Storage | 20 GB gp3 | ~$2 |
| Data Transfer | 50 GB outbound | ~$5 |
| Elastic IP | 1 IP (if instance running) | Free |
| **Total (t3.medium)** | | **~$37/month** |
| **Total (t3.large)** | | **~$67/month** |

### Additional costs:

| Service | Estimate |
|---------|----------|
| OpenAI API | $50-150/month (depends on usage) |
| Domain name | $10-15/year |
| SSL Certificate | Free (Let's Encrypt) |

---

## Quick Reference Commands

```bash
# Start/Stop/Restart application
sudo systemctl start restaurant-ai
sudo systemctl stop restaurant-ai
sudo systemctl restart restaurant-ai

# View logs
sudo journalctl -u restaurant-ai -f

# Update code (if using git)
cd /home/ubuntu/codebase
git pull
sudo systemctl restart restaurant-ai

# Restart all services
sudo systemctl restart postgresql redis-server restaurant-ai nginx

# Check disk space
df -h

# Check memory
free -m

# Check running processes
ps aux | grep python
```

---

## Security Checklist

- [ ] Changed default database password
- [ ] Generated unique SECRET_KEY
- [ ] Restricted SSH to your IP only
- [ ] Enabled HTTPS with SSL certificate
- [ ] Set `DEBUG=false` in .env
- [ ] Removed port 8000 from security group (use Nginx on 80/443)
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`

---

## Support

For issues with:
- **This codebase**: Check logs with `sudo journalctl -u restaurant-ai -f`
- **AWS EC2**: https://docs.aws.amazon.com/ec2/
- **OpenAI API**: https://platform.openai.com/docs

---

*Last updated: December 2024*

---

## Appendix: Amazon Linux 2023 Deployment

If using Amazon Linux 2023 instead of Ubuntu, follow these modified steps:

### Install System Dependencies (Amazon Linux 2023)

```bash
# Update system
sudo dnf update -y

# Install Python 3.11
sudo dnf install -y python3.11 python3.11-pip python3.11-devel

# Install PostgreSQL 15
sudo dnf install -y postgresql15-server postgresql15
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install Redis
sudo dnf install -y redis6
sudo systemctl start redis6
sudo systemctl enable redis6

# Install Nginx
sudo dnf install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Install build tools
sudo dnf install -y gcc gcc-c++ make libpq-devel

# Install git
sudo dnf install -y git
```

### Docker Deployment (Recommended for Amazon Linux 2023)

```bash
# Install Docker
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for docker group
exit

# After reconnecting, deploy with Docker
cd restaurant-ai/docker
docker-compose up -d --build
```

### Key Differences from Ubuntu

| Task | Ubuntu 22.04 | Amazon Linux 2023 |
|------|--------------|-------------------|
| Package manager | apt | dnf |
| Python install | ppa:deadsnakes | Built-in dnf |
| Redis service | redis-server | redis6 |
| PostgreSQL setup | Automatic | Requires --initdb |
| Default user | ubuntu | ec2-user |

---

## Instance Type Quick Reference

| Users | Instance | vCPUs | RAM | Cost/Month |
|-------|----------|-------|-----|------------|
| 1-20 | t3.medium | 2 | 4GB | ~$30 |
| 20-50 | t3.large | 2 | 8GB | ~$60 |
| 50-100 | t3.xlarge | 4 | 16GB | ~$120 |
| 100-200 | m6i.xlarge | 4 | 16GB | ~$140 |
| 200+ | m6i.2xlarge | 8 | 32GB | ~$280 |

**Recommendation**: Start with t3.large (~$60/month) for most restaurants.
