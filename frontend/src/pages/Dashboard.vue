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
      <div class="row q-mb-lg header-section">
        <div class="col-12">
          <div class="row items-center q-gutter-sm">
            <div class="text-h4 text-weight-bold text-white">
              Dashboard
            </div>
            <q-space />
            <div class="status-badge q-px-sm q-py-xs rounded-borders">
              <q-icon :name="serverStatusIcon" :color="serverStatusColor" size="16px" class="q-mr-xs" />
              <span class="text-caption text-white">{{ serverStatusText }}</span>
            </div>
            <q-btn
              flat
              round
              dense
              icon="settings"
              class="header-btn"
              size="sm"
              @click="openSettings"
            />
            <q-btn
              flat
              round
              dense
              icon="logout"
              class="header-btn logout-btn"
              size="sm"
              @click="handleLogout"
            />
          </div>
        </div>
      </div>

      <!-- System Stats Cards -->
      <!-- Row 1: CPU Card (Full Width) -->
      <div class="row q-gutter-md q-mb-lg">
        <div class="col-12">
          <q-card class="stat-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center">
                <div class="col">
                  <div class="row items-center q-mb-sm">
                    <q-icon name="memory" size="24px" color="grey-5" class="q-mr-sm" />
                    <div class="text-subtitle2 text-grey-6">CPU Usage</div>
                  </div>
                  <div class="text-h2 text-weight-bold text-white">
                    {{ stats.cpu?.cpu_percent?.toFixed(1) || 0 }}<span class="text-h5 text-grey-6">%</span>
                  </div>
                  <div class="text-caption text-grey-7 q-mt-xs">
                    {{ stats.cpu?.cpu_count || 0 }} cores @ {{ stats.cpu?.cpu_freq_mhz?.toFixed(0) || 0 }} MHz
                  </div>
                </div>
                <div class="col-auto">
                  <q-circular-progress
                    :value="stats.cpu?.cpu_percent || 0"
                    :thickness="0.3"
                    size="80px"
                    color="cyan"
                    track-color="rgba(34, 211, 238, 0.1)"
                    :indeterminate="loadingWithDisks.stats"
                    class="circular-progress"
                  />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Row 2: Memory & Primary Disk -->
      <div class="row q-gutter-md q-mb-lg">
        <!-- Memory Card -->
        <div class="col-6">
          <q-card class="stat-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-sm">
                <q-icon name="storage" size="20px" color="grey-5" class="q-mr-xs" />
                <div class="text-caption text-grey-6 text-weight-bold">MEMORY</div>
              </div>
              <div class="text-h4 text-weight-bold text-white q-mb-sm">
                {{ stats.memory?.percent?.toFixed(1) || 0 }}<span class="text-caption text-grey-6">%</span>
              </div>
              <q-linear-progress
                :value="stats.memory?.percent || 0"
                :thickness="4"
                color="white"
                track-color="rgba(255,255,255,0.1)"
                :indeterminate="loading.stats"
                rounded
                class="custom-progress q-mb-sm"
              />
              <div class="text-caption text-grey-7">
                {{ formatBytes(stats.memory?.used) }} / {{ formatBytes(stats.memory?.total) }}
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Primary Disk Card -->
        <div class="col-6">
          <q-card class="stat-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-sm">
                <q-icon name="folder_open" size="20px" color="grey-5" class="q-mr-xs" />
                <div class="text-caption text-grey-6 text-weight-bold">PRIMARY DISK</div>
              </div>
              <div class="text-h4 text-weight-bold text-white q-mb-sm">
                {{ stats.disk?.percent?.toFixed(1) || 0 }}<span class="text-caption text-grey-6">%</span>
              </div>
              <q-linear-progress
                :value="stats.disk?.percent || 0"
                :thickness="4"
                color="white"
                track-color="rgba(255,255,255,0.1)"
                :indeterminate="loading.stats"
                rounded
                class="custom-progress q-mb-sm"
              />
              <div class="text-caption text-grey-7">
                {{ formatBytes(stats.disk?.used) }} / {{ formatBytes(stats.disk?.total) }}
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- All Storage Devices (USB, Partitions, etc.) -->
      <div class="row q-gutter-md q-mb-lg">
        <div class="col-12">
          <q-card class="storage-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-md">
                <q-icon name="sd_storage" size="20px" color="grey-5" class="q-mr-sm" />
                <div class="text-subtitle2 text-white">All Storage Devices</div>
                <q-space />
                <q-btn
                  flat
                  round
                  dense
                  icon="refresh"
                  size="sm"
                  class="header-btn"
                  :loading="loadingState.disks"
                  @click="refreshDisks"
                >
                  <q-tooltip>Refresh storage list</q-tooltip>
                </q-btn>
              </div>
            </q-card-section>

            <q-card-section class="q-pt-none q-pb-md q-px-md">
              <!-- Empty State -->
              <div v-if="allDisks.length === 0 && !loadingState.disks" class="text-center q-pa-xl">
                <q-icon name="search" size="48px" color="grey-8" />
                <div class="text-caption q-mt-sm">No storage devices found</div>
              </div>

              <!-- Loading State -->
              <div v-else-if="loadingState.disks" class="text-center q-pa-xl">
                <q-spinner color="grey-6" size="32px" />
                <div class="text-caption text-grey-7 q-mt-sm">Scanning for storage devices...</div>
              </div>

              <!-- Disks List -->
              <div v-else class="q-gutter-sm">
                <q-card
                  v-for="(disk, index) in allDisks"
                  :key="index"
                  :class="['disk-item', disk.is_removable ? 'removable-disk' : '']"
                  flat
                  bordered
                >
                  <q-card-section class="q-pa-sm">
                    <div class="row items-center q-mb-xs">
                      <div class="col-auto q-mr-sm">
                        <q-icon
                          :name="disk.is_removable ? 'usb' : 'hard_disk'"
                          size="20px"
                          :color="disk.is_removable ? 'cyan' : 'grey-5'"
                        />
                      </div>
                      <div class="col">
                        <div class="row items-center">
                          <div class="text-subtitle2 text-white q-mr-sm">
                            {{ getDiskName(disk) }}
                          </div>
                          <q-chip
                            v-if="disk.is_removable"
                            label="USB/External"
                            size="sm"
                            color="cyan"
                            text-color="white"
                            class="q-pa-none"
                            style="background: rgba(34, 211, 238, 0.15); border: 1px solid rgba(34, 211, 238, 0.3);"
                          />
                        </div>
                        <div class="text-caption text-grey-6">
                          {{ disk.mountpoint || disk.device }}
                        </div>
                      </div>
                      <div class="col-auto text-right">
                        <div v-if="disk.percent !== null" class="text-h6 text-weight-bold text-white">
                          {{ disk.percent }}<span class="text-caption text-grey-6">%</span>
                        </div>
                        <div v-else class="text-caption text-grey-7">
                          N/A
                        </div>
                      </div>
                    </div>

                    <!-- Progress Bar (if usage data available) -->
                    <q-linear-progress
                      v-if="disk.percent !== null"
                      :value="disk.percent"
                      :thickness="3"
                      :color="disk.is_removable ? 'cyan' : 'white'"
                      track-color="rgba(255,255,255,0.1)"
                      rounded
                      class="q-mt-xs"
                    />

                    <!-- Additional Info -->
                    <div class="row q-mt-xs">
                      <div class="col-12">
                        <div v-if="disk.total" class="text-caption text-grey-7">
                          {{ formatBytes(disk.used) }} / {{ formatBytes(disk.total) }} used
                        </div>
                        <div class="text-caption text-grey-8">
                          {{ disk.fstype }} {{ disk.opts ? `(${disk.opts})` : '' }}
                        </div>
                      </div>
                    </div>
                  </q-card-section>
                </q-card>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- System Actions - 2x2 Grid -->
      <div class="row q-gutter-md q-mb-lg">
        <div class="col-12">
          <q-card class="action-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-md">
                <q-icon name="settings_applications" size="20px" color="grey-5" class="q-mr-sm" />
                <div class="text-subtitle2 text-white">System Actions</div>
              </div>
            </q-card-section>

            <q-card-section class="q-pt-none q-pb-md q-px-md">
              <!-- 2x2 Grid - Equal Spacing -->
              <div class="row q-col-gutter-sm">
                <!-- Row 1, Col 1: Shutdown -->
                <div class="col-6">
                  <q-btn
                    @click="confirmShutdown"
                    class="power-btn-outlined full-width"
                    size="md"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                    padding="sm md"
                    outline
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="power_settings_new" size="18px" class="q-mr-xs" />
                      <span class="text-caption text-weight-bold">Shutdown</span>
                    </div>
                  </q-btn>
                </div>

                <!-- Row 1, Col 2: Restart -->
                <div class="col-6">
                  <q-btn
                    @click="confirmRestart"
                    class="power-btn-outlined full-width"
                    size="md"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                    padding="sm md"
                    outline
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="refresh" size="18px" class="q-mr-xs" />
                      <span class="text-caption text-weight-bold">Restart</span>
                    </div>
                  </q-btn>
                </div>

                <!-- Row 2, Col 1: Hibernate -->
                <div class="col-6 q-mt-sm">
                  <q-btn
                    @click="confirmHibernate"
                    class="power-btn-outlined full-width"
                    size="md"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                    padding="sm md"
                    outline
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="bedtime" size="18px" class="q-mr-xs" />
                      <span class="text-caption text-weight-bold">Hibernate</span>
                    </div>
                  </q-btn>
                </div>

                <!-- Row 2, Col 2: Lock PC -->
                <div class="col-6 q-mt-sm">
                  <q-btn
                    @click="confirmLock"
                    class="power-btn-outlined full-width"
                    size="md"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                    padding="sm md"
                    outline
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="lock" size="18px" class="q-mr-xs" />
                      <span class="text-caption text-weight-bold">Lock PC</span>
                    </div>
                  </q-btn>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Historical Charts -->
      <div class="row q-gutter-md q-mb-lg">
        <div class="col-12">
          <q-card class="chart-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="text-subtitle2 text-weight-bold text-white q-mb-sm">
                <q-icon name="show_chart" color="grey-5" size="18px" class="q-mr-sm" />
                Historical Usage
              </div>
              <div v-if="systemStore.history.timestamps.length > 0" class="q-pb-sm">
                <LineChart :data="systemStore.combinedChartData" :height="180" />
              </div>
              <div v-else class="text-center text-grey-7 q-py-xl">
                <q-icon name="show_chart" size="48px" color="grey-8" />
                <div class="text-caption q-mt-sm">No historical data available</div>
                <div class="text-caption text-grey-8">Enable auto-refresh or real-time mode to see charts</div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="row q-gutter-md q-mb-lg">
        <div class="col-6">
          <q-card
            clickable
            @click="goToDocker"
            class="action-card cursor-pointer"
            flat
            bordered
          >
            <q-card-section class="q-pa-md">
              <div class="row items-center">
                <div class="col">
                  <div class="text-subtitle2 text-weight-bold text-white q-mb-xs">
                    <q-icon name="view_in_ar" color="grey-5" size="18px" class="q-mr-xs" />
                    Docker
                  </div>
                  <div class="text-caption text-grey-6">
                    {{ containers.length }} containers
                  </div>
                </div>
                <div class="col-auto">
                  <q-icon name="chevron_right" size="md" color="grey-7" class="arrow-icon" />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <div class="col-6">
          <q-card
            clickable
            @click="goToProcesses"
            class="action-card cursor-pointer"
            flat
            bordered
          >
            <q-card-section class="q-pa-md">
              <div class="row items-center">
                <div class="col">
                  <div class="text-subtitle2 text-weight-bold text-white q-mb-xs">
                    <q-icon name="memory" color="grey-5" size="18px" class="q-mr-xs" />
                    Processes
                  </div>
                  <div class="text-caption text-grey-6">
                    {{ processes.length }} processes
                  </div>
                </div>
                <div class="col-auto">
                  <q-icon name="chevron_right" size="md" color="grey-7" class="arrow-icon" />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Update Mode Toggle -->
      <div class="row q-gutter-md">
        <div class="col-12">
          <q-card class="settings-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center justify-between">
                <div class="row items-center">
                  <q-icon :name="systemStore.webSocketEnabled ? 'wifi' : 'autorenew'" size="20px" color="grey-5" class="q-mr-sm" />
                  <div>
                    <div class="text-subtitle2 text-weight-bold text-white">
                      Update Mode
                    </div>
                    <div class="text-caption text-grey-6">
                      <span v-if="systemStore.webSocketEnabled" class="text-cyan">
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
                  <div class="row q-gutter-sm">
                    <q-btn
                      :color="systemStore.webSocketEnabled ? 'cyan' : 'grey-7'"
                      :label="systemStore.webSocketEnabled ? 'Real-time' : 'Real-time'"
                      :outline="!systemStore.webSocketEnabled"
                      size="sm"
                      @click="toggleWebSocket"
                      :loading="systemStore.webSocketState === 'connecting'"
                      padding="xs sm"
                    >
                      <q-icon name="flash_on" class="q-mr-xs" size="14px" />
                    </q-btn>

                    <q-toggle
                      v-model="autoRefresh"
                      color="cyan"
                      size="md"
                      keep-color
                      :disable="systemStore.webSocketEnabled"
                      @update:model-value="toggleAutoRefresh"
                    />
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
import api from '../services/ApiService';

// Simple logger
const logger = {
  info: (msg) => console.log(`[Dashboard] ${msg}`),
  error: (msg) => console.error(`[Dashboard] ${msg}`)
};

// Get OS platform for disk naming
const OS_PLATFORM = navigator.platform || 'unknown';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'DashboardPage'
});

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

// Multi-disk state
const allDisks = ref([]);
const diskLoading = ref(false);

// Computed loading state with disks
const loadingWithDisks = computed(() => ({
  ...loading.value,
  disks: diskLoading.value
}));

// Helper for template
const loadingState = {
  get stats() { return loading.value; },
  get disks() { return diskLoading.value; }
};

// Computed
const serverStatusText = computed(() => {
  return systemStore.dockerAvailable ? 'Online' : 'Connected';
});

const serverStatusColor = computed(() => {
  return 'cyan';
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
 * Confirm lock screen
 */
function confirmLock() {
  $q.dialog({
    title: 'Lock PC',
    message: 'Are you sure you want to lock the PC?',
    cancel: true,
    persistent: true,
    class: 'glass-dialog'
  }).onOk(async () => {
    await executePowerAction('lock');
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
      case 'lock':
        endpoint = '/api/power/lock';
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
 * Refresh all storage devices (USB, partitions, etc.)
 */
async function refreshDisks() {
  diskLoading.value = true;
  try {
    const response = await api.get('/api/stats/disks');
    if (response.disks) {
      allDisks.value = response.disks;
      logger.info(`Found ${response.disks.length} storage devices`);
    }
  } catch (error) {
    logger.error('Failed to fetch storage devices:', error);
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to scan for storage devices',
      position: 'bottom',
      classes: 'notification-glossy'
    });
  } finally {
    diskLoading.value = false;
  }
}

/**
 * Get a friendly name for a disk
 */
function getDiskName(disk) {
  if (!disk) return 'Unknown Disk';

  // For removable drives, show more descriptive name
  if (disk.is_removable) {
    if (OS_PLATFORM === 'win32') {
      // Windows: D:, E:, etc. -> "Drive D", "Drive E"
      const match = disk.device.match(/^([A-Z]):/);
      if (match) {
        return `Drive ${match[1]}`;
      }
    }
    return disk.mountpoint || disk.device || 'External Drive';
  }

  // For system drives, show mountpoint or device
  if (disk.mountpoint) {
    if (disk.mountpoint === '/') return 'Root (/)';
    if (OS_PLATFORM === 'win32') {
      // Windows: C:\ -> "System (C:)"
      const match = disk.device.match(/^([A-Z]):/);
      if (match) {
        return `System (${match[0]})`;
      }
    }
    return disk.mountpoint;
  }

  return disk.device || 'Storage';
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

  // Fetch all storage devices
  await refreshDisks();
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

/* Cards - Pure Black with Subtle Border */
.stat-card,
.power-card,
.chart-card,
.settings-card,
.action-card,
.storage-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.stat-card:hover,
.action-card:hover,
.storage-card:hover {
  border-color: #444444;
}

/* Individual Disk Items */
.disk-item {
  background: #0A0A0A;
  border: 1px solid #333333;
}

.removable-disk {
  border: 1px solid rgba(34, 211, 238, 0.2);
  background: rgba(34, 211, 238, 0.02);
}

/* Header Section */
.header-section {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Status Badge */
.status-badge {
  background: var(--q-dark-page);
  border: 1px solid var(--q-separator);
}

.body--light .status-badge {
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
}

/* Header Buttons */
.header-btn {
  color: #FFFFFF;
  background: transparent;
  border: 1px solid #333333;
  border-radius: 8px;
}

.logout-btn {
  color: #ef4444;
}

/* Circular Progress */
.circular-progress {
  transition: all 0.2s ease;
}

.circular-progress:hover {
  transform: scale(1.05);
}

/* Linear Progress */
.custom-progress :deep(.q-linear-progress__track) {
  background: rgba(255, 255, 255, 0.1) !important;
}

.custom-progress :deep(.q-linear-progress__fill) {
  transition: all 0.3s ease;
}

/* Power Buttons - Outlined Style */
.power-btn-outlined {
  background: transparent !important;
  color: #FFFFFF !important;
  border: 1px solid #FFFFFF !important;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.power-btn-outlined:hover {
  background: #FFFFFF !important;
  color: #000000 !important;
}

.power-btn-outlined:active {
  background: #FFFFFF !important;
  color: #000000 !important;
  transform: scale(0.98);
}

.power-btn-outlined:disabled {
  border-color: #333333 !important;
  color: #666666 !important;
  background: transparent !important;
}

/* Action Cards */
.action-card:hover {
  border-color: rgba(34, 211, 238, 0.3);
}

.action-card .arrow-icon {
  transition: all 0.2s ease;
}

.action-card:hover .arrow-icon {
  transform: translateX(3px);
  color: #22d3ee;
}

/* Notification Styling */
:deep(.notification-glossy) {
  background: #0A0A0A !important;
  border: 1px solid #333333;
  color: #FFFFFF;
}

/* Dialog Styling */
:deep(.glass-dialog) {
  background: #0A0A0A !important;
  border: 1px solid #333333;
  color: #FFFFFF;
}

/* Cyan Accent Color Helper */
.text-cyan {
  color: #22d3ee;
}

/* Responsive adjustments */
@media (max-width: 575.98px) {
  .text-h2 {
    font-size: 1.75rem !important;
  }

  .text-h4 {
    font-size: 1.15rem !important;
  }

  .power-btn-outlined {
    min-height: 40px;
  }
}

@media (hover: none) and (pointer: coarse) {
  .stat-card:hover,
  .action-card:hover,
  .power-btn-outlined:hover {
    transform: none !important;
  }

  .power-btn-outlined {
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
}
</style>
