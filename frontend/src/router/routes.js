/**
 * ==============================================================================
 * NexControl - Remote PC Controller
 * Copyright (C) 2026 Thamindu-Dev
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * ==============================================================================
 */

const routes = [
  {
    path: '/login',
    component: () => import('pages/Login.vue'),
    meta: { requiresAuth: false }
  },

  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        component: () => import('pages/Dashboard.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'docker',
        component: () => import('pages/Docker.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'processes',
        component: () => import('pages/Processes.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'screenshot',
        component: () => import('pages/Screenshot.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'wol',
        component: () => import('pages/WoL.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'settings',
        component: () => import('pages/Settings.vue'),
        meta: { requiresAuth: true }
      }
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes
