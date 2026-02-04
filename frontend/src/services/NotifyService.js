/**
 * ============================================================
 * Secure Notification Service
 * ============================================================
 * Provides a secure, standardized wrapper around Quasar's $q.notify
 * to prevent XSS attacks and ensure consistent notification behavior.
 *
 * Security Features:
 * - html: false by default (prevents XSS)
 * - timeout with sensible defaults
 * - caption for additional context
 * - progress bar for long operations
 * - position consistency
 *
 * Usage:
 *   import { secureNotify } from '@/services/NotifyService';
 *   secureNotify.success('Settings saved');
 *   secureNotify.error('Failed to save', 'Invalid input');
 * ============================================================
 */

/**
 * Default notification options
 */
const DEFAULT_OPTIONS = {
  html: false,           // Disable HTML rendering to prevent XSS attacks
  timeout: 3000,         // Auto-dismiss after 3 seconds
  position: 'top',       // Consistent positioning
  progress: false,       // Progress bar (enabled for long operations)
  closeBtn: true         // Show close button
};

/**
 * Notification type configurations
 */
const NOTIFY_TYPES = {
  positive: {
    icon: 'check_circle',
    color: 'positive',
    timeout: 2500
  },
  negative: {
    icon: 'error',
    color: 'negative',
    timeout: 4000  // Longer timeout for errors to read message
  },
  warning: {
    icon: 'warning',
    color: 'warning',
    timeout: 3500
  },
  info: {
    icon: 'info',
    color: 'info',
    timeout: 3000
  }
};

/**
 * Create a secure notification
 * @param {Object} $q - Quasar instance
 * @param {string} type - Notification type (positive, negative, warning, info)
 * @param {string} message - Main message
 * @param {Object} options - Additional options
 * @returns {void}
 */
function createNotify($q, type, message, options = {}) {
  const typeConfig = NOTIFY_TYPES[type] || NOTIFY_TYPES.info;

  const notifyOptions = {
    ...DEFAULT_OPTIONS,
    ...typeConfig,
    ...options,
    type,
    message
  };

  // Ensure HTML is disabled for security
  notifyOptions.html = false;

  $q.notify(notifyOptions);
}

/**
 * Secure Notification Service
 */
export const secureNotify = {
  /**
   * Success notification
   * @param {Object} $q - Quasar instance
   * @param {string} message - Success message
   * @param {string} caption - Optional caption
   */
  success: ($q, message, caption = null) => {
    createNotify($q, 'positive', message, caption ? { caption } : {});
  },

  /**
   * Error notification
   * @param {Object} $q - Quasar instance
   * @param {string} message - Error message
   * @param {string} caption - Optional caption with details
   */
  error: ($q, message, caption = null) => {
    createNotify($q, 'negative', message, caption ? { caption } : {});
  },

  /**
   * Warning notification
   * @param {Object} $q - Quasar instance
   * @param {string} message - Warning message
   * @param {string} caption - Optional caption
   */
  warning: ($q, message, caption = null) => {
    createNotify($q, 'warning', message, caption ? { caption } : {});
  },

  /**
   * Info notification
   * @param {Object} $q - Quasar instance
   * @param {string} message - Info message
   * @param {string} caption - Optional caption
   */
  info: ($q, message, caption = null) => {
    createNotify($q, 'info', message, caption ? { caption } : {});
  },

  /**
   * Loading notification with progress
   * @param {Object} $q - Quasar instance
   * @param {string} message - Loading message
   * @param {Object} options - Additional options
   */
  loading: ($q, message, options = {}) => {
    createNotify($q, 'info', message, {
      ...options,
      progress: true,
      timeout: 0  // No auto-dismiss for loading
    });
  },

  /**
   * Custom notification with full control
   * @param {Object} $q - Quasar instance
   * @param {Object} options - Complete notification options
   */
  custom: ($q, options) => {
    createNotify($q, options.type || 'info', options.message, options);
  }
};

export default secureNotify;
