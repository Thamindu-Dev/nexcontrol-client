
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Optional
from app.core.security import SecurityManager
from app.services.wol import WoLManager
from app.models.schemas import WolRequest, CommandResponse

router = APIRouter(
    prefix="/wol",
    tags=["Wake-on-LAN"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

@router.get("/devices")
async def get_wol_devices():
    """Get registered WoL devices"""
    return WoLManager.get_devices()

@router.post("/register")
async def register_wol_device(
    device_name: str = Body(..., embed=True),
    mac_address: str = Body(..., embed=True),
    broadcast_ip: Optional[str] = Body(None, embed=True),
    port: Optional[int] = Body(None, embed=True)
):
    """Register a device for WoL"""
    return WoLManager.register_device(device_name, mac_address, broadcast_ip, port)

@router.delete("/devices/{device_name}")
async def delete_wol_device(device_name: str):
    """Delete a registered WoL device"""
    result = WoLManager.delete_device(device_name)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result

@router.post("/send")
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
