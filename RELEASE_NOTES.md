# NexControl v1.0.0 - Production Release

**Release Date:** February 12, 2026
**Version:** 1.0.0
**License:** GNU General Public License v3.0 (GPLv3)
**Security Status:** 🟢 LOW RISK

---

## What's New in v1.0.0

### ✨ Major Features

1. **Portable Server (Windows)**
   - Single executable with no dependencies
   - Built-in setup wizard for first-run configuration
   - DPAPI-encrypted config storage
   - Unique AES/SECRET keys per installation
   - QR code export for mobile app setup
   - No .env files exposed in portable folder

2. **Enhanced Security**
   - Removed default password fallback
   - Argon2id password hashing
   - DPAPI encryption for config storage
   - No hardcoded credentials
   - Rate limiting on all endpoints

3. **Mobile App Integration**
   - QR code scanning for easy setup
   - Settings-based encryption key entry
   - Real-time connection status
   - Biometric authentication support

4. **System Tray Support (Windows)**
   - Minimize server to system tray
   - Background operation with hidden console
   - Quick access menu for common tasks
   - Show/hide console window
   - Server status indicator
   - Quick launch web interface
   - Encryption key display with clipboard copy

---

## Distribution Package

### Portable Server (Windows)

**File:** `NexControl.exe` (33 MB)

**Location:** `backend/dist/NexControl.exe`

**Contents:**
- Single executable, no installation required
- Includes all dependencies via PyInstaller
- Setup wizard on first run
- Generates unique keys per installation

**After First Run, Creates:**
- `AES_KEY.txt` - Encryption key for mobile app
- `AES_KEY_QR.png` - QR code for scanning
- `SETUP_INSTRUCTIONS.txt` - User guide
- Config stored in: `%LOCALAPPDATA%\NexControl\config.dat`

---

## Quick Start Guide

### For End Users

1. **Download** `NexControl.exe`
2. **Run** the executable
3. **Follow** the setup wizard:
   - Create admin password (12+ characters)
   - Keys auto-generated
4. **Mobile App Setup:**
   - Copy key from `AES_KEY.txt` or scan `AES_KEY_QR.png`
   - Enter server URL: `http://YOUR_PC_IP:8000`
   - Login with your password

### For Developers

**Development Mode:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

**Build Portable Executable:**
```bash
cd backend
pip install pyinstaller
pyinstaller --onefile --name NexControl \
  --add-data "app;app" \
  --hidden-import passlib \
  --hidden-import argon2 \
  --hidden-import win32crypt \
  --hidden-import qrcode \
  main.py
```

---

## Security Features

| Feature | Implementation |
|---------|---------------|
| Password Hashing | Argon2id (memory-hard, OWASP recommended) |
| Config Encryption | Windows DPAPI (user-specific) |
| API Encryption | AES-256-GCM |
| Authentication | JWT (15-min expiration) |
| Rate Limiting | 5 login attempts/15min, 5 power actions/min |
| Replay Prevention | 5-second timestamp tolerance |
| Key Storage | DPAPI encrypted, not in portable folder |

---

## Project Structure

```
nexcontrol-client/
├── backend/                    # Python FastAPI backend
│   ├── main.py                # Server entry point
│   ├── app/                    # Application code
│   │   ├── core/              # Config, security
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   └── portable_setup.py  # Setup wizard module
│   ├── requirements.txt       # Python dependencies
│   ├── README.md             # API documentation
│   └── dist/                 # Portable executable
│       └── NexControl.exe    # Production binary (33MB)
├── frontend/                   # Quasar/Vue frontend
│   ├── src/                  # Source code
│   ├── capacitor.config.json # Mobile app config
│   └── README.md             # Frontend docs
├── PORTABLE_SERVER.md         # Portable server guide
├── README.md                  # Main documentation
├── LICENSE                    # GPLv3 license
└── setup_env.py              # Legacy setup script
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Main project documentation |
| [PORTABLE_SERVER.md](PORTABLE_SERVER.md) | Portable server guide |
| [backend/README.md](backend/README.md) | API documentation |
| [frontend/README.md](frontend/README.md) | Frontend guide |

---

## Requirements

### Portable Server (Windows)
- Windows 7 or later
- No installation required
- No dependencies to install

### Development Mode
- Python 3.8+
- Node.js 16+ (for frontend)
- Docker (optional, for container management)

---

## Mobile Apps

**Android:** APK available in releases
**iOS:** IPA available in releases (sideload with AltStore)

**Setup:**
1. Install app on mobile device
2. Open Settings → Encryption Key
3. Copy key from `AES_KEY.txt` or scan `AES_KEY_QR.png`
4. Enter server URL: `http://YOUR_PC_IP:8000`
5. Login with admin password

---

## Troubleshooting

### Server Not Starting

```powershell
# Check if another process is using port 8000
netstat -ano | findstr :8000

# Kill the process if needed
taskkill /PID <PID> /F
```

### Mobile App Can't Connect

1. **Check network:** Both devices on same WiFi
2. **Check IP:** `ipconfig | findstr IPv4`
3. **Check firewall:** Allow port 8000
4. **Test browser:** Open `http://YOUR_PC_IP:8000/docs`

### Forgot Password

```powershell
# Delete config to trigger setup wizard again
Remove-Item "$env:LOCALAPPDATA\NexControl\config.dat"
# Run NexControl.exe again
```

---

## Building from Source

### Backend (Python)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend (Vue/Quasar)

```bash
cd frontend
npm install
npm run dev      # Development
npm run build    # Production
```

### Portable Executable

```bash
cd backend
pip install pyinstaller
pyinstaller --onefile --name NexControl \
  --add-data "app;app" \
  --hidden-import passlib \
  --hidden-import argon2 \
  --hidden-import win32crypt \
  --hidden-import qrcode \
  --hidden-import cryptography \
  --hidden-import jose \
  --hidden-import customtkinter \
  --hidden-import PIL \
  --hidden-import docker \
  --hidden-import psutil \
  --hidden-import pyautogui \
  --hidden-import pystray \
  --noconfirm \
  main.py
```

---

## License

This project is licensed under the **GNU General Public License v3.0**.

**Copyright (c) 2026 Thamindu Hatharasinghe**

### Trademark Notice

The name **"NexControl"** and the project logo are trademarks of **Thamindu-Dev and Thamindu Hatharasinghe**.

Forks must:
- Keep the GPLv3 license
- Rename the project
- Remove all NexControl branding/logos
- Add their own copyright notice

---

## Support

- **Issues:** [GitHub Issues](https://github.com/Thamindu-Dev/NexControl/issues)
- **Documentation:** See README.md and PORTABLE_SERVER.md
- **Security:** Report vulnerabilities privately

---

## Changelog

### Version 1.0.0 (2026-02-12)

#### New Features
- Portable server with setup wizard
- DPAPI-encrypted config storage
- Unique keys per installation
- QR code export for mobile setup
- No .env files in portable folder
- System tray support (Windows)
- Minimize to tray functionality
- Background server operation
- Quick access menu from system tray
- Removed default password fallback

#### Security Fixes
- All critical/high vulnerabilities addressed
- Command injection protection
- Rate limiting implemented
- Argon2id password hashing
- Security audit logging
- CORS hardening
- Security headers

#### Bug Fixes
- Fixed DPAPI encryption/decryption
- Removed reload mode in production
- Fixed mobile app connectivity
- Improved error handling

---

## Credits

**Developer:** Thamindu Hatharasinghe
**License:** GNU General Public License v3.0
**Project:** https://github.com/Thamindu-Dev/NexControl

---

**End of Production Release Notes**
