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

### Phase 4: Backend Integration 🔄 IN PROGRESS
- [ ] Configure API base URLs for development/production
- [ ] Implement authentication flow
- [ ] Set up secure storage for tokens
- [ ] Implement API interceptors for error handling

### Phase 5: Core Features
- [ ] Dashboard/Home view
- [ ] Device management (list, add, edit, delete)
- [ ] Real-time device status updates
- [ ] Control panels for devices

### Phase 6: Native Features
- [ ] Push notifications setup
- [ ] Camera integration (if needed for QR/Barcodes)
- [ ] Biometric authentication (TouchID/FaceID)
- [ ] Background tasks/refresh

### Phase 7: Testing
- [ ] Unit tests for core components
- [ ] E2E testing with Capacitor
- [ ] Manual testing on physical devices
- [ ] Performance optimization

### Phase 8: Deployment
- [ ] Configure App Store Connect (iOS)
- [ ] Configure Google Play Console (Android)
- [ ] Set up code signing (iOS certificates)
- [ ] Set up app signing keys (Android)
- [ ] Deploy to TestFlight/Internal Testing
- [ ] Public release

## Current Focus
Phase 3: Core App Structure - configuring app icons, splash screens, and metadata.
