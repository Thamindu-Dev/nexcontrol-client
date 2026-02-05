<!--
  ==============================================================================
  NexControl - Remote PC Controller
  Copyright (C) 2026 Thamindu-Dev

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
  ==============================================================================
-->
<template>
  <div class="login-page">
    <!-- iOS Safe Area Spacer -->
    <div class="safe-area-spacer-top"></div>

    <!-- Black Background -->
    <div class="background"></div>

    <div class="row fullscreen items-center justify-center">
      <div class="col-12 col-sm-10 col-md-8 col-lg-5 col-xl-4 q-px-md">
        <!-- Login Card -->
        <q-card class="login-card" flat bordered>

          <!-- Logo & Title Section -->
          <q-card-section class="text-center q-pt-lg q-pb-md">
            <q-icon
              name="computer"
              size="72px"
              color="white"
              class="q-mb-md logo-icon"
            />
            <div class="text-h4 text-weight-bold text-white q-mb-xs">
              NexControl
            </div>
            <div class="text-subtitle2 text-grey-4">
              Remote PC Controller
            </div>
          </q-card-section>

          <q-separator class="bg-grey-8" />

          <q-card-section class="q-pt-lg q-pb-none">
            <q-form @submit="handleLogin" class="q-gutter-y-sm">

              <!-- Server IP & Port - Close Together -->
              <div class="row q-col-gutter-sm q-mb-sm">
                <div class="col-12 col-sm-8">
                  <div class="text-caption text-grey-5 q-mb-sm">Server IP Address</div>
                  <q-input
                    v-model="serverConfig.host"
                    outlined
                    dark
                    dense
                    color="white"
                    placeholder="192.168.1.100"
                    :rules="[val => !!val || 'Required']"
                    class="login-input"
                  >
                    <template v-slot:prepend>
                      <q-icon name="lan" color="grey-4" size="20px" />
                    </template>
                  </q-input>
                </div>
                <div class="col-12 col-sm-4">
                  <div class="text-caption text-grey-5 q-mb-sm">Port</div>
                  <q-input
                    v-model.number="serverConfig.port"
                    type="number"
                    outlined
                    dark
                    dense
                    color="white"
                    placeholder="8000"
                    :rules="[val => val > 0 || 'Required']"
                    class="login-input"
                  />
                </div>
              </div>

              <q-separator class="bg-grey-8 q-my-md" />

              <!-- Password Input -->
              <div>
                <div class="text-caption text-grey-5 q-mb-sm">Password</div>
                <q-input
                  v-model="password"
                  :type="isPwd ? 'password' : 'text'"
                  outlined
                  dark
                  dense
                  color="white"
                  placeholder="Enter password"
                  :rules="[val => !!val || 'Required']"
                  class="login-input"
                  @keyup.enter="handleLogin"
                >
                  <template v-slot:prepend>
                    <q-icon name="lock" color="grey-4" size="20px" />
                  </template>
                  <template v-slot:append>
                    <q-icon
                      :name="isPwd ? 'visibility_off' : 'visibility'"
                      class="cursor-pointer text-grey-5"
                      size="20px"
                      @click="isPwd = !isPwd"
                    />
                  </template>
                </q-input>
              </div>

              <!-- Error Message -->
              <div v-if="loginError" class="error-box q-pa-sm rounded-borders">
                <q-icon name="error" size="18px" class="q-mr-sm" />
                <span class="text-body2">{{ loginError }}</span>
              </div>

              <!-- Connect Button - Full Width -->
              <q-btn
                type="submit"
                class="login-btn full-width"
                :loading="loading"
                :disable="loading"
                size="lg"
                icon="arrow_forward"
                label="Connect"
              >
                <template v-slot:loading>
                  <q-spinner color="white" size="20px" />
                </template>
              </q-btn>

              <!-- Test Network Button - Below Connect -->
              <q-btn
                @click="testNetworkOnly"
                outline
                class="full-width"
                color="grey-7"
                size="md"
                icon="wifi_find"
                label="Test Network Connection"
              />

              <!-- Remember Toggle -->
              <div class="row items-center justify-center q-mt-sm">
                <q-toggle
                  v-model="saveCredentials"
                  color="grey-6"
                  label="Remember credentials"
                  dark
                  size="sm"
                  class="text-grey-5"
                />
              </div>

              <!-- Emergency Settings Button -->
              <div class="row items-center justify-center q-mt-md">
                <q-btn
                  flat
                  round
                  color="grey-6"
                  icon="settings"
                  size="sm"
                  @click="goToSettings"
                >
                  <q-tooltip>Server Settings</q-tooltip>
                </q-btn>
                <div class="text-caption text-grey-6 q-ml-xs">
                  Server Settings
                </div>
              </div>

            </q-form>
          </q-card-section>

          <!-- Footer Info -->
          <q-card-section class="text-center q-pt-none q-pb-sm">
            <div class="text-caption text-grey-6">
              <q-icon name="info" size="16px" class="q-mr-xs" />
              Local network only - Ensure both devices are on the same network
            </div>
          </q-card-section>
        </q-card>

        <!-- Version -->
        <div class="text-center q-mt-md">
          <div class="text-caption text-grey-7">
            Version {{ version }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Notify } from 'quasar';
import { useAuthStore } from '../stores/auth';
import { useSettingsStore } from '../stores/settings';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'LoginPage'
});

const router = useRouter();

// Stores
const authStore = useAuthStore();
const settingsStore = useSettingsStore();

// State
const password = ref('');
const isPwd = ref(true);
const loading = ref(false);
const loginError = ref(null);
const saveCredentials = ref(false);
const version = ref('1.0.0');

// Server configuration
const serverConfig = reactive({
  protocol: 'http',
  host: 'localhost',
  port: 8000
});

/**
 * Test network access - Makes a simple request to trigger iOS local network popup
 */
async function testNetworkOnly() {
  if (!serverConfig.host) {
    Notify.create({
      type: 'negative',
      message: 'Please enter server IP first',
      position: 'top',
      timeout: 2500,
      classes: 'notification-glossy'
    });
    return;
  }

  const testUrl = `${serverConfig.protocol}://${serverConfig.host}:${serverConfig.port}/api/test/connection`;
  console.log('[Test Network] Connecting to:', testUrl);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(testUrl, {
      method: 'GET',
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      console.log('[Test Network] Success:', data);
      Notify.create({
        type: 'positive',
        message: 'Network access working! Server reachable.',
        position: 'top',
        timeout: 3000,
        classes: 'notification-glossy'
      });
    } else {
      Notify.create({
        type: 'warning',
        message: `Server responded: ${response.status}`,
        position: 'top',
        timeout: 3000,
        classes: 'notification-glossy'
      });
    }
  } catch (error) {
    console.error('[Test Network] Error:', error);
    Notify.create({
      type: 'negative',
      message: 'Cannot reach server. Check IP and ensure server is running.',
      position: 'top',
      timeout: 3000,
      classes: 'notification-glossy'
    });
  }
}

/**
 * Validate IP address (private/local only for security)
 */
function isValidIP(ip) {
  if (!ip || typeof ip !== 'string') return false

  const ipLower = ip.toLowerCase().trim()

  if (ipLower === 'localhost') return true

  const privateRanges = [
    /^10\./,
    /^172\.(1[6-9]|2\d|3[01])\./,
    /^192\.168\./,
    /^127\./
  ]

  const ipv4Regex = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/
  const ipv4Match = ip.match(ipv4Regex)

  if (ipv4Match) {
    return privateRanges.some(range => range.test(ip))
  }

  return false
}

/**
 * Validate port number
 */
function isValidPort(port) {
  const portNum = Number(port)
  return !isNaN(portNum) && portNum >= 1 && portNum <= 65535
}

/**
 * Handle login form submission
 */
async function handleLogin() {
  // Validate host/IP
  if (!serverConfig.host || !serverConfig.host.trim()) {
    loginError.value = 'Server IP address is required'
    return
  }

  if (!isValidIP(serverConfig.host)) {
    loginError.value = 'Invalid IP address. Must be a local network IP'
    Notify.create({
      type: 'negative',
      message: 'Invalid IP address. Must be a local network IP (192.168.x.x, 10.x.x.x, 172.16-31.x.x, or localhost)',
      position: 'top',
      timeout: 4000,
      classes: 'notification-glossy'
    })
    return
  }

  // Validate port
  if (!isValidPort(serverConfig.port)) {
    loginError.value = 'Invalid port. Must be between 1 and 65535'
    Notify.create({
      type: 'negative',
      message: 'Invalid port. Must be between 1 and 65535',
      position: 'top',
      timeout: 2500,
      classes: 'notification-glossy'
    })
    return
  }

  loading.value = true;
  loginError.value = null;

  const serverUrl = `${serverConfig.protocol}://${serverConfig.host}:${serverConfig.port}`;
  console.log('[Login] Attempting to connect to:', serverUrl);

  try {
    // Update server configuration
    await settingsStore.updateServer(serverConfig);
    console.log('[Login] Server config updated');

    // Test connection
    const testUrl = `${serverUrl}/api/test/connection`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const testResponse = await fetch(testUrl, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!testResponse.ok) {
        throw new Error(`Server returned ${testResponse.status}`);
      }
    } catch (testError) {
      console.error('[Login] Connection test failed:', testError);
      loginError.value = 'Cannot reach server. Make sure your PC is on and check the IP address.';
      loading.value = false;

      if (typeof window !== 'undefined' && window.Capacitor?.getPlatform() === 'ios') {
        Notify.create({
          type: 'warning',
          message: 'If you see a popup about Local Network access, tap OK to allow',
          position: 'top',
          timeout: 5000,
          classes: 'notification-glossy'
        });
      }
      return;
    }

    // Attempt login
    const result = await authStore.login(password.value);
    console.log('[Login] Login result:', result);

    if (result.success) {
      // CRITICAL: Explicit timeout prevents infinite overlay blocking UI
      Notify.create({
        type: 'positive',
        message: 'Connected successfully!',
        position: 'top',
        timeout: 2500, // Auto-dismiss after 2.5 seconds
        classes: 'notification-glossy',
        dismissible: true // Allow tap-to-dismiss
      });

      if (saveCredentials.value) {
        // Credentials saved
      }

      // Navigate immediately - don't wait for notification
      router.push('/dashboard');
    } else {
      loginError.value = result.error || 'Login failed';
    }
  } catch (error) {
    console.error('[Login] Error:', error);
    loginError.value = error.message || 'Connection failed. Check server settings.';

    // Skip notification for security errors (already shown by showSecurityAlert)
    if (!error.isSecurityError) {
      Notify.create({
        type: 'negative',
        message: loginError.value,
        position: 'top',
        timeout: 3000,
        classes: 'notification-glossy'
      });
    }
  } finally {
    loading.value = false;
  }
}

/**
 * Navigate to Settings (emergency access)
 */
function goToSettings() {
  router.push('/settings');
}

/**
 * Load saved settings on mount
 */
onMounted(() => {
  settingsStore.loadSettings();

  const savedConfig = settingsStore.server;
  if (savedConfig) {
    Object.assign(serverConfig, savedConfig);
  }

  // Expose test functions to window for debugging
  if (typeof window !== 'undefined') {
    window.testNexControlConnection = async () => {
      try {
        const protocol = serverConfig.protocol || 'http';
        const host = serverConfig.host;
        const port = serverConfig.port;
        const url = `${protocol}://${host}:${port}/api/test/connection`;

        console.log('[Test GET] Connecting to:', url);

        const response = await fetch(url, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });

        console.log('[Test GET] Response status:', response.status);
        const data = await response.json();
        console.log('[Test GET] Response data:', data);
        return data;
      } catch (error) {
        console.error('[Test GET] Error:', error);
        throw error;
      }
    };

    window.testNexControlPOST = async () => {
      try {
        const protocol = serverConfig.protocol || 'http';
        const host = serverConfig.host;
        const port = serverConfig.port;
        const url = `${protocol}://${host}:${port}/api/test/echo`;

        console.log('[Test POST] Connecting to:', url);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ test: 'data', timestamp: Date.now() }),
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        console.log('[Test POST] Response status:', response.status);
        const data = await response.json();
        console.log('[Test POST] Response data:', data);
        return data;
      } catch (error) {
        console.error('[Test POST] Error:', error);
        if (error.name === 'AbortError') {
          console.error('[Test POST] Request timed out');
        }
        throw error;
      }
    };
  }
});
</script>

<style scoped>
/* iOS Safe Area Support */
.safe-area-spacer-top {
  height: constant(safe-area-inset-top);
  height: env(safe-area-inset-top);
  background: #000000;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1;
}

.login-page {
  min-height: 100vh;
  position: relative;
  background: #000000;
  padding-top: constant(safe-area-inset-top);
  padding-top: env(safe-area-inset-top);
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: constant(safe-area-inset-left);
  padding-left: env(safe-area-inset-left);
  padding-right: constant(safe-area-inset-right);
  padding-right: env(safe-area-inset-right);
}

/* Background */
.background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #000000;
  z-index: 0;
}

/* Login Card */
.login-card {
  position: relative;
  background: rgba(20, 20, 20, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
  z-index: 1;
}

/* Logo Icon */
.logo-icon {
  opacity: 0.9;
}

/* Inputs */
.login-input :deep(.q-field__control) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-radius: 8px;
}

.login-input :deep(.q-field__control):hover {
  background: rgba(255, 255, 255, 0.08) !important;
}

.login-input :deep(.q-field__native) {
  color: white !important;
}

.login-input :deep(.q-field__label) {
  color: #9ca3af !important;
}

.login-input :deep(.q-field__marginal) {
  color: #6b7280 !important;
}

/* Login Button */
.login-btn {
  background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  height: 48px;
}

.login-btn:hover {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
}

.login-btn:disabled {
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
  color: #6b7280;
}

/* Test Button - align with input field */
.test-btn {
  height: 40px;
  min-width: 56px;
}

/* Ensure input fields have consistent height */
.login-input :deep(.q-field__control) {
  height: 40px !important;
  min-height: 40px !important;
}

.login-input :deep(.q-field__native) {
  min-height: 40px !important;
  height: 40px !important;
}

/* Error Box */
.error-box {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
}

/* Responsive */
@media (max-width: 575.98px) {
  .login-card {
    margin: 16px !important;
  }

  .text-h4 {
    font-size: 1.5rem !important;
  }

  .logo-icon {
    font-size: 56px !important;
  }

  .login-btn {
    height: 44px;
  }
}

@media (hover: none) and (pointer: coarse) {
  .login-input :deep(.q-field__native) {
    min-height: 44px;
  }

  .login-btn {
    min-height: 44px;
  }
}

/* Safe Area Support */
@supports (padding: max(0px)) {
  .login-page {
    padding-top: max(16px, env(safe-area-inset-top));
    padding-bottom: max(16px, env(safe-area-inset-bottom));
    padding-left: max(16px, env(safe-area-inset-left));
    padding-right: max(16px, env(safe-area-inset-right));
  }

  .login-card {
    margin-left: max(0px, env(safe-area-inset-left));
    margin-right: max(0px, env(safe-area-inset-right));
  }
}

@media (max-width: 767.98px) and (orientation: landscape) {
  .login-card {
    margin: 12px !important;
  }
}
</style>
