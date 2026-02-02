# NexControl Backend

Secure, local network Remote PC Controller backend powered by FastAPI.

## Features

- **System Monitoring**: Real-time CPU, RAM, Disk, GPU, and Network stats
- **Power Management**: Shutdown, Hibernate, Restart commands
- **Docker Control**: Start/Stop/Restart containers, view logs
- **Process Manager**: List and kill system processes
- **Screenshot**: Capture screen as base64 image
- **Security**: AES-256-GCM encryption, JWT authentication, replay attack prevention
- **Cross-Platform**: Supports Windows and Linux

## Architecture

```
NexControl Backend (FastAPI)
├── Security Layer (AES + JWT)
├── System Monitor (psutil)
├── Power Manager (OS-specific commands)
├── Docker Manager (Docker SDK)
├── Process Manager (psutil)
└── Screenshot Service (pyautogui)
```

## Requirements

- Python 3.8+
- Windows 10/11 or Linux (Ubuntu 20.04+)
- Docker (optional, for container management)
- NVIDIA GPU (optional, for temperature monitoring)

## Installation

### 1. Clone or Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

### 5. Start the Server

**Development Mode (with auto-reload):**
```bash
python main.py
```

**Or using uvicorn directly:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Access the API

- **API Root**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Default Credentials

⚠️ **IMPORTANT**: Change the default password in production!

```
Password: admin123
```

To change the password, either:
1. Set `APP_PASSWORD_HASH` in `.env` (bcrypt hash)
2. Or modify `DEFAULT_APP_PASSWORD` in `main.py`

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login with app password, get JWT token |
| GET | `/api/auth/verify` | Verify JWT token validity |

### System Stats

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats/cpu` | CPU usage percentage |
| GET | `/api/stats/memory` | RAM usage statistics |
| GET | `/api/stats/disk` | Disk usage statistics |
| GET | `/api/stats/gpu` | GPU temperature (NVIDIA) |
| GET | `/api/stats/network` | Network I/O statistics |
| GET | `/api/stats/all` | All stats in one call |

### Power Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/power/shutdown` | Shutdown system (with optional delay) |
| POST | `/api/power/hibernate` | Hibernate system |
| POST | `/api/power/restart` | Restart system (with optional delay) |

### Docker Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/docker/status` | Check if Docker is available |
| GET | `/api/docker/containers` | List all containers |
| POST | `/api/docker/containers/{id}/start` | Start container |
| POST | `/api/docker/containers/{id}/stop` | Stop container |
| POST | `/api/docker/containers/{id}/restart` | Restart container |
| GET | `/api/docker/containers/{id}/logs` | Get container logs |

### Process Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/processes` | List processes (sorted by CPU/Memory) |
| DELETE | `/api/processes/{pid}` | Kill process by PID |
| GET | `/api/processes/{pid}` | Get process details |

### Screenshot

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/screenshot` | Capture screen as base64 image |

### Wake-on-LAN

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/wol/register` | Register device MAC address |
| GET | `/api/wol/devices` | List registered devices |

## Security

### Encryption

All sensitive requests use **AES-256-GCM** encryption:
- Frontend encrypts JSON payload with AES key
- Backend decrypts and validates timestamp (replay prevention)
- Response is encrypted before sending back

### Authentication

- **JWT (JSON Web Tokens)** for session management
- **bcrypt** for password hashing
- **Token expiration**: 60 minutes (configurable)

### Replay Attack Prevention

- Every request includes a Unix timestamp
- Server rejects requests with timestamps older than 30 seconds
- Configurable via `TIMESTAMP_TOLERANCE` constant

## OS-Specific Notes

### Windows

- Power commands use Windows `shutdown` utility
- Docker Desktop must be running for Docker features
- GPU monitoring requires NVIDIA GPU with drivers

### Linux

- Power commands use `systemctl`
- Some power commands may require `sudo` privileges
- Docker daemon must be running

## Troubleshooting

### Docker not available

```
Error: Docker not available
```

**Solution**: Start Docker Desktop (Windows) or Docker service (Linux):
```bash
sudo systemctl start docker  # Linux
```

### GPU temperature not working

```
Error: GPU monitoring not available
```

**Solution**: Install NVIDIA drivers and `nvidia-ml-py`:
```bash
pip install nvidia-ml-py
```

### Screenshot fails on headless system

```
Error: No display available
```

**Solution**: This is expected on servers without a display. The feature is designed for desktop systems.

### Port already in use

```
Error: [Errno 48] Address already in use
```

**Solution**: Change the port in `main.py` or stop the conflicting service:
```bash
# Linux/macOS
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Firewall Configuration

To allow local network access, you may need to configure your firewall:

**Windows (Windows Firewall):**
```cmd
netsh advfirewall firewall add rule name="NexControl" dir=in action=allow protocol=TCP localport=8000
```

**Linux (UFW):**
```bash
sudo ufw allow 8000/tcp
```

**Linux (firewalld):**
```bash
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment configuration template
├── README.md           # This file
└── nexcontrol.log      # Application logs (generated)
```

### Adding New Features

1. Add new class or function in appropriate section of `main.py`
2. Create Pydantic models for request/response if needed
3. Add route with `@app` decorator
4. Add authentication dependency if required: `Depends(get_current_user)`
5. Test endpoint using Swagger UI at `/docs`

### Logging

Logs are written to both:
- Console (stdout)
- `nexcontrol.log` file

Change log level in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
logging.basicConfig(level=logging.WARNING)  # Less verbose
```

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Change `DEFAULT_APP_PASSWORD` or set `APP_PASSWORD_HASH`
- [ ] Use environment variables for sensitive configuration
- [ ] Disable `reload=True` in uvicorn
- [ ] Set up reverse proxy (nginx/Apache) for HTTPS
- [ ] Configure firewall rules
- [ ] Monitor logs regularly
- [ ] Set up log rotation

### Running as Service

**Linux (systemd):**
```ini
# /etc/systemd/system/nexcontrol.service
[Unit]
Description=NexControl Backend
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/venv/bin"
ExecStart=/path/to/backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable nexcontrol
sudo systemctl start nexcontrol
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start program
   - Program: `venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\backend`

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please visit the main project repository.

---

**Version**: 1.0.0
**Last Updated**: 2025
