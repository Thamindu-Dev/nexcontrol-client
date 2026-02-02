/**
 * =============================================================
 * BiometricAuth - Biometric Authentication Service
 * =============================================================
 * Handles TouchID/FaceID authentication on mobile devices
 *
 * Note: For production, consider using @capacitor-community/capacitor-biometric-auth
 * This service provides a framework for biometric authentication
 */

import { getItem, setItem, removeItem, STORAGE_KEYS } from './SecureStorage';

// Check if running in Capacitor environment
const isCapacitor = () => {
  return typeof window !== 'undefined' && window.Capacitor;
};

/**
 * Check if device supports biometric authentication
 * @returns {Promise<Object>} Device capabilities
 */
export async function checkBiometricCapabilities() {
  try {
    if (!isCapacitor()) {
      return {
        isMobile: false,
        platform: 'web',
        hasFaceId: false,
        hasTouchId: false,
        hasFingerprint: false,
        supported: false
      };
    }

    const { Device } = await import('@capacitor/device');
    const info = await Device.getInfo();

    // Check if running on mobile platform
    const isMobile = info.platform === 'ios' || info.platform === 'android';

    return {
      isMobile,
      platform: info.platform,
      // These would be determined by a proper biometric plugin
      hasFaceId: isMobile && info.platform === 'ios',
      hasTouchId: isMobile && info.platform === 'ios',
      hasFingerprint: isMobile && info.platform === 'android',
      supported: isMobile
    };
  } catch (error) {
    console.error('Biometric capability check error:', error);
    return {
      isMobile: false,
      platform: 'web',
      hasFaceId: false,
      hasTouchId: false,
      hasFingerprint: false,
      supported: false
    };
  }
}

/**
 * Prompt user for biometric authentication
 * @param {string} reason - Reason for authentication prompt
 * @returns {Promise<boolean>} Authentication success
 */
// eslint-disable-next-line no-unused-vars
export async function authenticate(reason = 'Authenticate to access NexControl') {
  try {
    const capabilities = await checkBiometricCapabilities();

    if (!capabilities.supported) {
      console.warn('Biometric authentication not supported on this device');
      return false;
    }

    // Check if user has enabled biometric auth
    const enabled = await getItem(STORAGE_KEYS.BIOMETRIC_ENABLED);
    if (enabled !== 'true') {
      return false; // Not enabled by user
    }

    // TODO: Integrate with @capacitor-community/capacitor-biometric-auth
    // For now, return true (simulation)
    // In production:
    // const result = await BiometricAuth.verify({ reason });
    // return result.success;

    console.warn('Biometric auth plugin not installed. Returning simulation result.');
    return true;
  } catch (error) {
    console.error('Biometric authentication error:', error);
    // Common error codes:
    // - 'user_cancel': User cancelled authentication
    // - 'not_available': Biometric not available
    // - 'not_enrolled': No biometric enrolled
    // - 'authentication_failed': Authentication failed
    if (error.code === 'user_cancel') {
      return false;
    }
    throw error;
  }
}

/**
 * Enable biometric authentication for the app
 */
export async function enableBiometric() {
  try {
    const capabilities = await checkBiometricCapabilities();
    if (!capabilities.supported) {
      throw new Error('Biometric authentication not supported on this device');
    }

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

    if (capabilities.hasFaceId) {
      methods.push('Face ID');
    }
    if (capabilities.hasTouchId) {
      methods.push('Touch ID');
    }
    if (capabilities.hasFingerprint) {
      methods.push('Fingerprint');
    }

    return {
      available: methods.length > 0,
      methods,
      primary: methods[0] || null
    };
  } catch (error) {
    console.error('Get available methods error:', error);
    return {
      available: false,
      methods: [],
      primary: null
    };
  }
}

export default {
  checkBiometricCapabilities,
  authenticate,
  enableBiometric,
  disableBiometric,
  isBiometricEnabled,
  getAvailableMethods
};
