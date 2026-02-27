"""
A24 Restaurant Data Pipeline - Main Application
FastAPI application for PetPooja integration
"""

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import sys
from datetime import datetime
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.db_session_async import init_db_async, warm_connection_pool, close_db, get_db
from app.petpooja_client.order_client_async import close_async_order_client
from app.routers import menu_router, order_router, webhook_router, restaurant_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI application"""
    import time
    start_time = time.time()

    # Startup
    logger.info("=" * 70)
    logger.info("A24 Restaurant Data Pipeline - Starting")
    logger.info("=" * 70)
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")

    try:
        # Use async initialization to avoid blocking the event loop
        await init_db_async()
        logger.info("Async database initialized successfully")

        # Warm up connection pool for faster first requests
        await warm_connection_pool()
        logger.info("Async connection pool warmed up")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    if not settings.petpooja_credentials_configured:
        logger.warning("PetPooja credentials not configured")
    else:
        logger.info("PetPooja credentials configured")

    startup_time = time.time() - start_time
    logger.info(f"Startup complete in {startup_time:.2f}s!")
    logger.info("=" * 70)

    yield

    # Shutdown - Close async resources
    logger.info("A24 Restaurant Data Pipeline - Shutting Down")
    try:
        await close_async_order_client()
        await close_db()
        logger.info("Async resources closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="API for PetPooja integration and restaurant management",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
allowed_origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"]

if "*" in allowed_origins and not settings.DEBUG:
    logger.warning("CORS is set to allow ALL origins in production!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check Endpoints
@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["General"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Simple async health check
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_healthy = True
        overall_status = "healthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "type": "async_postgresql"
                },
                "petpooja": {
                    "status": "configured" if settings.petpooja_credentials_configured else "not_configured"
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


# Include API Routers
app.include_router(restaurant_router)
app.include_router(menu_router)
app.include_router(order_router)
app.include_router(webhook_router)


# Exception Handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Main Entry Point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
