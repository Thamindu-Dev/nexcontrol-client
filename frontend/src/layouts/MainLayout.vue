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
    <!-- Animated Background -->
    <div class="animated-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <!-- Header -->
    <q-header elevated class="glass-header">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          class="menu-btn glass-btn"
          @click="toggleLeftDrawer"
        />

        <q-toolbar-title>
          <div class="row items-center">
            <div class="logo-wrapper q-mr-sm">
              <q-icon name="computer" size="24px" color="white" />
            </div>
            <span class="app-title">NexControl</span>
          </div>
        </q-toolbar-title>

        <q-btn
          flat
          round
          dense
          icon="logout"
          class="glass-btn logout-btn"
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
      class="glass-drawer"
      :width="280"
    >
      <div class="drawer-header q-pa-lg">
        <div class="row items-center q-mb-md">
          <div class="logo-wrapper-large q-mr-sm">
            <q-icon name="computer" size="32px" color="white" />
          </div>
          <div>
            <div class="text-h6 text-weight-bold text-white">NexControl</div>
            <div class="text-caption text-grey-4">Remote PC Controller</div>
          </div>
        </div>
        <div class="connection-indicator q-pa-sm rounded-borders">
          <div class="row items-center">
            <q-icon
              :name="isConnected ? 'check_circle' : 'error'"
              :color="isConnected ? 'white' : 'grey-7'"
              size="20px"
              class="q-mr-sm"
            />
            <span class="text-subtitle2 text-white">{{ isConnected ? 'Connected' : 'Disconnected' }}</span>
          </div>
          <div class="text-caption text-grey-4 q-mt-xs">{{ serverInfo }}</div>
        </div>
      </div>

      <q-list class="drawer-list">
        <!-- Navigation Section -->
        <q-item-label header class="section-label">
          <q-icon name="navigation" size="16px" class="q-mr-xs" />
          Navigation
        </q-item-label>

        <q-item
          v-for="link in navigationLinks"
          :key="link.title"
          clickable
          :active="link.link === $route.path"
          active-class="nav-item-active"
          @click="navigateTo(link.link)"
          class="nav-item glass-btn"
          v-ripple
        >
          <q-item-section avatar>
            <div class="icon-wrapper" :class="{ 'icon-active': link.link === $route.path }">
              <q-icon :name="link.icon" size="24px" />
            </div>
          </q-item-section>
          <q-item-section>
            <q-item-label :class="{ 'text-weight-bold': link.link === $route.path, 'text-white': true }">
              {{ link.title }}
            </q-item-label>
            <q-item-label caption class="text-grey-4">{{ link.caption }}</q-item-label>
          </q-item-section>
          <q-item-section side v-if="link.link === $route.path">
            <q-icon name="chevron_right" color="white" size="20px" />
          </q-item-section>
        </q-item>

        <q-separator class="q-my-md bg-white" style="opacity: 0.1" />

        <!-- System Section -->
        <q-item-label header class="section-label">
          <q-icon name="settings" size="16px" class="q-mr-xs" />
          System
        </q-item-label>

        <q-item
          clickable
          @click="refreshStats"
          :disable="loading"
          class="nav-item glass-btn"
          v-ripple
        >
          <q-item-section avatar>
            <div class="icon-wrapper">
              <q-icon
                name="refresh"
                size="24px"
                :class="{ 'rotating': loading, 'text-white': loading }"
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
          class="nav-item glass-btn"
          v-ripple
        >
          <q-item-section avatar>
            <div class="icon-wrapper">
              <q-icon name="settings" size="24px" />
            </div>
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-white">Settings</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <!-- Page Container -->
    <q-page-container class="bg-transparent">
      <router-view />
    </q-page-container>

    <!-- Footer -->
    <q-footer v-if="authStore.isAuthenticated" elevated class="glass-footer">
      <q-toolbar class="q-pa-none">
        <div class="row col-12 items-center q-pa-sm footer-content">
          <div class="row items-center">
            <div class="status-dot q-mr-sm" :class="{ 'status-connected': isConnected, 'status-disconnected': !isConnected }"></div>
            <span class="text-subtitle2 text-white q-mr-md">
              {{ isConnected ? 'Connected' : 'Disconnected' }}
            </span>
            <q-separator vertical class="q-mx-md bg-white" style="opacity: 0.2" />
            <span class="text-caption text-grey-3">
              <q-icon name="dns" size="14px" class="q-mr-xs" />
              {{ serverInfo }}
            </span>
          </div>
          <q-space />
          <div class="text-caption text-grey-4">
            © 2026 Thamindu-Dev | v1.0.0
          </div>
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
      position: 'top',
      classes: 'notification-glossy'
    });
  } catch {
    isConnected.value = false;
    $q.notify({
      type: 'negative',
      message: 'Failed to refresh stats',
      position: 'top',
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

<style scoped>
/* Header */
.glass-header {
  background: rgba(15, 12, 41, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.app-title {
  font-size: 1.25rem;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-wrapper {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.logo-wrapper-large {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
  }
  50% {
    box-shadow: 0 6px 24px rgba(139, 92, 246, 0.6);
  }
}

/* Menu Button */
.menu-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Logout Button */
.logout-btn {
  color: #f87171;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
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

/* Drawer */
.glass-drawer {
  background: rgba(15, 12, 41, 0.95);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.drawer-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
}

.connection-indicator {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  backdrop-filter: blur(10px);
}

/* Drawer List */
.drawer-list {
  padding: 16px;
}

.section-label {
  color: #90caf9;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  padding-left: 8px;
  margin-bottom: 8px;
}

/* Navigation Items */
.nav-item {
  border-radius: 12px;
  margin-bottom: 4px;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(4px);
}

.nav-item-active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2)) !important;
  border: 1px solid rgba(59, 130, 246, 0.3);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.icon-active {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.nav-item:hover .icon-wrapper {
  background: rgba(59, 130, 246, 0.15);
  transform: scale(1.05);
}

.nav-item-active .icon-wrapper {
  transform: scale(1.05);
}

/* Rotating animation for refresh icon */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Footer */
.glass-footer {
  background: rgba(15, 12, 41, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-content {
  background: rgba(59, 130, 246, 0.05);
  border-radius: 8px;
  padding: 12px 16px;
}

/* Status Dot */
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse-dot 2s ease-in-out infinite;
}

.status-connected {
  background: #4ade80;
  box-shadow: 0 0 8px #4ade80;
}

.status-disconnected {
  background: #ef4444;
  box-shadow: 0 0 8px #ef4444;
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
.bg-transparent {
  background: transparent !important;
}

/* Dialog Styling */
:deep(.glass-dialog) {
  backdrop-filter: blur(20px);
  background: rgba(30, 30, 30, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Notification Styling */
:deep(.notification-glossy) {
  backdrop-filter: blur(10px);
  background: rgba(30, 30, 30, 0.9) !important;
}

/* Smooth Transitions */
* {
  transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease;
}

/* Remove default active background */
:deep(.q-item.q-item--active) {
  background-color: transparent !important;
}

/* Responsive Adjustments */
/* Extra small devices (phones, < 576px) */
@media (max-width: 575.98px) {
  /* Hide drawer text on very small screens */
  .nav-item :deep(.q-item__label) {
    font-size: 0.9rem;
  }

  /* Adjust header for mobile */
  .app-title {
    font-size: 1rem !important;
  }

  .logo-wrapper {
    width: 36px !important;
    height: 36px !important;
  }

  .logo-wrapper-large {
    width: 40px !important;
    height: 40px !important;
  }

  /* Make nav items more tap-friendly */
  .nav-item {
    min-height: 48px;
  }

  /* Adjust footer for mobile */
  .footer-content {
    flex-direction: column;
    align-items: flex-start !important;
    gap: 8px;
  }

  /* Hide some elements on very small screens */
  .text-caption {
    font-size: 0.7rem;
  }
}

/* Small devices (landscape phones, ≥ 576px) */
@media (min-width: 576px) and (max-width: 767.98px) {
  /* Adjust drawer for small tablets */
}

/* Medium devices (tablets, ≥ 768px) */
@media (min-width: 768px) and (max-width: 991.98px) {
  /* Tablet drawer adjustments */
}

/* Large devices (desktops, ≥ 992px) */
@media (min-width: 992px) {
  /* Desktop optimizations */
}

/* Touch device optimizations */
@media (hover: none) and (pointer: coarse) {
  /* Make nav items larger for touch */
  .nav-item {
    min-height: 48px;
    padding: 12px !important;
  }

  /* Increase touch targets */
  .q-btn.glass-btn {
    min-width: 44px;
    min-height: 44px;
  }

  /* Remove hover effects */
  .nav-item:hover,
  .glass-btn:hover,
  .glass-card:hover {
    transform: none !important;
  }
}

/* Safe area support for devices with notches */
@supports (padding: max(0px)) {
  .glass-header {
    padding-top: max(0px, env(safe-area-inset-top));
    padding-left: max(0px, env(safe-area-inset-left));
    padding-right: max(0px, env(safe-area-inset-right));
  }

  .glass-footer {
    padding-bottom: max(0px, env(safe-area-inset-bottom));
    padding-left: max(0px, env(safe-area-inset-left));
    padding-right: max(0px, env(safe-area-inset-right));
  }

  .glass-drawer {
    padding-left: max(0px, env(safe-area-inset-left));
    padding-bottom: max(0px, env(safe-area-inset-bottom));
  }
}

/* Mobile drawer adjustments */
@media (max-width: 767.98px) {
  /* Full width drawer on mobile */
  .glass-drawer {
    width: 280px !important;
  }

  /* Adjust logo in drawer */
  .logo-wrapper-large {
    width: 45px !important;
    height: 45px !important;
  }

  /* Hide connection indicator details on mobile */
  .connection-indicator .text-caption {
    display: none;
  }
}

/* Landscape mobile adjustments */
@media (max-width: 767.98px) and (orientation: landscape) {
  /* Reduce padding in landscape */
  .q-pa-lg {
    padding: 12px !important;
  }

  .drawer-header {
    padding: 16px !important;
  }
}

/* Animated Background */
.animated-background {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  z-index: 0;
  pointer-events: none;
}

/* Animated Orbs */
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
  animation: float 20s infinite;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #3b82f6 0%, transparent 70%);
  top: -100px;
  left: -100px;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
  bottom: -50px;
  right: -50px;
  animation-delay: -5s;
}

.orb-3 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
  top: 40%;
  left: 40%;
  transform: translate(-50%, -50%);
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}
</style>
