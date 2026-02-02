/**
 * =============================================================
 * SecureStorage - Secure Storage Service for NexControl
 * =============================================================
 * Provides secure storage for sensitive data using Capacitor
 * Falls back to localStorage when not in mobile environment
 */

// Dynamic import for Capacitor plugins to avoid build errors in web
let Preferences = null;

// Check if running in Capacitor environment
const isCapacitor = () => {
  return typeof window !== 'undefined' && window.Capacitor;
};

/**
 * Initialize Capacitor Preferences (lazy load)
 */
async function initPreferences() {
  if (Preferences || !isCapacitor()) {
    return;
  }

  try {
    const module = await import('@capacitor/preferences');
    Preferences = module.Preferences;
  } catch (error) {
    console.warn('Capacitor Preferences not available:', error);
  }
}

/**
 * Set a value in secure storage
 * @param {string} key - Storage key
 * @param {string} value - Value to store
 */
export async function setItem(key, value) {
  try {
    await initPreferences();

    if (Preferences && isCapacitor()) {
      await Preferences.set({ key, value });
      return true;
    }
  } catch (error) {
    console.warn('SecureStorage set error:', error);
  }

  // Fallback to localStorage
  try {
    localStorage.setItem(key, value);
    return true;
  } catch (fallbackError) {
    console.error('localStorage fallback error:', fallbackError);
    return false;
  }
}

/**
 * Get a value from secure storage
 * @param {string} key - Storage key
 * @returns {Promise<string|null>} Stored value or null
 */
export async function getItem(key) {
  try {
    await initPreferences();

    if (Preferences && isCapacitor()) {
      const { value } = await Preferences.get({ key });
      if (value !== null) {
        return value;
      }
    }
  } catch (error) {
    console.warn('SecureStorage get error:', error);
  }

  // Fallback to localStorage
  try {
    return localStorage.getItem(key);
  } catch (fallbackError) {
    console.error('localStorage fallback error:', fallbackError);
    return null;
  }
}

/**
 * Remove a value from secure storage
 * @param {string} key - Storage key
 */
export async function removeItem(key) {
  try {
    await initPreferences();

    if (Preferences && isCapacitor()) {
      await Preferences.remove({ key });
      return true;
    }
  } catch (error) {
    console.warn('SecureStorage remove error:', error);
  }

  // Fallback to localStorage
  try {
    localStorage.removeItem(key);
    return true;
  } catch (fallbackError) {
    console.error('localStorage fallback error:', fallbackError);
    return false;
  }
}

/**
 * Clear all secure storage
 */
export async function clear() {
  try {
    await initPreferences();

    if (Preferences && isCapacitor()) {
      await Preferences.clear();
    }
  } catch (error) {
    console.warn('SecureStorage clear error:', error);
  }

  // Fallback to localStorage
  try {
    localStorage.clear();
    return true;
  } catch (fallbackError) {
    console.error('localStorage fallback error:', fallbackError);
    return false;
  }
}

/**
 * Keys used in the app
 */
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'nexcontrol_auth_token',
  REFRESH_TOKEN: 'nexcontrol_refresh_token',
  SERVER_CONFIG: 'nexcontrol_server_config',
  BIOMETRIC_ENABLED: 'nexcontrol_biometric_enabled',
  THEME: 'nexcontrol_theme',
  LANGUAGE: 'nexcontrol_language'
};

export default {
  setItem,
  getItem,
  removeItem,
  clear,
  STORAGE_KEYS
};
