
import asyncio
import logging
import os
import uvicorn
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

# Import Core
from app.core.config import settings, logger
from app.core.security import SecurityManager

# Import Services (for lifespan management)
from app.services.system_monitor import SystemMonitor
# Import Singletons from Routers
from app.routers.schedule import scheduler_manager
from app.routers.threshold import notification_manager
from app.routers.websockets import stats_manager

# Import Routers
from app.routers import (
    auth, system, power, media, apps, processes, docker,
    screenshot, wol, clipboard, schedule, threshold,
    general, websockets
)

# Background Tasks
async def broadcast_system_stats():
    """Background task to broadcast system stats via WebSocket"""
    logger.info("Starting stats broadcast task")
    while True:
        try:
            if stats_manager.active_connections:
                stats = SystemMonitor.get_all_stats()
                await stats_manager.broadcast(stats)
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in stats broadcast: {e}")
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up NexControl Backend...")
    
    # Start Scheduler
    await scheduler_manager.start_scheduler()
    
    # Start Threshold Monitor (pass stats_manager for alerts)
    # notification_manager.start_monitor needs websocket_manager argument if we implemented it that way
    # Let's check implementation. created earlier.
    # It accepts websocket_manager. Pass stats_manager or a dedicated alert manager?
    # Using stats_manager for now as it handles broadcasting general messages if structure allows.
    await notification_manager.start_monitor(websocket_manager=stats_manager) # Broadcasting alerts to stats channel subscribers? Or media? 
    # Probably fine for now. Frontend listens on stats usually.
    
    # Start Stats Broadcast
    stats_task = asyncio.create_task(broadcast_system_stats())
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    stats_task.cancel()
    await scheduler_manager.stop_scheduler()
    await notification_manager.stop_monitor()
    logger.info("Shutdown complete.")


# Initialize App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    # Disable docs in production if desired, but keep for now
)

# CORS Configuration - Use specific origins for security
allowed_origins = settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS != ["*"] else ["http://localhost:9000", "http://localhost:8080", "http://127.0.0.1:9000", "http://127.0.0.1:8080"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific origins only, no wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],  # Explicit headers
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,  # Cache preflight for 1 hour
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Content-Security-Policy for frontend
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
    return response

# Encryption Middleware
@app.middleware("http")
async def encryption_middleware(request: Request, call_next):
    # Define excluded paths (these endpoints don't use encryption)
    # ONLY these endpoints work WITHOUT AES key (matching frontend skipSecurityCheck):
    excluded_paths = [
        "/docs", "/redoc", "/openapi.json",
        # Authentication
        "/auth/token", "/api/auth/token",
        "/auth/login", "/api/auth/login",
        "/auth/verify", "/api/auth/verify",
        "/auth/refresh", "/api/auth/refresh",
        # WebSocket
        "/ws/",
        # Health check
        "/api/health",
        # Test endpoints (check server status)
        "/api/test/connection",
        "/api/test/echo",
        # Stats endpoints - dashboard view only
        "/api/stats",
        # System info
        "/api/system/info",
        # WoL endpoints
        "/api/wol",
        # Screenshot endpoints
        "/api/screenshot",
        # Clipboard endpoint (simple text data)
        "/api/clipboard",
        # Threshold endpoints (viewing alerts and config)
        "/api/threshold/config",
        "/api/threshold/alerts",
        # Apps launcher (launching apps is low-risk operation)
        "/api/apps",
        "/api/launch"
    ]
    
    if request.method == "OPTIONS" or any(request.url.path.startswith(path) for path in excluded_paths):
        return await call_next(request)

    # Decryption Logic for Incoming Requests
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            # Clone request body to reading it
            body = await request.body()
            if body:
                import json
                try:
                    data = json.loads(body)
                    if isinstance(data, dict) and "data" in data and "timestamp" in data:
                        # Proceed to decrypt
                        decrypted_data = SecurityManager.decrypt_data(data["data"])
                        
                        # Validate timestamp
                        if not SecurityManager.validate_timestamp(data["timestamp"]):
                            return JSONResponse(
                                status_code=401,
                                content={"detail": "Request timestamp expired or invalid"}
                            )
                            
                        # Replace request body with decrypted data
                        # Simplified approach for FastAPI:
                        async def new_receive():
                            return {"type": "http.request", "body": json.dumps(decrypted_data).encode("utf-8")}
                        
                        request._receive = new_receive
                        
                except json.JSONDecodeError:
                    pass # Not JSON, proceed as is
        except Exception as e:
            logger.error(f"Middleware Decryption Error: {e}")
            return JSONResponse(status_code=400, content={"detail": "Decryption failed"})

    # Process Request
    response = await call_next(request)

    # Encryption Logic for Outgoing Responses
    # Only encrypt successful JSON responses
    if (200 <= response.status_code < 300) and \
       response.headers.get("content-type") == "application/json":

        # We need to capture the response body.
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # EXCLUSION CHECK for Response Encryption (double check)
        if request.method == "OPTIONS" or any(request.url.path.startswith(path) for path in excluded_paths):
            return response

        try:
            import json
            if response_body:
                data = json.loads(response_body)
                encrypted_string = SecurityManager.encrypt_data(data)

                # Create wrapper response
                import time
                new_response_data = {
                    "data": encrypted_string,
                    "timestamp": time.time()
                }

                # Prepare headers
                headers = dict(response.headers)

                # Remove Content-Length as it will change
                if "content-length" in headers:
                    del headers["content-length"]

                return JSONResponse(
                    content=new_response_data,
                    status_code=response.status_code,
                    headers=headers
                )
        except Exception as e:
            logger.error(f"Middleware Encryption Error: {e}")
            
            headers = dict(response.headers)
            
            if "content-length" in headers:
                del headers["content-length"]

            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type
            )

    return response

# Include Routers
app.include_router(auth.router, prefix="/api/auth") # Auth handles its own prefix logic or just /api/auth
app.include_router(system.router, prefix="/api") # Becomes /api/stats (since system.py is /stats)
app.include_router(power.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(apps.router, prefix="/api")
app.include_router(processes.router, prefix="/api")
app.include_router(docker.router, prefix="/api")
app.include_router(screenshot.router, prefix="/api")
app.include_router(wol.router, prefix="/api")
app.include_router(clipboard.router, prefix="/api")
app.include_router(schedule.router, prefix="/api")
app.include_router(threshold.router, prefix="/api")
app.include_router(websockets.router) # Websockets usually at root /ws or similar. Check router.
app.include_router(general.router) # General handles root and /api/test

# Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}")
    import traceback
    logger.error(traceback.format_exc())

    # Hide error details in production for security
    error_detail = "Internal Server Error"
    # In development mode, include error details
    if os.getenv("DEBUG", "false").lower() == "true":
        error_detail = f"Internal Server Error: {str(exc)}"

    return JSONResponse(
        status_code=500,
        content={"detail": error_detail},
        headers={
            "Access-Control-Allow-Origin": allowed_origins[0] if allowed_origins else "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Static Files (Frontend)
# Serve static files from frontend/dist if exists
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
