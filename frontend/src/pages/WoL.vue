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
        <div class="text-h5">Wake on LAN</div>
        <div class="text-caption text-grey q-mt-sm">
          Send Wake-on-LAN magic packets to remotely power on PCs on your local network.
        </div>
      </div>
    </div>

    <!-- Add Target Device -->
    <div class="row q-mb-md">
      <div class="col-12 col-md-6">
        <q-card>
          <q-card-section>
            <div class="text-h6">Add Target Device</div>
          </q-card-section>

          <q-card-section>
            <q-form @submit="addDevice" class="q-gutter-md">
              <q-input
                v-model="newDevice.name"
                label="Device Name"
                filled
                dense
                hint="e.g., Gaming PC, Work Laptop"
                :rules="[val => !!val || 'Name is required']"
              />

              <q-input
                v-model="newDevice.mac"
                label="MAC Address"
                filled
                dense
                hint="e.g., 00:11:22:33:44:55 or 00-11-22-33-44-55"
                :rules="[val => !!val || 'MAC address is required', isValidMac]"
                @input="formatMac"
              />

              <q-input
                v-model="newDevice.broadcast"
                label="Broadcast IP"
                filled
                dense
                hint="e.g., 192.168.1.255 (default: 255.255.255.255)"
              />

              <q-input
                v-model.number="newDevice.port"
                label="Port"
                type="number"
                filled
                dense
                hint="Default: 9"
              />

              <div class="row q-mt-md">
                <div class="col-12">
                  <q-btn
                    type="submit"
                    color="white"
                    class="full-width"
                    label="Add Device"
                  />
                </div>
              </div>
            </q-form>
          </q-card-section>
        </q-card>
      </div>

      <!-- How it Works -->
      <div class="col-12 col-md-6 q-mt-md q-mt-md-none">
        <q-card>
          <q-card-section>
            <div class="text-h6">How Wake-on-LAN Works</div>
          </q-card-section>

          <q-card-section>
            <div class="text-body2 q-gutter-sm">
              <p>
                <strong>1. Enable WoL in BIOS/UEFI:</strong><br>
                Restart your PC and enter BIOS/UEFI settings. Look for "Wake-on-LAN", "Wake on LAN", or "Power On by PCI-E/PCI" and enable it.
              </p>

              <p>
                <strong>2. Configure Network Adapter:</strong><br>
                In Windows, go to Device Manager → Network Adapters → Properties → Power Management → Check "Allow this device to wake the computer".
              </p>

              <p>
                <strong>3. Find MAC Address:</strong><br>
                Windows: <code>ipconfig /all</code><br>
                Linux: <code>ip link</code><br>
                macOS: <code>ifconfig</code>
              </p>

              <p>
                <strong>4. Device Must Be Off:</strong><br>
                WoL only works when the PC is in soft-off state (plugged in but powered off), not in hibernation or sleep.
              </p>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Saved Devices -->
    <div class="row q-mt-md">
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="row items-center q-gutter-sm">
              <div class="text-h6">Saved Devices</div>
              <q-space />
              <q-btn
                flat
                round
                dense
                icon="refresh"
                @click="loadDevices"
              />
            </div>
          </q-card-section>

          <q-card-section>
            <!-- Empty State -->
            <div v-if="devices.length === 0" class="text-center q-pa-xl">
              <q-icon
                name="computer"
                size="xl"
                color="grey"
                class="q-mb-md"
              />
              <div class="text-h6">No devices added</div>
              <div class="text-caption text-grey q-mt-sm">
                Add devices above to send Wake-on-LAN magic packets.
              </div>
            </div>

            <!-- Device List -->
            <q-list v-else separator>
              <q-item v-for="device in devices" :key="device.id">
                <q-item-section avatar>
                  <q-icon name="computer" size="md" />
                </q-item-section>

                <q-item-section>
                  <q-item-label>{{ device.name }}</q-item-label>
                  <q-item-label caption>
                    MAC: {{ device.mac }} | Broadcast: {{ device.broadcast || '255.255.255.255' }} | Port: {{ device.port || 9 }}
                  </q-item-label>
                </q-item-section>

                <q-item-section side>
                  <div class="row q-gutter-xs">
                    <q-btn
                      flat
                      round
                      color="white"
                      icon="power_settings_new"
                      @click="wakeDevice(device)"
                      :loading="waking[device.id]"
                    >
                      <q-tooltip>Wake Device</q-tooltip>
                    </q-btn>
                    <q-btn
                      flat
                      round
                      color="negative"
                      icon="delete"
                      @click="confirmDeleteDevice(device)"
                    >
                      <q-tooltip>Delete</q-tooltip>
                    </q-btn>
                  </div>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useQuasar } from 'quasar';
import { useSettingsStore } from '../stores/settings';

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'WakeOnLanPage'
});

const $q = useQuasar();
const settingsStore = useSettingsStore();

// State
const devices = ref([]);
const waking = ref({});
const newDevice = reactive({
  name: '',
  mac: '',
  broadcast: '',
  port: 9
});

/**
 * Format MAC address
 */
function formatMac(value) {
  // Remove all non-hex characters
  let cleaned = value.replace(/[^a-fA-F0-9]/g, '').toUpperCase();

  // Limit to 12 characters (6 bytes)
  if (cleaned.length > 12) {
    cleaned = cleaned.substring(0, 12);
  }

  // Format with colons
  if (cleaned.length > 2) {
    const parts = [];
    for (let i = 0; i < cleaned.length; i += 2) {
      parts.push(cleaned.substring(i, i + 2));
    }
    newDevice.mac = parts.join(':');
  }
}

/**
 * Validate MAC address
 */
function isValidMac(val) {
  const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
  return macRegex.test(val) || 'Invalid MAC address format';
}

/**
 * Add device
 */
function addDevice() {
  if (!newDevice.name || !newDevice.mac || !isValidMac(newDevice.mac)) {
    $q.notify({
      type: 'negative',
      message: 'Please fill all required fields correctly',
      position: 'top'
    });
    return;
  }

  const device = {
    id: Date.now(),
    name: newDevice.name,
    mac: newDevice.mac.toUpperCase(),
    broadcast: newDevice.broadcast || '255.255.255.255',
    port: newDevice.port || 9
  };

  devices.value.push(device);
  saveDevices();

  // Reset form
  newDevice.name = '';
  newDevice.mac = '';
  newDevice.broadcast = '';
  newDevice.port = 9;

  $q.notify({
    type: 'positive',
    message: 'Device added successfully',
    position: 'top'
  });
}

/**
 * Confirm delete device
 */
function confirmDeleteDevice(device) {
  $q.dialog({
    title: 'Delete Device',
    message: `Are you sure you want to delete ${device.name}?`,
    cancel: true,
    persistent: true
  }).onOk(() => {
    deleteDevice(device.id);
  });
}

/**
 * Delete device
 */
function deleteDevice(deviceId) {
  devices.value = devices.value.filter(d => d.id !== deviceId);
  saveDevices();

  $q.notify({
    type: 'info',
    message: 'Device deleted',
    position: 'top'
  });
}

/**
 * Wake device
 */
async function wakeDevice(device) {
  waking.value[device.id] = true;

  try {
    // In a browser environment, we need to forward this to the backend
    // since browsers cannot send raw UDP packets
    const WoLService = (await import('../services/WoLService')).default;
    await WoLService.sendMagicPacket(device.mac, device.broadcast, device.port);

    $q.notify({
      type: 'positive',
      message: `Magic packet sent to ${device.name}`,
      position: 'top'
    });
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: error.message || 'Failed to send magic packet',
      position: 'top'
    });
  } finally {
    waking.value[device.id] = false;
  }
}

/**
 * Save devices to local storage
 */
function saveDevices() {
  settingsStore.setWoLDevices(devices.value);
}

/**
 * Load devices from local storage
 */
function loadDevices() {
  const saved = settingsStore.woLDevices;
  if (saved) {
    devices.value = [...saved];
  }
}

/**
 * Lifecycle
 */
onMounted(() => {
  loadDevices();
});
</script>
