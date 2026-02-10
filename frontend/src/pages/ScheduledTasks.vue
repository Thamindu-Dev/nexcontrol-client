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
  <div class="scheduled-tasks-page">
    <q-page padding class="q-pl-none q-pr-md">
      <!-- Header Section -->
      <div class="row q-mb-md">
        <div class="col-12">
          <q-card class="action-card" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-center">
                <q-icon name="schedule" size="24px" color="cyan" class="q-mr-sm" />
                <div class="text-h6 text-white">Scheduled Tasks</div>
                <q-space />
                <q-btn
                  @click="showCreateDialog = true"
                  class="action-btn"
                  icon="add"
                  label="New Task"
                  no-caps
                  flat
                />
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Tasks List -->
      <div class="row q-col-gutter-md">
        <div
          v-for="task in tasks"
          :key="task.id"
          class="col-12 col-md-6"
        >
          <q-card class="task-card full-height" flat bordered>
            <q-card-section class="q-pa-md">
              <div class="row items-start">
                <div class="col">
                  <div class="row items-center q-mb-xs">
                    <div class="text-subtitle1 text-white text-weight-bold">
                      {{ task.name }}
                    </div>
                    <q-chip
                      :label="task.enabled ? 'Enabled' : 'Disabled'"
                      :color="task.enabled ? 'positive' : 'grey-9'"
                      :text-color="task.enabled ? 'white' : 'grey-5'"
                      size="sm"
                      class="q-ml-sm status-chip"
                      dense
                    />
                  </div>
                  
                  <div class="row items-center q-mt-sm">
                    <q-icon name="bolt" size="16px" color="cyan" class="q-mr-xs" />
                    <div class="text-body2 text-cyan text-weight-medium">
                      {{ formatAction(task.action) }}
                    </div>
                  </div>
                  
                  <div class="row items-center q-mt-xs">
                    <q-icon name="event" size="16px" color="grey-6" class="q-mr-xs" />
                    <div class="text-caption text-grey-6">
                      {{ formatDateTime(task.scheduled_time) }}
                    </div>
                  </div>
                </div>
                
                <div class="col-auto">
                  <div class="row q-gutter-sm">
                    <q-btn
                      :color="task.enabled ? 'amber' : 'positive'"
                      :icon="task.enabled ? 'pause' : 'play_arrow'"
                      round
                      flat
                      dense
                      class="action-icon-btn"
                      @click="toggleTask(task)"
                    >
                      <q-tooltip>{{ task.enabled ? 'Disable' : 'Enable' }}</q-tooltip>
                    </q-btn>
                    
                    <q-btn
                      color="cyan"
                      icon="edit"
                      round
                      flat
                      dense
                      class="action-icon-btn"
                      @click="openEditDialog(task)"
                    >
                      <q-tooltip>Edit</q-tooltip>
                    </q-btn>
                    
                    <q-btn
                      color="red-5"
                      icon="delete"
                      round
                      flat
                      dense
                      class="action-icon-btn"
                      @click="confirmDelete(task)"
                    >
                      <q-tooltip>Delete</q-tooltip>
                    </q-btn>
                  </div>
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="tasks.length === 0" class="row q-mt-xl justify-center">
        <div class="col-12 col-md-6 text-center">
          <div class="empty-state-container q-pa-xl">
            <q-icon
              name="event_busy"
              size="64px"
              color="grey-9"
              class="q-mb-md"
            />
            <div class="text-h6 text-grey-5 q-mb-sm">
              No tasks scheduled
            </div>
            <div class="text-caption text-grey-7 q-mb-lg">
              Create a task to automate power management actions
            </div>
            <q-btn
              @click="showCreateDialog = true"
              color="cyan"
              label="Create First Task"
              no-caps
              outline
              class="create-btn"
            />
          </div>
        </div>
      </div>

      <!-- Create Task Dialog -->
      <q-dialog v-model="showCreateDialog">
        <q-card class="dialog-card">
          <q-card-section class="row items-center q-pb-none">
            <div class="text-h6 text-white">New Scheduled Task</div>
            <q-space />
            <q-btn icon="close" flat round dense v-close-popup color="grey-5" />
          </q-card-section>

          <q-card-section class="q-pt-md">
            <q-form @submit="createTask" class="q-gutter-md">
              <q-input
                v-model="newTask.name"
                label="Task Name"
                filled
                dense
                input-class="text-white"
                label-color="grey-5"
                class="dark-input"
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
                input-class="text-white"
                label-color="grey-5"
                popup-content-class="dark-menu"
                class="dark-input"
                :rules="[val => !!val || 'Action is required']"
              >
                <template v-slot:option="scope">
                  <q-item v-bind="scope.itemProps" class="dark-item">
                    <q-item-section>
                      <q-item-label>{{ scope.opt.label }}</q-item-label>
                    </q-item-section>
                  </q-item>
                </template>
              </q-select>

              <q-input
                v-model="newTask.scheduled_time"
                label="Scheduled Time"
                type="datetime-local"
                filled
                dense
                input-class="text-white"
                label-color="grey-5"
                class="dark-input"
                :rules="[val => !!val || 'Time is required']"
              />

              <div class="row q-mt-lg justify-end q-gutter-sm">
                <q-btn
                  flat
                  label="Cancel"
                  color="grey-5"
                  v-close-popup
                  no-caps
                />
                <q-btn
                  type="submit"
                  color="cyan"
                  label="Create Task"
                  no-caps
                  :loading="creating"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>
      </q-dialog>

      <!-- Edit Task Dialog -->
      <q-dialog v-model="showEditDialog">
        <q-card class="dialog-card">
          <q-card-section class="row items-center q-pb-none">
            <div class="text-h6 text-white">Edit Task</div>
            <q-space />
            <q-btn icon="close" flat round dense v-close-popup color="grey-5" />
          </q-card-section>

          <q-card-section class="q-pt-md">
            <q-form @submit="updateTask" class="q-gutter-md">
              <q-input
                v-model="editingTask.name"
                label="Task Name"
                filled
                dense
                input-class="text-white"
                label-color="grey-5"
                class="dark-input"
                hint="e.g., Nightly Shutdown"
                :rules="[val => !!val || 'Name is required']"
              />

              <q-select
                v-model="editingTask.action"
                :options="actionOptions"
                label="Action"
                filled
                dense
                emit-value
                map-options
                input-class="text-white"
                label-color="grey-5"
                popup-content-class="dark-menu"
                class="dark-input"
                :rules="[val => !!val || 'Action is required']"
              >
                <template v-slot:option="scope">
                  <q-item v-bind="scope.itemProps" class="dark-item">
                    <q-item-section>
                      <q-item-label>{{ scope.opt.label }}</q-item-label>
                    </q-item-section>
                  </q-item>
                </template>
              </q-select>

              <q-input
                v-model="editingTask.scheduled_time"
                label="Scheduled Time"
                type="datetime-local"
                filled
                dense
                input-class="text-white"
                label-color="grey-5"
                class="dark-input"
                :rules="[val => !!val || 'Time is required']"
              />

              <div class="row q-mt-lg justify-end q-gutter-sm">
                <q-btn
                  flat
                  label="Cancel"
                  color="grey-5"
                  @click="closeEditDialog"
                  no-caps
                />
                <q-btn
                  type="submit"
                  color="cyan"
                  label="Save Changes"
                  no-caps
                  :loading="updating"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>
      </q-dialog>
    </q-page>
  </div>
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
const showEditDialog = ref(false);
const creating = ref(false);
const updating = ref(false);

// New task form
const newTask = reactive({
  name: '',
  action: 'shutdown',
  scheduled_time: ''
});

// Editing task form
const editingTask = reactive({
  id: null,
  name: '',
  action: 'shutdown',
  scheduled_time: ''
});

const actionOptions = [
  { label: 'Shutdown', value: 'shutdown' },
  { label: 'Restart', value: 'restart' },
  { label: 'Hibernate', value: 'hibernate' },
  { label: 'Lock Screen', value: 'lock' }
];

function formatAction(action) {
  const options = {
    shutdown: 'Shutdown',
    restart: 'Restart',
    hibernate: 'Hibernate',
    lock: 'Lock Screen'
  };
  return options[action] || action;
}

/**
 * Format ISO datetime for display
 */
function formatDateTime(isoString) {
  try {
    const date = new Date(isoString);
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return isoString;
  }
}

/**
 * Load all scheduled tasks
 */
async function loadTasks() {
  try {
    const response = await apiService.get('/api/schedule/list');
    // Backend returns array directly
    if (Array.isArray(response)) {
      // Sort by scheduled time
      tasks.value = response.sort((a, b) =>
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

    const response = await apiService.post('/api/schedule/create', {
      name: newTask.name,
      action: newTask.action,
      scheduled_time: isoTime
    });

    // Backend returns ScheduledTask object directly
    if (response && response.id) {
      $q.notify({
        type: 'positive',
        message: 'Task created successfully',
        position: 'top',
        color: 'positive'
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
async function toggleTask(task) {
  try {
    const response = await apiService.post(`/api/schedule/${task.id}/toggle`);

    // Backend returns ScheduledTask object or null
    if (response && response.id) {
      $q.notify({
        type: 'positive',
        message: `Task ${response.enabled ? 'enabled' : 'disabled'}`,
        color: 'positive',
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
    class: 'glass-dialog',
    cancel: {
      color: 'grey-5',
      flat: true
    },
    ok: {
      color: 'red',
      label: 'Delete'
    },
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
        color: 'positive',
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
 * Open edit dialog with task data
 */
async function openEditDialog(task) {
  try {
    // Use local task data directly
    const taskData = task;

    // Convert ISO datetime to datetime-local format for input
    const date = new Date(taskData.scheduled_time);
    // Adjust for timezone offset
    const offset = date.getTimezoneOffset() * 60000;
    const localISOTime = new Date(date.getTime() - offset).toISOString().slice(0, 16);

    editingTask.id = taskData.id;
    editingTask.name = taskData.name;
    editingTask.action = taskData.action;
    editingTask.scheduled_time = localISOTime;

    showEditDialog.value = true;
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to load task details',
      position: 'top'
    });
  }
}

/**
 * Close edit dialog and reset form
 */
function closeEditDialog() {
  showEditDialog.value = false;
  resetEditForm();
}

/**
 * Update an existing task
 */
async function updateTask() {
  updating.value = true;

  try {
    // Convert datetime-local to ISO format
    const isoTime = new Date(editingTask.scheduled_time).toISOString();

    const response = await apiService.put(`/api/schedule/${editingTask.id}`, {
      name: editingTask.name,
      action: editingTask.action,
      scheduled_time: isoTime
    });

    // Backend returns ScheduledTask object or null
    if (response && response.id) {
      $q.notify({
        type: 'positive',
        message: 'Task updated successfully',
        color: 'positive',
        position: 'top'
      });

      closeEditDialog();
      await loadTasks();
    } else {
      throw new Error('Task not found');
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to update task',
      position: 'top'
    });
  } finally {
    updating.value = false;
  }
}

/**
 * Reset the edit form
 */
function resetEditForm() {
  editingTask.id = null;
  editingTask.name = '';
  editingTask.action = 'shutdown';
  editingTask.scheduled_time = '';
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
.scheduled-tasks-page {
  min-height: 100vh;
  position: relative;
  background: #000000;
}

/* Card Styling - Match Dashboard */
.action-card,
.task-card,
.dialog-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.task-card:hover {
  border-color: #444444;
  transform: translateY(-2px);
}

/* Action Button */
.action-btn {
  background: rgba(34, 211, 238, 0.1);
  color: #22d3ee;
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(34, 211, 238, 0.2);
}

.create-btn {
  border-radius: 8px;
  padding: 8px 24px;
}

/* Icon Buttons */
.action-icon-btn {
  opacity: 0.7;
  transition: all 0.2s;
}

.action-icon-btn:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.05);
}

/* Form Inputs */
.dark-input :deep(.q-field__native) {
  color: white !important;
}

.dark-input :deep(.q-field__label) {
  color: #9e9e9e !important;
}

.dark-input :deep(.q-field__control) {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.dark-input :deep(.q-field__marginal) {
  color: #9e9e9e !important;
}

/* Empty State */
.empty-state-container {
  border: 2px dashed #333;
  border-radius: 12px;
  opacity: 0.7;
}

/* Status Chip */
.status-chip {
  font-weight: 600;
}

/* Dark Menu for Select */
:global(.dark-menu) {
  background: #1a1a1a !important;
  border: 1px solid #333;
}

:global(.dark-item) {
  color: white;
}

:global(.dark-item:hover) {
  background: rgba(255, 255, 255, 0.1);
}

/* Dialog Styles */
:global(.glass-dialog) {
  background: #0A0A0A !important;
  border: 1px solid #333333;
}

:global(.glass-dialog .q-dialog__title),
:global(.glass-dialog .q-dialog__message) {
  color: white !important;
}
</style>
