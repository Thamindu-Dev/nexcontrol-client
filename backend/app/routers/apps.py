
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.core.security import SecurityManager
from app.services.launcher import AppLauncher
from app.models.schemas import AppLaunchRequest, CommandResponse

router = APIRouter(
    prefix="/apps",
    tags=["Apps"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

# Instantiate AppLauncher service
launcher_service = AppLauncher()

from app.core.config import settings

@router.get("", response_model=Dict[str, Any])
async def list_apps():
    """List all available applications"""
    apps = launcher_service.get_all_apps()
    return {
        "success": True,
        "apps": apps,
        "platform": settings.OS_TYPE
    }

@router.post("/launch", response_model=CommandResponse)
async def launch_app(request: AppLaunchRequest, current_user: str = Depends(SecurityManager.get_current_user)):
    """Launch an application"""
    result = launcher_service.launch_app(request.app_id, user=current_user)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/custom")
async def add_custom_app(
    name: str, 
    app_type: str, 
    path: str = None, 
    url: str = None, 
    icon: str = "apps",
    current_user: str = Depends(SecurityManager.get_current_user)
):
    """Add a custom application"""
    return launcher_service.add_custom_app(name, app_type, path, url, icon, user=current_user)

@router.delete("/custom/{app_id}")
async def delete_custom_app(app_id: str):
    """Delete a custom application"""
    if launcher_service.delete_custom_app(app_id):
        return {"success": True, "message": "App deleted"}
    raise HTTPException(status_code=404, detail="App not found")
