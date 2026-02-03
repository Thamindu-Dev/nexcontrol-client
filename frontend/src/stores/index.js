/**
 * ==============================================================================
 * NexControl - Remote PC Controller
 * Copyright (C) 2026 Thamindu-Dev
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * ==============================================================================
 */

/**
 * =============================================================
 * Pinia Store Setup
 * =============================================================
 * Centralizes all Pinia stores and initializes Pinia
 */

import { defineStore } from '#q-app/wrappers';
import { createPinia } from 'pinia';
import { useAuthStore } from './auth';
import { useSettingsStore } from './settings';
import { useSystemStore } from './system';

// Export all stores for easy importing
export { useAuthStore, useSettingsStore, useSystemStore };

/*
 * Pinia instance creation
 * If not building with SSR mode, you can directly export the Store instantiation
 */

export default defineStore((/* { ssrContext } */) => {
  const pinia = createPinia();

  // You can add Pinia plugins here
  // pinia.use(SomePiniaPlugin)

  return pinia;
});

