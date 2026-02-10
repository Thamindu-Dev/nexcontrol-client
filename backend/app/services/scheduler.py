
import asyncio
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from app.core.config import settings, logger
from app.models.schemas import ScheduledTask
from app.services.power import PowerManager

class ScheduledTaskManager:
    """
    Manage scheduled power tasks
    """

    def __init__(self, storage_file: str = "scheduled_tasks.json"):
        self.storage_file = storage_file
        self.tasks: Dict[str, ScheduledTask] = {}
        self._scheduler_task = None
        self._running = False
        self._load_tasks()
        logger.info("ScheduledTaskManager initialized")

    def _load_tasks(self):
        """Load tasks from persistent storage"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = ScheduledTask(**task_data)
                        self.tasks[task.id] = task
                        if not task.enabled:
                            self.tasks.pop(task.id, None)
                logger.info(f"Loaded {len(self.tasks)} scheduled tasks from storage")
        except Exception as e:
            logger.error(f"Error loading scheduled tasks: {type(e).__name__}")

    def _save_tasks(self):
        """Save tasks to persistent storage"""
        try:
            with open(self.storage_file, 'w') as f:
                tasks_data = [task.dict() for task in self.tasks.values()]
                json.dump(tasks_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving scheduled tasks: {type(e).__name__}")

    def create_task(self, name: str, action: str, scheduled_time: str) -> ScheduledTask:
        """Create a new scheduled task"""
        import uuid
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            id=task_id,
            name=name,
            action=action,
            scheduled_time=scheduled_time,
            enabled=True,
            created_at=datetime.now().isoformat()
        )
        self.tasks[task_id] = task
        self._save_tasks()
        logger.info(f"Created scheduled task: {name} ({action}) at {scheduled_time}")
        return task

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        return self.tasks.get(task_id)

    def list_tasks(self) -> List[ScheduledTask]:
        return list(self.tasks.values())

    def update_task(self, task_id: str, **kwargs) -> Optional[ScheduledTask]:
        task = self.tasks.get(task_id)
        if not task:
            return None

        for key, value in kwargs.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)

        self._save_tasks()
        logger.info(f"Updated scheduled task: {task_id}")
        return task

    def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            logger.info(f"Deleted scheduled task: {task_id}")
            return True
        return False

    def toggle_task(self, task_id: str) -> Optional[ScheduledTask]:
        task = self.tasks.get(task_id)
        if not task:
            return None

        task.enabled = not task.enabled
        self._save_tasks()
        logger.info(f"Toggled scheduled task {task_id}: enabled={task.enabled}")
        return task

    async def start_scheduler(self):
        """Start the background task scheduler"""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduled task manager started")

    async def stop_scheduler(self):
        """Stop the background task scheduler"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduled task manager stopped")

    async def _scheduler_loop(self):
        """Background loop that checks and executes scheduled tasks"""
        while self._running:
            try:
                now = datetime.now()
                for task_id, task in list(self.tasks.items()):
                    if not task.enabled:
                        continue

                    try:
                        scheduled_dt = datetime.fromisoformat(task.scheduled_time.replace('Z', '+00:00'))

                        if scheduled_dt <= now:
                            logger.info(f"Executing scheduled task: {task.name} ({task.action})")
                            await self._execute_task(task)
                            self.delete_task(task_id)

                    except Exception as e:
                        logger.error(f"Error processing task {task_id}: {type(e).__name__}")

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {type(e).__name__}")
                await asyncio.sleep(5)

    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        try:
            if task.action == "shutdown":
                # Calls static methods of PowerManager
                result = PowerManager.shutdown(0)
            elif task.action == "restart":
                result = PowerManager.restart(0)
            elif task.action == "hibernate":
                result = PowerManager.hibernate()
            else:
                logger.error(f"Unknown action: {task.action}")
                return

            if result.get("success"):
                logger.info(f"Task executed successfully: {task.name}")
            else:
                logger.error(f"Task execution failed: {task.name} - {result.get('message')}")

        except Exception as e:
            logger.error(f"Error executing task {task.name}: {type(e).__name__}")
