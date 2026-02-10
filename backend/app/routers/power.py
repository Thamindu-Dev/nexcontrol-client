
from fastapi import APIRouter, Depends, HTTPException, Body
from app.core.security import SecurityManager
from app.services.power import PowerManager
from app.models.schemas import PowerActionRequest, CommandResponse

router = APIRouter(
    prefix="/system/power",
    tags=["Power"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

@router.post("/shutdown", response_model=CommandResponse)
async def shutdown_system(request: PowerActionRequest):
    """Shutdown the system"""
    result = PowerManager.shutdown(request.delay_seconds)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/restart", response_model=CommandResponse)
async def restart_system(request: PowerActionRequest):
    """Restart the system"""
    result = PowerManager.restart(request.delay_seconds)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/hibernate", response_model=CommandResponse)
async def hibernate_system():
    """Hibernate the system"""
    result = PowerManager.hibernate()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/lock", response_model=CommandResponse)
async def lock_system():
    """Lock the screen"""
    result = PowerManager.lock_screen()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result
