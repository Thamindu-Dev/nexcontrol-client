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
 * Force Dark Mode and ensure persistence
 */
onMounted(() => {
  // CRITICAL: Force Dark Mode on app startup
  // This prevents the "white text on white background" issue
  Dark.set(true);

  // Store preference in localStorage for persistence
  localStorage.setItem('quasar-dark-mode', 'true');

  // Listen for system theme changes and always force dark mode
  const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
  mediaQuery.addEventListener('change', handleThemeChange);

  // Double-check dark mode is set (defensive)
  if (!Dark.isActive) {
    Dark.set(true);
  }
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
</style>
