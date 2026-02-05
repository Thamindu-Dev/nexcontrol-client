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
  <q-page padding>
    <!-- Screenshot Status Bar -->
    <div class="row q-mb-md">
      <q-badge
        :color="screenshotAvailable ? 'positive' : 'negative'"
        rounded
      >
        {{ screenshotAvailable ? 'Available' : 'Unavailable' }}
      </q-badge>
      <q-space />
      <q-badge v-if="screenshotHistory.length > 0" color="cyan">
        {{ screenshotHistory.length }} screenshot{{ screenshotHistory.length > 1 ? 's' : '' }}
      </q-badge>
    </div>

    <!-- Screenshot Unavailable Message -->
    <div v-if="!screenshotAvailable" class="row q-mt-lg">
      <div class="col-12">
        <q-card flat bordered class="q-pa-xl text-center">
          <q-icon
            name="screenshot"
            size="xl"
            color="grey"
            class="q-mb-md"
          />
          <div class="text-h6">Screenshot not available</div>
          <div class="text-caption text-grey q-mt-sm">
            Screenshot functionality is not available on this system.<br>
            This may be due to running in a headless environment or missing dependencies.
          </div>
        </q-card>
      </div>
    </div>

    <!-- Screenshot Controls -->
    <div v-else class="row q-mb-md">
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="row items-center q-gutter-md">
              <div class="text-subtitle2">Actions</div>
              <q-space />
              <q-btn
                outline
                color="white"
                icon="screenshot"
                label="Capture Screenshot"
                :loading="capturing"
                @click="captureScreenshot"
              />
              <q-btn
                v-if="screenshotHistory.length > 0"
                flat
                color="negative"
                icon="delete_sweep"
                label="Clear All"
                @click="confirmClearAll"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Screenshot History List -->
    <div v-if="screenshotHistory.length > 0" class="row q-mt-md">
      <div class="col-12">
        <q-list separator bordered class="screenshot-list">
          <q-item
            v-for="(screenshot, index) in screenshotHistory"
            :key="screenshot.id"
            class="screenshot-item q-pa-md"
          >
            <!-- Thumbnail -->
            <q-item-section avatar>
              <q-img
                :src="`data:image/jpeg;base64,${screenshot.data}`"
                class="screenshot-thumbnail"
                fit="cover"
                style="width: 80px; height: 60px; border-radius: 8px;"
                @click="showFullscreen(screenshot)"
              >
                <template v-slot:error>
                  <div class="absolute-full flex flex-center bg-grey-9 text-grey">
                    <q-icon name="image" size="24px" />
                  </div>
                </template>
              </q-img>
            </q-item-section>

            <!-- Screenshot Info -->
            <q-item-section>
              <q-item-label class="text-white">
                Screenshot #{{ screenshotHistory.length - index }}
              </q-item-label>
              <q-item-label caption class="text-grey-6">
                {{ formatTimestamp(screenshot.timestamp) }}
              </q-item-label>
              <q-item-label caption class="text-cyan">
                {{ formatSize(screenshot.data) }}
              </q-item-label>
            </q-item-section>

            <!-- Action Buttons -->
            <q-item-section side>
              <div class="row q-gutter-xs">
                <q-btn
                  round
                  dense
                  flat
                  color="cyan"
                  icon="fullscreen"
                  @click="showFullscreen(screenshot)"
                >
                  <q-tooltip>View Fullscreen</q-tooltip>
                </q-btn>
                <q-btn
                  round
                  dense
                  flat
                  color="positive"
                  icon="save"
                  :loading="screenshot.saving"
                  @click="saveToGallery(screenshot)"
                >
                  <q-tooltip>Save to Gallery</q-tooltip>
                </q-btn>
                <q-btn
                  round
                  dense
                  flat
                  color="negative"
                  icon="delete"
                  @click="deleteScreenshot(index)"
                >
                  <q-tooltip>Delete</q-tooltip>
                </q-btn>
              </div>
            </q-item-section>
          </q-item>
        </q-list>
      </div>
    </div>

    <!-- Instructions (No screenshots yet) -->
    <div v-else-if="screenshotAvailable" class="row q-mt-lg">
      <div class="col-12">
        <q-card flat bordered class="q-pa-xl text-center">
          <q-icon
            name="photo_camera"
            size="xl"
            color="grey"
            class="q-mb-md"
          />
          <div class="text-h6">No screenshot captured</div>
          <div class="text-caption text-grey q-mt-sm">
            Click "Capture Screenshot" to take a screenshot of the remote PC.<br>
            Screenshots will be saved in a history list below.
          </div>
        </q-card>
      </div>
    </div>

    <!-- Fullscreen Image Dialog -->
    <q-dialog v-model="fullscreenDialog" maximized>
      <q-card class="fullscreen-card">
        <q-card-section class="q-pa-none">
          <div class="row items-center q-pa-sm bg-black">
            <q-space />
            <q-btn
              flat
              round
              color="white"
              icon="close"
              @click="fullscreenDialog = false"
            />
          </div>
        </q-card-section>

        <q-card-section class="q-pa-none bg-black">
          <img
            v-if="selectedScreenshot"
            :src="`data:image/jpeg;base64,${selectedScreenshot.data}`"
            alt="Screenshot Fullscreen"
            class="fullscreen-image"
          />
        </q-card-section>

        <q-card-section class="q-pa-sm bg-black fixed-bottom">
          <div class="row justify-center q-gutter-md">
            <q-btn
              color="positive"
              icon="save"
              label="Save to Gallery"
              :loading="selectedScreenshot?.saving"
              @click="selectedScreenshot && saveToGallery(selectedScreenshot)"
            />
            <q-btn
              color="white"
              icon="share"
              label="Share"
              @click="selectedScreenshot && shareScreenshot(selectedScreenshot)"
            />
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useQuasar } from 'quasar';
import { useSystemStore } from '../stores/system';
import api from '../services/ApiService';
import { Filesystem } from '@capacitor/filesystem';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'ScreenshotPage'
});

const $q = useQuasar();
const systemStore = useSystemStore();

// State
const capturing = ref(false);
const screenshotHistory = ref([]);
const fullscreenDialog = ref(false);
const selectedScreenshot = ref(null);

const screenshotAvailable = computed(() => systemStore.screenshotAvailable);

/**
 * Generate unique ID for screenshot
 */
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);

  if (diffMins < 1) {
    return 'Just now';
  } else if (diffMins < 60) {
    return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleString();
  }
}

/**
 * Format base64 data size
 */
function formatSize(base64) {
  const sizeInBytes = Math.round((base64.length * 3) / 4);
  const sizeInKB = (sizeInBytes / 1024).toFixed(2);
  return `${sizeInKB} KB`;
}

/**
 * Capture screenshot
 */
async function captureScreenshot() {
  capturing.value = true;

  try {
    const result = await api.post('/api/screenshot/capture', {});

    if (result.success && result.image) {
      // Add to history (newest first)
      screenshotHistory.value.unshift({
        id: generateId(),
        data: result.image,
        timestamp: Date.now(),
        saving: false
      });

      $q.notify({
        type: 'positive',
        message: 'Screenshot captured successfully',
        caption: `${screenshotHistory.value.length} screenshot(s) in history`,
        position: 'top'
      });
    } else {
      $q.notify({
        type: 'negative',
        message: result.message || 'Failed to capture screenshot',
        position: 'top'
      });
    }
  } catch (error) {
    console.error('[Screenshot] Capture error:', error);
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to capture screenshot',
      position: 'top'
    });
  } finally {
    capturing.value = false;
  }
}

/**
 * Show fullscreen image
 */
function showFullscreen(screenshot) {
  selectedScreenshot.value = screenshot;
  fullscreenDialog.value = true;
}

/**
 * Save screenshot to device gallery
 */
async function saveToGallery(screenshot) {
  if (!screenshot?.data) return;

  screenshot.saving = true;

  try {
    // Convert base64 to binary
    const base64Data = screenshot.data;
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);

    // Check if running in Capacitor (mobile app)
    const isCapacitor = window.Capacitor?.isNativePlatform?.();

    if (isCapacitor) {
      // Native mobile: Use Capacitor Filesystem + Share API
      try {
        const fileName = `nexcontrol_screenshot_${screenshot.timestamp}.jpg`;

        // Write file to app documents directory
        await Filesystem.writeFile({
          path: fileName,
          data: base64Data,
          directory: 'documents',
          recursive: true
        });

        // On iOS, use the Share API to save to Photos
        // Direct gallery access requires special permissions
        await navigator.share({
          files: [new File([byteArray], fileName, { type: 'image/jpeg' })],
          title: 'NexControl Screenshot',
          text: 'Screenshot captured with NexControl'
        });

        $q.notify({
          type: 'positive',
          message: 'Preparing to save...',
          caption: 'Choose "Save Image" from the share sheet',
          position: 'top'
        });
      } catch {
        // Fallback: Try direct download (works on some devices)
        const blob = new Blob([byteArray], { type: 'image/jpeg' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `nexcontrol_screenshot_${screenshot.timestamp}.jpg`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        $q.notify({
          type: 'positive',
          message: 'Screenshot downloaded',
          caption: 'Check your Downloads folder',
          position: 'top'
        });
      }
    } else {
      // Web browser: Use traditional download
      const blob = new Blob([byteArray], { type: 'image/jpeg' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `nexcontrol_screenshot_${screenshot.timestamp}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      $q.notify({
        type: 'positive',
        message: 'Screenshot downloaded',
        caption: 'Check your Downloads folder',
        position: 'top'
      });
    }
  } catch (error) {
    console.error('[Screenshot] Save error:', error);
    $q.notify({
      type: 'negative',
      message: 'Failed to save screenshot',
      caption: error.message || 'Unknown error',
      position: 'top'
    });
  } finally {
    screenshot.saving = false;
  }
}

/**
 * Share screenshot (Web Share API)
 */
async function shareScreenshot(screenshot) {
  if (!screenshot?.data) return;

  try {
    // Convert base64 to blob
    const base64Data = screenshot.data;
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new File([byteArray], `nexcontrol_screenshot_${screenshot.timestamp}.jpg`, {
      type: 'image/jpeg'
    });

    // Check if Web Share API is supported
    if (navigator.share) {
      await navigator.share({
        files: [blob],
        title: 'NexControl Screenshot',
        text: 'Screenshot captured with NexControl Remote PC Controller'
      });

      $q.notify({
        type: 'positive',
        message: 'Share sheet opened',
        position: 'top'
      });
    } else {
      $q.notify({
        type: 'warning',
        message: 'Share not supported',
        caption: 'Use "Save to Gallery" instead',
        position: 'top'
      });
    }
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error('[Screenshot] Share error:', error);
      $q.notify({
        type: 'negative',
        message: 'Failed to share screenshot',
        caption: error.message,
        position: 'top'
      });
    }
  }
}

/**
 * Delete single screenshot
 */
function deleteScreenshot(index) {
  $q.dialog({
    title: 'Delete Screenshot',
    message: 'Are you sure you want to delete this screenshot?',
    cancel: true,
    persistent: true,
    class: 'glass-dialog'
  }).onOk(() => {
    screenshotHistory.value.splice(index, 1);
    $q.notify({
      type: 'positive',
      message: 'Screenshot deleted',
      caption: `${screenshotHistory.value.length} screenshot(s) remaining`,
      position: 'top'
    });
  });
}

/**
 * Clear all screenshots
 */
function confirmClearAll() {
  $q.dialog({
    title: 'Clear All Screenshots',
    message: `Are you sure you want to delete all ${screenshotHistory.value.length} screenshot(s)?`,
    cancel: true,
    persistent: true,
    class: 'glass-dialog'
  }).onOk(() => {
    const count = screenshotHistory.value.length;
    screenshotHistory.value = [];
    $q.notify({
      type: 'positive',
      message: `${count} screenshot(s) deleted`,
      position: 'top'
    });
  });
}

/**
 * Lifecycle
 */
onMounted(async () => {
  // Check if screenshot is available
  try {
    await systemStore.checkScreenshotAvailability();
  } catch {
    // Silently fail - will show unavailable message
  }

  // Load screenshot history from local storage (optional persistence)
  try {
    const saved = localStorage.getItem('nexcontrol_screenshot_history');
    if (saved) {
      const parsed = JSON.parse(saved);
      // Only load if recent (last 24 hours)
      const oneDayAgo = Date.now() - 86400000;
      screenshotHistory.value = parsed.filter(s => s.timestamp > oneDayAgo);
    }
  } catch {
    // Silently fail - start fresh
  }
});

// Save history to localStorage whenever it changes
watch(screenshotHistory, (newHistory) => {
  try {
    // Only keep last 50 screenshots to avoid storage issues
    const toSave = newHistory.slice(0, 50);
    localStorage.setItem('nexcontrol_screenshot_history', JSON.stringify(toSave));
  } catch {
    // Silently fail if storage is full
  }
}, { deep: true });
</script>

<style scoped>
/* OLED Theme Styles */
.q-page {
  position: relative !important;
  z-index: 10 !important;
}

.q-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
  position: relative !important;
  z-index: 10 !important;
}

/* Screenshot List */
.screenshot-list {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
}

.screenshot-item {
  background: #000000;
  border-bottom: 1px solid #222222;
  transition: background 0.2s ease;
}

.screenshot-item:hover {
  background: #0A0A0A;
}

.screenshot-item:last-child {
  border-bottom: none;
}

.screenshot-thumbnail {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 1px solid #333333;
}

.screenshot-thumbnail:hover {
  transform: scale(1.05);
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.3);
}

/* Fullscreen Dialog */
.fullscreen-card {
  background: #000000;
}

.fullscreen-card .q-card-section {
  background: #000000;
}

.fullscreen-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.fixed-bottom {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
}

/* CRITICAL: Ensure all buttons are clickable */
.q-btn {
  position: relative !important;
  z-index: 1001 !important;
  pointer-events: auto !important;
}

/* CRITICAL: Ensure all interactive elements are clickable */
.q-page > *,
.q-page .row,
.q-page .col,
.q-page .col-12,
.screenshot-item {
  position: relative !important;
  z-index: 10 !important;
}

/* List item text colors */
:deep(.q-item__label) {
  color: #FFFFFF !important;
}

:deep(.q-item__label--caption) {
  color: #666666 !important;
}

:deep(.q-item) {
  color: #FFFFFF !important;
}

/* Thumbnail click feedback */
.screenshot-thumbnail:active {
  transform: scale(0.95);
}
</style>
