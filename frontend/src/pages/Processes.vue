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
  <div class="processes-page">
    <q-page padding class="q-pl-none q-pr-md q-pb-xl">
      <!-- Sort Controls -->
      <div class="row q-col-gutter-md q-mb-lg">
        <div class="col-12">
          <q-card class="glass-card q-pa-md">
            <div class="row items-center q-gutter-md">
              <div class="text-subtitle2 text-white">Sort by:</div>
              <q-btn-toggle
                v-model="sortBy"
                toggle-color="cyan"
                text-color="grey-6"
                rounded
                unelevated
                :options="[
                  { label: 'CPU', value: 'cpu' },
                  { label: 'Memory', value: 'memory' }
                ]"
                @update:model-value="handleSortChange"
                :disable="isRefreshing"
              />
              <q-space />
              <q-btn
                flat
                round
                color="cyan"
                icon="refresh"
                :loading="isRefreshing"
                @click="refreshProcesses"
                class="q-mr-sm"
              >
                <q-tooltip>Refresh processes</q-tooltip>
              </q-btn>
              <div class="text-caption text-grey-6">
                {{ processes.length }} process{{ processes.length !== 1 ? 'es' : '' }} shown
              </div>
            </div>
          </q-card>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading.processes || isRefreshing" class="row justify-center q-my-xl">
        <div class="col-12 col-sm-8 col-md-6 text-center">
          <q-spinner-dots color="cyan" size="4em" class="q-mb-md" />
          <div class="text-body1 text-grey-6">Loading processes...</div>
          <div class="text-caption text-grey-7 q-mt-sm">
            Fetching system process information
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="processes.length === 0" class="row justify-center q-mt-xl">
        <div class="col-12 col-sm-8 col-md-6 text-center">
          <q-card class="glass-card q-pa-xl">
            <q-icon
              name="memory"
              size="80px"
              color="grey-7"
              class="q-mb-md"
            />
            <div class="text-h5 text-white q-mb-md">No processes found</div>
            <div class="text-body1 text-grey-6">
              Unable to retrieve process list. Try refreshing.
            </div>
          </q-card>
        </div>
      </div>

      <!-- Processes Table -->
      <div v-else class="row q-col-gutter-md q-mt-md">
        <div class="col-12">
          <q-card class="glass-card">
            <q-markup-table>
              <table class="q-table">
                <thead>
                  <tr>
                    <th class="text-left">PID</th>
                    <th class="text-left">Name</th>
                    <th class="text-right">CPU %</th>
                    <th class="text-right">Memory %</th>
                    <th class="text-center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="process in processes" :key="process.pid">
                    <td class="text-left text-mono">{{ process.pid }}</td>
                    <td class="text-left">
                      <div class="text-white">{{ process.name || 'N/A' }}</div>
                      <div class="text-caption text-grey-6">
                        {{ process.username || 'N/A' }}
                      </div>
                    </td>
                    <td class="text-right">
                      <q-badge
                        :color="getCPUColor(process.cpu_percent)"
                        :label="process.cpu_percent?.toFixed(1) || '0'"
                        text-color="white"
                        class="q-px-sm"
                      />
                    </td>
                    <td class="text-right">
                      <q-badge
                        :color="getMemoryColor(process.memory_percent)"
                        :label="process.memory_percent?.toFixed(1) || '0'"
                        text-color="white"
                        class="q-px-sm"
                      />
                    </td>
                    <td class="text-center">
                      <q-btn
                        flat
                        dense
                        round
                        color="red"
                        icon="delete"
                        @click="confirmKillProcess(process.pid, process.name)"
                        :loading="killLoading[process.pid]"
                        :disable="killLoading[process.pid]"
                      >
                        <q-tooltip>Terminate process</q-tooltip>
                      </q-btn>
                    </td>
                  </tr>
                </tbody>
              </table>
            </q-markup-table>
          </q-card>
        </div>
      </div>
    </q-page>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import { useSystemStore } from '../stores/system';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'ProcessManagerPage'
});

const $q = useQuasar();
const systemStore = useSystemStore();

// State
const loading = computed(() => systemStore.loading);
const processes = computed(() => systemStore.processes);
const sortBy = ref('cpu');
const killLoading = ref({});
const isRefreshing = ref(false);

/**
 * Get CPU color based on usage
 */
function getCPUColor(percent) {
  if (percent >= 80) return 'red';
  if (percent >= 50) return 'orange';
  return 'green';
}

/**
 * Get memory color based on usage
 */
function getMemoryColor(percent) {
  if (percent >= 80) return 'red';
  if (percent >= 50) return 'orange';
  return 'cyan';
}

/**
 * Handle sort change
 */
async function handleSortChange() {
  await refreshProcesses();
}

/**
 * Refresh processes list
 */
async function refreshProcesses() {
  isRefreshing.value = true;
  try {
    await systemStore.fetchProcesses(30, sortBy.value);
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to fetch processes',
      position: 'top'
    });
  } finally {
    isRefreshing.value = false;
  }
}

/**
 * Confirm kill process
 */
function confirmKillProcess(pid, name) {
  $q.dialog({
    title: 'Kill Process',
    message: `Are you sure you want to kill process ${name} (PID: ${pid})?`,
    cancel: true,
    persistent: true,
    class: 'bg-dark'
  }).onOk(async () => {
    await killProcess(pid);
  });
}

/**
 * Kill a process
 */
async function killProcess(pid) {
  killLoading.value[pid] = true;

  try {
    const result = await systemStore.killProcess(pid);

    if (result.success) {
      $q.notify({
        type: 'positive',
        message: result.message || 'Process killed',
        position: 'top'
      });

      // Refresh the list after a short delay
      setTimeout(async () => {
        await refreshProcesses();
      }, 500);
    } else {
      $q.notify({
        type: 'negative',
        message: result.message || 'Failed to kill process',
        position: 'top'
      });
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to kill process',
      position: 'top'
    });
  } finally {
    killLoading.value[pid] = false;
  }
}

/**
 * Lifecycle
 */
onMounted(async () => {
  await refreshProcesses();
});
</script>

<style scoped>
/* Page Container */
.processes-page {
  background: #000000;
  min-height: calc(100vh - 50px);
}

/* OLED Theme Styles */
.glass-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
}

/* Table Styling - High Contrast */
.q-markup-table {
  background: #000000 !important;
}

.q-table {
  background: #000000 !important;
  color: #FFFFFF !important;
}

.q-table th {
  color: #FFFFFF !important;
  font-weight: 600;
  background: #0A0A0A !important;
  border-bottom: 2px solid #333333 !important;
}

.q-table td {
  color: #E0E0E0 !important;
  background: #000000 !important;
  border-bottom: 1px solid #1A1A1A !important;
}

.q-table tr:hover td {
  background: #0A0A0A !important;
}

.q-table tbody tr {
  background: #000000 !important;
}

/* Typography */
.text-mono {
  font-family: 'JetBrains Mono', 'Roboto Mono', 'Courier New', monospace;
  letter-spacing: -0.3px;
}
</style>
