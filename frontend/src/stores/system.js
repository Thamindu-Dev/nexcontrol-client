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

export const useSystemStore = defineStore('system', {
  state: () => ({
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

    // Historical data for charts (max 60 data points = 5 minutes at 5s interval)
    history: {
      cpu: [],
      memory: [],
      disk: [],
      timestamps: []
    },
    maxHistoryLength: 60
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
     * Get GPU temperature
     */
    gpuTemp: (state) => {
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
     */
    cpuChartData: (state) => {
      return {
        labels: state.history.timestamps.map(t => {
          const date = new Date(t);
          return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }),
        datasets: [{
          label: 'CPU Usage (%)',
          data: state.history.cpu,
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
     */
    memoryChartData: (state) => {
      return {
        labels: state.history.timestamps.map(t => {
          const date = new Date(t);
          return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }),
        datasets: [{
          label: 'Memory Usage (%)',
          data: state.history.memory,
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
     */
    diskChartData: (state) => {
      return {
        labels: state.history.timestamps.map(t => {
          const date = new Date(t);
          return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }),
        datasets: [{
          label: 'Disk Usage (%)',
          data: state.history.disk,
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
     */
    combinedChartData: (state) => {
      return {
        labels: state.history.timestamps.map(t => {
          const date = new Date(t);
          return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }),
        datasets: [
          {
            label: 'CPU',
            data: state.history.cpu,
            borderColor: 'rgb(255, 99, 132)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            tension: 0.4
          },
          {
            label: 'Memory',
            data: state.history.memory,
            borderColor: 'rgb(153, 102, 255)',
            backgroundColor: 'rgba(153, 102, 255, 0.2)',
            tension: 0.4
          },
          {
            label: 'Disk',
            data: state.history.disk,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            tension: 0.4
          }
        ]
      };
    }
  },

  actions: {
    /**
     * Fetch all system statistics (polling mode)
     */
    async fetchStats() {
      // Don't fetch if WebSocket is connected and working
      if (this.webSocketEnabled && this.isWebSocketConnected) {
        console.log('[System] Skipping fetch: WebSocket is connected');
        return;
      }

      this.loading.stats = true;
      this.errors.stats = null;

      try {
        const data = await api.get('/api/stats/all');
        this.stats = data;
        this.updateHistory();
      } catch (error) {
        console.error('Failed to fetch stats:', error);
        this.errors.stats = error.message || 'Failed to fetch stats';
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
      } catch (error) {
        console.error('Failed to fetch CPU stats:', error);
      }
    },

    /**
     * Fetch memory stats only
     */
    async fetchMemoryStats() {
      try {
        const data = await api.get('/api/stats/memory');
        this.stats.memory = data;
      } catch (error) {
        console.error('Failed to fetch memory stats:', error);
      }
    },

    /**
     * Fetch disk stats only
     */
    async fetchDiskStats() {
      try {
        const data = await api.get('/api/stats/disk');
        this.stats.disk = data;
      } catch (error) {
        console.error('Failed to fetch disk stats:', error);
      }
    },

    /**
     * Fetch GPU stats
     */
    async fetchGPUStats() {
      try {
        const data = await api.get('/api/stats/gpu');
        this.stats.gpu = data;
      } catch (error) {
        console.error('Failed to fetch GPU stats:', error);
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
    async fetchProcesses(limit = 20, sortBy = 'cpu') {
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
        await this.fetchProcesses(); // Refresh list
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
          this.stats = {
            ...this.stats,
            ...data,
            timestamp: Math.floor(Date.now() / 1000)
          };
          this.updateHistory();
        }
      };

      // Register handlers
      wsService.on('connected', this._wsEventHandlers.onConnected);
      wsService.on('disconnected', this._wsEventHandlers.onDisconnected);
      wsService.on('error', this._wsEventHandlers.onError);
      wsService.on('stats', this._wsEventHandlers.onStats);
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
     */
    updateHistory() {
      const now = Date.now();

      // Add current stats to history
      this.history.timestamps.push(now);
      this.history.cpu.push(this.cpuUsage);
      this.history.memory.push(this.memoryUsage);
      this.history.disk.push(this.diskUsage);

      // Keep only the last maxHistoryLength entries
      if (this.history.timestamps.length > this.maxHistoryLength) {
        this.history.timestamps.shift();
        this.history.cpu.shift();
        this.history.memory.shift();
        this.history.disk.shift();
      }
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
