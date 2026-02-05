# iOS App Transport Security (ATS) Fix

## The Problem
iOS blocks HTTP requests by default. Since your NexControl server runs on a local IP address (e.g., `http://192.168.1.100`), iOS will block these requests for security reasons.

## The Solution
You need to configure the iOS app to allow HTTP connections to local network addresses.

---

## Method 1: Automatic Configuration (Capacitor 3+)

Create or edit `capacitor.config.json` in the frontend root directory:

```json
{
  "appId": "com.nexcontrol.app",
  "appName": "NexControl",
  "webDir": "dist/spa",
  "bundledWebRuntime": false,
  "ios": {
    "contentSecurityPolicy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://192.168.*:* https://192.168.*:* http://localhost:* https://localhost:*; frame-src 'none';"
  }
}
```

Then rebuild the iOS app:
```bash
npm run build
npx cap sync ios
```

---

## Method 2: Manual Info.plist Configuration

If Method 1 doesn't work, manually edit the Info.plist file:

### Step 1: Locate Info.plist
The file is located at:
```
ios/App/App/Info.plist
```

### Step 2: Add ATS Configuration
Open `Info.plist` and add this inside the outer `<dict>` tag (before the closing `</dict>` and after `</plist>`):

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <!-- Allow arbitrary loads for local network testing -->
    <key>NSAllowsArbitraryLoads</key>
    <true/>
    
    <!-- Optional: More restrictive configuration (recommended for production) -->
    <key>NSAllowsLocalNetworking</key>
    <true/>
    
    <!-- Allow specific domains (optional, more secure) -->
    <key>NSExceptionDomains</key>
    <dict>
        <key>localhost</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <true/>
            <key>NSIncludesSubdomains</key>
            <true/>
        </dict>
        <key>192.168.1.100</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <true/>
        </dict>
        <key>192.168.0.0</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <true/>
            <key>NSIncludesSubdomains</key>
            <true/>
        </dict>
        <key>10.0.0.0</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <true/>
            <key>NSIncludesSubdomains</key>
            <true/>
        </dict>
        <key>172.16.0.0</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <true/>
            <key>NSIncludesSubdomains</key>
            <true/>
        </dict>
    </dict>
</dict>
```

### Important Placement
The XML should look like this:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Other existing keys... -->
    
    <!-- Add ATS configuration HERE -->
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
    
</dict>
</plist>
```

---

## Method 3: Using Xcode (Recommended for Development)

1. Open the iOS project in Xcode:
   ```bash
   open ios/App.xcworkspace
   ```

2. In Xcode, navigate to:
   - `App` folder in the Project Navigator
   - Select `Info.plist`
   - Add a new key by clicking the "+" button
   - Key: `App Transport Security Settings` (Type: Dictionary)
   - Expand it and add:
     - Key: `Allow Arbitrary Loads` (Type: Boolean)
     - Value: `YES`

3. Build and run the app from Xcode

---

## Verification

After making changes, rebuild and test:

```bash
# Build frontend
npm run build

# Sync with Capacitor
npx cap sync ios

# Open in Xcode
npx cap open ios

# Run in Xcode (Cmd+R)
```

When the app opens, check the Xcode console for:
- ✅ "Successfully connected to server"
- ✅ No ATS errors in the logs

---

## Common Issues & Solutions

### Issue 1: Still getting "Network Error"
**Solution**: 
- Make sure both devices are on the same network
- Check the server is running: `python main.py`
- Verify the IP address is correct

### Issue 2: "Load Failed" persists
**Solution**:
- Clear app data: Settings → General → iPhone Storage → NexControl → Offload App
- Reinstall the app completely

### Issue 3: HTTPS required error
**Solution**:
- Use Method 1 (Capacitor config) which automatically configures CSP
- Or use Method 2 with `NSAllowsArbitraryLoads` set to `true`

---

## Security Note

⚠️ **WARNING**: `NSAllowsArbitraryLoads` should ONLY be used for:
- Development/Testing environments
- Local network connections (192.168.x.x, 10.x.x.x, 172.16.x.x)
- NEVER use in production with public HTTPS servers

For production deployment, consider:
- Setting up HTTPS on the server with a self-signed certificate
- Using specific domain exceptions instead of arbitrary loads
- Implementing proper certificate pinning

