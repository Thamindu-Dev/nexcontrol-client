
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from app.core.security import SecurityManager
from app.services.media import MediaController
from app.models.schemas import MediaControlRequest, CommandResponse

router = APIRouter(
    prefix="/media",
    tags=["Media"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

@router.get("/apps", response_model=List[str])
async def get_media_apps():
    """Get list of running media applications"""
    return MediaController.get_media_apps()

@router.post("/control", response_model=CommandResponse)
async def control_media(request: MediaControlRequest):
    """
    Send media control command
    Scope: 'global' or 'targeted'
    """
    if request.scope == "global":
        result = MediaController.send_media_command("Default (Global)", request.action)
    else:
        # Targeted
        if not request.app_name:
             raise HTTPException(status_code=400, detail="App name required for targeted scope")
        result = MediaController.send_media_command(request.app_name, request.action)
        
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
        
    return result
