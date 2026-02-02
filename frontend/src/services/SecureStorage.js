/**
 * =============================================================
 * SecureStorage - Secure Storage Service for NexControl
 * =============================================================
 * Provides secure storage for sensitive data using Capacitor
 * Falls back to localStorage when not in mobile environment
 */

import { Preferences } from '@capacitor/preferences';

/**
 * Set a value in secure storage
 * @param {string} key - Storage key
 * @param {string} value - Value to store
 */
export async function setItem(key, value) {
  try {
    await Preferences.set({
      key,
      value
    });
    return true;
  } catch (error) {
    console.error('SecureStorage set error:', error);
    // Fallback to localStorage
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (fallbackError) {
      console.error('localStorage fallback error:', fallbackError);
      return false;
    }
  }
}

/**
 * Get a value from secure storage
 * @param {string} key - Storage key
 * @returns {Promise<string|null>} Stored value or null
 */
export async function getItem(key) {
  try {
    const { value } = await Preferences.get({ key });
    return value;
  } catch (error) {
    console.error('SecureStorage get error:', error);
    // Fallback to localStorage
    try {
      return localStorage.getItem(key);
    } catch (fallbackError) {
      console.error('localStorage fallback error:', fallbackError);
      return null;
    }
  }
}

/**
 * Remove a value from secure storage
 * @param {string} key - Storage key
 */
export async function removeItem(key) {
  try {
    await Preferences.remove({ key });
    return true;
  } catch (error) {
    console.error('SecureStorage remove error:', error);
    // Fallback to localStorage
    try {
      localStorage.removeItem(key);
      return true;
    } catch (fallbackError) {
      console.error('localStorage fallback error:', fallbackError);
      return false;
    }
  }
}

/**
 * Clear all secure storage
 */
export async function clear() {
  try {
    await Preferences.clear();
    return true;
  } catch (error) {
    console.error('SecureStorage clear error:', error);
    // Fallback to localStorage
    try {
      localStorage.clear();
      return true;
    } catch (fallbackError) {
      console.error('localStorage fallback error:', fallbackError);
      return false;
    }
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
