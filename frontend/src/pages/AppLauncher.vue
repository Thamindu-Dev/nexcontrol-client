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
  <div class="app-launcher-page">
    <q-page padding class="q-pl-md q-pr-md q-pt-md q-pb-md">
      <!-- Black Container -->
      <div class="apps-container">
        <!-- Action Bar -->
        <div class="row items-center justify-between q-mb-md">
          <!-- Platform Indicator -->
          <div class="row items-center q-gutter-sm">
            <q-chip
              :icon="platformIcon"
              :label="platformLabel"
              color="cyan"
              text-color="white"
              size="sm"
              dense
              class="platform-chip"
            />
            <span v-if="apps.length > 0" class="text-caption text-grey-6">
              {{ apps.length }} apps ({{ customAppsCount }} custom)
            </span>
          </div>

          <!-- Action Buttons -->
          <div class="row items-center q-gutter-xs">
            <q-btn
              flat
              round
              dense
              icon="add"
              size="sm"
              class="action-btn"
              @click="showAddAppDialog = true"
            >
              <q-tooltip>Add Custom App</q-tooltip>
            </q-btn>
            <q-btn
              flat
              round
              dense
              icon="refresh"
              size="sm"
              class="action-btn"
              :loading="loading"
              @click="loadApps"
            >
              <q-tooltip>Refresh</q-tooltip>
            </q-btn>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading && apps.length === 0" class="text-center q-pa-xl">
          <q-spinner color="cyan" size="48px" />
          <div class="text-caption text-grey-6 q-mt-md">Loading applications...</div>
        </div>

        <!-- Error State -->
        <div v-if="error && apps.length === 0" class="text-center q-pa-xl">
          <q-icon name="error_outline" size="64px" color="red" class="q-mb-sm" />
          <div class="text-h6 text-white q-mb-sm">{{ error }}</div>
          <q-btn
            flat
            label="Retry"
            color="cyan"
            @click="loadApps"
          />
        </div>

        <!-- Apps Grid -->
        <div v-if="!loading || apps.length > 0">
          <div class="row q-col-gutter-sm">
            <div
              v-for="app in apps"
              :key="app.id"
              class="col-6 col-sm-4 col-md-3 col-lg-2"
            >
              <q-btn
                @click="launchApp(app)"
                class="app-launcher-btn full-width"
                :loading="launchingApp === app.id"
                :disable="launchingApp !== null"
                size="md"
                padding="md"
                outline
                stack
              >
                <q-icon :name="app.icon" size="32px" :color="app.is_custom ? 'orange' : 'cyan'" />
                <div class="text-caption text-weight-medium q-mt-xs">{{ app.name }}</div>
                <q-tooltip v-if="app.is_custom">
                  {{ app.name }} (Custom App)
                  <br>
                  Type: {{ app.type }}
                </q-tooltip>
                <q-tooltip v-else>{{ app.name }}</q-tooltip>
              </q-btn>
            </div>
          </div>
        </div>
      </div>

      <!-- Add Custom App Dialog -->
      <q-dialog v-model="showAddAppDialog">
        <q-card class="add-app-dialog">
          <!-- Header -->
          <q-card-section class="dialog-header">
            <div class="row items-center no-wrap">
              <q-icon name="add_circle" size="24px" color="cyan" class="q-mr-sm" />
              <div class="text-h6 text-white">Add Custom App</div>
              <q-space />
              <q-btn flat round dense icon="close" color="grey-5" size="sm" v-close-popup>
                <q-tooltip>Close</q-tooltip>
              </q-btn>
            </div>
          </q-card-section>

          <!-- Form -->
          <q-card-section class="q-pt-none">
            <q-form @submit="addCustomApp" class="q-gutter-lg">
              <!-- App Name -->
              <div class="form-field">
                <div class="field-label">App Name</div>
                <q-input
                  v-model="newApp.name"
                  placeholder="e.g., Calculator"
                  outlined
                  dense
                  dark
                  color="cyan"
                  class="custom-input"
                  :rules="[val => !!val || 'Name is required']"
                />
              </div>

              <!-- App Type -->
              <div class="form-field">
                <div class="field-label">App Type</div>
                <q-select
                  v-model="newApp.type"
                  :options="[
                    { label: 'Local Application', value: 'local' },
                    { label: 'Website / URL', value: 'web' }
                  ]"
                  outlined
                  dense
                  dark
                  color="cyan"
                  class="custom-input"
                  emit-value
                  map-options
                />
              </div>

              <!-- Application Path (for local apps) -->
              <div class="form-field" v-if="newApp.type === 'local'">
                <div class="field-label">Application Path</div>
                <q-input
                  v-model="newApp.path"
                  placeholder="e.g., C:\\Program Files\\MyApp\\app.exe or /usr/bin/myapp"
                  outlined
                  dense
                  dark
                  color="cyan"
                  class="custom-input"
                  :rules="[val => newApp.type === 'local' ? !!val || 'Path is required' : true]"
                >
                  <template v-slot:prepend>
                    <q-icon name="folder_open" color="cyan" size="20px" />
                  </template>
                </q-input>
              </div>

              <!-- Website URL (for web apps) -->
              <div class="form-field" v-if="newApp.type === 'web'">
                <div class="field-label">Website URL</div>
                <q-input
                  v-model="newApp.url"
                  placeholder="e.g., https://youtube.com or https://github.com"
                  outlined
                  dense
                  dark
                  color="cyan"
                  class="custom-input"
                  :rules="[val => newApp.type === 'web' ? !!val || 'URL is required' : true]"
                >
                  <template v-slot:prepend>
                    <q-icon name="language" color="cyan" size="20px" />
                  </template>
                </q-input>
              </div>

              <!-- Icon Selection -->
              <div class="form-field">
                <div class="field-label">Icon</div>
                <q-select
                  v-model="newApp.icon"
                  :options="iconOptions"
                  outlined
                  dense
                  dark
                  color="cyan"
                  class="custom-input"
                  emit-value
                  map-options
                >
                  <template v-slot:prepend>
                    <q-icon :name="newApp.icon" color="cyan" size="20px" />
                  </template>
                </q-select>
              </div>
            </q-form>
          </q-card-section>

          <!-- Actions -->
          <q-card-section class="dialog-actions">
            <q-btn
              flat
              label="Cancel"
              color="grey-5"
              class="action-btn-cancel"
              v-close-popup
              no-caps
              :disable="addingApp"
            />
            <q-btn
              unelevated
              label="Add App"
              color="cyan"
              class="action-btn-add"
              :loading="addingApp"
              @click="addCustomApp"
              no-caps
              :disable="addingApp || !newApp.name || (newApp.type === 'local' && !newApp.path) || (newApp.type === 'web' && !newApp.url)"
            />
          </q-card-section>
        </q-card>
      </q-dialog>
    </q-page>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useQuasar } from 'quasar';
import api from '../services/ApiService';
import { secureNotify } from '../services/NotifyService';
import { mediaWsService } from '../services/MediaWebSocketService';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'AppLauncherPage'
});

const $q = useQuasar();

// State
const apps = ref([]);
const loading = ref(false);
const error = ref(null);
const launchingApp = ref(null);
const platform = ref('unknown');
const showAddAppDialog = ref(false);
const addingApp = ref(false);

// New app form
const newApp = ref({
  name: '',
  type: 'local',
  path: '',
  url: '',
  icon: 'apps'
});

// Icon options
const iconOptions = [
  { label: 'Apps', value: 'apps' },
  { label: 'Web', value: 'language' },
  { label: 'Code', value: 'code' },
  { label: 'Terminal', value: 'terminal' },
  { label: 'Folder', value: 'folder' },
  { label: 'Music', value: 'music_note' },
  { label: 'Video', value: 'play_circle' },
  { label: 'Image', value: 'image' },
  { label: 'Settings', value: 'settings' },
  { label: 'Favorite', value: 'favorite' },
  { label: 'Star', value: 'star' },
  { label: 'Cloud', value: 'cloud' },
  { label: 'Game', value: 'sports_esports' },
  { label: 'Social', value: 'people' },
  { label: 'Mail', value: 'email' },
  { label: 'Calculator', value: 'calculate' },
  { label: 'Edit', value: 'edit_note' }
];

// Computed
const platformIcon = computed(() => {
  switch (platform.value) {
    case 'Windows': return 'computer';
    case 'Linux': return 'desktop_linux';
    case 'Darwin': return 'laptop_mac';
    default: return 'devices';
  }
});

const platformLabel = computed(() => {
  switch (platform.value) {
    case 'Windows': return 'Windows';
    case 'Linux': return 'Linux';
    case 'Darwin': return 'macOS';
    default: return platform.value;
  }
});

const customAppsCount = computed(() => {
  return apps.value.filter(app => app.is_custom).length;
});

/**
 * Load available applications from backend
 */
async function loadApps() {
  loading.value = true;
  error.value = null;

  try {
    const response = await api.get('/api/apps');

    if (response.success && response.apps) {
      apps.value = response.apps;
      platform.value = response.platform || 'unknown';
      console.log(`[AppLauncher] Loaded ${apps.value.length} apps for ${platform.value}`);
    } else {
      throw new Error('Failed to load applications');
    }
  } catch (err) {
    console.error('[AppLauncher] Error loading apps:', err);
    error.value = err.message || 'Failed to load applications';
    secureNotify.error($q, error.value);
  } finally {
    loading.value = false;
  }
}

/**
 * Add custom application via WebSocket
 */
async function addCustomApp() {
  // Validate
  if (!newApp.value.name) {
    secureNotify.error($q, 'Please enter an app name');
    return;
  }

  if (newApp.value.type === 'local' && !newApp.value.path) {
    secureNotify.error($q, 'Please enter the application path');
    return;
  }

  if (newApp.value.type === 'web' && !newApp.value.url) {
    secureNotify.error($q, 'Please enter the website URL');
    return;
  }

  addingApp.value = true;

  try {
    // Get auth token for WebSocket
    const token = await api.getToken();

    // Connect to WebSocket if not already connected
    if (!mediaWsService.isConnected() && token) {
      console.log('[AppLauncher] Connecting to WebSocket...');
      try {
        await mediaWsService.connect(token);
        console.log('[AppLauncher] WebSocket connected');
      } catch (wsError) {
        console.warn('[AppLauncher] WebSocket connection failed:', wsError);
        secureNotify.error($q, 'Failed to connect to server');
        addingApp.value = false;
        return;
      }
    }

    // Prepare data to send
    const dataToSend = {
      name: newApp.value.name,
      type: newApp.value.type,
      icon: newApp.value.icon
    };

    // Only include path or url based on type
    if (newApp.value.type === 'local') {
      dataToSend.path = newApp.value.path;
    } else if (newApp.value.type === 'web') {
      dataToSend.url = newApp.value.url;
    }

    console.log('[AppLauncher] Adding custom app via WebSocket:', dataToSend);

    // Send via WebSocket
    const response = await mediaWsService.addCustomApp(dataToSend);
    console.log('[AppLauncher] Add custom app response:', response);

    if (response.success) {
      secureNotify.success($q, response.message || 'Custom app added successfully');

      // Reset form
      newApp.value = {
        name: '',
        type: 'local',
        path: '',
        url: '',
        icon: 'apps'
      };

      // Close dialog
      showAddAppDialog.value = false;

      // Reload apps
      await loadApps();
    } else {
      secureNotify.error($q, response.message || 'Failed to add custom app');
    }
  } catch (err) {
    console.error('[AppLauncher] Error adding custom app:', err);
    secureNotify.error($q, err.message || 'Failed to add custom app');
  } finally {
    addingApp.value = false;
  }
}

/**
 * Launch an application
 * Uses WebSocket for low latency, falls back to HTTP if needed
 */
async function launchApp(app) {
  if (launchingApp.value) {
    return;
  }

  launchingApp.value = app.id;

  try {
    console.log(`[AppLauncher] Launching ${app.name} (${app.id})`);

    // Try to get auth token for WebSocket
    const token = await api.getToken();

    // Connect to WebSocket if not already connected
    if (!mediaWsService.isConnected() && token) {
      console.log('[AppLauncher] Connecting to WebSocket...');
      try {
        await mediaWsService.connect(token);
        console.log('[AppLauncher] WebSocket connected');
      } catch (wsError) {
        console.warn('[AppLauncher] WebSocket connection failed, will use HTTP fallback:', wsError);
      }
    }

    // Send command via WebSocket (will fall back to HTTP if not connected)
    console.log('[AppLauncher] Sending launch command via WebSocket...');
    const response = await mediaWsService.launchApp(app.id);
    console.log('[AppLauncher] Launch result:', response);

    if (response.success) {
      // Provide haptic feedback on mobile
      if (navigator.vibrate) {
        navigator.vibrate(50);
      }

      secureNotify.success($q, response.message || `Launching ${app.name}...`);
      console.log(`[AppLauncher] Successfully launched ${app.name}`);
    } else {
      secureNotify.error($q, response.message || `Failed to launch ${app.name}`);
    }
  } catch (err) {
    console.error(`[AppLauncher] Error launching ${app.name}:`, err);
    secureNotify.error($q, err.message || `Failed to launch ${app.name}`);
  } finally {
    launchingApp.value = null;
  }
}

/**
 * Lifecycle
 */
onMounted(() => {
  loadApps();
});

onUnmounted(() => {
  // Cleanup WebSocket connection when leaving the page
  console.log('[AppLauncher] Cleaning up WebSocket connection');
  mediaWsService.disconnect();
});
</script>

<style scoped>
.app-launcher-page {
  min-height: 100vh;
  position: relative;
  background: #000000;
}

/* Apps Container */
.apps-container {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
  padding: 20px;
}

/* Platform chip */
.platform-chip {
  background: rgba(34, 211, 238, 0.15) !important;
  border: 1px solid rgba(34, 211, 238, 0.3);
}

/* Action buttons */
.action-btn {
  color: #FFFFFF;
  background: transparent;
  border: 1px solid #333333;
  border-radius: 8px;
}

.action-btn:hover {
  background: rgba(34, 211, 238, 0.1);
  border-color: #22d3ee;
}

/* App Launcher Buttons */
.app-launcher-btn {
  background: transparent !important;
  color: #FFFFFF !important;
  border: 1px solid #333333 !important;
  border-radius: 8px;
  transition: all 0.2s ease;
  position: relative;
  z-index: 1;
}

.app-launcher-btn:hover {
  background: rgba(34, 211, 238, 0.1) !important;
  border-color: #22d3ee !important;
  color: #22d3ee !important;
}

.app-launcher-btn:active {
  transform: scale(0.95);
}

.app-launcher-btn:disabled {
  opacity: 0.6;
}

/* Responsive adjustments */
@media (max-width: 575.98px) {
  .apps-container {
    padding: 16px;
  }

  .app-launcher-btn {
    padding: 12px !important;
  }
}

@media (hover: none) and (pointer: coarse) {
  .app-launcher-btn:hover {
    transform: none !important;
  }
}

/* ============================================
   Add Custom App Dialog Styles
   ============================================ */

.add-app-dialog {
  min-width: 420px;
  max-width: 500px;
  background: #0A0A0A !important;
  border: 1px solid #333333 !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

/* Dialog Header */
.dialog-header {
  border-bottom: 1px solid #333333;
  padding: 20px 24px !important;
}

/* Form Fields */
.form-field {
  margin-bottom: 0;
}

.field-label {
  color: #FFFFFF;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  letter-spacing: 0.25px;
}

.custom-input {
  margin-bottom: 0;
}

.custom-input :deep(.q-field__control) {
  background: #1A1A1A !important;
  border: 1px solid #333333 !important;
  border-radius: 8px !important;
  color: #FFFFFF !important;
  transition: all 0.2s ease;
}

.custom-input :deep(.q-field__control:before) {
  border: none !important;
}

.custom-input :deep(.q-field__control:hover) {
  border-color: #22d3ee !important;
}

.custom-input :deep(.q-field__control-outer) {
  background: transparent !important;
}

.custom-input :deep(.q-field__native) {
  color: #FFFFFF !important;
}

.custom-input :deep(.q-field__label) {
  color: #9CA3AF !important;
}

.custom-input :deep(.q-field__marginal) {
  color: #9CA3AF !important;
}

.custom-input :deep(.q-field__prepend) {
  color: #22d3ee !important;
}

/* Dialog Actions */
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 24px !important;
  border-top: 1px solid #333333;
}

.action-btn-cancel {
  border-radius: 8px !important;
  padding: 8px 24px !important;
  font-weight: 500;
  border: 1px solid #333333 !important;
}

.action-btn-cancel:hover {
  background: rgba(255, 255, 255, 0.05) !important;
}

.action-btn-add {
  border-radius: 8px !important;
  padding: 8px 24px !important;
  font-weight: 600;
  background: #22d3ee !important;
}

.action-btn-add:hover {
  background: #1AB0C8 !important;
}

.action-btn-add:disabled {
  background: #333333 !important;
  color: #666666 !important;
}

/* Responsive adjustments */
@media (max-width: 575.98px) {
  .add-app-dialog {
    min-width: 90vw;
    max-width: 90vw;
  }

  .dialog-header,
  .dialog-actions {
    padding-left: 16px !important;
    padding-right: 16px !important;
  }
}
</style>
