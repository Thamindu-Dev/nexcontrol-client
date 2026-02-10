
from fastapi import APIRouter, Depends
from app.core.security import SecurityManager
from app.services.system_monitor import SystemMonitor

router = APIRouter(
    prefix="/stats",
    tags=["System"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

@router.get("/all")
async def get_system_stats():
    """Get all system statistics"""
    return SystemMonitor.get_all_stats()

@router.get("/cpu")
async def get_cpu_stats():
    """Get CPU statistics"""
    return SystemMonitor.get_cpu_usage()

@router.get("/memory")
async def get_memory_stats():
    """Get memory statistics"""
    return SystemMonitor.get_memory_usage()

@router.get("/disk")
async def get_disk_stats():
    """Get primary disk usage statistics"""
    return SystemMonitor.get_disk_usage()

@router.get("/disks")
async def get_all_disks():
    """Get all disk storage devices"""
    return SystemMonitor.get_all_disks()

@router.get("/network")
async def get_network_stats():
    """Get network statistics"""
    return SystemMonitor.get_network_stats()

@router.get("/gpu")
async def get_gpu_stats():
    """Get GPU statistics"""
    return SystemMonitor.get_gpu_usage()
