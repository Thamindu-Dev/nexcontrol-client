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

          <q-card-section>
            <q-form @submit="saveServerConfig" class="q-gutter-md">
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
                :rules="[val => !!val || 'Host is required']"
              />

              <q-input
                v-model.number="serverConfig.port"
                label="Port"
                type="number"
                filled
                dense
                :rules="[val => val > 0 || 'Port is required']"
              />

              <div class="row q-mt-md">
                <div class="col-12">
                  <q-btn
                    type="submit"
                    color="white"
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

          <q-card-section>
            <div class="text-caption text-grey q-mb-sm">
              This key must match the backend's AES_KEY for encryption/decryption to work.
            </div>

            <q-input
              v-model="encryptionKey"
              label="AES Encryption Key (32+ characters)"
              filled
              dense
              :type="showKey ? 'text' : 'password'"
              hint="Must be at least 32 characters"
            >
              <template v-slot:append>
                <q-icon
                  :name="showKey ? 'visibility_off' : 'visibility'"
                  class="cursor-pointer"
                  @click="showKey = !showKey"
                />
              </template>
            </q-input>

            <div class="row q-mt-md">
              <div class="col-12">
                <q-btn
                  @click="saveEncryptionKey"
                  color="grey-7"
                  class="full-width"
                  :loading="savingKey"
                  label="Save Encryption Key"
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

          <q-card-section>
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

          <q-card-section>
            <div class="q-gutter-md">
              <q-toggle
                v-model="preferences.autoConnect"
                label="Auto-connect on start"
                color="white"
              />

              <q-select
                v-model="preferences.refreshInterval"
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

          <q-card-section>
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

            <q-slider
              v-model="thresholdConfig.cpu_threshold"
              :min="0"
              :max="100"
              :step="5"
              label
              label-always
              :markers="thresholdMarkers"
              color="grey-7"
              class="q-mb-md"
            >
              <template v-slot:label>
                CPU Alert: {{ thresholdConfig.cpu_threshold }}%
              </template>
            </q-slider>

            <q-slider
              v-model="thresholdConfig.memory_threshold"
              :min="0"
              :max="100"
              :step="5"
              label
              label-always
              :markers="thresholdMarkers"
              color="grey-7"
              class="q-mb-md"
            >
              <template v-slot:label>
                Memory Alert: {{ thresholdConfig.memory_threshold }}%
              </template>
            </q-slider>

            <q-slider
              v-model="thresholdConfig.disk_threshold"
              :min="0"
              :max="100"
              :step="5"
              label
              label-always
              :markers="thresholdMarkers"
              color="grey-8"
              class="q-mb-md"
            >
              <template v-slot:label>
                Disk Alert: {{ thresholdConfig.disk_threshold }}%
              </template>
            </q-slider>

            <q-btn
              @click="saveThresholdConfig"
              color="white"
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

          <q-card-section>
            <div class="q-gutter-md">
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
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from '../stores/auth';
import { useSettingsStore } from '../stores/settings';
import { useSystemStore } from '../stores/system';
import { getItem, setItem } from '../services/SecureStorage';
import apiService from '../services/ApiService';

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

// State
const serverConfig = reactive({
  protocol: 'http',
  host: 'localhost',
  port: 8000
});

const encryptionKey = ref('');
const showKey = ref(false);
const savingServer = ref(false);
const savingKey = ref(false);

// Preferences
const preferences = reactive({
  autoConnect: false,
  refreshInterval: 5000
});

const refreshOptions = [
  { label: '2 seconds', value: 2000 },
  { label: '5 seconds', value: 5000 },
  { label: '10 seconds', value: 10000 },
  { label: '30 seconds', value: 30000 }
];

// Watch polling interval changes and update system store
watch(() => preferences.refreshInterval, (newInterval) => {
  console.log('[Settings] Polling interval changed to:', newInterval, 'ms');

  // Update system store's polling interval
  systemStore.setRefreshInterval(newInterval);

  // Save the new interval to settings
  settingsStore.updatePreferences({ refreshInterval: newInterval });
}, { immediate: false });

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

  $q.notify({
    type: 'info',
    message: value ? 'Dark mode enabled' : 'Dark mode disabled',
    position: 'top'
  });
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

    $q.notify({
      type: 'info',
      message: 'Following system theme',
      position: 'top'
    });
  } else {
    // Switch back to manual mode
    $q.dark.set(darkMode.value);
    await setItem('nexcontrol_auto_dark_mode', 'false');
    await setItem('nexcontrol_dark_mode', darkMode.value ? 'true' : 'false');

    $q.notify({
      type: 'info',
      message: 'Manual theme mode',
      position: 'top'
    });
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
const thresholdMarkers = [
  { value: 0, label: '0%' },
  { value: 25, label: '25%' },
  { value: 50, label: '50%' },
  { value: 75, label: '75%' },
  { value: 100, label: '100%' }
];

/**
 * Save threshold configuration
 * This saves the threshold LEVELS (when to trigger alerts)
 * View actual alerts at /threshold-alerts
 */
async function saveThresholdConfig() {
  savingThreshold.value = true;

  try {
    const response = await apiService.put('/api/threshold/config', null, {
      cpu_threshold: thresholdConfig.cpu_threshold,
      memory_threshold: thresholdConfig.memory_threshold,
      disk_threshold: thresholdConfig.disk_threshold,
      enabled: thresholdConfig.enabled
    });

    if (response.success) {
      $q.notify({
        type: 'positive',
        message: 'Threshold settings saved',
        position: 'top'
      });
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to save threshold settings',
      position: 'top'
    });
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
    $q.notify({
      type: 'negative',
      message: 'Server IP address is required',
      position: 'top'
    })
    return
  }

  // SECURITY: Validate IP is private/local only (prevent SSRF)
  if (!isValidIP(serverConfig.host)) {
    $q.notify({
      type: 'negative',
      message: 'Invalid IP address. Must be a local network IP (192.168.x.x, 10.x.x.x, 172.16-31.x.x, or localhost)',
      position: 'top'
    })
    return
  }

  // Validate port
  if (!isValidPort(serverConfig.port)) {
    $q.notify({
      type: 'negative',
      message: 'Invalid port. Must be between 1 and 65535',
      position: 'top'
    })
    return
  }

  savingServer.value = true

  try {
    // Update store
    await settingsStore.updateServer(serverConfig)

    // Update API service base URL
    settingsStore.$patch({
      server: { ...serverConfig }
    })

    $q.notify({
      type: 'positive',
      message: 'Server configuration saved',
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to save server config',
      position: 'top'
    })
  } finally {
    savingServer.value = false
  }
}

/**
 * Save encryption key
 */
function saveEncryptionKey() {
  savingKey.value = true;

  try {
    if (encryptionKey.value && encryptionKey.value.length >= 32) {
      const success = settingsStore.setEncryptionKey(encryptionKey.value);

      if (success) {
        $q.notify({
          type: 'positive',
          message: 'Encryption key saved',
          position: 'top'
        });

        encryptionKey.value = '';
      } else {
        $q.notify({
          type: 'negative',
          message: 'Key must be at least 32 characters',
          position: 'top'
        });
      }
    } else {
      $q.notify({
        type: 'negative',
        message: 'Please enter a valid encryption key (32+ characters)',
        position: 'top'
      });
    }
  } finally {
    savingKey.value = false;
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
    settingsStore.resetSettings();

    // Reset local state
    Object.assign(serverConfig, {
      protocol: 'http',
      host: 'localhost',
      port: 8000
    });
    encryptionKey.value = '';
    preferences.autoConnect = false;
    preferences.refreshInterval = 5000;

    $q.notify({
      type: 'info',
      message: 'All settings reset to default',
      position: 'top'
    });
  });
}

/**
 * Load settings on mount
 */
onMounted(async () => {
  settingsStore.loadSettings();

  // Load server config
  const savedConfig = settingsStore.server;
  if (savedConfig) {
    Object.assign(serverConfig, { ...savedConfig });
  }

  // Load preferences
  const savedPrefs = settingsStore.preferences;
  if (savedPrefs) {
    Object.assign(preferences, { ...savedPrefs });

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
