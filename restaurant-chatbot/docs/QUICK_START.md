# Restaurant AI Assistant - Quick Start Guide

## 🚀 One-Click Setup

### Windows Users
```bash
# Double-click or run in Command Prompt
start.bat
```

### Linux/macOS Users
```bash
# Make executable and run
chmod +x start.sh
./start.sh
```

## 🔧 Manual Setup (If Needed)

### 1. Prerequisites
- **Python 3.8+** (Required)
- **PostgreSQL** (Required) 
- **Redis** (Optional - will be auto-started)
- **MongoDB** (Optional - will be auto-started)

### 2. Database Setup
The startup script will automatically:
- Create all database tables
- Insert test data
- Configure the schema

If you need to run database setup manually:
```bash
python fix_database_issues.py
```

### 3. Environment Configuration
The `.env` file is already configured with default values. Key settings:

```env
# Database (Update if needed)
DATABASE_URL=postgresql+asyncpg://postgres:123456@localhost:5432/restaurant_ai_dev

# API Keys (Update with your keys)
OPENAI_API_KEY=your_openai_key_here
RAZORPAY_KEY_ID=your_razorpay_key_here
```

### 4. Manual Service Start
If you prefer to start services manually:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Service Status

After startup, you'll see:
- ✅ **PostgreSQL**: Required for data storage
- ✅ **Database Schema**: Auto-created with test data
- ✅/⚠️ **Redis**: Optional (caching, sessions)
- ✅/⚠️ **MongoDB**: Optional (analytics, testing)

## 🌐 Access Points

Once running:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

## 🧪 Testing

### Test the API
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Test chat (WebSocket)
# Use the test client at: http://localhost:8000/static/testing/
```

### Run Test Suite
```bash
python comprehensive_test_suite.py
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check PostgreSQL is running
# Windows: Check Services
# Linux: sudo systemctl status postgresql
# macOS: brew services list | grep postgresql
```

#### 2. Redis/MongoDB Not Available
These are optional services. The app will work without them but with limited functionality:
- **Without Redis**: No caching, sessions stored in memory
- **Without MongoDB**: No analytics data storage

#### 3. Port Already in Use
```bash
# Check what's using port 8000
# Windows: netstat -ano | findstr :8000
# Linux/macOS: lsof -i :8000

# Kill the process or change port in .env
API_PORT=8001
```

#### 4. OpenAI API Errors
Update your API key in `.env`:
```env
OPENAI_API_KEY=your_actual_openai_key_here
```

### Log Files
Check logs for detailed error information:
- Application logs are printed to console
- Database logs: Check PostgreSQL logs
- Service logs: Check individual service logs

## 📝 Development

### Project Structure
```
app/
├── api/           # FastAPI routes and middleware
├── core/          # Database, Redis, configuration
├── database/      # SQLAlchemy models
├── features/      # Business logic (booking, ordering, etc.)
├── orchestration/ # LangGraph agent orchestration
├── services/      # External service integrations
└── tools/         # Agent tools and utilities
```

### Adding New Features
1. Create new agent in `app/features/`
2. Add database models in `app/database/models.py`
3. Register agent in `app/orchestration/graph.py`
4. Add API routes in `app/api/routes/`

### Environment Variables
Key configuration options in `.env`:
- `DEBUG=true` - Enable development mode
- `LOG_LEVEL=INFO` - Set logging level
- `REACT_GLOBAL_ENABLED=true` - Enable AI agents

## 🆘 Support

### Getting Help
1. Check this README first
2. Look at error logs in console
3. Verify all prerequisites are installed
4. Check the `.env` file configuration

### Common Commands
```bash
# Restart services
python start_services.py

# Reset database
python fix_database_issues.py

# Check service status
curl http://localhost:8000/api/v1/health

# View API documentation
# Open: http://localhost:8000/docs
```

## 🎉 Success!

If you see:
```
✅ Database: Ready
✅ Database Schema: Ready  
✅ Redis: Ready
✅ MongoDB: Ready
🚀 Starting Restaurant AI Assistant...
   API will be available at: http://localhost:8000
```

You're all set! The Restaurant AI Assistant is now running and ready to handle requests.

---

**Need help?** Check the logs for detailed error messages and ensure all prerequisites are installed.