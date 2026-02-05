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
    <!-- Alert Controls -->
    <div class="row q-mb-md q-gutter-sm">
      <q-btn
        v-if="alerts.length > 0 && hasUnacknowledgedAlerts"
        outline
        color="white"
        icon="done_all"
        label="Acknowledge All"
        @click="confirmAcknowledgeAll"
      />
      <q-btn
        v-if="alerts.length > 0"
        flat
        color="negative"
        icon="delete_sweep"
        label="Clear All"
        @click="clearAllAlerts"
      />
      <q-space />
      <q-btn
        flat
        round
        dense
        icon="refresh"
        :loading="loading"
        @click="loadAlerts"
      >
        <q-tooltip>Refresh from server</q-tooltip>
      </q-btn>
    </div>
    <div class="text-caption text-grey q-mb-md">
      View and manage system threshold alerts
    </div>

    <!-- Alert Statistics Cards -->
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col-6">
        <q-card flat bordered class="stat-card">
          <q-card-section class="q-pa-md">
            <div class="text-caption text-grey-6">Total Alerts</div>
            <div class="text-h4 text-weight-bold text-white">{{ alerts.length }}</div>
          </q-card-section>
        </q-card>
      </div>
      <div class="col-6">
        <q-card flat bordered class="stat-card">
          <q-card-section class="q-pa-md">
            <div class="text-caption text-grey-6">Unacknowledged</div>
            <div class="text-h4 text-weight-bold" :class="hasUnacknowledgedAlerts ? 'text-negative' : 'text-positive'">
              {{ unacknowledgedCount }}
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Alerts List -->
    <div v-if="loading && alerts.length === 0" class="row q-mt-xl">
      <div class="col-12 text-center">
        <q-spinner color="grey-6" size="40px" />
        <div class="text-caption text-grey-7 q-mt-sm">Loading alerts...</div>
      </div>
    </div>

    <!-- No Alerts State -->
    <div v-else-if="alerts.length === 0 && !loading" class="row q-mt-xl">
      <div class="col-12 text-center">
        <q-icon
          name="check_circle"
          size="80px"
          :color="hasUnacknowledgedAlerts ? 'grey-6' : 'positive'"
        />
        <div class="text-h6 text-grey q-mt-md">
          {{ hasUnacknowledgedAlerts ? 'No active alerts' : 'All clear!' }}
        </div>
        <div class="text-caption text-grey">
          {{ hasUnacknowledgedAlerts ? 'System is running within normal thresholds' : 'No threshold alerts to display' }}
        </div>
      </div>
    </div>

    <!-- Alerts Cards -->
    <div v-else class="q-gutter-md">
      <q-card
        v-for="alert in sortedAlerts"
        :key="alert.id"
        :class="['alert-card', getAlertClass(alert)]"
        flat
        bordered
      >
        <q-card-section class="q-pa-md">
          <div class="row items-center">
            <div class="col-auto q-mr-sm">
              <q-icon
                :name="getAlertIcon(alert)"
                :color="getAlertColor(alert)"
                size="32px"
              />
            </div>
            <div class="col">
              <div class="row items-center q-gutter-xs">
                <div class="text-subtitle1 text-white">
                  {{ getAlertTitle(alert) }}
                </div>
                <q-chip
                  v-if="alert.acknowledged"
                  label="Acknowledged"
                  size="sm"
                  color="grey-7"
                  text-color="grey-3"
                />
                <q-chip
                  v-else
                  label="Active"
                  size="sm"
                  color="negative"
                  text-color="white"
                />
              </div>
              <div class="text-caption text-grey q-mt-xs">
                {{ formatDateTime(alert.triggered_at) }}
              </div>
              <div class="text-caption q-mt-xs">
                <span :class="getValueClass(alert)">
                  {{ alert.value?.toFixed(1) || 'N/A' }}{{ alert.unit || '%' }}
                </span>
                exceeded threshold of {{ alert.threshold?.toFixed(1) || 'N/A' }}{{ alert.unit || '%' }}
              </div>
            </div>
            <div class="col-auto">
              <q-btn
                v-if="!alert.acknowledged"
                outline
                color="white"
                icon="done"
                label="Acknowledge"
                size="sm"
                @click="acknowledgeAlert(alert.id)"
              />
            </div>
          </div>
        </q-card-section>
      </q-card>
    </div>

    <!-- Configure Thresholds Link -->
    <div class="row q-mt-lg">
      <div class="col-12 text-center">
        <q-btn
          flat
          color="cyan"
          icon="settings"
          label="Configure Thresholds"
          to="/settings"
        />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useQuasar } from 'quasar';
import { storeToRefs } from 'pinia';
import { useSystemStore } from '../stores/system';
import api from '../services/ApiService';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'ThresholdAlertsPage'
});

const $q = useQuasar();
const systemStore = useSystemStore();

// Use storeToRefs for reactive access to store properties
const { alerts, unacknowledgedAlertCount } = storeToRefs(systemStore);

// State
const loading = ref(false);

// Computed
const sortedAlerts = computed(() => {
  return [...alerts.value].sort((a, b) => {
    // Sort by: unacknowledged first, then by time (newest first)
    if (a.acknowledged !== b.acknowledged) {
      return a.acknowledged ? 1 : -1;
    }
    return new Date(b.triggered_at) - new Date(a.triggered_at);
  });
});

const hasUnacknowledgedAlerts = computed(() => {
  return alerts.value.some(alert => !alert.acknowledged);
});

/**
 * Get alert icon based on type
 */
function getAlertIcon(alert) {
  switch (alert.metric_type) {
    case 'cpu':
      return 'memory';
    case 'memory':
      return 'storage';
    case 'disk':
      return 'folder_open';
    default:
      return 'warning';
  }
}

/**
 * Get alert color based on severity
 */
function getAlertColor(alert) {
  if (alert.acknowledged) return 'grey-6';

  const severity = getSeverityLevel(alert);
  switch (severity) {
    case 'critical': return 'red';
    case 'warning': return 'orange';
    case 'info': return 'yellow';
    default: return 'grey-6';
  }
}

/**
 * Get alert class for styling
 */
function getAlertClass(alert) {
  if (alert.acknowledged) return 'alert-acknowledged';

  const severity = getSeverityLevel(alert);
  return `alert-${severity}`;
}

/**
 * Get alert title
 */
function getAlertTitle(alert) {
  const type = alert.metric_type?.toUpperCase() || 'UNKNOWN';
  return `${type} Threshold Alert`;
}

/**
 * Get severity level
 */
function getSeverityLevel(alert) {
  const value = alert.value || 0;
  const threshold = alert.threshold || 100;

  const percentage = (value / threshold) * 100;

  if (percentage >= 120 || value >= 95) return 'critical';
  if (percentage >= 110 || value >= 90) return 'warning';
  return 'info';
}

/**
 * Get value class for coloring
 */
function getValueClass(alert) {
  if (alert.acknowledged) return 'text-grey-6';

  const severity = getSeverityLevel(alert);
  switch (severity) {
    case 'critical': return 'text-negative text-weight-bold';
    case 'warning': return 'text-orange';
    case 'info': return 'text-yellow';
    default: return 'text-grey-6';
  }
}

/**
 * Format datetime
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
 * Load all alerts from server (optional - for server-side persistence)
 */
async function loadAlerts() {
  loading.value = true;

  try {
    const response = await api.get('/api/threshold/alerts');

    if (response.success && response.alerts) {
      // Merge server alerts with local alerts (local alerts take precedence for recent ones)
      const localAlertIds = new Set(alerts.value.map(a => a.id));
      const serverAlerts = response.alerts.filter(a => !localAlertIds.has(a.id));

      // Add server alerts to the beginning (older alerts)
      alerts.value = [...alerts.value, ...serverAlerts];

      console.log(`[ThresholdAlerts] Loaded ${serverAlerts.length} server alerts, total: ${alerts.value.length}`);
    }
  } catch (error) {
    console.error('[ThresholdAlerts] Failed to load alerts from server:', error);
    // Don't show notification - local alerts are still available
  } finally {
    loading.value = false;
  }
}

/**
 * Acknowledge single alert
 */
function acknowledgeAlert(alertId) {
  try {
    // Update local state immediately for instant feedback
    systemStore.acknowledgeAlert(alertId);

    $q.notify({
      type: 'positive',
      message: 'Alert acknowledged',
      position: 'top'
    });

    // Optionally sync with server (non-blocking)
    api.put(`/api/threshold/alerts/${alertId}/acknowledge`).catch(err => {
      console.warn('[ThresholdAlerts] Failed to sync acknowledge with server:', err);
    });
  } catch (error) {
    console.error('[ThresholdAlerts] Failed to acknowledge alert:', error);
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to acknowledge alert',
      position: 'top'
    });
  }
}

/**
 * Confirm acknowledge all alerts
 */
function confirmAcknowledgeAll() {
  $q.dialog({
    title: 'Acknowledge All Alerts',
    message: `Are you sure you want to acknowledge all ${unacknowledgedAlertCount.value} active alerts?`,
    cancel: true,
    persistent: true
  }).onOk(() => {
    acknowledgeAllAlerts();
  });
}

/**
 * Acknowledge all alerts
 */
function acknowledgeAllAlerts() {
  try {
    // Update local state immediately for instant feedback
    systemStore.acknowledgeAllAlerts();

    $q.notify({
      type: 'positive',
      message: 'All alerts acknowledged',
      position: 'top'
    });

    // Optionally sync with server (non-blocking)
    api.put('/api/threshold/alerts/acknowledge-all').catch(err => {
      console.warn('[ThresholdAlerts] Failed to sync acknowledge all with server:', err);
    });
  } catch (error) {
    console.error('[ThresholdAlerts] Failed to acknowledge all alerts:', error);
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to acknowledge alerts',
      position: 'top'
    });
  }
}

/**
 * Clear all alerts
 */
function clearAllAlerts() {
  $q.dialog({
    title: 'Clear All Alerts',
    message: 'Are you sure you want to delete all alerts? This cannot be undone.',
    cancel: true,
    persistent: true
  }).onOk(() => {
    systemStore.clearAlerts();
    $q.notify({
      type: 'positive',
      message: 'All alerts cleared',
      position: 'top'
    });
  });
}

/**
 * Handle WebSocket alert event
 */
function handleWebSocketAlert(data) {
  console.log('[ThresholdAlerts] Received alert via WebSocket:', data);

  // Add new alert to the beginning of the list
  if (data && data.id) {
    alerts.value.unshift(data);

    // Show notification
    $q.notify({
      type: 'negative',
      message: `${data.metric_type?.toUpperCase() || 'System'} threshold exceeded: ${data.value}${data.unit || '%'}`,
      position: 'top',
      timeout: 5000,
      actions: [{ icon: 'close', color: 'white', round: true, dense: true }]
    });
  }
}

/**
 * Lifecycle
 */
onMounted(() => {
  loadAlerts();

  // Listen for WebSocket threshold alerts
  const wsService = systemStore.wsService;
  if (wsService) {
    wsService.on('threshold_alert', handleWebSocketAlert);
  }
});

onUnmounted(() => {
  // Remove WebSocket listener
  const wsService = systemStore.wsService;
  if (wsService) {
    wsService.off('threshold_alert', handleWebSocketAlert);
  }
});
</script>

<style scoped>
/* OLED Theme Styles */
.q-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
}

.stat-card {
  background: #000000;
  border: 1px solid #333333;
  border-radius: 12px;
}

/* Alert Card Styles */
.alert-card {
  transition: all 0.2s ease;
}

.alert-critical {
  border-left: 4px solid #ef4444;
  background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, transparent 100%);
}

.alert-warning {
  border-left: 4px solid #f97316;
  background: linear-gradient(90deg, rgba(249, 115, 22, 0.1) 0%, transparent 100%);
}

.alert-info {
  border-left: 4px solid #eab308;
  background: linear-gradient(90deg, rgba(234, 179, 8, 0.1) 0%, transparent 100%);
}

.alert-acknowledged {
  opacity: 0.6;
  border-left: 4px solid #6b7280;
}

.alert-card:hover {
  border-color: #444444;
}

.alert-acknowledged:hover {
  opacity: 0.8;
}
</style>
