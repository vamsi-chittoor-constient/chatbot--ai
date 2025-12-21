# Sandbox Environment Setup Guide

## Overview

This guide explains how to set up and configure the A24 Restaurant Data Pipeline for PetPooja's **SANDBOX** environment for testing and development purposes.

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- PetPooja Sandbox Account Credentials
- AWS Credentials (for API Gateway authentication)
- ngrok or similar tunneling tool (for webhook testing)

## Step 1: Database Setup

### Install PostgreSQL

Ensure PostgreSQL is running on your system.

### Create Database

```sql
CREATE DATABASE a24_v1;
CREATE USER postgres WITH PASSWORD '123456';
GRANT ALL PRIVILEGES ON DATABASE a24_v1 TO postgres;
```

## Step 2: Environment Configuration

### Copy .env File

Create a `.env` file in the project root with the following configuration:

```bash
# =============================================================================
# Database Configuration (Development)
# =============================================================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5434
POSTGRES_DB=a24_v1
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123456

DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# =============================================================================
# PetPooja SANDBOX Configuration
# =============================================================================
# Enable sandbox mode
PETPOOJA_SANDBOX_ENABLED=true

# Sandbox API URL (AWS API Gateway)
PETPOOJA_SANDBOX_BASE_URL=https://qle1yy2ydc.execute-api.ap-southeast-1.amazonaws.com/V1

# Sandbox Dashboard URL
PETPOOJA_SANDBOX_DASHBOARD_URL=https://developerapi.petpooja.com

# PetPooja Sandbox Credentials
PETPOOJA_APP_KEY=your_sandbox_app_key
PETPOOJA_APP_SECRET=your_sandbox_app_secret
PETPOOJA_ACCESS_TOKEN=your_sandbox_access_token

# Sandbox Restaurant ID (provided by PetPooja)
PETPOOJA_SANDBOX_RESTAURANT_ID=4878

# Mapping Code (from PetPooja dashboard)
PETPOOJA_MAPPING_CODE=czw6b9ykas

# =============================================================================
# AWS Credentials for API Gateway (REQUIRED for Sandbox)
# =============================================================================
# These credentials are required for AWS Signature Version 4 authentication
# Get these from your PetPooja developer account
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-southeast-1

# =============================================================================
# PetPooja API Endpoints
# =============================================================================
PETPOOJA_SAVE_ORDER_ENDPOINT=/save_order
PETPOOJA_FETCH_MENU_ENDPOINT=/getrestaurantdetails
PETPOOJA_FETCH_RESTAURANT_ENDPOINT=/getrestaurantdetails

# =============================================================================
# Webhook Configuration (Development)
# =============================================================================
# Use ngrok URL for local testing
PETPOOJA_CALLBACK_URL=https://your-ngrok-id.ngrok-free.app/api/webhooks/petpooja/order-status

# Webhook Security Secret
WEBHOOK_SECRET=a24-petpooja-webhook-secret-2024

# =============================================================================
# Main Backend Integration (Optional for testing)
# =============================================================================
MAIN_BACKEND_URL=http://localhost:3000
MAIN_BACKEND_API_TOKEN=a24-backend-secure-token-2024

# =============================================================================
# API Server Configuration (Development)
# =============================================================================
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4
API_RELOAD=true
API_LOG_LEVEL=debug
DEBUG=true

# =============================================================================
# Application Settings
# =============================================================================
APP_NAME=A24 Restaurant Data Pipeline
APP_VERSION=1.0.0

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_LEVEL=DEBUG
LOG_FILE=logs/petpooja_microservice.log

# =============================================================================
# HTTP Client Configuration
# =============================================================================
HTTP_TIMEOUT=30
HTTP_MAX_RETRIES=3
HTTP_RETRY_DELAY=2

# =============================================================================
# Security Settings
# =============================================================================
ALLOWED_ORIGINS=*
RATE_LIMIT_PER_MINUTE=100
```

## Step 3: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Database Migration

```bash
# Initialize alembic (if not already done)
alembic init alembic

# Run migrations to create tables
alembic upgrade head
```

## Step 5: Setup Ngrok for Webhooks

PetPooja needs to send webhooks to your local machine. Use ngrok to create a public URL.

```bash
# Install ngrok
# Download from: https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8001

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)
# Update .env file with this URL:
# PETPOOJA_CALLBACK_URL=https://abc123.ngrok-free.app/api/webhooks/petpooja/order-status
```

## Step 6: Configure PetPooja Dashboard

Log in to PetPooja Developer Dashboard at https://developerapi.petpooja.com

### Add Integration

1. Go to **Integrations** → **Add New Integration**
2. Fill in the following details:

**Basic Information:**
- **App Key**: (copy from your .env file)
- **App Secret**: (copy from your .env file)
- **Access Token**: (copy from your .env file)
- **Base URL**: `https://your-ngrok-id.ngrok-free.app`
- **Client Authorization**: `Bearer a24-petpooja-webhook-secret-2024`

**Integration Type:**
- Select: **Menu Fetch**

**API Endpoints:**
- **Get Store Status**: `/api/restaurants/status`
- **Update Store Status**: `/api/restaurants/update-status`
- **Item Off**: `/api/menu/item/disable`
- **Item On**: `/api/menu/item/enable`

**Webhook Endpoints (Optional):**
- **Order Status Callback**: `/api/webhooks/petpooja/order-status`
- **Delivery Status Callback**: `/api/webhooks/petpooja/delivery-status`
- **Order Cancellation**: `/api/webhooks/petpooja/order-cancellation`

3. Click **Save Configuration**

## Step 7: Start the Application

```bash
# Start the FastAPI server
python main.py

# Or with uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The server will start at `http://localhost:8001`

## Step 8: Verify Setup

### 1. Health Check

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "petpooja_credentials": "configured"
}
```

### 2. Test Restaurant Fetch

```bash
curl -X POST http://localhost:8001/api/restaurants/4878/fetch-details \
  -H "Authorization: Bearer a24-backend-secure-token-2024"
```

### 3. Test Menu Sync

```bash
curl -X POST http://localhost:8001/api/menu/4878/sync \
  -H "Authorization: Bearer a24-backend-secure-token-2024"
```

### 4. Test Order Placement

```bash
curl -X POST http://localhost:8001/api/orders/place_order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer a24-backend-secure-token-2024" \
  -d '{
    "order_id": "TEST_001",
    "restaurant_id": "4878",
    "mapping_code": "czw6b9ykas",
    "customer": {
      "name": "Test Customer",
      "phone": "9999999999",
      "email": "test@example.com",
      "address": "Test Address"
    },
    "order": {
      "order_type": "delivery",
      "order_date_time": "2025-11-14T10:00:00"
    },
    "payment": {
      "payment_method": "cod",
      "delivery_charge": 50,
      "delivery_tax_percentage": 5,
      "packing_charge": 20,
      "packing_tax_percentage": 5
    },
    "items": [
      {
        "item_id": "7765862",
        "item_name": "Test Item",
        "item_price": 100,
        "final_price": 100,
        "item_quantity": 1,
        "gst_liability": "vendor",
        "tax_inclusive": true,
        "item_tax": []
      }
    ],
    "total_amount": 170,
    "tax_total": 0
  }'
```

## Step 9: AWS Credentials Setup

The sandbox API requires AWS Signature Version 4 authentication.

### Obtain AWS Credentials

Contact PetPooja support to get:
- AWS Access Key ID
- AWS Secret Access Key

Or try using your PetPooja credentials:
```bash
AWS_ACCESS_KEY_ID=<your_petpooja_app_key>
AWS_SECRET_ACCESS_KEY=<your_petpooja_app_secret>
```

### Update .env File

Add the credentials to your `.env` file:
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalrXU...
AWS_REGION=ap-southeast-1
```

## Common Issues & Solutions

### Issue 1: 403 Forbidden Error

**Cause**: AWS credentials not configured or invalid

**Solution**:
1. Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set in .env
2. Contact PetPooja for correct credentials
3. Try using PetPooja app_key and app_secret as AWS credentials

### Issue 2: Database Connection Error

**Cause**: PostgreSQL not running or incorrect credentials

**Solution**:
1. Check if PostgreSQL is running: `pg_isready -h localhost -p 5434`
2. Verify database credentials in .env
3. Create database if not exists

### Issue 3: Webhook Not Receiving

**Cause**: ngrok not running or URL not updated

**Solution**:
1. Verify ngrok is running: check https://localhost:4040
2. Update PETPOOJA_CALLBACK_URL in .env with current ngrok URL
3. Restart the application after updating .env
4. Update callback URL in PetPooja dashboard

### Issue 4: Order Placement Fails

**Cause**: Missing required fields or invalid data

**Solution**:
1. Check application logs: `tail -f logs/petpooja_microservice.log`
2. Verify all required fields are present in the request
3. Check restaurant_id and mapping_code are correct
4. Ensure AWS credentials are valid

## Testing Workflow

1. **Start Services**: PostgreSQL → Application → ngrok
2. **Sync Data**: Fetch restaurant details → Sync menu
3. **Place Orders**: Use Postman or curl to test order placement
4. **Monitor**: Check logs for API calls and responses
5. **Verify**: Check PetPooja dashboard for order status

## Logs Location

Application logs are stored at:
```
logs/petpooja_microservice.log
```

View logs in real-time:
```bash
tail -f logs/petpooja_microservice.log
```

## Next Steps

After successful sandbox setup:
1. Test all API endpoints
2. Verify webhook functionality
3. Test order lifecycle (place → accept → dispatch → deliver)
4. Review error handling and edge cases
5. Once satisfied, proceed to Production setup

## Support

For issues:
- Check logs: `logs/petpooja_microservice.log`
- Review API documentation: `documents/API_REFERENCE.md`
- Contact PetPooja support: support@petpooja.com
