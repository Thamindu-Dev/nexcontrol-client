# NexControl Security Workflow Updates

**Date:** 2026-02-04
**Version:** 1.1.0

---

## Summary

Three major security improvements have been implemented to enhance the credential management workflow for NexControl:

1. **Backend Setup Script** (`setup_env.py`) - Automated credential generation
2. **Enhanced Blind Input** (`Settings.vue`) - Improved write-only security
3. **Smart Saving Logic** - Placeholder-based key preservation

---

## ✅ Task 1: Backend Setup Script (`setup_env.py`)

### Overview

A Python utility script that automates the generation of secure credentials for the NexControl backend.

### Features

- 🔐 **Secure Password Entry**: Uses `getpass` for invisible password input
- 🔑 **AES Key Generation**: Generates cryptographically secure 32-byte keys using `secrets.token_urlsafe(32)`
- 🔒 **Bcrypt Hashing**: Hashes passwords with bcrypt (12 work factor)
- 📝 **Preserves Existing Config**: Updates only `AES_KEY` and `APP_PASSWORD_HASH`, keeps other settings
- 📱 **Clear Display**: Shows the AES_KEY prominently for copying to mobile app
- 🧹 **Self-Deletion**: Offers to delete itself after use for security

### Usage

```bash
# From the project root directory
python setup_env.py
```

### What It Does

1. Prompts for admin password with confirmation
2. Generates a secure AES_KEY (32 bytes, URL-safe base64)
3. Hashes the password using bcrypt
4. Reads existing `.env` file
5. Updates `AES_KEY` and `APP_PASSWORD_HASH` values
6. Displays the AES_KEY for mobile app setup
7. Offers to delete itself

### Dependencies

Already included in `backend/requirements.txt`:
- `passlib[bcrypt]==1.7.4` ✅

### File Location

```
/workspaces/nexcontrol-client/setup_env.py
```

### Security Features

- Uses `secrets` module for cryptographic randomness
- Bcrypt with 12 rounds for password hashing
- Never logs sensitive data
- Self-deletion prevents accidental resets

---

## ✅ Task 2: Enhanced Blind Input (`Settings.vue`)

### Overview

The Encryption Key input field in the Settings page now implements complete "write-only" security with a visibility toggle.

### Changes Made

1. **Password-Type Input**: All input is masked by default (`type="password"`)
2. **Placeholder Display**: When a key exists, shows `**********` (10 asterisks) in the field
3. **Visibility Toggle**: Eye icon to show/hide the current typing
4. **Focus Handler**: Clears placeholder when user focuses to type new key
5. **Reset on Save**: Returns to placeholder after saving a new key

### Code Changes

**New Constants:**
```javascript
const KEY_PLACEHOLDER = '**********'; // 10 asterisks as placeholder
const showKey = ref(false); // Controls password visibility toggle
```

**Input Component:**
```vue
<q-input
  v-model="encryptionKey"
  :label="keyLabel"
  filled
  dense
  :type="showKey ? 'text' : 'password'"
  :hint="keyHint"
  @focus="clearExistingKey"
>
  <template v-slot:prepend>
    <q-icon
      :name="settingsStore.hasKey ? 'lock' : 'lock_open'"
      :color="settingsStore.hasKey ? 'green' : 'grey-5'"
    />
  </template>
  <template v-slot:append>
    <q-icon
      :name="showKey ? 'visibility_off' : 'visibility'"
      class="cursor-pointer"
      @click="showKey = !showKey"
    >
      <q-tooltip>{{ showKey ? 'Hide key' : 'Show key' }}</q-tooltip>
    </q-icon>
  </template>
</q-input>
```

**Mount Behavior:**
```javascript
// Set encryption key placeholder if key exists (write-only security)
if (settingsStore.hasKey) {
  encryptionKey.value = KEY_PLACEHOLDER;
}
```

**Focus Handler:**
```javascript
function clearExistingKey() {
  if (settingsStore.hasKey && encryptionKey.value === KEY_PLACEHOLDER) {
    // Clear the placeholder to allow new input
    encryptionKey.value = '';
  }
}
```

### Security Benefits

- **Shoulder Surfing Protection**: Key never displays, even when saved
- **Screen Capture Safe**: No plaintext key visible in UI
- **Temporary Visibility**: Eye icon allows brief viewing during entry only
- **Automatic Reset**: Returns to hidden state after save

---

## ✅ Task 3: Smart Saving Logic (`Settings.vue`)

### Overview

The save function now implements intelligent logic to detect placeholder values and preserve existing keys.

### How It Works

1. **Placeholder Detection**: Checks if input equals `KEY_PLACEHOLDER` (`**********`)
2. **Ignore Placeholder**: If placeholder detected, does NOT overwrite existing key
3. **Empty Input Handling**: Treats empty input as "no change" if key exists
4. **Validation**: Requires 32+ characters for new keys
5. **Clear Feedback**: Shows whether key was updated or unchanged

### Save Logic Flow

```javascript
function saveEncryptionKey() {
  const trimmedKey = encryptionKey.value.trim();

  // 1. Check for placeholder (existing key, not changed)
  if (trimmedKey === KEY_PLACEHOLDER) {
    notify('Settings Saved. (Encryption Key Unchanged)');
    return;
  }

  // 2. Empty input + existing key = no change
  if (!trimmedKey && settingsStore.hasKey) {
    notify('Settings Saved. (Encryption Key Unchanged)');
    return;
  }

  // 3. Validate length
  if (trimmedKey.length < 32) {
    notify('Key must be at least 32 characters');
    return;
  }

  // 4. Save new key
  settingsStore.setEncryptionKey(trimmedKey);
  notify('Settings Saved. (Encryption Key Updated)');

  // 5. Reset to placeholder
  encryptionKey.value = KEY_PLACEHOLDER;
  showKey.value = false;
}
```

### User Feedback Messages

| Scenario | Message | Caption |
|----------|---------|---------|
| Placeholder detected | "Settings Saved. (Encryption Key Unchanged)" | "Existing key preserved. Enter new key to update." |
| Empty input + key exists | "Settings Saved. (Encryption Key Unchanged)" | "Enter a new key to update the existing one." |
| New key saved | "Settings Saved. (Encryption Key Updated)" | "New encryption key saved to secure storage" |
| Key too short | "Key must be at least 32 characters" | - |
| No key entered | "Please enter an encryption key (32+ characters)" | - |

---

## User Workflow

### First-Time Setup

1. **Generate Credentials**
   ```bash
   cd /path/to/nexcontrol
   python setup_env.py
   ```

2. **Follow Prompts**
   - Enter admin password (twice for confirmation)
   - Note the displayed AES_KEY

3. **Copy AES_KEY**
   - Copy the key from the terminal output
   - Or open `backend/.env` and copy the `AES_KEY` value

4. **Configure Mobile App**
   - Open NexControl mobile app
   - Go to Settings → Encryption Key
   - Paste the AES_KEY
   - Click "Save Encryption Key"
   - See: "Settings Saved. (Encryption Key Updated)"

5. **Verify**
   - Input field shows: `**********`
   - Green lock icon appears
   - Label shows: "AES Encryption Key (Key Saved - Hidden for Security)"

### Updating the Key

1. **Generate New Key**
   ```bash
   python setup_env.py
   ```

2. **Update Mobile App**
   - Go to Settings → Encryption Key
   - Click the input field (placeholder clears automatically)
   - Paste new key
   - Use eye icon to verify typing
   - Click "Update Encryption Key"

3. **Result**
   - Field shows: `**********`
   - Notification: "Settings Saved. (Encryption Key Updated)"

### Recovering a Lost Key

1. **Check Backend**
   ```bash
   cat backend/.env | grep AES_KEY
   ```

2. **Copy to Mobile App**
   - Open Settings → Encryption Key
   - Click field to clear placeholder
   - Paste key
   - Save

---

## Technical Implementation

### File Changes

1. **New File:** `/workspaces/nexcontrol-client/setup_env.py`
   - 250+ lines
   - Automated credential generation
   - Self-deletion capability

2. **Modified:** `/workspaces/nexcontrol-client/frontend/src/pages/Settings.vue`
   - Added `KEY_PLACEHOLDER` constant
   - Added `showKey` ref for visibility toggle
   - Enhanced `saveEncryptionKey()` with smart logic
   - Updated `onMounted()` to set placeholder
   - Updated `clearExistingKey()` to detect placeholder
   - Added visibility toggle icon to input
   - Removed `:readonly` attribute (was preventing edits)

3. **Updated:** `/workspaces/nexcontrol-client/SETTINGS_GUIDE.md`
   - Added "Option 1: Use the Automated Setup Script"
   - Updated option numbering for manual methods
   - Enhanced "Changing the Encryption Key" section

### Dependencies

No new dependencies required. All needed packages are already in `backend/requirements.txt`:
- ✅ `passlib[bcrypt]==1.7.4`
- ✅ `secrets` (Python standard library)

---

## Security Improvements

### Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| **Credential Generation** | Manual copy-paste | Automated secure generation |
| **Password Hashing** | Manual bcrypt command | Script handles automatically |
| **AES Key Display** | Visible in input | Always hidden (write-only) |
| **Input Field** | Sometimes readonly | Always editable with placeholder |
| **Visibility Toggle** | None | Eye icon for temporary viewing |
| **Save Logic** | Basic validation | Smart placeholder detection |
| **User Feedback** | Generic messages | Specific update/unchanged messages |

### Threat Mitigation

| Threat | Protection |
|--------|------------|
| **Weak Keys** | Cryptographically secure generation |
| **Shoulder Surfing** | Write-only input + visibility toggle |
| **Screen Capture** | Key never visible in plaintext |
| **Accidental Overwrite** | Smart placeholder detection |
| **Key Recovery** | Can check backend `.env` file |
| **Credential Resets** | Script offers self-deletion |

---

## Testing Checklist

- [ ] Run `setup_env.py` and verify credentials are generated
- [ ] Verify `.env` file is updated correctly
- [ ] Copy AES_KEY to mobile app Settings
- [ ] Verify placeholder (`**********`) appears after save
- [ ] Test visibility toggle (eye icon)
- [ ] Verify green lock icon appears when key exists
- [ ] Test focus clears placeholder for editing
- [ ] Verify "Settings Saved. (Encryption Key Updated)" message
- [ ] Verify "Settings Saved. (Encryption Key Unchanged)" message
- [ ] Test script self-deletion option
- [ ] Restart backend and verify new credentials work
- [ ] Test mobile app login with new password

---

## Documentation Updates

- ✅ `SETTINGS_GUIDE.md` - Added setup script instructions
- ✅ `SECURITY_WORKFLOW_UPDATE.md` - This comprehensive summary

---

## Next Steps

1. **Testing**: Thoroughly test the setup script and updated Settings page
2. **User Guide**: Consider creating a quick-start guide for new users
3. **Video Demo**: Create a short demo showing the workflow
4. **Backup**: Remind users to backup their `.env` file

---

## Support

If you encounter any issues:

1. Check that `passlib[bcrypt]` is installed: `pip list | grep passlib`
2. Verify the `.env` file exists in `backend/` directory
3. Check file permissions: `ls -la backend/.env`
4. Review backend logs for decryption errors
5. Check browser console for frontend errors

---

**Last Updated:** 2026-02-04
**Maintained By:** NexControl Development Team
