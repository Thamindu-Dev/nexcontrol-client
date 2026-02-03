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
import { onMounted } from 'vue';
import { Dark } from 'quasar';

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
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
    Dark.set(true);
  });

  // Double-check dark mode is set (defensive)
  if (!Dark.isActive) {
    Dark.set(true);
  }
});
</script>
