
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import SecurityManager
from app.services.screenshot import ScreenshotService
from app.models.schemas import ScreenshotRequest

router = APIRouter(
    prefix="/system/screenshot",
    tags=["Screenshot"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

@router.post("/capture")
async def capture_screenshot(request: ScreenshotRequest):
    """Capture a screenshot"""
    if not ScreenshotService.is_available():
        raise HTTPException(status_code=503, detail="Screenshot service unavailable")
        
    result = ScreenshotService.capture_screen(request.quality)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
        
    return result
