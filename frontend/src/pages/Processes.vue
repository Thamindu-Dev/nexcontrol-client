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
    <div class="row q-mb-md">
      <div class="col-12">
        <div class="row items-center q-gutter-sm">
          <div class="text-h5">Process Manager</div>
          <q-space />
          <q-btn
            flat
            round
            dense
            icon="refresh"
            :loading="loading.processes"
            @click="refreshProcesses"
          >
            Refresh
          </q-btn>
        </div>
      </div>
    </div>

    <!-- Sort Controls -->
    <div class="row q-mb-md">
      <div class="col-12">
        <q-card class="glass-card q-pa-sm">
          <div class="row items-center q-gutter-md">
            <div class="text-subtitle2">Sort by:</div>
            <q-btn-toggle
              v-model="sortBy"
              toggle-color="white"
              :options="[
                { label: 'CPU', value: 'cpu' },
                { label: 'Memory', value: 'memory' }
              ]"
              @update:model-value="handleSortChange"
            />
            <q-space />
            <div class="text-caption text-grey">
              {{ processes.length }} processes shown
            </div>
          </div>
        </q-card>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="processes.length === 0 && !loading.processes" class="row q-mt-lg">
      <div class="col-12">
        <q-card class="glass-card q-pa-xl text-center">
          <q-icon
            name="memory"
            size="xl"
            color="grey"
            class="q-mb-md"
          />
          <div class="text-h6">No processes found</div>
        </q-card>
      </div>
    </div>

    <!-- Processes Table -->
    <div v-else class="row q-mt-md">
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
                  <td class="text-left">{{ process.pid }}</td>
                  <td class="text-left">
                    <div>{{ process.name || 'N/A' }}</div>
                    <div class="text-caption text-secondary">
                      {{ process.username || 'N/A' }}
                    </div>
                  </td>
                  <td class="text-right">
                    <q-badge
                      :color="getCPUColor(process.cpu_percent)"
                      :label="process.cpu_percent?.toFixed(1) || '0'"
                      text-color="white"
                    />
                  </td>
                  <td class="text-right">
                    <q-badge
                      :color="getMemoryColor(process.memory_percent)"
                      :label="process.memory_percent?.toFixed(1) || '0'"
                      text-color="white"
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
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </q-markup-table>
        </q-card>
      </div>
    </div>
  </q-page>
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
  return 'blue';
}

/**
 * Handle sort change
 */
function handleSortChange() {
  refreshProcesses();
}

/**
 * Refresh processes list
 */
async function refreshProcesses() {
  try {
    await systemStore.fetchProcesses(20, sortBy.value);
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to fetch processes',
      position: 'top'
    });
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
    persistent: true
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

      // Refresh the list
      await refreshProcesses();
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
/* Theme Aware Styles */
.glass-card {
  background: var(--q-dark-page);
  border: 1px solid var(--q-separator);
  border-radius: 12px;
}

.body--light .glass-card {
  background: #ffffff;
  border: 1px solid #e0e0e0;
}

/* Table Styling - Theme Aware */
.q-markup-table {
  background: var(--q-dark-page) !important;
}

.body--light .q-markup-table {
  background: #ffffff !important;
}

.q-table {
  background: var(--q-dark-page) !important;
  color: var(--q-primary-text) !important;
}

.q-table th {
  color: var(--q-primary-text) !important;
  font-weight: 600;
  background: var(--q-dark-page) !important;
  border-bottom: 2px solid var(--q-separator) !important;
}

.body--light .q-table th {
  background: #f5f5f5 !important;
  border-bottom: 2px solid #e0e0e0 !important;
}

.q-table td {
  color: var(--q-primary-text) !important;
  background: var(--q-dark-page) !important;
  border-bottom: 1px solid var(--q-separator) !important;
}

.body--light .q-table td {
  background: #ffffff !important;
  border-bottom: 1px solid #eeeeee !important;
}

.q-table tr:hover td {
  background: rgba(255, 255, 255, 0.03) !important;
}

.body--light .q-table tr:hover td {
  background: #f5f5f5 !important;
}

.q-table tbody tr {
  background: var(--q-dark-page) !important;
}

.body--light .q-table tbody tr {
  background: #ffffff !important;
}

/* Process list text colors */
.process-name {
  color: var(--q-primary-text);
}

.process-user {
  color: var(--q-secondary-text);
}

.body--light .process-user {
  color: #757575;
}
</style>
