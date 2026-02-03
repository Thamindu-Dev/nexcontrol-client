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
 * WoLService - Wake-on-LAN (Magic Packet) Service
 * =============================================================
 * Sends Wake-on-LAN magic packets to wake up remote PCs
 *
 * NOTE: Browser cannot send raw UDP packets due to security restrictions.
 *
 * For web browsers:
 * - This service will forward WoL requests through the backend
 *
 * For mobile (Capacitor):
 * - Requires a UDP plugin (like @capacitor-community/udp)
 * - Or can use backend proxy
 *
 * Magic Packet Format:
 * - 6 bytes of 0xFF followed by 16 repetitions of target MAC address
 */

import api from './ApiService';

/**
 * Send Wake-on-LAN magic packet through backend
 *
 * Browsers cannot send raw UDP packets, so we use the backend as a proxy
 *
 * @param {string} macAddress - Target MAC address (XX:XX:XX:XX:XX:XX)
 * @param {string} broadcastIp - Broadcast IP (default: 255.255.255.255)
 * @param {number} port - UDP port (default: 9)
 * @returns {Promise} Result
 */
export async function sendMagicPacket(macAddress, broadcastIp = '255.255.255.255', port = 9) {
  try {
    // Validate MAC address format
    const macPattern = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
    if (!macPattern.test(macAddress)) {
      throw new Error('Invalid MAC address format');
    }

    // Build query parameters
    const params = new URLSearchParams({
      mac_address: macAddress,
      broadcast_ip: broadcastIp,
      port: port.toString()
    });

    // Send through backend using query parameters
    const response = await api.post(`/api/wol/send?${params.toString()}`);

    return response;
  } catch (error) {
    console.error('WoL error:', error);

    // If backend endpoint doesn't exist, show error
    if (error.message?.includes('404')) {
      throw new Error('WoL endpoint not available. Please ensure backend WoL feature is enabled.');
    }

    throw error;
  }
}

/**
 * Register a device for Wake-on-LAN
 *
 * @param {string} deviceName - Friendly name for the device
 * @param {string} macAddress - MAC address
 * @returns {Promise} Registration result
 */
export async function registerDevice(deviceName, macAddress) {
  try {
    // Validate MAC address
    const macPattern = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
    if (!macPattern.test(macAddress)) {
      throw new Error('Invalid MAC address format');
    }

    // Send to backend for storage
    const response = await api.post('/api/wol/register', null, false);
    return response;
  } catch (error) {
    console.error('WoL registration error:', error);
    throw error;
  }
}

/**
 * Get list of registered devices
 *
 * @returns {Promise} List of devices
 */
export async function getRegisteredDevices() {
  try {
    const response = await api.get('/api/wol/devices');
    return response.devices || {};
  } catch (error) {
    console.error('Get WoL devices error:', error);
    throw error;
  }
}

/**
 * Validate MAC address format
 *
 * @param {string} mac - MAC address to validate
 * @returns {boolean} True if valid
 */
export function validateMacAddress(mac) {
  const macPattern = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
  return macPattern.test(mac);
}

/**
 * Format MAC address consistently
 *
 * @param {string} mac - MAC address
 * @param {string} separator - Separator to use (default: ':')
 * @returns {string} Formatted MAC address
 */
export function formatMacAddress(mac, separator = ':') {
  const cleaned = mac.replace(/[:-]/g, '');
  return cleaned.match(/.{1,2}/g).join(separator);
}

/**
 * Get saved devices from localStorage
 *
 * @returns {Array} List of saved devices
 */
export function getSavedDevices() {
  const stored = localStorage.getItem('nexcontrol_wol_devices');
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      return [];
    }
  }
  return [];
}

/**
 * Save device to localStorage
 *
 * @param {Object} device - Device to save {name, mac, ip}
 */
export function saveDevice(device) {
  const devices = getSavedDevices();

  // Check if device already exists
  const existingIndex = devices.findIndex(d => d.name === device.name);
  if (existingIndex >= 0) {
    devices[existingIndex] = device;
  } else {
    devices.push(device);
  }

  localStorage.setItem('nexcontrol_wol_devices', JSON.stringify(devices));
}

/**
 * Remove device from localStorage
 *
 * @param {string} deviceName - Name of device to remove
 */
export function removeDevice(deviceName) {
  const devices = getSavedDevices();
  const filtered = devices.filter(d => d.name !== deviceName);
  localStorage.setItem('nexcontrol_wol_devices', JSON.stringify(filtered));
}

export default {
  sendMagicPacket,
  registerDevice,
  getRegisteredDevices,
  validateMacAddress,
  formatMacAddress,
  getSavedDevices,
  saveDevice,
  removeDevice
};
