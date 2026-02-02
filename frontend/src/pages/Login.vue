<template>
  <div class="login-page q-pa-md">
    <div class="column fullscreen bg-blue-1">
      <div class="row items-center">
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <q-card class="q-pa-md">
            <q-card-section>
              <div class="text-h5 text-center text-weight-bold text-primary">
                NexControl
              </div>
              <div class="text-subtitle2 text-center text-grey">
                Remote PC Controller
              </div>
            </q-card-section>

            <q-card-section>
              <q-form @submit="handleLogin" class="q-gutter-md">
                <!-- Server Configuration -->
                <div class="text-subtitle2 text-grey-7">
                  Server Configuration
                </div>

                <q-input
                  v-model="serverConfig.host"
                  label="Server IP"
                  filled
                  dense
                  hint="e.g., 192.168.1.100"
                  :rules="[val => !!val || 'Host is required']"
                />

                <q-input
                  v-model.number="serverConfig.port"
                  label="Port"
                  type="number"
                  filled
                  dense
                  hint="Default: 8000"
                  :rules="[val => val > 0 || 'Port is required']"
                />

                <q-separator class="q-my-md" />

                <!-- Login Form -->
                <div class="text-subtitle2 text-grey-7">
                  Login
                </div>

                <q-input
                  v-model="password"
                  label="Password"
                  :type="isPwd ? 'password' : 'text'"
                  filled
                  dense
                  hint="Enter your app password"
                  :rules="[val => !!val || 'Password is required']"
                >
                  <template v-slot:append>
                    <q-icon
                      :name="isPwd ? 'visibility_off' : 'visibility'"
                      class="cursor-pointer"
                      @click="isPwd = !isPwd"
                    />
                  </template>
                </q-input>

                <div v-if="loginError" class="text-negative text-caption q-mb-sm">
                  {{ loginError }}
                </div>

                <q-btn
                  type="submit"
                  color="primary"
                  class="full-width"
                  :loading="loading"
                  :disable="loading"
                  label="Connect"
                  size="md"
                />

                <div class="q-mt-md">
                  <q-checkbox v-model="saveCredentials" label="Save credentials" />
                </div>
              </q-form>
            </q-card-section>

            <q-card-section>
              <div class="text-caption text-grey">
                <div><strong>Note:</strong> This is a local network app.</div>
                <div>Make sure your PC is on the same network.</div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from 'stores/auth';
import { useSettingsStore } from 'stores/settings';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'LoginPage'
});

const router = useRouter();
const $q = useQuasar();

// Stores
const authStore = useAuthStore();
const settingsStore = useSettingsStore();

// State
const password = ref('');
const isPwd = ref(true);
const loading = ref(false);
const loginError = ref(null);
const saveCredentials = ref(false);

// Server configuration
const serverConfig = reactive({
  protocol: 'http',
  host: 'localhost',
  port: 8000
});

/**
 * Handle login form submission
 */
async function handleLogin() {
  loading.value = true;
  loginError.value = null;

  try {
    // Update server configuration
    await settingsStore.updateServer(serverConfig);

    // Attempt login
    const result = await authStore.login(password.value);

    if (result.success) {
      // Show success message
      $q.notify({
        type: 'positive',
        message: 'Connected successfully!',
        position: 'top'
      });

      // Save credentials if checked
      if (saveCredentials.value) {
        // Credentials already saved in stores
      }

      // Navigate to dashboard
      router.push('/dashboard');
    } else {
      loginError.value = result.error || 'Login failed';
    }
  } catch (error) {
    loginError.value = error.message || 'Connection failed. Check server settings.';
    $q.notify({
      type: 'negative',
      message: loginError.value,
      position: 'top'
    });
  } finally {
    loading.value = false;
  }
}

/**
 * Load saved settings on mount
 */
onMounted(() => {
  settingsStore.loadSettings();

  // Load saved server config
  const savedConfig = settingsStore.server;
  if (savedConfig) {
    Object.assign(serverConfig, savedConfig);
  }
});
</script>

<style scoped>
.login-page {
  min-height: 100vh;
}

.fullscreen {
  min-height: 100vh;
}
</style>
