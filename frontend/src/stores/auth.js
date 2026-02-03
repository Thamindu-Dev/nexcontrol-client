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
     * Check if JWT token is expired
     * @param {string} token - JWT token
     * @returns {boolean} True if expired
     */
    isTokenExpired(token) {
      if (!token) return true

      try {
        // JWT format: header.payload.signature
        const parts = token.split('.')
        if (parts.length !== 3) return true

        // Decode payload (base64url)
        const payload = JSON.parse(atob(parts[1]))
        const now = Math.floor(Date.now() / 1000)

        // Check if token is expired or will expire in next 5 minutes
        return payload.exp < (now - 300)
      } catch {
        return true
      }
    },

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

      // Check token expiration first (before making API call)
      if (this.isTokenExpired(this.token)) {
        this.token = null;
        this.isAuthenticated = false;
        this.serverConnected = false;
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
