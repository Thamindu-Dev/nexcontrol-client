<template>
  <q-page padding>
    <div class="row q-mb-md">
      <div class="col-12">
        <div class="text-h5">Settings</div>
      </div>
    </div>

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
                    color="primary"
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
                  color="secondary"
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
                color="primary"
              />

              <q-select
                v-model="preferences.refreshInterval"
                :options="refreshOptions"
                label="Auto-refresh interval"
                filled
                dense
                emit-value
                map
              />
            </div>
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
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from 'stores/auth';
import { useSettingsStore } from 'stores/settings';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'SettingsPage'
});

const router = useRouter();
const $q = useQuasar();

// Stores
const authStore = useAuthStore();
const settingsStore = useSettingsStore();

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

/**
 * Save server configuration
 */
async function saveServerConfig() {
  savingServer.value = true;

  try {
    // Update store
    await settingsStore.updateServer(serverConfig);

    // Update API service base URL
    settingsStore.$patch({
      server: { ...serverConfig }
    });

    $q.notify({
      type: 'positive',
      message: 'Server configuration saved',
      position: 'top'
    });
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to save server config',
      position: 'top'
    });
  } finally {
    savingServer.value = false;
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
onMounted(() => {
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
  }
});
</script>
