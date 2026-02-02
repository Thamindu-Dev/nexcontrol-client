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
 * - Uses Capacitor HTTP on mobile for better iOS compatibility
 */

import { encryptPayload, decryptResponse } from './EncryptionService';
import { getApiBaseUrl } from './EnvConfig';
import { getItem as getSecureItem, setItem as setSecureItem, removeItem as removeSecureItem, STORAGE_KEYS } from './SecureStorage';

// Capacitor HTTP plugin (dynamically imported for mobile)
let CapacitorHttp = null;

/**
 * Check if running in Capacitor environment
 */
const isCapacitor = () => {
  return typeof window !== 'undefined' && window.Capacitor;
};

/**
 * Initialize Capacitor HTTP (lazy load)
 */
async function initCapacitorHttp() {
  if (CapacitorHttp || !isCapacitor()) {
    return;
  }

  try {
    const module = await import('@capacitor/http');
    CapacitorHttp = module.CapacitorHttp;
  } catch (error) {
    console.warn('Capacitor HTTP not available:', error);
  }
}

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
  // Handle 401 Unauthorized - token expired or invalid
  if (response.status === 401) {
    clearToken();
    // Redirect to login (handled by router guard)
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new Error('Authentication required. Please login again.');
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
    await initCapacitorHttp();

    const url = `${this.baseURL}${endpoint}`;
    console.log('[API Request]', method, url, 'Capacitor:', !!CapacitorHttp);

    // Get token
    const token = await getToken().catch(() => null);

    // Prepare headers
    const headers = {
      'Content-Type': 'application/json'
    };

    // Add Authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Prepare request body
    let body = null;
    if (data && ['POST', 'PUT', 'PATCH'].includes(method.toUpperCase())) {
      if (encrypted) {
        body = encryptPayload(data);
      } else {
        body = data;
      }
    }

    try {
      // Use Capacitor HTTP on mobile, fetch on web
      if (CapacitorHttp && isCapacitor()) {
        console.log('[API] Using Capacitor HTTP');

        const options = {
          url,
          method: method.toLowerCase(),
          headers,
          connectTimeout: 30000,
          readTimeout: 30000
        };

        // Add body for POST/PUT/PATCH
        if (body) {
          options.data = body;
        }

        const response = await CapacitorHttp.options?.(options) ?? CapacitorHttp.request(options);
        console.log('[API] Capacitor Response Status:', response.status);

        // Handle non-OK responses
        if (response.status < 200 || response.status >= 300) {
          return handleApiError({ status: response.status }, response.data || {});
        }

        const responseData = response.data;

        // Decrypt if response contains encrypted data
        if (responseData.data) {
          return decryptResponse(responseData);
        }

        return responseData;
      } else {
        // Use fetch for web
        console.log('[API] Using fetch API');

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);

        const options = {
          method,
          headers,
          signal: controller.signal
        };

        if (body) {
          options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);
        clearTimeout(timeoutId);

        // Handle non-OK responses
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          return handleApiError(response, errorData);
        }

        const responseData = await response.json();

        // Decrypt if response contains encrypted data
        if (responseData.data) {
          return decryptResponse(responseData);
        }

        return responseData;
      }
    } catch (error) {
      console.error('[API] Error:', error);

      // Handle abort errors specifically
      if (error.name === 'AbortError' || error.message?.includes('timeout')) {
        throw new Error('Request timeout. Please check your connection and try again.');
      }

      // Re-throw API errors
      if (error.message) {
        throw error;
      }

      throw new Error('Network error. Please check your connection.');
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
