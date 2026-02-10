/**
 * =============================================================================
 * NexControl - Remote PC Controller
 * Copyright (C) 2026 Thamindu-Dev
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * =============================================================================
 */

/**
 * =============================================================
 * System Store - System Statistics & Monitoring
 * =============================================================
 * Manages real-time system statistics
 * Supports both polling and WebSocket (real-time) modes
 */

import { defineStore } from 'pinia';
import api from '../services/ApiService';
import { wsService, WebSocketState } from '../services/WebSocketService';
import { LocalNotifications } from '@capacitor/local-notifications';

export const useSystemStore = defineStore('system', {
  state: () => ({
    // Connection status
    isConnected: true,

    // System statistics
    stats: {
      cpu: { cpu_percent: 0, cpu_count: 0, cpu_freq_mhz: 0 },
      memory: { total: 0, used: 0, free: 0, percent: 0 },
      disk: { total: 0, used: 0, free: 0, percent: 0 },
      gpu: null,
      network: { bytes_sent: 0, bytes_recv: 0 },
      timestamp: 0
    },

    // Docker containers
    containers: [],
    dockerAvailable: false,

    // Processes
    processes: [],

    // Screenshot availability
    screenshotAvailable: false,

    // Threshold alerts history
    alerts: [],

    // Loading states
    loading: {
      stats: false,
      containers: false,
      processes: false
    },

    // Errors
    errors: {
      stats: null,
      containers: null,
      processes: null
    },

    // Auto-refresh (polling mode)
    autoRefresh: false,
    refreshInterval: 5000,
    refreshTimer: null,

    // WebSocket (real-time mode)
    webSocketEnabled: false,
    webSocketState: WebSocketState.DISCONNECTED,
    _wsEventHandlers: null,

    // Historical data for charts (max 60 data points = 5 minutes at 5-second interval)
    history: {
      cpu: [],
      memory: [],
      disk: [],
      timestamps: []
    },
    maxHistoryLength: 60,

    // Threshold configuration
    thresholdConfig: {
      enabled: false,
      cpu_threshold: 80,
      memory_threshold: 85,
      disk_threshold: 90
    },
    // Track last alert timestamp to avoid spam
    _lastAlertTime: {
      cpu: 0,
      memory: 0,
      disk: 0
    },
    // Minimum time between alerts (in milliseconds) - 5 minutes
    _alertCooldown: 5 * 60 * 1000
  }),

  getters: {
    /**
     * Get CPU usage percentage
     */
    cpuUsage: (state) => state.stats.cpu?.cpu_percent || 0,

    /**
     * Get memory usage percentage
     */
    memoryUsage: (state) => state.stats.memory?.percent || 0,

    /**
     * Get disk usage percentage
     */
    diskUsage: (state) => state.stats.disk?.percent || 0,

    /**
     * Get GPU usage percentage
     */
    gpuUsage: (state) => {
      if (state.stats.gpu?.usage) {
        return state.stats.gpu.usage.usage_percent;
      }
      return null;
    },

    /**
     * Get GPU name
     */
    gpuName: (state) => {
      if (state.stats.gpu?.usage) {
        return state.stats.gpu.usage.name;
      }
      return null;
    },

    /**
     * Get GPU temperature (fallback)
     */
    gpuTemp: (state) => {
      // Try new format first
      if (state.stats.gpu?.temperature?.gpus && state.stats.gpu.temperature.gpus.length > 0) {
        return state.stats.gpu.temperature.gpus[0].temperature_c;
      }
      // Try old format
      if (state.stats.gpu?.gpus && state.stats.gpu.gpus.length > 0) {
        return state.stats.gpu.gpus[0].temperature_c;
      }
      return null;
    },

    /**
     * Check if data is stale (older than 10 seconds)
     */
    isStale: (state) => {
      if (!state.stats.timestamp) return true;
      const now = Math.floor(Date.now() / 1000);
      return (now - state.stats.timestamp) > 10;
    },

    /**
     * Check if WebSocket is connected
     */
    isWebSocketConnected: (state) => {
      return state.webSocketEnabled && state.webSocketState === WebSocketState.CONNECTED;
    },

    /**
     * Get update mode (polling vs real-time)
     */
    updateMode: (state) => {
      return state.webSocketEnabled ? 'real-time' : 'polling';
    },

    /**
     * Get chart data for CPU usage
     * CRITICAL: Returns shallow copies to prevent infinite recursion with Chart.js
     */
    cpuChartData: (state) => {
      return {
        labels: [...state.history.timestamps].map(t => {
          const date = new Date(t);
          return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }),
        datasets: [{
          label: 'CPU Usage (%)',
          data: [...state.history.cpu], // Shallow copy prevents reactivity loop
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.4,
          fill: true,
          pointRadius: 2,
          pointHoverRadius: 5
        }]
      };
    },

    /**
     * Get chart data for Memory usage
     * CRITICAL: Returns shallow copies to prevent infinite recursion with Chart.js
     */
    memoryChartData: (state) => {
      return {
        labels: [...state.history.timestamps].map(t => {
          const date = new Date(t);
          return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }),
        datasets: [{
          label: 'Memory Usage (%)',
          data: [...state.history.memory], // Shallow copy prevents reactivity loop
          borderColor: 'rgb(153, 102, 255)',
          backgroundColor: 'rgba(153, 102, 255, 0.2)',
          tension: 0.4,
          fill: true,
          pointRadius: 2,
          pointHoverRadius: 5
        }]
      };
    },

    /**
     * Get chart data for Disk usage
     * CRITICAL: Returns shallow copies to prevent infinite recursion with Chart.js
     */
    diskChartData: (state) => {
      return {
        labels: [...state.history.timestamps].map(t => {
          const date = new Date(t);
          return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }),
        datasets: [{
          label: 'Disk Usage (%)',
          data: [...state.history.disk], // Shallow copy prevents reactivity loop
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.4,
          fill: true,
          pointRadius: 2,
          pointHoverRadius: 5
        }]
      };
    },

    /**
     * Get combined chart data for all metrics
     * CRITICAL: Returns shallow copies to prevent infinite recursion with Chart.js
     */
    combinedChartData: (state) => {
      return {
        labels: [...state.history.timestamps].map(t => {
          const date = new Date(t);
          return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }),
        datasets: [
          {
            label: 'CPU',
            data: [...state.history.cpu], // Shallow copy prevents reactivity loop
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            tension: 0.4
          },
          {
            label: 'Memory',
            data: [...state.history.memory], // Shallow copy prevents reactivity loop
            borderColor: 'rgb(153, 102, 255)',
            backgroundColor: 'rgba(153, 102, 255, 0.2)',
            tension: 0.4
          },
          {
            label: 'Disk',
            data: [...state.history.disk], // Shallow copy prevents reactivity loop
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            tension: 0.4
          }
        ]
      };
    },

    /**
     * Get WebSocket service instance
     */
    wsService: () => wsService,

    /**
     * Get all alerts
     */
    allAlerts: (state) => state.alerts,

    /**
     * Get unacknowledged alerts
     */
    unacknowledgedAlerts: (state) => {
      return state.alerts.filter(alert => !alert.acknowledged);
    },

    /**
     * Get alert count
     */
    alertCount: (state) => state.alerts.length,

    /**
     * Get unacknowledged alert count
     */
    unacknowledgedAlertCount: (state) => {
      return state.alerts.filter(alert => !alert.acknowledged).length;
    }
  },

  actions: {
    /**
     * Fetch all system statistics (polling mode)
     */
    async fetchStats() {
      // Fetch stats and update history
      // Even if WebSocket is connected, we want to ensure data is available
      this.loading.stats = true;
      this.errors.stats = null;

      try {
        const data = await api.get('/api/stats/all');
        console.log('[SystemStore] API Response Source: HTTP Polling');
        console.log('[SystemStore] Full API Response:', JSON.stringify(data, null, 2));
        console.log('[SystemStore] CPU Percent from API:', data?.cpu?.cpu_percent);
        console.log('[SystemStore] CPU Object:', data?.cpu);
        this.stats = data;
        this.isConnected = true;
        this.updateHistory(data);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
        this.errors.stats = error.message || 'Failed to fetch stats';
        this.isConnected = false;
      } finally {
        this.loading.stats = false;
      }
    },

    /**
     * Fetch CPU stats only
     */
    async fetchCPUStats() {
      try {
        const data = await api.get('/api/stats/cpu');
        this.stats.cpu = data;
        this.isConnected = true;
      } catch (error) {
        console.error('Failed to fetch CPU stats:', error);
        this.isConnected = false;
      }
    },

    /**
     * Fetch memory stats only
     */
    async fetchMemoryStats() {
      try {
        const data = await api.get('/api/stats/memory');
        this.stats.memory = data;
        this.isConnected = true;
      } catch (error) {
        console.error('Failed to fetch memory stats:', error);
        this.isConnected = false;
      }
    },

    /**
     * Fetch disk stats only
     */
    async fetchDiskStats() {
      try {
        const data = await api.get('/api/stats/disk');
        this.stats.disk = data;
        this.isConnected = true;
      } catch (error) {
        console.error('Failed to fetch disk stats:', error);
        this.isConnected = false;
      }
    },

    /**
     * Fetch GPU stats
     */
    async fetchGPUStats() {
      try {
        const data = await api.get('/api/stats/gpu');
        this.stats.gpu = data;
        this.isConnected = true;
      } catch (error) {
        console.error('Failed to fetch GPU stats:', error);
        this.isConnected = false;
      }
    },

    /**
     * Fetch Docker containers
     */
    async fetchContainers() {
      this.loading.containers = true;
      this.errors.containers = null;

      try {
        const data = await api.get('/api/docker/containers');
        this.containers = data.containers || [];

        // Check Docker availability
        const status = await api.get('/api/docker/status');
        this.dockerAvailable = status.available || false;
      } catch (error) {
        console.error('Failed to fetch containers:', error);
        this.errors.containers = error.message || 'Failed to fetch containers';
        this.dockerAvailable = false;
      } finally {
        this.loading.containers = false;
      }
    },

    /**
     * Start a container
     */
    async startContainer(containerId) {
      try {
        const result = await api.post(`/api/docker/containers/${containerId}/start`);
        await this.fetchContainers(); // Refresh list
        return result;
      } catch (error) {
        console.error('Failed to start container:', error);
        throw error;
      }
    },

    /**
     * Stop a container
     */
    async stopContainer(containerId) {
      try {
        const result = await api.post(`/api/docker/containers/${containerId}/stop`);
        await this.fetchContainers(); // Refresh list
        return result;
      } catch (error) {
        console.error('Failed to stop container:', error);
        throw error;
      }
    },

    /**
     * Restart a container
     */
    async restartContainer(containerId) {
      try {
        const result = await api.post(`/api/docker/containers/${containerId}/restart`);
        await this.fetchContainers(); // Refresh list
        return result;
      } catch (error) {
        console.error('Failed to restart container:', error);
        throw error;
      }
    },

    /**
     * Fetch processes
     */
    async fetchProcesses(limit = 50, sortBy = 'cpu') {
      this.loading.processes = true;
      this.errors.processes = null;

      try {
        const data = await api.get(`/api/processes?limit=${limit}&sort_by=${sortBy}`);
        this.processes = data.processes || [];
      } catch (error) {
        console.error('Failed to fetch processes:', error);
        this.errors.processes = error.message || 'Failed to fetch processes';
      } finally {
        this.loading.processes = false;
      }
    },

    /**
     * Kill a process
     */
    async killProcess(pid) {
      try {
        const result = await api.delete(`/api/processes/${pid}`);
        await this.fetchProcesses(50); // Refresh list with default limit
        return result;
      } catch (error) {
        console.error('Failed to kill process:', error);
        throw error;
      }
    },

    /**
     * Enable auto-refresh (polling mode)
     */
    enableAutoRefresh(interval = 5000) {
      // Disable WebSocket if enabled
      if (this.webSocketEnabled) {
        this.disableWebSocket();
      }

      this.disableAutoRefresh();
      this.autoRefresh = true;
      this.refreshInterval = interval;

      // Start refresh timer
      this.refreshTimer = setInterval(() => {
        this.fetchStats();
      }, interval);

      // Initial fetch
      this.fetchStats();
    },

    /**
     * Disable auto-refresh (polling mode)
     */
    disableAutoRefresh() {
      this.autoRefresh = false;

      if (this.refreshTimer) {
        clearInterval(this.refreshTimer);
        this.refreshTimer = null;
      }
    },

    /**
     * Update refresh interval
     */
    setRefreshInterval(interval) {
      if (this.autoRefresh) {
        this.enableAutoRefresh(interval);
      }
      this.refreshInterval = interval;
    },

    /**
     * Enable WebSocket (real-time mode)
     */
    enableWebSocket() {
      // Disable polling if enabled
      if (this.autoRefresh) {
        this.disableAutoRefresh();
      }

      this.webSocketEnabled = true;
      this._setupWebSocketHandlers();
      wsService.connect({ keepAliveInterval: 30000 });

      console.log('[System] WebSocket enabled');
    },

    /**
     * Disable WebSocket (real-time mode)
     */
    disableWebSocket() {
      this.webSocketEnabled = false;
      this._removeWebSocketHandlers();
      wsService.disconnect();
      this.webSocketState = WebSocketState.DISCONNECTED;

      console.log('[System] WebSocket disabled');
    },

    /**
     * Setup WebSocket event handlers
     */
    _setupWebSocketHandlers() {
      // Remove old handlers if any
      this._removeWebSocketHandlers();

      // Create handler functions
      this._wsEventHandlers = {
        onConnected: () => {
          this.webSocketState = WebSocketState.CONNECTED;
          console.log('[System] WebSocket connected - receiving real-time updates');
        },

        onDisconnected: () => {
          this.webSocketState = WebSocketState.DISCONNECTED;
          console.log('[System] WebSocket disconnected');
        },

        onError: (error) => {
          this.webSocketState = WebSocketState.ERROR;
          console.error('[System] WebSocket error:', error);
        },

        onStats: (data) => {
          // Update stats from WebSocket
          console.log('[SystemStore] WebSocket Stats Update Received');
          console.log('[SystemStore] WebSocket CPU Percent:', data?.cpu?.cpu_percent);
          console.log('[SystemStore] WebSocket CPU Object:', data?.cpu);
          console.log('[SystemStore] Full WebSocket Data:', JSON.stringify(data, null, 2));

          this.stats = {
            ...this.stats,
            ...data,
            timestamp: Math.floor(Date.now() / 1000)
          };

          console.log('[SystemStore] After merge - this.stats.cpu:', this.stats.cpu);
          console.log('[SystemStore] After merge - this.stats.cpu.cpu_percent:', this.stats.cpu?.cpu_percent);

          // Pass data directly to updateHistory for immediate processing
          this.updateHistory(data);
        },

        onThresholdAlert: (data) => {
          // Handle threshold alerts from WebSocket
          console.log('[System] Threshold alert received via WebSocket:', data);

          // Add alert to the alerts array
          if (data && data.id) {
            // Check if alert already exists to avoid duplicates
            const existingIndex = this.alerts.findIndex(a => a.id === data.id);
            if (existingIndex === -1) {
              // Add new alert at the beginning
              this.alerts.unshift(data);
              console.log(`[System] Added new threshold alert: ${data.metric_type} - ${data.value}%`);
            } else {
              // Update existing alert
              this.alerts[existingIndex] = data;
              console.log(`[System] Updated threshold alert: ${data.metric_type}`);
            }
          }
        }
      };

      // Register handlers
      wsService.on('connected', this._wsEventHandlers.onConnected);
      wsService.on('disconnected', this._wsEventHandlers.onDisconnected);
      wsService.on('error', this._wsEventHandlers.onError);
      wsService.on('stats', this._wsEventHandlers.onStats);
      wsService.on('threshold_alert', this._wsEventHandlers.onThresholdAlert);
    },

    /**
     * Remove WebSocket event handlers
     */
    _removeWebSocketHandlers() {
      if (this._wsEventHandlers) {
        wsService.off('connected', this._wsEventHandlers.onConnected);
        wsService.off('disconnected', this._wsEventHandlers.onDisconnected);
        wsService.off('error', this._wsEventHandlers.onError);
        wsService.off('stats', this._wsEventHandlers.onStats);
        wsService.off('threshold_alert', this._wsEventHandlers.onThresholdAlert);
        this._wsEventHandlers = null;
      }
    },

    /**
     * Check screenshot availability
     */
    async checkScreenshotAvailability() {
      try {
        const result = await api.get('/api/screenshot/status');
        this.screenshotAvailable = result.available || false;
      } catch {
        this.screenshotAvailable = false;
      }
    },

    /**
     * Update historical data for charts
     * @param {Object} data - Optional data object to use directly (avoids reactivity timing issues)
     */
    updateHistory(data = null) {
      const now = Date.now();

      // Extract values - CRITICAL: Use data directly to avoid getter recursion
      let cpuValue, memoryValue, diskValue;

      console.log('[updateHistory] Called with data:', data ? 'YES' : 'NO');
      console.log('[updateHistory] Input data.cpu?.cpu_percent:', data?.cpu?.cpu_percent);

      if (data) {
        // Use provided data directly (no getters - prevents infinite recursion)
        cpuValue = data.cpu?.cpu_percent ?? 0;
        memoryValue = data.memory?.percent ?? 0;
        diskValue = data.disk?.percent ?? 0;
        console.log('[updateHistory] Extracted from provided data - CPU:', cpuValue, 'Memory:', memoryValue, 'Disk:', diskValue);
      } else {
        // Fallback to current stats (access directly, not through getters)
        cpuValue = this.stats.cpu?.cpu_percent ?? 0;
        memoryValue = this.stats.memory?.percent ?? 0;
        diskValue = this.stats.disk?.percent ?? 0;
        console.log('[updateHistory] Extracted from this.stats - CPU:', cpuValue, 'Memory:', memoryValue, 'Disk:', diskValue);
      }

      // Validate values (prevent NaN/undefined)
      cpuValue = typeof cpuValue === 'number' ? cpuValue : 0;
      memoryValue = typeof memoryValue === 'number' ? memoryValue : 0;
      diskValue = typeof diskValue === 'number' ? diskValue : 0;

      // Add current stats to history
      this.history.timestamps.push(now);
      this.history.cpu.push(cpuValue);
      this.history.memory.push(memoryValue);
      this.history.disk.push(diskValue);

      // Keep only the last maxHistoryLength entries
      if (this.history.timestamps.length > this.maxHistoryLength) {
        this.history.timestamps.shift();
        this.history.cpu.shift();
        this.history.memory.shift();
        this.history.disk.shift();
      }

      console.log('[System] History updated:', {
        cpu: cpuValue,
        memory: memoryValue,
        disk: diskValue,
        dataPoints: this.history.timestamps.length,
        historyArray: this.history.cpu
      });

      // Check thresholds after updating history
      this.checkThresholds(cpuValue, memoryValue, diskValue);
    },

    /**
     * Load threshold configuration from backend
     */
    async loadThresholdConfig() {
      try {
        const response = await api.get('/api/threshold/config');
        if (response.success && response.data) {
          this.thresholdConfig = {
            enabled: response.data.enabled || false,
            cpu_threshold: response.data.cpu_threshold || 80,
            memory_threshold: response.data.memory_threshold || 85,
            disk_threshold: response.data.disk_threshold || 90
          };
          console.log('[System] Threshold config loaded:', this.thresholdConfig);
        }
      } catch (error) {
        console.error('[System] Failed to load threshold config:', error);
        // Use defaults on error
        this.thresholdConfig = {
          enabled: false,
          cpu_threshold: 80,
          memory_threshold: 85,
          disk_threshold: 90
        };
      }
    },

    /**
     * Check if values exceed thresholds and trigger alerts
     * @param {number} cpuValue - Current CPU usage percentage
     * @param {number} memoryValue - Current Memory usage percentage
     * @param {number} diskValue - Current Disk usage percentage
     */
    checkThresholds(cpuValue, memoryValue, diskValue) {
      // Don't check if threshold monitoring is disabled
      if (!this.thresholdConfig.enabled) {
        return;
      }

      const now = Date.now();
      const alerts = [];

      // Check CPU threshold
      if (cpuValue >= this.thresholdConfig.cpu_threshold) {
        if (now - this._lastAlertTime.cpu > this._alertCooldown) {
          alerts.push({
            id: `cpu-${now}`,
            type: 'cpu',
            metric_type: 'cpu',
            metric: 'CPU Usage',
            value: cpuValue,
            threshold: this.thresholdConfig.cpu_threshold,
            triggered_at: new Date(now).toISOString(),
            acknowledged: false
          });
          this._lastAlertTime.cpu = now;
        }
      }

      // Check Memory threshold
      if (memoryValue >= this.thresholdConfig.memory_threshold) {
        if (now - this._lastAlertTime.memory > this._alertCooldown) {
          alerts.push({
            id: `memory-${now}`,
            type: 'memory',
            metric_type: 'memory',
            metric: 'Memory Usage',
            value: memoryValue,
            threshold: this.thresholdConfig.memory_threshold,
            triggered_at: new Date(now).toISOString(),
            acknowledged: false
          });
          this._lastAlertTime.memory = now;
        }
      }

      // Check Disk threshold
      if (diskValue >= this.thresholdConfig.disk_threshold) {
        if (now - this._lastAlertTime.disk > this._alertCooldown) {
          alerts.push({
            id: `disk-${now}`,
            type: 'disk',
            metric_type: 'disk',
            metric: 'Disk Usage',
            value: diskValue,
            threshold: this.thresholdConfig.disk_threshold,
            triggered_at: new Date(now).toISOString(),
            acknowledged: false
          });
          this._lastAlertTime.disk = now;
        }
      }

      // Trigger alerts for any exceeded thresholds
      if (alerts.length > 0) {
        alerts.forEach(alert => {
          console.warn('[System] Threshold Alert:', alert);

          // Add alert to store for UI
          this.alerts.unshift(alert);

          // Keep only last 100 alerts to prevent memory issues
          if (this.alerts.length > 100) {
            this.alerts = this.alerts.slice(0, 100);
          }

          // Send native notification
          this.sendNativeNotification(alert);
        });

        // Update _lastAlert for backwards compatibility
        this.$patch?.({ _lastAlert: alerts[0] });
      }
    },

    /**
     * Send native mobile notification for threshold alert
     * @param {Object} alert - Alert object
     */
    async sendNativeNotification(alert) {
      try {
        // Check if we're running in a native environment (Capacitor)
        const isNative = window.Capacitor?.isNativePlatform?.();

        if (!isNative) {
          // Not running in native app, skip native notifications
          console.log('[System] Not in native environment, skipping native notification');
          return;
        }

        // Request permissions if not already granted
        const permissions = await LocalNotifications.checkPermissions();
        if (permissions.display !== 'granted') {
          const result = await LocalNotifications.requestPermissions();
          if (result.display !== 'granted') {
            console.warn('[System] Notification permission denied');
            return;
          }
        }

        // Determine severity based on how much the threshold is exceeded
        const excess = alert.value - alert.threshold;
        let priority = 1; // Default low priority
        let sound = 'beep';

        if (excess >= 20) {
          priority = 2; // High priority
          sound = 'beep';
        } else if (excess >= 10) {
          priority = 1.5; // Medium priority
        }

        // Create notification body with all alerts
        const body = `${alert.metric}: ${alert.value.toFixed(1)}% (Threshold: ${alert.threshold}%)`;

        // Schedule the notification
        await LocalNotifications.schedule({
          notifications: [
            {
              id: Date.now(), // Unique ID based on timestamp
              title: `⚠️ ${alert.metric} Alert`,
              body: body,
              schedule: { at: new Date(Date.now() + 100) }, // Fire immediately (100ms delay)
              sound: sound,
              priority: priority,
              smallIcon: 'ic_stat_notification', // Custom icon if available
              largeIcon: 'ic_stat_notification', // Custom icon if available
              extra: {
                alertId: alert.id,
                type: alert.type
              }
            }
          ]
        });

        console.log('[System] Native notification sent for alert:', alert.id);
      } catch (error) {
        console.error('[System] Failed to send native notification:', error);
        // Don't throw - notification failures shouldn't break the app
      }
    },

    /**
     * Fetch threshold alerts from backend
     */
    async fetchAlerts() {
      try {
        const response = await api.get('/api/threshold/alerts');
        if (response.success && response.alerts) {
          // Merge server alerts with local alerts (server takes precedence for synchronization)
          const serverAlertIds = new Set(response.alerts.map(a => a.id));
          // Keep local alerts that aren't on server (not yet synced)
          const localOnlyAlerts = this.alerts.filter(a => !serverAlertIds.has(a.id));
          // Replace with server alerts and add back local-only alerts
          this.alerts = [...response.alerts, ...localOnlyAlerts];
          console.log(`[SystemStore] Fetched ${response.alerts.length} alerts from server, total: ${this.alerts.length}`);
        }
      } catch (error) {
        console.error('[SystemStore] Failed to fetch threshold alerts:', error);
      }
    },

    /**
     * Clear all alerts
     */
    clearAlerts() {
      this.alerts = [];
    },

    /**
     * Acknowledge an alert
     * @param {string} alertId - Alert ID to acknowledge
     */
    acknowledgeAlert(alertId) {
      const alert = this.alerts.find(a => a.id === alertId);
      if (alert) {
        alert.acknowledged = true;
        alert.acknowledged_at = new Date().toISOString();
      }
    },

    /**
     * Acknowledge all alerts
     */
    acknowledgeAllAlerts() {
      this.alerts.forEach(alert => {
        if (!alert.acknowledged) {
          alert.acknowledged = true;
          alert.acknowledged_at = new Date().toISOString();
        }
      });
    },

    /**
     * Clear historical data
     */
    clearHistory() {
      this.history.timestamps = [];
      this.history.cpu = [];
      this.history.memory = [];
      this.history.disk = [];
    }
  }
});
