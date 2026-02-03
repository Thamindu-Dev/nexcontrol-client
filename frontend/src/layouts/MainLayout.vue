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
  <q-layout view="lHh Lpr lFf">
    <!-- Header -->
    <q-header elevated class="app-header">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          class="header-btn"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>
          <div class="row items-center">
            <div class="logo-wrapper q-mr-sm">
              <q-icon name="computer" size="22px" color="white" />
            </div>
            <span class="app-title">NexControl</span>
          </div>
        </q-toolbar-title>

        <q-btn
          flat
          round
          dense
          icon="logout"
          class="header-btn logout-btn"
          @click="logout"
          v-if="authStore.isAuthenticated"
        >
          <q-tooltip anchor="bottom middle" self="top middle">Logout</q-tooltip>
        </q-btn>
      </q-toolbar>
    </q-header>

    <!-- Drawer -->
    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      class="app-drawer"
      :width="280"
    >
      <div class="drawer-header q-pa-lg">
        <div class="row items-center q-mb-md">
          <div class="logo-wrapper-large q-mr-sm">
            <q-icon name="computer" size="32px" color="white" />
          </div>
          <div>
            <div class="text-h6 text-weight-bold text-white">NexControl</div>
            <div class="text-caption text-grey-5">Remote PC Controller</div>
          </div>
        </div>
        <div class="connection-indicator q-pa-sm rounded-borders">
          <div class="row items-center">
            <q-icon
              :name="isConnected ? 'check_circle' : 'error'"
              :color="isConnected ? 'cyan' : 'grey-6'"
              size="18px"
              class="q-mr-sm"
            />
            <span class="text-subtitle2 text-white">{{ isConnected ? 'Connected' : 'Disconnected' }}</span>
          </div>
          <div class="text-caption text-grey-6 q-mt-xs">{{ serverInfo }}</div>
        </div>
      </div>

      <q-list class="drawer-list">
        <!-- Navigation Section -->
        <q-item-label header class="section-label">
          Navigation
        </q-item-label>

        <q-item
          v-for="link in navigationLinks"
          :key="link.title"
          clickable
          :active="link.link === $route.path"
          active-class="nav-item-active"
          @click="navigateTo(link.link)"
          class="nav-item"
          v-ripple
        >
          <q-item-section avatar>
            <div class="icon-wrapper" :class="{ 'icon-active': link.link === $route.path }">
              <q-icon :name="link.icon" size="22px" :color="link.link === $route.path ? 'cyan' : 'grey-5'" />
            </div>
          </q-item-section>
          <q-item-section>
            <q-item-label :class="{ 'text-weight-bold': link.link === $route.path, 'text-white': true }">
              {{ link.title }}
            </q-item-label>
            <q-item-label caption class="text-grey-6">{{ link.caption }}</q-item-label>
          </q-item-section>
          <q-item-section side v-if="link.link === $route.path">
            <q-icon name="chevron_right" color="cyan" size="20px" />
          </q-item-section>
        </q-item>

        <q-separator class="q-my-md bg-grey-9" style="opacity: 0.5" />

        <!-- System Section -->
        <q-item-label header class="section-label">
          System
        </q-item-label>

        <q-item
          clickable
          @click="refreshStats"
          :disable="loading"
          class="nav-item"
          v-ripple
        >
          <q-item-section avatar>
            <div class="icon-wrapper">
              <q-icon
                name="refresh"
                size="22px"
                :color="loading ? 'cyan' : 'grey-5'"
                :class="{ 'rotating': loading }"
              />
            </div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-white">Refresh Stats</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          clickable
          @click="navigateTo('/settings')"
          class="nav-item"
          v-ripple
        >
          <q-item-section avatar>
            <div class="icon-wrapper">
              <q-icon name="settings" size="22px" color="grey-5" />
            </div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-white">Settings</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <!-- Page Container -->
    <q-page-container class="bg-black">
      <router-view />
    </q-page-container>

    <!-- Footer -->
    <q-footer v-if="authStore.isAuthenticated" elevated class="app-footer">
      <q-toolbar class="q-pa-none">
        <div class="row col-12 items-center q-pa-sm footer-content">
          <div class="row items-center">
            <div class="status-dot q-mr-sm" :class="{ 'status-connected': isConnected, 'status-disconnected': !isConnected }"></div>
            <span class="text-subtitle2 text-white q-mr-md">
              {{ isConnected ? 'Connected' : 'Disconnected' }}
            </span>
            <q-separator vertical class="q-mx-md bg-grey-8" style="opacity: 0.3" />
            <span class="text-caption text-grey-6">
              <q-icon name="dns" size="14px" class="q-mr-xs" />
              {{ serverInfo }}
            </span>
          </div>
          <q-space />
          <div class="text-caption text-grey-7">
            © 2026 Thamindu-Dev | v1.0.0
          </div>
        </div>
      </q-toolbar>
    </q-footer>
  </q-layout>
</template>

<!-- Global styles for iOS Safe Area (not scoped) -->
<style>
/* iOS Safe Area Support - Critical for Dynamic Island/Notch */
.q-layout > .q-header {
  padding-top: constant(safe-area-inset-top) !important; /* iOS 11.0 */
  padding-top: env(safe-area-inset-top) !important; /* iOS 11.2+ */
}

.q-layout > .q-footer {
  padding-bottom: constant(safe-area-inset-bottom) !important; /* iOS 11.0 */
  padding-bottom: env(safe-area-inset-bottom) !important; /* iOS 11.2+ */
}

.q-layout > .q-page-container {
  padding-left: constant(safe-area-inset-left) !important;
  padding-left: env(safe-area-inset-left) !important;
  padding-right: constant(safe-area-inset-right) !important;
  padding-right: env(safe-area-inset-right) !important;
}
</style>

<style scoped>
/* Header - Pure Black */
.app-header {
  background: #000000;
  border-bottom: 1px solid #333333;
}

/* Ensure toolbar has proper spacing with safe area */
.app-header .q-toolbar {
  min-height: calc(50px + constant(safe-area-inset-top));
  min-height: calc(50px + env(safe-area-inset-top));
}

.app-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: 0.5px;
}

.logo-wrapper {
  width: 36px;
  height: 36px;
  background: #0A0A0A;
  border: 1px solid #333333;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-wrapper-large {
  width: 48px;
  height: 48px;
  background: #0A0A0A;
  border: 1px solid #333333;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
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
  border-color: #333333;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.1);
}

/* Drawer - Pure Black */
.app-drawer {
  background: #000000;
  border-right: 1px solid #333333;
}

.drawer-header {
  border-bottom: 1px solid #333333;
  background: #000000;
}

.connection-indicator {
  background: #0A0A0A;
  border: 1px solid #333333;
}

/* Drawer List */
.drawer-list {
  padding: 16px;
}

.section-label {
  color: #666666;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding-left: 8px;
  margin-bottom: 8px;
}

/* Navigation Items */
.nav-item {
  border-radius: 10px;
  margin-bottom: 4px;
  padding: 10px 12px;
  transition: all 0.2s ease;
  background: transparent;
}

.nav-item:hover {
  background: #0A0A0A;
}

.nav-item-active {
  background: #0A0A0A !important;
  border: 1px solid rgba(34, 211, 238, 0.3);
}

.icon-wrapper {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #0A0A0A;
  border: 1px solid #333333;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.icon-active {
  background: rgba(34, 211, 238, 0.1);
  border-color: rgba(34, 211, 238, 0.5);
}

.nav-item:hover .icon-wrapper {
  background: #111111;
}

/* Rotating animation */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Footer - Pure Black */
.app-footer {
  background: #000000;
  border-top: 1px solid #333333;
}

.footer-content {
  background: #0A0A0A;
  border-radius: 8px;
  padding: 10px 12px;
}

/* Status Dot - Neon Cyan when connected */
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse-dot 2s ease-in-out infinite;
}

.status-connected {
  background: #22d3ee;
  box-shadow: 0 0 8px rgba(34, 211, 238, 0.6);
}

.status-disconnected {
  background: #666666;
  box-shadow: none;
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

/* Page Container */
.bg-black {
  background: #000000 !important;
}

/* Dialog Styling */
:deep(.glass-dialog) {
  background: #0A0A0A !important;
  border: 1px solid #333333;
  color: #FFFFFF;
}

/* Notification Styling */
:deep(.notification-glossy) {
  background: #0A0A0A !important;
  border: 1px solid #333333;
  color: #FFFFFF;
}

/* Responsive Adjustments */
@media (max-width: 575.98px) {
  .app-title {
    font-size: 0.95rem !important;
  }

  .logo-wrapper {
    width: 32px !important;
    height: 32px !important;
  }

  .logo-wrapper-large {
    width: 40px !important;
    height: 40px !important;
  }

  .nav-item {
    min-height: 44px;
  }

  .footer-content {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 6px;
  }

  .text-caption {
    font-size: 0.65rem;
  }
}

@media (hover: none) and (pointer: coarse) {
  .nav-item {
    min-height: 44px;
    padding: 10px !important;
  }

  .header-btn {
    min-width: 44px;
    min-height: 44px;
  }

  .nav-item:hover {
    background: transparent;
  }
}

@media (max-width: 767.98px) {
  .app-drawer {
    width: 280px !important;
  }

  .logo-wrapper-large {
    width: 42px !important;
    height: 42px !important;
  }

  .connection-indicator .text-caption {
    display: none;
  }
}

@media (max-width: 767.98px) and (orientation: landscape) {
  .q-pa-lg {
    padding: 10px !important;
  }

  .drawer-header {
    padding: 14px !important;
  }
}
</style>

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
  },
  {
    title: 'Scheduled Tasks',
    caption: 'Schedule power actions',
    icon: 'schedule',
    link: '/scheduled-tasks'
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
    persistent: true,
    class: 'glass-dialog'
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
    $q.notify({
      type: 'positive',
      message: 'Stats refreshed successfully',
      position: 'bottom',
      classes: 'notification-glossy'
    });
  } catch {
    isConnected.value = false;
    $q.notify({
      type: 'negative',
      message: 'Failed to refresh stats',
      position: 'bottom',
      classes: 'notification-glossy'
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
