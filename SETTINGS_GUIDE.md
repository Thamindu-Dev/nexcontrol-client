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

#### Option 1: Use the Automated Setup Script (Recommended)

NexControl includes a convenient setup script that generates both the `AES_KEY` and `APP_PASSWORD_HASH` automatically.

**Usage:**

```bash
# From the project root directory
python setup_env.py
```

**What the script does:**

1. ✅ Prompts you to enter a new admin password (with confirmation)
2. ✅ Generates a secure 32-byte AES key using `secrets.token_urlsafe(32)`
3. ✅ Hashes your admin password using bcrypt (12 rounds)
4. ✅ Updates `backend/.env` with the new values
5. ✅ Preserves all other existing settings in the `.env` file
6. ✅ Displays the AES_KEY clearly for you to copy to the mobile app
7. ✅ Offers to delete itself after use (prevents accidental resets)

**Output Example:**

```
🔧 NexControl Environment Setup
============================================================
Target: /path/to/backend/.env

------------------------------------------------------------
Step 1/2: Admin Password
------------------------------------------------------------
This password will be used to login to the NexControl backend.
Choose a strong password (12+ characters recommended).

Enter new admin password: ********
Confirm password: ********

------------------------------------------------------------
Step 2/2: Generate Credentials
------------------------------------------------------------
🔄 Generating secure AES_KEY...
✅ Generated 32-byte AES key
🔄 Hashing admin password...
✅ Password hashed (bcrypt, 12 rounds)

------------------------------------------------------------
Step 3/3: Update .env File
------------------------------------------------------------
✅ Updated: /path/to/backend/.env

============================================================
📱 Copy This Key to Your Mobile App
============================================================

⚠️  IMPORTANT: Copy this key and enter it in the NexControl
   mobile app Settings → Encryption Key

   ┌─────────────────────────────────────────────────────┐
   │ Xy9...generatedKey...3Ab │
   └─────────────────────────────────────────────────────┘

💡 Tip: You can also find this key in backend/.env file
   under the 'AES_KEY' variable.
```

**After running the script:**

1. **Backend**: Restart the backend to load the new credentials
2. **Frontend**: Copy the displayed `AES_KEY` and paste it in Settings → Encryption Key
3. **Login**: Use the admin password you just set to login

> 🔒 **Security**: The script offers to delete itself after use to prevent accidental credential resets. You can always recreate it from the repository if needed.

---

#### Option 2: Use Python Manual (Backend)

```python
import secrets
print(secrets.token_urlsafe(32))
```

#### Option 3: Use OpenSSL

```bash
openssl rand -base64 32
```

#### Option 4: Use a Password Manager

Generate a random 32-character password.

### Changing the Encryption Key

If you want to change the encryption key:

**Option 1: Use the Setup Script (Recommended)**

1. Run `python setup_env.py` from the project root
2. Enter a new admin password when prompted
3. Copy the displayed AES_KEY to your mobile app
4. Restart the backend to load new credentials

**Option 2: Manual Update**

1. **Backend**: Edit `.env` file and change `AES_KEY`
2. **Restart Backend**: Stop and restart `main.py`
3. **Frontend**: Go to Settings → Encryption Key → Enter new key → Save

> 💡 **Tip**: Both Frontend and Backend must be updated to use the new key, or communication will fail.

### Write-Only Security Feature

> 🔒 **Security Feature**: The Encryption Key input field is "write-only" for maximum protection against "shoulder surfing" (someone looking over your shoulder).

**How It Works:**

1. **Hidden Value**: Once you save a key, the input field will NOT display it
   - Shows: `******** - Saved for security` or `(Key Saved - Hidden for Security)`
   - Shows: 🔒 (green lock icon) when a key is configured

2. **No Readback**: You can never view the saved key in the UI
   - Prevents accidental exposure
   - Protects against screen capture/recording
   - Safe even if someone opens Settings while you're away

3. **Update Key**: To change the key, just click the field and type a new one
   - The old key is immediately replaced
   - Empty input won't overwrite the existing key (prevents accidental deletion)

> ⚠️ **Important**: If you forget your key, you must check the backend's `.env` file or clear all settings.

---

### Pre-Flight Security Validation

> 🛡️ **Pre-Flight Check**: The Frontend validates the encryption key BEFORE sending any command to the backend.

**Protected Actions:**
- ❌ No Shutdown/Lock/Restart command without key
- ❌ No Docker operations without key
- ❌ No Process management without key
- ❌ No Screenshot capture without key
- ✅ Can view System Stats (read-only, no key needed initially)

**Security Flow:**

```
User clicks "Shutdown"
  ↓
Frontend checks: Is AES Key configured?
  ↓
NO → Block immediately
     → Show: "⚠️ Security Key Missing. Please configure it in Settings."
     → Redirect to /settings
  ↓
YES → Encrypt command with AES Key
  ↓
Send to Backend
  ↓
Backend validates AES Key
  ↓
Keys Match? → Execute Command
Keys Don't Match → Return 401 Unauthorized
```

**Error Messages:**

| Error | Message | Action |
|-------|---------|--------|
| **No key** | "⚠️ Security Key Missing" | Go to Settings and configure key |
| **Wrong key** | "🚫 Authentication Failed. Check your Encryption Key." | Verify key matches backend `.env` file |
| **Decryption error** | "🚫 Authentication Failed. Check your Encryption Key." | Key mismatch detected |

> 💡 **Why This Matters**: Even if someone gains access to your device, they cannot control your PC without knowing the encryption key.

---

### Backend Validation

The NexControl backend performs strict validation on **every encrypted request**:

#### 1. Decryption Guard

The backend wraps all decryption attempts in a `try-except` block:

```python
# Backend decrypts the payload
try:
    decrypted_data = decrypt_data(encrypted_payload)
    # Process command...
except CryptoError:
    # Wrong AES key detected!
    logger.warning("DECRYPTION FAILED (Invalid AES Key)")
    raise HTTPException(status_code=401, detail="Invalid Encryption Key")
```

#### 2. Verification Endpoint

A special endpoint `/api/auth/verify-key` exists to test if keys match:

**Request:**
```json
{
  "data": "<base64-encrypted-test-string>"
}
```

**Success (200):**
```json
{
  "success": true,
  "status": "valid",
  "message": "Encryption key matched successfully"
}
```

**Failure (401):**
```json
{
  "success": false,
  "status": "invalid",
  "message": "Encryption key does not match"
}
```

**When Verification Happens:**
- When you click "Save Encryption Key" in Settings
- Before allowing sensitive operations
- During connection tests

> 🔐 **Zero Trust**: The backend never trusts blindly. Every command must prove it has the correct key.

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

### "⚠️ Security Key Missing" Error

**Cause**: No encryption key configured in Settings

**Solution**:

1. Open Backend `.env` file
2. Find the `AES_KEY` line (must be 32+ characters)
3. Go to Settings → Encryption Key
4. Paste the key
5. Save

> 📝 **Note**: All commands will be blocked until a valid key is configured

### "🚫 Authentication Failed" (Wrong Key)

**Cause**: Encryption key in Settings doesn't match backend's `AES_KEY`

**Solution**:

1. Verify backend `.env` file has the correct key
2. Check for extra spaces or copy-paste errors
3. Delete key from Settings and re-enter it manually
4. Save and retry

### "Key Saved but Still Shows as Missing"

**Cause**: Browser localStorage has the key but Settings page can't detect it

**Solution**:

1. Refresh the page (Settings page uses store state that loads on mount)
2. Check browser console for: `[SettingsPage] Encryption key state after loadSettings:`
3. If still shows as missing, try clearing browser cache and reload

### Verification Tests Passed But Commands Fail

**Cause**: Key verification succeeded but actual decryption fails (unlikely)

**Solution**:

1. Check backend logs for: `[Key Verification] FAILED - Key mismatch`
2. Check frontend console for decryption errors
3. Restart backend to clear any cached encryption state

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
2. **Use a strong AES key** (32+ random characters, use a password manager)
3. **Change the default AES key** before deploying to production
4. **Keep your Encryption key private** - never share it via email, chat, or unsecured channels
5. **Use local network only** when possible (192.168.x.x range)
6. **Disable auto-connect** on shared devices
7. **Clear credentials** before selling/giving away your device

### 🔐 New Security Features (v1.1)

#### Write-Only Key Protection

- **Benefit**: Your encryption key is never displayed in the UI, even when saved
- **How it works**: The input field shows `********` when a key is configured
- **Why it matters**: Prevents "shoulder surfing" - someone looking over your shoulder can't see your key
- **Recovery**: If you forget the key, check the backend `.env` file directly

#### Pre-Flight Validation

- **Benefit**: No command is ever sent without a valid key
- **How it works**: Frontend checks for key BEFORE making API requests
- **Why it matters**: Even with your device, no one can control your PC without the key
- **Protected actions**: Shutdown, Lock, Restart, Docker, Processes, Screenshots

#### Backend Decryption Guard

- **Benefit**: Backend rejects all commands with wrong keys immediately
- **How it works**: Server uses 401 Unauthorized for decryption failures
- **Why it matters**: Double-layer protection (frontend + backend validation)
- **Error messages**: "Invalid Encryption Key" (logged with IP address)

#### Automatic Key Verification

- **Benefit**: Tests key match before allowing sensitive operations
- **How it works**: `/api/auth/verify-key` endpoint validates key when you save it
- **Why it matters**: You'll know immediately if the key is correct (200) or wrong (401)

### Security Checklist

- [ ] Key is 32+ characters (longer is better)
- [ ] Key contains letters, numbers, and symbols
- [ ] Key is stored in backend `.env` file
- [ ] Frontend Settings shows green lock icon
- [ ] Input field shows `******** - Saved for security`
- [ ] Pre-flight check allows commands to execute
- [ ] Backend logs show successful key matches
- [ ] No yellow warnings in console about missing key

---

## Advanced Security Architecture

### Defense in Depth

NexControl uses multiple layers of security to protect your PC:

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: Frontend Pre-Flight Check                          │
│ - Blocks commands before network request                   │
│ - Shows "Security Key Missing" if no key configured            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: AES-256-GCM Encryption                           │
│ - All commands encrypted before sending                    │
│ - Payload includes timestamp (replay attack prevention)      │
│ - Nonce + Authenticated Encryption (AEAD)                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: Backend Decryption Guard                          │
│ - Try-except block catches decryption failures               │
│ - Returns 401 Unauthorized immediately on wrong key           │
│ - Logs all failures with IP address                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: JWT Authentication (Optional Extra Layer)           │
│ - Token-based auth for API access                          │
│ - Token expiration (24 hours)                                │
└─────────────────────────────────────────────────────────────┘
```

### Threat Model

| Threat | Protection | Status |
|--------|------------|--------|
| **Shoulder Surfing** | Write-only input field (key never displayed) | ✅ Protected |
| **Device Theft** | Pre-flight check blocks all commands | ✅ Protected |
| **Network Sniffing** | AES-256-GCM encryption + HTTPS | ✅ Protected |
| **Replay Attacks** | Timestamp validation on all requests | ✅ Protected |
| **Wrong Key Error** | 401 Unauthorized with clear message | ✅ Protected |
| **Missing Key** | Blocks commands before sending | ✅ Protected |

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
