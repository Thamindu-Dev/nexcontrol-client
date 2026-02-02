# App Icons and Splash Screens

## How to Add Icons and Splash Screens

### Option 1: Use Capacitor Assets (Recommended)

1. Install the Capacitor Assets CLI:
   ```bash
   npm install -g @capacitor/assets
   ```

2. Add your icon and splash screen images to this directory:
   - `icon.png` - 1024x1024px PNG (app icon)
   - `splash.png` - 2732x2732px PNG (splash screen)

3. Generate resources for all platforms:
   ```bash
   npx @capacitor/assets generate
   ```

### Option 2: Manual Setup

#### iOS Icons
Add icons to: `ios/App/App/Assets.xcassets/AppIcon.appiconset/`

Required sizes:
- iPhone App 60pt (1x, 2x, 3x)
- iPhone App 76pt (1x, 2x) - iPad
- iPhone App 83.5pt (2x) - iPhone Pro
- iPhone Notification 20pt (1x, 2x, 3x)
- iPhone Settings 29pt (1x, 2x, 3x)
- iPhone Spotlight 40pt (1x, 2x, 3x)
- App Store 1024pt

#### Android Icons
Add icons to: `android/app/src/main/res/mipmap-*/ic_launcher.png`

Required directories:
- mipmap-mdpi (48x48px)
- mipmap-hdpi (72x72px)
- mipmap-xhdpi (96x96px)
- mipmap-xxhdpi (144x144px)
- mipmap-xxxhdpi (192x192px)

#### Splash Screens
- iOS: `ios/App/App/Assets.xcassets/LaunchImage.imageset/`
- Android: `android/app/src/main/res/drawable-*/splash.png`

## Current Status
🚧 Default Capacitor icons are in place. Add custom assets above to personalize your app.
