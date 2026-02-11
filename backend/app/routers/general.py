
import platform
import socket
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["General"])

@router.get("/api/info/root")
async def root():
    """Root endpoint (moved from / to allow static files)"""
    return {"message": "NexControl API is running", "timestamp": datetime.now().isoformat()}

@router.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@router.get("/api/system/info")
async def get_system_info():
    """Get basic system information (no auth required)"""
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }

@router.get("/test/error")
async def test_error():
    """Test error handling"""
    raise ValueError("This is a test error")

@router.get("/api/test/connection")
async def test_connection():
    """Test connection endpoint"""
    return {"status": "ok", "message": "Connection successful"}
