<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-primary">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>
          <q-avatar color="white" text-color="primary" size="sm" class="q-mr-sm">
            <q-icon name="computer" />
          </q-avatar>
          NexControl
        </q-toolbar-title>

        <q-btn
          flat
          round
          dense
          icon="logout"
          @click="logout"
          v-if="authStore.isAuthenticated"
        >
          <q-tooltip>Logout</q-tooltip>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item-label header>Navigation</q-item-label>

        <q-item
          v-for="link in navigationLinks"
          :key="link.title"
          clickable
          :active="link.link === $route.path"
          @click="navigateTo(link.link)"
          v-ripple
        >
          <q-item-section avatar>
            <q-icon :name="link.icon" :color="link.link === $route.path ? 'primary' : undefined" />
          </q-item-section>
          <q-item-section>
            <q-item-label :class="{ 'text-weight-bold': link.link === $route.path }">
              {{ link.title }}
            </q-item-label>
            <q-item-label caption>{{ link.caption }}</q-item-label>
          </q-item-section>
        </q-item>

        <q-separator spaced />

        <q-item-label header>System</q-item-label>

        <q-item
          clickable
          @click="refreshStats"
          :disable="loading"
          v-ripple
        >
          <q-item-section avatar>
            <q-icon name="refresh" :class="{ 'text-primary': loading }" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Refresh Stats</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          clickable
          @click="navigateTo('/settings')"
          v-ripple
        >
          <q-item-section avatar>
            <q-icon name="settings" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Settings</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>

    <!-- Connection Status Footer -->
    <q-footer v-if="authStore.isAuthenticated" elevated class="bg-grey-9">
      <q-toolbar class="q-pa-none">
        <div class="row col-12 items-center q-pa-sm">
          <q-icon
            :name="isConnected ? 'check_circle' : 'error'"
            :color="isConnected ? 'positive' : 'negative'"
            size="sm"
          />
          <span class="q-ml-sm text-caption">
            {{ isConnected ? 'Connected' : 'Disconnected' }}
          </span>
          <q-space />
          <span class="text-caption text-grey">
            {{ serverInfo }}
          </span>
        </div>
      </q-toolbar>
    </q-footer>
  </q-layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from '../stores/auth';
import { useSettingsStore } from '../stores/settings';
import { useSystemStore } from '../stores/system';

const router = useRouter();
const $q = useQuasar();

// Stores
const authStore = useAuthStore();
const settingsStore = useSettingsStore();
const systemStore = useSystemStore();

// State
const leftDrawerOpen = ref(false);
const isConnected = ref(true);
const loading = ref(false);

// Navigation links
const navigationLinks = [
  {
    title: 'Dashboard',
    caption: 'System Overview',
    icon: 'dashboard',
    link: '/dashboard'
  },
  {
    title: 'Docker',
    caption: 'Container Management',
    icon: 'inventory_2',
    link: '/docker'
  },
  {
    title: 'Processes',
    caption: 'Process Manager',
    icon: 'memory',
    link: '/processes'
  },
  {
    title: 'Screenshot',
    caption: 'Remote Screenshot',
    icon: 'screenshot',
    link: '/screenshot'
  },
  {
    title: 'Wake on LAN',
    caption: 'WoL Manager',
    icon: 'power_settings_new',
    link: '/wol'
  }
];

// Computed
const serverInfo = computed(() => {
  const server = settingsStore.server;
  if (server) {
    return `${server.protocol || 'http'}://${server.host}:${server.port}`;
  }
  return 'Not configured';
});

/**
 * Toggle left drawer
 */
function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

/**
 * Navigate to route
 */
function navigateTo(path) {
  router.push(path);
}

/**
 * Logout
 */
function logout() {
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
 * Refresh all stats
 */
async function refreshStats() {
  loading.value = true;
  try {
    await Promise.all([
      systemStore.fetchCPUStats(),
      systemStore.fetchMemoryStats(),
      systemStore.fetchDiskStats(),
      systemStore.fetchGPUStats()
    ]);
    isConnected.value = true;
  } catch {
    isConnected.value = false;
    $q.notify({
      type: 'negative',
      message: 'Failed to refresh stats',
      position: 'top'
    });
  } finally {
    loading.value = false;
  }
}

/**
 * Connection check interval
 */
let connectionCheckInterval;

/**
 * Lifecycle
 */
onMounted(() => {
  // Check connection every 30 seconds
  connectionCheckInterval = setInterval(async () => {
    try {
      await systemStore.fetchCPUStats();
      isConnected.value = true;
    } catch {
      isConnected.value = false;
    }
  }, 30000);
});

onUnmounted(() => {
  if (connectionCheckInterval) {
    clearInterval(connectionCheckInterval);
  }
});
</script>

<style scoped>
.q-item.q-item--active {
  background-color: rgba(0, 0, 0, 0.03);
}
</style>
