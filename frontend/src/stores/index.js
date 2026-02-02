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

