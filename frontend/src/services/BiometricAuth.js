/**
 * =============================================================================
 * NexControl - Remote PC Controller
 * Copyright (C) 2026 Thamindu-Dev
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * =============================================================================
 */

/**
 * =============================================================
 * BiometricAuth - Biometric Authentication Service
 * =============================================================
 * Handles TouchID/FaceID authentication on mobile devices
 * Uses @capacitor-community/capacitor-biometric-auth plugin
 */

import { getItem, setItem, removeItem, STORAGE_KEYS } from './SecureStorage';

// Check if running in Capacitor environment
const isCapacitor = () => {
  return typeof window !== 'undefined' && window.Capacitor;
};

// Lazy load BiometricAuth plugin
let BiometricAuth = null;

async function getBiometricAuth() {
  if (BiometricAuth) return BiometricAuth;

  if (!isCapacitor()) {
    return null;
  }

  try {
    const plugin = await import('@capacitor-community/capacitor-biometric-auth');
    BiometricAuth = plugin.BiometricAuth;
    return BiometricAuth;
  } catch (error) {
    console.error('Failed to load BiometricAuth plugin:', error);
    return null;
  }
}

/**
 * Check if device supports biometric authentication
 * @returns {Promise<Object>} Device capabilities
 */
export async function checkBiometricCapabilities() {
  try {
    const auth = await getBiometricAuth();

    if (!auth) {
      return {
        isMobile: false,
        platform: 'web',
        hasFaceId: false,
        hasTouchId: false,
        hasFingerprint: false,
        supported: false
      };
    }

    const result = await auth.isAvailable();

    return {
      isMobile: true,
      platform: await getPlatform(),
      hasFaceId: result.has === true,
      hasTouchId: result.has === true,
      hasFingerprint: result.has === true,
      supported: result.has || false,
      reason: result.reason || null
    };
  } catch (error) {
    console.error('Biometric capability check error:', error);
    return {
      isMobile: isCapacitor(),
      platform: await getPlatform(),
      hasFaceId: false,
      hasTouchId: false,
      hasFingerprint: false,
      supported: false,
      error: error.message
    };
  }
}

/**
 * Get current platform
 */
async function getPlatform() {
  if (!isCapacitor()) return 'web';

  try {
    const { Device } = await import('@capacitor/device');
    const info = await Device.getInfo();
    return info.platform;
  } catch {
    return 'unknown';
  }
}

/**
 * Prompt user for biometric authentication
 * @param {string} reason - Reason for authentication prompt
 * @returns {Promise<boolean>} Authentication success
 */
export async function authenticate(reason = 'Authenticate to access NexControl') {
  try {
    const auth = await getBiometricAuth();

    if (!auth) {
      console.warn('BiometricAuth plugin not available');
      return false;
    }

    // Check if user has enabled biometric auth
    const enabled = await getItem(STORAGE_KEYS.BIOMETRIC_ENABLED);
    if (enabled !== 'true') {
      return false; // Not enabled by user
    }

    // Perform biometric authentication
    const result = await auth.verify({
      reason,
      title: 'NexControl',
      subtitle: 'Unlock to continue',
      description: 'Use your biometric to unlock the app'
    });

    console.log('Biometric auth result:', result);
    return true;

  } catch (error) {
    console.error('Biometric authentication error:', error);

    // Handle specific error codes
    if (error.code === 'user_cancel') {
      console.log('User cancelled biometric authentication');
      return false;
    }
    if (error.code === 'not_available') {
      console.warn('Biometric authentication not available');
      return false;
    }
    if (error.code === 'not_enrolled') {
      console.warn('No biometric enrolled on device');
      return false;
    }
    if (error.code === 'authentication_failed') {
      console.warn('Biometric authentication failed');
      return false;
    }

    return false;
  }
}

/**
 * Enable biometric authentication for the app
 */
export async function enableBiometric() {
  try {
    const auth = await getBiometricAuth();

    if (!auth) {
      throw new Error('BiometricAuth plugin not available');
    }

    // Check availability first
    const capabilities = await checkBiometricCapabilities();
    if (!capabilities.supported) {
      throw new Error(capabilities.reason || 'Biometric authentication not supported on this device');
    }

    // Store user preference
    await setItem(STORAGE_KEYS.BIOMETRIC_ENABLED, 'true');
    return true;
  } catch (error) {
    console.error('Enable biometric error:', error);
    throw error;
  }
}

/**
 * Disable biometric authentication
 */
export async function disableBiometric() {
  try {
    await removeItem(STORAGE_KEYS.BIOMETRIC_ENABLED);
    return true;
  } catch (error) {
    console.error('Disable biometric error:', error);
    return false;
  }
}

/**
 * Check if biometric authentication is enabled
 * @returns {Promise<boolean>} Enabled status
 */
export async function isBiometricEnabled() {
  try {
    const enabled = await getItem(STORAGE_KEYS.BIOMETRIC_ENABLED);
    return enabled === 'true';
  } catch (error) {
    console.error('Check biometric enabled error:', error);
    return false;
  }
}

/**
 * Get available biometric methods
 * @returns {Promise<Object>} Available methods
 */
export async function getAvailableMethods() {
  try {
    const capabilities = await checkBiometricCapabilities();
    const methods = [];

    if (!capabilities.supported) {
      return {
        available: false,
        methods: [],
        primary: null
      };
    }

    // Determine available methods based on platform
    if (capabilities.platform === 'ios') {
      if (capabilities.hasFaceId) {
        methods.push('Face ID');
      }
      if (capabilities.hasTouchId) {
        methods.push('Touch ID');
      }
    } else if (capabilities.platform === 'android') {
      if (capabilities.hasFingerprint) {
        methods.push('Fingerprint');
        methods.push('Face Unlock'); // Android face unlock
      }
    }

    return {
      available: methods.length > 0,
      methods,
      primary: methods[0] || null,
      platform: capabilities.platform
    };
  } catch (error) {
    console.error('Get available methods error:', error);
    return {
      available: false,
      methods: [],
      primary: null,
      error: error.message
    };
  }
}

/**
 * Check if biometric lock is currently active
 * @returns {Promise<boolean>} Lock status
 */
export async function isLocked() {
  try {
    const locked = await getItem(STORAGE_KEYS.BIOMETRIC_LOCKED);
    return locked === 'true';
  } catch (error) {
    return false;
  }
}

/**
 * Set biometric lock state
 * @param {boolean} locked - Lock state
 */
export async function setLocked(locked) {
  try {
    if (locked) {
      await setItem(STORAGE_KEYS.BIOMETRIC_LOCKED, 'true');
    } else {
      await removeItem(STORAGE_KEYS.BIOMETRIC_LOCKED);
    }
    return true;
  } catch (error) {
    console.error('Set locked state error:', error);
    return false;
  }
}

export default {
  checkBiometricCapabilities,
  authenticate,
  enableBiometric,
  disableBiometric,
  isBiometricEnabled,
  getAvailableMethods,
  isLocked,
  setLocked
};
