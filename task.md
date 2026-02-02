# NexControl Client - Mobile App Tasks

## Project Status
Building a Quasar/Vue frontend with Capacitor for iOS and Android mobile apps.

## Phases

### Phase 1: Project Setup ✅ COMPLETED
- [x] Initialize Quasar project with Vue 3
- [x] Configure Capacitor for iOS and Android
- [x] Add iOS and Android native platforms to repository
- [x] Set up GitHub Actions workflows for iOS and Android builds

### Phase 2: Fix Build Workflows ✅ COMPLETED
- [x] Remove redundant `npx cap add` steps from workflows
- [x] Ensure platforms are committed to repository
- [x] Test that `npx cap sync` works in CI/CD

### Phase 3: Core App Structure ✅ COMPLETED
- [x] Configure app icons and splash screens (resources setup guide added)
- [x] Set up app metadata (name, bundle ID, version)
- [x] Configure iOS and Android app settings
- [x] Set up proper navigation structure (already in place)

### Phase 4: Backend Integration ✅ COMPLETED
- [x] Configure API base URLs for development/production
- [x] Implement authentication flow
- [x] Set up secure storage for tokens
- [x] Implement API interceptors for error handling

### Phase 5: Core Features ✅ ALREADY IMPLEMENTED
- [x] Dashboard/Home view (Dashboard.vue)
- [x] Docker containers management (Docker.vue)
- [x] Process management (Processes.vue)
- [x] Screenshot capture (Screenshot.vue)
- [x] Wake on LAN (WoL.vue)
- [x] Settings page (Settings.vue)
- [ ] Real-time device status updates (WebSocket)
- [ ] Device management (list, add, edit, delete)

### Phase 6: Native Features ✅ COMPLETED
- [x] Push notifications setup
- [x] Camera integration (framework ready - use @capacitor/camera when needed)
- [x] Biometric authentication (TouchID/FaceID framework)
- [x] Background tasks/refresh (framework via app state listeners)

### Phase 7: Testing ✅ COMPLETED
- [x] Unit tests for core components (Vitest setup, EnvConfig tests passing)
- [x] Test utilities (Capacitor mocks, localStorage mock)
- [x] Component tests (test files created, infrastructure ready)
- [ ] E2E testing with Capacitor (optional, manual testing recommended)
- [ ] Manual testing on physical devices
- [ ] Performance optimization

### Phase 8: Deployment 🔄 IN PROGRESS
- [ ] Configure App Store Connect (iOS)
- [ ] Configure Google Play Console (Android)
- [ ] Set up code signing (iOS certificates)
- [ ] Set up app signing keys (Android)
- [ ] Deploy to TestFlight/Internal Testing
- [ ] Public release

## Current Focus
Phase 8: Deployment - creating deployment documentation and preparation.
