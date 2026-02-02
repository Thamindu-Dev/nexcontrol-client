<template>
  <q-page padding>
    <!-- Header -->
    <div class="row q-mb-md">
      <div class="col-12">
        <div class="row items-center q-gutter-sm">
          <div class="text-h5">NexControl Dashboard</div>
          <q-space />
          <q-badge :color="serverStatusColor" rounded>
            {{ serverStatusText }}
          </q-badge>
          <q-btn flat round dense icon="settings" @click="openSettings" />
          <q-btn flat round dense icon="logout" @click="handleLogout" />
        </div>
      </div>
    </div>

    <!-- System Stats Cards -->
    <div class="row q-gutter-md q-mb-lg">
      <!-- CPU Card -->
      <div class="col-12 col-sm-6 col-md-3">
        <q-card>
          <q-card-section>
            <div class="text-subtitle2 text-grey-7">CPU Usage</div>
          <div class="row items-center q-mt-sm">
              <div class="col">
                <div class="text-h4">{{ stats.cpu?.cpu_percent?.toFixed(1) || 0 }}%</div>
              </div>
              <div class="col-auto">
                <q-circular-progress
                  :value="stats.cpu?.cpu_percent || 0"
                  :thickness="0.2"
                  size="60px"
                  color="primary"
                  :indeterminate="loading.stats"
                />
              </div>
            </div>
            <div class="text-caption text-grey">
              {{ stats.cpu?.cpu_count || 0 }} cores @ {{ stats.cpu?.cpu_freq_mhz?.toFixed(0) || 0 }} MHz
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Memory Card -->
      <div class="col-12 col-sm-6 col-md-3">
        <q-card>
          <q-card-section>
            <div class="text-subtitle2 text-grey-7">Memory Usage</div>
            <div class="q-mt-sm">
              <div class="text-h4">{{ stats.memory?.percent?.toFixed(1) || 0 }}%</div>
              <q-linear-progress
                :value="stats.memory?.percent || 0"
                :thickness="0.2"
                color="info"
                :indeterminate="loading.stats"
              />
            </div>
            <div class="text-caption text-grey q-mt-sm">
              {{ formatBytes(stats.memory?.used) }} / {{ formatBytes(stats.memory?.total) }}
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Disk Card -->
      <div class="col-12 col-sm-6 col-md-3">
        <q-card>
          <q-card-section>
            <div class="text-subtitle2 text-grey-7">Disk Usage</div>
            <div class="q-mt-sm">
              <div class="text-h4">{{ stats.disk?.percent?.toFixed(1) || 0 }}%</div>
              <q-linear-progress
                :value="stats.disk?.percent || 0"
                :thickness="0.2"
                color="warning"
                :indeterminate="loading.stats"
              />
            </div>
            <div class="text-caption text-grey q-mt-sm">
              {{ formatBytes(stats.disk?.used) }} / {{ formatBytes(stats.disk?.total) }}
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- GPU Card -->
      <div class="col-12 col-sm-6 col-md-3">
        <q-card>
          <q-card-section>
            <div class="text-subtitle2 text-grey-7">GPU Temperature</div>
            <div class="text-h4 q-mt-sm">
              {{ gpuTemp || 'N/A' }}
              <span class="text-caption text-grey">°C</span>
            </div>
            <div v-if="stats.gpu?.error" class="text-caption text-warning q-mt-sm">
              {{ stats.gpu.error }}
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Power Controls -->
    <div class="row q-gutter-md q-mb-lg">
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Power Management</div>
          </q-card-section>

          <q-card-section class="q-pt-none">
            <div class="row q-gutter-md">
              <div class="col-12 col-sm-4">
                <q-btn
                  @click="confirmShutdown"
                  color="red"
                  class="full-width"
                  size="lg"
                  :loading="powerActionLoading"
                >
                  <q-icon name="power_settings_new" class="q-mr-sm" />
                  Shutdown
                </q-btn>
              </div>

              <div class="col-12 col-sm-4">
                <q-btn
                  @click="confirmHibernate"
                  color="orange"
                  class="full-width"
                  size="lg"
                  :loading="powerActionLoading"
                >
                  <q-icon name="bedtime" class="q-mr-sm" />
                  Hibernate
                </q-btn>
              </div>

              <div class="col-12 col-sm-4">
                <q-btn
                  @click="confirmRestart"
                  color="yellow"
                  class="full-width"
                  size="lg"
                  text-color="black"
                  :loading="powerActionLoading"
                >
                  <q-icon name="refresh" class="q-mr-sm" />
                  Restart
                </q-btn>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="row q-gutter-md">
      <div class="col-12 col-sm-6">
        <q-card
          clickable
          @click="goToDocker"
          class="cursor-pointer"
        >
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-subtitle1">Docker Manager</div>
                <div class="text-caption text-grey">
                  {{ containers.length }} containers
                </div>
              </div>
              <div class="col-auto">
                <q-icon name="view_in_ar" size="lg" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6">
        <q-card
          clickable
          @click="goToProcesses"
          class="cursor-pointer"
        >
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-subtitle1">Process Manager</div>
                <div class="text-caption text-grey">
                  {{ processes.length }} processes
                </div>
              </div>
              <div class="col-auto">
                <q-icon name="memory" size="lg" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Auto-Refresh Toggle -->
    <div class="row q-mt-md">
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-subtitle2">Auto-Refresh</div>
                <div class="text-caption text-grey">
                  {{ autoRefresh ? `Every ${refreshInterval/1000}s` : 'Disabled' }}
                </div>
              </div>
              <div class="col-auto">
                <q-toggle
                  v-model="autoRefresh"
                  color="primary"
                  @update:model-value="toggleAutoRefresh"
                  :label="autoRefresh ? 'On' : 'Off'"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from 'stores/auth';
import { useSystemStore } from 'stores/system';
import { useSettingsStore } from 'stores/settings';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'DashboardPage'
});
import api from 'services/ApiService';

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
 * Confirm shutdown
 */
function confirmShutdown() {
  $q.dialog({
    title: 'Shutdown PC',
    message: 'Are you sure you want to shutdown the PC?',
    cancel: true,
    persistent: true
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
    persistent: true
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
    persistent: true
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
      position: 'top'
    });
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || `${action} failed`,
      position: 'top'
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
    persistent: true
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
