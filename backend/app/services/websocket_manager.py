
from fastapi import WebSocket
from typing import List, Dict
import json
import asyncio
from app.core.config import logger

class WebSocketConnectionManager:
    """
    Manage WebSocket connections for real-time updates
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
            logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        # Use asyncio.create_task for async removal if needed, but list removal is fast and synchronous is okay here usually
        # but to be safe with async lock:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        async with self.lock:
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
                    # Don't modify list while iterating if possible without copy
                    # But here we might just log and remove later or rely on disconnect handler
                    pass
