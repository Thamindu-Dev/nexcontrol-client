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
 * ApiService - HTTP Client for Backend Communication
 * =============================================================
 * Handles all HTTP requests to the NexControl backend
 * Supports both encrypted and unencrypted endpoints
 *
 * Features:
 * - Environment-aware base URL configuration
 * - JWT token management with secure storage
 * - Request/Response interceptors
 * - Automatic encryption for sensitive endpoints
 * - Error handling and token refresh
 */

import { encryptPayload, decryptResponse } from './EncryptionService';
import { getApiBaseUrl } from './EnvConfig';
import { getItem as getSecureItem, setItem as setSecureItem, removeItem as removeSecureItem, STORAGE_KEYS } from './SecureStorage';

/**
 * Get stored JWT token from secure storage
 */
async function getToken() {
  try {
    // Try secure storage first (mobile)
    return await getSecureItem(STORAGE_KEYS.AUTH_TOKEN);
  } catch {
    // Fallback to localStorage for web
    return localStorage.getItem('nexcontrol_token');
  }
}

/**
 * Check if AES encryption key is configured
 * @returns {boolean} True if key exists and is valid (>= 32 characters)
 */
function hasEncryptionKey() {
  const key = localStorage.getItem('nexcontrol_aes_key');
  return !!(key && key.length >= 32);
}

// Track last security notification time to prevent duplicates
let lastSecurityNotificationTime = 0;
const SECURITY_NOTIFICATION_DEBOUNCE = 3000; // 3 seconds

/**
 * Show security notification and redirect to settings
 * This is a fallback when Quasar is not available
 */
function showSecurityAlert(message) {
  console.error('[Security] ' + message);

  // Check if we recently showed a security notification to prevent duplicates
  const now = Date.now();
  if (now - lastSecurityNotificationTime < SECURITY_NOTIFICATION_DEBOUNCE) {
    console.log('[Security] Skipping duplicate security notification');
    return; // Skip duplicate
  }
  lastSecurityNotificationTime = now;

  // Try to use Quasar notify if available
  if (window.Quasar && window.Quasar.Notify) {
    window.Quasar.Notify.create({
      type: 'warning',
      message: message,
      caption: 'Configure it in Settings',
      position: 'top',
      timeout: 5000
    });
  } else {
    // Fallback to alert
    alert(message + '\n\nPlease configure it in Settings.');
  }

  // Redirect to settings after a short delay
  setTimeout(() => {
    if (!window.location.hash.includes('settings')) {
      window.location.href = '/#/settings';
    }
  }, 1500);
}

/**
 * Set JWT token in secure storage
 */
async function setToken(token) {
  try {
    await setSecureItem(STORAGE_KEYS.AUTH_TOKEN, token);
  } catch {
    // Fallback to localStorage
    localStorage.setItem('nexcontrol_token', token);
  }
}

/**
 * Clear JWT token (logout)
 */
export async function clearToken() {
  try {
    await removeSecureItem(STORAGE_KEYS.AUTH_TOKEN);
    await removeSecureItem(STORAGE_KEYS.REFRESH_TOKEN);
  } catch {
    localStorage.removeItem('nexcontrol_token');
  }
}

/**
 * Get server configuration
 */
export function getServerConfig() {
  const stored = localStorage.getItem('nexcontrol_server_config');
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      // Return default if invalid
    }
  }
  return {
    protocol: 'http',
    host: 'localhost',
    port: 8000
  };
}

/**
 * Set server configuration
 */
export function setServerConfig(config) {
  localStorage.setItem('nexcontrol_server_config', JSON.stringify(config));
}

/**
 * Handle API errors
 */
function handleApiError(response, errorData) {
  // Handle 401 Unauthorized - token expired or invalid encryption
  if (response.status === 401) {
    console.error('[Security] Authentication failed:', {
      status: response.status,
      error: errorData
    });

    // Check if it's an encryption/decryption error
    const isDecryptionError = errorData.detail?.toLowerCase().includes('decrypt') ||
                             errorData.message?.toLowerCase().includes('decrypt') ||
                             errorData.detail?.toLowerCase().includes('encryption') ||
                             errorData.message?.toLowerCase().includes('encryption');

    if (isDecryptionError) {
      // Decryption error means the AES key is wrong
      showSecurityAlert('🚫 Authentication Failed. Check your Encryption Key in Settings.');
      throw new Error('Encryption key mismatch. Please verify your key matches the backend.');
    } else {
      // Regular 401 - token issue
      clearToken();
      if (!window.location.hash.includes('login')) {
        window.location.href = '/#/login';
      }
      throw new Error('Authentication required. Please login again.');
    }
  }

  // Handle 403 Forbidden
  if (response.status === 403) {
    throw new Error('You do not have permission to perform this action.');
  }

  // Handle 404 Not Found
  if (response.status === 404) {
    throw new Error('The requested resource was not found.');
  }

  // Handle 500 Server Error
  if (response.status >= 500) {
    throw new Error('Server error. Please try again later.');
  }

  // Default error message
  throw new Error(errorData.detail || errorData.message || 'Request failed');
}

/**
 * Create API client with base configuration
 */
const api = {
  /**
   * Get current base URL
   */
  get baseURL() {
    return getApiBaseUrl();
  },

  /**
   * Make an API request
   *
   * @param {string} endpoint - API endpoint path
   * @param {string} method - HTTP method
   * @param {Object} data - Request data
   * @param {boolean} encrypted - Whether to encrypt payload
   * @returns {Promise} Response data
   */
  async request(endpoint, method = 'GET', data = null, encrypted = false) {
    try {
      const url = `${this.baseURL}${endpoint}`;
      console.log('[API Request]', method, url);

      // ============================================
      // PRE-FLIGHT SECURITY CHECK
      // ============================================
      // Check for encryption key before making any request
      // Skip check for login/register/test/stats endpoints (these don't require encryption)
      // Stats endpoints are allowed without key so users can view dashboard
      const skipSecurityCheck = [
        '/api/auth/login',
        '/api/auth/register',
        '/api/auth/refresh',
        '/api/auth/verify',
        '/api/test/connection',
        '/api/test/echo',
        '/api/stats/cpu',
        '/api/stats/memory',
        '/api/stats/gpu',
        '/api/stats/disk',
        '/api/stats/system',
        '/api/system/info',
        '/api/media/status'
      ].some(path => endpoint.includes(path));

      if (!skipSecurityCheck && !hasEncryptionKey()) {
        console.warn('[Security] Blocking request - No AES key configured:', endpoint);
        showSecurityAlert('⚠️ Security Key Missing. Please configure it in Settings.');
        // Throw a special error type that can be identified to prevent duplicate notifications
        const error = new Error('Security key missing. Please configure encryption key in Settings.');
        error.isSecurityError = true; // Mark as security error
        throw error;
      }
      // ============================================

      // Get token without timeout - let it resolve naturally
      const token = await getToken().catch(() => null);

      // Prepare headers
      const headers = {
        'Content-Type': 'application/json'
      };

      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Prepare request options with longer timeout (30 seconds)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const options = {
        method,
        headers,
        signal: controller.signal
      };

      // Add body for POST/PUT/PATCH
      if (data && ['POST', 'PUT', 'PATCH'].includes(method.toUpperCase())) {
        if (encrypted) {
          // Encrypt the payload
          const encryptedData = encryptPayload(data);
          options.body = JSON.stringify(encryptedData);
        } else {
          options.body = JSON.stringify(data);
        }
      }

      console.log('[API Request] Sending to:', url);

      // Make the request
      const response = await fetch(url, options);

      // Clear timeout
      clearTimeout(timeoutId);

      console.log('[API Response] Status:', response.status);

      // Handle non-OK responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return handleApiError(response, errorData);
      }

      // Parse response
      const responseData = await response.json();

      // Decrypt if response contains encrypted data
      // Only decrypt if data is a string (encrypted), not an object (plain JSON)
      if (responseData.data && typeof responseData.data === 'string') {
        return decryptResponse(responseData);
      }

      return responseData;
    } catch (error) {
      console.error('[API] Request failed:', error);

      // Handle abort errors specifically
      if (error.name === 'AbortError') {
        console.error('[API] Request timeout or aborted:', endpoint);
        throw new Error('Request timeout. Please check your connection and try again.');
      }

      // Handle decryption/encryption errors
      const errorMessage = error.message || error.toString();
      if (errorMessage.includes('decrypt') ||
          errorMessage.includes('decrypt') ||
          errorMessage.includes('encrypt') ||
          errorMessage.includes('AES') ||
          errorMessage.includes('base64')) {
        console.error('[Security] Decryption error:', error);
        showSecurityAlert('🚫 Authentication Failed. Check your Encryption Key in Settings.');
        throw new Error('Decryption failed. Your encryption key may not match the server.');
      }

      // Enhanced network error handling
      if (error.message && error.message.includes('fetch')) {
        // Network fetch failed
        if (typeof window !== 'undefined' && window.Capacitor) {
          const platform = window.Capacitor.getPlatform();
          if (platform === 'ios') {
            console.error('[API] iOS Network Error - Possibly blocked by ATS');
            throw new Error('iOS Network Error: Cannot reach server. Ensure Local Network permission is allowed in iOS Settings.');
          } else if (platform === 'android') {
            throw new Error('Android Network Error: Cannot reach server. Check if the app has permission to access your local network.');
          }
        }
        throw new Error('Network Error: Cannot reach server. Check IP address and ensure both devices are on the same network.');
      }

      // Re-throw API errors with message
      if (error.message) {
        throw error;
      }

      // Generic network error
      console.error('[API] Unknown network error:', error);
      throw new Error(`Network error: ${errorMessage}`);
    }
  },

  /**
   * GET request
   */
  async get(endpoint) {
    return this.request(endpoint, 'GET');
  },

  /**
   * POST request
   */
  async post(endpoint, data, encrypted = false) {
    return this.request(endpoint, 'POST', data, encrypted);
  },

  /**
   * PUT request
   */
  async put(endpoint, data, encrypted = false) {
    return this.request(endpoint, 'PUT', data, encrypted);
  },

  /**
   * DELETE request
   */
  async delete(endpoint) {
    return this.request(endpoint, 'DELETE');
  },

  /**
   * Login with password
   */
  async login(password) {
    const response = await this.post('/api/auth/login', { password });
    if (response.access_token) {
      await setToken(response.access_token);
    }
    return response;
  },

  /**
   * Logout
   */
  async logout() {
    await clearToken();
  },

  /**
   * Check if authenticated
   */
  async isAuthenticated() {
    const token = await getToken();
    return !!token;
  },

  /**
   * Get current auth token
   */
  async getToken() {
    return getToken();
  }
};

export default api;
