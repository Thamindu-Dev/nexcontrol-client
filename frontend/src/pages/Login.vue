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
  <div class="login-page q-pa-md">
    <div class="column fullscreen bg-blue-1">
      <div class="row items-center">
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <q-card class="q-pa-md">
            <q-card-section>
              <div class="text-h5 text-center text-weight-bold text-primary">
                NexControl
              </div>
              <div class="text-subtitle2 text-center text-grey">
                Remote PC Controller
              </div>
            </q-card-section>

            <q-card-section>
              <q-form @submit="handleLogin" class="q-gutter-md">
                <!-- Server Configuration -->
                <div class="text-subtitle2 text-grey-7">
                  Server Configuration
                </div>

                <q-input
                  v-model="serverConfig.host"
                  label="Server IP"
                  filled
                  dense
                  hint="e.g., 192.168.1.100"
                  :rules="[val => !!val || 'Host is required']"
                />

                <q-input
                  v-model.number="serverConfig.port"
                  label="Port"
                  type="number"
                  filled
                  dense
                  hint="Default: 8000"
                  :rules="[val => val > 0 || 'Port is required']"
                />

                <q-separator class="q-my-md" />

                <!-- Login Form -->
                <div class="text-subtitle2 text-grey-7">
                  Login
                </div>

                <q-input
                  v-model="password"
                  label="Password"
                  :type="isPwd ? 'password' : 'text'"
                  filled
                  dense
                  hint="Enter your app password"
                  :rules="[val => !!val || 'Password is required']"
                >
                  <template v-slot:append>
                    <q-icon
                      :name="isPwd ? 'visibility_off' : 'visibility'"
                      class="cursor-pointer"
                      @click="isPwd = !isPwd"
                    />
                  </template>
                </q-input>

                <div v-if="loginError" class="text-negative text-caption q-mb-sm">
                  {{ loginError }}
                </div>

                <q-btn
                  type="submit"
                  color="primary"
                  class="full-width"
                  :loading="loading"
                  :disable="loading"
                  label="Connect"
                  size="md"
                />

                <div class="q-mt-md">
                  <q-checkbox v-model="saveCredentials" label="Save credentials" />
                </div>
              </q-form>
            </q-card-section>

            <q-card-section>
              <div class="text-caption text-grey">
                <div><strong>Note:</strong> This is a local network app.</div>
                <div>Make sure your PC is on the same network.</div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from '../stores/auth';
import { useSettingsStore } from '../stores/settings';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'LoginPage'
});

const router = useRouter();
const $q = useQuasar();

// Stores
const authStore = useAuthStore();
const settingsStore = useSettingsStore();

// State
const password = ref('');
const isPwd = ref(true);
const loading = ref(false);
const loginError = ref(null);
const saveCredentials = ref(false);

// Server configuration
const serverConfig = reactive({
  protocol: 'http',
  host: 'localhost',
  port: 8000
});

/**
 * Validate IP address (private/local only for security)
 * @param {string} ip - IP address to validate
 * @returns {boolean} True if valid private/local IP
 */
function isValidIP(ip) {
  if (!ip || typeof ip !== 'string') return false

  const ipLower = ip.toLowerCase().trim()

  // Check for localhost
  if (ipLower === 'localhost') return true

  // IPv4 private ranges
  const privateRanges = [
    /^10\./,                           // 10.0.0.0/8
    /^172\.(1[6-9]|2\d|3[01])\./,    // 172.16.0.0/12
    /^192\.168\./,                     // 192.168.0.0/16
    /^127\./                           // 127.0.0.0/8 (loopback)
  ]

  // Check IPv4 format
  const ipv4Regex = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/
  const ipv4Match = ip.match(ipv4Regex)

  if (ipv4Match) {
    // Valid IPv4, check if in private range
    return privateRanges.some(range => range.test(ip))
  }

  return false
}

/**
 * Validate port number
 * @param {number} port - Port to validate
 * @returns {boolean} True if valid port
 */
function isValidPort(port) {
  const portNum = Number(port)
  return !isNaN(portNum) && portNum >= 1 && portNum <= 65535
}

/**
 * Handle login form submission (with validation)
 */
async function handleLogin() {
  // Validate host/IP
  if (!serverConfig.host || !serverConfig.host.trim()) {
    loginError.value = 'Server IP address is required'
    return
  }

  // SECURITY: Validate IP is private/local only (prevent SSRF)
  if (!isValidIP(serverConfig.host)) {
    loginError.value = 'Invalid IP address. Must be a local network IP'
    $q.notify({
      type: 'negative',
      message: 'Invalid IP address. Must be a local network IP (192.168.x.x, 10.x.x.x, 172.16-31.x.x, or localhost)',
      position: 'top'
    })
    return
  }

  // Validate port
  if (!isValidPort(serverConfig.port)) {
    loginError.value = 'Invalid port. Must be between 1 and 65535'
    $q.notify({
      type: 'negative',
      message: 'Invalid port. Must be between 1 and 65535',
      position: 'top'
    })
    return
  }

  loading.value = true;
  loginError.value = null;

  // Debug logging
  const serverUrl = `${serverConfig.protocol}://${serverConfig.host}:${serverConfig.port}`;
  console.log('[Login] Attempting to connect to:', serverUrl);
  console.log('[Login] Capacitor available:', typeof window !== 'undefined' && window.Capacitor);

  try {
    // Update server configuration
    await settingsStore.updateServer(serverConfig);
    console.log('[Login] Server config updated');

    // FIRST: Test connection to trigger iOS local network permission popup
    console.log('[Login] Testing connection...');
    const testUrl = `${serverUrl}/api/test/connection`;

    try {
      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const testResponse = await fetch(testUrl, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      console.log('[Login] Test connection response:', testResponse.status);

      // Parse the response body to ensure it's valid
      let testData;
      try {
        testData = await testResponse.json();
        console.log('[Login] Test connection data:', testData);
      } catch (parseError) {
        console.error('[Login] Failed to parse test response:', parseError);
        // Even if parsing fails, if status is OK, continue
      }

      // If test fails, don't proceed with login
      if (!testResponse.ok) {
        throw new Error(`Server returned ${testResponse.status}`);
      }

      // Check for expected response
      if (!testData || !testData.status || (testData.status !== 'connected' && testData.status !== 'ok')) {
        console.warn('[Login] Unexpected test response:', testData);
      }
    } catch (testError) {
      console.error('[Login] Connection test failed:', testError);
      loginError.value = 'Cannot reach server. Make sure your PC is on and check the IP address.';
      loading.value = false;

      // Show helpful message for iOS
      if (typeof window !== 'undefined' && window.Capacitor?.getPlatform() === 'ios') {
        $q.notify({
          type: 'warning',
          message: 'If you see a popup about Local Network access, tap OK to allow',
          position: 'top',
          timeout: 5000
        });
      }
      return;
    }

    // SECOND: Attempt login now that connection is confirmed
    console.log('[Login] Connection OK, calling authStore.login...');

    const result = await authStore.login(password.value);
    console.log('[Login] Login result:', result);

    if (result.success) {
      // Show success message
      $q.notify({
        type: 'positive',
        message: 'Connected successfully!',
        position: 'top'
      });

      // Save credentials if checked
      if (saveCredentials.value) {
        // Credentials already saved in stores
      }

      // Navigate to dashboard
      router.push('/dashboard');
    } else {
      loginError.value = result.error || 'Login failed';
    }
  } catch (error) {
    console.error('[Login] Error:', error);
    loginError.value = error.message || 'Connection failed. Check server settings.';
    $q.notify({
      type: 'negative',
      message: loginError.value,
      position: 'top'
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

  // Load saved server config
  const savedConfig = settingsStore.server;
  if (savedConfig) {
    Object.assign(serverConfig, savedConfig);
  }

  // Expose test function to window for debugging from Safari console
  if (typeof window !== 'undefined') {
    // Test GET request
    window.testNexControlConnection = async () => {
      try {
        const protocol = serverConfig.protocol || 'http';
        const host = serverConfig.host;
        const port = serverConfig.port;
        const url = `${protocol}://${host}:${port}/api/test/connection`;

        console.log('[Test GET] Connecting to:', url);

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
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

    // Test POST request
    window.testNexControlPOST = async () => {
      try {
        const protocol = serverConfig.protocol || 'http';
        const host = serverConfig.host;
        const port = serverConfig.port;
        const url = `${protocol}://${host}:${port}/api/test/echo`;

        console.log('[Test POST] Connecting to:', url);
        console.log('[Test POST] Testing POST request...');

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ test: 'data from iOS', timestamp: Date.now() }),
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
          console.error('[Test POST] Request timed out after 10 seconds');
        }
        throw error;
      }
    };

    console.log('[NexControl] Debug: Call window.testNexControlConnection() for GET test');
    console.log('[NexControl] Debug: Call window.testNexControlPOST() for POST test');
  }
});
</script>

<style scoped>
.login-page {
  min-height: 100vh;
}

.fullscreen {
  min-height: 100vh;
}
</style>
