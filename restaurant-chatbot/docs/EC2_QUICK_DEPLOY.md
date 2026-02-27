# EC2 One-Command Deployment Guide

Deploy the Restaurant AI Assistant on AWS EC2 in under 10 minutes.

## Instance Type Selection

| Concurrent Users | Instance | vCPUs | RAM | Storage | Cost/Month | Notes |
|------------------|----------|-------|-----|---------|------------|-------|
| 1-20 | t3.medium | 2 | 4GB | 30GB | ~$30 | Development/Testing |
| 20-50 | t3.large | 2 | 8GB | 50GB | ~$60 | Small restaurant |
| 50-100 | t3.xlarge | 4 | 16GB | 100GB | ~$120 | Medium restaurant |
| 100-200 | m6i.xlarge | 4 | 16GB | 100GB | ~$140 | Busy restaurant |
| 200-500 | m6i.2xlarge | 8 | 32GB | 200GB | ~$280 | High traffic |
| 500+ | m6i.4xlarge | 16 | 64GB | 500GB | ~$560 | Enterprise |

**Recommendation**: Start with `t3.large` (~$60/month) for most restaurants.

---

## Step 1: Launch EC2 Instance

### AWS Console Steps:
1. Go to EC2 Dashboard → Launch Instance
2. **Name**: `restaurant-ai`
3. **AMI**: Amazon Linux 2023 (recommended) or Ubuntu 22.04
4. **Instance type**: t3.large (or per table above)
5. **Key pair**: Create or select existing
6. **Security Group**: Create with these rules:

| Type | Port | Source | Purpose |
|------|------|--------|---------|
| SSH | 22 | Your IP | Admin access |
| HTTP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | 443 | 0.0.0.0/0 | Secure web traffic |

7. **Storage**: 50GB gp3 (minimum)
8. Click **Launch Instance**

---

## Step 2: Connect to Instance

```bash
# Download your .pem key file and connect
chmod 400 your-key.pem
ssh -i your-key.pem ec2-user@<your-ec2-public-ip>
```

---

## Step 3: Install Docker (Amazon Linux 2023)

```bash
# Update system
sudo dnf update -y

# Install Docker
sudo dnf install -y docker git

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# IMPORTANT: Logout and reconnect for docker group to take effect
exit
```

---

## Step 4: Deploy Application

```bash
# Reconnect to instance
ssh -i your-key.pem ec2-user@<your-ec2-public-ip>

# Clone repository
git clone https://github.com/vamsi-chittoor-constient/chatbot_food.git
cd chatbot_food

# Configure environment
cp .env.example .env
nano .env
```

### Required .env Configuration:

```bash
# Minimum required - add your OpenAI API key
OPENAI_API_KEY=sk-your-actual-openai-key-here

# For high traffic - add multiple accounts (optional)
ACCOUNT_1_API_KEY=sk-account-1-key
ACCOUNT_2_API_KEY=sk-account-2-key
# ... up to ACCOUNT_20_API_KEY
```

### Deploy with ONE command:

```bash
docker compose up -d --build
```

### Wait for services to start (~2-3 minutes):

```bash
# Watch the logs
docker compose logs -f

# Check service status
docker compose ps
```

---

## Step 5: Access Your Application

Your app is now live at:

| Service | URL |
|---------|-----|
| Frontend | `http://<ec2-public-ip>` |
| API | `http://<ec2-public-ip>/api/v1` |
| API Docs | `http://<ec2-public-ip>/api/v1/docs` |
| Health Check | `http://<ec2-public-ip>/api/v1/health` |

---

## Step 6: Add Custom Domain (Optional)

### Point DNS to EC2:
1. Get an Elastic IP (so IP doesn't change on restart):
   - EC2 Console → Elastic IPs → Allocate → Associate with instance
2. Add A record in your DNS provider pointing to Elastic IP

### Add SSL with Certbot:

```bash
# Install Certbot
sudo dnf install -y certbot

# Stop nginx temporarily
docker compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Update nginx config to use SSL (or use the certificate with your nginx container)
# Restart services
docker compose up -d
```

---

## Management Commands

```bash
# View logs
docker compose logs -f
docker compose logs -f app      # Only app logs

# Restart all services
docker compose restart

# Restart specific service
docker compose restart app

# Stop everything
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v

# Update and redeploy
git pull
docker compose up -d --build

# Check resource usage
docker stats
```

---

## Ubuntu 22.04 Alternative

If using Ubuntu instead of Amazon Linux:

```bash
# Connect
ssh -i your-key.pem ubuntu@<your-ec2-public-ip>

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git

sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu

# Logout and reconnect, then continue from Step 4
exit
```

---

## Scaling Guide

### When to Scale Up:

| Symptom | Solution |
|---------|----------|
| High CPU (>80%) | Upgrade instance type |
| High Memory (>85%) | Upgrade instance type |
| Slow responses | Add more OpenAI accounts |
| Rate limit errors | Add more OpenAI accounts |

### Multi-Account Load Balancing:

With 20 OpenAI accounts configured, the system automatically:
- Round-robin distributes requests across accounts
- Switches accounts at 80% rate limit usage
- Handles 10,000+ RPM combined capacity

---

## Troubleshooting

### Services not starting:
```bash
docker compose logs app
docker compose ps
```

### Database connection issues:
```bash
docker compose logs postgres
docker compose exec postgres psql -U admin -d restaurant_ai -c "SELECT 1"
```

### Redis issues:
```bash
docker compose exec redis redis-cli ping
```

### Check disk space:
```bash
df -h
docker system df
docker system prune -a  # Clean up unused images
```

### View application errors:
```bash
docker compose logs app --tail 100 | grep -i error
```

---

## Cost Optimization

### Use Spot Instances (up to 90% savings):
- Good for development/testing
- Not recommended for production (can be terminated)

### Reserved Instances (up to 72% savings):
- Commit to 1 or 3 years
- Best for production workloads

### Auto-scaling (coming soon):
- Scale based on traffic patterns
- Requires ECS/EKS setup

---

## Security Checklist

- [ ] Use Elastic IP (static IP)
- [ ] Restrict SSH to your IP only
- [ ] Enable AWS CloudWatch monitoring
- [ ] Set up automated backups for data volumes
- [ ] Use AWS Secrets Manager for API keys (advanced)
- [ ] Enable SSL/TLS with custom domain
- [ ] Set up AWS WAF for DDoS protection (optional)

---

## Quick Reference

```bash
# One-liner to check everything
docker compose ps && docker compose logs --tail 5 app

# Quick health check
curl http://localhost/api/v1/health

# Test chat endpoint
curl -X POST http://localhost/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-123", "message": "show menu"}'
```

---

*Last updated: December 2024*
