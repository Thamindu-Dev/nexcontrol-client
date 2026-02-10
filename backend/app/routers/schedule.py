
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from app.core.security import SecurityManager
from app.services.scheduler import ScheduledTaskManager
from app.models.schemas import ScheduledTask, CreateScheduledTaskRequest, UpdateScheduledTaskRequest, CommandResponse

router = APIRouter(
    prefix="/schedule",
    tags=["Schedule"],
    dependencies=[Depends(SecurityManager.get_current_user)]
)

scheduler_manager = ScheduledTaskManager()

@router.get("/list", response_model=List[ScheduledTask])
async def list_scheduled_tasks():
    """List scheduled tasks"""
    return scheduler_manager.list_tasks()

@router.post("/create", response_model=ScheduledTask)
async def create_scheduled_task(task_data: CreateScheduledTaskRequest):
    """Create a new scheduled task"""
    return scheduler_manager.create_task(
        task_data.name, 
        task_data.action, 
        task_data.scheduled_time
    )

@router.put("/{task_id}", response_model=Optional[ScheduledTask])
async def update_scheduled_task(task_id: str, task_data: UpdateScheduledTaskRequest):
    """Update a scheduled task"""
    task = scheduler_manager.update_task(task_id, **task_data.dict(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", response_model=CommandResponse)
async def delete_scheduled_task(task_id: str):
    """Delete a scheduled task"""
    if scheduler_manager.delete_task(task_id):
        return {"success": True, "message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task not found")

@router.post("/{task_id}/toggle", response_model=Optional[ScheduledTask])
async def toggle_scheduled_task(task_id: str):
    """Toggle a scheduled task enabled state"""
    task = scheduler_manager.toggle_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
