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

    <!-- Main Container - Vertical Stack -->
    <div class="fullscreen bg-dark text-white flex flex-center column q-pa-md">

      <!-- Compact Login Card (Top Section) -->
      <q-card class="compact-login-card q-mb-xl" flat bordered>

          <!-- Logo & Title - Compact -->
          <q-card-section class="text-center q-pt-sm q-pb-sm">
            <div class="row items-center justify-center q-mb-sm">
              <q-icon
                name="computer"
                size="40px"
                color="white"
                class="q-mr-sm"
              />
              <div class="text-h5 text-weight-bold text-white">NexControl</div>
            </div>
            <div class="text-caption text-grey-5">Remote PC Controller</div>
          </q-card-section>

          <q-separator class="bg-grey-8" />

          <!-- Form - Compact -->
          <q-card-section class="q-pt-sm q-pb-none">
            <q-form @submit="handleLogin" class="q-gutter-xs">

              <!-- Server IP -->
              <div class="q-mb-xs">
                <q-input
                  v-model="serverConfig.host"
                  outlined
                  dark
                  dense
                  color="white"
                  placeholder="192.168.1.100"
                  :rules="[val => !!val || 'Required']"
                  label="Server IP"
                  class="compact-input"
                >
                  <template v-slot:prepend>
                    <q-icon name="lan" color="grey-4" size="16px" />
                  </template>
                </q-input>
              </div>

              <!-- Port -->
              <div class="q-mb-xs">
                <q-input
                  v-model.number="serverConfig.port"
                  type="number"
                  outlined
                  dark
                  dense
                  color="white"
                  placeholder="8000"
                  :rules="[val => val > 0 || 'Required']"
                  label="Port"
                  class="compact-input"
                />
              </div>

              <!-- Password -->
              <div class="q-mb-xs">
                <q-input
                  v-model="password"
                  :type="isPwd ? 'password' : 'text'"
                  outlined
                  dark
                  dense
                  color="white"
                  placeholder="Password"
                  :rules="[val => !!val || 'Required']"
                  label="Password"
                  class="compact-input"
                  @keyup.enter="handleLogin"
                >
                  <template v-slot:prepend>
                    <q-icon name="lock" color="grey-4" size="16px" />
                  </template>
                  <template v-slot:append>
                    <q-icon
                      :name="isPwd ? 'visibility_off' : 'visibility'"
                      class="cursor-pointer text-grey-5"
                      size="16px"
                      @click="isPwd = !isPwd"
                    />
                  </template>
                </q-input>
              </div>

              <!-- Error Message -->
              <div v-if="loginError" class="error-box q-pa-xs rounded-borders q-mb-xs">
                <q-icon name="error" size="14px" class="q-mr-xs" />
                <span class="text-caption">{{ loginError }}</span>
              </div>

              <!-- Login Button -->
              <q-btn
                type="submit"
                class="login-btn full-width"
                :loading="loading"
                :disable="loading"
                size="md"
                icon="arrow_forward"
                label="Connect"
              >
                <template v-slot:loading>
                  <q-spinner color="white" size="16px" />
                </template>
              </q-btn>

              <!-- Quick Actions -->
              <div class="row items-center justify-between q-mt-xs">
                <q-btn
                  flat
                  dense
                  round
                  color="grey-6"
                  icon="settings"
                  size="sm"
                  @click="goToSettings"
                >
                  <q-tooltip>Server Settings</q-tooltip>
                </q-btn>
                <q-toggle
                  v-model="saveCredentials"
                  color="grey-6"
                  dark
                  size="sm"
                  class="text-caption text-grey-6"
                  label="Remember"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>

        <!-- Custom Power Button -->
        <div class="column items-center q-mt-xl">
          <button
            class="power-btn flex flex-center"
            :class="{ 'status-offline': !isSystemOnline, 'status-online': isSystemOnline }"
            @click="handleWakeUp"
            :disabled="isSystemOnline"
          >
            <q-icon name="power_settings_new" size="40px" />
          </button>

          <div class="q-mt-md text-caption text-grey-5 tracking-widest uppercase">
            {{ isSystemOnline ? 'System Online' : 'Tap to Wake' }}
          </div>

          <!-- Emergency Network Test -->
          <div class="q-mt-lg">
            <q-btn
              flat
              dense
              color="grey-7"
              icon="wifi_find"
              label="Test Connection"
              size="sm"
              @click="testNetworkOnly"
            />
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

// System status detection
const isSystemOnline = ref(false);
const checkingStatus = ref(false);
const wakingUp = ref(false);

// Server configuration
const serverConfig = reactive({
  protocol: 'http',
  host: 'localhost',
  port: 8000
});

/**
 * Check system status - Ping server to see if it's online
 */
async function checkSystemStatus() {
  if (!serverConfig.host) {
    isSystemOnline.value = false;
    return;
  }

  checkingStatus.value = true;

  try {
    // Ping server with short timeout
    const testUrl = `${serverConfig.protocol}://${serverConfig.host}:${serverConfig.port}/api/test/connection`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout

    const response = await fetch(testUrl, {
      method: 'GET',
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json' }
    });

    clearTimeout(timeoutId);

    isSystemOnline.value = response.ok;
    console.log('[Login] System status check:', isSystemOnline.value);
  } catch (error) {
    console.log('[Login] System appears to be offline:', error);
    isSystemOnline.value = false;
  } finally {
    checkingStatus.value = false;
  }
}

/**
 * Handle WoL button click
 */
async function handleWakeUp() {
  if (isSystemOnline.value || wakingUp.value) {
    return;
  }

  if (!serverConfig.host) {
    Notify.create({
      type: 'warning',
      message: 'Please enter server IP address first',
      position: 'top',
      timeout: 2000,
      classes: 'notification-glossy'
    });
    return;
  }

  wakingUp.value = true;

  try {
    // Send WoL packet using backend API
    const api = (await import('../services/ApiService')).default;

    // First, try to get saved WoL devices from settings
    const woLDevices = settingsStore.woLDevices || [];

    if (woLDevices.length > 0) {
      // Use the first WoL device
      const targetDevice = woLDevices[0];

      const result = await api.post('/api/wol/send', {
        mac: targetDevice.mac,
        ip: targetDevice.ip,
        port: targetDevice.port || 9
      });

      if (result.success) {
        Notify.create({
          type: 'positive',
          message: 'Wake-on-LAN packet sent! Waiting for PC to start...',
          caption: 'This may take 30-60 seconds',
          position: 'top',
          timeout: 3000,
          classes: 'notification-glossy'
        });

        // Auto-check status again after a delay
        setTimeout(() => {
          checkSystemStatus();
        }, 5000);
      } else {
        Notify.create({
          type: 'negative',
          message: result.message || 'Failed to send WoL packet',
          position: 'top',
          timeout: 3000,
          classes: 'notification-glossy'
        });
      }
    } else {
      Notify.create({
        type: 'warning',
        message: 'No WoL devices configured. Please add devices in Settings.',
        caption: 'Settings → WoL Manager → Add Device',
        position: 'top',
        timeout: 4000,
        classes: 'notification-glossy'
      });
    }
  } catch (error) {
    console.error('[Login] WoL error:', error);
    Notify.create({
      type: 'negative',
      message: error.message || 'Failed to send WoL packet',
      position: 'top',
      timeout: 3000,
      classes: 'notification-glossy'
    });
  } finally {
    // Stop waking animation after 3 seconds
    setTimeout(() => {
      wakingUp.value = false;
    }, 3000);
  }
}

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

      // Update system status based on test
      isSystemOnline.value = true;

      Notify.create({
        type: 'positive',
        message: 'Network connection working! Server reachable.',
        position: 'top',
        timeout: 3000,
        classes: 'notification-glossy'
      });
    } else {
      isSystemOnline.value = false;

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

    // If connection was successful but timed out, it's reachable
    if (error.name === 'AbortError') {
      Notify.create({
        type: 'warning',
        message: 'Server reachable but slow response',
        position: 'top',
        timeout: 3000,
        classes: 'notification-glossy'
      });
    } else {
      isSystemOnline.value = false;

      Notify.create({
        type: 'negative',
        message: 'Cannot reach server. Check IP address and ensure both devices are on the same network.',
        position: 'top',
        timeout: 4000,
        classes: 'notification-glossy'
      });
    }
  }
}

/**
 * Handle login form submission
 */
async function handleLogin() {
  loginError.value = null;

  // Validate host
  if (!serverConfig.host || !serverConfig.host.trim()) {
    loginError.value = 'Server IP address is required';
    return;
  }

  if (!serverConfig.port || serverConfig.port <= 0) {
    loginError.value = 'Valid port number is required';
    return;
  }

  if (!password.value || !password.value.trim()) {
    loginError.value = 'Password is required';
    return;
  }

  loading.value = true;

  try {
    console.log('[Login] Server config:', serverConfig);

    // Update API service base URL
    settingsStore.$patch({
      server: { ...serverConfig }
    });

    // Test connection first
    const testUrl = `${serverConfig.protocol}://${serverConfig.host}:${serverConfig.port}/api/test/connection`;
    console.log('[Login] Attempting to connect to:', testUrl);

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
        timeout: 2500,
        classes: 'notification-glossy',
        dismissible: true
      });

      if (saveCredentials.value) {
        // Credentials saved
      }

      // Navigate immediately
      router.push('/dashboard');
    } else {
      loginError.value = result.error || 'Login failed';
    }
  } catch (error) {
    console.error('[Login] Error:', error);
    loginError.value = error.message || 'Connection failed. Check server settings.';
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
 * Load saved settings and check system status on mount
 */
onMounted(async () => {
  settingsStore.loadSettings();

  const savedConfig = settingsStore.server;
  if (savedConfig) {
    Object.assign(serverConfig, savedConfig);
  }

  // Check system status on mount
  await checkSystemStatus();

  // Auto-refresh status every 30 seconds
  setInterval(checkSystemStatus, 30000);
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

/* Login Page Layout - Fullscreen Flex */
.login-page {
  min-height: 100vh;
  position: relative;
  background: #000000;
}

.background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #000000;
  z-index: 0;
}

/* Compact Login Card */
.compact-login-card {
  background: rgba(20, 20, 20, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
  width: 100%;
  max-width: 400px;
}

.compact-login-card .q-card-section {
  padding: 12px 16px;
}

.compact-login-card .q-card-section:last-child {
  padding-bottom: 12px;
}

/* Compact inputs */
.compact-input :deep(.q-field__control) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-radius: 6px;
}

.compact-input :deep(.q-field__control):hover {
  background: rgba(255, 255, 255, 0.08) !important;
}

.compact-input :deep(.q-field__native) {
  color: white !important;
}

.compact-input :deep(.q-field__label) {
  color: #9ca3af !important;
  font-size: 12px !important;
}

.compact-input :deep(.q-field__marginal) {
  color: #6b7280 !important;
}

/* Power Button - Gaming PC Style */
.power-btn {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 2px solid #333;
  background: #1a1a1a; /* Dark Grey Background */
  color: #555;
  cursor: pointer;
  outline: none;
  transition: all 0.4s ease;
  position: relative;
  box-shadow: inset 0 0 10px #000; /* Inner shadow for depth */
}

/* OFFLINE STATE (Red Glow + Pulse) */
.power-btn.status-offline {
  border-color: #ff3333;
  color: #ff3333;
  box-shadow: 0 0 15px rgba(255, 51, 51, 0.5), inset 0 0 10px #000;
  animation: pulse-red 2s infinite;
}

.power-btn.status-offline:active {
  transform: scale(0.95);
  box-shadow: 0 0 5px rgba(255, 51, 51, 0.8), inset 0 0 15px #000;
}

/* ONLINE STATE (Green Static) */
.power-btn.status-online {
  border-color: #00e676;
  color: #00e676;
  box-shadow: 0 0 20px rgba(0, 230, 118, 0.3), inset 0 0 10px #000;
  cursor: default;
}

/* Animations */
@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(255, 51, 51, 0.4), inset 0 0 10px #000; }
  70% { box-shadow: 0 0 0 15px rgba(255, 51, 51, 0), inset 0 0 10px #000; }
  100% { box-shadow: 0 0 0 0 rgba(255, 51, 51, 0), inset 0 0 10px #000; }
}

/* Utility Classes */
.tracking-widest {
  letter-spacing: 0.1em;
}

.uppercase {
  text-transform: uppercase;
}


/* Error Box */
.error-box {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
}

/* Login Button */
.login-btn {
  background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
  color: white;
  border-radius: 8px;
}

.login-btn:hover {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
}

/* Responsive */
@media (max-height: 700px) {
  .compact-login-card {
    margin-bottom: 20px;
  }
}

@media (max-height: 600px) {
  .compact-login-card {
    margin-bottom: 12px;
  }
}
</style>
