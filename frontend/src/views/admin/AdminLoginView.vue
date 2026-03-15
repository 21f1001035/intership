<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useAdminStore } from '@/stores/admin'

const router = useRouter()
const store = useAdminStore()

const form = reactive({ email: '', password: '' })
const errors = reactive({})
const showPassword = ref(false)
const serverError = ref('')

function validate() {
  const e = {}
  if (!form.email.trim()) e.email = 'Email is required.'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Enter a valid email address.'
  if (!form.password) e.password = 'Password is required.'
  Object.keys(errors).forEach((k) => delete errors[k])
  Object.assign(errors, e)
  return Object.keys(e).length === 0
}

async function handleLogin() {
  serverError.value = ''
  if (!validate()) return
  try {
    await store.login(form.email, form.password)
    router.push('/admin/dashboard')
  } catch {
    serverError.value = store.error || 'Login failed. Please check your credentials.'
  }
}
</script>

<template>
  <div class="min-h-screen bg-dark-900 flex items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <!-- Brand -->
      <div class="text-center mb-8">
        <div class="w-14 h-14 rounded-2xl bg-brand-red flex items-center justify-center mx-auto mb-4 shadow-lg">
          <span class="text-white font-bold text-sm">IIT</span>
        </div>
        <h1 class="text-xl font-bold text-neutral-100">IIT Ropar</h1>
        <p class="text-sm text-neutral-500 mt-1">AI/ML Internship Screening Portal</p>
      </div>

      <!-- Card -->
      <div class="bg-dark-700 border border-dark-500 rounded-2xl p-8">
        <h2 class="text-base font-semibold text-neutral-200 mb-6">Admin Portal</h2>

        <ErrorAlert :message="serverError" @dismiss="serverError = ''" class="mb-5" />

        <form @submit.prevent="handleLogin" novalidate class="space-y-4">
          <!-- Email -->
          <div>
            <label class="label">Email Address</label>
            <input
              v-model="form.email"
              type="email"
              autocomplete="email"
              placeholder="admin@iitrpr.ac.in"
              class="input-field"
            />
            <p v-if="errors.email" class="text-red-400 text-xs mt-1">{{ errors.email }}</p>
          </div>

          <!-- Password -->
          <div>
            <label class="label">Password</label>
            <div class="relative">
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="Enter your password"
                class="input-field pr-10"
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 transition-colors"
                @click="showPassword = !showPassword"
                tabindex="-1"
              >
                <svg v-if="!showPassword" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              </button>
            </div>
            <p v-if="errors.password" class="text-red-400 text-xs mt-1">{{ errors.password }}</p>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="store.isLoading"
            class="btn-primary w-full py-3 flex items-center justify-center gap-2 mt-2"
          >
            <LoadingSpinner v-if="store.isLoading" />
            <span>{{ store.isLoading ? 'Signing in...' : 'Sign In' }}</span>
          </button>
        </form>
      </div>

      <p class="text-center text-xs text-neutral-600 mt-6">
        IIT Ropar AI/ML Internship Screening System · Admin Access Only
      </p>
    </div>
  </div>
</template>
