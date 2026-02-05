# iOS Info.plist Fix for Local HTTP Connections

## The Problem
iOS blocks HTTP requests to local network IPs by default. Even with `NSAllowsArbitraryLoads`, you need the **exact correct XML structure**.

## EXACT XML to Add to Info.plist

### Step 1: Open Info.plist
File location:
```
ios/App/App/Info.plist
```

### Step 2: Find the Outer <dict> Tag
Look for this structure:
```xml
<plist version="1.0">
<dict>
    <!-- Other keys like CFBundleDisplayName, etc. -->
    
    <!-- ⬇️ ADD THE XML BELOW HERE ⬇️ -->
    
</dict>
</plist>
```

### Step 3: Paste This EXACT XML Inside <dict>

```xml
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
        <key>NSAllowsArbitraryLoadsInWebContent</key>
        <true/>
        <key>NSExceptionDomains</key>
        <dict>
            <key>localhost</key>
            <dict>
                <key>NSExceptionAllowsInsecureHTTPLoads</key>
                <true/>
                <key>NSIncludesSubdomains</key>
                <true/>
            </dict>
        </dict>
    </dict>
```

### Full Example of How It Should Look

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>NexControl</string>
    
    <!-- Other existing keys... -->
    
    <!-- ⬇️ ADD THIS SECTION ⬇️ -->
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
        <key>NSAllowsArbitraryLoadsInWebContent</key>
        <true/>
        <key>NSExceptionDomains</key>
        <dict>
            <key>localhost</key>
            <dict>
                <key>NSExceptionAllowsInsecureHTTPLoads</key>
                <true/>
                <key>NSIncludesSubdomains</key>
                <true/>
            </dict>
        </dict>
    </dict>
    <!-- ⬆️ END OF NEW SECTION ⬆️ -->
    
    <key>NSLocalNetworkUsageDescription</key>
    <string>This app requires access to your local network to connect to and control your PC.</string>
    
</dict>
</plist>
```

## CRITICAL: After Editing Info.plist

### 1. Clean Build Folder in Xcode
- Open Xcode
- Product → Clean Build Folder (Cmd+Shift+K)

### 2. Delete App from iPhone
- Long press NexControl app → Remove App
- OR: Settings → General → iPhone Storage → NexControl → Delete App

### 3. Rebuild and Install
- Product → Build (Cmd+B)
- Run on your device (Cmd+R)

## Verify the Fix

When you tap Connect:
1. **Check the DEBUG alert** - It will show the exact URL being used
2. Look for: `Attempted Connection: http://192.168.X.X:8000`
3. If you see: `Attempted Connection: http://localhost:8000` → WRONG IP!
4. You MUST enter your PC's actual LAN IP (192.168.x.x)

