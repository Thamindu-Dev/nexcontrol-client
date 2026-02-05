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
  <div class="fullscreen bg-black text-white text-center q-pa-md flex flex-center error-page">
    <div class="error-content">
      <div style="font-size: 30vh">404</div>

      <div class="text-h2" style="opacity: 0.4">Oops. Nothing here...</div>

      <q-btn
        class="q-mt-xl go-home-btn"
        color="white"
        text-color="black"
        unelevated
        to="/"
        label="Go Home"
        no-caps
      />
    </div>
  </div>
</template>

<script setup>
//
</script>

<style scoped>
/* Ensure page and button are clickable */
.error-page {
  position: relative !important;
  z-index: 1 !important;
}

.error-content {
  position: relative !important;
  z-index: 10 !important;
}

.go-home-btn {
  position: relative !important;
  pointer-events: auto !important;
}
</style>
