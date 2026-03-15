import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { adminApi } from '@/api/admin'

export const useAdminStore = defineStore('admin', () => {
  const token = ref(localStorage.getItem('admin_token') || null)
  const adminUser = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email, password) {
    isLoading.value = true
    error.value = null
    try {
      const res = await adminApi.login(email, password)
      token.value = res.data.access_token
      localStorage.setItem('admin_token', res.data.access_token)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Login failed'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    token.value = null
    adminUser.value = null
    localStorage.removeItem('admin_token')
  }

  return { token, adminUser, isLoading, error, isAuthenticated, login, logout }
})
