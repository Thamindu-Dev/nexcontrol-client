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
 * MediaWebSocketService - Low-latency media control via WebSocket
 * Dedicated WebSocket connection for media commands to eliminate HTTP overhead
 */

import { getWebSocketUrl } from './EnvConfig';
import api from './ApiService';

/**
 * WebSocket connection states
 */
export const MediaWebSocketState = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error'
};

/**
 * MediaWebSocketService class
 * Singleton pattern to manage WebSocket connection for media control
 */
class MediaWebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3;
    this.reconnectDelay = 1000;
    this.state = MediaWebSocketState.DISCONNECTED;
    this.pendingCommands = new Map(); // Store pending commands with callbacks
    this._reconnectTimeout = null;
    this._keepAliveInterval = null;
    this._commandId = 0;
  }

  /**
   * Connect to WebSocket server
   * @param {string} token - JWT authentication token
   */
  async connect(token) {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      console.log('[MediaWS] Already connected or connecting');
      return true;
    }

    this.setState(MediaWebSocketState.CONNECTING);

    return new Promise((resolve, reject) => {
      try {
        // Construct WebSocket URL - append /media to base WebSocket URL
        const baseUrl = getWebSocketUrl();
        const wsUrl = token ? `${baseUrl}/media?token=${token}` : `${baseUrl}/media`;
        console.log('[MediaWS] Connecting to:', wsUrl.replace(/token=[^&]+/, 'token=***'));

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('[MediaWS] Connected');
          this.setState(MediaWebSocketState.CONNECTED);
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;
          this._startKeepAlive();
          resolve(true);
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('[MediaWS] Message received:', data);

            // Handle media, launch, and add_custom_app responses
            if (data.type === 'media_response' || data.type === 'launch_response' || data.type === 'add_custom_app_response') {
              // Find and execute pending callback
              for (const [id, callback] of this.pendingCommands) {
                callback(data);
                this.pendingCommands.delete(id);
                break;
              }
            } else if (data.type === 'error') {
              console.error('[MediaWS] Server error:', data.message);
              // Reject all pending commands on error
              for (const [id, callback] of this.pendingCommands) {
                callback({ success: false, message: data.message });
                this.pendingCommands.delete(id);
              }
            } else if (data.type === 'pong') {
              // Keep-alive response
            }
          } catch (error) {
            console.error('[MediaWS] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[MediaWS] Error:', error);
          this.setState(MediaWebSocketState.ERROR);
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log('[MediaWS] Disconnected:', event.code, event.reason);
          this.setState(MediaWebSocketState.DISCONNECTED);
          this._stopKeepAlive();

          // Reject any pending commands
          for (const [id, callback] of this.pendingCommands) {
            callback({ success: false, message: 'Connection closed' });
            this.pendingCommands.delete(id);
          }

          // Attempt to reconnect
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this._scheduleReconnect(token);
          } else {
            console.error('[MediaWS] Max reconnection attempts reached');
          }
        };

      } catch (error) {
        console.error('[MediaWS] Connection error:', error);
        this.setState(MediaWebSocketState.ERROR);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    // Already disconnected or nothing to clean up
    if (!this.ws && this.pendingCommands.size === 0) {
      return;
    }

    console.log('[MediaWS] Disconnecting...');

    // Cancel any pending reconnection
    if (this._reconnectTimeout) {
      clearTimeout(this._reconnectTimeout);
      this._reconnectTimeout = null;
    }

    // Stop keep-alive
    this._stopKeepAlive();

    // Reject all pending commands with abort
    console.log('[MediaWS] Cleaning up pending commands:', this.pendingCommands.size);
    for (const [id, callback] of this.pendingCommands) {
      try {
        callback({ success: false, message: 'Connection closed', aborted: true });
      } catch {
        // Ignore callback errors
      }
      this.pendingCommands.delete(id);
    }

    // Close WebSocket
    if (this.ws) {
      try {
        if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
          this.ws.close(1000, 'Client disconnecting');
        }
      } catch (e) {
        console.warn('[MediaWS] Error closing WebSocket:', e);
      }
      this.ws = null;
    }

    this.setState(MediaWebSocketState.DISCONNECTED);
    this.reconnectAttempts = 0;
  }

  /**
   * Send media command
   * @param {string} app - Target application
   * @param {string} action - Action to perform
   * @returns {Promise} Command result
   */
  async sendCommand(app, action) {
    // If WebSocket is connected, use it
    if (this.isConnected()) {
      return new Promise((resolve) => {
        const commandId = ++this._commandId;

        // Set timeout for response
        const timeout = setTimeout(() => {
          if (this.pendingCommands.has(commandId)) {
            this.pendingCommands.delete(commandId);
            console.warn('[MediaWS] Command timeout, falling back to HTTP');
            // Fallback to HTTP
            resolve(this._sendViaHttp(app, action));
          }
        }, 2000); // 2 second timeout

        // Store callback
        this.pendingCommands.set(commandId, (result) => {
          clearTimeout(timeout);
          resolve(result);
        });

        // Send command
        const message = JSON.stringify({
          type: 'media_command',
          app: app,
          action: action
        });

        console.log('[MediaWS] Sending command:', { app, action });
        this.ws.send(message);
      });
    } else {
      // Fallback to HTTP
      console.log('[MediaWS] Not connected, using HTTP');
      return this._sendViaHttp(app, action);
    }
  }

  /**
   * Launch application via WebSocket
   * @param {string} app_id - Application ID to launch
   * @returns {Promise} Launch result
   */
  async launchApp(app_id) {
    // If WebSocket is connected, use it
    if (this.isConnected()) {
      return new Promise((resolve) => {
        const commandId = ++this._commandId;

        // Set timeout for response
        const timeout = setTimeout(() => {
          if (this.pendingCommands.has(commandId)) {
            this.pendingCommands.delete(commandId);
            console.warn('[MediaWS] Launch timeout, falling back to HTTP');
            // Fallback to HTTP
            resolve(this._launchViaHttp(app_id));
          }
        }, 5000); // 5 second timeout

        // Store callback
        this.pendingCommands.set(commandId, (result) => {
          clearTimeout(timeout);
          resolve(result);
        });

        // Send launch command
        const message = JSON.stringify({
          type: 'launch_app',
          app_id: app_id
        });

        console.log('[MediaWS] Sending launch command:', app_id);
        this.ws.send(message);
      });
    } else {
      // Fallback to HTTP
      console.log('[MediaWS] Not connected, using HTTP for app launch');
      return this._launchViaHttp(app_id);
    }
  }

  /**
   * Add custom app via WebSocket (WebSocket only, no HTTP fallback)
   * @param {Object} appData - App data {name, type, path, url, icon}
   * @returns {Promise} Add result
   */
  async addCustomApp(appData) {
    if (!this.isConnected()) {
      return {
        success: false,
        message: 'WebSocket not connected. Please refresh the page.'
      };
    }

    return new Promise((resolve) => {
      const commandId = ++this._commandId;

      // Set timeout for response
      const timeout = setTimeout(() => {
        if (this.pendingCommands.has(commandId)) {
          this.pendingCommands.delete(commandId);
          console.warn('[MediaWS] Add custom app timeout');
          resolve({
            success: false,
            message: 'Request timeout. Please check your connection and try again.'
          });
        }
      }, 5000); // 5 second timeout

      // Store callback
      this.pendingCommands.set(commandId, (result) => {
        clearTimeout(timeout);
        resolve(result);
      });

      // Send add custom app command
      const message = JSON.stringify({
        type: 'add_custom_app',
        app_data: appData
      });

      console.log('[MediaWS] Sending add custom app command:', appData);
      this.ws.send(message);
    });
  }


  /**
   * Fallback to HTTP API for media control
  */
  async _sendViaHttp(app, action) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout for rapid button presses

    try {
      console.log('[MediaWS] Using HTTP fallback for:', { app, action });

      // Use fetch directly to have abort control
      const url = `${api.baseURL}/api/media/control`;
      const token = await api.getToken();

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({ app, action }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      const result = await response.json();
      return result;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error.name === 'AbortError') {
        return {
          success: false,
          message: 'HTTP request timeout'
        };
      }

      return {
        success: false,
        message: error.message || 'HTTP request failed'
      };
    }
  }

  /**
   * Fallback to HTTP API for app launch
   */
  async _launchViaHttp(app_id) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    try {
      console.log('[MediaWS] Using HTTP fallback for app launch:', app_id);

      // Use fetch directly to have abort control
      const url = `${api.baseURL}/api/launch`;
      const token = await api.getToken();

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({ app_id }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      const result = await response.json();
      return result;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error.name === 'AbortError') {
        return {
          success: false,
          message: 'HTTP request timeout'
        };
      }

      return {
        success: false,
        message: error.message || 'HTTP request failed'
      };
    }
  }

  /**
   * Get current connection state
   */
  getState() {
    return this.state;
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.state === MediaWebSocketState.CONNECTED && this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Set connection state
   */
  setState(state) {
    const oldState = this.state;
    this.state = state;
    if (oldState !== state) {
      console.log(`[MediaWS] State: ${oldState} -> ${state}`);
    }
  }

  /**
   * Schedule reconnection attempt
   */
  _scheduleReconnect(token) {
    this.reconnectAttempts++;

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      10000 // Max 10 seconds
    );

    console.log(`[MediaWS] Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

    this._reconnectTimeout = setTimeout(async () => {
      console.log(`[MediaWS] Reconnect attempt ${this.reconnectAttempts}`);
      try {
        await this.connect(token);
      } catch (error) {
        console.error('[MediaWS] Reconnect failed:', error);
      }
    }, delay);
  }

  /**
   * Start keep-alive ping interval
   */
  _startKeepAlive() {
    this._stopKeepAlive();
    this._keepAliveInterval = setInterval(() => {
      if (this.isConnected()) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // 30 seconds
  }

  /**
   * Stop keep-alive ping interval
   */
  _stopKeepAlive() {
    if (this._keepAliveInterval) {
      clearInterval(this._keepAliveInterval);
      this._keepAliveInterval = null;
    }
  }
}

// Export singleton instance
export const mediaWsService = new MediaWebSocketService();

// Export class for testing
export default MediaWebSocketService;
