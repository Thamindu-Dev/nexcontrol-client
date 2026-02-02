/**
 * =============================================================
 * Auth Store - Authentication State Management
 * =============================================================
 * Manages user authentication state using Pinia
 * Handles login, logout, and JWT token storage
 */

import { defineStore } from 'pinia';
import api from '../services/ApiService';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('nexcontrol_token') || null,
    user: null,
    isAuthenticated: false,
    loginError: null,
    serverConnected: false
  }),

  getters: {
    /**
     * Get authentication token
     */
    getToken: (state) => state.token,

    /**
     * Check if user is authenticated
     */
    isLoggedIn: (state) => state.isAuthenticated && !!state.token,

    /**
     * Get current user info
     */
    getUser: (state) => state.user
  },

  actions: {
    /**
     * Login with password
     */
    async login(password) {
      try {
        this.loginError = null;

        // Call login API
        const response = await api.login(password);

        if (response.access_token) {
          this.token = response.access_token;
          this.isAuthenticated = true;
          this.user = { sub: 'nexcontrol_user' };
          this.serverConnected = true;

          // Store token in Pinia state
          this.token = response.access_token;

          return { success: true };
        }
      } catch (error) {
        this.loginError = error.message || 'Login failed';
        this.isAuthenticated = false;
        this.token = null;

        return { success: false, error: this.loginError };
      }
    },

    /**
     * Logout user
     */
    async logout() {
      try {
        await api.logout();
      } catch (error) {
        console.error('Logout error:', error);
      } finally {
        this.token = null;
        this.isAuthenticated = false;
        this.user = null;
        this.loginError = null;
      }
    },

    /**
     * Verify token validity
     */
    async verifyToken() {
      if (!this.token) {
        this.isAuthenticated = false;
        return false;
      }

      try {
        await api.get('/api/auth/verify');
        this.isAuthenticated = true;
        this.serverConnected = true;
        return true;
      } catch {
        // Token is invalid or expired
        this.token = null;
        this.isAuthenticated = false;
        this.serverConnected = false;
        return false;
      }
    },

    /**
     * Set token manually (for testing)
     */
    setToken(token) {
      this.token = token;
      this.isAuthenticated = !!token;
    },

    /**
     * Clear login error
     */
    clearLoginError() {
      this.loginError = null;
    },

    /**
     * Set server connection status
     */
    setServerConnected(connected) {
      this.serverConnected = connected;
    }
  }
});
