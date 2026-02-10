
import base64
import os
import logging
from io import BytesIO

from app.core.config import settings, logger

# PyAutoGUI for Screenshots
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
except Exception:
    PYAUTOGUI_AVAILABLE = False


class ScreenshotService:
    """
    Capture screen screenshots using pyautogui
    Returns base64-encoded images
    """

    # Maximum screenshot size (10MB)
    MAX_SCREENSHOT_SIZE = 10 * 1024 * 1024

    @staticmethod
    def capture_screen(quality: int = 75) -> dict:
        """
        Capture the screen and return as base64 image
        
        Args:
            quality: JPEG quality (1-100)
        """
        # Check if pyautogui is available
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "message": "Screenshot feature not available (headless system or pyautogui not installed)"
            }

        try:
            # Validate quality range
            quality = max(1, min(100, int(quality)))

            # Check if display is available (not headless)
            if settings.OS_TYPE != "Windows" and os.environ.get('DISPLAY') is None:
                logger.warning("Screenshot attempted on headless system")
                return {
                    "success": False,
                    "message": "No display available (headless system)"
                }

            # Take screenshot
            screenshot = pyautogui.screenshot()

            # Convert to bytes with specified quality
            buffer = BytesIO()
            screenshot.save(buffer, format="JPEG", quality=quality)
            image_bytes = buffer.getvalue()

            # Check size limits
            if len(image_bytes) > ScreenshotService.MAX_SCREENSHOT_SIZE:
                logger.warning(f"Screenshot too large: {len(image_bytes)} bytes")
                # Retry with lower quality
                for retry_quality in [50, 30, 10]:
                    buffer = BytesIO()
                    screenshot.save(buffer, format="JPEG", quality=retry_quality)
                    image_bytes = buffer.getvalue()
                    if len(image_bytes) <= ScreenshotService.MAX_SCREENSHOT_SIZE:
                        break

            # Encode to base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            return {
                "success": True,
                "image": image_b64,
                "format": "jpeg",
                "quality": quality,
                "size": len(image_bytes)
            }

        except Exception as e:
            logger.error(f"Screenshot error: {type(e).__name__}")
            return {
                "success": False,
                "message": "Screenshot failed"
            }

    @staticmethod
    def is_available() -> bool:
        return PYAUTOGUI_AVAILABLE
