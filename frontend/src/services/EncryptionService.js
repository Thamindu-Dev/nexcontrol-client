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
 * EncryptionService - AES-256-GCM Encryption/Decryption
 * =============================================================
 * Handles encryption of API payloads using AES-256-GCM
 * Compatible with the backend's encryption implementation
 *
 * Uses Web Crypto API when available (localhost/HTTPS)
 * Falls back to crypto-js for local network IP access
 *
 * Format:
 * - Nonce: 12 bytes (96-bit)
 * - Ciphertext: variable length
 * - Tag: 16 bytes (128-bit) - appended to ciphertext
 *
 * The encrypted data is sent as base64(nonce + ciphertext + tag)
 */

import CryptoJS from 'crypto-js';

// Configuration
const AES_KEY_SIZE = 32; // 256 bits
const NONCE_SIZE = 12; // 96 bits for GCM
const TIMESTAMP_TOLERANCE = 30; // seconds

// Check if Web Crypto API is available
// Web Crypto API works in: HTTPS, localhost, and Capacitor apps (capacitor://)
const isSecureContext = typeof window !== 'undefined' &&
  (window.location.protocol === 'https:' ||
   window.location.protocol === 'capacitor:' ||
   window.location.protocol === 'ionic:' ||
   window.location.hostname === 'localhost' ||
   window.location.hostname === '127.0.0.1' ||
   // Check if running in Capacitor
   (window.Capacitor?.getPlatform() !== undefined));

const useWebCrypto = isSecureContext &&
  typeof crypto !== 'undefined' &&
  crypto.subtle;

console.log('[EncryptionService] Protocol:', window.location.protocol);
console.log('[EncryptionService] Secure context:', isSecureContext);
console.log('[EncryptionService] Using', useWebCrypto ? 'Web Crypto API' : 'crypto-js');

/**
 * Get the AES key (must match backend)
 * In production, this should be stored securely
 */
function getAESKey() {
  // This key MUST match the backend's AES_KEY
  // Loaded from .env (VITE_AES_KEY)
  const defaultKey = import.meta.env.VITE_AES_KEY;

  if (!defaultKey) {
    console.error('Encryption Key (VITE_AES_KEY) not found in environment variables!');
  }

  // Try to get from localStorage (user configurable)
  const storedKey = localStorage.getItem('nexcontrol_aes_key');
  return storedKey || (defaultKey ? defaultKey.substring(0, AES_KEY_SIZE) : '');
}

// ============================================================================
// Web Crypto API Implementation (for localhost/HTTPS)
// ============================================================================

async function importKeyWebCrypto(keyString) {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(keyString.substring(0, AES_KEY_SIZE));

  return await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToArrayBuffer(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

async function encryptWebCrypto(data) {
  const jsonStr = JSON.stringify(data);
  const encoder = new TextEncoder();
  const plaintext = encoder.encode(jsonStr);

  const nonce = crypto.getRandomValues(new Uint8Array(NONCE_SIZE));
  const key = await importKeyWebCrypto(getAESKey());

  const ciphertextWithTag = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: nonce },
    key,
    plaintext
  );

  const combined = new Uint8Array(nonce.length + ciphertextWithTag.byteLength);
  combined.set(nonce, 0);
  combined.set(new Uint8Array(ciphertextWithTag), nonce.length);

  return arrayBufferToBase64(combined.buffer);
}

async function decryptWebCrypto(encryptedData) {
  try {
    console.log('[WebCrypto] Decrypting data');
    const combined = base64ToArrayBuffer(encryptedData);
    const nonce = combined.slice(0, NONCE_SIZE);
    const ciphertextWithTag = combined.slice(NONCE_SIZE);
    const key = await importKeyWebCrypto(getAESKey());

    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: new Uint8Array(nonce) },
      key,
      ciphertextWithTag
    );

    const decoder = new TextDecoder();
    const result = JSON.parse(decoder.decode(decrypted));
    console.log('[WebCrypto] Decryption successful');
    return result;
  } catch (error) {
    console.error('[WebCrypto] Decryption failed:', error);
    throw error;
  }
}

// ============================================================================
// crypto-js Implementation (for local network IP access)
// ============================================================================

function encryptCryptoJS(data) {
  const jsonStr = JSON.stringify(data);
  const nonce = CryptoJS.lib.WordArray.random(NONCE_SIZE);
  const key = CryptoJS.enc.Utf8.parse(getAESKey());

  // Encrypt using AES-GCM
  const encrypted = CryptoJS.AES.encrypt(jsonStr, key, {
    mode: CryptoJS.mode.GCM,
    padding: CryptoJS.pad.Pkcs7,
    iv: nonce
  });

  // crypto-js stores tag separately - we need to append it
  const ciphertextWithTag = CryptoJS.lib.WordArray.create([
    encrypted.ciphertext,
    encrypted.tag
  ]);

  const combined = CryptoJS.lib.WordArray.create([nonce, ciphertextWithTag]);
  return CryptoJS.enc.Base64.stringify(combined);
}

function decryptCryptoJS(encryptedData) {
  try {
    console.log('[CryptoJS] Decrypting data, length:', encryptedData.length);
    const combined = CryptoJS.enc.Base64.parse(encryptedData);
    console.log('[CryptoJS] Combined words:', combined.words.length);

    const nonceWords = 3; // 12 bytes / 4 bytes per word
    const tagWords = 4; // 16 bytes / 4 bytes per word

    if (combined.words.length < nonceWords + tagWords) {
      throw new Error(`Encrypted data too short: ${combined.words.length} words`);
    }

    const nonce = CryptoJS.lib.WordArray.create(combined.words.slice(0, nonceWords));
    const ciphertextWithTag = CryptoJS.lib.WordArray.create(combined.words.slice(nonceWords));

    const ciphertext = CryptoJS.lib.WordArray.create(ciphertextWithTag.words.slice(0, -tagWords));
    const tag = CryptoJS.lib.WordArray.create(ciphertextWithTag.words.slice(-tagWords));

    const key = CryptoJS.enc.Utf8.parse(getAESKey());
    console.log('[CryptoJS] Key length:', key.words.length * 4, 'bytes');

    const decrypted = CryptoJS.AES.decrypt(
      { ciphertext: ciphertext, tag: tag },
      key,
      { mode: CryptoJS.mode.GCM, padding: CryptoJS.pad.Pkcs7, iv: nonce }
    );

    const jsonStr = decrypted.toString(CryptoJS.enc.Utf8);
    if (!jsonStr) throw new Error('Decryption produced empty result');
    console.log('[CryptoJS] Decryption successful');
    return JSON.parse(jsonStr);
  } catch (error) {
    console.error('[CryptoJS] Decryption failed:', error);
    throw error;
  }
}

// ============================================================================
// Public API
// ============================================================================

/**
 * Encrypt data using AES-256-GCM
 * Compatible with Python's cryptography library
 *
 * @param {Object} data - Data to encrypt
 * @returns {Promise<Object>} Encrypted payload with data and timestamp
 */
export async function encryptPayload(data) {
  try {
    let encryptedBase64;

    if (useWebCrypto) {
      encryptedBase64 = await encryptWebCrypto(data);
    } else {
      encryptedBase64 = encryptCryptoJS(data);
    }

    return {
      data: encryptedBase64,
      timestamp: Math.floor(Date.now() / 1000)
    };
  } catch (error) {
    console.error('[EncryptionService] Encryption error:', error);
    throw new Error('Failed to encrypt payload: ' + error.message);
  }
}

/**
 * Decrypt response from backend
 * Compatible with Python's cryptography library
 *
 * @param {Object} encryptedResponse - Response with encrypted data
 * @returns {Promise<Object>} Decrypted data
 */
export async function decryptResponse(encryptedResponse) {
  const encryptedData = encryptedResponse.data || encryptedResponse;

  if (!encryptedData) {
    throw new Error('No encrypted data in response');
  }

  console.log('[EncryptionService] Decrypting, using WebCrypto:', useWebCrypto);

  // Try primary method
  try {
    if (useWebCrypto) {
      return await decryptWebCrypto(encryptedData);
    } else {
      return decryptCryptoJS(encryptedData);
    }
  } catch (primaryError) {
    console.error('[EncryptionService] Primary decryption failed:', primaryError);

    // If WebCrypto failed and crypto-js is available, try it as fallback
    if (useWebCrypto && typeof CryptoJS !== 'undefined') {
      console.log('[EncryptionService] Falling back to crypto-js');
      try {
        return decryptCryptoJS(encryptedData);
      } catch (fallbackError) {
        console.error('[EncryptionService] Fallback also failed:', fallbackError);
      }
    }

    // If we get here, both methods failed
    if (primaryError.name === 'OperationError') {
      throw new Error('Decryption failed: Encryption key mismatch or corrupted data');
    }

    throw new Error('Failed to decrypt response: ' + (primaryError.message || 'Unknown error'));
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
