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
                    {{ apps.length }} apps available
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
                      <q-icon :name="app.icon" size="32px" color="cyan" />
                      <div class="text-caption text-weight-medium q-mt-xs">{{ app.name }}</div>
                      <q-tooltip>{{ app.name }}</q-tooltip>
                    </q-btn>
                  </div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
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

      secureNotify.success($q, `Launching ${app.name}...`);
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
