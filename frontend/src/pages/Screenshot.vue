<template>
  <q-page padding>
    <div class="row q-mb-md">
      <div class="col-12">
        <div class="row items-center q-gutter-sm">
          <div class="text-h5">Screenshot</div>
          <q-space />
          <q-badge
            :color="screenshotAvailable ? 'positive' : 'negative'"
            rounded
          >
            {{ screenshotAvailable ? 'Available' : 'Unavailable' }}
          </q-badge>
        </div>
      </div>
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
                color="primary"
                icon="screenshot"
                label="Capture Screenshot"
                :loading="capturing"
                @click="captureScreenshot"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Screenshot Preview -->
    <div v-if="screenshotData" class="row q-mt-md">
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="row items-center q-gutter-sm">
              <div class="text-h6">Screenshot Preview</div>
              <q-space />
              <q-btn
                flat
                color="secondary"
                icon="download"
                label="Download"
                @click="downloadScreenshot"
              />
              <q-btn
                flat
                color="negative"
                icon="delete"
                label="Clear"
                @click="screenshotData = null"
              />
            </div>
          </q-card-section>

          <q-card-section>
            <div class="text-center">
              <img
                :src="`data:image/jpeg;base64,${screenshotData}`"
                alt="Screenshot"
                class="screenshot-image"
                style="max-width: 100%; height: auto;"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Instructions -->
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
            Click "Capture Screenshot" to take a screenshot of the remote PC.
          </div>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import { useSystemStore } from 'stores/system';
import api from 'services/ApiService';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'ScreenshotPage'
});

const $q = useQuasar();
const systemStore = useSystemStore();

// State
const capturing = ref(false);
const screenshotData = ref(null);
const screenshotAvailable = computed(() => systemStore.screenshotAvailable);

/**
 * Capture screenshot
 */
async function captureScreenshot() {
  capturing.value = true;

  try {
    const result = await api.get('/api/screenshot/capture');

    if (result.success && result.screenshot) {
      screenshotData.value = result.screenshot;

      $q.notify({
        type: 'positive',
        message: 'Screenshot captured successfully',
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
 * Download screenshot
 */
function downloadScreenshot() {
  if (!screenshotData.value) return;

  try {
    // Create base64 to blob
    const base64Data = screenshotData.value;
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'image/jpeg' });

    // Create download link
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `screenshot_${new Date().getTime()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    $q.notify({
      type: 'positive',
      message: 'Screenshot downloaded',
      position: 'top'
    });
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to download screenshot',
      position: 'top'
    });
  }
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
});
</script>

<style scoped>
.screenshot-image {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
