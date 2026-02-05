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
  <q-layout view="hHh lpR fFf">
    <!-- Static Global Header -->
    <q-header elevated class="bg-black text-white global-header">
      <q-toolbar style="min-height: 60px; padding-top: env(safe-area-inset-top);">
        <!-- Left Side: Navigation Control -->
        <q-btn
          v-if="isDashboard"
          flat
          round
          dense
          icon="menu"
          @click="toggleDrawer"
          class="header-btn"
        />
        <q-btn
          v-else
          flat
          round
          dense
          icon="arrow_back"
          @click="goBack"
          class="header-btn"
        />

        <!-- Center: Page Title -->
        <q-toolbar-title class="app-title">
          {{ currentPageTitle }}
        </q-toolbar-title>

        <!-- Right Side: Actions -->
        <template v-if="isDashboard">
          <!-- Polling/Realtime Toggle (Dashboard only) -->
          <div class="row items-center q-gutter-sm">
            <q-icon name="timer" size="16px" color="grey-6" />
            <span class="text-caption text-grey-6">Polling</span>
            <q-toggle
              :model-value="systemStore.webSocketEnabled"
              @update:model-value="toggleWebSocket"
              color="cyan"
              keep-emphasis
              size="md"
              checked-icon="bolt"
              unchecked-icon="timer"
            />
            <span class="text-caption text-cyan">Real-time</span>
            <q-icon name="bolt" size="16px" color="cyan" />
          </div>
        </template>
      </q-toolbar>
    </q-header>

    <!-- Drawer -->
    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      class="app-drawer"
      :width="280"
      :content-style="{ zIndex: 10001 }"
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
          v-ripple
          :to="link.link"
          class="nav-item"
          :class="{ 'nav-item-active': link.link === $route.path }"
          exact
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
          @click="refreshStats"
          :disable="loading"
          class="nav-item"
          v-ripple
          style="cursor: pointer !important;"
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
          v-ripple
          to="/settings"
          class="nav-item"
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

        <q-separator class="q-my-md bg-grey-9" style="opacity: 0.5" />

        <!-- Logout -->
        <q-item
          @click="logout"
          class="nav-item"
          v-ripple
          style="cursor: pointer !important;"
        >
          <q-item-section avatar>
            <div class="icon-wrapper">
              <q-icon name="logout" size="22px" color="grey-5" />
            </div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-white">Logout</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <!-- Page Container -->
    <q-page-container class="bg-black" style="padding-top: 20px !important; padding-bottom: 20px !important;">
      <router-view />
    </q-page-container>

    <!-- Footer -->
    <q-footer v-if="authStore.isAuthenticated" elevated class="app-footer" style="padding-bottom: 0 !important;">
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

<!-- Global styles for iOS Safe Area and Overflow (not scoped) -->
<style>
/* iOS Safe Area Support - CRITICAL FIX */

/* Force remove bottom safe area spacing from footer - COMPLETELY REMOVE IT */
.q-layout > .q-footer,
.q-footer,
.app-footer,
.q-layout > .q-footer .q-toolbar,
.q-footer .q-toolbar {
  padding-bottom: 0 !important;
}

.q-layout > .q-page-container {
  padding-left: constant(safe-area-inset-left) !important;
  padding-left: env(safe-area-inset-left) !important;
  padding-right: constant(safe-area-inset-right) !important;
  padding-right: env(safe-area-inset-right) !important;
}

/* Fix Horizontal Overflow - Prevent screen sliding */
body,
.q-layout,
.q-page,
.q-page-container {
  overflow-x: hidden !important;
  max-width: 100vw !important;
}

/* Fix row overflow issues */
.row {
  flex-wrap: wrap !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
}

/* Z-INDEX HIERARCHY - Proper stacking context
   Quasar defaults:
   - Drawer: 1000
   - Drawer backdrop: 500
   - Dialog/Menu: 6000
   - Notifications: 9500
*/

/* Notifications - Must be above everything except top-most modals */
.q-notifications {
  pointer-events: none !important;
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  height: auto !important;
  max-height: 200px !important;
  z-index: 9500 !important; /* Quasar default */
  overflow: visible !important;
}

.q-notifications__list {
  pointer-events: none !important;
}

.q-notification {
  pointer-events: auto !important;
}

/* Drawer backdrop - Below drawer but above content */
.q-drawer__backdrop {
  pointer-events: auto !important;
  z-index: 999 !important; /* Just below drawer's 1000 */
}

/* Hide backdrop when drawer is closed */
.q-drawer--on-layout:not(.q-drawer--open) ~ .q-drawer__backdrop,
.q-layout > .q-drawer__backdrop:hidden,
.q-drawer:not(.q-drawer--open) ~ .q-drawer__backdrop {
  display: none !important;
  pointer-events: none !important;
  opacity: 0 !important;
}

/* Ensure backdrop only blocks when drawer is actually open */
.q-drawer--open ~ .q-drawer__backdrop,
.q-drawer__backdrop--visible {
  pointer-events: auto !important;
  opacity: 1 !important;
}

/* FIX: Remove overly aggressive z-index overrides
   Standard UI elements should use natural DOM order */

body,
#q-app,
.q-layout,
.q-page,
.q-page-container {
  position: relative !important;
}

/* ONLY ensure interactive elements have pointer-events enabled
   DO NOT add z-index to standard buttons */
.q-btn,
button,
a,
.q-item,
.q-card[clickable],
.q-card.clickable,
[role="button"],
[onclick] {
  pointer-events: auto !important;
  cursor: pointer !important;
}

/* ONLY disable pointer-events on specific non-interactive elements */
.static-content,
.non-interactive,
[pointer-events="none"] {
  pointer-events: none !important;
}

/* CRITICAL: Drawer z-index */
.q-drawer {
  position: fixed !important;
  z-index: 1000 !important; /* Quasar default */
  pointer-events: auto !important;
}

.q-drawer > *,
.q-drawer .q-list,
.q-drawer .drawer-list,
.q-drawer .q-item {
  position: relative !important;
  z-index: 10002 !important;
  pointer-events: auto !important;
  cursor: pointer !important;
}

/* CRITICAL: Backdrop should NOT block drawer */
.q-drawer__backdrop {
  z-index: 10000 !important;
}

/* Hide backdrop when drawer is closed */
.q-drawer:not(.q-drawer--open) ~ .q-drawer__backdrop {
  display: none !important;
}
</style>

<style scoped>
/* Global Header Styles */
.global-header {
  border-bottom: 1px solid #333333;
  min-height: 60px;
}

.global-header .q-toolbar {
  min-height: 60px;
}

.header-btn {
  min-width: 44px;
  min-height: 44px;
}

.app-title {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: 0.5px;
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

/* Make all drawer items clickable */
.drawer-list,
.drawer-list .q-item,
.drawer-list .nav-item {
  position: relative !important;
  pointer-events: auto !important;
  cursor: pointer !important;
}

.drawer-list .q-item:hover {
  pointer-events: auto !important;
}

/* Ensure all children allow parent to receive click */
.drawer-list .q-item > * {
  pointer-events: none !important;
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
  position: relative !important;
  pointer-events: none !important;
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
    font-size: 1rem !important;
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from '../stores/auth';
import { useSettingsStore } from '../stores/settings';
import { useSystemStore } from '../stores/system';

const router = useRouter();
const $route = useRoute();
const $q = useQuasar();

// Stores
const authStore = useAuthStore();
const settingsStore = useSettingsStore();
const systemStore = useSystemStore();

// State
const leftDrawerOpen = ref(false);
const loading = ref(false);

// Connection status - use store as source of truth
const isConnected = computed(() => systemStore.isConnected);

// Check if current route is dashboard
const isDashboard = computed(() => $route.path === '/dashboard');

// Page title mapping
const pageTitleMap = {
  '/dashboard': 'Dashboard',
  '/docker': 'Docker Manager',
  '/processes': 'Process Manager',
  '/screenshot': 'Screenshot',
  '/wol': 'Wake on LAN',
  '/threshold-alerts': 'Threshold Alerts',
  '/scheduled-tasks': 'Scheduled Tasks',
  '/settings': 'Settings'
};

// Current page title
const currentPageTitle = computed(() => {
  return pageTitleMap[$route.path] || 'NexControl';
});

// CRITICAL: Watch route changes to close drawer on navigation
// This prevents the backdrop from blocking UI interactions
watch(() => $route.path, () => {
  leftDrawerOpen.value = false;
}, { flush: 'post' });

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
    title: 'Threshold Alerts',
    caption: 'System Alerts',
    icon: 'notifications',
    link: '/threshold-alerts'
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
 * Toggle drawer
 */
function toggleDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

/**
 * Go back to previous page
 */
function goBack() {
  router.back();
}

/**
 * Toggle WebSocket real-time mode
 */
function toggleWebSocket() {
  if (systemStore.webSocketEnabled) {
    systemStore.disableWebSocket();
  } else {
    systemStore.enableWebSocket();
  }
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
    // isConnected is now managed by the store
    $q.notify({
      type: 'positive',
      message: 'Stats refreshed successfully',
      position: 'bottom',
      classes: 'notification-glossy'
    });
  } catch {
    // isConnected is now managed by the store
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
 * Handle toggle drawer event
 */
function handleToggleDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

/**
 * Lifecycle
 */
onMounted(() => {
  // Check connection every 30 seconds
  connectionCheckInterval = setInterval(async () => {
    try {
      await systemStore.fetchCPUStats();
      // isConnected is now managed by the store
    } catch {
      // isConnected is now managed by the store
    }
  }, 30000);

  // Listen for toggle-drawer event from child components
  window.addEventListener('toggle-drawer', handleToggleDrawer);
});

onUnmounted(() => {
  if (connectionCheckInterval) {
    clearInterval(connectionCheckInterval);
  }
  // Remove event listener
  window.removeEventListener('toggle-drawer', handleToggleDrawer);
});
</script>
