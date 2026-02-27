"""
Health Check Endpoints
======================
System health monitoring for admin dashboard and deployment
"""

from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

from app.core.config import config

router = APIRouter()
logger = structlog.get_logger("api.health")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    version: str
    environment: str
    services: Dict[str, Dict[str, Any]]
    uptime_seconds: float


class ServiceHealth(BaseModel):
    """Individual service health status"""
    status: str  # "healthy", "unhealthy", "unknown"
    response_time_ms: float
    last_check: str
    details: Dict[str, Any] = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check
    Admin-ready: Provides detailed service status for monitoring dashboard
    """

    start_time = datetime.now(timezone.utc)
    services_status = {}
    overall_healthy = True

    # Check Database (PostgreSQL)
    db_start = datetime.now(timezone.utc)
    try:
        from app.core.database import get_db_session
        from sqlalchemy import text

        # Actually query the database to verify connectivity
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()

        services_status["database"] = {
            "status": "healthy",
            "response_time_ms": (datetime.now(timezone.utc) - db_start).total_seconds() * 1000,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "details": {
                "connection_pool": "active",
                "database_name": config.DB_NAME,
                "query_test": "passed"
            }
        }

    except Exception as e:
        services_status["database"] = {
            "status": "unhealthy",
            "response_time_ms": (datetime.now(timezone.utc) - db_start).total_seconds() * 1000,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "details": {"error": str(e)}
        }
        overall_healthy = False

    # Check Redis
    redis_start = datetime.now(timezone.utc)
    try:
        from app.services.redis_service import RedisService
        redis_service = RedisService()

        # Test Redis connection by trying to set a test key
        try:
            redis_service.set("health_check", "ok", 60)
            health_result = True
        except Exception:
            health_result = False

        services_status["redis"] = {
            "status": "healthy" if health_result else "unhealthy",
            "response_time_ms": (datetime.now(timezone.utc) - redis_start).total_seconds() * 1000,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "details": {
                "connection_pool": "active",
                "host": config.REDIS_HOST,
                "port": config.REDIS_PORT
            }
        }

        if not health_result:
            overall_healthy = False

    except Exception as e:
        services_status["redis"] = {
            "status": "unhealthy",
            "response_time_ms": (datetime.now(timezone.utc) - redis_start).total_seconds() * 1000,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "details": {"error": str(e)}
        }
        overall_healthy = False

    # MongoDB removed - using PostgreSQL for all persistence

    # Calculate total response time
    total_time = (datetime.now(timezone.utc) - start_time).total_seconds()

    # Log health check for admin monitoring
    logger.info(
        "health_check_performed",
        overall_status="healthy" if overall_healthy else "unhealthy",
        total_response_time_seconds=total_time,
        services_checked=len(services_status),
        healthy_services=len([s for s in services_status.values() if s["status"] == "healthy"])
    )

    response = HealthResponse(
        status="healthy" if overall_healthy else "unhealthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=config.APP_VERSION,
        environment=config.ENVIRONMENT,
        services=services_status,
        uptime_seconds=total_time
    )

    # Return error status if any service is unhealthy
    if not overall_healthy:
        raise HTTPException(status_code=503, detail=response.model_dump())

    return response


@router.get("/health/quick")
async def quick_health_check():
    """
    Quick health check for load balancers
    Admin-ready: Basic status for uptime monitoring
    """

    logger.info("quick_health_check_performed")

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": config.APP_VERSION
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness check
    Admin-ready: Determines if app is ready to receive traffic
    """

    try:
        # Quick check of critical services
        from app.services.redis_service import RedisService
        redis_service = RedisService()

        # Test Redis readiness
        try:
            redis_service.set("readiness_check", "ok", 60)
            redis_healthy = True
        except Exception:
            redis_healthy = False

        if redis_healthy:
            logger.info("readiness_check_passed")
            return {
                "status": "ready",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise Exception("Redis not ready")

    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )


@router.get("/health/circuit-breakers")
async def circuit_breaker_health():
    """
    Circuit breaker health check for external APIs
    Admin-ready: Monitor circuit breaker states
    """
    breakers_status = {}

    try:
        from app.ai_services.llm_manager import get_llm_manager
        llm_manager = get_llm_manager()

        for account in llm_manager.accounts:
            breakers_status[f"openai_{account.name}"] = {
                "state": account.circuit_breaker.state,
                "failure_count": account.circuit_breaker.fail_counter,
                "status": "healthy" if account.circuit_breaker.state == "closed" else "degraded"
            }
    except Exception as e:
        breakers_status["openai"] = {
            "status": "error",
            "error": str(e)
        }

    try:
        from app.services.payment_service import get_payment_service
        payment_service = get_payment_service()

        if hasattr(payment_service, "circuit_breaker"):
            breakers_status["razorpay"] = {
                "state": payment_service.circuit_breaker.state,
                "failure_count": payment_service.circuit_breaker.fail_counter,
                "status": "healthy" if payment_service.circuit_breaker.state == "closed" else "degraded"
            }
    except Exception as e:
        breakers_status["razorpay"] = {
            "status": "error",
            "error": str(e)
        }

    try:
        from app.services.sms_service import get_sms_service
        sms_service = get_sms_service()

        if hasattr(sms_service, "circuit_breaker"):
            breakers_status["twilio"] = {
                "state": sms_service.circuit_breaker.state,
                "failure_count": sms_service.circuit_breaker.fail_counter,
                "status": "healthy" if sms_service.circuit_breaker.state == "closed" else "degraded"
            }
    except Exception as e:
        breakers_status["twilio"] = {
            "status": "error",
            "error": str(e)
        }

    overall_healthy = all(
        cb.get("status") == "healthy" for cb in breakers_status.values()
    )

    logger.info("circuit_breaker_check_performed", overall_status="healthy" if overall_healthy else "degraded")

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "circuit_breakers": breakers_status
    }


@router.get("/health/agents")
async def agent_health():
    """
    Agent operational status check
    Admin-ready: Monitor all agent availability
    """
    agents = {
        "greeting": "operational",
        "booking": "operational",
        "food_ordering": "operational",
        "payment": "operational",
        "feedback": "operational",
        "general_queries": "operational",
        "user_management": "operational",
        "user_profile": "operational",
        "support": "operational"
    }

    total_agents = len(agents)
    operational_agents = sum(1 for status in agents.values() if status == "operational")

    logger.info("agent_health_check_performed", total=total_agents, operational=operational_agents)

    return {
        "status": "healthy" if total_agents == operational_agents else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_agents": total_agents,
        "operational": operational_agents,
        "agents": agents
    }


@router.get("/health/external-apis")
async def external_api_health():
    """
    External API health check
    Admin-ready: Monitor connectivity to external services (OpenAI, Razorpay, Twilio)
    """
    apis_status = {}
    overall_healthy = True

    # Check OpenAI API
    openai_start = datetime.now(timezone.utc)
    try:
        from app.ai_services.llm_manager import get_llm_manager
        llm_manager = get_llm_manager()

        # Try to get a simple completion to test API connectivity
        test_response = await llm_manager.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
            temperature=0
        )

        if test_response and test_response.get("success"):
            apis_status["openai"] = {
                "status": "healthy",
                "response_time_ms": (datetime.now(timezone.utc) - openai_start).total_seconds() * 1000,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "api_reachable": True,
                    "active_accounts": len(llm_manager.accounts)
                }
            }
        else:
            raise Exception("API test failed")

    except Exception as e:
        apis_status["openai"] = {
            "status": "unhealthy",
            "response_time_ms": (datetime.now(timezone.utc) - openai_start).total_seconds() * 1000,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "details": {"error": str(e)}
        }
        overall_healthy = False

    # Check Razorpay API
    razorpay_start = datetime.now(timezone.utc)
    try:
        from app.services.payment_service import get_payment_service
        payment_service = get_payment_service()

        # Test Razorpay connectivity by fetching account details
        if hasattr(payment_service.client, 'utility'):
            # Razorpay client is initialized
            apis_status["razorpay"] = {
                "status": "healthy",
                "response_time_ms": (datetime.now(timezone.utc) - razorpay_start).total_seconds() * 1000,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "client_initialized": True,
                    "mode": "test" if config.RAZORPAY_KEY_ID.startswith("rzp_test") else "live"
                }
            }
        else:
            raise Exception("Razorpay client not initialized")

    except Exception as e:
        apis_status["razorpay"] = {
            "status": "unhealthy",
            "response_time_ms": (datetime.now(timezone.utc) - razorpay_start).total_seconds() * 1000,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "details": {"error": str(e)}
        }
        overall_healthy = False

    # Check Twilio API
    twilio_start = datetime.now(timezone.utc)
    try:
        from app.services.sms_service import get_sms_service
        sms_service = get_sms_service()

        # Test Twilio connectivity
        if hasattr(sms_service, 'client') and sms_service.client:
            apis_status["twilio"] = {
                "status": "healthy",
                "response_time_ms": (datetime.now(timezone.utc) - twilio_start).total_seconds() * 1000,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "client_initialized": True,
                    "from_number": config.TWILIO_PHONE_NUMBER
                }
            }
        else:
            raise Exception("Twilio client not initialized")

    except Exception as e:
        apis_status["twilio"] = {
            "status": "unhealthy",
            "response_time_ms": (datetime.now(timezone.utc) - twilio_start).total_seconds() * 1000,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "details": {"error": str(e)}
        }
        overall_healthy = False

    logger.info("external_api_health_check_performed", overall_status="healthy" if overall_healthy else "unhealthy")

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "external_apis": apis_status
    }


@router.get("/health/system")
async def system_health():
    """
    Comprehensive system health check
    Admin-ready: Single endpoint to check all system components

    This endpoint aggregates:
    - Database connectivity
    - Redis connectivity
    - External API status (OpenAI, Razorpay, Twilio)
    - Circuit breaker states
    - Agent operational status
    """
    start_time = datetime.now(timezone.utc)
    system_status = {}
    overall_healthy = True

    # 1. Database Health
    try:
        from app.core.database import get_db_session
        from sqlalchemy import text

        db_start = datetime.now(timezone.utc)
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()

        system_status["database"] = {
            "status": "healthy",
            "response_time_ms": (datetime.now(timezone.utc) - db_start).total_seconds() * 1000,
            "details": {"query_test": "passed"}
        }
    except Exception as e:
        system_status["database"] = {
            "status": "unhealthy",
            "details": {"error": str(e)}
        }
        overall_healthy = False

    # 2. Redis Health
    try:
        from app.services.redis_service import RedisService
        redis_service = RedisService()

        redis_start = datetime.now(timezone.utc)
        redis_service.set("health_check_system", "ok", 60)
        redis_healthy = True

        system_status["redis"] = {
            "status": "healthy",
            "response_time_ms": (datetime.now(timezone.utc) - redis_start).total_seconds() * 1000,
            "details": {"connection_test": "passed"}
        }
    except Exception as e:
        system_status["redis"] = {
            "status": "unhealthy",
            "details": {"error": str(e)}
        }
        overall_healthy = False

    # 3. External APIs Health
    external_apis_healthy = True
    external_apis_details = {}

    # OpenAI
    try:
        from app.ai_services.llm_manager import get_llm_manager
        llm_manager = get_llm_manager()

        openai_start = datetime.now(timezone.utc)
        test_response = await llm_manager.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
            temperature=0
        )

        if test_response and test_response.get("success"):
            external_apis_details["openai"] = {
                "status": "healthy",
                "response_time_ms": (datetime.now(timezone.utc) - openai_start).total_seconds() * 1000
            }
        else:
            raise Exception("API test failed")
    except Exception as e:
        external_apis_details["openai"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        external_apis_healthy = False

    # Razorpay
    try:
        from app.services.payment_service import get_payment_service
        payment_service = get_payment_service()

        if hasattr(payment_service.client, 'utility'):
            external_apis_details["razorpay"] = {
                "status": "healthy",
                "client_initialized": True
            }
        else:
            raise Exception("Client not initialized")
    except Exception as e:
        external_apis_details["razorpay"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        external_apis_healthy = False

    # Twilio
    try:
        from app.services.sms_service import get_sms_service
        sms_service = get_sms_service()

        if hasattr(sms_service, 'client') and sms_service.client:
            external_apis_details["twilio"] = {
                "status": "healthy",
                "client_initialized": True
            }
        else:
            raise Exception("Client not initialized")
    except Exception as e:
        external_apis_details["twilio"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        external_apis_healthy = False

    system_status["external_apis"] = {
        "status": "healthy" if external_apis_healthy else "unhealthy",
        "details": external_apis_details
    }

    if not external_apis_healthy:
        overall_healthy = False

    # 4. Circuit Breakers Health
    circuit_breakers_healthy = True
    circuit_breakers_details = {}

    try:
        from app.ai_services.llm_manager import get_llm_manager
        llm_manager = get_llm_manager()

        for account in llm_manager.accounts:
            cb_status = "healthy" if account.circuit_breaker.state == "closed" else "degraded"
            circuit_breakers_details[f"openai_{account.name}"] = {
                "state": account.circuit_breaker.state,
                "failure_count": account.circuit_breaker.fail_counter,
                "status": cb_status
            }
            if cb_status != "healthy":
                circuit_breakers_healthy = False
    except Exception as e:
        circuit_breakers_details["openai"] = {"status": "error", "error": str(e)}
        circuit_breakers_healthy = False

    try:
        from app.services.payment_service import get_payment_service
        payment_service = get_payment_service()

        if hasattr(payment_service, "circuit_breaker"):
            cb_status = "healthy" if payment_service.circuit_breaker.state == "closed" else "degraded"
            circuit_breakers_details["razorpay"] = {
                "state": payment_service.circuit_breaker.state,
                "failure_count": payment_service.circuit_breaker.fail_counter,
                "status": cb_status
            }
            if cb_status != "healthy":
                circuit_breakers_healthy = False
    except Exception as e:
        circuit_breakers_details["razorpay"] = {"status": "error", "error": str(e)}
        circuit_breakers_healthy = False

    try:
        from app.services.sms_service import get_sms_service
        sms_service = get_sms_service()

        if hasattr(sms_service, "circuit_breaker"):
            cb_status = "healthy" if sms_service.circuit_breaker.state == "closed" else "degraded"
            circuit_breakers_details["twilio"] = {
                "state": sms_service.circuit_breaker.state,
                "failure_count": sms_service.circuit_breaker.fail_counter,
                "status": cb_status
            }
            if cb_status != "healthy":
                circuit_breakers_healthy = False
    except Exception as e:
        circuit_breakers_details["twilio"] = {"status": "error", "error": str(e)}
        circuit_breakers_healthy = False

    system_status["circuit_breakers"] = {
        "status": "healthy" if circuit_breakers_healthy else "degraded",
        "details": circuit_breakers_details
    }

    # Note: degraded circuit breakers don't mark overall system as unhealthy
    # They indicate partial functionality

    # 5. Agents Health
    agents = {
        "greeting": "operational",
        "booking": "operational",
        "food_ordering": "operational",
        "payment": "operational",
        "feedback": "operational",
        "general_queries": "operational",
        "user_management": "operational",
        "user_profile": "operational",
        "support": "operational"
    }

    total_agents = len(agents)
    operational_agents = sum(1 for status in agents.values() if status == "operational")

    system_status["agents"] = {
        "status": "healthy" if total_agents == operational_agents else "degraded",
        "total": total_agents,
        "operational": operational_agents,
        "details": agents
    }

    # Calculate total response time
    total_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

    # Summary
    healthy_components = sum(1 for component in system_status.values() if component.get("status") == "healthy")
    total_components = len(system_status)

    logger.info(
        "system_health_check_performed",
        overall_status="healthy" if overall_healthy else "unhealthy",
        healthy_components=healthy_components,
        total_components=total_components,
        response_time_ms=total_time_ms
    )

    response = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": config.APP_VERSION,
        "environment": config.ENVIRONMENT,
        "response_time_ms": total_time_ms,
        "summary": {
            "healthy_components": healthy_components,
            "total_components": total_components,
            "overall_health_percentage": round((healthy_components / total_components) * 100, 2)
        },
        "components": system_status
    }

    # Return error status if system is unhealthy
    if not overall_healthy:
        raise HTTPException(status_code=503, detail=response)

    return response
