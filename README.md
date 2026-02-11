##
 NexControl - Remote PC Controller
 Copyright (C) 2026 Thamindu Hatharasinghe

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
##

## Table of Contents
- [Overview](#overview)
- [License & Copyright](#license--copyright)
- [Features](#features)
- [Project Status](#project-status)
- [Quick Start](#quick-start)
- [Server GUI](#server-gui)
- [Documentation](#documentation)
- [Security](#security)
- [Changelog](#changelog)
- [Support](#support)

## Overview

**NexControl** is a secure, local network Remote PC Controller designed for engineering students and system administrators. It provides a modern web interface and mobile apps (iOS/Android) for monitoring and controlling Windows/Linux PCs from your local network.

**Architecture:**
- **Backend:** Python FastAPI (~3,000 lines)
- **Frontend:** Quasar Framework (Vue 3 + Vite)
- **Mobile:** Capacitor (iOS & Android apps)
- **Security:** AES-256-GCM encryption + JWT authentication
- **Server GUI:** CustomTkinter desktop application (Windows)

## License & Copyright

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.
You are free to use, modify, and distribute the code, but you must keep it open-source.

**Copyright (c) 2026 Thamindu Hatharasinghe**

> **Note on Branding:**
> While the source code is open-source, the name **"NexControl"** and the project logo are trademarks of **Thamindu-Dev and Thamindu Hatharasinghe**. You may not use this name or logo in derivative works (forks) without explicit permission. If you fork this project, please rename it to avoid confusion.

## Features

### System Monitoring
- Real-time CPU usage with core count and frequency
- Memory usage statistics with used/total/percentage
- Disk usage for all drives (including USB/external storage)
- GPU temperature (NVIDIA support)
- Network I/O statistics
- Historical data visualization with Chart.js
- WebSocket real-time stats (optional toggle)

### Power Management
- Shutdown PC with optional delay (0-3600 seconds)
- Restart PC with optional delay
- Hibernate PC
- Lock PC
- Schedule power actions (create, edit, delete, enable/disable)

### Docker Management
- List all containers with status
- Start/Stop/Restart containers
- View container logs with auto-scroll
- Graceful handling when Docker unavailable

### Process Management
- Sortable process list (by CPU/Memory)
- Kill processes with confirmation
- Protected PIDs (system processes)
- Platform-specific PID validation
- Process ownership checking

### Additional Features
- Remote screenshot capture
- Wake-on-LAN (WoL) support with device management
- Threshold notifications (CPU/Memory/Disk alerts)
- Biometric authentication framework (TouchID/FaceID)
- OLED dark mode with cyan/red/orange accents
- App launcher with predefined and custom applications
- Clipboard synchronization
- Media player controls

### Security Features ✅
- **AES-256-GCM encryption** for all sensitive requests
- **JWT authentication** with 15-minute expiration
- **argon2** password hashing (memory-hard algorithm)
- **Replay attack prevention** (5-second timestamp tolerance)
- **Rate limiting** (5 power actions/minute, 5 login attempts lockout)
- **Command injection protection** (no shell=True, validated paths)
- **Input sanitization** and validation
- **Security audit logging** (security_audit.log)
- **CORS configuration** for local network + mobile apps
- **Security headers** (CSP, X-Frame-Options, HSTS)

## Project Status

| Component | Status | Completion |
|-----------|--------|------------|
| **Backend** | ✅ Complete | 100% |
| **Frontend Web** | ✅ Complete | 100% |
| **iOS App** | ✅ Complete | 100% |
| **Android App** | ✅ Complete | 100% |
| **Server GUI** | ✅ Complete | 100% |
| **Security Fixes** | ✅ Complete | 100% |
| **Documentation** | ✅ Complete | 95% |

**Overall Project Completion: ~98%**

**Security Status:** 🟢 **LOW RISK** - All critical and high-severity vulnerabilities fixed

## Quick Start

### Prerequisites
- Python 3.8+ (backend)
- Node.js 16+ (frontend)
- Docker (optional, for container management)

### Option 1: Server GUI (Recommended for Windows)

1. **Download the latest release** or build from source
2. **Run the executable:** `NexControlServer.exe`
3. **Click "Start Server"** in the GUI
4. **Access the web interface** at http://localhost:8000

**Server GUI Features:**
- Start/Stop server with one click
- View real-time server logs
- System tray support (minimize to tray)
- Auto-start on startup (optional)
- Open dashboard directly from GUI

**Server GUI Features:**
- Start/Stop server with one click
- View real-time server logs
- System tray support (minimize to tray)
- Auto-start on startup (optional)
- Open dashboard directly from GUI

### Option 2: Command Line

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python main.py
```

Backend will run on: http://localhost:8000

#### Frontend Setup (Web Dev)

```bash
cd frontend
npm install
npm run dev
```

Web app will run on: http://localhost:9000

#### Building the Server GUI

```bash
cd backend
python build_server_gui.py
# Exe will be in: backend/dist/NexControlServer.exe
```

### Mobile App Build

```bash
cd frontend
npm install
npm run build
npm run cap:sync
npm run cap:build ios    # Opens Xcode
npm run cap:build android # Opens Android Studio
```

See [frontend/README.md](frontend/README.md) for mobile build instructions.

## Server GUI

The NexControl Server GUI provides an easy-to-use desktop interface for managing the backend server on Windows.

**Features:**
- **One-click Start/Stop:** Launch the server with a single button
- **Real-time Logs:** View server logs directly in the GUI
- **System Tray:** Minimize to system tray, run in background
- **Status Indicators:** Visual feedback for server state
- **Dashboard Link:** Quick access to web interface
- **Cache Management:** Clear logs and build artifacts
- **Environment Setup:** Quick access to setup_env.py

**Building the GUI:**
```bash
cd backend
python build_server_gui.py
```

See [backend/README.md](backend/README.md) for API documentation.

## Documentation

- [backend/README.md](backend/README.md) - Backend API documentation
- [frontend/README.md](frontend/README.md) - Frontend development guide

## Security

### Security Posture

**Current Risk Level:** 🟢 **LOW**

**All Critical & High Severity Issues Fixed:**
- ✅ Command injection vulnerabilities
- ✅ CORS wildcard configuration
- ✅ Rate limiting on power actions
- ✅ Strong password hashing (argon2)
- ✅ Platform-specific PID validation
- ✅ Container ID path traversal prevention
- ✅ MAC address validation (no broadcast/multicast)
- ✅ Security headers implementation
- ✅ Password timing attack prevention
- ✅ Memory leak fixes

### Production Deployment Checklist

Before deploying to production:

- [ ] Generate new strong AES/SECRET keys (43+ random characters)
- [ ] Set strong admin password via environment variable
- [ ] Set `ENVIRONMENT=production` in .env
- [ ] Review `ALLOWED_ORIGINS` for your network
- [ ] Ensure `.env` is in `.gitignore` and NOT committed
- [ ] Set up log rotation for `security_audit.log` and `nexcontrol.log`
- [ ] Test all authentication flows
- [ ] Verify rate limiting works
- [ ] For remote access: Set up VPN (WireGuard recommended)

### Key Generation

Generate secure keys for production:

```python
import secrets
# Generate 43+ character keys
AES_KEY = secrets.token_urlsafe(32)
SECRET_KEY = secrets.token_urlsafe(32)
print(f"AES_KEY={AES_KEY}")
print(f"SECRET_KEY={SECRET_KEY}")
```

### Default Credentials

⚠️ **IMPORTANT:** Change default password before production!

| Credential | Default Value | Location |
|------------|---------------|----------|
| **App Password** | `admin123` | backend/.env |
| **Secret Key** | Auto-generated | backend/.env (32+ chars) |
| **AES Key** | Auto-generated | backend/.env (32 chars) |

Security audit completed - all critical and high-severity vulnerabilities fixed.

## Changelog

### Version 1.0.0 (2026-02-11)

#### Security Fixes ✅
- **Command Injection:** Removed all `shell=True`, added path validation
- **CORS:** Custom middleware with explicit origins + local network detection
- **Rate Limiting:** 5 power actions/minute per IP
- **Session Timeout:** Reduced from 60 to 15 minutes
- **Timestamp Tolerance:** Reduced from 30 to 5 seconds
- **Password Hashing:** Upgraded to argon2 (memory-hard)
- **Timing Attack:** Added constant-time delay to password verification
- **Key Validation:** Added entropy checks for AES keys
- **Security Logging:** New `security_audit.log` for all sensitive actions
- **Security Headers:** CSP, X-Frame-Options, HSTS implemented
- **Memory Leaks:** Added cleanup functions for login attempts and power actions

#### Bug Fixes ✅
- **Scheduler Race Conditions:** Added asyncio.Lock for thread-safety
- **PID Validation:** Platform-specific max PID checks (Windows: 4M, macOS: 99K, Linux: 32K)
- **Process Ownership:** Users can only kill their own processes
- **Container Validation:** Path traversal prevention
- **MAC Address:** Rejects broadcast and multicast addresses
- **Disabled Tasks:** Now preserved instead of deleted
- **Timezone Handling:** Verified UTC consistency
- **CORS Preflight:** Added 1-hour caching
- **Verbose Errors:** Hide details in production mode

#### New Features ✨
- **Server GUI:** Desktop application for easy server management
- **Security Audit:** Comprehensive security report with all fixes documented
- **Clipboard Sync:** Synchronize clipboard between devices
- **App Launcher:** Launch predefined or custom applications
- **Media Player Controls:** Control media playback remotely

#### UI Improvements 🎨
- **OLED Dark Mode:** Cyan/red/orange color scheme
- **Threshold Alerts:** Visual notifications for system thresholds
- **Glassmorphism:** Modern UI design on login and dashboard
- **Responsive Layout:** Fixed card alignment and spacing

### Previous Versions

All features and bug fixes implemented in v1.0.0 are documented above.

## Support

For issues, questions, or contributions:
- See [backend/README.md](backend/README.md) for API documentation
- See [frontend/README.md](frontend/README.md) for frontend development
- Ensure you're on the same local network as the target PC
- Check `nexcontrol.log` and `security_audit.log` for debugging

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE](LICENSE) file for full text.

---

**Version:** 1.0.0
**Last Updated:** 2026-02-11
**Project Completion:** ~98%
**Security Status:** 🟢 LOW RISK
