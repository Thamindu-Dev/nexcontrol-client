/**
 * Tests for EncryptionService
 */

import { describe, it, expect } from 'vitest'
import { encryptPayload, decryptResponse } from './EncryptionService'

describe('EncryptionService', () => {
  describe('encryptPayload', () => {
    it('should encrypt a simple payload', () => {
      const payload = { test: 'data', number: 123 }
      const encrypted = encryptPayload(payload)

      expect(encrypted).toHaveProperty('data')
      expect(encrypted.data).toBeTruthy()
      expect(encrypted.data).not.toEqual(JSON.stringify(payload))
    })

    it('should produce different output for same input', () => {
      const payload = { test: 'data' }
      const encrypted1 = encryptPayload(payload)
      const encrypted2 = encryptPayload(payload)

      // Due to random IV, encrypted data should be different
      expect(encrypted1.data).not.toEqual(encrypted2.data)
    })

    it('should handle nested objects', () => {
      const payload = {
        user: { name: 'Test', email: 'test@example.com' },
        settings: { theme: 'dark' }
      }
      const encrypted = encryptPayload(payload)

      expect(encrypted).toHaveProperty('data')
    })

    it('should handle arrays', () => {
      const payload = { items: [1, 2, 3, 4, 5] }
      const encrypted = encryptPayload(payload)

      expect(encrypted).toHaveProperty('data')
    })
  })

  describe('decryptResponse', () => {
    it('should decrypt an encrypted payload', () => {
      const original = { test: 'data', number: 123 }
      const encrypted = encryptPayload(original)
      const decrypted = decryptResponse(encrypted)

      expect(decrypted).toEqual(original)
    })

    it('should handle complex nested objects', () => {
      const original = {
        user: { name: 'Test', email: 'test@example.com' },
        settings: { theme: 'dark', notifications: true },
        items: [1, 2, 3]
      }
      const encrypted = encryptPayload(original)
      const decrypted = decryptResponse(encrypted)

      expect(decrypted).toEqual(original)
    })

    it('should return null for invalid data', () => {
      const result = decryptResponse({ invalid: true })
      expect(result).toBeNull()
    })

    it('should return null for malformed data', () => {
      const result = decryptResponse({ data: 'invalid-base64' })
      expect(result).toBeNull()
    })
  })

  describe('encrypt/decrypt roundtrip', () => {
    it('should maintain data integrity through roundtrip', () => {
      const testCases = [
        { simple: 'string' },
        { number: 42, float: 3.14 },
        { bool: true, false: false },
        { null: null },
        { array: [1, 2, 'three', { four: 4 }] },
        {
          nested: {
            deeply: {
              value: 'test'
            }
          }
        }
      ]

      testCases.forEach((original) => {
        const encrypted = encryptPayload(original)
        const decrypted = decryptResponse(encrypted)
        expect(decrypted).toEqual(original)
      })
    })
  })
})
