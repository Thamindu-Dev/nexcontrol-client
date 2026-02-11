# NexControl Backend

FastAPI-based backend for the NexControl Remote PC Controller application. Provides REST API, WebSocket support, and comprehensive security features.

## Table of Contents
- [Architecture](#architecture)
- [Setup](#setup)
- [API Endpoints](#api-endpoints)
- [WebSocket](#websocket)
- [Security](#security)
- [Configuration](#configuration)
- [Development](#development)

## Architecture

### Modular Structure

The backend follows a modular architecture for maintainability:

```
backend/
├── main.py                      # Application entry point
├── server_gui.py               # Desktop GUI (Windows)
├── build_server_gui.py         # GUI build script
├── setup_env.py                # Environment setup helper
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
│
└── app/
    ├── __init__.py
    ├── core/                    # Core functionality
    │   ├── config.py           # Settings & configuration
    │   └── security.py         # Auth, encryption, validation
    ├── models/                  # Data models
    │   └── schemas.py          # Pydantic models
    ├── routers/                 # API endpoints
    │   ├── auth.py             # Authentication
    │   ├── system.py           # System stats
    │   ├── power.py            # Power management
    │   ├── media.py            # Media controls
    │   ├── apps.py             # App launcher
    │   ├── processes.py        # Process manager
    │   ├── docker.py           # Docker management
    │   ├── screenshot.py       # Screenshot capture
    │   ├── wol.py              # Wake-on-LAN
    │   ├── clipboard.py        # Clipboard sync
    │   ├── schedule.py         # Scheduled tasks
    │   ├── threshold.py        # Threshold alerts
    │   ├── websockets.py       # WebSocket endpoints
    │   └── general.py          # General/test endpoints
    └── services/                # Business logic
        ├── system_monitor.py   # System stats
        ├── power.py            # Power actions
        ├── media.py            # Media control
        ├── launcher.py         # App launching
        ├── processes.py        # Process management
        ├── docker.py           # Docker client
        ├── screenshot.py       # Screenshot logic
        ├── wol.py              # WoL packets
        ├── scheduler.py        # Task scheduler
        └── notifications.py    # Threshold monitoring
```

### Key Design Patterns

- **Separation of Concerns:** Routers handle HTTP, services handle logic
- **Dependency Injection:** FastAPI Depends for auth/validation
- **Async/Await:** Non-blocking I/O for better performance
- **Middleware:** Custom middleware for CORS, security, encryption

## Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate virtual environment:**
   ```bash
   # Windows:
   venv\Scripts\activate

   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run the server:**
   ```bash
   python main.py
   ```

The server will start on: **http://localhost:8000**

### Server GUI (Windows)

For Windows users, a desktop GUI is available:

```bash
python build_server_gui.py
# Exe will be in: backend/dist/NexControlServer.exe
```

See [SERVER_GUI_GUIDE.md](../SERVER_GUI_GUIDE.md) for details.

## API Endpoints

### Authentication

#### POST `/api/auth/login`
Login and receive JWT token.

**Request (encrypted):**
```json
{
  "data": "<encrypted_payload>",
  "timestamp": 1234567890.123
}
```

**Payload (after decryption):**
```json
{
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### POST `/api/auth/verify`
Verify JWT token is valid.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "valid": true,
  "user": "admin"
}
```

### System Monitoring

#### GET `/api/stats/all`
Get all system statistics.

**Response:**
```json
{
  "cpu": {
    "percent": 45.2,
    "percent_per_cpu": [42.1, 48.5, 43.8, 46.2],
    "count": 4,
    "frequency": 3200000000
  },
  "memory": {
    "total": 17179869184,
    "available": 8589934592,
    "percent": 50.0,
    "used": 8589934592
  },
  "disk": [
    {
      "device": "C:",
      "mountpoint": "C:",
      "total": 500000000000,
      "used": 250000000000,
      "percent": 50.0
    }
  ],
  "gpu": {
    "temperature": 65
  }
}
```

#### GET `/api/system/info`
Get system information.

**Response:**
```json
{
  "system": "Windows",
  "hostname": "DESKTOP-PC",
  "release": "11",
  "version": "10.0.22621"
}
```

### Power Management

All power endpoints require authentication + encryption.

#### POST `/api/system/power/shutdown`
Shutdown the system.

**Request (encrypted):**
```json
{
  "delay": 0
}
```

**Rate Limit:** 5 requests per minute per IP

#### POST `/api/system/power/restart`
Restart the system.

**Request (encrypted):**
```json
{
  "delay": 0
}
```

#### POST `/api/system/power/hibernate`
Hibernate the system.

#### POST `/api/system/power/lock`
Lock the screen.

### Process Management

#### GET `/api/processes`
Get list of running processes.

**Query Parameters:**
- `sort`: `cpu` | `memory` | `name` (default: `cpu`)
- `limit`: Number of processes (default: 50)

**Response:**
```json
{
  "processes": [
    {
      "pid": 1234,
      "name": "chrome.exe",
      "cpu_percent": 5.2,
      "memory_mb": 512.5
    }
  ]
}
```

#### DELETE `/api/processes/{pid}`
Kill a process.

**Rate Limit:** Users can only kill their own processes (protected by ownership check)

### Docker Management

#### GET `/api/docker/containers`
List all Docker containers.

**Response:**
```json
{
  "containers": [
    {
      "id": "abc123",
      "name": "nginx",
      "status": "running",
      "image": "nginx:latest"
    }
  ]
}
```

#### POST `/api/docker/containers/{container_id}/start`
Start a container.

**Container ID Validation:** Path traversal protected

#### POST `/api/docker/containers/{container_id}/stop`
Stop a container.

#### GET `/api/docker/containers/{container_id}/logs`
Get container logs.

**Query Parameters:**
- `tail`: Number of lines from end (default: 100)

### Scheduled Tasks

#### GET `/api/schedule/list`
List all scheduled tasks.

**Response:**
```json
{
  "tasks": [
    {
      "id": "uuid",
      "name": "Daily Restart",
      "action": "restart",
      "scheduled_time": "2026-02-12T02:00:00Z",
      "enabled": true,
      "created_at": "2026-02-11T10:00:00Z",
      "last_run": "2026-02-11T02:00:00Z"
    }
  ]
}
```

#### POST `/api/schedule/create`
Create a new scheduled task.

**Request (encrypted):**
```json
{
  "name": "Daily Shutdown",
  "action": "shutdown",
  "scheduled_time": "2026-02-12T22:00:00Z"
}
```

#### POST `/api/schedule/{task_id}/toggle`
Enable/disable a task.

#### DELETE `/api/schedule/{task_id}`
Delete a scheduled task.

### Threshold Alerts

#### GET `/api/threshold/config`
Get threshold configuration.

**Response:**
```json
{
  "enabled": true,
  "cpu_threshold": 80,
  "memory_threshold": 85,
  "disk_threshold": 90
}
```

#### POST `/api/threshold/config`
Update threshold configuration.

**Request (encrypted):**
```json
{
  "enabled": true,
  "cpu_threshold": 90,
  "memory_threshold": 90,
  "disk_threshold": 95
}
```

#### GET `/api/threshold/alerts`
Get threshold alerts.

**Query Parameters:**
- `limit`: Max alerts to return (default: 50)
- `unacknowledged_only`: Only show unacknowledged (default: false)

**Response:**
```json
{
  "alerts": [
    {
      "id": "uuid",
      "metric_type": "cpu",
      "threshold": 80,
      "value": 85.5,
      "triggered_at": "2026-02-11T10:30:00Z",
      "acknowledged": false,
      "unit": "%"
    }
  ]
}
```

#### POST `/api/threshold/alerts/{alert_id}/acknowledge`
Acknowledge an alert.

### App Launcher

#### GET `/api/apps`
Get list of predefined applications.

**Response:**
```json
{
  "apps": [
    {
      "id": "notepad",
      "name": "Notepad",
      "type": "predefined",
      "path": "C:\\Windows\\System32\\notepad.exe",
      "icon": "notepad.png"
    }
  ]
}
```

#### POST `/api/launch`
Launch an application.

**Request (encrypted):**
```json
{
  "app_id": "notepad",
  "custom_path": null,
  "args": null
}
```

**Security:** Path validated, no shell=True, command injection protected

### Clipboard Sync

#### GET `/api/clipboard`
Get clipboard content.

**Response:**
```json
{
  "content": "clipboard text here"
}
```

#### POST `/api/clipboard`
Set clipboard content.

**Request (encrypted):**
```json
{
  "content": "new clipboard content"
}
```

### Screenshot

#### GET `/api/screenshot`
Capture and return screenshot.

**Response:** Binary image data (PNG)

### Wake-on-LAN

#### GET `/api/wol/devices`
List registered WoL devices.

**Response:**
```json
{
  "devices": [
    {
      "name": "Desktop-PC",
      "mac_address": "00:11:22:33:44:55"
    }
  ]
}
```

#### POST `/api/wol/send`
Send WoL magic packet.

**Request (encrypted):**
```json
{
  "mac_address": "00:11:22:33:44:55",
  "broadcast_ip": "255.255.255.255",
  "port": 9
}
```

**Validation:** MAC validated (no broadcast/multicast), IP validated

#### POST `/api/wol/register`
Register a WoL device.

### Media Controls

#### POST `/api/media/play`
Play/pause media.

#### POST `/api/media/next`
Next track.

#### POST `/api/media/previous`
Previous track.

#### POST `/api/media/volume`
Set volume level.

**Request (encrypted):**
```json
{
  "volume": 50
}
```

## WebSocket

### `/ws/stats` - Real-time Stats

WebSocket endpoint for real-time system statistics.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stats');
```

**Message Format:**
```json
{
  "cpu": {
    "percent": 45.2
  },
  "memory": {
    "percent": 50.0
  }
}
```

**Auto-reconnect:** Frontend implements automatic reconnection with backoff

## Security

### Encryption

All sensitive endpoints use AES-256-GCM encryption:

1. **Request Format:**
   ```json
   {
     "data": "<base64_encrypted_data>",
     "timestamp": 1234567890.123
   }
   ```

2. **Timestamp Validation:** Requests must be within ±5 seconds

3. **Excluded Endpoints:** Auth, WebSocket, health check, and view-only endpoints

### Authentication

- **JWT Tokens:** 15-minute expiration
- **Hashing:** argon2 (memory-hard, time-hard)
- **Rate Limiting:**
  - Login: 5 attempts, then 15-minute lockout
  - Power actions: 5 per minute per IP

### Input Validation

- **PID Validation:** Platform-specific max values
- **Path Validation:** No `..`, no shell metacharacters
- **Container ID:** No path traversal characters
- **MAC Address:** No broadcast/multicast addresses

### Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy`: Restrictive policy

### Audit Logging

All sensitive actions logged to `security_audit.log`:
- Power actions (shutdown, restart, etc.)
- Failed login attempts
- Rate limit violations
- Process kills

Format: `timestamp - event_type - user - action - IP`

## Configuration

### Environment Variables

Located in `.env` file:

```bash
# Security
SECRET_KEY=<32+ random characters>
AES_KEY=<32+ random characters>
APP_PASSWORD_HASH=<argon2 hash or leave empty>

# Server
HOST=0.0.0.0
PORT=8000

# CORS (comma-separated)
ALLOWED_ORIGINS=http://localhost:9000,http://localhost:8080

# Environment (production or development)
ENVIRONMENT=production
```

### Key Generation

Generate secure keys:

```python
import secrets

# Generate 43+ character keys
AES_KEY = secrets.token_urlsafe(32)
SECRET_KEY = secrets.token_urlsafe(32)

print(f"AES_KEY={AES_KEY}")
print(f"SECRET_KEY={SECRET_KEY}")
```

### Password Hashing

Generate password hash:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
hash = pwd_context.hash("your_password")
print(f"APP_PASSWORD_HASH={hash}")
```

## Development

### Adding New Features

1. **Create Service** (in `app/services/`):
   ```python
   class MyService:
       @staticmethod
       def do_something():
           return {"result": "success"}
   ```

2. **Create Schema** (in `app/models/schemas.py`):
   ```python
   class MyRequest(BaseModel):
       field1: str
       field2: int
   ```

3. **Create Router** (in `app/routers/`):
   ```python
   from fastapi import APIRouter, Depends
   from app.core.security import SecurityManager

   router = APIRouter(
       prefix="/myfeature",
       tags=["MyFeature"],
       dependencies=[Depends(SecurityManager.get_current_user)]
   )

   @router.post("/action")
   async def my_action(request: MyRequest):
       result = MyService.do_something()
       return result
   ```

4. **Include Router** (in `main.py`):
   ```python
   from app.routers import myfeature
   app.include_router(myfeature.router, prefix="/api")
   ```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Debugging

Enable debug mode:

```bash
# In .env
ENVIRONMENT=development
DEBUG=true
```

Debug mode includes:
- Detailed error messages
- Full stack traces
- CORS allows all origins

### Logs

- **Application Log:** `nexcontrol.log`
- **Security Audit Log:** `security_audit.log`
- **Server Logs:** Visible in Server GUI or console

Log rotation recommended for production.

## API Documentation (Interactive)

When the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Interactive API documentation with "Try it out" functionality.

---

**Version:** 1.0.0
**Last Updated:** 2026-02-11
**Python:** 3.8+
**Framework:** FastAPI 0.104+
