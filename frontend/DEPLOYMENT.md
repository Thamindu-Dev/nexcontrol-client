# NexControl Mobile App - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [iOS Deployment](#ios-deployment)
3. [Android Deployment](#android-deployment)
4. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- Node.js 20+
- npm or yarn
- Xcode (for iOS) - Mac only
- Android Studio (for Android)
- CocoaPods (for iOS)

### Install CocoaPods (macOS)
```bash
sudo gem install cocoapods
cd frontend/ios
pod install
```

### Check Capacitor Setup
```bash
cd frontend
npx cap doctor
```

---

## iOS Deployment

### Step 1: Configure App Signing

1. **Create Apple Developer Account**
   - Go to [Apple Developer](https://developer.apple.com)
   - Enroll in the program ($99/year)

2. **Create App ID**
   - Go to Certificates, Identifiers & Profiles
   - Create a new App ID: `com.nexcontrol.app`
   - Enable capabilities: Push Notifications

3. **Create Provisioning Profile**
   - Create a Development Provisioning Profile for testing
   - Create a Distribution Provisioning Profile for App Store

### Step 2: Configure Xcode Project

```bash
cd frontend
npx cap open ios
```

1. **Set Bundle Identifier**
   - Select project in navigator
   - Set Bundle Identifier to: `com.nexcontrol.app`

2. **Set Signing Team**
   - Select your development team
   - Xcode will manage signing automatically

3. **Set Version Numbers**
   - Version: `1.0.0`
   - Build: Increment for each release

### Step 3: Build for Testing

#### Simulator (Quick Test)
```bash
cd frontend
npx cap sync ios
npx cap open ios
# In Xcode: Product > Run (⌘R)
```

#### Physical Device (Development)
```bash
cd frontend
npx cap sync ios
npx cap open ios
# Connect device, select it in Xcode, then run
```

### Step 4: Build for App Store

```bash
cd frontend
npx cap sync ios
npx cap open ios
```

In Xcode:
1. Select "Any iOS Device (arm64)"
2. Product > Archive
3. Distribute App:
   - Select "App Store Connect"
   - Follow the prompts

### Step 5: TestFlight Distribution

1. Upload build to App Store Connect
2. Add testers in TestFlight
3. Create testing group
4. Distribute for internal testing

### Step 6: Public Release

1. **Prepare Store Listing**
   - App name: NexControl
   - Description (provide details)
   - Screenshots (required)
   - App icon (1024x1024)

2. **Submit for Review**
   - Complete all required fields
   - Submit for App Store review
   - Wait for approval (typically 1-3 days)

---

## Android Deployment

### Step 1: Configure App Signing

#### Option A: Automatic Signing (Recommended for testing)
```bash
cd frontend
npx cap sync android
npx cap open android
```

In Android Studio:
- Build > Generate Signed Bundle / APK
- Select "Android App Bundle"
- Create new keystore or use existing

#### Option B: Manual Keystore

**Create Keystore**
```bash
keytool -genkey -v -keystore nexcontrol-release.keystore \
  -alias nexcontrol -keyalg RSA -keysize 2048 -validity 10000
```

**Configure signing in `android/app/build.gradle`**:
```gradle
android {
    signingConfigs {
        release {
            storeFile file("nexcontrol-release.keystore")
            storePassword "YOUR_PASSWORD"
            keyAlias "nexcontrol"
            keyPassword "YOUR_PASSWORD"
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}
```

### Step 2: Build APK (Testing)

```bash
cd frontend
npx cap sync android
cd android
./gradlew assembleDebug
```

Output: `android/app/build/outputs/apk/debug/app-debug.apk`

### Step 3: Build App Bundle (Production)

```bash
cd frontend
npx cap sync android
cd android
./gradlew bundleRelease
```

Output: `android/app/build/outputs/bundle/release/app-release.aab`

### Step 4: Google Play Console Setup

1. **Create Developer Account**
   - Go to [Google Play Console](https://play.google.com/console)
   - Pay $25 one-time fee

2. **Create App**
   - Fill in app details
   - Select app type: Apps
   - Choose pricing: Free or Paid

3. **Upload AAB**
   - Go to Testing & Release
   - Upload `app-release.aab`

### Step 5: Internal Testing

1. **Create Internal Test Track**
   - Add tester email addresses
   - Roll out to internal testers

2. **Test the App**
   - Download via Play Store link
   - Test all features

### Step 6: Production Release

1. **Complete Store Listing**
   - App name: NexControl
   - Description (at least 80 characters)
   - Screenshots (at least 2)
   - App icon (512x512)

2. **Content Rating**
   - Complete questionnaire
   - Get content rating

3. **Privacy Policy URL**
   - Add privacy policy URL

4. **Release to Production**
   - Create production release
   - Roll out to production

---

## Build Commands Reference

### iOS
```bash
# Sync Capacitor
npx cap sync ios

# Open in Xcode
npx cap open ios

# Copy web assets
npx cap copy ios
```

### Android
```bash
# Sync Capacitor
npx cap sync android

# Open in Android Studio
npx cap open android

# Copy web assets
npx cap copy android

# Build debug APK
cd android && ./gradlew assembleDebug

# Build release AAB
cd android && ./gradlew bundleRelease
```

---

## GitHub Actions CI/CD

The project includes GitHub Actions workflows for automated builds:

### iOS Build (`.github/workflows/ios-build.yml`)
- Triggers on push to main branch
- Builds Quasar app
- Syncs Capacitor iOS
- Ready for Xcode cloud integration

### Android Build (`.github/workflows/android-build.yml`)
- Triggers on push to main branch
- Builds Quasar app
- Syncs Capacitor Android
- Builds debug APK
- Can be extended for release builds

---

## Troubleshooting

### iOS Issues

#### "Pod install failed"
```bash
cd frontend/ios
pod deintegrate
pod install
```

#### "Code signing errors"
- Verify your Apple Developer account is active
- Check Bundle Identifier matches App ID
- Ensure Provisioning Profile includes your device

#### "Push notifications not working"
- Verify Push Notifications capability is enabled
- Check APNs certificates are valid
- Ensure backend server is configured

### Android Issues

#### "Gradle build failed"
```bash
cd frontend/android
./gradlew clean
./gradlew build
```

#### "App crashes on startup"
- Check `android:usesCleartextTraffic` in AndroidManifest.xml
- Verify network security config
- Check logcat: `adb logcat`

#### "Install fails"
- Uninstall old version first
- Check Android version compatibility (minSdkVersion 21+)

### Common Issues

#### "Capacitor sync fails"
```bash
npx cap clean
npx cap sync
```

#### "Platform not found"
```bash
npx cap add ios
npx cap add android
```

#### "Build fails after dependency update"
```bash
rm -rf node_modules
rm package-lock.json
npm install
npx cap sync
```

---

## Environment Configuration

### Development
- API URL: `http://localhost:8000`
- No app signing required

### Staging
- API URL: `https://staging-api.nexcontrol.example.com`
- Development signing

### Production
- API URL: `https://api.nexcontrol.example.com`
- Production signing required

Configure in `capacitor.config.json` or via environment variables.

---

## Post-Release Checklist

- [ ] Monitor crash reports (Firebase Crashlytics recommended)
- [ ] Respond to user reviews
- [ ] Track analytics
- [ ] Plan for updates
- [ ] Keep dependencies updated
- [ ] Renew certificates annually

---

## Support

For issues or questions:
- GitHub Issues: [Create issue](https://github.com/yourusername/nexcontrol/issues)
- Documentation: Check Capacitor docs at https://capacitorjs.com
