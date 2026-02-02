/**
 * =============================================================
 * ApiService - HTTP Client for Backend Communication
 * =============================================================
 * Handles all HTTP requests to the NexControl backend
 * Supports both encrypted and unencrypted endpoints
 *
 * Features:
 * - Base URL configuration
 * - JWT token management
 * - Request/Response interceptors
 * - Automatic encryption for sensitive endpoints
 */

import { encryptPayload, decryptResponse } from './EncryptionService';

// Configuration
const TOKEN_STORAGE_KEY = 'nexcontrol_token';
const SERVER_CONFIG_KEY = 'nexcontrol_server_config';

/**
 * Get the base URL from localStorage or use default
 */
function getBaseUrl() {
  const config = getServerConfig();
  return `${config.protocol}://${config.host}:${config.port}`;
}

/**
 * Get server configuration
 */
function getServerConfig() {
  const stored = localStorage.getItem(SERVER_CONFIG_KEY);
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
  localStorage.setItem(SERVER_CONFIG_KEY, JSON.stringify(config));
}

/**
 * Get stored JWT token
 */
function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

/**
 * Set JWT token
 */
function setToken(token) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

/**
 * Clear JWT token (logout)
 */
export function clearToken() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

/**
 * Create axios instance with base configuration
 */
const api = {
  baseURL: getBaseUrl(),

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
      const token = getToken();

      // Prepare headers
      const headers = {
        'Content-Type': 'application/json'
      };

      // Add Authorization header if token exists
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Prepare request options
      const options = {
        method,
        headers
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

      // Make the request
      const response = await fetch(url, options);

      // Handle non-OK responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: response.statusText
        }));
        throw new Error(errorData.detail || 'Request failed');
      }

      // Parse response
      const responseData = await response.json();

      // Decrypt if response contains encrypted data
      if (responseData.data) {
        return decryptResponse(responseData);
      }

      return responseData;
    } catch (error) {
      console.error('API request error:', error);
      throw error;
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
      setToken(response.access_token);
    }
    return response;
  },

  /**
   * Logout
   */
  async logout() {
    clearToken();
  },

  /**
   * Check if authenticated
   */
  isAuthenticated() {
    return !!getToken();
  },

  /**
   * Update base URL (call this after changing server config)
   */
  updateBaseUrl() {
    this.baseURL = getBaseUrl();
  }
};

export default api;
