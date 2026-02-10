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
  <div class="dashboard-page relative-position">
    <!-- Background Orbs for Premium Feel -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>

    <q-page padding class="q-pl-none q-pr-md q-pb-xl relative-position" style="z-index: 2;">
      <!-- Header Section -->
      <div class="row items-center justify-between q-mb-lg q-pl-lg">
        

        <div class="row q-gutter-md items-center">
          <q-toggle
            v-model="autoRefresh"
            checked-icon="sync"
            color="cyan"
            unchecked-icon="sync_disabled"
            label="Auto-Refresh"
            left-label
            class="text-grey-5"
            size="sm"
            @update:model-value="handleAutoRefreshToggle"
          />

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
        <div class="col-12 col-md-8 text-center fade-in">
          <q-card class="stat-card q-pa-xl glass-panel">
            <q-icon
              name="cloud_off"
              size="5rem"
              color="grey-8"
              class="q-mb-md"
            />
            <div class="text-h4 text-white text-weight-light">Docker Engine Not Detectable</div>
            <div class="text-body1 text-grey-5 q-mt-md" style="max-width: 500px; margin: 16px auto 0;">
              Please ensure Docker Desktop/Engine is running on the host machine.
              <br>The system will auto-retry connection.
            </div>
            <q-btn
              color="cyan"
              outline
              label="Retry Connection"
              class="q-mt-lg glass-btn"
              rounded
              @click="refreshContainers"
            />
          </q-card>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="containers.length === 0 && !loading.containers" class="row justify-center q-mt-xl">
        <div class="col-12 col-md-8 text-center fade-in">
          <q-card class="stat-card q-pa-xl glass-panel">
            <q-icon
              name="inventory_2"
              size="5rem"
              color="grey-8"
              class="q-mb-md"
            />
            <div class="text-h4 text-white text-weight-light">No Containers Found</div>
            <div class="text-body1 text-grey-5 q-mt-md">
              Your container list is empty. Start some containers to see them here.
            </div>
          </q-card>
        </div>
      </div>

      <!-- Loading State -->
      <div v-else-if="loading.containers" class="row justify-center q-my-xl">
        <q-spinner-orbit color="cyan" size="5em" />
        <div class="text-cyan q-mt-md text-subtitle1">Scanning Docker Env...</div>
      </div>

      <!-- Containers Grid -->
      <div v-else class="row q-col-gutter-lg">
        <div
          v-for="container in containers"
          :key="container.id"
          class="col-12 col-md-6 col-lg-4"
        >
          <q-card class="stat-card glass-panel column full-height card-hover">
            <!-- Card Header -->
            <q-card-section class="q-pb-sm">
              <div class="row items-center no-wrap justify-between">
                <!-- Name and Image (Left) -->
                <div class="col q-pr-sm" style="min-width: 0; max-width: 60%;">
                  <div class=" text-white text-weight-bold ellipsis text-shadow-sm">
                    {{ container.name }}
                  </div>
                  <div class="text-caption text-cyan-3 ellipsis q-mt-xs flex items-center">
                    {{ container.image }}
                  </div>
                </div>
                
                <!-- Status Badge (Right) -->
                <div class="col-auto">
                   <q-badge
                    :class="['status-badge q-py-xs q-px-md', container.state === 'running' ? 'bg-cyan-9 text-cyan-1' : 'bg-grey-9 text-grey-4']"
                    rounded
                  >
                    <div class="row items-center no-wrap">
                      <div :class="['status-dot q-mr-sm', container.state === 'running' ? 'bg-cyan-4' : 'bg-red-4']"></div>
                      <span class="text-weight-bold" style="font-size: 0.75rem">{{ container.state.toUpperCase() }}</span>
                    </div>
                  </q-badge>
                </div>
              </div>
            </q-card-section>

            <!-- Card Body (Stats) -->
            <q-card-section class="q-pt-xs col-grow">
              <div class="glass-separator q-my-sm"></div>

              <div class="row q-col-gutter-md text-caption">
                <div class="col-6">
                  <div class="text-grey-5 text-xs q-mb-xs">CONTAINER ID</div>
                  <div class="text-mono text-white bg-white-5 q-px-sm q-py-xs rounded-borders text-center">
                    {{ container.id.substring(0, 12) }}
                  </div>
                </div>
                <div class="col-6">
                  <div class="text-grey-5 text-xs q-mb-xs">STATUS</div>
                  <div class="text-white ellipsis q-pt-xs text-weight-medium">
                    {{ container.status }}
                  </div>
                </div>
              </div>
            </q-card-section>

            <!-- Actions Footer -->
            <q-card-actions align="left" class="q-pa-md bg-dark-glass">
              <div class="row full-width justify-between items-center no-wrap q-gutter-x-sm">

                <!-- Main Action (Play/Stop) -->
                <q-btn
                  v-if="container.state !== 'running'"
                  class="action-btn col-grow"
                  unelevated
                  color="cyan-9"
                  text-color="cyan-1"
                  icon="play_arrow"
                  label="Start"
                  @click="startContainer(container.id)"
                  :loading="actionLoading[container.id]"
                >
                  <q-tooltip>Start Container</q-tooltip>
                </q-btn>

                <q-btn
                  v-else
                  class="action-btn col-grow"
                  unelevated
                  color="red-9"
                  text-color="red-1"
                  icon="stop"
                  label="Stop"
                  @click="stopContainer(container.id)"
                  :loading="actionLoading[container.id]"
                >
                  <q-tooltip>Stop Container</q-tooltip>
                </q-btn>

                <!-- Restart -->
                <q-btn
                  class="action-btn-icon"
                  flat
                  round
                  color="orange-4"
                  icon="restart_alt"
                  @click="restartContainer(container.id)"
                  :loading="actionLoading[container.id]"
                >
                  <q-tooltip>Restart</q-tooltip>
                </q-btn>

                <!-- Logs -->
                <q-btn
                  class="action-btn-icon"
                  flat
                  round
                  color="grey-4"
                  icon="terminal"
                  @click="viewLogs(container.id)"
                >
                  <q-tooltip>View Logs</q-tooltip>
                </q-btn>
              </div>
            </q-card-actions>
          </q-card>
        </div>
      </div>

      <!-- Logs Dialog -->
      <q-dialog v-model="showLogs" maximized transition-show="slide-up" transition-hide="slide-down">
        <q-card class="bg-black text-white column logs-card">
          <!-- Log Header -->
          <q-toolbar class="bg-glass-header q-py-md border-bottom-glass">
            <q-icon name="terminal" color="cyan" size="sm" class="q-mr-md" />
            <div class="column">
              <div class="text-h6 text-weight-bold">Container Logs</div>
              <div class="text-caption text-mono text-cyan-3">{{ currentContainerId?.substring(0,12) }}</div>
            </div>
            <q-space />
            <q-btn flat round dense icon="close" v-close-popup />
          </q-toolbar>

          <!-- Log Content -->
          <q-card-section class="col q-pa-none scroll relative-position bg-terminal" id="logs-container">
            <div v-if="logsLoading" class="absolute-center text-center">
              <q-spinner-grid color="cyan" size="3em" />
              <div class="q-mt-sm text-grey-5">Fetching logs stream...</div>
            </div>

            <div v-else class="fit q-pa-md font-mono text-body2">
              <pre class="no-margin text-white" style="white-space: pre-wrap; word-break: break-all;">{{ logs || 'No logs available.' }}</pre>
            </div>
          </q-card-section>
        </q-card>
      </q-dialog>
    </q-page>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useQuasar } from 'quasar';
import { useSystemStore } from '../stores/system';
import api from '../services/ApiService';

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

// Load auto-refresh state from localStorage
const autoRefresh = ref(localStorage.getItem('docker_autoRefresh') === 'true');
let pollingInterval = null;

// Methods
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

async function viewLogs(containerId) {
  currentContainerId.value = containerId;
  showLogs.value = true;
  logsLoading.value = true;
  logs.value = '';

  try {
    const result = await api.get(`/api/docker/containers/${containerId}/logs?tail=200`);
    logs.value = result.logs || 'No logs available';
    
    // Auto-scroll to bottom
    await nextTick();
    const container = document.getElementById('logs-container');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  } catch {
    logs.value = 'Failed to load logs';
  } finally {
    logsLoading.value = false;
  }
}

function startPolling() {
  if (pollingInterval) clearInterval(pollingInterval);
  
  // refresh every 5 seconds
  pollingInterval = setInterval(() => {
    // Only poll if window is focused AND auto-refresh is enabled
    if (document.visibilityState === 'visible' && autoRefresh.value) {
      refreshContainers();
    }
  }, 5000);
}

function handleAutoRefreshToggle(val) {
  // Save state to localStorage
  localStorage.setItem('docker_autoRefresh', val.toString());

  if (val) {
    refreshContainers(); // Refresh immediately
    startPolling();
  } else {
    if (pollingInterval) clearInterval(pollingInterval);
    pollingInterval = null;
  }
}

// Lifecycle
onMounted(async () => {
  await refreshContainers();
  if (autoRefresh.value) {
    startPolling();
  }
});

onUnmounted(() => {
  if (pollingInterval) clearInterval(pollingInterval);
});
</script>

<style scoped>
/* Glassmorphism Panel */
.glass-panel {
  background: rgba(20, 25, 30, 0.6);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(34, 211, 238, 0.15);
  border-color: rgba(34, 211, 238, 0.4);
}

/* Badges & Status */
.glass-badge {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.status-badge {
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,0.05);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
}

/* Typography & Decor */
.text-shadow-sm {
  text-shadow: 0 2px 4px rgba(0,0,0,0.5);
}

.glass-separator {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
}

.bg-white-5 {
  background: rgba(255,255,255,0.05);
}

.bg-dark-glass {
  background: rgba(0,0,0,0.3);
}

/* Background Orbs */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
  z-index: 1;
  pointer-events: none;
}

.orb-1 {
  top: -100px;
  left: -100px;
  width: 400px;
  height: 400px;
  background: #00bcd4; /* Cyan */
}

.orb-2 {
  bottom: 0px;
  right: -100px;
  width: 300px;
  height: 300px;
  background: #9c27b0; /* Purple */
}

/* Buttons */
.action-btn {
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
  background: rgba(34, 211, 238, 0.15);
  transition: all 0.2s ease;
}

.action-btn:hover {
  filter: brightness(1.2);
}

.action-btn-icon {
  width: 42px;
  height: 42px;
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  transition: all 0.2s;
}

.action-btn-icon:hover {
  background: rgba(255,255,255,0.15);
  transform: scale(1.05);
}

.glass-btn {
  backdrop-filter: blur(4px);
}

/* Header Button */
.header-btn {
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.2);
  transition: all 0.3s ease;
}

.header-btn:hover {
  background: rgba(34, 211, 238, 0.3);
  transform: rotate(180deg);
}

/* Logs */
.logs-card {
  background: #0a0a0a;
}
.bg-terminal {
  background-color: #050505;
}
.bg-glass-header {
  background: rgba(20,20,20,0.95);
  backdrop-filter: blur(10px);
}
.border-bottom-glass {
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

/* Utils */
.text-xs {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.opacity-70 {
  opacity: 0.7;
}

.fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 600px) {
  .stat-card {
    min-height: auto;
  }
}
</style>
