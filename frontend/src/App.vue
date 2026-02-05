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
  <router-view />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { Dark, Notify } from 'quasar';
import { useSettingsStore } from './stores/settings';
import { useSystemStore } from './stores/system';

/**
 * CRITICAL: Configure global notification defaults
 * This prevents the "Ghost Overlay" bug where notifications block UI interactions
 */
Notify.setDefaults({
  timeout: 2500, // ALL notifications auto-dismiss after 2.5 seconds
  position: 'top',
  actions: [{ icon: 'close', color: 'white', round: true, dense: true }]
});

/**
 * Handle system theme changes - stored for cleanup
 */
function handleThemeChange() {
  Dark.set(true);
}

/**
 * App Initialization
 * Initialize all stores and load persisted settings
 */
onMounted(async () => {
  // Initialize stores
  const settingsStore = useSettingsStore();
  const systemStore = useSystemStore();

  // Load settings from localStorage
  settingsStore.loadSettings();
  console.log('[App] Settings loaded from localStorage');

  // Load threshold configuration from backend
  try {
    await systemStore.loadThresholdConfig();
    console.log('[App] Threshold config loaded from backend');
  } catch (error) {
    console.warn('[App] Failed to load threshold config:', error);
  }

  // Apply dark mode from saved preferences
  if (settingsStore.preferences?.theme === 'dark' || settingsStore.preferences?.theme === 'auto') {
    Dark.set(true);
  } else {
    // Default to dark mode if not set
    Dark.set(true);
  }

  // Double-check dark mode is set (defensive)
  if (!Dark.isActive) {
    Dark.set(true);
  }

  // Listen for system theme changes and always force dark mode
  const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
  mediaQuery.addEventListener('change', handleThemeChange);
});

/**
 * Cleanup event listeners on unmount
 * Note: App.vue typically never unmounts in SPA, but this follows Vue 3 best practices
 */
onUnmounted(() => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
  mediaQuery.removeEventListener('change', handleThemeChange);
});
</script>

<style>
/* CRITICAL: Safety fix for notification wrappers - Prevents Ghost Overlay */
.q-notifications__list {
  pointer-events: none !important;
}

.q-notification {
  pointer-events: auto !important; /* Allow clicking the toast itself to dismiss */
}

/* Additional safety: ensure no invisible overlays block interactions */
.q-notifications {
  pointer-events: none !important;
}

/* FIX: Prevent dialog backdrop from receiving focus (accessibility fix) */
.q-dialog__backdrop {
  pointer-events: none !important;
}

.q-dialog__backdrop:focus {
  outline: none !important;
}

/* Ensure dialog content is still interactive */
.q-dialog {
  pointer-events: auto !important;
}

.q-dialog .q-card,
.q-dialog .q-card * {
  pointer-events: auto !important;
}
</style>
