#!/usr/bin/env python3
"""
 =============================================================================
 NexControl Update Router
 =============================================================================
 API endpoints for checking application updates.
 =============================================================================
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/update", tags=["Update"])


# This will be initialized in main.py
update_checker = None


def set_update_checker(checker):
    """Set the update checker instance (called from main.py)."""
    global update_checker
    update_checker = checker


@router.get("/check")
async def check_for_updates():
    """
    Check for application updates from GitHub.
    
    Returns:
        Update information including current version, latest version,
        availability status, release notes, and download URL.
    """
    if not update_checker:
        raise HTTPException(status_code=503, detail="Update checker not available")
    
    try:
        # Force a new check
        update_info = await update_checker.check_for_updates()
        return JSONResponse(content=update_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update check failed: {str(e)}")


@router.get("/status")
async def get_update_status():
    """
    Get cached update status (doesn't make a new API call).
    
    Returns:
        Cached update information from the last check.
    """
    if not update_checker:
        raise HTTPException(status_code=503, detail="Update checker not available")
    
    return JSONResponse(content=update_checker.get_status())
