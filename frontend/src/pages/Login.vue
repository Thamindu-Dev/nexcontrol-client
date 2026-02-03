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
    <!-- Animated Background -->
    <div class="animated-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div class="row fullscreen items-center justify-center">
      <div class="col-12 col-sm-8 col-md-6 col-lg-4 q-px-md">
        <!-- Glassmorphism Card -->
        <q-card class="glass-card q-pa-xl glossy" flat bordered>
          <!-- Header Section -->
          <q-card-section class="text-center q-pb-xl">
            <!-- Logo Icon -->
            <div class="logo-container q-mb-md">
              <q-icon
                name="computer"
                size="80px"
                class="logo-icon"
              />
            </div>

            <div class="text-h4 text-weight-bold text-white q-mb-sm">
              NexControl
            </div>
            <div class="text-subtitle2 text-blue-2">
              Remote PC Controller
            </div>
            <div class="text-caption text-grey-4 q-mt-xs">
              Control your PC from anywhere
            </div>
          </q-card-section>

          <q-card-section>
            <q-form @submit="handleLogin" class="q-gutter-md">
              <!-- Server Configuration -->
              <div class="section-label q-mb-sm">
                <q-icon name="dns" size="20px" class="q-mr-xs text-primary" />
                <span class="text-subtitle2 text-white">Server Configuration</span>
              </div>

              <q-input
                v-model="serverConfig.host"
                label="Server IP"
                outlined
                dark
                dense
                color="white"
                label-color="blue-2"
                hint="e.g., 192.168.1.100"
                :rules="[val => !!val || 'Host is required']"
                class="styled-input"
              >
                <template v-slot:prepend>
                  <q-icon name="lan" color="primary" />
                </template>
              </q-input>

              <q-input
                v-model.number="serverConfig.port"
                label="Port"
                type="number"
                outlined
                dark
                dense
                color="white"
                label-color="blue-2"
                hint="Default: 8000"
                :rules="[val => val > 0 || 'Port is required']"
                class="styled-input"
              >
                <template v-slot:prepend>
                  <q-icon name="settings_ethernet" color="primary" />
                </template>
              </q-input>

              <q-separator class="q-my-lg bg-white" style="opacity: 0.1" />

              <!-- Login Form -->
              <div class="section-label q-mb-sm">
                <q-icon name="lock" size="20px" class="q-mr-xs text-primary" />
                <span class="text-subtitle2 text-white">Login</span>
              </div>

              <q-input
                v-model="password"
                label="Password"
                :type="isPwd ? 'password' : 'text'"
                outlined
                dark
                dense
                color="white"
                label-color="blue-2"
                hint="Enter your app password"
                :rules="[val => !!val || 'Password is required']"
                class="styled-input"
              >
                <template v-slot:prepend>
                  <q-icon name="vpn_key" color="primary" />
                </template>
                <template v-slot:append>
                  <q-icon
                    :name="isPwd ? 'visibility_off' : 'visibility'"
                    class="cursor-pointer text-grey-5 hover:text-primary"
                    @click="isPwd = !isPwd"
                  />
                </template>
              </q-input>

              <!-- Error Message -->
              <div v-if="loginError" class="error-message q-mb-sm q-pa-sm rounded-borders">
                <q-icon name="error_outline" size="20px" class="q-mr-sm" />
                <span>{{ loginError }}</span>
              </div>

              <!-- Connect Button -->
              <q-btn
                type="submit"
                class="connect-btn full-width q-mb-sm glossy"
                :loading="loading"
                :disable="loading"
                size="lg"
              >
                <template v-slot:default>
                  <div class="row items-center justify-center no-wrap">
                    <q-icon name="rocket_launch" class="q-mr-sm" />
                    <span>Connect to Server</span>
                  </div>
                </template>
              </q-btn>

              <!-- Test Network Button -->
              <q-btn
                @click="testNetworkOnly"
                outline
                class="full-width q-mb-sm"
                color="blue-grey"
                size="md"
                icon-right="wifi_find"
              >
                Test Network Access
              </q-btn>

              <!-- Save Credentials -->
              <div class="row items-center justify-center q-mt-md">
                <q-toggle
                  v-model="saveCredentials"
                  color="primary"
                  label="Remember credentials"
                  dark
                  keep-color
                  class="text-caption text-grey-4"
                />
              </div>
            </q-form>
          </q-card-section>

          <q-card-section class="text-center">
            <div class="info-box q-pa-sm rounded-borders">
              <q-icon name="info" size="16px" class="q-mr-xs text-blue-2" />
              <span class="text-caption text-grey-4">
                Local network app - Make sure your PC is on the same network
              </span>
            </div>
          </q-card-section>
        </q-card>

        <!-- Version Info -->
        <div class="text-center q-mt-md">
          <div class="text-caption text-grey-6">
            v{{ version }}
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
        classes: 'notification-glossy'
      });
    }
  } catch (error) {
    console.error('[Test Network] Error:', error);
    Notify.create({
      type: 'negative',
      message: 'Cannot reach server. Check IP and ensure server is running.',
      position: 'top',
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
      Notify.create({
        type: 'positive',
        message: 'Connected successfully!',
        position: 'top',
        classes: 'notification-glossy'
      });

      if (saveCredentials.value) {
        // Credentials saved
      }

      router.push('/dashboard');
    } else {
      loginError.value = result.error || 'Login failed';
    }
  } catch (error) {
    console.error('[Login] Error:', error);
    loginError.value = error.message || 'Connection failed. Check server settings.';
    Notify.create({
      type: 'negative',
      message: loginError.value,
      position: 'top',
      classes: 'notification-glossy'
    });
  } finally {
    loading.value = false;
  }
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
.login-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

/* Animated Background */
.animated-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  z-index: 0;
}

/* Animated Orbs */
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
  animation: float 20s infinite;
}

.orb-1 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #3b82f6 0%, transparent 70%);
  top: -150px;
  left: -150px;
  animation-delay: 0s;
}

.orb-2 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
  bottom: -100px;
  right: -100px;
  animation-delay: -5s;
}

.orb-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -50px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

/* Glassmorphism Card */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

/* Logo Icon */
.logo-container {
  display: inline-block;
  padding: 20px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 50%;
  animation: pulse-glow 3s ease-in-out infinite;
}

.logo-icon {
  color: white;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
  }
  50% {
    box-shadow: 0 0 40px rgba(139, 92, 246, 0.8);
  }
}

/* Section Labels */
.section-label {
  display: flex;
  align-items: center;
}

/* Styled Inputs */
.styled-input :deep(.q-field__control) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-radius: 8px;
}

.styled-input :deep(.q-field__label) {
  color: #90caf9 !important;
}

.styled-input :deep(.q-field__marginal) {
  color: #90caf9 !important;
}

/* Connect Button */
.connect-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.connect-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 30px rgba(102, 126, 234, 0.5);
}

.connect-btn:disabled {
  background: linear-gradient(135deg, #4a5568 0%, #374151 100%);
  box-shadow: none;
  transform: none;
}

/* Error Message */
.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

/* Info Box */
.info-box {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

/* Smooth Transitions */
* {
  transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
}

/* Glossy Effect */
.glossy {
  position: relative;
  overflow: hidden;
}

.glossy::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.5s;
}

.glossy:hover::before {
  left: 100%;
}

/* Notification Styling */
:deep(.notification-glossy) {
  backdrop-filter: blur(10px);
  background: rgba(30, 30, 30, 0.9) !important;
}

/* Responsive Adjustments */
/* Extra small devices (phones, < 576px) */
@media (max-width: 575.98px) {
  .glass-card {
    margin: 16px !important;
  }

  .text-h4 {
    font-size: 1.5rem !important;
  }

  .text-subtitle1 {
    font-size: 1rem !important;
  }

  /* Reduce icon sizes */
  .logo-icon {
    width: 60px !important;
    height: 60px !important;
    font-size: 50px !important;
  }

  /* Make buttons full width with proper touch targets */
  .connect-btn, .q-btn {
    min-height: 44px; /* iOS touch target minimum */
  }

  /* Stack elements vertically on very small screens */
  .row {
    flex-direction: column;
  }

  .col-12.col-sm-8.col-md-6.col-lg-4 {
    width: 100% !important;
    flex: 0 0 100%;
  }
}

/* Small devices (landscape phones, ≥ 576px) */
@media (min-width: 576px) and (max-width: 767.98px) {
  .text-h4 {
    font-size: 1.75rem !important;
  }

  .glass-card {
    margin: 16px !important;
  }
}

/* Medium devices (tablets, ≥ 768px) */
@media (min-width: 768px) and (max-width: 991.98px) {
  /* Tablet specific adjustments */
}

/* Touch device optimizations */
@media (hover: none) and (pointer: coarse) {
  /* Improve touch targets */
  .q-btn {
    min-height: 44px;
    min-width: 44px;
  }

  /* Remove hover transitions on touch devices */
  .connect-btn:hover,
  .glossy:hover::before {
    transform: none;
  }

  /* Remove hover effects */
  .styled-input:hover :deep(.q-field__control) {
    background: rgba(255, 255, 255, 0.05) !important;
  }

  /* Make inputs more tap-friendly */
  .q-input :deep(.q-field__native) {
    min-height: 44px;
  }
}

/* Fix for safe areas on devices with notches */
@supports (padding: max(0px)) {
  .login-page {
    padding-left: max(16px, env(safe-area-inset-left));
    padding-right: max(16px, env(safe-area-inset-right));
  }

  .glass-card {
    margin-left: max(0px, env(safe-area-inset-left));
    margin-right: max(0px, env(safe-area-inset-right));
  }
}

/* Landscape orientation on mobile */
@media (max-width: 767.98px) and (orientation: landscape) {
  .q-pa-xl {
    padding: 12px !important;
  }

  .logo-container {
    padding: 12px !important;
  }

  .logo-icon {
    width: 50px !important;
    height: 50px !important;
    font-size: 40px !important;
  }
}
</style>
