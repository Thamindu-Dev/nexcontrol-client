
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import asyncio
from app.core.config import logger
from app.services.websocket_manager import WebSocketConnectionManager
from app.services.system_monitor import SystemMonitor
from app.services.media import MediaController
from app.services.launcher import AppLauncher

router = APIRouter(
    tags=["WebSockets"]
)

stats_manager = WebSocketConnectionManager()
media_manager = WebSocketConnectionManager()

@router.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    await stats_manager.connect(websocket)
    try:
        while True:
            # Wait for any message from client
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "get_stats":
                    stats = SystemMonitor.get_all_stats()
                    await websocket.send_json(stats)
            except WebSocketDisconnect:
                stats_manager.disconnect(websocket)
                break
            except Exception as e:
                logger.error(f"WebSocket stats receive error: {e}")
                break
    except Exception as e:
        logger.error(f"WebSocket stats connection error: {e}")
    finally:
        stats_manager.disconnect(websocket)

@router.websocket("/ws/media")
async def websocket_media_control(websocket: WebSocket):
    await media_manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                command_type = message.get("type")
                
                if command_type == "media_command":
                    action = message.get("action")
                    app_name = message.get("app", "Default (Global)")
                    if action:
                        result = MediaController.send_media_command(app_name, action)
                        # send result back to sender? Or broadcast?
                        # Usually media control just performs action. But feedback is nice.
                        await websocket.send_json({"type": "command_result", "data": result})

                elif command_type == "launch_app":
                     app_id = message.get("app_id")
                     if app_id:
                         launcher = AppLauncher()
                         result = launcher.launch_app(app_id)
                         await websocket.send_json({"type": "launch_result", "data": result})

                elif command_type == "ping":
                     await websocket.send_text("pong")

            except json.JSONDecodeError:
                pass
            except WebSocketDisconnect:
                media_manager.disconnect(websocket)
                break
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
    except Exception as e:
        logger.error(f"WebSocket media connection error: {e}")
    finally:
        media_manager.disconnect(websocket)
