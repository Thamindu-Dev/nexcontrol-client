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
  <div class="dashboard-page">
    <q-page padding class="relative-position">
      <!-- Header -->
      <div class="row q-mb-md header-section">
        <div class="col-12">
          <div class="row items-center q-gutter-sm">
            <div class="text-h4 text-weight-bold text-white">
              <q-icon name="dashboard" class="q-mr-sm" color="white" />
              Dashboard
            </div>
            <q-space />
            <div class="status-badge glossy q-px-sm q-py-xs rounded-borders">
              <q-icon :name="serverStatusIcon" :color="serverStatusColor" size="18px" class="q-mr-xs" />
              <span class="text-caption text-white">{{ serverStatusText }}</span>
            </div>
            <q-btn
              flat
              round
              dense
              icon="settings"
              class="glass-btn"
              size="sm"
              @click="openSettings"
            />
            <q-btn
              flat
              round
              dense
              icon="logout"
              class="glass-btn text-negative"
              size="sm"
              @click="handleLogout"
            />
          </div>
        </div>
      </div>

      <!-- System Stats Cards -->
      <!-- Row 1: CPU Card (Full Width) -->
      <div class="row q-gutter-sm q-mb-md">
        <div class="col-12">
          <q-card class="stat-card glass-card glossy" flat bordered>
            <q-card-section class="q-pa-sm">
              <div class="row items-center">
                <q-icon name="memory" size="28px" color="white" class="q-mr-sm stat-icon" />
                <div class="text-subtitle2 text-white">CPU Usage</div>
                <q-space />
                <div class="text-h3 text-weight-bold text-white">
                  {{ stats.cpu?.cpu_percent?.toFixed(1) || 0 }}<span class="text-h6 text-grey-4">%</span>
                </div>
                <div class="q-ml-md">
                  <q-circular-progress
                    :value="stats.cpu?.cpu_percent || 0"
                    :thickness="0.25"
                    size="60px"
                    color="white"
                    track-color="rgba(255,255,255,0.1)"
                    :indeterminate="loading.stats"
                    class="circular-progress"
                  />
                </div>
              </div>
              <div class="text-caption text-grey-4 q-mt-xs">
                <q-icon name="settings_ethernet" size="12px" class="q-mr-xs" />
                {{ stats.cpu?.cpu_count || 0 }} cores @ {{ stats.cpu?.cpu_freq_mhz?.toFixed(0) || 0 }} MHz
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Row 2: Memory & Disk (Side by Side) -->
      <div class="row q-gutter-sm q-mb-md">
        <!-- Memory Card -->
        <div class="col-6">
          <q-card class="stat-card glass-card glossy" flat bordered>
            <q-card-section class="q-pa-sm">
              <div class="row items-center q-mb-xs">
                <q-icon name="storage" size="24px" color="white" class="q-mr-xs stat-icon" />
                <div class="text-caption text-white text-weight-bold">Memory</div>
              </div>
              <div class="text-h4 text-weight-bold text-white q-mb-xs">
                {{ stats.memory?.percent?.toFixed(1) || 0 }}<span class="text-caption text-grey-4">%</span>
              </div>
              <q-linear-progress
                :value="stats.memory?.percent || 0"
                :thickness="6"
                color="white"
                track-color="rgba(255,255,255,0.1)"
                :indeterminate="loading.stats"
                rounded
                class="custom-progress q-mb-sm"
              />
              <div class="text-caption text-grey-4">
                {{ formatBytes(stats.memory?.used) }} / {{ formatBytes(stats.memory?.total) }}
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Disk Card -->
        <div class="col-6">
          <q-card class="stat-card glass-card glossy" flat bordered>
            <q-card-section class="q-pa-sm">
              <div class="row items-center q-mb-xs">
                <q-icon name="folder_open" size="24px" color="white" class="q-mr-xs stat-icon" />
                <div class="text-caption text-white text-weight-bold">Disk</div>
              </div>
              <div class="text-h4 text-weight-bold text-white q-mb-xs">
                {{ stats.disk?.percent?.toFixed(1) || 0 }}<span class="text-caption text-grey-4">%</span>
              </div>
              <q-linear-progress
                :value="stats.disk?.percent || 0"
                :thickness="6"
                color="white"
                track-color="rgba(255,255,255,0.1)"
                :indeterminate="loading.stats"
                rounded
                class="custom-progress q-mb-sm"
              />
              <div class="text-caption text-grey-4">
                {{ formatBytes(stats.disk?.used) }} / {{ formatBytes(stats.disk?.total) }}
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Power Controls -->
      <div class="row q-gutter-sm q-mb-md">
        <div class="col-12">
          <q-card class="glass-card glossy" flat bordered>
            <q-card-section class="q-pa-sm">
              <div class="row items-center q-mb-sm">
                <q-icon name="bolt" size="20px" color="white" class="q-mr-sm" />
                <div class="text-subtitle2 text-white">Power Management</div>
              </div>
            </q-card-section>

            <q-card-section class="q-pt-none q-pb-sm q-px-sm">
              <div class="row q-gutter-xs">
                <div class="col-4">
                  <q-btn
                    @click="confirmShutdown"
                    class="power-btn power-shutdown full-width glossy"
                    size="md"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                    padding="xs md"
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="power_settings_new" size="18px" class="q-mr-xs" />
                      <span class="text-caption text-weight-bold">Shutdown</span>
                    </div>
                  </q-btn>
                </div>

                <div class="col-4">
                  <q-btn
                    @click="confirmHibernate"
                    class="power-btn power-hibernate full-width glossy"
                    size="md"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                    padding="xs md"
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="bedtime" size="18px" class="q-mr-xs" />
                      <span class="text-caption text-weight-bold">Hibernate</span>
                    </div>
                  </q-btn>
                </div>

                <div class="col-4">
                  <q-btn
                    @click="confirmRestart"
                    class="power-btn power-restart full-width glossy"
                    size="md"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                    padding="xs md"
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="refresh" size="18px" class="q-mr-xs" />
                      <span class="text-caption text-weight-bold">Restart</span>
                    </div>
                  </q-btn>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Historical Charts -->
      <div class="row q-gutter-sm q-mb-md">
        <div class="col-12">
          <q-card class="glass-card glossy" flat bordered>
            <q-card-section class="q-pa-sm">
              <div class="text-subtitle2 text-weight-bold text-white q-mb-sm">
                <q-icon name="show_chart" color="white" size="18px" class="q-mr-sm" />
                Historical Usage (Last {{ systemStore.history.timestamps.length }} data points)
              </div>
              <div v-if="systemStore.history.timestamps.length > 0" class="q-pb-sm">
                <LineChart :data="systemStore.combinedChartData" :height="200" />
              </div>
              <div v-else class="text-center text-grey-4 q-py-lg">
                <q-icon name="show_chart" size="48px" color="grey-6" />
                <div class="text-caption q-mt-sm">No historical data available</div>
                <div class="text-caption text-grey-5">Enable auto-refresh or real-time mode to see charts</div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="row q-gutter-sm q-mb-md">
        <div class="col-6">
          <q-card
            clickable
            @click="goToDocker"
            class="action-card glass-card glossy cursor-pointer"
            flat
            bordered
          >
            <q-card-section class="q-pa-sm">
              <div class="row items-center">
                <div class="col">
                  <div class="text-subtitle2 text-weight-bold text-white q-mb-xs">
                    <q-icon name="view_in_ar" color="white" size="18px" class="q-mr-xs" />
                    Docker
                  </div>
                  <div class="text-caption text-grey-4">
                    {{ containers.length }} containers
                  </div>
                </div>
                <div class="col-auto">
                  <q-icon name="chevron_right" size="md" color="grey-5" class="arrow-icon" />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-6">
          <q-card
            clickable
            @click="goToProcesses"
            class="action-card glass-card glossy cursor-pointer"
            flat
            bordered
          >
            <q-card-section class="q-pa-sm">
              <div class="row items-center">
                <div class="col">
                  <div class="text-subtitle2 text-weight-bold text-white q-mb-xs">
                    <q-icon name="memory" color="white" size="18px" class="q-mr-xs" />
                    Processes
                  </div>
                  <div class="text-caption text-grey-4">
                    {{ processes.length }} processes
                  </div>
                </div>
                <div class="col-auto">
                  <q-icon name="chevron_right" size="md" color="grey-5" class="arrow-icon" />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Update Mode Toggle (Auto-Refresh / Real-Time) -->
      <div class="row q-gutter-sm">
        <div class="col-12">
          <q-card class="glass-card glossy" flat bordered>
            <q-card-section class="q-pa-sm">
              <div class="row items-center justify-between">
                <div class="row items-center">
                  <q-icon :name="systemStore.webSocketEnabled ? 'wifi' : 'autorenew'" size="20px" color="white" class="q-mr-sm" />
                  <div>
                    <div class="text-subtitle2 text-weight-bold text-white">
                      Update Mode
                    </div>
                    <div class="text-caption text-grey-4">
                      <span v-if="systemStore.webSocketEnabled" class="text-white">
                        <q-icon name="flash_on" size="12px" class="q-mr-xs" />
                        Real-time (WebSocket)
                      </span>
                      <span v-else>
                        {{ autoRefresh ? `Polling every ${refreshInterval/1000}s` : 'Manual refresh' }}
                      </span>
                    </div>
                  </div>
                </div>
                <div class="col-auto">
                  <div class="row q-gutter-xs">
                    <!-- Real-time toggle -->
                    <q-btn
                      :color="systemStore.webSocketEnabled ? 'white' : 'grey-7'"
                      :label="systemStore.webSocketEnabled ? 'Real-time' : 'Real-time'"
                      :outline="!systemStore.webSocketEnabled"
                      size="sm"
                      class="glossy"
                      @click="toggleWebSocket"
                      :loading="systemStore.webSocketState === 'connecting'"
                      padding="xs sm"
                    >
                      <q-icon name="flash_on" class="q-mr-xs" size="14px" />
                      <q-tooltip v-if="!systemStore.webSocketEnabled">Enable real-time updates via WebSocket</q-tooltip>
                      <q-tooltip v-else>Disable real-time updates</q-tooltip>
                    </q-btn>

                    <!-- Auto-refresh toggle (disabled when WebSocket is active) -->
                    <q-toggle
                      v-model="autoRefresh"
                      color="white"
                      size="sm"
                      keep-color
                      dark
                      :disable="systemStore.webSocketEnabled"
                      @update:model-value="toggleAutoRefresh"
                    >
                      <q-tooltip v-if="systemStore.webSocketEnabled">Auto-refresh is disabled in real-time mode</q-tooltip>
                    </q-toggle>
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
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from '../stores/auth';
import { useSystemStore } from '../stores/system';
import { useSettingsStore } from '../stores/settings';
import LineChart from '../components/LineChart.vue';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'DashboardPage'
});
import api from '../services/ApiService';

const router = useRouter();
const $q = useQuasar();

// Stores
const authStore = useAuthStore();
const systemStore = useSystemStore();
const settingsStore = useSettingsStore();

// State
const loading = computed(() => systemStore.loading);
const stats = computed(() => systemStore.stats);
const containers = computed(() => systemStore.containers);
const processes = computed(() => systemStore.processes);
const powerActionLoading = ref(false);
const autoRefresh = ref(false);
const refreshInterval = ref(5000);

// Computed
const serverStatusText = computed(() => {
  return systemStore.dockerAvailable ? 'Online' : 'Connected';
});

const serverStatusColor = computed(() => {
  return 'white';
});

const serverStatusIcon = computed(() => {
  return systemStore.dockerAvailable ? 'cloud_done' : 'cloud';
});

/**
 * Format bytes to human readable
 */
function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Fetch all stats
 */
async function fetchStats() {
  try {
    await systemStore.fetchStats();
  } catch (error) {
    console.error('Failed to fetch stats:', error);
  }
}

/**
 * Toggle auto-refresh
 */
function toggleAutoRefresh(value) {
  if (value) {
    systemStore.enableAutoRefresh(refreshInterval.value);
  } else {
    systemStore.disableAutoRefresh();
  }
}

/**
 * Toggle WebSocket real-time mode
 */
function toggleWebSocket() {
  if (systemStore.webSocketEnabled) {
    systemStore.disableWebSocket();
    $q.notify({
      type: 'info',
      message: 'Switched to polling mode',
      position: 'bottom',
      classes: 'notification-glossy'
    });
  } else {
    systemStore.enableWebSocket();
    $q.notify({
      type: 'positive',
      message: 'Real-time updates enabled',
      position: 'bottom',
      classes: 'notification-glossy'
    });
  }
}

/**
 * Confirm shutdown
 */
function confirmShutdown() {
  $q.dialog({
    title: 'Shutdown PC',
    message: 'Are you sure you want to shutdown the PC?',
    cancel: true,
    persistent: true,
    class: 'glass-dialog'
  }).onOk(async () => {
    await executePowerAction('shutdown');
  });
}

/**
 * Confirm hibernate
 */
function confirmHibernate() {
  $q.dialog({
    title: 'Hibernate PC',
    message: 'Are you sure you want to hibernate the PC?',
    cancel: true,
    persistent: true,
    class: 'glass-dialog'
  }).onOk(async () => {
    await executePowerAction('hibernate');
  });
}

/**
 * Confirm restart
 */
function confirmRestart() {
  $q.dialog({
    title: 'Restart PC',
    message: 'Are you sure you want to restart the PC?',
    cancel: true,
    persistent: true,
    class: 'glass-dialog'
  }).onOk(async () => {
    await executePowerAction('restart');
  });
}

/**
 * Execute power action
 */
async function executePowerAction(action) {
  powerActionLoading.value = true;

  try {
    let endpoint = '';
    switch (action) {
      case 'shutdown':
        endpoint = '/api/power/shutdown';
        break;
      case 'hibernate':
        endpoint = '/api/power/hibernate';
        break;
      case 'restart':
        endpoint = '/api/power/restart';
        break;
    }

    const result = await api.post(endpoint, {});

    $q.notify({
      type: 'positive',
      message: result.message || `${action} command sent successfully`,
      position: 'bottom',
      classes: 'notification-glossy'
    });
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || `${action} failed`,
      position: 'bottom',
      classes: 'notification-glossy'
    });
  } finally {
    powerActionLoading.value = false;
  }
}

/**
 * Handle logout
 */
async function handleLogout() {
  $q.dialog({
    title: 'Logout',
    message: 'Are you sure you want to logout?',
    cancel: true,
    persistent: true,
    class: 'glass-dialog'
  }).onOk(async () => {
    await authStore.logout();
    router.push('/login');
  });
}

/**
 * Open settings
 */
function openSettings() {
  router.push('/settings');
}

/**
 * Navigate to pages
 */
function goToDocker() {
  router.push('/docker');
}

function goToProcesses() {
  router.push('/processes');
}

/**
 * Lifecycle hooks
 */
onMounted(async () => {
  // Load settings
  settingsStore.loadSettings();
  refreshInterval.value = settingsStore.preferences.refreshInterval;

  // Initial stats fetch
  await fetchStats();

  // Fetch containers and processes
  await systemStore.fetchContainers();
  await systemStore.fetchProcesses();
});

onUnmounted(() => {
  systemStore.disableAutoRefresh();
});
</script>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  position: relative;
  background: #000000;
}

/* Glassmorphism Card - Dark Grey */
.glass-card {
  background: #1E1E1E;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  transition: all 0.3s ease;
}

.glass-card:hover {
  background: #252525;
  border-color: rgba(255, 255, 255, 0.15);
}

/* Header Section */
.header-section {
  animation: slideDown 0.4s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Status Badge */
.status-badge {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
}

/* Stat Cards */
.stat-card {
  animation: fadeInUp 0.4s ease-out backwards;
}

.stat-card:nth-child(1) { animation-delay: 0.05s; }
.stat-card:nth-child(2) { animation-delay: 0.1s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-icon {
  animation: pulse-icon 2s ease-in-out infinite;
}

@keyframes pulse-icon {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Circular Progress */
.circular-progress {
  transition: all 0.3s ease;
}

.circular-progress:hover {
  transform: scale(1.05);
}

/* Linear Progress */
.custom-progress :deep(.q-linear-progress__track) {
  background: rgba(255, 255, 255, 0.1) !important;
}

.custom-progress :deep(.q-linear-progress__fill) {
  transition: all 0.5s ease;
}

/* Power Buttons - Monochrome Gradients */
.power-btn {
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  transition: all 0.3s ease;
}

.power-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.6);
}

.power-btn:active {
  transform: translateY(-1px);
}

.power-btn:disabled {
  transform: none;
  opacity: 0.6;
}

.power-shutdown {
  background: linear-gradient(135deg, #4a4a4a 0%, #2a2a2a 100%);
}

.power-shutdown:hover {
  background: linear-gradient(135deg, #5a5a5a 0%, #3a3a3a 100%);
}

.power-hibernate {
  background: linear-gradient(135deg, #3a3a3a 0%, #1a1a1a 100%);
}

.power-hibernate:hover {
  background: linear-gradient(135deg, #4a4a4a 0%, #2a2a2a 100%);
}

.power-restart {
  background: linear-gradient(135deg, #2a2a2a 0%, #0a0a0a 100%);
}

.power-restart:hover {
  background: linear-gradient(135deg, #3a3a3a 0%, #1a1a1a 100%);
}

/* Action Cards */
.action-card {
  transition: all 0.3s ease;
}

.action-card:hover {
  background: #252525;
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateX(3px);
}

.action-card .arrow-icon {
  transition: all 0.3s ease;
}

.action-card:hover .arrow-icon {
  transform: translateX(3px);
}

/* Glass Button */
.glass-btn {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.glass-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: scale(1.05);
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
    rgba(255, 255, 255, 0.05),
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
  background: rgba(30, 30, 30, 0.95) !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Dialog Styling */
:deep(.glass-dialog) {
  backdrop-filter: blur(20px);
  background: rgba(30, 30, 30, 0.95) !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Smooth Transitions */
* {
  transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
}

/* Responsive adjustments */
@media (max-width: 575.98px) {
  .text-h3 {
    font-size: 1.5rem !important;
  }

  .text-h4 {
    font-size: 1.25rem !important;
  }

  .stat-icon {
    font-size: 20px !important;
  }

  .circular-progress :deep(.q-circular-progress) {
    width: 45px !important;
    height: 45px !important;
  }

  .power-btn {
    min-height: 40px;
  }

  .header-section .text-h4 {
    font-size: 1.25rem !important;
  }
}

@media (hover: none) and (pointer: coarse) {
  .glass-btn:hover,
  .glass-card:hover,
  .power-btn:hover,
  .action-card:hover {
    transform: none !important;
  }

  .q-btn,
  .action-card {
    min-height: 44px;
    min-width: 44px;
  }

  .arrow-icon {
    display: none;
  }
}

@media (max-width: 767.98px) and (orientation: landscape) {
  .dashboard-page {
    min-height: 100vh;
  }

  .glass-card {
    margin-bottom: 6px;
  }

  .q-pa-xl {
    padding: 12px !important;
  }
}

/* Safe Area Support */
@supports (padding: max(0px)) {
  .dashboard-page {
    padding-left: max(12px, env(safe-area-inset-left));
    padding-right: max(12px, env(safe-area-inset-right));
  }
}

@media (max-width: 767.98px) and (orientation: landscape) {
  .q-gutter-sm > .col,
  .q-gutter-sm > [class*="col-"] {
    padding: 4px;
  }
}
</style>
