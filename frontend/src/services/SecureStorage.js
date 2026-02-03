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
 * SecureStorage - Secure Storage Service for NexControl
 * =============================================================
 * Provides secure storage for sensitive data using Capacitor
 * Falls back to localStorage when not in mobile environment
 */

// Dynamic import for Capacitor plugins to avoid build errors in web
let Preferences = null;
let preferencesInitStarted = false;
let preferencesReady = false;

// Check if running in Capacitor environment
const isCapacitor = () => {
  return typeof window !== 'undefined' && window.Capacitor;
};

/**
 * Initialize Capacitor Preferences (lazy load with caching)
 */
async function initPreferences() {
  // Return early if already ready
  if (preferencesReady || !isCapacitor()) {
    return;
  }

  // Return early if initialization already started (to prevent parallel imports)
  if (preferencesInitStarted) {
    // Wait up to 2 seconds for initialization
    const maxWait = 20;
    let waited = 0;
    while (!preferencesReady && waited < maxWait) {
      await new Promise(resolve => setTimeout(resolve, 100));
      waited++;
    }
    return;
  }

  preferencesInitStarted = true;

  try {
    // Add timeout to prevent hanging
    const module = await Promise.race([
      import('@capacitor/preferences'),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Preferences import timeout')), 3000)
      )
    ]);
    Preferences = module.Preferences;
    preferencesReady = true;
  } catch (error) {
    console.warn('Capacitor Preferences not available:', error);
    preferencesReady = false;
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
  AUTH_TOKEN: 'nexcontrol_token',
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
