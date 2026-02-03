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
  <div class="fullscreen text-white text-center q-pa-md flex flex-center error-page">
    <!-- Animated Background -->
    <div class="animated-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div class="relative-position z-top">
      <div class="glass-card q-pa-xl rounded-borders">
        <div style="font-size: 30vh; line-height: 1" class="text-gradient">404</div>

        <div class="text-h2 text-weight-bold q-mb-md" style="opacity: 0.8">Oops!</div>
        <div class="text-h5 text-grey-4 q-mb-xl">Nothing here...</div>

        <q-btn
          class="glass-btn"
          unelevated
          to="/"
          size="lg"
          no-caps
        >
          <div class="row items-center no-wrap">
            <q-icon name="home" class="q-mr-sm" size="24px" />
            <span>Go Home</span>
          </div>
        </q-btn>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: 'ErrorNotFound'
});
</script>

<style scoped>
.error-page {
  background: #0f0c29;
  overflow: hidden;
}

/* Animated Background */
.animated-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  z-index: 0;
}

/* Animated Orbs */
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
  animation: float 20s infinite;
}

.orb-1 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #3b82f6 0%, transparent 70%);
  top: -50px;
  left: -50px;
}

.orb-2 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
  bottom: -50px;
  right: -50px;
  animation-delay: -5s;
}

.orb-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -50px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}

/* Glass Card */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

/* Glass Button */
.glass-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.glass-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.4);
}

.text-gradient {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
