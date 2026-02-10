
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict
from app.core.security import SecurityManager
from app.services.wol import WoLManager
from app.models.schemas import WolRequest, CommandResponse

router = APIRouter(
    prefix="/wol",
    tags=["Wake-on-LAN"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

@router.get("/devices", response_model=Dict[str, Dict[str, str]])
async def get_wol_devices():
    """Get registered WoL devices"""
    return WoLManager.get_devices()

@router.post("/register", response_model=CommandResponse)
async def register_wol_device(
    device_name: str = Body(..., embed=True), 
    mac_address: str = Body(..., embed=True)
):
    """Register a device for WoL"""
    return WoLManager.register_device(device_name, mac_address)

@router.post("/send", response_model=CommandResponse)
async def send_wol_packet(request: WolRequest):
    """Send WoL magic packet"""
    try:
        return WoLManager.send_magic_packet(
            request.mac_address, 
            request.broadcast_ip, 
            request.port
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
