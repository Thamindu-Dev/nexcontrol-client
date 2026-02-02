/**
 * Tests for EnvConfig
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { getApiBaseUrl, getWebSocketUrl, isDevelopment, isProduction } from './EnvConfig'

describe('EnvConfig', () => {
  let originalLocation

  beforeEach(() => {
    originalLocation = { ...window.location }
    vi.stubGlobal('import', {
      meta: {
        env: {}
      }
    })
  })

  afterEach(() => {
    Object.defineProperty(window, 'location', { value: originalLocation })
    localStorage.clear()
  })

  describe('getApiBaseUrl', () => {
    it('should return localhost URL in development', () => {
      const url = getApiBaseUrl()
      expect(url).toBe('http://localhost:8000')
    })

    it('should use custom config from localStorage', () => {
      localStorage.setItem('nexcontrol_server_config', JSON.stringify({
        protocol: 'https',
        host: 'example.com',
        port: 443
      }))

      const url = getApiBaseUrl()
      expect(url).toBe('https://example.com:443')
    })

    it('should return empty string in Codespaces', () => {
      Object.defineProperty(window, 'location', {
        value: {
          hostname: 'test.app.github.dev'
        }
      })

      const url = getApiBaseUrl()
      expect(url).toBe('')
    })
  })

  describe('getWebSocketUrl', () => {
    it('should return ws://localhost for development', () => {
      const url = getWebSocketUrl()
      expect(url).toBe('ws://localhost:8000/ws')
    })

    it('should use custom config from localStorage', () => {
      localStorage.setItem('nexcontrol_server_config', JSON.stringify({
        protocol: 'https',
        host: 'example.com',
        port: 443
      }))

      const url = getWebSocketUrl()
      expect(url).toBe('wss://example.com:443/ws')
    })
  })

  describe('isDevelopment', () => {
    it('should return true in development', () => {
      expect(isDevelopment()).toBe(true)
    })
  })

  describe('isProduction', () => {
    it('should return false in development', () => {
      expect(isProduction()).toBe(false)
    })
  })
})
