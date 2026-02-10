
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
from app.core.security import SecurityManager
from app.services.docker import DockerManager
from app.models.schemas import CommandResponse

router = APIRouter(
    prefix="/docker",
    tags=["Docker"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

# Instantiate DockerManager (connection initialized once)
docker_manager = DockerManager()

@router.get("/status")
async def get_docker_status():
    """Check Docker status"""
    return docker_manager.get_status()

@router.get("/containers", response_model=Dict[str, Any])
async def list_containers(all: bool = True):
    """List containers"""
    return docker_manager.list_containers(all)

@router.post("/containers/{container_id}/start", response_model=CommandResponse)
async def start_container(container_id: str):
    """Start a container"""
    result = docker_manager.start_container(container_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/containers/{container_id}/stop", response_model=CommandResponse)
async def stop_container(container_id: str):
    """Stop a container"""
    result = docker_manager.stop_container(container_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/containers/{container_id}/restart", response_model=CommandResponse)
async def restart_container(container_id: str):
    """Restart a container"""
    result = docker_manager.restart_container(container_id)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/containers/{container_id}/logs")
async def get_container_logs(container_id: str, tail: int = 100):
    """Get container logs"""
    result = docker_manager.get_container_logs(container_id, tail)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result
