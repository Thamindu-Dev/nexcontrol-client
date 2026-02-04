# NexControl Settings Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Server Configuration](#server-configuration-the-connection)
3. [Encryption Key](#encryption-key-crucial-the-env-link)
4. [Appearance Settings](#appearance-settings)
5. [Preferences](#preferences)
6. [Threshold Configuration](#threshold-configuration)
7. [Danger Zone](#danger-zone)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

The **Settings page** is the control center of NexControl. It's where you configure how the Frontend (Vue.js application) connects to and communicates with the Backend (Python/FastAPI server).

### Understanding the Architecture

NexControl consists of two separate components:

1. **Frontend**: A Vue.js web application that runs in your browser or mobile app
2. **Backend**: A Python FastAPI server (`main.py`) that runs on the PC you want to control

These two components communicate over HTTP/WebSocket, and the Settings page is where you tell the Frontend **how to find** and **how to authenticate** with the Backend.

> 💡 **Key Concept**: The Frontend and Backend are independent. You can run the Frontend on any device (phone, tablet, another PC) and control the Backend remotely as long as they're on the same network.

---

## Server Configuration (The Connection)

The Server Configuration section tells the Frontend **where** to find the Backend server.

### Protocol

Currently, NexControl uses **HTTP** (not HTTPS).

- **HTTP**: Unencrypted connection (suitable for local/home networks)
- **HTTPS**: Encrypted connection (planned for future versions)

> ⚠️ **Security Note**: HTTP is fine for local networks, but avoid exposing NexControl to the public internet without proper authentication and HTTPS.

### Server IP Address

This is the network address of the computer running the Backend (`main.py`).

#### Common Scenarios

| Scenario   | IP Address                      |
|------------|---------------------------------|
| Same Machine | `localhost` or `127.0.0.1`    |
| Local Network | `192.168.1.100` (example)   |
| Another Room  | `192.168.1.X` (find your IP) |

#### How to Find Your Backend IP Address

**Windows:**

```bash
# Open Command Prompt and type:
ipconfig

# Look for "IPv4 Address" under your network adapter
# Example: IPv4 Address. . .  . . . . . . . : 192.168.1.100
```

**Linux/Mac:**

```bash
# Open Terminal and type:
ip addr show
# or
ifconfig

# Look for "inet" address
# Example: inet 192.168.1.100
```

### Port

The **Port** is the communication channel the Backend server listens on.

- **Default**: `8000`
- **Custom**: If you modified the port in `main.py`, enter it here

> 📝 **Note**: The port in Settings must match the port configured in the Backend's `main.py` file.

#### Example Connection String

```text
http://192.168.1.100:8000
```

Broken down:

- `http://` → Protocol
- `192.168.1.100` → Server IP
- `8000` → Port

---

## Encryption Key (Crucial - The .env Link)

This is the **most critical section** of the Settings page. It ensures that only authorized clients can control your PC.

### How Encryption Works

NexControl uses **AES-256 Encryption** to secure all commands sent between the Frontend and Backend:

1. Frontend encrypts commands using the **AES Key**
2. Backend receives and decrypts commands using the **same AES Key**
3. If keys match → Command executes
4. If keys don't match → Command rejected (401 Unauthorized)

### The Backend .env File

The Backend stores its encryption key in a file named `.env` in the root directory of the backend project.

#### Example `.env` file

```env
# NexControl Backend Environment Variables

# AES Encryption Key (MUST be 32+ characters)
# CHANGE THIS TO A SECURE RANDOM STRING
AES_KEY=your-very-secure-32-character-aes-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Other settings...
DEBUG=false
```

### ⚠️ CRITICAL WARNING: KEYS MUST MATCH

> **The AES Encryption Key entered in the Settings page MUST BE IDENTICAL to the `AES_KEY` in the backend's `.env` file.**

#### What Happens If Keys Don't Match

| Symptom                        | Cause                          |
|--------------------------------|--------------------------------|
| "401 Unauthorized" errors      | Keys don't match               |
| "Decryption failed" in console | Keys don't match               |
| Commands execute but return errors | Backend can't decrypt requests |
| Login/authentication failures   | Keys mismatch                  |

#### Example: Correct Setup

**Backend `.env` file:**

```env
AES_KEY=my-super-secret-key-1234567890abc
```

**Settings Page → Encryption Key:**

```text
my-super-secret-key-1234567890abc
```

✅ **Result**: Connection successful, commands work

#### Example: Incorrect Setup

**Backend `.env` file:**

```env
AES_KEY=my-super-secret-key-1234567890abc
```

**Settings Page → Encryption Key:**

```text
different-key-here-xyz
```

❌ **Result**: All commands fail with 401 Unauthorized

### Key Requirements

- **Minimum Length**: 32 characters
- **Recommended**: 64 characters (more secure)
- **Characters**: Letters, numbers, symbols allowed
- **No Spaces**: Avoid spaces in the key
- **Case Sensitive**: `ABC` ≠ `abc`

### How to Generate a Secure Key

#### Option 1: Use Python (Backend)

```python
import secrets
print(secrets.token_urlsafe(32))
```

#### Option 2: Use OpenSSL

```bash
openssl rand -base64 32
```

#### Option 3: Use a Password Manager

Generate a random 32-character password.

### Changing the Encryption Key

If you want to change the encryption key:

1. **Backend**: Edit `.env` file and change `AES_KEY`
2. **Restart Backend**: Stop and restart `main.py`
3. **Frontend**: Go to Settings → Encryption Key → Enter new key → Save

> 💡 **Tip**: Both Frontend and Backend must be updated to use the new key, or communication will fail.

---

## Appearance Settings

Customize the visual appearance of the NexControl interface.

### Dark Mode

Toggle between light and dark themes.

- **Enabled**: Dark background, light text (OLED-friendly)
- **Disabled**: Light background, dark text

> **Recommendation**: Dark mode is optimized for OLED screens and reduces eye strain in low-light environments.

### Follow System

Automatically switch between light/dark mode based on your device's system settings.

- **Enabled**: Matches your OS theme (e.g., switches at sunset)
- **Disabled**: Uses manual selection

---

## Preferences

### Auto-Connect on Start

When enabled, the Frontend will automatically connect to the Backend when you open the app.

- **Enabled**: Quick access, no manual connection needed
- **Disabled**: You must manually connect (useful if you have multiple servers)

> ⚠️ **Note**: Requires valid Server Configuration and Encryption Key to work.

### Polling Interval

Controls how often the Frontend asks the Backend for system stats updates.

| Interval      | Use Case                  | Pros                 | Cons                  |
|---------------|---------------------------|----------------------|-----------------------|
| 2 seconds     | Gaming, real-time         | Most responsive      | Higher battery usage  |
| 5 seconds     | General use               | Balanced             | Moderate battery usage|
| 10 seconds    | Background monitoring     | Lower battery usage  | Less responsive       |
| 30 seconds    | Long-term monitoring      | Lowest battery usage | Very slow updates     |

#### Technical Explanation

```text
Polling Interval = How often Frontend says "Backend, send me CPU/RAM/Disk stats"

Example: 5 seconds
- Every 5 seconds, Frontend requests: GET /api/stats/all
- Backend responds with: { cpu: 45%, memory: 62%, disk: 78% }
- Frontend updates Dashboard charts
```

> 💡 **Battery Tip**: On mobile devices, use 10-30 second intervals to conserve battery. On desktop, use 2-5 seconds for real-time updates.

---

## Threshold Configuration

Thresholds are **usage limits** that trigger alerts when system resources exceed safe levels.

### Enable Threshold Monitoring

Toggle this ON to activate threshold alerts.

### Threshold Sliders

Three sliders control alert triggers:

1. **CPU Alert** (Default: 80%)
   - Triggers when CPU usage exceeds this value
   - Example: Set to 90% to get alerts when CPU is nearly maxed out

2. **Memory Alert** (Default: 85%)
   - Triggers when RAM usage exceeds this value
   - Example: Set to 90% for systems with lots of RAM

3. **Disk Alert** (Default: 90%)
   - Triggers when disk usage exceeds this value
   - Example: Set to 95% to get early warning before disk is full

#### How Alerts Work

```text
Frontend checks stats every 5 seconds (Polling Interval)

If CPU > 80% (threshold):
  → Show notification: "⚠️ CPU Usage is at 85% (Threshold: 80%)"
  → Play alert sound (if enabled)
  → Log alert to history

Next alert won't show for 5 minutes (cooldown period)
```

### Alert Cooldown

To prevent notification spam, alerts have a **5-minute cooldown**:

- If threshold exceeded at 10:00 AM → Alert shown
- If still exceeded at 10:01 AM → No alert (wait until 10:05 AM)

### Recommended Thresholds

| System Type | CPU  | Memory | Disk |
|-------------|------|--------|------|
| Gaming PC   | 90%  | 90%    | 95%  |
| Work PC     | 80%  | 85%    | 90%  |
| Server      | 70%  | 80%    | 85%  |

---

## Danger Zone

⚠️ **Caution**: Actions in this section cannot be easily undone.

### Clear Saved Credentials

Removes all saved connection data from your device:

- ❌ Server IP address
- ❌ Encryption key
- ❌ Auto-connect preference
- ❌ Theme settings

**When to use this:**

- Switching to a different backend server
- Selling/giving away your device
- Troubleshooting connection issues

**Effect:** You'll need to re-enter all settings on next use.

### Reset All Settings

Resets **all** settings to their default values:

- Server: `localhost:8000`
- Protocol: `HTTP`
- Encryption Key: (empty)
- Polling Interval: `5000ms` (5 seconds)
- Thresholds: CPU 80%, Memory 85%, Disk 90%
- Theme: Dark mode enabled

**When to use this:**

- Settings are corrupted
- Starting fresh
- Complete configuration reset

> 💡 **Note**: This does NOT affect the Backend `.env` file or server settings. It only resets the Frontend.

---

## Troubleshooting

### "401 Unauthorized" Error

**Cause**: Encryption key mismatch

**Solution**:

1. Check Backend `.env` file for `AES_KEY`
2. Go to Settings → Encryption Key
3. Enter the EXACT same key
4. Save

### "Connection Refused" Error

**Cause**: Wrong IP address or port

**Solution**:

1. Verify Backend is running (`main.py` is started)
2. Check IP address matches Backend PC's local IP
3. Verify port is `8000` (or custom port if changed)
4. Test connection in browser: `http://<IP>:8000/docs`

### "Decryption Failed" Error

**Cause**: Frontend and Backend using different encryption keys

**Solution**:

1. Open Backend `.env` file
2. Copy the `AES_KEY` value
3. Paste into Settings → Encryption Key
4. Save and retry

### Threshold Alerts Not Showing

**Cause**: Threshold monitoring is disabled

**Solution**:

1. Go to Settings → Threshold Configuration
2. Enable "Enable Threshold Monitoring" toggle
3. Set desired threshold levels
4. Save Threshold Settings

### Stats Not Updating

**Cause**: Polling interval too long or auto-refresh disabled

**Solution**:

1. Check Settings → Preferences → Polling Interval
2. Set to 5 seconds or less
3. Refresh page
4. Check browser console for errors

---

## Quick Reference

### Minimal Setup (First Time)

1. **Server IP**: Enter Backend PC's IP (e.g., `192.168.1.100`)
2. **Port**: Keep `8000` (default)
3. **Encryption Key**: Copy `AES_KEY` from Backend `.env` file
4. **Save Server Config**
5. **Save Encryption Key**

### Recommended Settings

| Setting           | Recommended Value              |
|-------------------|--------------------------------|
| Protocol          | HTTP                           |
| Server IP         | Your Backend PC's local IP     |
| Port              | 8000                           |
| Polling Interval  | 5000ms (5 seconds)             |
| CPU Threshold     | 80%                            |
| Memory Threshold  | 85%                            |
| Disk Threshold    | 90%                            |
| Theme             | Dark Mode                      |
| Auto-Connect      | Enabled (for personal device)  |

---

## Security Best Practices

1. **Never expose your Backend to the public internet** without HTTPS and strong authentication
2. **Use a strong AES key** (32+ random characters)
3. **Change the default AES key** before deploying
4. **Keep your Encryption key private** - don't share it
5. **Use local network only** when possible (192.168.x.x range)
6. **Disable auto-connect** on shared devices
7. **Clear credentials** before selling/giving away your device

---

## Additional Resources

- [Backend Documentation](./backend/README.md)
- [API Documentation](http://localhost:8000/docs) (when backend is running)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [GitHub Repository](https://github.com/your-repo/nexcontrol)

---

**Last Updated**: 2026-01-04
**Version**: 1.0.0
**Maintained By**: NexControl Development Team
