# Restaurant AI Assistant - System Architecture

## Visual Architecture

![Restaurant AI Architecture](./architecture.svg)

*Click image to view full size. For detailed component descriptions, see sections below.*

### Detailed Architecture Diagrams

| Diagram | Description | Link |
|---------|-------------|------|
| **Request Flow** | End-to-end message journey through all layers | [View](./diagrams/01-request-flow.svg) |
| **Agent Architecture** | CrewAI multi-agent system & tool layer | [View](./diagrams/02-agent-architecture.svg) |
| **Database Schema** | PostgreSQL, Redis, MongoDB schemas | [View](./diagrams/03-database-schema.svg) |
| **Authentication Flow** | OTP-based phone verification flow | [View](./diagrams/04-auth-flow.svg) |
| **Deployment Architecture** | AWS EC2 + Docker Compose setup | [View](./diagrams/05-deployment.svg) |

*All diagrams are SVG (vector) format - click to view full size, zoom infinitely.*

---

## Performance Summary (December 2025)

| Metric | Result | Status |
|--------|--------|--------|
| **API Throughput** | 484 req/sec | EXCELLENT |
| **Max Concurrent Users** | 500+ tested | NO ERRORS |
| **LLM Concurrent Calls** | 50 tested | 0% ERROR RATE |
| **Average Response** | 0.5-2.0s | GOOD |

*Full load test report: [LOAD_TEST_REPORT.md](./LOAD_TEST_REPORT.md)*

---

## Quick Start - One Command Deployment

```bash
# 1. Clone and enter directory
git clone <repository-url>
cd codebase

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Deploy everything with ONE command
docker compose up -d --build

# That's it! Access at:
# - Frontend: http://localhost
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Helper Scripts
```bash
# Linux/Mac
./deploy.sh          # Deploy all services
./deploy.sh down     # Stop all services
./deploy.sh logs     # View logs

# Windows
deploy.bat           # Deploy all services
deploy.bat down      # Stop all services
deploy.bat logs      # View logs
```

---

## High-Level Architecture

```mermaid
graph TB
    subgraph Client_Layer["Client Layer"]
        WEB[React Web App<br/>Port 3000]
        MOBILE[Mobile Browser]
    end

    subgraph Reverse_Proxy["Reverse Proxy"]
        NGINX[NGINX<br/>Port 80<br/>Load Balancer]
    end

    subgraph Application_Layer["Application Layer"]
        FASTAPI[FastAPI Backend<br/>Port 8000]
        WS[WebSocket Handler]
        REST[REST API]
        STREAM[SSE Stream]
    end

    subgraph AI_Processing["AI Processing Layer"]
        CREW[Restaurant Crew<br/>CrewAI Orchestrator]
        TOOLS[Sync Tools]
        LLM_POOL[LLM Account Pool<br/>20 OpenAI Accounts]
    end

    subgraph Data_Layer["Data Layer"]
        PG[(PostgreSQL<br/>Port 5432)]
        REDIS[(Redis<br/>Port 6379)]
        MONGO[(MongoDB<br/>Port 27017)]
    end

    WEB --> NGINX
    MOBILE --> NGINX
    NGINX --> FASTAPI
    FASTAPI --> WS
    FASTAPI --> REST
    FASTAPI --> STREAM
    WS --> CREW
    CREW --> TOOLS
    CREW --> LLM_POOL
    TOOLS --> PG
    TOOLS --> REDIS
    FASTAPI --> MONGO
```

## Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant N as NGINX
    participant WS as WebSocket
    participant AUTH as Auth Service
    participant CREW as CrewAI Agent
    participant LLM as OpenAI
    participant DB as PostgreSQL

    C->>N: Connect WebSocket
    N->>WS: Proxy to /api/v1/chat/{session_id}
    
    C->>WS: Send Message
    WS->>AUTH: Check Session Auth
    
    alt Not Authenticated
        AUTH->>C: AUTH_REQUIRED Event
        C->>WS: Phone Number
        WS->>AUTH: Send OTP
        C->>WS: OTP Code
        AUTH->>DB: Create/Get User
    end
    
    WS->>CREW: Process Message
    CREW->>LLM: Intent Classification (gpt-4o)
    CREW->>DB: Execute Tools (Menu/Cart)
    CREW->>LLM: Generate Response (gpt-4o-mini)
    CREW-->>WS: Response + AG-UI Events
    WS-->>C: Stream Events
```

## AG-UI Event Flow

```mermaid
flowchart LR
    RUN_START[RUN_STARTED] --> ACTIVITY[ACTIVITY_START]
    ACTIVITY --> TOOL[TOOL_CALL Events]
    TOOL --> CARD[CARD_DATA]
    CARD --> ACTIVITY_END[ACTIVITY_END]
    ACTIVITY_END --> TEXT[TEXT_MESSAGE Events]
    TEXT --> RUN_END[RUN_FINISHED]
```

### Card Types
- **MENU_CARD**: Display menu items with images, prices
- **CART_CARD**: Shopping cart with items, quantities, totals
- **ORDER_DATA**: Order confirmation with order number
- **AUTH_REQUIRED**: Phone/OTP authentication form

## Database Schema

```mermaid
erDiagram
    USERS ||--o{ ORDERS : places
    USERS ||--o{ CARTS : has
    ORDERS ||--|{ ORDER_ITEMS : contains
    MENU_ITEMS ||--o{ ORDER_ITEMS : referenced
    MENU_ITEMS }|--|| CATEGORIES : belongs_to
    CARTS ||--|{ CART_ITEMS : contains

    USERS {
        uuid id PK
        string phone_number UK
        string name
        boolean is_authenticated
    }

    MENU_ITEMS {
        uuid id PK
        string name
        decimal price
        uuid category_id FK
        boolean available
    }

    CARTS {
        uuid id PK
        string session_id UK
        uuid user_id FK
    }

    ORDERS {
        uuid id PK
        string order_number UK
        uuid user_id FK
        string order_type
        string status
        decimal total_amount
    }
```

## Session Context Architecture

```mermaid
flowchart TB
    subgraph Session_Flow["Session Lifecycle"]
        NEW[New Session] --> AUTH[Auth Required]
        AUTH --> AUTHED[Authenticated]
        AUTHED --> ACTIVE[Active]
        ACTIVE --> EXPIRED[Expired 30min]
    end

    subgraph Context_Flow["Context Propagation"]
        CHAT[chat.py] -->|extract user_id| PROC[process_with_agui_streaming]
        PROC -->|set_session_context| POOL[crew_pool.py]
        POOL -->|get_current_user_id| TOOLS[Tools]
    end
```

## CrewAI Tool Architecture

**IMPORTANT**: CrewAI does not properly await async tools even with .
All tools MUST be SYNC functions that internally call async code via .

```mermaid
flowchart LR
    subgraph Sync_Tools["SYNC Tool Wrappers"]
        SEARCH[search_menu_tool]
        ADD[add_to_cart_tool]
        VIEW[view_cart_tool]
        CHECKOUT[checkout_tool]
    end

    subgraph Async_Impl["Async Implementation"]
        A_SEARCH[search_menu_impl_async]
        A_ADD[add_to_cart_impl_async]
        A_VIEW[view_cart_impl_async]
        A_CHECKOUT[create_order_async]
    end

    SEARCH -->|asyncio.run| A_SEARCH
    ADD -->|asyncio.run| A_ADD
    VIEW -->|asyncio.run| A_VIEW
    CHECKOUT -->|asyncio.run| A_CHECKOUT
```

## Docker Architecture

```mermaid
graph TB
    subgraph Docker_Network["restaurant-network"]
        NGINX_C[nginx container<br/>Port 80]
        APP_C[app container<br/>Port 8000]
        PG_C[postgres container<br/>Port 5432]
        REDIS_C[redis container<br/>Port 6379]
        MONGO_C[mongodb container<br/>Port 27017]
    end

    EXTERNAL[External Traffic] --> NGINX_C
    NGINX_C --> APP_C
    APP_C --> PG_C
    APP_C --> REDIS_C
    APP_C --> MONGO_C
```

## LLM Load Balancing

```mermaid
flowchart TB
    REQ[Request] --> ROUTER[Round Robin Router]
    ROUTER --> CHECK{Usage < 80%?}
    CHECK -->|Yes| ACCOUNT[Use Account N]
    CHECK -->|No| COOLDOWN[60s Cooldown]
    COOLDOWN --> ROUTER
    ACCOUNT --> GPT4O[gpt-4o Intent]
    ACCOUNT --> GPT4OMINI[gpt-4o-mini Agent]
```

## File Structure

```
codebase/
├── app/
│   ├── api/routes/
│   │   ├── chat.py              # WebSocket handler
│   │   ├── stream.py            # SSE streaming
│   │   ├── menu.py              # Menu REST API
│   │   └── orders.py            # Orders REST API
│   ├── core/
│   │   ├── agui_events.py       # AG-UI event system
│   │   ├── config.py            # Configuration
│   │   └── database.py          # DB connections
│   ├── features/food_ordering/
│   │   ├── crew_agent.py        # CrewAI agent + tools
│   │   └── services/            # Business logic
│   ├── orchestration/
│   │   └── restaurant_crew.py   # Main orchestrator
│   └── services/
│       ├── crew_pool.py         # CrewAI pool + context
│       └── identity_service.py  # Auth service
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── hooks/useWebSocket.js
│   │   └── pages/
│   └── package.json
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile               # Backend
│   └── Dockerfile.nginx         # Frontend + proxy
├── db/
│   ├── init.sql
│   ├── 01-schema.sql
│   └── 02-data.sql
├── docs/
│   ├── ARCHITECTURE.md           # This file
│   ├── architecture.svg          # Visual system diagram
│   ├── LOAD_TEST_REPORT.md       # Performance testing results
│   └── EC2_DEPLOY.md             # AWS deployment guide
├── load_test.py                  # Basic load test
├── load_test_full.py             # Multi-endpoint load test
├── load_test_api.py              # API discovery + testing
└── load_test_extreme.py          # Stress testing script
```

## Key Technical Decisions

1. **Sync Tools for CrewAI**: CrewAI cannot properly handle async tools. All tools are sync wrappers around async implementations.

2. **Session Context via ContextVar**: User ID and session ID are propagated through ContextVar for thread-safe access in tools.

3. **AG-UI Protocol**: Real-time streaming events for typing indicators, tool progress, and card data.

4. **20-Account LLM Pool**: Round-robin load balancing across multiple OpenAI accounts for high throughput.

5. **Docker Compose Orchestration**: All services in single network with health checks and proper startup order.
