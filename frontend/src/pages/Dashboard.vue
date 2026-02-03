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
  <div class="dashboard-page">
    <q-page padding class="relative-position">
      <!-- Header -->
      <div class="row q-mb-lg header-section">
        <div class="col-12">
          <div class="row items-center q-gutter-sm">
            <div class="text-h4 text-weight-bold text-white">
              <q-icon name="dashboard" class="q-mr-sm" color="primary" />
              Dashboard
            </div>
            <q-space />
            <div class="status-badge glossy q-px-md q-py-sm rounded-borders">
              <q-icon :name="serverStatusIcon" :color="serverStatusColor" size="20px" class="q-mr-xs" />
              <span class="text-subtitle2 text-white">{{ serverStatusText }}</span>
            </div>
            <q-btn
              flat
              round
              dense
              icon="settings"
              class="glass-btn"
              @click="openSettings"
            />
            <q-btn
              flat
              round
              dense
              icon="logout"
              class="glass-btn text-negative"
              @click="handleLogout"
            />
          </div>
        </div>
      </div>

      <!-- System Stats Cards -->
      <div class="row q-gutter-md q-mb-xl">
        <!-- CPU Card -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card class="stat-card glass-card glossy" flat bordered>
            <q-card-section>
              <div class="row items-center q-mb-sm">
                <q-icon name="memory" size="32px" color="cyan" class="q-mr-sm stat-icon" />
                <div class="text-subtitle2 text-blue-1">CPU Usage</div>
              </div>
              <div class="row items-center q-mt-sm">
                <div class="col">
                  <div class="text-h3 text-weight-bold text-white">
                    {{ stats.cpu?.cpu_percent?.toFixed(1) || 0 }}<span class="text-h5">%</span>
                  </div>
                </div>
                <div class="col-auto">
                  <div class="circular-progress-wrapper">
                    <q-circular-progress
                      :value="stats.cpu?.cpu_percent || 0"
                      :thickness="0.25"
                      size="70px"
                      color="cyan"
                      track-color="rgba(255,255,255,0.1)"
                      :indeterminate="loading.stats"
                      class="circular-progress"
                    />
                  </div>
                </div>
              </div>
              <div class="text-caption text-grey-4 q-mt-sm">
                <q-icon name="settings_ethernet" size="14px" class="q-mr-xs" />
                {{ stats.cpu?.cpu_count || 0 }} cores @ {{ stats.cpu?.cpu_freq_mhz?.toFixed(0) || 0 }} MHz
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Memory Card -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card class="stat-card glass-card glossy" flat bordered>
            <q-card-section>
              <div class="row items-center q-mb-sm">
                <q-icon name="storage" size="32px" color="purple" class="q-mr-sm stat-icon" />
                <div class="text-subtitle2 text-blue-1">Memory</div>
              </div>
              <div class="q-mt-sm">
                <div class="text-h3 text-weight-bold text-white">
                  {{ stats.memory?.percent?.toFixed(1) || 0 }}<span class="text-h5">%</span>
                </div>
                <div class="progress-wrapper q-mt-sm">
                  <q-linear-progress
                    :value="stats.memory?.percent || 0"
                    :thickness="8"
                    color="purple"
                    track-color="rgba(255,255,255,0.1)"
                    :indeterminate="loading.stats"
                    rounded
                    class="custom-progress"
                  />
                </div>
              </div>
              <div class="text-caption text-grey-4 q-mt-sm">
                <q-icon name="folder" size="14px" class="q-mr-xs" />
                {{ formatBytes(stats.memory?.used) }} / {{ formatBytes(stats.memory?.total) }}
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Disk Card -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card class="stat-card glass-card glossy" flat bordered>
            <q-card-section>
              <div class="row items-center q-mb-sm">
                <q-icon name="folder_open" size="32px" color="orange" class="q-mr-sm stat-icon" />
                <div class="text-subtitle2 text-blue-1">Disk</div>
              </div>
              <div class="q-mt-sm">
                <div class="text-h3 text-weight-bold text-white">
                  {{ stats.disk?.percent?.toFixed(1) || 0 }}<span class="text-h5">%</span>
                </div>
                <div class="progress-wrapper q-mt-sm">
                  <q-linear-progress
                    :value="stats.disk?.percent || 0"
                    :thickness="8"
                    color="orange"
                    track-color="rgba(255,255,255,0.1)"
                    :indeterminate="loading.stats"
                    rounded
                    class="custom-progress"
                  />
                </div>
              </div>
              <div class="text-caption text-grey-4 q-mt-sm">
                <q-icon name="hard_disk" size="14px" class="q-mr-xs" />
                {{ formatBytes(stats.disk?.used) }} / {{ formatBytes(stats.disk?.total) }}
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- GPU Card -->
        <div class="col-12 col-sm-6 col-md-3">
          <q-card class="stat-card glass-card glossy" flat bordered>
            <q-card-section>
              <div class="row items-center q-mb-sm">
                <q-icon name="videogame_asset" size="32px" color="green" class="q-mr-sm stat-icon" />
                <div class="text-subtitle2 text-blue-1">GPU</div>
              </div>
              <div class="text-h3 text-weight-bold text-white q-mt-sm">
                {{ gpuTemp || '--' }}
                <span class="text-h5 text-grey-4">°C</span>
              </div>
              <div v-if="stats.gpu?.error" class="text-caption text-warning q-mt-sm">
                <q-icon name="warning" size="14px" class="q-mr-xs" />
                {{ stats.gpu.error }}
              </div>
              <div v-else class="text-caption text-grey-4 q-mt-sm">
                <q-icon name="check_circle" size="14px" class="q-mr-xs text-positive" />
                Monitoring Active
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Power Controls -->
      <div class="row q-gutter-md q-mb-xl">
        <div class="col-12">
          <q-card class="glass-card glossy" flat bordered>
            <q-card-section>
              <div class="row items-center q-mb-md">
                <q-icon name="bolt" size="28px" color="yellow" class="q-mr-sm" />
                <div class="text-h5 text-white">Power Management</div>
              </div>
            </q-card-section>

            <q-card-section class="q-pt-none">
              <div class="row q-gutter-md">
                <div class="col-12 col-sm-4">
                  <q-btn
                    @click="confirmShutdown"
                    class="power-btn power-shutdown full-width glossy"
                    size="lg"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="power_settings_new" size="24px" class="q-mr-sm" />
                      <span class="text-subtitle1 text-weight-bold">Shutdown</span>
                    </div>
                  </q-btn>
                </div>

                <div class="col-12 col-sm-4">
                  <q-btn
                    @click="confirmHibernate"
                    class="power-btn power-hibernate full-width glossy"
                    size="lg"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="bedtime" size="24px" class="q-mr-sm" />
                      <span class="text-subtitle1 text-weight-bold">Hibernate</span>
                    </div>
                  </q-btn>
                </div>

                <div class="col-12 col-sm-4">
                  <q-btn
                    @click="confirmRestart"
                    class="power-btn power-restart full-width glossy"
                    size="lg"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="refresh" size="24px" class="q-mr-sm" />
                      <span class="text-subtitle1 text-weight-bold">Restart</span>
                    </div>
                  </q-btn>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="row q-gutter-md q-mb-xl">
        <div class="col-12 col-sm-6">
          <q-card
            clickable
            @click="goToDocker"
            class="action-card glass-card glossy cursor-pointer"
            flat
            bordered
          >
            <q-card-section>
              <div class="row items-center">
                <div class="col">
                  <div class="text-subtitle1 text-weight-bold text-white q-mb-xs">
                    <q-icon name="view_in_ar" color="primary" class="q-mr-sm" />
                    Docker Manager
                  </div>
                  <div class="text-caption text-grey-4">
                    <q-icon name="widgets" size="14px" class="q-mr-xs" />
                    {{ containers.length }} containers
                  </div>
                </div>
                <div class="col-auto">
                  <q-icon name="arrow_forward" size="lg" color="primary" class="arrow-icon" />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-12 col-sm-6">
          <q-card
            clickable
            @click="goToProcesses"
            class="action-card glass-card glossy cursor-pointer"
            flat
            bordered
          >
            <q-card-section>
              <div class="row items-center">
                <div class="col">
                  <div class="text-subtitle1 text-weight-bold text-white q-mb-xs">
                    <q-icon name="memory" color="primary" class="q-mr-sm" />
                    Process Manager
                  </div>
                  <div class="text-caption text-grey-4">
                    <q-icon name="list" size="14px" class="q-mr-xs" />
                    {{ processes.length }} processes
                  </div>
                </div>
                <div class="col-auto">
                  <q-icon name="arrow_forward" size="lg" color="primary" class="arrow-icon" />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Update Mode Toggle (Auto-Refresh / Real-Time) -->
      <div class="row q-mt-md">
        <div class="col-12">
          <q-card class="glass-card glossy" flat bordered>
            <q-card-section>
              <div class="row items-center justify-between">
                <div class="row items-center">
                  <q-icon :name="systemStore.webSocketEnabled ? 'wifi' : 'autorenew'" size="24px" :color="systemStore.isWebSocketConnected ? 'positive' : 'primary'" class="q-mr-sm" />
                  <div>
                    <div class="text-subtitle1 text-weight-bold text-white">
                      Update Mode
                    </div>
                    <div class="text-caption text-grey-4">
                      <span v-if="systemStore.webSocketEnabled" class="text-positive">
                        <q-icon name="flash_on" size="14px" class="q-mr-xs" />
                        Real-time (WebSocket)
                      </span>
                      <span v-else>
                        {{ autoRefresh ? `Polling every ${refreshInterval/1000}s` : 'Manual refresh' }}
                      </span>
                    </div>
                  </div>
                </div>
                <div class="col-auto">
                  <div class="row q-gutter-sm">
                    <!-- Real-time toggle -->
                    <q-btn
                      :color="systemStore.webSocketEnabled ? 'positive' : 'grey-7'"
                      :label="systemStore.webSocketEnabled ? 'Real-time' : 'Real-time'"
                      :outline="!systemStore.webSocketEnabled"
                      size="md"
                      class="glossy"
                      @click="toggleWebSocket"
                      :loading="systemStore.webSocketState === 'connecting'"
                    >
                      <q-icon name="flash_on" class="q-mr-xs" size="18px" />
                      <q-tooltip v-if="!systemStore.webSocketEnabled">Enable real-time updates via WebSocket</q-tooltip>
                      <q-tooltip v-else>Disable real-time updates</q-tooltip>
                    </q-btn>

                    <!-- Auto-refresh toggle (disabled when WebSocket is active) -->
                    <q-toggle
                      v-model="autoRefresh"
                      color="primary"
                      size="md"
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
  return 'positive';
});

const serverStatusIcon = computed(() => {
  return systemStore.dockerAvailable ? 'cloud_done' : 'cloud';
});

const gpuTemp = computed(() => {
  if (stats.value.gpu?.gpus && stats.value.gpu.gpus.length > 0) {
    return stats.value.gpu.gpus[0].temperature_c;
  }
  return null;
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
      position: 'top',
      classes: 'notification-glossy'
    });
  } else {
    systemStore.enableWebSocket();
    $q.notify({
      type: 'positive',
      message: 'Real-time updates enabled',
      position: 'top',
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
      position: 'top',
      classes: 'notification-glossy'
    });
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || `${action} failed`,
      position: 'top',
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
  overflow: hidden;
}

/* Glassmorphism Card */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  transition: all 0.3s ease;
}

.glass-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
}

/* Header Section */
.header-section {
  animation: slideDown 0.6s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Status Badge */
.status-badge {
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  backdrop-filter: blur(10px);
}

/* Stat Cards */
.stat-card {
  animation: fadeInUp 0.6s ease-out backwards;
}

.stat-card:nth-child(1) { animation-delay: 0.1s; }
.stat-card:nth-child(2) { animation-delay: 0.2s; }
.stat-card:nth-child(3) { animation-delay: 0.3s; }
.stat-card:nth-child(4) { animation-delay: 0.4s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
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
.circular-progress-wrapper {
  position: relative;
}

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

/* Power Buttons */
.power-btn {
  border: none;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.power-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.5);
}

.power-btn:active {
  transform: translateY(-1px);
}

.power-btn:disabled {
  transform: none;
  opacity: 0.6;
}

.power-shutdown {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.power-shutdown:hover {
  background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
}

.power-hibernate {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.power-hibernate:hover {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
}

.power-restart {
  background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
}

.power-restart:hover {
  background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
}

/* Action Cards */
.action-card {
  transition: all 0.3s ease;
}

.action-card:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(59, 130, 246, 0.4);
  transform: translateX(5px);
}

.action-card .arrow-icon {
  transition: all 0.3s ease;
}

.action-card:hover .arrow-icon {
  transform: translateX(5px);
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
    rgba(255, 255, 255, 0.1),
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

/* Dialog Styling */
:deep(.glass-dialog) {
  backdrop-filter: blur(20px);
  background: rgba(30, 30, 30, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Smooth Transitions */
* {
  transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
}

/* Responsive adjustments */
/* Extra small devices (phones, less than 576px) */
@media (max-width: 575.98px) {
  .text-h3 {
    font-size: 1.75rem !important;
  }

  .text-h4 {
    font-size: 1.5rem !important;
  }

  .text-h5 {
    font-size: 1.1rem !important;
  }

  /* Reduce icon sizes on mobile */
  .stat-icon {
    font-size: 24px !important;
  }

  /* Adjust circular progress size */
  .circular-progress-wrapper :deep(.q-circular-progress) {
    width: 50px !important;
    height: 50px !important;
  }

  /* Stack stat cards vertically */
  .stat-card {
    margin-bottom: 16px;
  }

  /* Power buttons stack */
  .power-btn {
    margin-bottom: 12px;
  }

  /* Adjust header */
  .header-section .text-h4 {
    font-size: 1.5rem !important;
  }

  /* Reduce button sizes */
  .power-btn, .action-btn {
    min-height: 44px; /* iOS touch target minimum */
  }
}

/* Small devices (landscape phones, 576px and up) */
@media (min-width: 576px) and (max-width: 767.98px) {
  .text-h3 {
    font-size: 2rem;
  }
}

/* Medium devices (tablets, 768px and up) */
@media (min-width: 768px) and (max-width: 991.98px) {
  /* Tablet adjustments */
  .glass-card {
    margin-bottom: 16px;
  }
}

/* Large devices (desktops, 992px and up) */
@media (min-width: 992px) {
  /* Desktop optimizations */
}

/* Extra large devices (large desktops, 1200px and up) */
@media (min-width: 1200px) {
  /* Extra large desktop */
}

/* Touch device optimizations */
@media (hover: none) and (pointer: coarse) {
  /* Remove hover effects on touch devices */
  .glass-btn:hover,
  .glass-card:hover,
  .power-btn:hover,
  .action-card:hover,
  .nav-item:hover {
    transform: none !important;
  }

  /* Ensure touch targets are large enough */
  .q-btn,
  .action-card,
  .nav-item {
    min-height: 44px;
    min-width: 44px;
  }

  /* Remove arrow icons on touch */
  .arrow-icon {
    display: none;
  }
}

/* Landscape mode on mobile */
@media (max-width: 767.98px) and (orientation: landscape) {
  .dashboard-page {
    min-height: 100vh;
  }

  /* Reduce vertical spacing in landscape */
  .glass-card {
    margin-bottom: 8px;
  }

  .q-pa-xl {
    padding: 16px !important;
  }
}

/* Fix for small screens with notch */
@supports (padding: max(0px)) {
  .dashboard-page {
    padding-left: max(16px, env(safe-area-inset-left));
    padding-right: max(16px, env(safe-area-inset-right));
  }
}
</style>
