
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
import pyperclip
from app.core.security import SecurityManager
from app.core.config import logger

router = APIRouter(
    prefix="/clipboard",
    tags=["Clipboard"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

class ClipboardContent(BaseModel):
    content: str

@router.get("", response_model=ClipboardContent)
async def get_clipboard_content():
    """Get current clipboard content"""
    try:
        content = pyperclip.paste()
        return {"content": content}
    except Exception as e:
        logger.error(f"Clipboard read error: {e}")
        return {"content": ""}

@router.post("", response_model=ClipboardContent)
async def set_clipboard_content(data: ClipboardContent):
    """Set clipboard content"""
    try:
        pyperclip.copy(data.content)
        return {"content": data.content}
    except Exception as e:
        logger.error(f"Clipboard write error: {e}")
        raise HTTPException(status_code=500, detail="Failed to write to clipboard")
