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
  <div class="dashboard-page">
    <q-page padding class="q-pl-none q-pr-md q-pb-xl">
      <!-- Header Section -->
      <div class="row items-center justify-between q-mb-lg q-pl-xs">
        

        <div class="row q-gutter-sm items-center">
          <q-badge
            :color="dockerAvailable ? 'cyan' : 'grey-9'"
            :text-color="dockerAvailable ? 'black' : 'grey-5'"
            class="q-py-xs q-px-sm text-subtitle2"
            style="border: 1px solid rgba(255,255,255,0.1)"
            rounded
          >
            <q-icon :name="dockerAvailable ? 'check_circle' : 'error'" class="q-mr-xs" />
            {{ dockerAvailable ? 'Engine Running' : 'Unavailable' }}
          </q-badge>

          <q-btn
            round
            flat
            color="cyan"
            icon="refresh"
            :loading="loading.containers"
            @click="refreshContainers"
            class="header-btn"
          >
            <q-tooltip>Refresh List</q-tooltip>
          </q-btn>
        </div>
      </div>

      <!-- No Docker Available Message -->
      <div v-if="!dockerAvailable" class="row justify-center q-mt-xl">
        <div class="col-12 col-md-8 text-center">
          <q-card class="stat-card q-pa-xl">
            <q-icon
              name="cloud_off"
              size="4rem"
              color="grey-8"
              class="q-mb-md"
            />
            <div class="text-h5 text-white">Docker Engine Not Detectable</div>
            <div class="text-body1 text-grey q-mt-sm">
              Please ensure Docker Desktop/Engine is running on the host machine.
            </div>
          </q-card>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="containers.length === 0 && !loading.containers" class="row justify-center q-mt-xl">
        <div class="col-12 col-md-8 text-center">
          <q-card class="stat-card q-pa-xl">
            <q-icon
              name="inventory_2"
              size="4rem"
              color="grey-8"
              class="q-mb-md"
            />
            <div class="text-h5 text-white">No Containers Found</div>
            <div class="text-body1 text-grey q-mt-sm">
              Your container list is empty. Start some containers to see them here.
            </div>
          </q-card>
        </div>
      </div>

      <!-- Loading State -->
      <div v-else-if="loading.containers" class="row justify-center q-my-xl">
        <q-spinner-dots color="cyan" size="4em" />
      </div>

      <!-- Containers Grid -->
      <div v-else class="row q-col-gutter-md">
        <div
          v-for="container in containers"
          :key="container.id"
          class="col-12 col-md-6 col-lg-4"
        >
          <q-card class="stat-card column full-height">
            <!-- Card Header -->
            <q-card-section class="q-pb-none">
              <div class="row items-start no-wrap">
                <div class="col">
                  <div class="text-h6 text-white text-weight-bold ellipsis">
                    {{ container.name }}
                  </div>
                  <div class="text-caption text-cyan ellipsis q-mt-none">
                    <q-icon name="image" size="xs" class="q-mr-xs" />
                    {{ container.image }}
                  </div>
                </div>
                <div class="col-auto q-ml-sm">
                  <q-badge
                    :color="container.state === 'running' ? 'cyan' : 'grey-9'"
                    :text-color="container.state === 'running' ? 'black' : 'grey-5'"
                    class="q-py-xs q-px-sm"
                    style="border: 1px solid rgba(255,255,255,0.1)"
                    rounded
                  >
                    <q-icon
                      :name="container.state === 'running' ? 'play_circle' : 'stop_circle'"
                      class="q-mr-xs"
                      size="xs"
                    />
                    {{ container.state.toUpperCase() }}
                  </q-badge>
                </div>
              </div>
            </q-card-section>

            <!-- Card Body -->
            <q-card-section class="q-pt-sm col-grow">
              <q-separator dark class="q-mb-sm opacity-20" />

              <div class="row q-col-gutter-sm text-caption text-grey-4">
                <div class="col-6">
                  <div class="text-grey-6 text-xs">CONTAINER ID</div>
                  <div class="text-mono">{{ container.id.substring(0, 12) }}</div>
                </div>
                <div class="col-6">
                  <div class="text-grey-6 text-xs">STATUS DETAIL</div>
                  <div class="ellipsis">{{ container.status }}</div>
                </div>
              </div>
            </q-card-section>

            <!-- Actions -->
            <q-separator dark class="opacity-20" />
            <q-card-actions align="around" class="q-py-sm bg-dark-page">
              <q-btn
                v-if="container.state !== 'running'"
                class="action-btn"
                flat
                round
                color="cyan"
                icon="play_arrow"
                @click="startContainer(container.id)"
                :loading="actionLoading[container.id]"
              >
                <q-tooltip>Start Container</q-tooltip>
              </q-btn>

              <q-btn
                v-else
                class="action-btn"
                flat
                round
                color="red-4"
                icon="stop"
                @click="stopContainer(container.id)"
                :loading="actionLoading[container.id]"
              >
                <q-tooltip>Stop Container</q-tooltip>
              </q-btn>

              <q-btn
                class="action-btn"
                flat
                round
                color="orange-4"
                icon="restart_alt"
                @click="restartContainer(container.id)"
                :loading="actionLoading[container.id]"
              >
                <q-tooltip>Restart</q-tooltip>
              </q-btn>

              <q-btn
                class="action-btn"
                flat
                round
                color="grey-4"
                icon="terminal"
                @click="viewLogs(container.id)"
              >
                <q-tooltip>View Logs</q-tooltip>
              </q-btn>
            </q-card-actions>
          </q-card>
        </div>
      </div>

      <!-- Logs Dialog -->
      <q-dialog v-model="showLogs" maximized transition-show="slide-up" transition-hide="slide-down">
        <q-card class="bg-black text-white column">

          <!-- Log Header -->
          <q-toolbar class="bg-dark-page border-bottom q-py-sm">
            <q-icon name="terminal" color="cyan" size="sm" class="q-mr-sm" />
            <q-toolbar-title class="text-subtitle1">
               Container Logs <span class="text-grey text-caption q-ml-sm">{{ currentContainerId?.substring(0,12) }}</span>
            </q-toolbar-title>
            <q-btn flat round dense icon="close" v-close-popup />
          </q-toolbar>

          <!-- Log Content -->
          <q-card-section class="col q-pa-none scroll relative-position bg-black">
            <div v-if="logsLoading" class="absolute-center text-center">
              <q-spinner-dots color="cyan" size="3em" />
              <div class="q-mt-sm text-grey">Fetching logs...</div>
            </div>

            <div v-else class="fit q-pa-md font-mono text-body2">
              <pre class="no-margin text-grey-4" style="white-space: pre-wrap; word-break: break-all;">{{ logs || 'No logs available.' }}</pre>
            </div>
          </q-card-section>
        </q-card>
      </q-dialog>
    </q-page>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import { useSystemStore } from '../stores/system';
import api from '../services/ApiService';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'DockerManagerPage'
});

const $q = useQuasar();
const systemStore = useSystemStore();

// State
const loading = computed(() => systemStore.loading);
const containers = computed(() => systemStore.containers);
const dockerAvailable = computed(() => systemStore.dockerAvailable);
const actionLoading = ref({});
const showLogs = ref(false);
const logs = ref('');
const logsLoading = ref(false);
const currentContainerId = ref(null);

/**
 * Refresh containers list
 */
async function refreshContainers() {
  try {
    await systemStore.fetchContainers();
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to fetch containers',
      position: 'top'
    });
  }
}

/**
 * Start container
 */
async function startContainer(containerId) {
  actionLoading.value[containerId] = true;
  try {
    const result = await systemStore.startContainer(containerId);
    $q.notify({ type: 'positive', message: result.message || 'Container started', position: 'top' });
  } catch (error) {
    $q.notify({ type: 'negative', message: error.message || 'Failed to start container', position: 'top' });
  } finally {
    actionLoading.value[containerId] = false;
  }
}

/**
 * Stop container
 */
async function stopContainer(containerId) {
  actionLoading.value[containerId] = true;
  try {
    const result = await systemStore.stopContainer(containerId);
    $q.notify({ type: 'positive', message: result.message || 'Container stopped', position: 'top' });
  } catch (error) {
    $q.notify({ type: 'negative', message: error.message || 'Failed to stop container', position: 'top' });
  } finally {
    actionLoading.value[containerId] = false;
  }
}

/**
 * Restart container
 */
async function restartContainer(containerId) {
  actionLoading.value[containerId] = true;
  try {
    const result = await systemStore.restartContainer(containerId);
    $q.notify({ type: 'positive', message: result.message || 'Container restarted', position: 'top' });
  } catch (error) {
    $q.notify({ type: 'negative', message: error.message || 'Failed to restart container', position: 'top' });
  } finally {
    actionLoading.value[containerId] = false;
  }
}

/**
 * View container logs
 */
async function viewLogs(containerId) {
  currentContainerId.value = containerId;
  showLogs.value = true;
  logsLoading.value = true;
  logs.value = ''; // Reset logs

  try {
    const result = await api.get(`/api/docker/containers/${containerId}/logs?tail=100`);
    logs.value = result.logs || 'No logs available';
  } catch {
    logs.value = 'Failed to load logs';
  } finally {
    logsLoading.value = false;
  }
}

/**
 * Lifecycle
 */
onMounted(async () => {
  await refreshContainers();
});
</script>

<style scoped>
/* Dashboard-consistent Card Style */
.stat-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 16px;
  transition: all 0.3s ease;
  min-height: 220px;
}

.docker-card:hover {
  border-color: rgba(34, 211, 238, 0.3);
  box-shadow: 0 4px 20px rgba(34, 211, 238, 0.1);
  transform: translateY(-2px);
}

.card-header {
  background: rgba(0, 0, 0, 0.3);
}

/* Action Buttons */
.action-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.3);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(34, 211, 238, 0.1);
  transform: scale(1.05);
}

/* Logs Dialog */
.logs-dialog {
  background: #000000;
}

.logs-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

/* Typography */
.text-mono {
  font-family: 'JetBrains Mono', 'Roboto Mono', 'Courier New', monospace;
  letter-spacing: -0.3px;
}

.text-xs {
  font-size: 0.7rem;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  font-weight: 600;
}

/* Utilities */
.opacity-20 {
  opacity: 0.2;
}

.bg-dark-page {
  background: rgba(0, 0, 0, 0.3);
}

.ellipsis {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-margin {
  margin: 0;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
  .page-header {
    padding: 16px;
  }

  .page-content {
    padding: 16px;
  }

  .docker-card {
    min-height: 200px;
  }

  .action-btn {
    width: 44px;
    height: 44px;
  }
}
</style>
