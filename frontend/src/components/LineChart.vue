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
  <div class="chart-container">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue';
import { Chart, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

// Define component name for ESLint multi-word rule
defineOptions({
  name: 'LineChart'
});

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  options: {
    type: Object,
    default: () => ({})
  },
  height: {
    type: Number,
    default: 200
  }
});

const canvasRef = ref(null);
let chartInstance = null;

// Default chart options for dark theme
const defaultOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: 'rgba(255, 255, 255, 0.7)'
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(255, 255, 255, 0.1)'
      },
      ticks: {
        color: 'rgba(255, 255, 255, 0.7)'
      }
    },
    y: {
      grid: {
        color: 'rgba(255, 255, 255, 0.1)'
      },
      ticks: {
        color: 'rgba(255, 255, 255, 0.7)'
      },
      beginAtZero: true,
      max: 100
    }
  },
  interaction: {
    intersect: false,
    mode: 'index'
  },
  ...props.options
}));

/**
 * Initialize chart
 */
function initChart() {
  if (!canvasRef.value) return;

  const ctx = canvasRef.value.getContext('2d');

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: props.data,
    options: defaultOptions.value
  });
}

/**
 * Update chart data
 */
function updateChart() {
  if (chartInstance && props.data) {
    chartInstance.data = props.data;
    chartInstance.options = defaultOptions.value;
    chartInstance.update('none'); // 'none' mode for better performance
  }
}

/**
 * Destroy chart
 */
function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
}

// Watch for data changes
watch(() => props.data, () => {
  updateChart();
}, { deep: true });

onMounted(() => {
  initChart();
});

onBeforeUnmount(() => {
  destroyChart();
});
</script>

<style scoped>
.chart-container {
  position: relative;
  height: v-bind('height + "px"');
  width: 100%;
}
</style>
