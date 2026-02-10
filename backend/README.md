
# NexControl Backend

This is the backend for the NexControl application, built with FastAPI and Python.

## Modular Structure

The backend has been refactored from a monolithic `main.py` into a modular architecture:

- **`main.py`**: The application entry point. It orchestrates startup/shutdown and includes routers.
- **`app/`**: The main application package.
  - **`core/`**: Core configuration and security.
    - `config.py`: Application settings and environment variables.
    - `security.py`: Authentication, encryption, and hashing utilities.
  - **`models/`**: Pydantic models and schemas.
    - `schemas.py`: Request/response schemas.
  - **`routers/`**: API route definitions.
    - `auth.py`: Authentication endpoints.
    - `system.py`: System monitoring endpoints.
    - `power.py`: Power management endpoints.
    - `media.py`: Media control endpoints.
    - `apps.py`: Application launching endpoints.
    - `processes.py`: Process management endpoints.
    - `docker.py`: Docker management endpoints.
    - `screenshot.py`: Screenshot endpoints.
    - `wol.py`: Wake-on-LAN endpoints.
    - `clipboard.py`: Clipboard sync endpoints.
    - `schedule.py`: Scheduled task endpoints.
    - `threshold.py`: Notification threshold endpoints.
    - `websockets.py`: WebSocket handlers for real-time stats and control.
  - **`services/`**: Business logic and external system interactions.
    - `system_monitor.py`: Logic for retrieving system stats.
    - `power.py`: Logic for shutdown, restart, etc.
    - `media.py`: Logic for media control.
    - `launcher.py`: Logic for launching applications.
    - `processes.py`: Logic for listing and killing processes.
    - `docker.py`: Logic for interacting with Docker engine.
    - `screenshot.py`: Logic for capturing screenshots.
    - `wol.py`: Logic for sending WoL packets.
    - `scheduler.py`: Logic for managing and executing scheduled tasks.
    - `notifications.py`: Logic for monitoring thresholds and alerts.
    - `websocket_manager.py`: Logic for managing WebSocket connections.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Copy `.env.example` to `.env` and configure your settings (e.g., specific paths, keys).

3.  **Run**:
    ```bash
    uvicorn main:app --reload
    ```
    Or simply:
    ```bash
    python main.py
    ```

## Development

-   **Adding Features**: 
    -   Add business logic in `app/services/`.
    -   Define Pydantic models in `app/models/schemas.py`.
    -   Create a new router in `app/routers/` or update an existing one.
    -   Include the router in `main.py` if it's new.

-   **Testing**:
    Run `pytest` to execute tests (if available).

