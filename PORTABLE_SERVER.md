# NexControl Portable Server Guide

This guide explains how to use the **NexControl Portable Server** - a standalone Windows executable that requires no installation.

---

## Features

| Feature | Description |
|---------|-------------|
| **Single File** | One .exe file, no dependencies or installation |
| **Setup Wizard** | GUI-based first-run configuration |
| **DPAPI Encryption** | Config encrypted with Windows Data Protection API |
| **Unique Keys** | AES and SECRET keys auto-generated per installation |
| **QR Code Export** | Scan with mobile app for instant setup |
| **Secure Storage** | Config stored in Windows AppData (not in portable folder) |

---

## Quick Start

### 1. Download and Run

```powershell
# Download NexControl.exe
# Double-click to run, or:
.\NexControl.exe
```

### 2. Setup Wizard (First Run Only)

The first time you run NexControl, a setup wizard will appear:

1. **Create Admin Password** (12+ characters recommended)
   - This is the password you'll use to login
   - Stored securely using Argon2id hashing

2. **Key Generation** (Automatic)
   - AES_KEY: 32 bytes, used for API encryption
   - SECRET_KEY: 32 bytes, used for JWT signing
   - Both keys are unique per installation

3. **Export Files Created**
   - `AES_KEY.txt` - Copy this key to your mobile app
   - `AES_KEY_QR.png` - Scan this QR code with your phone
   - `SETUP_INSTRUCTIONS.txt` - Setup guide

4. **Config Location**
   - Windows AppData: `%LOCALAPPDATA%\NexControl\config.dat`
   - Encrypted with DPAPI (tied to your Windows user account)

### 3. Server Starts Automatically

After setup, the server starts immediately:
- **Web Interface:** http://localhost:8000
- **API:** http://localhost:8000/api
- **Docs:** http://localhost:8000/docs

---

## Mobile App Setup

### Step 1: Install Mobile App

Download and install NexControl mobile app:
- **Android:** Download APK from releases
- **iOS:** Download IPA (sideload with AltStore)

### Step 2: Get Your PC's IP Address

**Windows:**
```powershell
ipconfig | findstr IPv4
```

Example output: `192.168.1.100`

### Step 3: Configure Mobile App

1. **Open NexControl** on your mobile device
2. **Go to Settings**
3. **Server Configuration:**
   - IP Address: `192.168.1.100` (your PC's IP)
   - Port: `8000`
4. **Encryption Key:**
   - Open `AES_KEY.txt` on your PC
   - Copy the key
   - Paste in mobile app Settings → Encryption Key
   - OR scan `AES_KEY_QR.png` with your phone
5. **Login:** Use the admin password you created during setup

### Step 4: Connect!

- Mobile app should show "Online" status
- Dashboard loads with real-time system stats
- All features now available from your phone

---

## File Structure (After Setup)

```
portable_folder/
├── NexControl.exe              # Main executable (run this)
├── AES_KEY.txt                 # Copy to mobile app
├── AES_KEY_QR.png              # Scan with mobile app
└── SETUP_INSTRUCTIONS.txt      # Setup guide

Windows AppData/ (Config Location)
└── NexControl/
    └── config.dat               # Encrypted config (DPAPI)
```

---

## Security

### How It Works

1. **First Run Detection**
   - Checks `%LOCALAPPDATA%\NexControl\config.dat`
   - If not found → Launch setup wizard
   - If found → Load config and start server

2. **Password Storage**
   - Password hashed with **Argon2id** (memory-hard algorithm)
   - Hash stored in DPAPI-encrypted config
   - Plain-text password **never stored**

3. **Key Generation**
   - **AES_KEY:** Generated using `secrets.token_urlsafe(32)`
   - **SECRET_KEY:** Generated using `secrets.token_urlsafe(32)`
   - Both unique per installation (not shared across installs)

4. **DPAPI Encryption**
   - Config encrypted with Windows Data Protection API
   - Tied to Windows user credentials
   - Only the Windows user who created it can decrypt it
   - Protected against file theft

### Security Checklist

- ✅ No hardcoded passwords
- ✅ Unique keys per installation
- ✅ Argon2id password hashing
- ✅ DPAPI-encrypted config storage
- ✅ AES-256-GCM API encryption
- ✅ JWT token authentication (15-min expiration)
- ✅ Rate limiting (5 login attempts/15min)
- ✅ No .env files in portable folder

---

## Troubleshooting

### "Server offline" in mobile app

**Causes:**
1. Wrong IP address
2. Devices not on same network
3. Windows Firewall blocking
4. Server not running

**Solutions:**
```powershell
# 1. Check server is running
# Look for "Uvicorn running on http://0.0.0.0:8000"

# 2. Check IP address
ipconfig | findstr IPv4

# 3. Check Windows Firewall
# Allow port 8000
New-NetFirewallRule -DisplayName "NexControl" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# 4. Test from phone browser
# Open: http://YOUR_PC_IP:8000/docs
# Should see API documentation
```

### "Login failed"

**Causes:**
1. Wrong encryption key
2. Wrong password
3. Server config corrupted

**Solutions:**
```powershell
# 1. Verify encryption key matches
# AES_KEY.txt in portable folder
# Settings → Encryption Key in mobile app

# 2. Reset config (will trigger setup wizard again)
# Delete: %LOCALAPPDATA%\NexControl\config.dat
# Run NexControl.exe again
```

### Setup wizard not appearing

**Cause:** Config already exists from previous installation

**Solution:**
```powershell
# Delete existing config
Remove-Item "$env:LOCALAPPDATA\NexControl\config.dat"

# Run NexControl.exe again
.\NexControl.exe
```

---

## Advanced Usage

### System Tray Feature (Windows)

NexControl includes a system tray icon that allows you to minimize the server to the background.

**Features:**
- **Minimize to Tray** - Hide console window while server keeps running
- **Show/Hide Console** - Toggle console window visibility
- **Server Status** - View if server is running or stopped
- **Open Web Interface** - Quick launch browser to http://localhost:8000
- **Show Encryption Key** - Display your AES key (copied to clipboard)
- **Stop Server** - Stop the server without closing tray
- **Exit** - Clean shutdown of server and tray

**Usage:**
1. Run NexControl.exe
2. Look for the NexControl icon in your system tray (near the clock)
3. Right-click the icon to access all options
4. Use "Minimize to Tray" to hide the console window
5. Use "Exit" when done to properly shut down

### Running as Service (Windows)

To run NexControl as a Windows service (auto-start on boot):

1. **Create service using NSSM (recommended):**
```powershell
# Download NSSM: https://nssm.cc/download
nssm install NexControl "C:\Path\To\NexControl.exe"
nssm start NexControl
```

2. **Or use Task Scheduler:**
- Open Task Scheduler
- Create Basic Task
- Trigger: At startup
- Action: Start program
- Program: `C:\Path\To\NexControl.exe`

### Server Logging

Logs are stored in the same directory as the executable:
- `nexcontrol.log` - General server logs
- `security_audit.log` - Security events

### Updating NexControl

1. **Download new version** of NexControl.exe
2. **Replace old executable** with new one
3. **Config persists** (stored in AppData, not portable folder)
4. **Run new version** - old config works automatically

---

## Development

### Building Portable Executable

```bash
cd backend
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --onefile --name NexControl \
  --add-data "app;app" \
  --hidden-import passlib \
  --hidden-import passlib.handlers.argon2 \
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

Output: `backend/dist/NexControl.exe`

---

## FAQ

**Q: Can I move NexControl.exe to another folder?**
A: Yes! The exe is fully portable. Just move the exe - it will work anywhere.

**Q: Do I need to run setup again if I move the exe?**
A: No! Config is stored in Windows AppData, not in the portable folder.

**Q: Can I run multiple instances of NexControl?**
A: Only one per Windows PC (port 8000 conflict). To run multiple, change port in code.

**Q: Is my password safe?**
A: Yes! Password is hashed with Argon2id and never stored in plain text. Only the hash is stored (encrypted with DPAPI).

**Q: What if I forget my password?**
A: Delete `%LOCALAPPDATA%\NexControl\config.dat` and run NexControl.exe again to create new password.

**Q: Can I backup my config?**
A: Yes! Copy `%LOCALAPPDATA%\NexControl\config.dat` to backup location. **Note:** It's encrypted with DPAPI and tied to your Windows user account.

---

## Support

For issues or questions:
- [GitHub Issues](https://github.com/Thamindu-Dev/NexControl/issues)
- [Documentation](../README.md)

---

**Version:** 1.0.0
**Last Updated:** 2026-02-12
**License:** GPL v3
