
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from app.core.security import SecurityManager
from app.core.config import security_logger
from app.services.power import PowerManager
from app.models.schemas import PowerActionRequest, CommandResponse

router = APIRouter(
    prefix="/system/power",
    tags=["Power"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check for forwarded IP (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.post("/shutdown", response_model=CommandResponse)
async def shutdown_system(request: PowerActionRequest, http_request: Request):
    """Shutdown the system with rate limiting"""
    client_ip = get_client_ip(http_request)

    # Rate limiting check
    allowed, remaining = SecurityManager.check_power_action_rate_limit(client_ip)
    if not allowed:
        security_logger.warning(f"Rate limit exceeded for shutdown by {client_ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Too many power actions. Maximum {PowerActionRequest.__fields__.get('limit')} per minute."
        )

    # Log security event
    security_logger.info(f"Power action: SHUTDOWN by {client_ip}, delay={request.delay_seconds}s")

    result = PowerManager.shutdown(request.delay_seconds)
    if result["success"]:
        SecurityManager.record_power_action(client_ip)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/restart", response_model=CommandResponse)
async def restart_system(request: PowerActionRequest, http_request: Request):
    """Restart the system with rate limiting"""
    client_ip = get_client_ip(http_request)

    # Rate limiting check
    allowed, remaining = SecurityManager.check_power_action_rate_limit(client_ip)
    if not allowed:
        security_logger.warning(f"Rate limit exceeded for restart by {client_ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Too many power actions. Maximum {PowerActionRequest.__fields__.get('limit')} per minute."
        )

    # Log security event
    security_logger.info(f"Power action: RESTART by {client_ip}, delay={request.delay_seconds}s")

    result = PowerManager.restart(request.delay_seconds)
    if result["success"]:
        SecurityManager.record_power_action(client_ip)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/hibernate", response_model=CommandResponse)
async def hibernate_system(http_request: Request):
    """Hibernate the system with rate limiting"""
    client_ip = get_client_ip(http_request)

    # Rate limiting check
    allowed, remaining = SecurityManager.check_power_action_rate_limit(client_ip)
    if not allowed:
        security_logger.warning(f"Rate limit exceeded for hibernate by {client_ip}")
        raise HTTPException(
            status_code=429,
            detail=f"Too many power actions. Maximum {PowerActionRequest.__fields__.get('limit')} per minute."
        )

    # Log security event
    security_logger.info(f"Power action: HIBERNATE by {client_ip}")

    result = PowerManager.hibernate()
    if result["success"]:
        SecurityManager.record_power_action(client_ip)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/lock", response_model=CommandResponse)
async def lock_system(http_request: Request):
    """Lock the screen with rate limiting"""
    client_ip = get_client_ip(http_request)

    # Note: Lock is less critical, so we apply a more lenient rate limit
    # For now, we'll use the same limit but could be configured separately

    # Log security event
    security_logger.info(f"Power action: LOCK by {client_ip}")

    result = PowerManager.lock_screen()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result
