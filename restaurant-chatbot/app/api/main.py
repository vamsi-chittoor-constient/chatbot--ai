"""
FastAPI Main Application
========================
Entry point for pure agentic AI restaurant assistant
"""

# Load environment variables FIRST
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Load .env file before importing config
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import config
from app.api.middleware.logging import setup_logging
from app.api.routes import health, config as config_routes, chat, payment, llm_manager, stream, voice

# Setup structured logging
setup_logging()

# Configure logging
import logging

# Configure watchfiles logging to reduce verbosity (file change detection)
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("watchfiles.main").setLevel(logging.WARNING)

# Configure uvicorn logging to reduce reload verbosity
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)

# Configure OpenAI client to be less verbose
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Configure MongoDB to be less verbose (disable command monitoring)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("pymongo.command").setLevel(logging.WARNING)
logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
logging.getLogger("pymongo.serverSelection").setLevel(logging.WARNING)
logging.getLogger("pymongo.topology").setLevel(logging.WARNING)

# Import structlog after setup
try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(
        f"FastAPI startup - {config.APP_NAME} v{config.APP_VERSION} ({config.ENVIRONMENT}) debug={config.DEBUG}"
    )

    # Initialize services
    try:
        # Initialize database connections (using new core database manager)
        from app.core.database import db_manager
        db_manager.init_database()  # Synchronous initialization
        logger.info("Database connection initialized")

        # Verify database is ready with retry logic
        max_retries = 10
        for i in range(max_retries):
            if db_manager.is_initialized():
                # Double-check with actual query
                try:
                    from sqlalchemy import text
                    async with db_manager.get_session() as session:
                        await session.execute(text("SELECT 1"))
                    logger.info("Database connection verified and ready")
                    break
                except Exception as e:
                    if i == max_retries - 1:
                        logger.error(f"Database verification failed after {max_retries} retries: {str(e)}")
                        raise
                    logger.warning(f"Database not ready, retry {i+1}/{max_retries}", error=str(e))
                    import asyncio
                    await asyncio.sleep(1)
            else:
                if i == max_retries - 1:
                    raise Exception("Database not initialized after init_database() call")
                logger.warning(f"Database engine not ready, retry {i+1}/{max_retries}")
                import asyncio
                await asyncio.sleep(1)

        # Initialize centralized Redis connection pool (RedisManager)
        from app.core.redis import redis_manager
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_manager.init_redis(redis_url=redis_url, max_connections=50)
        logger.info("Centralized Redis connection pool initialized")

        # Initialize Redis service (now uses shared RedisManager pool)
        from app.services.redis_service import RedisService
        redis_service = RedisService()
        logger.info("Redis service initialized (using shared connection pool)")

        # Load restaurant config into Redis cache (for phone validation)
        from app.services.restaurant_cache_service import load_restaurant_config_to_redis
        restaurant_cache_success = await load_restaurant_config_to_redis()
        if restaurant_cache_success:
            logger.info("Restaurant configuration loaded into Redis cache (phone validation)")
        else:
            logger.warning("Failed to load restaurant config into Redis - phone validation may be slower")

        # Load all restaurant configs for multi-tenant API authentication
        from app.services.restaurant_cache_service import get_restaurant_config_cache
        restaurant_config_cache = get_restaurant_config_cache()
        config_load_result = await restaurant_config_cache.load_all_restaurants()
        if config_load_result["success"]:
            logger.info(
                "Restaurant configurations loaded for multi-tenant auth",
                total=config_load_result["total_restaurants"],
                loaded=config_load_result["loaded"]
            )
        else:
            logger.error("Failed to load restaurant configurations for multi-tenant auth")

        # Initialize inventory sync service and load inventory from DB to Redis
        from app.services.inventory_sync_service import get_inventory_sync_service
        inventory_sync = get_inventory_sync_service()
        await inventory_sync.sync_on_startup()
        inventory_sync.start_sync_timer()
        logger.info("Inventory sync service initialized with 5-minute periodic sync")

        # Initialize menu cache service and load full menu data to Redis
        try:
            from app.services.menu_cache_service import get_menu_cache_service
            menu_cache = get_menu_cache_service()
            await menu_cache.load_menu_from_db()
            logger.info("Menu cache loaded successfully from database")
        except Exception as e:
            logger.warning(f"Menu cache loading failed (will load on-demand): {str(e)}")

        # Run database migrations before loading menu preloader
        try:
            from app.core.migrations import run_migrations
            await run_migrations()
            logger.info("Database migrations completed")
        except Exception as e:
            logger.warning(f"Database migrations failed (continuing with existing schema): {str(e)}")

        # Auto-sync menu from PetPooja on first startup (if DB has no menu items)
        try:
            async with db_manager.get_session() as session:
                result = await session.execute(text(
                    "SELECT COUNT(*) FROM menu_item WHERE is_deleted = FALSE AND menu_item_status = 'active'"
                ))
                menu_count = result.scalar() or 0

            if menu_count == 0:
                logger.info("Empty menu detected - triggering PetPooja menu sync")
                import httpx
                petpooja_url = os.getenv("PETPOOJA_SERVICE_URL", "http://petpooja-app:8001")

                async with db_manager.get_session() as session:
                    result = await session.execute(text("""
                        SELECT DISTINCT ic.restaurant_id
                        FROM integration_config_table ic
                        JOIN integration_provider_table ip ON ic.provider_id = ip.provider_id
                        WHERE ip.provider_name ILIKE '%petpooja%'
                        AND ic.is_enabled = TRUE AND ic.is_deleted = FALSE
                    """))
                    restaurant_ids = [str(row[0]) for row in result.fetchall()]

                if restaurant_ids:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        for rid in restaurant_ids:
                            resp = await client.post(
                                f"{petpooja_url}/api/menu/fetch",
                                json={"restaurant_id": rid}
                            )
                            logger.info(f"PetPooja menu sync for {rid}: status={resp.status_code}")
                else:
                    logger.warning("No PetPooja integrations found in DB - menu will remain empty until sync")
            else:
                logger.info(f"Menu has {menu_count} active items - skipping PetPooja sync")
        except Exception as e:
            logger.warning(f"Auto menu sync check failed (continuing with existing data): {e}")

        # Initialize in-memory menu preloader for instant tool responses
        try:
            from app.core.preloader import preload_all
            await preload_all()
            logger.info("Menu preloader initialized - tools will have instant menu access")
        except Exception as e:
            logger.warning(f"Menu preloader failed (tools will fallback to DB): {str(e)}")

        # Pre-warm LLM connections for instant first message response
        # This eliminates the ~2-3 second delay on first user message
        try:
            from app.services.crew_pool import prewarm_llm
            await prewarm_llm()
            logger.info("LLM connections pre-warmed across all accounts")
        except Exception as e:
            logger.warning(f"LLM pre-warming failed (will warm on first request): {str(e)}")

        # ============ TESTING MODULE INITIALIZATION ============
        # WARNING: This section can be removed when manual testing is complete
        # Initialize MongoDB for testing data storage
        try:
            from app.database.mongodb import get_mongodb_testing_manager
            mongo_testing = get_mongodb_testing_manager()
            await mongo_testing.connect()
            logger.info("MongoDB testing connection initialized")
        except Exception as e:
            logger.warning(f"MongoDB testing connection failed (skipping): {str(e)}")
        # ============ END TESTING MODULE ============

        # Start background cleanup task for inactive sessions
        import asyncio
        from app.api.routes.chat import websocket_manager

        async def cleanup_task():
            """Background task to cleanup inactive sessions every 5 minutes"""
            while True:
                try:
                    await asyncio.sleep(300)  # Every 5 minutes
                    result = await websocket_manager.cleanup_inactive_sessions(inactive_timeout_minutes=15)
                    if result["sessions_cleaned"] > 0:
                        logger.info(
                            f"Cleaned up {result['sessions_cleaned']} inactive sessions: {result['removed_sessions']}"
                        )
                except Exception as e:
                    logger.error(f"Session cleanup task error: {str(e)}")

        # Start cleanup task in background
        cleanup_task_handle = asyncio.create_task(cleanup_task())
        logger.info("Session cleanup background task started (runs every 5 minutes)")

        # Print all routes for debugging
        logger.info("Registered Routes:")
        for route in app.routes:
            methods = getattr(route, 'methods', ['WebSocket']) if hasattr(route, 'methods') else ['WebSocket']
            logger.info(f"Route: {route.path} [{','.join(methods)}]")
        
        logger.info("FastAPI startup complete - All services initialized successfully")

    except Exception as e:
        logger.error(f"FastAPI startup failed: {str(e)}")
        # Don't raise - allow app to start even if some services fail
        cleanup_task_handle = None  # Set to None if startup failed
        
        # Still print routes even if startup failed
        logger.info("Registered Routes (startup failed):")
        for route in app.routes:
            methods = getattr(route, 'methods', ['WebSocket']) if hasattr(route, 'methods') else ['WebSocket']
            logger.info(f"Route: {route.path} [{','.join(methods)}]")

    yield

    # Shutdown
    logger.info("FastAPI shutdown initiated")

    # Stop menu preloader background refresh
    try:
        from app.core.preloader import cleanup_preloaders
        await cleanup_preloaders()
        logger.info("Menu preloader stopped")
    except Exception:
        pass

    # Stop inventory sync timer
    try:
        from app.services.inventory_sync_service import get_inventory_sync_service
        inventory_sync = get_inventory_sync_service()
        inventory_sync.stop_sync_timer()
        logger.info("Inventory sync timer stopped")
    except Exception:
        pass

    # Cancel background tasks
    try:
        if 'cleanup_task_handle' in locals() and cleanup_task_handle is not None:
            cleanup_task_handle.cancel()
            logger.info("Background cleanup task cancelled")
    except Exception:
        pass

    # ============ TESTING MODULE SHUTDOWN ============
    # WARNING: This section can be removed when manual testing is complete
    # Close MongoDB testing connection
    try:
        from app.database.mongodb import get_mongodb_testing_manager
        mongo_testing = get_mongodb_testing_manager()
        await mongo_testing.disconnect()
        logger.info("MongoDB testing connection closed")
    except Exception:
        pass
    # ============ END TESTING MODULE ============

    logger.info("FastAPI shutdown complete")


# Create FastAPI application with lifespan
app = FastAPI(
    title="Restaurant AI Assistant API",
    description="Pure agentic AI-powered restaurant assistant",
    version="1.0.0",
    docs_url="/docs" if config.DEBUG else None,  # Only show docs in debug mode
    redoc_url="/redoc" if config.DEBUG else None,
    lifespan=lifespan
)

# CORS Configuration for iframe embedding
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
allowed_methods = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
allowed_headers = os.getenv("ALLOWED_HEADERS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=allowed_methods,
    allow_headers=allowed_headers,
    expose_headers=["*"],
)

# Database readiness middleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class DatabaseReadinessMiddleware(BaseHTTPMiddleware):
    """Middleware to check database readiness before processing requests"""

    async def dispatch(self, request: Request, call_next):
        # Skip health check endpoint
        if request.url.path in ["/", "/api/v1/health", "/api/v1/health/"]:
            return await call_next(request)

        # Check database readiness
        from app.core.database import db_manager

        if not db_manager.is_initialized():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service temporarily unavailable",
                    "message": "Database is initializing, please retry in a moment"
                }
            )

        return await call_next(request)

app.add_middleware(DatabaseReadinessMiddleware)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(config_routes.router, prefix="/api/v1", tags=["config"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(payment.router, prefix="/api/v1", tags=["payment"])
# Debug router removed
app.include_router(llm_manager.router, prefix="/api/v1", tags=["llm-manager"])  # LLM Manager monitoring
app.include_router(stream.router, prefix="/api/v1", tags=["ag-ui-streaming"])  # AG-UI SSE streaming
app.include_router(voice.router, prefix="/api/v1", tags=["voice"])  # Voice chat WebSocket

# ============ TESTING MODULE ROUTES ============
from app.api.routes import testing
app.include_router(testing.router, prefix="/api/v1", tags=["testing"])
# ============ END TESTING MODULE ============

# Mount static files for frontend assets
app.mount("/assets", StaticFiles(directory="static/testing/assets"), name="assets")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint - Serve frontend
@app.get("/")
async def root():
    """Serve the chatbot frontend interface at root URL"""
    return FileResponse("static/testing/index.html")

# Print all routes on startup for debugging (moved to lifespan)
# This function is now called within the lifespan context manager

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting uvicorn server on {config.API_HOST}:{config.API_PORT} (debug={config.DEBUG})")

    uvicorn.run(
        "app.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
        log_level="info" if not config.DEBUG else "debug",
        # Reduce reload verbosity by only watching specific patterns
        reload_includes=["*.py"] if config.DEBUG else None,
        reload_excludes=["__pycache__/*", "*.pyc", "*.pyo", ".git/*", ".venv/*"] if config.DEBUG else None,
        # Use access log only in production
        access_log=not config.DEBUG
    )

