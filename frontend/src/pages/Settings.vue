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
  <q-page padding>
    <!-- Server Configuration -->
    <div class="row q-mb-md">
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Server Configuration</div>
          </q-card-section>

          <q-card-section class="q-pa-md">
            <q-form @submit="saveServerConfig" class="q-gutter-y-md">
              <q-input
                v-model="serverConfig.protocol"
                label="Protocol"
                filled
                dense
                disable
                hint="HTTP (HTTPS not yet supported)"
              />

              <q-input
                v-model="serverConfig.host"
                label="Server IP Address"
                filled
                dense
                hint="e.g., 192.168.1.100 or localhost"
                :rules="[validateHost]"
              />

              <q-input
                v-model.number="serverConfig.port"
                label="Port"
                type="number"
                filled
                dense
                :rules="[validatePort]"
              />

              <div class="row q-mt-md">
                <div class="col-12">
                  <q-btn
                    type="submit"
                    color="cyan"
                    text-color="black"
                    unelevated
                    class="full-width"
                    label="Save Server Config"
                    :loading="savingServer"
                  />
                </div>
              </div>
            </q-form>
          </q-card-section>
        </q-card>
      </div>

      <!-- Encryption Key -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Encryption Key</div>
          </q-card-section>

          <q-card-section class="q-pa-md">
            <div class="text-caption text-grey q-mb-sm">
              This key must match the backend's AES_KEY for encryption/decryption to work.
            </div>

            <q-input
              v-model="encryptionKey"
              :label="keyLabel"
              filled
              dense
              :type="showKey ? 'text' : 'password'"
              :hint="keyHint"
              :rules="[validateEncryptionKey]"
              @focus="clearExistingKey"
            >
              <template v-slot:prepend>
                <q-icon
                  :name="hasKey ? 'lock' : 'lock_open'"
                  :color="hasKey ? 'green' : 'grey-5'"
                />
              </template>
              <template v-slot:append>
                <q-icon
                  :name="showKey ? 'visibility_off' : 'visibility'"
                  class="cursor-pointer"
                  @click="showKey = !showKey"
                >
                  <q-tooltip>{{ showKey ? 'Hide key' : 'Show key' }}</q-tooltip>
                </q-icon>
              </template>
            </q-input>

            <div class="row q-mt-md">
              <div class="col-12">
                <q-btn
                  @click="saveEncryptionKey"
                  color="cyan"
                  text-color="black"
                  unelevated
                  class="full-width"
                  :loading="savingKey"
                  :label="saveKeyLabel"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Appearance -->
    <div class="row q-mb-md">
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Appearance</div>
          </q-card-section>

          <q-card-section class="q-pa-md">
            <div class="text-caption text-grey q-mb-md">
              Customize the app's appearance and theme.
            </div>

            <!-- Dark Mode Toggle -->
            <div class="row items-center q-mb-md">
              <div class="col">
                <div class="text-subtitle1 q-mb-xs">Dark Mode</div>
                <div class="text-caption text-grey">
                  {{ darkModeStatus }}
                </div>
              </div>
              <div class="col-auto">
                <q-toggle
                  v-model="darkMode"
                  color="white"
                  size="lg"
                  checked-icon="nights_stay"
                  unchecked-icon="wb_sunny"
                  @update:model-value="toggleDarkMode"
                >
                  <q-tooltip v-if="!darkMode">Enable dark theme</q-tooltip>
                  <q-tooltip v-else>Disable dark theme</q-tooltip>
                </q-toggle>
              </div>
            </div>

            <!-- Auto Dark Mode -->
            <div class="row items-center">
              <div class="col">
                <div class="text-subtitle2 q-mb-xs">Follow System</div>
                <div class="text-caption text-grey">
                  Automatically switch based on device settings
                </div>
              </div>
              <div class="col-auto">
                <q-toggle
                  v-model="autoDarkMode"
                  color="white"
                  size="md"
                  @update:model-value="toggleAutoDarkMode"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Preferences -->
    <div class="row q-mb-md">
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Preferences</div>
          </q-card-section>

          <q-card-section class="q-pa-md">
            <div class="q-gutter-y-md">
              <q-toggle
                v-model="localPrefs.autoConnect"
                label="Auto-connect on start"
                color="white"
              />

              <q-select
                v-model="localPrefs.refreshInterval"
                :options="refreshOptions"
                label="Polling Interval"
                filled
                dense
                emit-value
                map-options
              />
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Threshold Configuration -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Threshold Configuration</div>
          </q-card-section>

          <q-card-section class="q-pa-md">
            <div class="text-caption text-grey q-mb-md">
              Configure alert thresholds for system resources.
              <q-btn
                flat
                dense
                color="cyan"
                icon="open_in_new"
                label="View Alerts"
                to="/threshold-alerts"
                class="q-ml-sm"
              />
            </div>

            <q-toggle
              v-model="thresholdConfig.enabled"
              label="Enable Threshold Monitoring"
              color="white"
              class="q-mb-md"
            />

            <!-- CPU Threshold Slider -->
            <div class="q-mb-md">
              <div class="text-subtitle2 text-white q-mb-sm">
                <q-icon name="memory" size="16px" class="q-mr-xs" />
                CPU Usage Alert (%)
              </div>
              <q-slider
                v-model="thresholdConfig.cpu_threshold"
                :min="0"
                :max="100"
                :step="5"
                label
                label-always
                color="grey-7"
              >
                <template v-slot:label>
                  {{ thresholdConfig.cpu_threshold }}%
                </template>
              </q-slider>
            </div>

            <!-- RAM/Memory Threshold Slider -->
            <div class="q-mb-md">
              <div class="text-subtitle2 text-white q-mb-sm">
                <q-icon name="storage" size="16px" class="q-mr-xs" />
                RAM Usage Alert (%)
              </div>
              <q-slider
                v-model="thresholdConfig.memory_threshold"
                :min="0"
                :max="100"
                :step="5"
                label
                label-always
                color="grey-7"
              >
                <template v-slot:label>
                  {{ thresholdConfig.memory_threshold }}%
                </template>
              </q-slider>
            </div>

            <!-- Disk Threshold Slider -->
            <div class="q-mb-md">
              <div class="text-subtitle2 text-white q-mb-sm">
                <q-icon name="folder" size="16px" class="q-mr-xs" />
                Disk Usage Alert (%)
              </div>
              <q-slider
                v-model="thresholdConfig.disk_threshold"
                :min="0"
                :max="100"
                :step="5"
                label
                label-always
                color="grey-8"
              >
                <template v-slot:label>
                  {{ thresholdConfig.disk_threshold }}%
                </template>
              </q-slider>
            </div>

            <q-btn
              @click="saveThresholdConfig"
              color="cyan"
              text-color="black"
              unelevated
              class="full-width q-mt-md"
              :loading="savingThreshold"
              label="Save Threshold Settings"
            />
          </q-card-section>
        </q-card>
      </div>

      <!-- Danger Zone -->
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6 text-negative">Danger Zone</div>
          </q-card-section>

          <q-card-section class="q-pa-md">
            <div class="q-gutter-y-md">
              <q-btn
                @click="clearCredentials"
                outline
                color="negative"
                class="full-width"
                label="Clear Saved Credentials"
              />

              <q-btn
                @click="resetAllSettings"
                outline
                color="negative"
                class="full-width"
                label="Reset All Settings"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- App Info -->
    <div class="row q-mt-md">
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle2">About NexControl</div>
            <div class="text-caption text-grey">
              Version 1.0.0 - Remote PC Controller<br>
              Created for Engineering Students & SysAdmins
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { storeToRefs } from 'pinia';
import { useAuthStore } from '../stores/auth';
import { useSettingsStore } from '../stores/settings';
import { useSystemStore } from '../stores/system';
import { getItem, setItem } from '../services/SecureStorage';
import apiService from '../services/ApiService';
import { secureNotify } from '../services/NotifyService';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'SettingsPage'
});

const router = useRouter();
const $q = useQuasar();

// Stores
const authStore = useAuthStore();
const settingsStore = useSettingsStore();
const systemStore = useSystemStore();

// Use storeToRefs to preserve reactivity when destructuring
// Only destructure state and getters, NOT actions
const { hasKey, hasEncryptionKey, server, preferences } = storeToRefs(settingsStore);

// Keep actions as direct references (not from storeToRefs)
const { updateServer, setEncryptionKey: setStoreEncryptionKey, updatePreferences, loadSettings, resetSettings } = settingsStore;

// Constants for write-only security
const KEY_PLACEHOLDER = '**********'; // 10 asterisks as placeholder

// State
const serverConfig = reactive({
  protocol: 'http',
  host: 'localhost',
  port: 8000
});

const encryptionKey = ref('');
const savingServer = ref(false);
const savingKey = ref(false);
const showKey = ref(false); // Controls password visibility toggle

// Watch encryption key state changes for debugging
watch(hasEncryptionKey, (hasKey) => {
  console.log('[SettingsPage] Encryption key state changed:', hasKey);
}, { immediate: true });

// Computed properties for encryption key field (using reactive refs from storeToRefs)
const keyLabel = computed(() => {
  return hasKey.value
    ? 'AES Encryption Key (Key Saved - Hidden for Security)'
    : 'AES Encryption Key (32+ characters)';
});

const keyHint = computed(() => {
  if (hasKey.value) {
    return 'Current key hidden. Clear field to enter a new one';
  }
  return 'Must be at least 32 characters';
});

const saveKeyLabel = computed(() => {
  return hasKey.value ? 'Update Encryption Key' : 'Save Encryption Key';
});

// Local preferences state (avoid shadowing store's preferences ref)
const localPrefs = reactive({
  autoConnect: false,
  refreshInterval: 5000
});

const refreshOptions = [
  { label: '2 seconds', value: 2000 },
  { label: '5 seconds', value: 5000 },
  { label: '10 seconds', value: 10000 },
  { label: '30 seconds', value: 30000 }
];

// ============================================================
// VALIDATION RULES (Quasar form validation)
// ============================================================

/**
 * Validate host address (IP or hostname)
 */
const validateHost = (val) => {
  if (!val) return 'Host is required';

  // Check for localhost
  if (val === 'localhost') return true;

  // Check for IPv4 pattern
  const ipv4Pattern = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;
  if (ipv4Pattern.test(val)) {
    const parts = val.split('.');
    if (parts.every(part => parseInt(part) >= 0 && parseInt(part) <= 255)) {
      return true;
    }
  }

  // Check for hostname pattern (basic check)
  const hostnamePattern = /^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/;
  if (hostnamePattern.test(val)) return true;

  return 'Invalid IP address or hostname';
};

/**
 * Validate port number (1-65535)
 */
const validatePort = (val) => {
  if (!val || val <= 0) return 'Port is required';
  if (val < 1 || val > 65535) return 'Port must be between 1 and 65535';
  return true;
};

/**
 * Validate encryption key length
 */
const validateEncryptionKey = (val) => {
  if (!val) return true; // Empty is allowed (means no change)
  if (val === KEY_PLACEHOLDER) return true; // Placeholder is allowed
  if (val.length < 32) return 'Key must be at least 32 characters';
  return true;
};

// Watch polling interval changes and update system store (with proper async handling)
watch(
  () => localPrefs.refreshInterval,
  async (newInterval, oldInterval) => {
    console.log(`[Settings] Polling interval changing from ${oldInterval} to ${newInterval}ms`);

    // Wait for next tick to ensure DOM updates
    await nextTick();

    // Update system store's polling interval
    systemStore.setRefreshInterval(newInterval);

    // Save the new interval to settings
    updatePreferences({ refreshInterval: newInterval });
  },
  { flush: 'post' }
);

// Dark Mode
const darkMode = ref($q.dark.isActive);
const autoDarkMode = ref(false);

/**
 * Computed property for dark mode status text
 */
const darkModeStatus = computed(() => {
  if (autoDarkMode.value) return 'Following system';
  return darkMode.value ? 'Enabled' : 'Disabled';
});

/**
 * Toggle dark mode
 */
async function toggleDarkMode(value) {
  darkMode.value = value;
  $q.dark.set(value);

  // Save to storage
  await setItem('nexcontrol_dark_mode', value ? 'true' : 'false');
  await setItem('nexcontrol_auto_dark_mode', 'false');
  autoDarkMode.value = false;

  secureNotify.info($q, value ? 'Dark mode enabled' : 'Dark mode disabled');
}

/**
 * Toggle auto dark mode (follow system)
 */
async function toggleAutoDarkMode(value) {
  autoDarkMode.value = value;

  if (value) {
    $q.dark.set('auto');
    darkMode.value = $q.dark.isActive;
    await setItem('nexcontrol_auto_dark_mode', 'true');
    await setItem('nexcontrol_dark_mode', 'false');

    secureNotify.info($q, 'Following system theme');
  } else {
    // Switch back to manual mode
    $q.dark.set(darkMode.value);
    await setItem('nexcontrol_auto_dark_mode', 'false');
    await setItem('nexcontrol_dark_mode', darkMode.value ? 'true' : 'false');

    secureNotify.info($q, 'Manual theme mode');
  }
}

// Threshold Configuration
const thresholdConfig = reactive({
  enabled: true,
  cpu_threshold: 80,
  memory_threshold: 85,
  disk_threshold: 90
});
const savingThreshold = ref(false);

/**
 * Save threshold configuration
 * This saves the threshold LEVELS (when to trigger alerts)
 * View actual alerts at /threshold-alerts
 */
async function saveThresholdConfig() {
  savingThreshold.value = true;

  try {
    const response = await apiService.post('/api/threshold/config', {
      cpu_threshold: thresholdConfig.cpu_threshold,
      memory_threshold: thresholdConfig.memory_threshold,
      disk_threshold: thresholdConfig.disk_threshold,
      enabled: thresholdConfig.enabled
    });

    // Backend returns ThresholdConfig directly on success
    if (response && (response.cpu_threshold !== undefined || response.enabled !== undefined)) {
      secureNotify.success($q, 'Threshold settings saved');
      // Update local state with response
      Object.assign(thresholdConfig, response);
    } else {
      secureNotify.error($q, 'Failed to save threshold settings');
    }
  } catch (error) {
    secureNotify.error($q, error.message || 'Failed to save threshold settings');
  } finally {
    savingThreshold.value = false;
  }
}

/**
 * Load threshold configuration
 */
async function loadThresholdConfig() {
  try {
    const response = await apiService.get('/api/threshold/config');
    if (response.success && response.data) {
      Object.assign(thresholdConfig, response.data);
    }
  } catch (error) {
    // Silently fail - use defaults
    console.error('Failed to load threshold config:', error);
  }
}

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
 * Save server configuration (with validation)
 */
async function saveServerConfig() {
  // Validate host/IP
  if (!serverConfig.host || !serverConfig.host.trim()) {
    secureNotify.error($q, 'Server IP address is required');
    return
  }

  // SECURITY: Validate IP is private/local only (prevent SSRF)
  if (!isValidIP(serverConfig.host)) {
    secureNotify.error($q, 'Invalid IP address. Must be a local network IP (192.168.x.x, 10.x.x.x, 172.16-31.x.x, or localhost)');
    return
  }

  // Validate port
  if (!isValidPort(serverConfig.port)) {
    secureNotify.error($q, 'Invalid port. Must be between 1 and 65535');
    return
  }

  savingServer.value = true

  try {
    // Update store using destructured action
    await updateServer(serverConfig)

    // Update API service base URL
    settingsStore.$patch({
      server: { ...serverConfig }
    })

    secureNotify.success($q, 'Server configuration saved');

    // Navigate to dashboard after successful save
    // CRITICAL: Use Vue Router instead of window.location for SPA navigation
    await router.push('/dashboard');
  } catch (error) {
    secureNotify.error($q, error.message || 'Failed to save server config');
  } finally {
    savingServer.value = false
  }
}

/**
 * Save encryption key (Write-Only Security)
 * Smart saving logic: Ignores placeholder value, only saves actual new keys
 */
function saveEncryptionKey() {
  savingKey.value = true;

  try {
    const trimmedKey = encryptionKey.value.trim();

    // Smart saving: Check if value is placeholder (means existing key, not changed)
    if (trimmedKey === KEY_PLACEHOLDER) {
      secureNotify.info($q, 'Settings Saved. (Encryption Key Unchanged)', 'Existing key preserved. Enter new key to update.');
      savingKey.value = false;
      return;
    }

    // If input is empty, treat as "no change" if key exists
    if (!trimmedKey) {
      if (hasKey.value) {
        secureNotify.info($q, 'Settings Saved. (Encryption Key Unchanged)', 'Enter a new key to update the existing one.');
      } else {
        secureNotify.error($q, 'Please enter an encryption key (32+ characters)');
      }
      savingKey.value = false;
      return;
    }

    // Validate key length
    if (trimmedKey.length < 32) {
      secureNotify.error($q, 'Key must be at least 32 characters');
      savingKey.value = false;
      return;
    }

    // Save the new key using the destructured action
    const success = setStoreEncryptionKey(trimmedKey);

    if (success) {
      secureNotify.success($q, 'Settings Saved. (Encryption Key Updated)', 'New encryption key saved to secure storage');

      // Reset to placeholder and hide
      encryptionKey.value = KEY_PLACEHOLDER;
      showKey.value = false;
    } else {
      secureNotify.error($q, 'Failed to save encryption key');
    }
  } finally {
    savingKey.value = false;
  }
}

/**
 * Clear the existing key placeholder when user focuses on input
 * This allows them to enter a new key
 */
function clearExistingKey() {
  if (hasKey.value && encryptionKey.value === KEY_PLACEHOLDER) {
    // Clear the placeholder to allow new input
    encryptionKey.value = '';
  }
}

/**
 * Clear saved credentials
 */
function clearCredentials() {
  $q.dialog({
    title: 'Clear Credentials',
    message: 'Are you sure you want to clear all saved credentials?',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    await authStore.logout();
    router.push('/login');
  });
}

/**
 * Reset all settings
 */
function resetAllSettings() {
  $q.dialog({
    title: 'Reset Settings',
    message: 'Are you sure you want to reset all settings to default?',
    cancel: true,
    persistent: true
  }).onOk(() => {
    resetSettings();

    // Reset local state
    Object.assign(serverConfig, {
      protocol: 'http',
      host: 'localhost',
      port: 8000
    });
    encryptionKey.value = ''; // Will be re-set to placeholder on next mount if key exists
    showKey.value = false;
    localPrefs.autoConnect = false;
    localPrefs.refreshInterval = 5000;

    secureNotify.info($q, 'All settings reset to default');
  });
}

/**
 * Load settings on mount
 */
onMounted(async () => {
  loadSettings();

  // Debug: Verify encryption key state from store
  console.log('[SettingsPage] Encryption key state after loadSettings:', {
    hasKey: hasKey.value,
    hasEncryptionKey: hasEncryptionKey.value
  });

  // Load server config using reactive ref
  const savedConfig = server.value;
  if (savedConfig) {
    Object.assign(serverConfig, { ...savedConfig });
  }

  // Load preferences using reactive ref
  const savedPrefs = preferences.value;
  if (savedPrefs) {
    Object.assign(localPrefs, { ...savedPrefs });

    // Initialize system store with polling interval from settings
    if (systemStore.autoRefresh) {
      systemStore.setRefreshInterval(savedPrefs.refreshInterval || 5000);
    }
  }

  // Load dark mode settings
  const savedDarkMode = await getItem('nexcontrol_dark_mode');
  const savedAutoDarkMode = await getItem('nexcontrol_auto_dark_mode');

  if (savedAutoDarkMode === 'true') {
    autoDarkMode.value = true;
    $q.dark.set('auto');
    darkMode.value = $q.dark.isActive;
  } else if (savedDarkMode === 'true') {
    darkMode.value = true;
    $q.dark.set(true);
  } else if (savedDarkMode === 'false') {
    darkMode.value = false;
    $q.dark.set(false);
  } else {
    // Default to auto if no setting saved
    darkMode.value = $q.dark.isActive;
  }

  // Load threshold configuration
  await loadThresholdConfig();

  // Set encryption key placeholder if key exists (write-only security)
  if (hasKey.value) {
    encryptionKey.value = KEY_PLACEHOLDER;
  }
});
</script>

<style scoped>
/* OLED Theme Styles */
.q-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
}
</style>
