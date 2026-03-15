<script setup>
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'

const router = useRouter()
const adminStore = useAdminStore()

function logout() {
  adminStore.logout()
  router.push('/admin/login')
}
</script>

<template>
  <aside class="w-64 h-screen bg-dark-800 border-r border-dark-500 flex flex-col fixed left-0 top-0 z-10">
    <!-- Brand -->
    <div class="px-4 py-5 border-b border-dark-500">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-brand-red flex items-center justify-center text-white font-bold text-xs">IIT</div>
        <div>
          <div class="text-neutral-100 font-semibold text-sm">IIT Ropar</div>
          <div class="text-neutral-500 text-xs">Admin Panel</div>
        </div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-3 py-4 space-y-1">
      <router-link
        to="/admin/dashboard"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-150 text-neutral-300 hover:bg-dark-600 hover:text-neutral-100"
        active-class="bg-dark-600 text-neutral-100"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"/>
        </svg>
        Dashboard
      </router-link>
      <router-link
        to="/admin/applications"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-150 text-neutral-300 hover:bg-dark-600 hover:text-neutral-100"
        active-class="bg-dark-600 text-neutral-100"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        Applications
      </router-link>
    </nav>

    <!-- Logout -->
    <div class="px-3 py-4 border-t border-dark-500">
      <button @click="logout" class="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-neutral-400 hover:bg-dark-600 hover:text-neutral-100 transition-colors duration-150">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
        </svg>
        Sign out
      </button>
    </div>
  </aside>
</template>
