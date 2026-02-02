/**
 * =============================================================
 * EnvConfig - Environment Configuration for NexControl
 * =============================================================
 * Provides environment-based configuration for development
 * and production builds
 */

/**
 * Get current environment
 */
export function getEnvironment() {
  // Check environment variables set during build
  if (import.meta.env.VITE_BUILD_TYPE) {
    return import.meta.env.VITE_BUILD_TYPE;
  }

  // Check if running in Capacitor/mobile
  if (window.Capacitor) {
    return 'mobile';
  }

  // Check if running in Codespaces
  if (window.location.hostname.endsWith('.app.github.dev') ||
      window.location.hostname.includes('codespaces')) {
    return 'codespaces';
  }

  // Default to development
  return 'development';
}

/**
 * Get API base URL for current environment
 */
export function getApiBaseUrl() {
  const env = getEnvironment();

  // User can override via localStorage (for Settings page)
  const customConfig = localStorage.getItem('nexcontrol_server_config');
  if (customConfig) {
    try {
      const config = JSON.parse(customConfig);
      return `${config.protocol}://${config.host}:${config.port}`;
    } catch {
      // Invalid config, continue with defaults
    }
  }

  switch (env) {
    case 'production':
      // Production API URL - configure this for your deployment
      return 'https://api.nexcontrol.example.com';

    case 'staging':
      // Staging API URL
      return 'https://staging-api.nexcontrol.example.com';

    case 'mobile':
      // Mobile apps use the production API by default
      return 'https://api.nexcontrol.example.com';

    case 'codespaces':
      // In Codespaces, use proxy (empty relative path)
      return '';

    case 'development':
    default:
      // Local development
      return 'http://localhost:8000';
  }
}

/**
 * Get WebSocket URL for current environment
 */
export function getWebSocketUrl() {
  const env = getEnvironment();

  const customConfig = localStorage.getItem('nexcontrol_server_config');
  if (customConfig) {
    try {
      const config = JSON.parse(customConfig);
      const protocol = config.protocol === 'https' ? 'wss' : 'ws';
      return `${protocol}://${config.host}:${config.port}/ws`;
    } catch {
      // Invalid config, continue with defaults
    }
  }

  switch (env) {
    case 'production':
      return 'wss://api.nexcontrol.example.com/ws';
    case 'staging':
      return 'wss://staging-api.nexcontrol.example.com/ws';
    case 'mobile':
      return 'wss://api.nexcontrol.example.com/ws';
    case 'codespaces': {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${wsProtocol}//${window.location.host}/ws`;
    }
    default:
      return 'ws://localhost:8000/ws';
  }
}

/**
 * Check if current environment is development
 */
export function isDevelopment() {
  return getEnvironment() === 'development' || getEnvironment() === 'codespaces';
}

/**
 * Check if current environment is production
 */
export function isProduction() {
  return getEnvironment() === 'production';
}

/**
 * Check if running in mobile app (Capacitor)
 */
export function isMobile() {
  return getEnvironment() === 'mobile';
}

/**
 * Check if running in Codespaces
 */
export function isCodespaces() {
  return getEnvironment() === 'codespaces';
}

export default {
  getEnvironment,
  getApiBaseUrl,
  getWebSocketUrl,
  isDevelopment,
  isProduction,
  isMobile,
  isCodespaces
};
