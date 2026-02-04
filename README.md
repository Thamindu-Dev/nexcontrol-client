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
- [Documentation](#documentation)
- [Recent Updates](#recent-updates)
- [Support](#support)

## Overview

**NexControl** is a secure, local network Remote PC Controller designed for engineering students and system administrators. It provides a modern web interface and mobile apps (iOS/Android) for monitoring and controlling Windows/Linux PCs from your local network.

**Architecture:**
- **Backend:** Python FastAPI (~2,700 lines)
- **Frontend:** Quasar Framework (Vue 3 + Vite)
- **Mobile:** Capacitor (iOS & Android apps)
- **Security:** AES-256-GCM encryption + JWT authentication

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

### Power Management
- Shutdown PC with optional delay
- Restart PC with optional delay
- Hibernate PC
- Lock PC
- Schedule power actions (new)

### Docker Management
- List all containers with status
- Start/Stop/Restart containers
- View container logs with auto-scroll
- Graceful handling when Docker unavailable

### Process Management
- Sortable process list (by CPU/Memory)
- Kill processes with confirmation
- Protected PIDs (0, 1, 2, kernel processes)
- Input validation and sanitization

### Additional Features
- Remote screenshot capture
- Wake-on-LAN (WoL) support
- Threshold notifications (CPU/Memory/Disk alerts)
- WebSocket real-time stats (optional)
- Biometric authentication framework (TouchID/FaceID)
- Dark mode toggle

### Security Features
- AES-256-GCM encryption for all sensitive requests
- JWT authentication with 60-minute expiration
- Replay attack prevention (30-second timestamp tolerance)
- Rate limiting (10 req/min, 5 attempts lockout)
- bcrypt password hashing
- Input sanitization and validation
- CORS configuration for local network

## Project Status

| Component | Status | Completion |
|-----------|--------|------------|
| **Backend** | ✅ Complete | 100% |
| **Frontend Web** | ✅ Complete | 100% |
| **iOS App** | ✅ Complete | 100% |
| **Android App** | ✅ Complete | 100% |
| **UI Modernization** | ✅ Complete | 100% |
| **Bug Fixes** | ✅ Complete | 100% |
| **Documentation** | 🟡 Partial | 85% |

**Overall Project Completion: ~97%**

## Quick Start

### Prerequisites
- Python 3.8+ (backend)
- Node.js 16+ (frontend)
- Docker (optional, for container management)

### Backend Setup

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

### Frontend Setup (Web Dev)

```bash
cd frontend
npm install
npm run dev
```

Web app will run on: http://localhost:9000

### Mobile App Build

```bash
cd frontend
npm run build
npm run cap:sync
npm run cap:build ios    # Opens Xcode
npm run cap:build android # Opens Android Studio
```

See [MOBILE_DEPLOYMENT.md](MOBILE_DEPLOYMENT.md) for detailed mobile deployment instructions.

## Documentation

- [TASKS.md](TASKS.md) - Detailed implementation tasks and progress
- [MOBILE_DEPLOYMENT.md](MOBILE_DEPLOYMENT.md) - Mobile app deployment guide
- [backend/README.md](backend/README.md) - Backend API documentation
- [frontend/README.md](frontend/README.md) - Frontend development guide

## Recent Updates (2026-02-04)

### Bug Fixes ✅

#### Dashboard Layout Fixes
- **Header Layout Asymmetry:** Reduced left padding to move Menu button closer to screen edge
- **Equal Height Cards:** Applied flexbox stretch to all stat cards (Memory, GPU, Disk, Temp) for perfect alignment
- **Action Cards:** Fixed Docker/Processes cards to have equal heights
- **Text Shortening:** Changed "GPU data not available" to "N/A" for cleaner layout

#### Connection Status Fixes
- **Unified Status Source:** Both header badge and footer now use `systemStore.isConnected` as single source of truth
- **Store Integration:** Added `isConnected` state to system store
- **Real-time Updates:** Connection status updates automatically on API success/failure

#### Data Updates
- **2-Second Polling:** Changed refresh interval from 5 seconds to 2 seconds for more responsive real-time updates
- **Auto-Refresh:** Proper cleanup with `onUnmounted` to prevent memory leaks

#### Disk Usage Calculation
- **Base-1000 Conversion:** Changed from base-1024 (GiB) to base-1000 (GB) to match OS display standards
- **Safety Checks:** Added validation for negative/NaN values

#### Ghost Overlay Prevention
- **Z-Index Protection:** Added comprehensive z-index management to all interactive elements
- **Drawer Backdrop:** Fixed backdrop blocking UI when drawer is closed
- **Pointer Events:** Made progress bars and decorative elements non-blocking
- **Page Content:** Elevated page content above closed drawer backdrop (z-index: 5000)

### Previous Updates (2026-02-03)

#### UI Modernization
- **Login.vue:** Glassmorphism design, animated gradient background, 3 floating orbs
- **Dashboard.vue:** Animated stat cards, gradient power buttons, 4 floating orbs
- **MainLayout.vue:** Glassmorphism header/drawer/footer, pulsing status dot

#### WebSocket Support
- **Backend:** Added `/ws/stats` WebSocket endpoint for real-time stats
- **Frontend:** Created `WebSocketService.js` with auto-reconnect
- **Dashboard:** Toggle button for real-time vs polling mode

#### Scheduled Tasks
- **Backend:** ScheduledTaskManager with persistent storage
- **API:** Create, list, update, delete, toggle scheduled tasks
- **Frontend:** ScheduledTasks.vue page with full CRUD operations

#### Threshold Notifications
- **Backend:** ThresholdNotificationManager for system alerts
- **WebSocket:** Real-time alert broadcasting
- **Frontend:** Threshold settings in Settings.vue

## Default Credentials

⚠️ **IMPORTANT:** Change default password before production!

| Credential | Default Value | Location |
|------------|---------------|----------|
| **App Password** | `admin123` | backend/.env |
| **Secret Key** | Auto-generate | backend/.env (32+ chars) |
| **AES Key** | Auto-generate | backend/.env (32 chars) |

## Support

For issues, questions, or contributions:
- Check the [TASKS.md](TASKS.md) for known issues and implementation details
- Review backend/frontend README files for technical documentation
- Ensure you're on the same local network as the target PC

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE](LICENSE) file for full text.

---

**Version:** 1.0.0
**Last Updated:** 2026-02-04
**Project Completion:** ~97%
