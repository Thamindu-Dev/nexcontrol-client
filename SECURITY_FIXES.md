# Security Fixes for NexControl

## Critical Fixes (Required Before Deployment)

### Fix 1: Router Guard Async Bug (HIGH PRIORITY)
**File:** `src/router/index.js`

The current router guard has a race condition where it doesn't properly wait for token verification.

**Current (BUGGY):**
```javascript
Router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth !== false) {
    if (!authStore.isAuthenticated) {
      next('/login')
    } else {
      authStore.verifyToken().then(isValid => {
        if (isValid) {
          next()
        } else {
          next('/login')
        }
      })
      // BUG: Guard continues here without waiting!
    }
  } else {
    next()
  }
})
```

**Fixed:**
```javascript
Router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth !== false) {
    if (!authStore.isAuthenticated) {
      next('/login')
      return
    }

    // Properly await token verification
    const isValid = await authStore.verifyToken()
    if (isValid) {
      next()
    } else {
      next('/login')
    }
  } else {
    next()
  }
})
```

---

### Fix 2: Add Input Validation for Server Config
**File:** `src/pages/Settings.vue`

Add validation to prevent SSRF attacks:

```javascript
// Add to script setup
function isValidIP(ip) {
  // Check for private IP ranges
  const privateRanges = [
    /^10\./,
    /^172\.(1[6-9]|2\d|3[01])\./,
    /^192\.168\./,
    /^127\./,
    /^localhost$/i
  ]

  return privateRanges.some(range => range.test(ip))
}

function isValidPort(port) {
  return port >= 1 && port <= 65535
}

// In your save handler
async function saveServerConfig() {
  if (!isValidIP(serverConfig.host)) {
    $q.notify({
      type: 'negative',
      message: 'Invalid IP address. Must be a local network IP.'
    })
    return
  }

  if (!isValidPort(serverConfig.port)) {
    $q.notify({
      type: 'negative',
      message: 'Invalid port. Must be between 1-65535.'
    })
    return
  }

  // Save config...
}
```

---

### Fix 3: Add Token Expiration Check
**File:** `src/stores/auth.js`

```javascript
// Add to auth store
actions: {
  /**
   * Decode JWT and check expiration
   */
  isTokenExpired(token) {
    if (!token) return true

    try {
      // JWT format: header.payload.signature
      const parts = token.split('.')
      if (parts.length !== 3) return true

      const payload = JSON.parse(atob(parts[1]))
      const now = Math.floor(Date.now() / 1000)

      // Check if token is expired or will expire in next 5 minutes
      return payload.exp < (now - 300)
    } catch {
      return true
    }
  },

  async verifyToken() {
    if (!this.token) {
      this.isAuthenticated = false
      return false
    }

    // Check token expiration
    if (this.isTokenExpired(this.token)) {
      this.token = null
      this.isAuthenticated = false
      this.serverConnected = false
      return false
    }

    try {
      await api.get('/api/auth/verify')
      this.isAuthenticated = true
      this.serverConnected = true
      return true
    } catch {
      this.token = null
      this.isAuthenticated = false
      this.serverConnected = false
      return false
    }
  }
}
```

---

### Fix 4: Rate Limiting for Login
**File:** `src/pages/Login.vue`

```javascript
// Add to component
const loginAttempts = ref(0)
const lastAttemptTime = ref(0)
const LOCKOUT_DURATION = 5 * 60 * 1000 // 5 minutes
const MAX_ATTEMPTS = 5

async function handleLogin() {
  // Check if locked out
  if (loginAttempts.value >= MAX_ATTEMPTS) {
    const timeSinceLastAttempt = Date.now() - lastAttemptTime.value
    if (timeSinceLastAttempt < LOCKOUT_DURATION) {
      const remainingTime = Math.ceil((LOCKOUT_DURATION - timeSinceLastAttempt) / 1000 / 60)
      loginError.value = `Too many attempts. Try again in ${remainingTime} minutes.`
      return
    } else {
      // Reset attempts after lockout period
      loginAttempts.value = 0
    }
  }

  loading.value = true
  loginError.value = null

  try {
    await settingsStore.updateServer(serverConfig)
    const result = await authStore.login(password.value)

    if (result.success) {
      // Reset attempts on successful login
      loginAttempts.value = 0

      $q.notify({
        type: 'positive',
        message: 'Connected successfully!',
        position: 'top'
      })

      router.push('/dashboard')
    } else {
      // Increment failed attempts
      loginAttempts.value++
      lastAttemptTime.value = Date.now()
      loginError.value = result.error || 'Login failed'
    }
  } catch (error) {
    loginAttempts.value++
    lastAttemptTime.value = Date.now()
    // ... error handling
  } finally {
    loading.value = false
  }
}
```

---

### Fix 5: Remove Cleartext HTTP (Production)
**File:** `capacitor.config.json`

For production, disable cleartext traffic:

```json
{
  "server": {
    "androidScheme": "https",
    "cleartext": false,  // Changed from true
    "allowNavigation": [
      "http://localhost:*",
      "https://*"
    ]
  }
}
```

**Note:** Since this is a local network app, you may need HTTP for development.
Consider adding a build flag to control this.

---

### Fix 6: Sanitize Error Messages
**File:** `src/services/ApiService.js`

```javascript
function handleApiError(response, errorData) {
  // Handle 401 Unauthorized
  if (response.status === 401) {
    clearToken()
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    throw new Error('Authentication required')
  }

  // Handle 403 Forbidden
  if (response.status === 403) {
    throw new Error('Access denied')
  }

  // Handle 404 Not Found
  if (response.status === 404) {
    throw new Error('Resource not found')
  }

  // Handle 500 Server Error
  if (response.status >= 500) {
    throw new Error('Server error. Please try again later.')
  }

  // Generic error - don't leak backend details
  throw new Error('Request failed')
}
```

---

### Fix 7: Add Content Security Policy
**File:** `index.html` or `quasar.config.js`

Add to `quasar.config.js`:

```javascript
build: {
  extendViteConf(viteConf) {
    viteConf.server = viteConf.server || {}
    viteConf.server.proxy = viteConf.server.proxy || {}
    viteConf.server.proxy['/api'] = {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }

    // Add CSP headers for development
    viteConf.server.headers = viteConf.server.headers || {}
    viteConf.server.headers['Content-Security-Policy'] =
      "default-src 'self'; " +
      "script-src 'self' 'unsafe-inline'; " +
      "style-src 'self' 'unsafe-inline'; " +
      "img-src 'self' data:; " +
      "connect-src 'self' http://localhost:* ws://localhost:*; " +
      "font-src 'self';"
  }
}
```

---

### Fix 8: Remove Console Logs in Production
**File:** Multiple files

Create a production-safe logger:

```javascript
// src/services/Logger.js
const isDevelopment = import.meta.env.DEV

export const logger = {
  error: (...args) => {
    if (isDevelopment) {
      console.error('[ERROR]', ...args)
    }
    // In production, send to error tracking service
  },
  warn: (...args) => {
    if (isDevelopment) {
      console.warn('[WARN]', ...args)
    }
  },
  info: (...args) => {
    if (isDevelopment) {
      console.log('[INFO]', ...args)
    }
  }
}

// Replace all console.error with logger.error
```

---

## Recommended Improvements (Not Critical)

### 1. Add Request Nonce for Replay Protection
```javascript
// Generate unique nonce for each request
const generateNonce = () => crypto.randomUUID()

// Include in encrypted payload
{
  data: encryptedBase64,
  timestamp: Date.now(),
  nonce: generateNonce()
}
```

### 2. Implement CSRF Tokens
```javascript
// On first request, get CSRF token from server
// Include in all subsequent requests
headers: {
  'X-CSRF-Token': csrfToken
}
```

### 3. Use Secure Storage for Keys
Generate unique AES key per installation:

```javascript
// On first launch
async function generateAndStoreKey() {
  const key = CryptoJS.lib.WordArray.random(32).toString()
  await setSecureItem('aes_key', key)
}
```

---

## Deployment Checklist

Before deploying to users:

- [ ] Fix router guard async bug
- [ ] Add IP/port validation
- [ ] Implement token expiration check
- [ ] Add login rate limiting
- [ ] Review cleartext HTTP setting
- [ ] Sanitize all error messages
- [ ] Remove production console logs
- [ ] Add Content Security Policy
- [ ] Change default AES key or require user to set one
- [ ] Add security documentation for users

---

## Priority Order

1. **Router Guard Bug** - Immediate fix, allows auth bypass
2. **Input Validation** - Prevents SSRF attacks
3. **Token Expiration** - Prevents indefinite token usage
4. **Rate Limiting** - Prevents brute force
5. **Error Sanitization** - Prevents information leakage
6. **Console Logs** - Prevents information leakage
7. **CSP** - XSS protection
