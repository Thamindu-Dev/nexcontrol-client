/**
 * ==============================================================================
 * NexControl - Remote PC Controller
 * Copyright (C) 2026 Thamindu-Dev
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * ==============================================================================
 */

/**
 * =============================================================
 * NativeFeatures - Unified Native Features Service
 * =============================================================
 * Centralized access to all native Capacitor features
 */

// Check if running in Capacitor environment
const isCapacitor = () => {
  return typeof window !== 'undefined' && window.Capacitor;
};

import PushNotifications from './PushNotifications';
import BiometricAuth from './BiometricAuth';

/**
 * Get device information
 * @returns {Promise<Object>} Device info
 */
export async function getDeviceInfo() {
  try {
    if (!isCapacitor()) {
      return {
        platform: 'web',
        model: 'unknown',
        osVersion: 'unknown'
      };
    }

    const { Device } = await import('@capacitor/device');
    const info = await Device.getInfo();
    const language = await Device.getLanguageCode();
    const battery = await Device.getBatteryInfo();

    return {
      ...info,
      language,
      battery
    };
  } catch (error) {
    console.error('Get device info error:', error);
    return {
      platform: 'web',
      model: 'unknown',
      osVersion: 'unknown'
    };
  }
}

/**
 * Check if running on mobile (Capacitor)
 * @returns {Promise<boolean>}
 */
export async function isMobile() {
  try {
    if (!isCapacitor()) return false;

    const { Device } = await import('@capacitor/device');
    const info = await Device.getInfo();
    return info.platform === 'ios' || info.platform === 'android';
  } catch {
    return false;
  }
}

/**
 * Check if running on iOS
 * @returns {Promise<boolean>}
 */
export async function isIOS() {
  try {
    if (!isCapacitor()) return false;

    const { Device } = await import('@capacitor/device');
    const info = await Device.getInfo();
    return info.platform === 'ios';
  } catch {
    return false;
  }
}

/**
 * Check if running on Android
 * @returns {Promise<boolean>}
 */
export async function isAndroid() {
  try {
    if (!isCapacitor()) return false;

    const { Device } = await import('@capacitor/device');
    const info = await Device.getInfo();
    return info.platform === 'android';
  } catch {
    return false;
  }
}

/**
 * Vibrate device with haptic feedback
 * @param {string} style - Impact style: 'light', 'medium', 'heavy'
 */
export async function hapticImpact(style = 'medium') {
  try {
    if (!isCapacitor()) return;

    const { Haptics, ImpactStyle } = await import('@capacitor/haptics');
    const impactStyle = {
      light: ImpactStyle.Light,
      medium: ImpactStyle.Medium,
      heavy: ImpactStyle.Heavy
    }[style] || ImpactStyle.Medium;

    await Haptics.impact({ style: impactStyle });
  } catch (error) {
    console.error('Haptic impact error:', error);
  }
}

/**
 * Vibrate with notification haptic
 * @param {string} type - Type: 'SUCCESS', 'WARNING', 'ERROR'
 */
export async function hapticNotification(type = 'SUCCESS') {
  try {
    if (!isCapacitor()) return;

    const { Haptics } = await import('@capacitor/haptics');
    await Haptics.notification({ type });
  } catch (error) {
    console.error('Haptic notification error:', error);
  }
}

/**
 * Show/hide keyboard programmatically
 * @param {boolean} show - Show or hide keyboard
 */
export async function setKeyboard(show = true) {
  try {
    if (!isCapacitor()) return;

    const { Keyboard } = await import('@capacitor/keyboard');
    if (show) {
      await Keyboard.show();
    } else {
      await Keyboard.hide();
    }
  } catch (error) {
    console.error('Keyboard control error:', error);
  }
}

/**
 * Get keyboard status
 * @returns {Promise<boolean>} Keyboard visible status
 */
export async function isKeyboardVisible() {
  try {
    if (!isCapacitor()) return false;

    const { Keyboard } = await import('@capacitor/keyboard');
    const result = await Keyboard.isVisible();
    return result.isVisible;
  } catch {
    return false;
  }
}

/**
 * Add app state change listener
 * @param {Function} callback - Callback with state change info
 */
export async function addAppStateListener(callback) {
  try {
    if (!isCapacitor()) return;

    const { App } = await import('@capacitor/app');
    await App.addListener('appStateChange', (state) => {
      callback(state);
    });
  } catch (error) {
    console.error('App state listener error:', error);
  }
}

/**
 * Add app URL open listener (for deep links)
 * @param {Function} callback - Callback with URL data
 */
export async function addUrlOpenListener(callback) {
  try {
    if (!isCapacitor()) return;

    const { App } = await import('@capacitor/app');
    await App.addListener('appUrlOpen', (data) => {
      callback(data);
    });
  } catch (error) {
    console.error('URL open listener error:', error);
  }
}

/**
 * Get app info (version, build, etc)
 * @returns {Promise<Object>} App info
 */
export async function getAppInfo() {
  try {
    if (!isCapacitor()) {
      return {
        appName: 'NexControl',
        version: '1.0.0',
        build: '1'
      };
    }

    const { App } = await import('@capacitor/app');
    const info = await App.getInfo();
    return info;
  } catch (error) {
    console.error('Get app info error:', error);
    return {
      appName: 'NexControl',
      version: '1.0.0',
      build: '1'
    };
  }
}

/**
 * Exit the app (mobile only)
 */
export async function exitApp() {
  try {
    if (!isCapacitor()) return;

    const { App } = await import('@capacitor/app');
    await App.exitApp();
  } catch (error) {
    console.error('Exit app error:', error);
  }
}

/**
 * Minimize the app (background)
 */
export async function minimizeApp() {
  try {
    if (!isCapacitor()) return;

    const info = await getDeviceInfo();
    if (info.platform === 'android') {
      const { App } = await import('@capacitor/app');
      await App.minimizeApp();
    }
  } catch (error) {
    console.error('Minimize app error:', error);
  }
}

/**
 * Initialize all native features
 * Should be called on app startup
 */
export async function initialize() {
  try {
    const mobile = await isMobile();

    if (!mobile) {
      console.log('Not running on mobile, skipping native features init');
      return;
    }

    // Add app state listener
    await addAppStateListener((state) => {
      console.log('App state changed:', state.isActive ? 'active' : 'inactive');
    });

    console.log('Native features initialized successfully');
  } catch (error) {
    console.error('Native features initialization error:', error);
  }
}

/**
 * Request all necessary permissions
 * @returns {Promise<Object>} Granted permissions status
 */
export async function requestAllPermissions() {
  const permissions = {
    push: false,
    biometric: false
  };

  try {
    // Push notifications
    permissions.push = await PushNotifications.checkPermission();

    // Biometric
    const biometricCaps = await BiometricAuth.checkBiometricCapabilities();
    permissions.biometric = biometricCaps.supported;
  } catch (error) {
    console.error('Request permissions error:', error);
  }

  return permissions;
}

// Export all services
export {
  PushNotifications,
  BiometricAuth
};

export default {
  // Device info
  getDeviceInfo,
  isMobile,
  isIOS,
  isAndroid,

  // Haptics
  hapticImpact,
  hapticNotification,

  // Keyboard
  setKeyboard,
  isKeyboardVisible,

  // App lifecycle
  addAppStateListener,
  addUrlOpenListener,
  getAppInfo,
  exitApp,
  minimizeApp,

  // Push notifications
  ...PushNotifications,

  // Biometric
  ...BiometricAuth,

  // Utilities
  initialize,
  requestAllPermissions
};
