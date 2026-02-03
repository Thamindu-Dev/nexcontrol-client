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
 * WebSocketService - Real-time stats streaming
 * Manages WebSocket connection to backend for live system updates
 */

import { getWebSocketUrl } from './EnvConfig';

/**
 * WebSocket connection states
 */
export const WebSocketState = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error'
};

/**
 * WebSocketService class
 * Singleton pattern to manage a single WebSocket connection
 */
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.maxReconnectDelay = 30000; // Max 30 seconds
    this.state = WebSocketState.DISCONNECTED;
    this.listeners = new Map();
    this._reconnectTimeout = null;
    this._keepAliveInterval = null;
  }

  /**
   * Connect to WebSocket server
   * @param {Object} options - Connection options
   * @param {number} options.keepAliveInterval - Ping interval in ms (default: 30000)
   */
  connect(options = {}) {
    const { keepAliveInterval = 30000 } = options;

    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      console.log('[WebSocket] Already connected or connecting');
      return;
    }

    this.setState(WebSocketState.CONNECTING);

    try {
      const wsUrl = getWebSocketUrl().replace('/ws', '/ws/stats');
      console.log('[WebSocket] Connecting to:', wsUrl);

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected');
        this.setState(WebSocketState.CONNECTED);
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this._startKeepAlive(keepAliveInterval);
        this._emit('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[WebSocket] Message received:', data);

          // Emit based on message type
          if (data.type === 'stats_update') {
            this._emit('stats', data.data);
          } else if (data.type === 'pong') {
            this._emit('pong');
          } else {
            this._emit('message', data);
          }
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        this.setState(WebSocketState.ERROR);
        this._emit('error', error);
      };

      this.ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected:', event.code, event.reason);
        this.setState(WebSocketState.DISCONNECTED);
        this._stopKeepAlive();
        this._emit('disconnected', { code: event.code, reason: event.reason });

        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this._scheduleReconnect();
        } else {
          console.error('[WebSocket] Max reconnection attempts reached');
          this._emit('maxReconnectReached');
        }
      };

    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      this.setState(WebSocketState.ERROR);
      this._emit('error', error);
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    console.log('[WebSocket] Disconnecting...');

    // Cancel any pending reconnection
    if (this._reconnectTimeout) {
      clearTimeout(this._reconnectTimeout);
      this._reconnectTimeout = null;
    }

    // Stop keep-alive
    this._stopKeepAlive();

    // Close WebSocket
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }

    this.setState(WebSocketState.DISCONNECTED);
    this.reconnectAttempts = 0;
  }

  /**
   * Request current stats from server
   */
  requestStats() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send('get_stats');
    } else {
      console.warn('[WebSocket] Cannot request stats: not connected');
    }
  }

  /**
   * Send ping to server
   */
  ping() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send('ping');
    }
  }

  /**
   * Subscribe to events
   * @param {string} event - Event name ('connected', 'disconnected', 'stats', 'error', etc.)
   * @param {Function} callback - Callback function
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  /**
   * Unsubscribe from events
   * @param {string} event - Event name
   * @param {Function} callback - Callback function to remove
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
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
    return this.state === WebSocketState.CONNECTED && this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Set connection state
   */
  setState(state) {
    const oldState = this.state;
    this.state = state;
    if (oldState !== state) {
      console.log(`[WebSocket] State: ${oldState} -> ${state}`);
    }
  }

  /**
   * Emit event to listeners
   */
  _emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WebSocket] Error in ${event} listener:`, error);
        }
      });
    }
  }

  /**
   * Schedule reconnection attempt
   */
  _scheduleReconnect() {
    this.reconnectAttempts++;

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(`[WebSocket] Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

    this._reconnectTimeout = setTimeout(() => {
      console.log(`[WebSocket] Reconnect attempt ${this.reconnectAttempts}`);
      this.connect();
    }, delay);
  }

  /**
   * Start keep-alive ping interval
   */
  _startKeepAlive(interval) {
    this._stopKeepAlive();
    this._keepAliveInterval = setInterval(() => {
      this.ping();
    }, interval);
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
export const wsService = new WebSocketService();

// Export class for testing
export default WebSocketService;
