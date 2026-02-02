/**
 * Test Setup for Vitest
 */

import { vi } from 'vitest'
import crypto from 'crypto'

// Extend crypto for crypto-js in test environment
// happy-dom already provides crypto, we just ensure it has the needed methods
if (!global.crypto.getRandomValues) {
  global.crypto.getRandomValues = (arr) => {
    const values = crypto.randomBytes(arr.length)
    for (let i = 0; i < arr.length; i++) {
      arr[i] = values[i]
    }
    return arr
  }
}

// Mock Capacitor plugins
vi.mock('@capacitor/app', () => ({
  App: {
    addListener: vi.fn(() => Promise.resolve()),
    removeAllListeners: vi.fn(() => Promise.resolve()),
    getState: vi.fn(() => Promise.resolve({ isActive: true })),
    exitApp: vi.fn(() => Promise.resolve()),
    minimizeApp: vi.fn(() => Promise.resolve())
  }
}))

vi.mock('@capacitor/push-notifications', () => ({
  PushNotifications: {
    requestPermissions: vi.fn(() => Promise.resolve({ receive: 'granted' })),
    checkPermissions: vi.fn(() => Promise.resolve({ receive: 'granted' })),
    register: vi.fn(() => Promise.resolve()),
    unregister: vi.fn(() => Promise.resolve()),
    addListener: vi.fn(() => Promise.resolve()),
    removeAllListeners: vi.fn(() => Promise.resolve())
  }
}))

vi.mock('@capacitor/local-notifications', () => ({
  LocalNotifications: {
    requestPermissions: vi.fn(() => Promise.resolve({ display: 'granted' })),
    checkPermissions: vi.fn(() => Promise.resolve({ display: 'granted' })),
    schedule: vi.fn(() => Promise.resolve()),
    cancel: vi.fn(() => Promise.resolve()),
    getPending: vi.fn(() => Promise.resolve({ notifications: [] })),
    addListener: vi.fn(() => Promise.resolve()),
    removeAllListeners: vi.fn(() => Promise.resolve())
  }
}))

vi.mock('@capacitor/preferences', () => ({
  Preferences: {
    get: vi.fn(() => Promise.resolve({ value: null })),
    set: vi.fn(() => Promise.resolve()),
    remove: vi.fn(() => Promise.resolve()),
    clear: vi.fn(() => Promise.resolve())
  }
}))

vi.mock('@capacitor/device', () => ({
  Device: {
    getInfo: vi.fn(() => Promise.resolve({
      platform: 'web',
      model: 'web',
      osVersion: 'unknown'
    })),
    getLanguageCode: vi.fn(() => Promise.resolve({ value: 'en' })),
    getBatteryInfo: vi.fn(() => Promise.resolve({ batteryLevel: 1 }))
  }
}))

vi.mock('@capacitor/haptics', () => ({
  Haptics: {
    impact: vi.fn(() => Promise.resolve()),
    notification: vi.fn(() => Promise.resolve()),
    selectionStart: vi.fn(() => Promise.resolve()),
    selectionChanged: vi.fn(() => Promise.resolve()),
    selectionEnd: vi.fn(() => Promise.resolve())
  },
  ImpactStyle: {
    Light: 'light',
    Medium: 'medium',
    Heavy: 'heavy'
  }
}))

vi.mock('@capacitor/keyboard', () => ({
  Keyboard: {
    show: vi.fn(() => Promise.resolve()),
    hide: vi.fn(() => Promise.resolve()),
    isVisible: vi.fn(() => Promise.resolve({ isVisible: false }))
  }
}))

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = String(value) },
    removeItem: (key) => { delete store[key] },
    clear: () => { store = {} }
  }
})()

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock
})

// Mock window.location
Object.defineProperty(global, 'window', {
  value: {
    location: {
      hostname: 'localhost',
      href: 'http://localhost:9000/',
      pathname: '/',
      protocol: 'http:',
      search: '',
      hash: ''
    },
    Capacitor: undefined
  }
})
