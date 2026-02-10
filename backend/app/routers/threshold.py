
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from app.core.security import SecurityManager
from app.services.notifications import ThresholdNotificationManager
from app.models.schemas import ThresholdConfig, ThresholdAlert, CommandResponse

router = APIRouter(
    prefix="/threshold",
    tags=["Threshold"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

notification_manager = ThresholdNotificationManager()

@router.get("/config", response_model=ThresholdConfig)
async def get_threshold_config():
    """Get threshold configuration"""
    return notification_manager.get_config()

@router.post("/config", response_model=ThresholdConfig)
async def update_threshold_config(config: ThresholdConfig):
    """Update threshold configuration"""
    return notification_manager.update_config(**config.dict())

@router.get("/alerts", response_model=List[ThresholdAlert])
async def get_threshold_alerts(limit: int = 50, unacknowledged_only: bool = False):
    """Get threshold alerts"""
    return notification_manager.get_alerts(limit, unacknowledged_only)

@router.post("/alerts/{alert_id}/acknowledge", response_model=CommandResponse)
async def acknowledge_alert(alert_id: str):
    """Acknowledge a specific alert"""
    if notification_manager.acknowledge_alert(alert_id):
        return {"success": True, "message": "Alert acknowledged"}
    raise HTTPException(status_code=404, detail="Alert not found")

@router.post("/alerts/acknowledge-all", response_model=CommandResponse)
async def acknowledge_all_alerts():
    """Acknowledge all alerts"""
    count = notification_manager.acknowledge_all_alerts()
    return {"success": True, "message": f"Acknowledged {count} alerts"}
