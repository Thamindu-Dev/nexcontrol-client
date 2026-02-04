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
    <!-- Docker Status Bar -->
    <div class="row q-mb-md q-gutter-sm">
      <q-btn
        flat
        round
        dense
        icon="refresh"
        :loading="loading.containers"
        @click="refreshContainers"
      />
      <q-badge
        :color="dockerAvailable ? 'positive' : 'negative'"
        rounded
      >
        {{ dockerAvailable ? 'Docker Running' : 'Docker Unavailable' }}
      </q-badge>
    </div>

    <!-- No Docker Available Message -->
    <div v-if="!dockerAvailable" class="row q-mt-lg">
      <div class="col-12">
        <q-card class="glass-card q-pa-xl text-center">
          <q-icon
            name="warning"
            size="xl"
            color="warning"
            class="q-mb-md"
          />
          <div class="text-h6">Docker is not available</div>
          <div class="text-caption text-grey q-mt-sm">
            Docker is either not installed or not running on the remote PC.<br>
            Install Docker and start the Docker daemon to use this feature.
          </div>
        </q-card>
      </div>
    </div>

    <!-- Containers List -->
    <div v-else-if="containers.length === 0 && !loading.containers" class="row q-mt-lg">
      <div class="col-12">
        <q-card class="glass-card q-pa-xl text-center">
          <q-icon
            name="inventory_2"
            size="xl"
            color="grey"
            class="q-mb-md"
          />
          <div class="text-h6">No containers found</div>
        </q-card>
      </div>
    </div>

    <!-- Container Cards -->
    <div class="row q-gutter-md q-mt-md">
      <div
        v-for="container in containers"
        :key="container.id"
        class="col-12 col-sm-6 col-md-4"
      >
        <q-card class="glass-card">
          <q-card-section>
            <div class="row items-center q-mb-sm">
              <div class="col">
                <div class="text-subtitle1 text-weight-bold">
                  {{ container.name }}
                </div>
                <div class="text-caption text-grey">
                  {{ container.image }}
                </div>
              </div>
              <div class="col-auto">
                <q-badge
                  :color="container.state === 'running' ? 'positive' : 'grey'"
                  :label="container.state"
                  rounded
                />
              </div>
            </div>
          </q-card-section>

          <q-card-section class="q-pt-none">
            <div class="text-caption">
              <div>ID: {{ container.id }}</div>
              <div>Status: {{ container.status }}</div>
            </div>
          </q-card-section>

            <q-card-actions align="right">
              <q-btn
                v-if="container.state === 'running'"
                flat
                color="grey-7"
                icon="stop"
                @click="stopContainer(container.id)"
                :loading="actionLoading[container.id]"
              >
                Stop
              </q-btn>
              <q-btn
                v-else
                flat
                color="grey-6"
                icon="play_arrow"
                @click="startContainer(container.id)"
                :loading="actionLoading[container.id]"
              >
                Start
              </q-btn>
              <q-btn
                flat
                color="grey-8"
                icon="refresh"
                @click="restartContainer(container.id)"
                :loading="actionLoading[container.id]"
              >
                Restart
              </q-btn>
              <q-btn
                flat
                color="grey"
                icon="list"
                @click="viewLogs(container.id)"
              >
                Logs
              </q-btn>
            </q-card-actions>
        </q-card>
      </div>
    </div>

    <!-- Logs Dialog -->
    <q-dialog v-model="showLogs" maximized>
      <q-card class="glass-card">
        <q-card-section>
          <div class="row items-center q-gutter-sm">
            <div class="text-h6">Container Logs</div>
            <q-space />
            <q-btn flat round dense icon="close" @click="showLogs = false" />
          </div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <div v-if="logsLoading" class="text-center q-pa-lg">
            <q-spinner color="white" size="3em" />
            <div class="q-mt-md">Loading logs...</div>
          </div>
          <pre v-else class="bg-grey-10 q-pa-md" style="max-height: 400px; overflow-y: auto;">{{ logs || 'No logs available' }}</pre>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Close" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
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
    $q.notify({
      type: 'positive',
      message: result.message || 'Container started',
      position: 'top'
    });
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to start container',
      position: 'top'
    });
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
    $q.notify({
      type: 'positive',
      message: result.message || 'Container stopped',
      position: 'top'
    });
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to stop container',
      position: 'top'
    });
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
    $q.notify({
      type: 'positive',
      message: result.message || 'Container restarted',
      position: 'top'
    });
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to restart container',
      position: 'top'
    });
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
/* Container Cards - OLED Theme */
/* Glass Card - Dark Mode */
.glass-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
}

/* Preformatted text for logs */
pre {
  background: #0A0A0A !important;
  border: 1px solid #333333;
  border-radius: 8px;
  color: #E0E0E0;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
}
</style>
