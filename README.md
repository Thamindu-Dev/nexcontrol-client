##
 NexControl - Remote PC Controller
 Copyright (C) 2026 Thamindu Hatharasinghe

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
##

<div align="center">

![NexControl Logo](docs/logo.png)

# NexControl - Remote PC Controller

**A secure, open-source local network PC controller for system administrators and engineering students**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Security](https://img.shields.io/badge/Security-LOW%20RISK-green.svg)](https://github.com/Thamindu-Dev/NexControl)

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Security](#security) • [License](#license)

**Version:** 1.0.0 | **Last Updated:** 2026-02-12

</div>

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
  - [Option 1: Portable Executable (Recommended)](#option-1-portable-executable-recommended)
  - [Option 2: Development Mode](#option-2-development-mode)
- [Mobile App Setup](#mobile-app-setup)
- [Documentation](#documentation)
- [Security](#security)
- [Building from Source](#building-from-source)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

---

## Overview

**NexControl** is a secure, local network Remote PC Controller designed for engineering students and system administrators. It provides a modern web interface and mobile apps (iOS/Android) for monitoring and controlling Windows/Linux PCs from your local network.

### Architecture
- **Backend:** Python FastAPI (RESTful API + WebSocket support)
- **Frontend:** Quasar Framework (Vue 3 + Vite SPA)
- **Mobile:** Capacitor (iOS & Android native apps)
- **Portable Server:** PyInstaller-based standalone executable
- **Security:** AES-256-GCM encryption + Argon2id password hashing + JWT auth

### Why NexControl?
- 🔒 **Secure** - All sensitive data encrypted with AES-256-GCM
- 📱 **Mobile Apps** - Native iOS and Android applications
- 🖥️ **Portable** - Single executable, no installation required
- 🎨 **Modern UI** - OLED-optimized dark mode with real-time stats
- 🛡️ **Production-Ready** - Comprehensive security audit completed
- 📜 **Open Source** - GPL v3 licensed, fully auditable codebase

---

## Features

### System Monitoring
- ✅ Real-time CPU usage with per-core statistics
- ✅ Memory usage (used/total/percentage)
- ✅ Disk usage for all drives (includes USB/external)
- ✅ GPU temperature (NVIDIA support)
- ✅ Network I/O statistics
- ✅ Historical data visualization (Chart.js)
- ✅ WebSocket real-time updates

### Power Management
- ✅ Shutdown with configurable delay (0-3600s)
- ✅ Restart PC
- ✅ Hibernate/Sleep support
- ✅ Lock screen
- ✅ Scheduled power actions (cron-like scheduler)

### Docker Management
- ✅ List all containers with status
- ✅ Start/Stop/Restart containers
- ✅ View container logs with auto-scroll
- ✅ Graceful handling when Docker unavailable

### Process Management
- ✅ Sortable process list (by CPU/Memory)
- ✅ Kill processes with confirmation
- ✅ Protected PIDs (system processes)
- ✅ Platform-specific validation

### Additional Features
- ✅ Remote screenshot capture
- ✅ Wake-on-LAN (WoL) with device management
- ✅ Threshold notifications (CPU/Memory/Disk alerts)
- ✅ Biometric authentication (TouchID/FaceID) framework
- ✅ OLED dark mode (cyan/red/orange accents)
- ✅ App launcher with predefined/custom applications
- ✅ Clipboard synchronization
- ✅ Media player controls

---

## Quick Start

### Option 1: Portable Executable (Recommended)

#### For Windows Users

1. **Download the portable executable**
   ```bash
   NexControl.exe  # Single file, no installation required
   ```

2. **Run the setup wizard** (first run only)
   ```powershell
   .\NexControl.exe
   ```

3. **Follow the setup wizard:**
   - Create admin password (12+ characters recommended)
   - AES key and secret key auto-generated per installation
   - AES key exported to `AES_KEY.txt` and `AES_KEY_QR.png`
   - Config stored securely in Windows AppData (DPAPI encrypted)

4. **Access the web interface**
   - **From PC:** http://localhost:8000
   - **From Mobile:** http://YOUR_PC_IP:8000

5. **Configure Mobile App**
   - Open NexControl mobile app
   - Go to Settings → Encryption Key
   - Enter the key from `AES_KEY.txt` or scan `AES_KEY_QR.png`
   - Enter server URL: `http://YOUR_PC_IP:8000`
   - Login with your admin password

#### Portable Server Features

| Feature | Description |
|---------|-------------|
| **Single Executable** | No installation, no dependencies |
| **Setup Wizard** | GUI-based first-run configuration |
| **DPAPI Encryption** | Config tied to Windows user credentials |
| **Unique Keys** | Each installation generates unique AES/SECRET keys |
| **QR Code Export** | Scan with mobile app for easy setup |
| **System Tray** | Minimize to tray, background operation |
| **No .env Files** | Config stored securely in AppData |

**System Tray Options:**
- Minimize to Tray - Hide console while server runs in background
- Show/Hide Console - Toggle console window
- Server Status - View running state
- Open Web Interface - Quick browser launch
- Show Encryption Key - Display AES key
- Stop Server - Stop without closing tray
- Exit - Clean shutdown

### Option 2: Development Mode

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend runs on: http://localhost:8000

#### Frontend Setup (Development)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:9000

---

## Mobile App Setup

### Download Mobile Apps

- **Android:** Download APK from [Releases](../../releases)
- **iOS:** Download IPA from [Releases](../../releases) (sideload with AltStore)

### Configure Mobile App

1. **Install the app** on your mobile device
2. **Open Settings**
3. **Server Configuration:**
   - IP Address: Your PC's local IP (e.g., 192.168.1.100)
   - Port: 8000
4. **Encryption Key:**
   - Copy from `AES_KEY.txt` (generated during setup)
   - Or scan `AES_KEY_QR.png` with your phone camera
5. **Login:** Use the admin password you created during setup

### Finding Your PC's IP

**Windows:**
```powershell
ipconfig | findstr IPv4
```

**Linux/Mac:**
```bash
ip addr show | grep inet
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [backend/README.md](backend/README.md) | Backend API documentation |
| [frontend/README.md](frontend/README.md) | Frontend development guide |
| [PORTABLE_SERVER.md](PORTABLE_SERVER.md) | Portable server setup guide |
| [SECURITY_AUDIT.md](SECURITY_AUDIT.md) | Security audit report |

---

## Security

### Security Posture

**Risk Level:** 🟢 **LOW** (All critical/high vulnerabilities fixed)

### Implemented Security Measures

| Feature | Implementation |
|---------|---------------|
| **Encryption** | AES-256-GCM for all API requests |
| **Authentication** | JWT tokens (15-min expiration) |
| **Password Hashing** | Argon2id (memory-hard, OWASP recommended) |
| **Rate Limiting** | 5 power actions/min, 5 login attempts/15min |
| **Replay Prevention** | 5-second timestamp tolerance |
| **Input Validation** | Path traversal protection, command injection prevention |
| **CORS** | Explicit origins + local network detection |
| **Security Headers** | CSP, X-Frame-Options, HSTS |
| **Audit Logging** | All security events logged |
| **Key Storage** | DPAPI encrypted (Windows) |

### Default Credentials

⚠️ **IMPORTANT:** The setup wizard generates unique credentials per installation.

| Setting | Default | Notes |
|---------|---------|-------|
| Admin Password | User-defined | Set during setup wizard |
| AES Key | Auto-generated | 32 bytes, unique per installation |
| Secret Key | Auto-generated | 32 bytes, unique per installation |

### Production Checklist

Before deploying to production:

- [x] Generate unique AES/SECRET keys per installation
- [x] Strong admin password required
- [x] No hardcoded credentials
- [x] Rate limiting enabled
- [x] Security headers implemented
- [x] Input validation on all endpoints
- [x] Audit logging enabled
- [x] CORS properly configured
- [x] TLS encryption for API communication
- [ ] VPN for remote access (recommended)

---

## Building from Source

### Backend (Python)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Portable Executable

```bash
cd backend
pip install pyinstaller
pyinstaller --onefile --name NexControl \
  --add-data "app;app" \
  --hidden-import passlib \
  --hidden-import passlib.handlers.argon2 \
  --hidden-import argon2 \
  --hidden-import win32crypt \
  --hidden-import qrcode \
  --hidden-import pystray \
  --hidden-import cryptography \
  --hidden-import jose \
  --hidden-import customtkinter \
  --hidden-import PIL \
  --hidden-import docker \
  --hidden-import psutil \
  --hidden-import pyautogui \
  --noconfirm \
  main.py
```

Output: `backend/dist/NexControl.exe`

### Frontend (Web)

```bash
cd frontend
npm install
npm run build    # Production build
npm run dev      # Development server
```

### Mobile Apps

```bash
cd frontend
npm install
npm run build
npm run cap:sync
npm run cap:build android    # Opens Android Studio
npm run cap:build ios        # Opens Xcode
```

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Code Style:** Follow PEP 8 for Python, ESLint for JavaScript
2. **Commits:** Clear commit messages with issue references
3. **Testing:** Test all changes before submitting PRs
4. **Security:** Report security vulnerabilities privately

### Development Setup

```bash
git clone https://github.com/Thamindu-Dev/NexControl.git
cd NexControl

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

---

## License & Copyright

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License v3.0**.

**Copyright (c) 2026 Thamindu Hatharasinghe**

### Trademark Notice

> **Note:** The name **"NexControl"** and the project logo are trademarks of **Thamindu-Dev and Thamindu Hatharasinghe**. While the source code is open-source (GPLv3), you may not use this name or logo in derivative works (forks) without explicit permission.

For forks, please:
- Keep the GPLv3 license
- Rename your project to avoid confusion
- Remove all NexControl branding/logos
- Add your own copyright notice

---

## Support

### Documentation

- [Backend API Docs](backend/README.md)
- [Frontend Guide](frontend/README.md)
- [Portable Server Guide](PORTABLE_SERVER.md)

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/Thamindu-Dev/NexControl/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Thamindu-Dev/NexControl/discussions)
- **Security:** Report security issues privately via email

### Troubleshooting

**Common Issues:**

1. **"Server offline" in mobile app**
   - Ensure both devices on same WiFi network
   - Check Windows Firewall allows port 8000
   - Verify IP address is correct

2. **"Login failed"**
   - Verify encryption key matches server
   - Check admin password is correct
   - Ensure server is running

3. **Portable exe not starting**
   - Run as Administrator
   - Check Windows Event Viewer for errors
   - Verify .NET Framework is installed

---

## Changelog

### Version 1.0.0 (2026-02-12)

#### New Features ✨
- **Portable Server:** Single executable with built-in setup wizard
- **DPAPI Encryption:** Windows Data Protection API for secure config storage
- **QR Code Export:** Scan to configure mobile app instantly
- **Unique Keys:** Auto-generated AES/SECRET keys per installation
- **No .env Files:** Config stored in AppData (portable-friendly)

#### Security Fixes ✅
- All critical and high-severity vulnerabilities addressed
- Command injection protection
- Rate limiting implemented
- Argon2id password hashing
- Security audit logging
- CORS hardening
- Security headers

#### Bug Fixes 🐛
- Fixed DPAPI encryption/decryption
- Removed reload mode in production
- Fixed mobile app connectivity issues
- Improved error handling

---

<div align="center">

**Built with ❤️ for the open-source community**

**[⬆ Back to Top](#-nexcontrol---remote-pc-controller)**

</div>
