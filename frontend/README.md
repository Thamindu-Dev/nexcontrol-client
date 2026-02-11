# NexControl Frontend

Quasar Framework (Vue 3) frontend for the NexControl Remote PC Controller application.

## Table of Contents
- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Development](#development)
- [Building](#building)
- [Mobile Deployment](#mobile-deployment)
- [Project Structure](#project-structure)
- [Key Services](#key-services)

## Overview

Modern, responsive web application for controlling Windows/Linux PCs from a local network. Features real-time stats, OLED dark mode, and mobile apps (iOS/Android).

**Tech Stack:**
- Vue 3 Composition API
- Quasar Framework v2
- Vite
- Pinia (State Management)
- Chart.js (Data Visualization)
- Capacitor (Mobile Apps)

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Quasar** | 2.x | UI Framework |
| **Vue** | 3.x | Frontend Framework |
| **Vite** | 5.x | Build Tool |
| **Pinia** | 2.x | State Management |
| **Chart.js** | 4.x | Charts |
| **Capacitor** | 6.x | Mobile Runtime |
| **CryptoJS** | 4.x | AES Encryption |

## Features

### Pages
- **Login** - Biometric authentication, glassmorphism design
- **Dashboard** - Real-time stats, power controls, quick actions
- **Docker** - Container management with live logs
- **Processes** - Sortable process list with kill confirmation
- **Scheduled Tasks** - Create, edit, enable/disable scheduled power actions
- **Threshold Alerts** - Configure and view system threshold alerts
- **Settings** - Server configuration, AES key setup, theme toggle

### UI Components
- **OLED Dark Mode** - Cyan/red/orange accent colors
- **Real-time Stats** - WebSocket or polling (2-second interval)
- **Glassmorphism Design** - Modern frosted glass effects
- **Responsive Layout** - Mobile, tablet, desktop optimized
- **Toast Notifications** - Success/error feedback
- **Confirmation Dialogs** - Prevent accidental actions

### Security
- **AES-256-GCM Encryption** - For sensitive requests
- **JWT Authentication** - 15-minute token expiry
- **Secure Storage** - Capacitor SecureStorage for mobile
- **Biometric Auth** - TouchID/FaceID framework ready

## Architecture

### Component Structure

```
frontend/
├── src/
│   ├── layouts/           # Layout components
│   │   └── MainLayout.vue # Main app layout
│   ├── pages/             # Page components
│   │   ├── Login.vue      # Authentication
│   │   ├── Dashboard.vue  # Main dashboard
│   │   ├── Docker.vue     # Docker management
│   │   ├── Processes.vue  # Process manager
│   │   ├── ScheduledTasks.vue
│   │   └── Settings.vue
│   ├── components/        # Reusable components
│   │   ├── StatCard.vue   # Dashboard stat cards
│   │   └── ...
│   ├── services/          # API and business logic
│   │   ├── api.js         # HTTP client wrapper
│   │   ├── ApiService.js  # API calls
│   │   ├── encryption.js  # AES encryption/decryption
│   │   └── *Service.js    # Feature-specific services
│   ├── stores/            # Pinia stores
│   │   ├── system.js      # System state
│   │   ├── auth.js        # Auth state
│   │   └── docker.js      # Docker state
│   ├── assets/            # Static assets
│   └── router/            # Vue Router configuration
└── quasar.config.js       # Quasar configuration
```

### State Management (Pinia)

- **systemStore** - System stats, connection status
- **authStore** - Authentication state, token
- **dockerStore** - Container state, logs
- **processStore** - Process list state
- **scheduleStore** - Scheduled tasks state
- **thresholdStore** - Threshold configuration and alerts

### Services Layer

- **ApiService** - Main API client with encryption
- **WebSocketService** - Real-time stats
- **DockerService** - Docker API calls
- **ProcessService** - Process management
- **ScheduleService** - Scheduled tasks
- **ThresholdService** - Threshold alerts

## Installation

### Prerequisites
- Node.js 16+
- npm or yarn

### Setup

```bash
cd frontend
npm install
```

### Environment Configuration

Create `src/services/config.js` or use environment variables:

```javascript
export const API_BASE_URL = 'http://localhost:8000'
export const WS_URL = 'ws://localhost:8000/ws/stats'
```

## Development

### Start Dev Server

```bash
npm run dev
```

The app will run on: **http://localhost:9000**

### Hot Reload

Vite provides hot module replacement (HMR). Changes appear instantly without full refresh.

### Linting

```bash
npm run lint
```

### Formatting

```bash
npm run format
```

## Building

### Development Build

```bash
npm run build
```

Output: `dist/spa/`

### Production Build

```bash
npm run build
```

Output: `dist/spa/` (optimized, minified)

The built files can be served by:
1. FastAPI backend (serves from `/dist/spa`)
2. nginx/Apache
3. Any static file server

## Mobile Deployment

### Prerequisites

**iOS:**
- macOS with Xcode 15+
- Apple Developer Account (for device deployment)
- CocoaPods installed

**Android:**
- Android Studio
- Android SDK

### Build Steps

1. **Build web assets:**
   ```bash
   npm run build
   ```

2. **Sync Capacitor:**
   ```bash
   npm run cap:sync
   ```

3. **Open in IDE:**
   ```bash
   # iOS
   npm run cap:open ios

   # Android
   npm run cap:open android
   ```

4. **Build from IDE:**
   - **iOS:** Xcode → Product → Run
   - **Android:** Android Studio → Run

### Configuration

Edit `capacitor.config.json`:

```json
{
  "appId": "com.nexcontrol.app",
  "appName": "NexControl",
  "webDir": "dist/spa",
  "bundledWebRuntime": false,
  "server": {
    "cleartext": true,
    "allowNavigation": [
      "http://localhost:8000",
      "http://192.168.*.*"
    ]
  }
}
```

### iOS Specific

1. **Update Bundle Identifier:**
   - Xcode → Target → Bundle Identifier
   - Use your own domain (e.g., `com.yourcompany.nexcontrol`)

2. **Enable Permissions:**
   - Info.plist → Add required permissions
   - TouchID: `NSFaceIDUsageDescription`

3. **Code Signing:**
   - Xcode → Signing & Capabilities
   - Select your development team

### Android Specific

1. **Update Package Name:**
   - AndroidManifest.xml → package
   - Use reverse domain notation

2. **Permissions:**
   - Add to AndroidManifest.xml:
     ```xml
     <uses-permission android:name="android.permission.INTERNET" />
     <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
     ```

## Project Structure

### Key Files

| File | Purpose |
|------|---------|
| `quasar.config.js` | Quasar & Vite configuration |
| `src/App.vue` | Root component |
| `src/main.js` | Application entry point |
| `src/router/routes.js` | Vue Router routes |
| `src/layouts/MainLayout.vue` | Main app layout |
| `src/pages/*.vue` | Page components |
| `src/stores/*.js` | Pinia stores |
| `src/services/*.js` | API and business logic |

### Configuration Files

| File | Purpose |
|------|---------|
| `package.json` | Dependencies and scripts |
| `quasar.config.js` | Quasar framework config |
| `.eslintrc.js` | ESLint rules |
| `.prettierrc` | Prettier formatting |
| `capacitor.config.json` | Capacitor mobile config |

## Key Services

### ApiService

Main HTTP client with encryption:

```javascript
import { api } from '@/services/ApiService'

// GET request (auto-decrypts response)
const stats = await api.get('/api/stats/all')

// POST request (auto-encrypts body)
const result = await api.post('/api/system/power/shutdown', {
  delay: 0
})
```

### WebSocketService

Real-time stats connection:

```javascript
import { WebSocketService } from '@/services/WebSocketService'

// Connect
WebSocketService.connect()

// Listen for messages
WebSocketService.on('stats', (data) => {
  console.log('CPU:', data.cpu.percent)
})

// Disconnect
WebSocketService.disconnect()
```

### EncryptionService

AES-256-GCM encryption:

```javascript
import { encryptPayload, decryptResponse } from '@/services/encryption'

// Encrypt
const encrypted = await encryptPayload({
  password: 'admin123'
})

// Decrypt
const decrypted = await decryptResponse(encryptedData)
```

## Troubleshooting

### Issues and Solutions

**Issue:** "Cannot connect to server"
- **Solution:** Ensure backend is running on port 8000
- Check firewall settings
- Verify you're on same local network

**Issue:** "Encryption failed"
- **Solution:** Check AES_KEY matches backend
- Ensure key is 32+ characters

**Issue:** "Mobile app blank screen"
- **Solution:** Check server URL in Capacitor config
- Ensure local network IP is correct (not localhost)

**Issue:** "WebSocket not connecting"
- **Solution:** Verify backend WebSocket endpoint is running
- Check if firewall blocks WebSocket

### Debug Mode

Enable console logging:

```javascript
// In quasar.config.js
build: {
  extendViteConf (viteConf) {
    viteConf.build = {
      minify: false  // Disable minification
    }
  }
}
```

## Performance

### Optimization Tips

1. **Lazy Loading:** Routes are lazy-loaded by default
2. **Chart.js:** Limit data points to 100 for smooth rendering
3. **WebSocket:** Prefer over polling for real-time stats
4. **Debouncing:** Search/filter inputs use debounce

### Bundle Size

Current bundle size: ~500KB (gzipped)

To analyze:
```bash
npm run build
# Check dist/spa/assets/ for file sizes
```

---

**Version:** 1.0.0
**Last Updated:** 2026-02-11
**Quasar:** 2.x
**Vue:** 3.x
