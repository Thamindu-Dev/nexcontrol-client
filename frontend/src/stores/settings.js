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
 * Settings Store - Application Settings
 * =============================================================
 * Manages application settings including:
 * - Server configuration (IP, port)
 * - AES encryption key
 * - Auto-connect preferences
 * - Display preferences
 */

import { defineStore } from 'pinia';
import { setAESKey as setEncryptionKey } from '../services/EncryptionService';
import { setServerConfig } from '../services/ApiService';

const SERVER_CONFIG_KEY = 'nexcontrol_server_config';
const AES_KEY_KEY = 'nexcontrol_aes_key';
const PREFS_KEY = 'nexcontrol_preferences';
const WOL_DEVICES_KEY = 'nexcontrol_wol_devices';

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    // Server configuration
    server: {
      protocol: 'http',
      host: 'localhost',
      port: 8000
    },

    // Encryption key (will not expose actual key in state)
    hasEncryptionKey: !!localStorage.getItem(AES_KEY_KEY),

    // Preferences
    preferences: {
      autoConnect: false,
      refreshInterval: 5000, // 5 seconds
      theme: 'dark', // 'light' or 'dark'
      notifications: true,
      showToastMessages: true
    },

    // WoL devices
    woLDevices: []
  }),

  getters: {
    /**
     * Get server URL
     */
    getServerUrl: (state) => {
      const { protocol, host, port } = state.server;
      return `${protocol}://${host}:${port}`;
    },

    /**
     * Get refresh interval in seconds
     */
    getRefreshInterval: (state) => {
      return state.preferences.refreshInterval;
    },

    /**
     * Check if encryption key is set
     */
    hasKey: (state) => state.hasEncryptionKey,

    /**
     * Get WoL devices
     */
    getWoLDevices: (state) => state.woLDevices
  },

  actions: {
    /**
     * Update server configuration
     */
    updateServer(config) {
      this.server = { ...this.server, ...config };

      // Save to localStorage
      localStorage.setItem(SERVER_CONFIG_KEY, JSON.stringify(this.server));

      // Update API service
      setServerConfig(this.server);
    },

    /**
     * Set encryption key
     */
    setEncryptionKey(key) {
      if (key && key.length >= 32) {
        const truncatedKey = key.substring(0, 32);
        localStorage.setItem(AES_KEY_KEY, truncatedKey);

        // Update the encryption service
        setEncryptionKey(truncatedKey);

        this.hasEncryptionKey = true;
        return true;
      }
      return false;
    },

    /**
     * Clear encryption key
     */
    clearEncryptionKey() {
      localStorage.removeItem(AES_KEY_KEY);
      this.hasEncryptionKey = false;
    },

    /**
     * Update preferences
     */
    updatePreferences(prefs) {
      this.preferences = { ...this.preferences, ...prefs };

      // Save to localStorage
      localStorage.setItem(PREFS_KEY, JSON.stringify(this.preferences));
    },

    /**
     * Set WoL devices
     */
    setWoLDevices(devices) {
      this.woLDevices = devices;
      localStorage.setItem(WOL_DEVICES_KEY, JSON.stringify(devices));
    },

    /**
     * Load settings from localStorage
     */
    loadSettings() {
      // Load server config
      const serverConfig = localStorage.getItem(SERVER_CONFIG_KEY);
      if (serverConfig) {
        try {
          this.server = JSON.parse(serverConfig);
          setServerConfig(this.server);
        } catch (e) {
          console.error('Failed to load server config:', e);
        }
      }

      // Check encryption key
      this.hasEncryptionKey = !!localStorage.getItem(AES_KEY_KEY);

      // Load preferences
      const prefs = localStorage.getItem(PREFS_KEY);
      if (prefs) {
        try {
          this.preferences = { ...this.preferences, ...JSON.parse(prefs) };
        } catch (e) {
          console.error('Failed to load preferences:', e);
        }
      }

      // Load WoL devices
      const wolDevices = localStorage.getItem(WOL_DEVICES_KEY);
      if (wolDevices) {
        try {
          this.woLDevices = JSON.parse(wolDevices);
        } catch (e) {
          console.error('Failed to load WoL devices:', e);
        }
      }
    },

    /**
     * Reset all settings to default
     */
    resetSettings() {
      // Clear localStorage
      localStorage.removeItem(SERVER_CONFIG_KEY);
      localStorage.removeItem(AES_KEY_KEY);
      localStorage.removeItem(PREFS_KEY);
      localStorage.removeItem(WOL_DEVICES_KEY);

      // Reset state
      this.server = {
        protocol: 'http',
        host: 'localhost',
        port: 8000
      };
      this.hasEncryptionKey = false;
      this.preferences = {
        autoConnect: false,
        refreshInterval: 5000,
        theme: 'dark',
        notifications: true,
        showToastMessages: true
      };
      this.woLDevices = [];
    }
  }
});
