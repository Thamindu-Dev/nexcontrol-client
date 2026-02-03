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
        <div class="text-h5">Scheduled Tasks</div>
        <div class="text-caption text-grey">
          Schedule power management tasks for specific times
        </div>
      </div>
    </div>

    <!-- Create New Task Button -->
    <div class="row q-mb-md">
      <div class="col-12">
        <q-btn
          @click="showCreateDialog = true"
          outline
          color="white"
          icon="add"
          label="Create New Task"
          class="full-width"
        />
      </div>
    </div>

    <!-- Tasks List -->
    <div class="row q-gutter-md">
      <div
        v-for="task in tasks"
        :key="task.id"
        class="col-12"
      >
        <q-card class="glass-card">
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-subtitle1">
                  {{ task.name }}
                  <q-chip
                    :label="task.enabled ? 'Enabled' : 'Disabled'"
                    :color="task.enabled ? 'positive' : 'grey'"
                    size="sm"
                    class="q-ml-sm"
                  />
                </div>
                <div class="text-caption text-grey q-mt-xs">
                  Action: <strong>{{ task.action }}</strong><br>
                  Scheduled: {{ formatDateTime(task.scheduled_time) }}
                </div>
              </div>
              <div class="col-auto">
                <div class="row q-gutter-xs">
                  <q-btn
                    :color="task.enabled ? 'grey-7' : 'grey-6'"
                    :icon="task.enabled ? 'pause' : 'play_arrow'"
                    round
                    flat
                    size="sm"
                    @click="toggleTask(task.id)"
                  >
                    <q-tooltip>{{ task.enabled ? 'Disable' : 'Enable' }} task</q-tooltip>
                  </q-btn>
                  <q-btn
                    color="grey-8"
                    icon="delete"
                    round
                    flat
                    size="sm"
                    @click="confirmDelete(task)"
                  >
                    <q-tooltip>Delete task</q-tooltip>
                  </q-btn>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="tasks.length === 0" class="row q-mt-xl">
      <div class="col-12 text-center">
        <q-icon
          name="schedule"
          size="100px"
          color="grey-4"
        />
        <div class="text-h6 text-grey q-mt-md">
          No scheduled tasks
        </div>
        <div class="text-caption text-grey">
          Create a task to schedule power management actions
        </div>
      </div>
    </div>

    <!-- Create Task Dialog -->
    <q-dialog v-model="showCreateDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Create Scheduled Task</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="createTask" class="q-gutter-md">
            <q-input
              v-model="newTask.name"
              label="Task Name"
              filled
              dense
              hint="e.g., Nightly Shutdown"
              :rules="[val => !!val || 'Name is required']"
            />

            <q-select
              v-model="newTask.action"
              :options="actionOptions"
              label="Action"
              filled
              dense
              emit-value
              map-options
              :rules="[val => !!val || 'Action is required']"
            />

            <q-input
              v-model="newTask.scheduled_time"
              label="Scheduled Time"
              type="datetime-local"
              filled
              dense
              :rules="[val => !!val || 'Time is required']"
            />

            <div class="row q-mt-md">
              <div class="col-6 q-pr-sm">
                <q-btn
                  flat
                  label="Cancel"
                  class="full-width"
                  v-close-popup
                />
              </div>
              <div class="col-6 q-pl-sm">
                <q-btn
                  type="submit"
                  outline
                  color="white"
                  label="Create"
                  class="full-width"
                  :loading="creating"
                />
              </div>
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import apiService from '../services/ApiService';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'ScheduledTasksPage'
});

const $q = useQuasar();

// State
const tasks = ref([]);
const showCreateDialog = ref(false);
const creating = ref(false);

// New task form
const newTask = reactive({
  name: '',
  action: 'shutdown',
  scheduled_time: ''
});

const actionOptions = [
  { label: 'Shutdown', value: 'shutdown' },
  { label: 'Restart', value: 'restart' },
  { label: 'Hibernate', value: 'hibernate' }
];

/**
 * Format ISO datetime for display
 */
function formatDateTime(isoString) {
  try {
    const date = new Date(isoString);
    return date.toLocaleString();
  } catch {
    return isoString;
  }
}

/**
 * Load all scheduled tasks
 */
async function loadTasks() {
  try {
    const response = await apiService.get('/api/schedule');
    if (response.success) {
      // Sort by scheduled time
      tasks.value = response.tasks.sort((a, b) =>
        new Date(a.scheduled_time) - new Date(b.scheduled_time)
      );
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to load tasks',
      position: 'top'
    });
  }
}

/**
 * Create a new scheduled task
 */
async function createTask() {
  creating.value = true;

  try {
    // Convert datetime-local to ISO format
    const isoTime = new Date(newTask.scheduled_time).toISOString();

    const response = await apiService.post('/api/schedule', {
      name: newTask.name,
      action: newTask.action,
      scheduled_time: isoTime
    });

    if (response.success) {
      $q.notify({
        type: 'positive',
        message: 'Task created successfully',
        position: 'top'
      });

      showCreateDialog.value = false;
      resetForm();
      await loadTasks();
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to create task',
      position: 'top'
    });
  } finally {
    creating.value = false;
  }
}

/**
 * Toggle task enabled state
 */
async function toggleTask(taskId) {
  try {
    const response = await apiService.put(`/api/schedule/${taskId}/toggle`);

    if (response.success) {
      $q.notify({
        type: 'positive',
        message: response.message,
        position: 'top'
      });
      await loadTasks();
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to toggle task',
      position: 'top'
    });
  }
}

/**
 * Confirm task deletion
 */
function confirmDelete(task) {
  $q.dialog({
    title: 'Delete Task',
    message: `Are you sure you want to delete "${task.name}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    await deleteTask(task.id);
  });
}

/**
 * Delete a task
 */
async function deleteTask(taskId) {
  try {
    const response = await apiService.delete(`/api/schedule/${taskId}`);

    if (response.success) {
      $q.notify({
        type: 'positive',
        message: 'Task deleted successfully',
        position: 'top'
      });
      await loadTasks();
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to delete task',
      position: 'top'
    });
  }
}

/**
 * Reset the create form
 */
function resetForm() {
  newTask.name = '';
  newTask.action = 'shutdown';
  newTask.scheduled_time = '';
}

/**
 * Load tasks on mount
 */
onMounted(() => {
  loadTasks();
});
</script>

<style scoped>
/* OLED Theme Styles */
.glass-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
}

/* Dialog Styling */
:deep(.q-card) {
  background: #0A0A0A;
  border: 1px solid #333333;
  color: #FFFFFF;
}
</style>


