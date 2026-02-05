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
    <q-page padding class="q-pl-none q-pr-md">
      <!-- Encryption Key Warning Banner -->
      <q-banner v-if="showKeyWarning" class="key-warning-banner q-mb-md" dense rounded>
        <template v-slot:avatar>
          <q-icon name="warning" color="orange" />
        </template>
        <div class="text-body2">
          <span class="text-orange">⚠️ Data may be encrypted.</span>
          Configure your Encryption Key in Settings to decrypt all data.
          <q-btn flat color="orange" label="Go to Settings" size="sm" class="q-ml-sm" @click="router.push('/settings')" />
        </div>
      </q-banner>

      <!-- System Stats Cards - CENTERED -->
      <div class="stats-container">
        <!-- Row 1: CPU Card (Full Width) -->
        <div class="row q-col-gutter-md q-mb-lg">
          <div class="col-12">
            <q-card class="stat-card" flat bordered>
              <q-card-section class="q-pa-md">
                <div class="row items-center">
                  <div class="col">
                    <div class="row items-center q-mb-sm">
                      <q-icon name="developer_board" size="24px" color="grey-5" class="q-mr-sm" />
                      <div class="text-subtitle2 text-grey-6">CPU Usage</div>
                    </div>
                  <div class="text-h2 text-weight-bold text-white">
                    {{ stats.cpu?.cpu_percent?.toFixed(1) || 0 }}<span class="text-h5 text-grey-6">%</span>
                  </div>
                  <div class="text-caption text-grey-7 q-mt-sm">
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
                    class="circular-progress"
                  />
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Row 2: 2x2 Grid Stats (Memory, GPU, Disk, Temperature) -->
      <div class="row q-col-gutter-md q-mb-lg stats-row equal-height-row">
        <!-- Memory Card -->
        <div class="col-6">
          <q-card class="stat-card stat-card-equal" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-sm">
                <q-icon name="dns" size="20px" color="grey-5" class="q-mr-xs" />
                <div class="text-caption text-grey-6 text-weight-bold">MEMORY</div>
              </div>
              <div class="text-h4 text-weight-bold text-white q-mb-sm">
                {{ stats.memory?.percent?.toFixed(1) || 0 }}<span class="text-caption text-grey-6">%</span>
              </div>
              <q-linear-progress
                :value="stats.memory?.percent / 100 || 0"
                :thickness="6"
                color="cyan"
                track-color="grey-8"
                rounded
                animation-speed="500"
                class="q-mb-sm"
              />
              <div class="text-caption text-grey-7">
                {{ formatBytes(stats.memory?.used) }} / {{ formatBytes(stats.memory?.total) }}
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- GPU Usage Card -->
        <div class="col-6">
          <q-card class="stat-card stat-card-equal" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-sm">
                <q-icon name="videogame_asset" size="20px" color="grey-5" class="q-mr-xs" />
                <div class="text-caption text-grey-6 text-weight-bold">GPU USAGE</div>
              </div>
              <div class="text-h4 text-weight-bold text-white q-mb-sm">
                <template v-if="stats.gpu">
                  {{ stats.gpu?.usage_percent?.toFixed(1) || 0 }}<span class="text-caption text-grey-6">%</span>
                </template>
                <template v-else>
                  <span class="text-h5 text-grey-6">N/A</span>
                </template>
              </div>
              <q-linear-progress
                v-if="stats.gpu"
                :value="stats.gpu?.usage_percent / 100 || 0"
                :thickness="6"
                color="cyan"
                track-color="grey-8"
                rounded
                animation-speed="500"
                class="q-mb-sm"
              />
              <q-linear-progress
                v-else
                :value="0"
                :thickness="6"
                color="grey-7"
                track-color="grey-8"
                rounded
                class="q-mb-sm"
              />
              <div class="text-caption text-grey-7">
                {{ stats.gpu?.name || 'N/A' }}
                <template v-if="stats.gpu?.temperature">
                  <span class="text-grey-6 q-ml-xs">· {{ stats.gpu.temperature.toFixed(0) }}°C</span>
                </template>
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Primary Disk Card -->
        <div class="col-6">
          <q-card class="stat-card stat-card-equal" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-sm">
                <q-icon name="storage" size="20px" color="grey-5" class="q-mr-xs" />
                <div class="text-caption text-grey-6 text-weight-bold">PRIMARY DISK</div>
              </div>
              <div class="text-h4 text-weight-bold text-white q-mb-sm">
                {{ stats.disk?.percent?.toFixed(1) || 0 }}<span class="text-caption text-grey-6">%</span>
              </div>
              <q-linear-progress
                :value="stats.disk?.percent / 100 || 0"
                :thickness="6"
                color="cyan"
                track-color="grey-8"
                rounded
                animation-speed="500"
                class="q-mb-sm"
              />
              <div class="text-caption text-grey-7">
                {{ formatBytes(stats.disk?.used) }} / {{ formatBytes(stats.disk?.total) }}
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Temperature Card -->
        <div class="col-6">
          <q-card class="stat-card stat-card-equal" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-sm">
                <q-icon name="thermostat" size="20px" color="grey-5" class="q-mr-xs" />
                <div class="text-caption text-grey-6 text-weight-bold">TEMPERATURE</div>
              </div>
              <div class="row items-center justify-between">
                <div class="text-h4 text-weight-bold text-white q-mb-sm">
                  {{ stats.cpu?.temperature?.toFixed(0) || stats.temperature?.toFixed(0) || 'N/A' }}
                  <span class="text-caption text-grey-6">°C</span>
                </div>
                <q-icon
                  :name="getTemperatureIcon(stats.cpu?.temperature || stats.temperature)"
                  :color="getTemperatureColor(stats.cpu?.temperature || stats.temperature)"
                  size="32px"
                />
              </div>
              <div class="text-caption text-grey-7 q-mt-sm">
                CPU Temperature
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
      </div>

      <!-- All Storage Devices (USB, Partitions, etc.) -->
      <div class="row q-col-gutter-md q-mb-sm">
        <div class="col-12">
          <q-card class="storage-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-md">
                <q-icon name="storage" size="20px" color="grey-5" class="q-mr-sm" />
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
                          :name="disk.drive_type === 'External' || disk.is_removable ? 'usb' : 'folder_open'"
                          size="24px"
                          :class="disk.drive_type === 'External' || disk.is_removable ? 'text-cyan' : 'text-grey-5'"
                          style="display: flex; opacity: 1; visibility: visible;"
                        />
                      </div>
                      <div class="col">
                        <div class="row items-center">
                          <div class="text-subtitle2 text-white q-mr-sm">
                            {{ getDiskName(disk) }}
                          </div>
                          <q-chip
                            v-if="disk.drive_type === 'External' || disk.is_removable"
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
                      :value="disk.percent / 100"
                      :thickness="6"
                      color="cyan"
                      track-color="grey-8"
                      rounded
                      animation-speed="500"
                      class="q-mt-sm"
                    />

                    <!-- Additional Info -->
                    <div class="row q-mt-xs">
                      <div class="col-12">
                        <div v-if="disk.total" class="text-caption text-grey-7">
                          {{ formatBytes(disk.used) }} / {{ formatBytes(disk.total) }} used
                        </div>
                        <div class="text-caption text-grey-8">
                          {{ disk.fstype }}{{ disk.drive_type ? ` (${disk.drive_type})` : '' }}
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

      <!-- System Actions - 2x2 Grid - CRITICAL: Ensure clickable -->
      <div class="row q-col-gutter-md q-mb-sm">
        <div class="col-12">
          <q-card class="action-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-md">
                <q-icon name="settings_applications" size="20px" color="grey-5" class="q-mr-sm" />
                <div class="text-subtitle2 text-white">System Actions</div>
              </div>
            </q-card-section>

            <q-card-section class="q-pt-none q-pb-md q-px-md">
              <!-- 4 Buttons - 2x2 Grid -->
              <div class="row q-col-gutter-sm">
                <!-- Row 1: Shutdown, Restart -->
                <div class="col-6">
                  <q-btn
                    @click.stop="confirmShutdown"
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

                <div class="col-6">
                  <q-btn
                    @click.stop="confirmRestart"
                    class="power-btn-outlined full-width"
                    size="md"
                    :loading="powerActionLoading"
                    :disable="powerActionLoading"
                    padding="sm md"
                    outline
                  >
                    <div class="row items-center justify-center no-wrap">
                      <q-icon name="restart_alt" size="18px" class="q-mr-xs" />
                      <span class="text-caption text-weight-bold">Restart</span>
                    </div>
                  </q-btn>
                </div>

                <!-- Row 2: Hibernate, Lock PC -->
                <div class="col-6 q-mt-sm">
                  <q-btn
                    @click.stop="confirmHibernate"
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

                <div class="col-6 q-mt-sm">
                  <q-btn
                    @click.stop="confirmLock"
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

        <!-- Media Control Card -->
        <div class="col-12">
          <q-card class="action-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center q-mb-md">
                <q-icon name="play_circle" size="20px" color="grey-5" class="q-mr-sm" />
                <div class="text-subtitle2 text-white">Media Control</div>
              </div>
            </q-card-section>

            <q-card-section class="q-pt-none q-pb-md q-px-md">
              <!-- App Selector -->
              <div class="q-mb-md">
                <q-select
                  v-model="selectedMediaApp"
                  :options="mediaApps"
                  label="Target Application"
                  outlined
                  dark
                  dense
                  color="cyan"
                  emit-value
                  map-options
                  @update:model-value="refreshMediaApps"
                  :loading="mediaAppsLoading"
                  class="media-selector"
                >
                  <template v-slot:prepend>
                    <q-icon name="apps" color="grey-5" size="16px" />
                  </template>
                  <template v-slot:append>
                    <q-icon
                      name="refresh"
                      color="grey-5"
                      size="16px"
                      class="cursor-pointer"
                      @click.stop="refreshMediaApps"
                    />
                  </template>
                </q-select>
              </div>

              <!-- Playback Controls -->
              <div class="row q-col-gutter-sm q-mb-md">
                <div class="col-4">
                  <q-btn
                    @click="sendMediaCommand('prev')"
                    class="media-btn full-width"
                    size="md"
                    padding="sm md"
                    outline
                  >
                    <q-icon name="skip_previous" size="24px" />
                  </q-btn>
                </div>

                <div class="col-4">
                  <q-btn
                    @click="sendMediaCommand('playpause')"
                    class="media-btn full-width"
                    size="md"
                    padding="sm md"
                    :loading="mediaCommandLoading"
                    :disable="mediaCommandLoading"
                    outline
                  >
                    <q-icon name="play_circle" size="24px" />
                  </q-btn>
                </div>

                <div class="col-4">
                  <q-btn
                    @click="sendMediaCommand('next')"
                    class="media-btn full-width"
                    size="md"
                    padding="sm md"
                    outline
                  >
                    <q-icon name="skip_next" size="24px" />
                  </q-btn>
                </div>
              </div>

              <!-- Volume Controls -->
              <div class="row q-col-gutter-sm">
                <div class="col-4">
                  <q-btn
                    @click="sendMediaCommand('volumedown')"
                    class="media-btn full-width"
                    size="sm"
                    padding="xs"
                    outline
                  >
                    <q-icon name="volume_down" size="20px" />
                  </q-btn>
                </div>

                <div class="col-4">
                  <q-btn
                    @click="sendMediaCommand('volumemute')"
                    class="media-btn full-width"
                    size="sm"
                    padding="xs"
                    outline
                  >
                    <q-icon name="volume_off" size="20px" />
                  </q-btn>
                </div>

                <div class="col-4">
                  <q-btn
                    @click="sendMediaCommand('volumeup')"
                    class="media-btn full-width"
                    size="sm"
                    padding="xs"
                    outline
                  >
                    <q-icon name="volume_up" size="20px" />
                  </q-btn>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Historical Charts -->
      <div class="row q-col-gutter-md q-mb-sm">
        <div class="col-12">
          <q-card class="chart-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="text-subtitle2 text-weight-bold text-white q-mb-sm">
                <q-icon name="show_chart" color="grey-5" size="18px" class="q-mr-sm" />
                Historical Usage
              </div>
              <div v-if="hasHistoryData" class="q-pb-sm">
                <LineChart
                  :data="chartData"
                  :options="chartOptions"
                  :height="200"
                />
              </div>
              <div v-else class="text-center q-pa-lg">
                <q-spinner color="grey-6" size="24px" />
                <div class="text-caption text-grey-7 q-mt-sm">Loading historical data...</div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="row q-col-gutter-md q-mb-lg actions-row items-stretch">
        <!-- Docker Card -->
        <div class="col-6">
          <q-card
            clickable
            @click="goToDocker"
            class="action-mini-card full-height full-width"
            flat
            bordered
          >
            <q-card-section class="q-pa-md">
              <div class="text-subtitle2 text-weight-bold text-white q-mb-sm">
                <q-icon name="inventory_2" color="cyan" size="24px" class="q-mr-xs" />
                Docker
              </div>
              <div class="text-caption text-grey-6 q-mb-sm">
                Manage containers
              </div>
              <q-separator class="q-my-sm bg-grey-8" />
              <div class="text-caption text-cyan">
                View & Control →
              </div>
            </q-card-section>
          </q-card>
        </div>

        <!-- Processes Card -->
        <div class="col-6">
          <q-card
            clickable
            @click="goToProcesses"
            class="action-mini-card full-height full-width"
            flat
            bordered
          >
            <q-card-section class="q-pa-md">
              <div class="text-subtitle2 text-weight-bold text-white q-mb-sm">
                <q-icon name="memory" color="cyan" size="24px" class="q-mr-xs" />
                Processes
              </div>
              <div class="text-caption text-grey-6 q-mb-sm">
                View running processes
              </div>
              <q-separator class="q-my-sm bg-grey-8" />
              <div class="text-caption text-cyan">
                Monitor & Manage →
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </q-page>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { storeToRefs } from 'pinia';
import { useSystemStore } from '../stores/system';
import { useSettingsStore } from '../stores/settings';
import LineChart from '../components/LineChart.vue';
import api from '../services/ApiService';
import { secureNotify } from '../services/NotifyService';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'DashboardPage'
});

const router = useRouter();
const $q = useQuasar();
const systemStore = useSystemStore();
const settingsStore = useSettingsStore();

// Use storeToRefs for reactive store properties (best practice per Pinia docs)
const { stats, history, loading } = storeToRefs(systemStore);

// Check if encryption key is missing
const hasEncryptionKey = computed(() => settingsStore.hasEncryptionKey);

// Show warning banner if encryption key is missing
const showKeyWarning = computed(() => !hasEncryptionKey.value);

// State
const powerActionLoading = ref(false);
const autoRefresh = ref(false);
const refreshInterval = ref(5000); // 5 seconds
let refreshTimer = null;

// Media Control State
const mediaApps = ref(['Default (Global)']);
const selectedMediaApp = ref('Default (Global)');
const mediaAppsLoading = ref(false);
const mediaCommandLoading = ref(false);

// Multi-disk state
const allDisks = ref([]);
const diskLoading = ref(false);

// Computed
const loadingState = computed(() => ({
  stats: loading.value.stats,
  disks: diskLoading.value
}));

// Computed for history timestamps check
const hasHistoryData = computed(() => history.value.timestamps.length > 0);

// Chart data
const chartData = computed(() => {
  // CRITICAL: Use shallow copies to prevent infinite recursion with Chart.js
  return {
    labels: [...history.value.timestamps].map(t => {
      const date = new Date(t);
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }),
    datasets: [
      {
        label: 'CPU %',
        data: [...history.value.cpu], // Shallow copy prevents reactivity loop
        borderColor: 'rgb(34, 211, 238)',
        backgroundColor: 'rgba(34, 211, 238, 0.1)',
        tension: 0.4
      },
      {
        label: 'Memory %',
        data: [...history.value.memory], // Shallow copy prevents reactivity loop
        borderColor: 'rgb(168, 85, 247)',
        backgroundColor: 'rgba(168, 85, 247, 0.1)',
        tension: 0.4
      }
    ]
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#9ca3af',
        font: { size: 11 },
        usePointStyle: true,
        pointStyle: 'circle',
        boxWidth: 12,
        boxHeight: 12,
        padding: 20
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 100,
      ticks: { color: '#6b7280', font: { size: 10 } },
      grid: { color: 'rgba(255,255,255,0.05)' }
    },
    x: {
      display: false
    }
  }
}));

/**
 * Format bytes to human readable
 * Uses base-1024 (GiB) to match Windows File Explorer
 */
function formatBytes(bytes) {
  if (!bytes || bytes < 0 || isNaN(bytes)) return '0 B';
  const k = 1024;  // Use base-1024 (GiB binary) to match Windows
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Get temperature icon based on value
 */
function getTemperatureIcon(temp) {
  if (!temp) return 'thermostat';
  if (temp >= 80) return 'warning';
  if (temp >= 60) return 'whatshot';
  return 'ac_unit';
}

/**
 * Get temperature color based on value
 */
function getTemperatureColor(temp) {
  if (!temp) return 'grey-5';
  if (temp >= 80) return 'red';
  if (temp >= 60) return 'orange';
  if (temp >= 40) return 'yellow';
  return 'cyan';
}

/**
 * Get disk name
 */
function getDiskName(disk) {
  if (!disk) return 'Unknown Disk';

  // For removable drives, show more descriptive name
  if (disk.is_removable) {
    if (disk.device && disk.device.includes('/') || disk.device && disk.device.includes(':')) {
      if (disk.device.match(/^([A-Z]):/)) {
        const match = disk.device.match(/^([A-Z]):/);
        if (match) return `Drive ${match[1]}`;
      }
      return disk.mountpoint || disk.device || 'External Drive';
    }
    return disk.mountpoint || disk.device || 'External Drive';
  }

  // For system drives, show mountpoint or device
  if (disk.mountpoint) {
    if (disk.mountpoint === '/') return 'Root (/)';
    if (disk.device && disk.device.match(/^([A-Z]):/)) {
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
 * Fetch all stats
 */
async function refreshStats() {
  try {
    await systemStore.fetchStats();
  } catch (error) {
    console.error('[Dashboard] Error fetching stats:', error);
  }
}

/**
 * Refresh disks list
 */
async function refreshDisks() {
  diskLoading.value = true;
  try {
    const response = await api.get('/api/stats/disks');
    if (response.disks) {
      allDisks.value = response.disks;
      console.log(`[Dashboard] Found ${response.disks.length} storage devices`);
    }
  } catch (error) {
    console.error('[Dashboard] Error refreshing disks:', error);
    secureNotify.error($q, error.message || 'Failed to scan for storage devices');
  } finally {
    diskLoading.value = false;
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
    let payload = {};

    switch (action) {
      case 'shutdown':
        endpoint = '/api/power/shutdown';
        payload = { delay_seconds: 0 };
        break;
      case 'hibernate':
        endpoint = '/api/power/hibernate';
        break;
      case 'restart':
        endpoint = '/api/power/restart';
        payload = { delay_seconds: 0 };
        break;
      case 'lock':
        endpoint = '/api/power/lock';
        break;
      default:
        throw new Error(`Unknown action: ${action}`);
    }

    const result = await api.post(endpoint, payload);

    secureNotify.success($q, result.message || `${action} command sent successfully`);
  } catch (error) {
    console.error('[Dashboard] Power action error:', error);
    secureNotify.error($q, error.response?.data?.message || error.message || `${action} failed`);
  } finally {
    powerActionLoading.value = false;
  }
}

/**
 * =============================================================
 * MEDIA CONTROL FUNCTIONS
 * =============================================================
 */

/**
 * Get available media apps from backend
 */
async function refreshMediaApps() {
  mediaAppsLoading.value = true;

  try {
    const result = await api.get('/api/media/apps');

    if (result.success && result.apps) {
      mediaApps.value = result.apps;

      // Ensure selected app is still valid
      if (!result.apps.includes(selectedMediaApp.value)) {
        selectedMediaApp.value = 'Default (Global)';
      }
    }
  } catch (error) {
    console.error('[Dashboard] Failed to load media apps:', error);
    secureNotify.error($q, 'Failed to load media applications');
  } finally {
    mediaAppsLoading.value = false;
  }
}

/**
 * Send media command to selected app
 */
async function sendMediaCommand(action) {
  if (mediaCommandLoading.value) {
    return;
  }

  mediaCommandLoading.value = true;

  try {
    const result = await api.post('/api/media/control', {
      app: selectedMediaApp.value,
      action: action
    });

    if (result.success) {
      // Provide haptic feedback on mobile
      if (navigator.vibrate) {
        navigator.vibrate(50); // Short vibration
      }

      secureNotify.success($q, result.message || `${action} sent successfully`);
    } else {
      secureNotify.error($q, result.message || 'Failed to send command');
    }
  } catch (error) {
    console.error('[Dashboard] Media control error:', error);
    secureNotify.error($q, error.response?.data?.message || error.message || 'Failed to send media command');
  } finally {
    mediaCommandLoading.value = false;
  }
}

/**
 * Navigation
 */
function goToDocker() {
  router.push('/docker');
}

function goToProcesses() {
  router.push('/processes');
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(() => {
    if (!document.hidden) {
      refreshStats();
    }
  }, refreshInterval.value);
  autoRefresh.value = true;
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
  autoRefresh.value = false;
}

/**
 * Handle visibility change - properly stored for cleanup
 */
function handleVisibilityChange() {
  if (document.hidden) {
    stopAutoRefresh();
  } else {
    startAutoRefresh();
  }
}

/**
 * Watch for threshold alerts
 */
watch(() => systemStore._lastAlert, (alert) => {
  if (alert && !document.hidden) {
    secureNotify.warning(
      $q,
      `${alert.metric} is at ${alert.value}% (Threshold: ${alert.threshold}%)`,
      `Threshold exceeded for ${alert.metric}`
    );
  }
}, { deep: true });

/**
 * Lifecycle
 */
onMounted(async () => {
  await refreshStats();
  await refreshDisks();

  // Load threshold configuration
  await systemStore.loadThresholdConfig();

  // Load media apps
  await refreshMediaApps();

  // Start auto-refresh
  startAutoRefresh();

  // Listen for visibility changes - using named function for proper cleanup
  document.addEventListener('visibilitychange', handleVisibilityChange);
});

onUnmounted(() => {
  stopAutoRefresh();
  // CRITICAL: Use same function reference to properly remove event listener
  document.removeEventListener('visibilitychange', handleVisibilityChange);
});
</script>

<style scoped>
/* Simplified Dashboard - Fix Ghost Overlay Issue */
.dashboard-page {
  min-height: 100vh;
  position: relative;
  background: #000000;
}

.stats-container {
  width: 100%;
  position: relative;
}

/* Encryption Key Warning Banner */
.key-warning-banner {
  background: rgba(255, 152, 0, 0.1) !important;
  border: 1px solid rgba(255, 152, 0, 0.3) !important;
  color: #FFFFFF !important;
}

.key-warning-banner .text-body2 {
  color: #FFFFFF;
}

/* Header buttons */
.header-menu-btn {
  position: relative !important;
  pointer-events: auto !important;
  color: #FFFFFF;
  background: rgba(10, 10, 10, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.header-menu-btn:hover {
  background: rgba(30, 30, 30, 0.9);
}

/* Status Badge - NOT clickable */
.status-badge {
  background: rgba(10, 10, 10, 0.8);
  border: 1px solid #333333;
  pointer-events: none !important;
}

.status-badge > * {
  pointer-events: none !important;
}

/* Cards - Pure Black with Subtle Border */
.stat-card,
.power-card,
.chart-card,
.settings-card,
.action-card,
.storage-card,
.action-mini-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.stat-card:hover,
.action-card:hover,
.storage-card:hover,
.action-mini-card:hover {
  border-color: #444444;
}

/* Individual Disk Items */
.disk-item {
  background: #0A0A0A;
  border: 1px solid #333333;
}

/* Ensure disk icons are visible */
.disk-item .q-icon {
  display: flex !important;
  opacity: 1 !important;
  visibility: visible !important;
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

/* Header Buttons */
.header-btn {
  color: #FFFFFF;
  background: transparent;
  border: 1px solid #333333;
  border-radius: 8px;
}

/* Circular Progress */
.circular-progress {
  transition: all 0.2s ease;
  pointer-events: none !important;
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

.custom-progress {
  pointer-events: none !important;
}

/* Power Buttons - Outlined Style */
.power-btn-outlined {
  background: transparent !important;
  color: #FFFFFF !important;
  border: 1px solid #FFFFFF !important;
  border-radius: 8px;
  transition: all 0.2s ease;
  position: relative;
  z-index: 1;
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

/* Media Control Buttons */
.media-btn {
  background: transparent !important;
  color: #FFFFFF !important;
  border: 1px solid #333333 !important;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.media-btn:hover {
  background: rgba(34, 211, 238, 0.1) !important;
  border-color: #22d3ee !important;
  color: #22d3ee !important;
}

.media-btn:active {
  transform: scale(0.95);
}

.media-selector {
  border-color: #333333 !important;
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
  color: #FFFFFF !important;
  z-index: 7000 !important;
}

/* Dialog title and message - ensure white text */
:deep(.glass-dialog .q-dialog__title) {
  color: #FFFFFF !important;
}

:deep(.glass-dialog .q-dialog__message) {
  color: #FFFFFF !important;
}

/* Cyan Accent Color Helper */
.text-cyan {
  color: #22d3ee;
}

/* Stats Row - Equal height cards */
.stats-row {
  align-items: stretch;
}

/* CRITICAL: Equal height grid - force all 4 cards to same height */
.equal-height-row {
  display: flex;
  flex-wrap: wrap;
}

.equal-height-row .col-6 {
  display: flex;
  flex-direction: column;
}

.stat-card-equal {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 140px;
  justify-content: space-between;
}

.stat-card-equal .q-card-section {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}

.stats-row .col-6 {
  display: flex;
}

/* Actions Row - Equal height cards */
.actions-row {
  align-items: stretch;
}

.actions-row .col-6 {
  display: flex;
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
  .power-btn-outlined:hover,
  .action-mini-card:hover {
    transform: none !important;
  }

  .power-btn-outlined {
    min-height: 44px;
    min-width: 44px;
  }
}

@media (max-width: 767.98px) and (orientation: landscape) {
  .dashboard-page {
    min-height: 100vh;
  }
}

/* CRITICAL: Simplified clickable elements */
.dashboard-page .q-btn {
  position: relative !important;
  pointer-events: auto !important;
}

.dashboard-page .q-card {
  position: relative !important;
}
</style>
