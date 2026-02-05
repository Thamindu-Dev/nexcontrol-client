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
    <q-page padding class="q-pl-none q-pr-md">
      <!-- App Launcher Card -->
      <div class="row q-col-gutter-md q-mb-sm">
        <div class="col-12">
          <q-card class="action-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center justify-between">
                <div class="row items-center">
                  <q-icon name="apps" size="20px" color="grey-5" class="q-mr-sm" />
                  <div class="text-subtitle2 text-white">App Launcher</div>
                </div>
                <div class="row items-center q-gutter-xs">
                  <q-btn
                    flat
                    round
                    dense
                    icon="add"
                    size="sm"
                    class="header-btn"
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
                    class="header-btn"
                    :loading="loading"
                    @click="loadApps"
                  >
                    <q-tooltip>Refresh app list</q-tooltip>
                  </q-btn>
                </div>
              </div>
            </q-card-section>

            <q-card-section class="q-pt-none q-pb-md q-px-md">
              <!-- Platform Indicator -->
              <div class="row q-mb-md">
                <div class="col-12">
                  <q-chip
                    :icon="platformIcon"
                    :label="platformLabel"
                    color="cyan"
                    text-color="white"
                    size="sm"
                    dense
                    class="platform-chip"
                  />
                  <span v-if="apps.length > 0" class="text-grey-6 q-ml-md text-caption">
                    {{ apps.length }} apps available ({{ customAppsCount }} custom)
                  </span>
                </div>
              </div>

              <!-- Loading State -->
              <div v-if="loading && apps.length === 0" class="text-center q-pa-xl">
                <q-spinner color="cyan" size="32px" />
                <div class="text-caption text-grey-6 q-mt-sm">Loading applications...</div>
              </div>

              <!-- Error State -->
              <div v-if="error && apps.length === 0" class="text-center q-pa-lg">
                <q-icon name="error_outline" size="40px" color="red" class="q-mb-sm" />
                <div class="text-caption text-white q-mb-sm">{{ error }}</div>
                <q-btn
                  flat
                  label="Retry"
                  color="cyan"
                  size="sm"
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
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Add Custom App Dialog -->
      <q-dialog v-model="showAddAppDialog" class="glass-dialog">
        <q-card style="min-width: 400px; background: #000000; color: #FFFFFF;">
          <q-card-section class="q-pa-md">
            <div class="text-h6 text-white">Add Custom App</div>
          </q-card-section>

          <q-card-section class="q-pt-none q-pa-md">
            <q-form @submit="addCustomApp" class="q-gutter-md">
              <q-input
                v-model="newApp.name"
                label="App Name"
                outlined
                dark
                color="cyan"
                :rules="[val => !!val || 'Name is required']"
              />

              <q-select
                v-model="newApp.type"
                :options="[
                  { label: 'Local Application', value: 'local' },
                  { label: 'Website / URL', value: 'web' }
                ]"
                label="App Type"
                outlined
                dark
                color="cyan"
                emit-value
                map-options
              />

              <q-input
                v-if="newApp.type === 'local'"
                v-model="newApp.path"
                label="Application Path"
                outlined
                dark
                color="cyan"
                hint="e.g., C:\Program Files\MyApp\app.exe or /usr/bin/myapp"
                :rules="[val => newApp.type === 'local' ? !!val || 'Path is required' : true]"
              >
                <template v-slot:prepend>
                  <q-icon name="folder" color="grey-5" />
                </template>
              </q-input>

              <q-input
                v-if="newApp.type === 'web'"
                v-model="newApp.url"
                label="Website URL"
                outlined
                dark
                color="cyan"
                hint="e.g., https://youtube.com or https://github.com"
                :rules="[val => newApp.type === 'web' ? !!val || 'URL is required' : true]"
              >
                <template v-slot:prepend>
                  <q-icon name="language" color="grey-5" />
                </template>
              </q-input>

              <q-select
                v-model="newApp.icon"
                :options="iconOptions"
                label="Icon"
                outlined
                dark
                color="cyan"
                emit-value
                map-options
              >
                <template v-slot:prepend>
                  <q-icon :name="newApp.icon" color="cyan" />
                </template>
              </q-select>
            </q-form>
          </q-card-section>

          <q-card-section class="q-pa-md" style="display: flex; justify-content: flex-end; gap: 8px;">
            <q-btn flat label="Cancel" color="grey-5" v-close-popup />
            <q-btn
              unelevated
              label="Add App"
              color="cyan"
              :loading="addingApp"
              @click="addCustomApp"
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
 * Add custom application
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
    const response = await api.post('/api/apps/custom', newApp.value);

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

/* Platform chip */
.platform-chip {
  background: rgba(34, 211, 238, 0.15) !important;
  border: 1px solid rgba(34, 211, 238, 0.3);
}

/* Header button */
.header-btn {
  color: #FFFFFF;
  background: transparent;
  border: 1px solid #333333;
  border-radius: 8px;
}

.header-btn:hover {
  background: rgba(30, 30, 30, 0.9);
}

/* App Launcher Buttons - Matching Dashboard Media Control Style */
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
  .app-launcher-btn {
    padding: 12px !important;
  }
}

@media (hover: none) and (pointer: coarse) {
  .app-launcher-btn:hover {
    transform: none !important;
  }
}
</style>
