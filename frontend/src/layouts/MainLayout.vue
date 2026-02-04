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
    <!-- Dynamic Island / Notch Spacer - CRITICAL for iOS -->
    <div class="dynamic-island-spacer"></div>

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

        <q-separator class="q-my-md bg-grey-9" style="opacity: 0.5" />

        <!-- Logout -->
        <q-item
          clickable
          @click="logout"
          class="nav-item"
          v-ripple
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

<!-- Global styles for iOS Safe Area and Overflow (not scoped) -->
<style>
/* iOS Safe Area Support */
.q-layout > .q-header {
  padding-top: constant(safe-area-inset-top) !important;
  padding-top: env(safe-area-inset-top) !important;
}

.q-layout > .q-footer {
  padding-bottom: constant(safe-area-inset-bottom) !important;
  padding-bottom: env(safe-area-inset-bottom) !important;
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

/* CRITICAL: Fix Notification Freeze Issue - Ghost Overlay Prevention */
.q-notifications {
  pointer-events: none !important;
  position: fixed !important;
  z-index: 10000 !important;
}

.q-notifications__list {
  pointer-events: none !important;
}

.q-notifications > * {
  pointer-events: auto !important;
}

.q-notification {
  pointer-events: auto !important;
}

/* CRITICAL: Fix drawer backdrop blocking UI */
.q-drawer__backdrop {
  pointer-events: auto !important;
  z-index: 4999 !important;
}

/* CRITICAL: Hide backdrop when drawer is closed - MUST NOT BLOCK UI */
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
</style>

<style scoped>
/* Dynamic Island / Notch Spacer - REDUCED by 5px */
.dynamic-island-spacer {
  width: 100%;
  height: max(35px, calc(env(safe-area-inset-top) - 5px));
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
  background: transparent;
  pointer-events: none;
}

/* Adjust page container to account for reduced spacer */
.q-page-container {
  padding-top: max(40px, calc(env(safe-area-inset-top))) !important;
}

/* CRITICAL: Fix z-index issues to prevent UI blocking */
.q-page {
  position: relative;
  z-index: 1;
}

/* CRITICAL: Ensure ALL buttons are clickable - higher than closed drawer backdrop */
.q-btn {
  position: relative !important;
  z-index: 1000 !important;
  pointer-events: auto !important;
}

.q-card, .stat-card, .action-card, .storage-card {
  position: relative;
  z-index: 10 !important;
}

/* System Actions buttons - CRITICAL FIX */
.action-card .q-btn {
  position: relative !important;
  z-index: 1001 !important;
  pointer-events: auto !important;
}

/* Storage card refresh button */
.storage-card .q-btn {
  z-index: 1001 !important;
  pointer-events: auto !important;
}

/* Quick action cards (Docker, Processes) */
.action-mini-card {
  pointer-events: auto !important;
  cursor: pointer !important;
}

/* CRITICAL: Fix z-index issues to prevent UI unresponsiveness */
.q-layout {
  position: relative;
  z-index: 1;
}

.q-drawer {
  z-index: 5000 !important;
}

.q-page-container {
  position: relative;
  z-index: 1;
}

/* Ensure no overlays block interaction */
.q-page,
.q-page > * {
  position: relative;
  z-index: 1;
}

/* CRITICAL: Ensure ALL page content is clickable and above backdrop */
.q-page-container > .q-page {
  position: relative !important;
  z-index: 100 !important;
}

.q-page > .q-card,
.q-page > .row,
.q-page > div {
  position: relative !important;
  z-index: 10 !important;
}

/* CRITICAL: ALL buttons must be clickable */
.q-page .q-btn {
  position: relative !important;
  z-index: 1001 !important;
  pointer-events: auto !important;
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
 * Navigate to route
 * CRITICAL: Close drawer after navigation to prevent backdrop blocking UI
 */
function navigateTo(path) {
  router.push(path);
  // Close drawer on navigation (especially important for mobile/overlay mode)
  leftDrawerOpen.value = false;
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
});

onUnmounted(() => {
  if (connectionCheckInterval) {
    clearInterval(connectionCheckInterval);
  }
});
</script>
