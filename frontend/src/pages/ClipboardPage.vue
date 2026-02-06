<!--
  ==============================================================================
  NexControl - Remote PC Controller
  Copyright (C) 2026 Thamindu-Dev

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
  ==============================================================================
-->
<template>
  <q-page class="clipboard-page bg-black q-pa-md">
    <!-- Page Header -->
    <div class="row items-center q-mb-xl">
      <q-icon name="content_copy" size="28px" color="cyan" class="q-mr-md" />
      <div class="text-h5 text-white text-weight-bold">Clipboard Sync</div>
    </div>

    <!-- Top Section: From PC (Incoming) -->
    <div class="clipboard-section q-mb-lg">
      <div class="row items-center q-mb-md">
        <q-icon name="computer" size="20px" color="cyan" class="q-mr-sm" />
        <div class="text-subtitle1 text-white text-weight-medium">PC Clipboard</div>
        <q-space />
        <q-badge v-if="pcText" :label="`${pcText.length} chars`" color="cyan" transparent />
      </div>

      <q-input
        v-model="pcText"
        type="textarea"
        readonly
        outlined
        dark
        color="cyan"
        input-class="text-white"
        label-color="grey"
        placeholder="Click Refresh to load clipboard content from PC..."
        class="clipboard-input"
        rows="6"
      />

      <div class="row q-gutter-sm q-mt-md">
        <q-btn
          outline
          color="white"
          icon="refresh"
          label="Refresh"
          :loading="loadingPC"
          @click="fetchFromPC"
          no-caps
        />
        <q-btn
          outline
          color="cyan"
          icon="content_copy"
          label="Copy to Phone"
          :disable="!pcText"
          @click="copyToPhone"
          no-caps
        />
      </div>
    </div>

    <!-- Separator -->
    <q-separator dark class="q-my-lg" style="background: #333333;" />

    <!-- Bottom Section: Send to PC (Outgoing) -->
    <div class="clipboard-section">
      <div class="row items-center q-mb-md">
        <q-icon name="smartphone" size="20px" color="cyan" class="q-mr-sm" />
        <div class="text-subtitle1 text-white text-weight-medium">Send to PC</div>
        <q-space />
        <q-badge v-if="phoneText" :label="`${phoneText.length} chars`" color="cyan" transparent />
      </div>

      <q-input
        v-model="phoneText"
        type="textarea"
        outlined
        dark
        color="cyan"
        input-class="text-white"
        label-color="grey"
        placeholder="Type or paste text here to send to PC..."
        class="clipboard-input"
        rows="6"
      />

      <div class="row q-gutter-sm q-mt-md">
        <q-btn
          outline
          color="cyan"
          icon="send"
          label="Push to PC"
          :loading="sending"
          :disable="!phoneText || sending"
          @click="sendToPC"
          no-caps
        />
        <q-btn
          outline
          color="grey-7"
          icon="backspace"
          label="Clear"
          :disable="!phoneText"
          @click="phoneText = ''"
          no-caps
        />
      </div>
    </div>

    <!-- Directional Arrow (Visual Flow Indicator) -->
    <div class="row justify-center q-my-lg">
      <q-icon name="arrow_downward" size="32px" color="grey-6" />
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue';
import { useQuasar, copyToClipboard } from 'quasar';
import api from '../services/ApiService';
import { secureNotify } from '../services/NotifyService';

// Define component name
defineOptions({
  name: 'ClipboardPage'
});

const $q = useQuasar();

// State
const pcText = ref('');
const phoneText = ref('');
const loadingPC = ref(false);
const sending = ref(false);

/**
 * Fetch clipboard content from PC
 */
async function fetchFromPC() {
  loadingPC.value = true;

  try {
    const response = await api.get('/api/clipboard');

    if (response.success && response.text) {
      pcText.value = response.text;
      secureNotify.success($q, 'Clipboard content loaded from PC');
    } else {
      secureNotify.error($q, response.message || 'Failed to fetch clipboard');
    }
  } catch (error) {
    console.error('[Clipboard] Error fetching from PC:', error);
    secureNotify.error($q, error.message || 'Failed to fetch clipboard');
  } finally {
    loadingPC.value = false;
  }
}

/**
 * Copy PC clipboard content to phone's local clipboard
 */
function copyToPhone() {
  if (!pcText.value) {
    secureNotify.error($q, 'No content to copy');
    return;
  }

  copyToClipboard(pcText.value)
    .then(() => {
      secureNotify.success($q, 'Copied to phone clipboard');
      // Haptic feedback on mobile
      if (navigator.vibrate) {
        navigator.vibrate(50);
      }
    })
    .catch(() => {
      secureNotify.error($q, 'Failed to copy to clipboard');
    });
}

/**
 * Send text from phone to PC clipboard
 */
async function sendToPC() {
  if (!phoneText.value) {
    secureNotify.error($q, 'Please enter text to send');
    return;
  }

  sending.value = true;

  try {
    const response = await api.post('/api/clipboard', {
      text: phoneText.value
    });

    if (response.success) {
      secureNotify.success($q, response.message || 'Sent to PC clipboard');
      phoneText.value = ''; // Clear after successful send
      // Haptic feedback
      if (navigator.vibrate) {
        navigator.vibrate([50, 50, 50]); // Triple vibration pattern
      }
    } else {
      secureNotify.error($q, response.message || 'Failed to send to PC');
    }
  } catch (error) {
    console.error('[Clipboard] Error sending to PC:', error);
    secureNotify.error($q, error.message || 'Failed to send to PC');
  } finally {
    sending.value = false;
  }
}
</script>

<style scoped>
.clipboard-page {
  min-height: 100vh;
}

.clipboard-section {
  /* Transparent container with no background */
}

.clipboard-input :deep(.q-field__control) {
  background: transparent !important;
  border: 1px solid #FFFFFF !important;
  border-radius: 8px !important;
  color: #FFFFFF !important;
  transition: all 0.2s ease;
}

.clipboard-input :deep(.q-field__control:hover) {
  border-color: #22d3ee !important;
}

.clipboard-input :deep(.q-field__control-outer) {
  background: transparent !important;
}

.clipboard-input :deep(.q-field__native) {
  color: #FFFFFF !important;
}

.clipboard-input :deep(.q-field__label) {
  color: #9CA3AF !important;
}

/* Button hover effects */
.q-btn:hover {
  transform: translateY(-1px);
  transition: all 0.2s ease;
}

/* Responsive adjustments */
@media (max-width: 575.98px) {
  .clipboard-page {
    padding: 16px;
  }

  .q-btn {
    font-size: 12px;
  }
}
</style>
