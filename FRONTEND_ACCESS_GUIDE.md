# Frontend Access Guide
**Restaurant Chatbot - Local Development**

---

## 🎯 Quick Start (Recommended)

### **Testing Interface - Instant Access**

**URL:** http://localhost:8000/static/testing/index.html

**Features:**
- ✅ Pre-built and ready to use
- ✅ No setup required
- ✅ WebSocket chat interface
- ✅ Direct connection to chatbot

**Just open the URL in your browser and start chatting!**

---

## 🚀 Full React Frontend

### **Start Development Server**

```bash
# Navigate to frontend directory
cd C:\Users\HP\Downloads\Order-v1-codebase-2\restaurant-chatbot\frontend

# Start Vite dev server (dependencies already installed)
npm run dev
```

**Access:** http://localhost:3000

### **Configuration**
- **Port:** 3000 (Vite dev server)
- **API Proxy:** Configured to proxy `/api` → `http://localhost:8000`
- **WebSocket Proxy:** Configured to proxy `/ws` → `ws://localhost:8000`

### **Tech Stack**
- React 18.2
- Vite 5.0
- Tailwind CSS 3.3
- Lucide React (icons)
- React Markdown

---

## 🛠️ Other Access Methods

### **1. Python WebSocket Client**

Use the provided script:

```bash
python chat_with_bot.py
```

Interactive CLI chat interface with the bot.

### **2. Direct WebSocket Connection**

```python
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8000/api/v1/chat/my-session-123"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "message": "Show me the menu",
            "timestamp": "2025-12-22T10:00:00"
        }))

        async for msg in ws:
            data = json.loads(msg)
            print(data)
            if data.get("type") == "RUN_FINISHED":
                break

asyncio.run(test())
```

### **3. API Documentation**

**Swagger UI:** http://localhost:8000/docs

Browse all available endpoints and test them interactively.

---

## 🌐 Available Endpoints

### **WebSocket Chat**
```
ws://localhost:8000/api/v1/chat/{session_id}
```

### **SSE Streaming**
```
POST http://localhost:8000/api/v1/chat/stream
Content-Type: application/json

{
  "message": "Your message here",
  "session_id": "your-session-id"
}
```

### **Health Check**
```
GET http://localhost:8000/api/v1/health
```

### **Root Info**
```
GET http://localhost:8000/
```

---

## 🧪 Testing the Chatbot

### **Sample Queries to Try:**

1. **Menu Exploration**
   - "Show me the menu"
   - "What burgers do you have?"
   - "Do you have vegetarian options?"

2. **Ordering**
   - "Add 2 chicken burgers to my cart"
   - "Show my cart"
   - "I want to order a pizza with extra cheese"

3. **Table Reservation**
   - "Book a table for 4 people tomorrow at 7 PM"
   - "Do you have tables available tonight?"

4. **Order Tracking**
   - "Track my order"
   - "What's the status of my last order?"

5. **Loyalty & Promotions**
   - "Do you have any offers?"
   - "Check my loyalty points"

6. **Restaurant Info**
   - "What are your operating hours?"
   - "What's your delivery policy?"

---

## 🔍 Monitoring & Debugging

### **View Real-time Logs**

```bash
docker compose -f docker-compose.root.yml logs chatbot-app -f
```

### **Check Service Status**

```bash
docker compose -f docker-compose.root.yml ps
```

### **View Database Menu Items**

```bash
docker exec a24-postgres psql -U postgres -d unified_restaurant_management_db -c "SELECT menu_item_name, menu_item_price FROM menu_item WHERE is_deleted = FALSE LIMIT 10;"
```

---

## 📊 Expected Behavior

### **First Message**
- Connection establishes in ~500ms
- AI responds within 8-10 seconds
- Streaming response appears word-by-word

### **Tool Calling**
- Watch logs for tool execution indicators
- Tools called automatically based on user intent
- Example: "Show menu" → `search_menu` tool called

### **Response Format**
- WebSocket events: `RUN_STARTED`, `ACTIVITY_START`, `TEXT_MESSAGE_CONTENT`, `RUN_FINISHED`
- Streaming text for smooth UX
- Quick reply suggestions after response

---

## ❌ Troubleshooting

### **Issue: Can't access http://localhost:8000/static/testing/index.html**

**Solution:**
1. Verify chatbot service is running:
   ```bash
   docker compose -f docker-compose.root.yml ps
   ```

2. Check logs for errors:
   ```bash
   docker compose -f docker-compose.root.yml logs chatbot-app --tail 50
   ```

### **Issue: React frontend won't start**

**Solution:**
```bash
cd restaurant-chatbot/frontend
npm install  # Reinstall dependencies
npm run dev
```

### **Issue: WebSocket connection fails**

**Solution:**
- Ensure session_id is included in URL
- Check that chatbot service is healthy
- Verify no firewall blocking port 8000

### **Issue: Generic AI responses (not using tools)**

**Solution:**
- Check logs for tool execution
- Verify max_tokens=2048 in crew_agent.py
- Try more specific queries (e.g., "Add chicken burger to cart" instead of "I want food")

---

## 📝 Quick Reference

| Access Method | URL/Command | Purpose |
|---------------|-------------|---------|
| **Testing Interface** | http://localhost:8000/static/testing/index.html | Quick chat test |
| **React Frontend** | http://localhost:3000 (after `npm run dev`) | Full featured UI |
| **API Docs** | http://localhost:8000/docs | Swagger documentation |
| **Health Check** | http://localhost:8000/api/v1/health | Service status |
| **Python Chat** | `python chat_with_bot.py` | CLI interface |
| **Logs** | `docker compose -f docker-compose.root.yml logs chatbot-app -f` | Monitor activity |

---

## 🎨 Customization

### **Modify React Frontend**

```bash
cd restaurant-chatbot/frontend/src
# Edit components in src/
# Changes auto-reload with Vite
```

### **Build for Production**

```bash
cd restaurant-chatbot/frontend
npm run build
# Output: dist/ directory
```

---

## ✅ System Requirements

- ✅ Docker services running (chatbot-app on port 8000)
- ✅ Node.js installed (for React frontend)
- ✅ Python 3.10+ (for Python client)
- ✅ Modern browser (Chrome, Firefox, Edge)

---

**Ready to chat!** 🤖

Start with: http://localhost:8000/static/testing/index.html
