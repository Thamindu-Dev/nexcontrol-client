/**
 * =============================================================
 * EncryptionService - AES-256-GCM Encryption/Decryption
 * =============================================================
 * Handles encryption of API payloads using AES-256-GCM
 * Compatible with the backend's encryption implementation
 *
 * Format:
 * - Nonce: 12 bytes (96-bit)
 * - Ciphertext: variable length
 * - Tag: 16 bytes (128-bit) - automatically appended by GCM
 *
 * The encrypted data is sent as base64(nonce + ciphertext)
 */

import CryptoJS from 'crypto-js';

// Configuration
const AES_KEY_SIZE = 32; // 256 bits
const TIMESTAMP_TOLERANCE = 30; // seconds

/**
 * Get the AES key (must match backend)
 * In production, this should be stored securely
 */
function getAESKey() {
  // This key MUST match the backend's AES_KEY
  // For now, using the same default as backend
  // In production, load from secure storage
  const defaultKey = 'NexControl-AES-Key-32-Bytes-Change!!';

  // Try to get from localStorage (user configurable)
  const storedKey = localStorage.getItem('nexcontrol_aes_key');
  return storedKey || defaultKey.substring(0, AES_KEY_SIZE);
}

/**
 * Encrypt data using AES-256-GCM
 *
 * @param {Object} data - Data to encrypt
 * @returns {Object} Encrypted payload with data and timestamp
 */
export function encryptPayload(data) {
  try {
    // Convert data to JSON string
    const jsonStr = JSON.stringify(data);

    // Generate random nonce (12 bytes)
    const nonce = CryptoJS.lib.WordArray.random(128 / 8);

    // Get the key
    const key = CryptoJS.enc.Utf8.parse(getAESKey());

    // Encrypt using AES
    const encrypted = CryptoJS.AES.encrypt(jsonStr, key, {
      mode: CryptoJS.mode.GCM,
      padding: CryptoJS.pad.Pkcs7,
      iv: nonce
    });

    // Combine nonce + ciphertext
    const combined = CryptoJS.lib.WordArray.create([nonce, encrypted.ciphertext]);

    // Convert to base64
    const encryptedBase64 = CryptoJS.enc.Base64.stringify(combined);

    // Add timestamp for replay attack prevention
    return {
      data: encryptedBase64,
      timestamp: Math.floor(Date.now() / 1000)
    };
  } catch (error) {
    console.error('Encryption error:', error);
    throw new Error('Failed to encrypt payload');
  }
}

/**
 * Decrypt response from backend
 *
 * @param {Object} encryptedResponse - Response with encrypted data
 * @returns {Object} Decrypted data
 */
export function decryptResponse(encryptedResponse) {
  try {
    // Handle both direct data and wrapped responses
    const encryptedData = encryptedResponse.data || encryptedResponse;

    if (!encryptedData) {
      throw new Error('No encrypted data in response');
    }

    // Decode from base64
    const combined = CryptoJS.enc.Base64.parse(encryptedData);

    // Split nonce and ciphertext
    // Nonce is first 12 bytes, rest is ciphertext
    const nonce = CryptoJS.lib.WordArray.create(combined.words.slice(0, 3)); // 3 words = 12 bytes
    const ciphertext = CryptoJS.lib.WordArray.create(combined.words.slice(3));

    // Get the key
    const key = CryptoJS.enc.Utf8.parse(getAESKey());

    // Decrypt using AES
    const decrypted = CryptoJS.AES.decrypt(
      { ciphertext: ciphertext },
      key,
      {
        mode: CryptoJS.mode.GCM,
        padding: CryptoJS.pad.Pkcs7,
        iv: nonce
      }
    );

    // Convert to UTF-8 string
    const jsonStr = decrypted.toString(CryptoJS.enc.Utf8);

    // Parse JSON
    return JSON.parse(jsonStr);
  } catch (error) {
    console.error('Decryption error:', error);
    throw new Error('Failed to decrypt response');
  }
}

/**
 * Validate timestamp for replay attack prevention
 *
 * @param {number} timestamp - Unix timestamp from request/response
 * @returns {boolean} True if timestamp is valid
 */
export function validateTimestamp(timestamp) {
  const currentTime = Math.floor(Date.now() / 1000);
  const timeDiff = Math.abs(currentTime - timestamp);

  return timeDiff <= TIMESTAMP_TOLERANCE;
}

/**
 * Set the AES key (for user configuration)
 *
 * @param {string} key - AES key (at least 32 characters)
 */
export function setAESKey(key) {
  if (key && key.length >= 32) {
    localStorage.setItem('nexcontrol_aes_key', key.substring(0, 32));
    return true;
  }
  return false;
}

/**
 * Get the current AES key
 *
 * @returns {string} Current AES key
 */
export function getCurrentAESKey() {
  return getAESKey();
}

export default {
  encryptPayload,
  decryptResponse,
  validateTimestamp,
  setAESKey,
  getCurrentAESKey
};
