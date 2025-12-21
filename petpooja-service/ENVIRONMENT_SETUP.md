# Environment Configuration Guide

Complete guide for configuring environment variables for the PetPooja Service.

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Update required values:**
   - Database credentials (if different from defaults)
   - PetPooja API URLs (if using production)
   - Security settings (encryption key, webhook secret)
   - Callback URLs (for production deployment)

3. **Start the service:**
   ```bash
   # Local development
   python main.py

   # Docker deployment
   docker-compose -f ../docker-compose.root.yml up -d
   ```

---

## Environment Variables Reference

### Database Configuration

#### Shared Database Settings
Both `petpooja-service` and `restaurant-chatbot` share the same PostgreSQL database.

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | Database host (`postgres` for Docker, `localhost` for local) |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_DB` | `restaurant_ai` | Database name |
| `POSTGRES_USER` | `admin` | Database user |
| `POSTGRES_PASSWORD` | `admin123` | Database password |

#### Database Connection Pool Settings (Sync)

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_POOL_SIZE` | `10` | Number of connections to maintain |
| `DB_MAX_OVERFLOW` | `20` | Maximum overflow connections |
| `DB_POOL_TIMEOUT` | `30` | Seconds to wait for connection |
| `DB_POOL_RECYCLE` | `1800` | Recycle connections after 30 minutes |
| `DB_STATEMENT_TIMEOUT` | `30000` | SQL query timeout (milliseconds) |
| `DB_EXECUTOR_MAX_WORKERS` | `2` | Thread pool size for sync DB ops |

#### Database Connection Pool Settings (Async)

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_ASYNC_POOL_SIZE` | `20` | Async pool size (can be larger) |
| `DB_ASYNC_MAX_OVERFLOW` | `40` | Async max overflow |
| `DB_ASYNC_POOL_TIMEOUT` | `30` | Async pool timeout (seconds) |
| `DB_ASYNC_POOL_RECYCLE` | `1800` | Async connection recycle (seconds) |

---

### PetPooja API Configuration

#### Production & Sandbox URLs

| Variable | Default | Description |
|----------|---------|-------------|
| `PETPOOJA_BASE_URL` | `https://api-v2.petpooja.com` | Production API base URL |
| `PETPOOJA_SANDBOX_ENABLED` | `true` | Enable sandbox mode (set to `false` for production) |
| `PETPOOJA_SANDBOX_BASE_URL` | AWS API Gateway URL | Sandbox base URL |
| `PETPOOJA_SANDBOX_ORDER_URL` | AWS API Gateway URL | Sandbox order URL |
| `PETPOOJA_SANDBOX_UPDATE_ORDER_URL` | AWS API Gateway URL | Sandbox order status update URL |
| `PETPOOJA_SANDBOX_DASHBOARD_URL` | `https://developerapi.petpooja.com` | Sandbox dashboard |

**Important:** PetPooja credentials (app_key, app_secret, access_token) should be passed via API request body, NOT stored in .env

#### API Endpoints

| Variable | Default | Description |
|----------|---------|-------------|
| `PETPOOJA_SAVE_ORDER_ENDPOINT` | `/save_order` | Save order endpoint |
| `PETPOOJA_FETCH_MENU_ENDPOINT` | `/mapped_restaurant_menus` | Fetch menu endpoint |
| `PETPOOJA_FETCH_RESTAURANT_ENDPOINT` | `/getrestaurantdetails` | Fetch restaurant endpoint |

---

### Webhook & Callback Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PETPOOJA_CALLBACK_URL` | `http://localhost:8001/...` | Your public URL for PetPooja callbacks |
| `WEBHOOK_SECRET` | `your-secure-webhook-secret-here` | Secret for HMAC verification |
| `PETPOOJA_WEBHOOK_ENDPOINT` | `/webhook` | Webhook base path |

**Production Setup:**
- Configure webhook URLs in PetPooja Dashboard:
  - Order Status: `{YOUR_URL}/api/webhooks/petpooja/order-status`
  - Delivery Status: `{YOUR_URL}/api/webhooks/petpooja/delivery-status`
  - Order Cancellation: `{YOUR_URL}/api/webhooks/petpooja/order-cancellation`

---

### Main Backend Integration

| Variable | Default | Description |
|----------|---------|-------------|
| `MAIN_BACKEND_URL` | `http://localhost:3000` | Main backend URL |
| `MAIN_BACKEND_API_TOKEN` | `your-backend-api-token-here` | Backend API token (change in production!) |
| `MAIN_BACKEND_WEBHOOK_ENDPOINT` | `/api/webhooks/petpooja` | Backend webhook endpoint |

---

### API Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Bind to all interfaces |
| `API_PORT` | `8001` | Service port |
| `API_WORKERS` | `4` | Number of Uvicorn workers |
| `API_RELOAD` | `true` | Auto-reload on code changes (dev only) |
| `API_LOG_LEVEL` | `info` | Log level: debug, info, warning, error |
| `DEBUG` | `true` | Enable debug mode (dev only) |
| `APP_NAME` | `A24 Restaurant Data Pipeline` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |

---

### HTTP Client Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HTTP_TIMEOUT` | `30` | Timeout in seconds |
| `HTTP_MAX_RETRIES` | `3` | Number of retries |
| `HTTP_RETRY_DELAY` | `2` | Delay between retries (seconds) |
| `HTTPX_MAX_KEEPALIVE_CONNECTIONS` | `20` | Keep-alive connections |
| `HTTPX_MAX_CONNECTIONS` | `100` | Total connection limit |
| `CREDENTIALS_CACHE_TTL_SECONDS` | `300` | Credentials cache TTL (5 minutes) |

---

### Security Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENCRYPTION_KEY` | `your-32-byte-base64-encoded-key-here` | Fernet encryption key |
| `ALLOWED_ORIGINS` | `*` | CORS origins (use specific domains in production!) |
| `RATE_LIMIT_PER_MINUTE` | `60` | Requests per minute per IP |

**Generate Encryption Key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

### Order Processing Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ORDER_ID_PREFIX` | `A24-` | Prefix for generated order IDs |
| `PETPOOJA_ORDER_UDID` | `a24-pipeline` | Unique device ID |
| `PETPOOJA_ORDER_DEVICE_TYPE` | `Web` | Device type (Web/Mobile/POS) |
| `DEFAULT_PREP_TIME_OFFSET_MINUTES` | `30` | Default prep time offset |
| `MIN_PREP_TIME_MINUTES` | `20` | Minimum preparation time |
| `URGENT_ORDER_TIME_MINUTES` | `30` | Urgent order threshold |

---

### Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_FILE` | `logs/petpooja_microservice.log` | Log file path |

---

## Environment-Specific Configurations

### Development Environment
- `POSTGRES_HOST=localhost`
- `DEBUG=true`
- `API_RELOAD=true`
- `LOG_LEVEL=DEBUG`
- `PETPOOJA_SANDBOX_ENABLED=true`
- `ALLOWED_ORIGINS=*`

### Production Environment
- `POSTGRES_HOST=postgres`
- `DEBUG=false`
- `API_RELOAD=false`
- `LOG_LEVEL=WARNING`
- `PETPOOJA_SANDBOX_ENABLED=false`
- `ALLOWED_ORIGINS=https://yourdomain.com`
- Generate secure random strings for all secrets

---

## Security Best Practices

### 1. Never Commit Secrets
- ✅ `.env` is in `.gitignore`
- ✅ `.env.example` contains safe placeholder values
- ❌ Never commit actual `.env` files to git

### 2. Rotate Secrets Regularly
- Change `WEBHOOK_SECRET` periodically
- Rotate `ENCRYPTION_KEY` and re-encrypt stored credentials
- Update `MAIN_BACKEND_API_TOKEN` regularly

### 3. Use Environment-Specific Secrets
- Use different secrets for dev/staging/production
- Never use production secrets in development

### 4. CORS Configuration
```env
# ❌ Never use wildcard in production
ALLOWED_ORIGINS=*

# ✅ Use specific domains
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## Troubleshooting

### Database Connection Issues
**Problem:** `could not connect to server`

**Solution:** Check `POSTGRES_HOST` setting
- For Docker Compose: `POSTGRES_HOST=postgres`
- For local development: `POSTGRES_HOST=localhost`

### PetPooja API Errors
**Problem:** 401 Unauthorized

**Solution:** Credentials should be passed via API request body, not environment variables. Verify credentials using `/api/chain/fetch-petpooja` endpoint.

### Webhook Not Receiving Callbacks
**Problem:** PetPooja not sending webhooks

**Solutions:**
1. Verify `PETPOOJA_CALLBACK_URL` is publicly accessible
2. For local testing, use ngrok: `ngrok http 8001`
3. Check PetPooja Dashboard webhook configuration
4. Verify `WEBHOOK_SECRET` matches PetPooja settings

---

**Last Updated:** 2025-12-21
**Version:** 2.0.0 (Environment-based configuration)
