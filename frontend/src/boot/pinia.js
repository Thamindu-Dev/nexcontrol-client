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
 * Pinia Boot File
 * Register Pinia plugins for automatic store persistence
 */

import { pinia } from 'quasar/wrappers';
import { createSettingsPersistencePlugin } from '../stores/settings';

export default async () => {
  // Register settings persistence plugin
  pinia.use(createSettingsPersistencePlugin());

  console.log('[Boot] Pinia plugins registered');
};
