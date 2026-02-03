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
 * Services Export
 * =============================================================
 * Central export point for all services
 */

import ApiService from './ApiService';
import { encryptPayload, decryptResponse, setAESKey } from './EncryptionService';
import WoLService from './WoLService';
import { wsService, WebSocketState } from './WebSocketService';

export {
  ApiService,
  encryptPayload,
  decryptResponse,
  setAESKey,
  WoLService,
  wsService,
  WebSocketState
};

export default {
  ApiService,
  WoLService,
  wsService
};
