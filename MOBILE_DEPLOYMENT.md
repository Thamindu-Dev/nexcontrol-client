# Mobile Deployment Guide - NexControl

## Building Mobile Apps

NexControl can be deployed as native mobile apps using Capacitor.

---

## Option 1: GitHub Actions (Recommended)

### iOS IPA Build

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Build mobile apps"
   git push
   ```

2. **Run the workflow**
   - Go to: `https://github.com/YOUR_USERNAME/nexcontrol-client/actions`
   - Select "Build iOS App" workflow
   - Click "Run workflow" → Select branch → Click "Run workflow"
   - Wait ~10-15 minutes for the build

3. **Download the IPA**
   - Go to the Actions tab
   - Click on the completed workflow run
   - Download "NexControl-iOS" artifact
   - Extract to get the `.ipa` file

4. **Install on iPhone**
   - **Method A (Direct):** Use AltStore or Sideloadly
   - **Method B (TestFlight):** Upload to App Store Connect (requires Apple Developer account)
   - **Method C (Ad-hoc):** Requires provisioning profiles

### Android APK Build

1. **Run the workflow**
   - Go to Actions tab → "Build Android APK"
   - Click "Run workflow"

2. **Download the APK**
   - Download "NexControl-Android" artifact
   - Extract to get `app-debug.apk`

3. **Install on Android**
   - Transfer APK to your phone
   - Enable "Install from unknown sources"
   - Open the APK to install

---

## Option 2: Local Build

### Prerequisites

**For iOS:**
- Mac computer with Xcode 15+
- Apple Developer account (for signing)
- CocoaPods installed: `sudo gem install cocoapods`

**For Android:**
- Android Studio (or just JDK 17+)
- Android SDK

### Build Steps

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   npm install -g @capacitor/cli
   ```

2. **Build the web app**
   ```bash
   npm run build
   ```

3. **Add iOS/Android platforms**
   ```bash
   npx cap add ios
   npx cap add android
   ```

4. **Sync files**
   ```bash
   npx cap sync
   ```

5. **Open in IDE**
   ```bash
   # iOS (requires Xcode)
   npx cap open ios

   # Android (requires Android Studio)
   npx cap open android
   ```

6. **Build from IDE**
   - **Xcode:** Product → Archive (or Product → Run for simulator)
   - **Android Studio:** Build → Build Bundle(s) / APK(s) → Build APK(s)

---

## Configuration

### Server Configuration

The mobile app needs to connect to your PC's backend. Update the server settings in the app:

1. Open the app
2. Go to **Settings**
3. Enter your PC's **local IP address** (e.g., `192.168.1.100`)
4. Enter **Port** (default: `8000`)
5. Click **Save Server Config**

### Finding Your PC's IP

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your network adapter

**macOS/Linux:**
```bash
ifconfig | grep inet
```
or
```bash
ip addr show
```

### iOS Local Network Permission

iOS requires explicit permission for local network access. This is already configured in:
```
frontend/App/ios/App/App/Info.plist
```

The app will prompt users on first launch to allow local network access.

---

## Testing

### 1. Start Backend on Your PC

```bash
cd backend
python main.py
```

Backend will run on: `http://0.0.0.0:8000`

### 2. Ensure Devices are on Same Network

- Your PC and mobile device must be on the same WiFi/network
- Firewalls must allow port 8000

### 3. Connect from Mobile App

- Open NexControl app
- Enter server IP: `YOUR_PC_IP:8000`
- Enter password: `admin123`
- Click Connect

---

## Troubleshooting

### "Cannot connect to server"

- Ensure backend is running: `curl http://localhost:8000/`
- Check firewall settings (allow port 8000)
- Verify devices are on same network
- Try the IP address directly in mobile browser

### iOS "Local Network" permission

- iOS 14+ requires explicit permission
- Go to: Settings → NexControl → Local Network
- Enable the toggle

### Android "Cleartext traffic" warning

- For development, HTTP is allowed
- For production, enable HTTPS in backend

### Build errors

- Ensure Node.js 20+ is installed
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Clear Capacitor cache: `npx cap clean`

---

## Production Deployment

### Apple App Store (iOS)

1. **Enroll in Apple Developer Program** ($99/year)
2. **Create App ID** in App Store Connect
3. **Configure signing certificates**
4. **Update exportOptions.plist** with your Team ID
5. **Build with GitHub Actions** (select "Release" option)
6. **Upload IPA** to App Store Connect
7. **Submit for review**

### Google Play Store (Android)

1. **Create Google Play Console account** ($25 one-time)
2. **Create signing key** for the app
3. **Update build configuration** in Android
4. **Build signed APK/AAB** via GitHub Actions
5. **Upload to Play Console**
6. **Complete store listing**
7. **Submit for review**

---

## Quick Start Summary

**For immediate testing:**
1. Run backend on your PC: `python main.py`
2. Build Android APK via GitHub Actions
3. Download and install APK on your phone
4. Enter your PC's IP in app settings
5. Login with password: `admin123`

**For production:**
1. Set up Apple/Google developer accounts
2. Configure signing certificates
3. Build via GitHub Actions with release mode
4. Submit to app stores

---

## Files Changed for Mobile

- `.github/workflows/ios-build.yml` - iOS build workflow
- `.github/workflows/android-build.yml` - Android build workflow
- `frontend/App/ios/exportOptions.plist` - iOS export configuration
- `frontend/capacitor.config.ts` - Capacitor configuration
- `frontend/App/ios/App/App/Info.plist` - iOS permissions

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Run GitHub Actions workflows
3. ✅ Download IPA/APK files
4. ⏳ Install on mobile device
5. ⏳ Test all features
6. ⏳ Submit to app stores (optional)
