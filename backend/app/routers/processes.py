
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from app.core.security import SecurityManager
from app.services.processes import ProcessManager
from app.models.schemas import CommandResponse
from fastapi.security import HTTPBearer

router = APIRouter(
    prefix="/processes",
    tags=["Processes"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

security = HTTPBearer()

@router.get("")
async def list_processes(
    limit: int = Query(default=30, ge=1, le=100),
    sort_by: str = Query(default="cpu", regex="^(cpu|memory)$")
):
    """List running processes sorted by CPU or memory usage"""
    processes = ProcessManager.list_processes(limit, sort_by)
    return {"processes": processes}

@router.post("/kill/{pid}", response_model=CommandResponse)
async def kill_process(pid: int, current_user: str = Depends(SecurityManager.get_current_user)):
    """Kill a process by PID with ownership checking"""
    # get_current_user returns the username string directly
    result = ProcessManager.kill_process(pid, current_user)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.get("/{pid}")
async def get_process_details(pid: int):
    """Get details for a specific process"""
    result = ProcessManager.get_process_details(pid)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
