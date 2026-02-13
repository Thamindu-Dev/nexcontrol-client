
import asyncio
import logging
import os
import sys
import platform
import threading
from pathlib import Path

# Fix console encoding for Windows (handles emojis)
if platform.system() == "Windows":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# ============================================================
# FIRST-RUN CHECK (Must be before config import!)
# ============================================================
def safe_print(*args, **kwargs):
    """Print function that handles encoding errors gracefully."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback to ASCII-only output
        ascii_args = []
        for arg in args:
            if isinstance(arg, str):
                # Remove emojis and unicode symbols
                ascii_args.append(arg.encode('ascii', 'ignore').decode('ascii'))
            else:
                ascii_args.append(arg)
        print(*ascii_args, **kwargs)

def check_first_run_and_launch_setup():
    """
    Check if this is the first run (no config exists).
    If so, launch the setup wizard before starting the server.
    """
    # Check if we should skip setup (for CI/CD, docker, etc.)
    if os.getenv("NEXCONTROL_SKIP_SETUP"):
        return False

    # Only works on Windows for DPAPI mode
    if platform.system() != "Windows":
        return False

    try:
        import win32crypt
        import json
    except ImportError:
        # DPAPI not available, skip setup check
        return False

    # Check for DPAPI config
    config_dir = Path(os.getenv('LOCALAPPDATA', '~')) / 'NexControl'
    config_file = config_dir / 'config.dat'

    # If config exists, not first run
    if config_file.exists():
        return False

    # First run - launch setup wizard
    safe_print("\n" + "=" * 60)
    safe_print("[*] NexControl First-Run Setup")
    safe_print("=" * 60)
    safe_print("\nNo configuration found. Launching setup wizard...\n")

    try:
        from app.portable_setup import run_setup_wizard
        run_setup_wizard(on_complete_callback=lambda: None)
        safe_print("\n[+] Setup complete! Starting server...\n")
        return True
    except Exception as e:
        import traceback
        safe_print(f"\n[!] Setup wizard failed: {e}")
        safe_print(f"\n[!] Traceback:\n{traceback.format_exc()}")
        safe_print("\nPlease run setup manually:")
        safe_print("  python -m app.portable_setup")
        sys.exit(1)


# Run first-run check before importing config (which will fail if no config)
setup_completed = check_first_run_and_launch_setup()

import uvicorn
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

# Import Core (safe now after setup check)
from app.core.config import settings, logger
from app.core.security import SecurityManager

# Import Services (for lifespan management)
from app.services.system_monitor import SystemMonitor
from app.services.update_checker import UpdateChecker
# Import Singletons from Routers
from app.routers.schedule import scheduler_manager
from app.routers.threshold import notification_manager
from app.routers.websockets import stats_manager

# Import Routers
from app.routers import (
    auth, system, power, media, apps, processes, docker,
    screenshot, wol, clipboard, schedule, threshold,
    general, websockets, update
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
    
    # Initialize Update Checker
    update_checker_service = UpdateChecker(
        current_version=settings.VERSION,
        github_repo="Thamindu-Dev/nexcontrol-client",
        check_interval_hours=24  # Check for updates every 24 hours
    )
    
    # Set update checker in router
    update.set_update_checker(update_checker_service)
    
    # Start Update Checker
    await update_checker_service.start()
    
    # Start Scheduler
    await scheduler_manager.start_scheduler()
    
    # Start Threshold Monitor
    await notification_manager.start_monitor(websocket_manager=stats_manager)
    
    # Start Stats Broadcast
    stats_task = asyncio.create_task(broadcast_system_stats())
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    stats_task.cancel()
    await scheduler_manager.stop_scheduler()
    await notification_manager.stop_monitor()
    await update_checker_service.stop()
    logger.info("Shutdown complete.")


# Initialize App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    # Disable docs in production if desired, but keep for now
)

# CORS Configuration - Secure but flexible for local network
# If ALLOWED_ORIGINS is set in .env, use it. Otherwise, allow localhost and local network
if settings.ALLOWED_ORIGINS == ["*"]:
    # For local network use: allow localhost and common local IP ranges
    allowed_origins = [
        "http://localhost:9000",
        "http://localhost:8080",
        "http://127.0.0.1:9000",
        "http://127.0.0.1:8080",
        "capacitor://localhost",  # For mobile apps
        "http://localhost",  # Development servers
        "http://ionic.local",  # Ionic dev server
    ]
    # Also allow any local network IP (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
    # This is detected dynamically at runtime from requests
else:
    allowed_origins = settings.ALLOWED_ORIGINS

def is_local_network(origin: str) -> bool:
    """Check if origin is from local network"""
    if not origin:
        return False
    # Allow localhost variants
    if origin in allowed_origins:
        return True
    # Allow local network IPs
    for prefix in ["http://192.168.", "http://10.", "http://172.16.", "http://172.17.", "http://172.18.", "http://172.19.",
                    "http://172.20.", "http://172.21.", "http://172.22.", "http://172.23.", "http://172.24.",
                    "http://172.25.", "http://172.26.", "http://172.27.", "http://172.28.", "http://172.29.",
                    "http://172.30.", "http://172.31.", "https://192.168.", "https://10.", "capacitor://"]:
        if origin.startswith(prefix):
            return True
    return False

# Custom CORS middleware that handles dynamic local network origins
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    
    # Check if this is a CORS-eligible request
    should_add_cors = (
        not origin or  # No origin (native mobile apps)
        origin in allowed_origins or  # Explicitly allowed
        is_local_network(origin)  # Local network
    )
    
    # Handle preflight (OPTIONS) requests
    if request.method == "OPTIONS":
        if should_add_cors:
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response
        else:
            # Not allowed, let it fail
            return Response(status_code=403)
    
    # For non-OPTIONS requests, proceed normally
    response = await call_next(request)

    # Add CORS headers for actual requests
    if should_add_cors:
        response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With"
        response.headers["Access-Control-Expose-Headers"] = "Content-Type, Authorization"

    return response

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
        "/api/launch",
        # Update endpoints (public info)
        "/api/update/check",
        "/api/update/status"
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
app.include_router(update.router, prefix="/api")
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
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist", "spa")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

# ============================================================
# SYSTEM TRAY SUPPORT (Windows Only, Production Mode)
# ============================================================
_system_tray = None

def get_system_tray():
    """Get or create system tray manager (lazy import)."""
    global _system_tray
    if _system_tray is None and platform.system() == "Windows":
        try:
            from app.system_tray import SystemTrayManager
            exe_path = Path(sys.executable).parent / "NexControl.exe"
            _system_tray = SystemTrayManager(exe_path)
        except ImportError:
            logger = logging.getLogger("nexcontrol")
            logger.warning("System tray feature not available. Install: pip install pystray")
    return _system_tray

if __name__ == "__main__":
    # Detect if running from exe or production mode
    is_production = (
        getattr(sys, 'frozen', False) or  # Running as PyInstaller bundle
        os.getenv('ENVIRONMENT', 'production') == 'production'
    )

    if is_production:
        # In production/exe mode, start system tray and run server
        tray = get_system_tray()

        # Start system tray in background
        if tray:
            tray.start()
            safe_print("\n[+] System tray started. Server is running in the background.")
            safe_print("[] Look for the NexControl icon in your system tray.")
            safe_print("[*] Use the tray menu to control the server.\n")

        # Run server (blocking)
        # Note: System tray runs in separate thread
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # In development mode, use reload
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
