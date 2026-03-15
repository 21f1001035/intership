<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useApplicationStore } from '@/stores/application'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const router = useRouter()
const appStore = useApplicationStore()

const form = reactive({
  full_name: '',
  email: '',
  phone: '',
  college: '',
  degree: '',
  branch: '',
  year_of_study: '',
  cgpa: '',
  linkedin_url: '',
  github_url: '',
})
const errors = reactive({})
const submitting = ref(false)
const serverError = ref('')

function validate() {
  const e = {}
  if (!form.full_name.trim()) e.full_name = 'Required'
  if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = 'Valid email required'
  if (!form.college.trim()) e.college = 'Required'
  if (!form.degree) e.degree = 'Required'
  if (!form.branch.trim()) e.branch = 'Required'
  if (!form.year_of_study) e.year_of_study = 'Required'
  if (form.cgpa && (parseFloat(form.cgpa) < 0 || parseFloat(form.cgpa) > 10)) e.cgpa = 'Must be between 0 and 10'
  Object.keys(errors).forEach((k) => delete errors[k])
  Object.assign(errors, e)
  return Object.keys(e).length === 0
}

async function submit() {
  serverError.value = ''
  if (!validate()) return
  submitting.value = true
  try {
    const payload = { ...form, year_of_study: parseInt(form.year_of_study), cgpa: form.cgpa ? parseFloat(form.cgpa) : null }
    const data = await appStore.createApplication(payload)
    router.push(`/application/${data.id}/upload`)
  } catch (e) {
    serverError.value = appStore.error || 'Submission failed. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-dark-900 flex flex-col">
    <!-- Top bar -->
    <div class="bg-dark-800 border-b border-dark-500 px-6 py-4">
      <div class="max-w-2xl mx-auto flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-brand-red flex items-center justify-center text-white font-bold text-xs flex-shrink-0">IIT</div>
        <div>
          <div class="text-neutral-100 font-semibold text-sm">IIT Ropar</div>
          <div class="text-neutral-500 text-xs">AI/ML Internship Screening</div>
        </div>
      </div>
    </div>

    <!-- Body -->
    <div class="flex-1 px-4 py-10">
      <div class="max-w-2xl mx-auto">
        <div class="mb-8">
          <h1 class="text-2xl font-semibold text-neutral-100">Apply for AI/ML Internship</h1>
          <p class="text-neutral-400 text-sm mt-1">Fill in your details to begin the screening process.</p>
        </div>

        <ErrorAlert :message="serverError" @dismiss="serverError = ''" class="mb-6" />

        <form @submit.prevent="submit" class="space-y-5">
          <!-- Personal Info -->
          <div class="card">
            <h2 class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-4">Personal Information</h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="label">Full Name <span class="text-red-400">*</span></label>
                <input v-model="form.full_name" type="text" class="input-field" placeholder="Ravi Kumar" />
                <p v-if="errors.full_name" class="text-red-400 text-xs mt-1">{{ errors.full_name }}</p>
              </div>
              <div>
                <label class="label">Email <span class="text-red-400">*</span></label>
                <input v-model="form.email" type="email" class="input-field" placeholder="ravi@example.com" />
                <p v-if="errors.email" class="text-red-400 text-xs mt-1">{{ errors.email }}</p>
              </div>
              <div>
                <label class="label">Phone</label>
                <input v-model="form.phone" type="tel" class="input-field" placeholder="+91 98765 43210" />
              </div>
              <div>
                <label class="label">CGPA</label>
                <input v-model="form.cgpa" type="number" step="0.01" min="0" max="10" class="input-field" placeholder="8.5" />
                <p v-if="errors.cgpa" class="text-red-400 text-xs mt-1">{{ errors.cgpa }}</p>
              </div>
            </div>
          </div>

          <!-- Academic Info -->
          <div class="card">
            <h2 class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-4">Academic Background</h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div class="sm:col-span-2">
                <label class="label">College / University <span class="text-red-400">*</span></label>
                <input v-model="form.college" type="text" class="input-field" placeholder="IIT Ropar" />
                <p v-if="errors.college" class="text-red-400 text-xs mt-1">{{ errors.college }}</p>
              </div>
              <div>
                <label class="label">Degree <span class="text-red-400">*</span></label>
                <select v-model="form.degree" class="input-field">
                  <option value="">Select degree</option>
                  <option v-for="d in ['B.Tech','M.Tech','PhD','B.Sc','M.Sc','MBA','Other']" :key="d" :value="d">{{ d }}</option>
                </select>
                <p v-if="errors.degree" class="text-red-400 text-xs mt-1">{{ errors.degree }}</p>
              </div>
              <div>
                <label class="label">Branch / Department <span class="text-red-400">*</span></label>
                <input v-model="form.branch" type="text" class="input-field" placeholder="Computer Science & Engineering" />
                <p v-if="errors.branch" class="text-red-400 text-xs mt-1">{{ errors.branch }}</p>
              </div>
              <div>
                <label class="label">Year of Study <span class="text-red-400">*</span></label>
                <select v-model="form.year_of_study" class="input-field">
                  <option value="">Select year</option>
                  <option v-for="y in [1,2,3,4,5,6]" :key="y" :value="y">Year {{ y }}</option>
                </select>
                <p v-if="errors.year_of_study" class="text-red-400 text-xs mt-1">{{ errors.year_of_study }}</p>
              </div>
            </div>
          </div>

          <!-- Links -->
          <div class="card">
            <h2 class="text-xs font-semibold text-neutral-500 uppercase tracking-wide mb-4">Online Profiles</h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="label">LinkedIn URL</label>
                <input v-model="form.linkedin_url" type="url" class="input-field" placeholder="https://linkedin.com/in/..." />
              </div>
              <div>
                <label class="label">GitHub URL</label>
                <input v-model="form.github_url" type="url" class="input-field" placeholder="https://github.com/..." />
              </div>
            </div>
          </div>

          <button type="submit" :disabled="submitting" class="btn-primary w-full flex items-center justify-center gap-2 py-3">
            <LoadingSpinner v-if="submitting" />
            <span>{{ submitting ? 'Submitting...' : 'Continue to Resume Upload →' }}</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
