<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApplicationStore } from '@/stores/application'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const store = useApplicationStore()
const appId = route.params.id

const loading = ref(true)
const fetchError = ref('')
const application = computed(() => store.applicationData)

let pollTimer = null

const statusConfigs = {
  received: {
    icon: '📋',
    title: 'Application Received',
    message: 'Your application has been received. Please complete the resume upload and interview to proceed.',
    containerClass: 'bg-neutral-700/30 border-neutral-600',
    titleClass: 'text-neutral-100',
    textClass: 'text-neutral-400',
    iconBg: 'bg-neutral-700',
  },
  interview_in_progress: {
    icon: '⏳',
    title: 'Interview In Progress',
    message: 'Your AI interview session is underway. Please continue and complete all questions.',
    containerClass: 'bg-amber-900/20 border-amber-800',
    titleClass: 'text-amber-300',
    textClass: 'text-amber-400/80',
    iconBg: 'bg-amber-900/40',
  },
  completed: {
    icon: '✓',
    title: 'Interview Completed',
    message: 'Your interview has been completed. Results are pending review by our faculty.',
    containerClass: 'bg-blue-900/20 border-blue-800',
    titleClass: 'text-blue-300',
    textClass: 'text-blue-400/80',
    iconBg: 'bg-blue-900/40',
  },
  shortlisted: {
    icon: '★',
    title: 'Shortlisted!',
    message: 'Congratulations! You have been shortlisted for the IIT Ropar AI/ML Internship. Our team will contact you shortly.',
    containerClass: 'bg-green-900/20 border-green-800',
    titleClass: 'text-green-300',
    textClass: 'text-green-400/80',
    iconBg: 'bg-green-900/40',
  },
  hold: {
    icon: '⏸',
    title: 'Under Review',
    message: 'Your application is under additional review. We will update you soon.',
    containerClass: 'bg-orange-900/20 border-orange-800',
    titleClass: 'text-orange-300',
    textClass: 'text-orange-400/80',
    iconBg: 'bg-orange-900/40',
  },
  rejected: {
    icon: '✕',
    title: 'Application Not Selected',
    message: 'Thank you for applying to IIT Ropar\'s internship programme. Unfortunately, you were not selected at this time. We encourage you to apply again.',
    containerClass: 'bg-red-900/20 border-red-800',
    titleClass: 'text-red-300',
    textClass: 'text-red-400/80',
    iconBg: 'bg-red-900/40',
  },
  needs_review: {
    icon: '👁',
    title: 'Additional Review Required',
    message: 'Your application requires additional review from our team. We will be in touch.',
    containerClass: 'bg-purple-900/20 border-purple-800',
    titleClass: 'text-purple-300',
    textClass: 'text-purple-400/80',
    iconBg: 'bg-purple-900/40',
  },
}

const defaultConfig = {
  icon: '?',
  title: 'Status Unknown',
  message: 'Please check back later.',
  containerClass: 'bg-dark-700 border-dark-500',
  titleClass: 'text-neutral-200',
  textClass: 'text-neutral-400',
  iconBg: 'bg-dark-600',
}

const statusConfig = computed(() => {
  const status = application.value?.status
  return statusConfigs[status] || defaultConfig
})

const steps = computed(() => {
  const s = application.value?.status || ''
  const passedStatuses = ['completed', 'shortlisted', 'hold', 'rejected', 'needs_review']
  return [
    {
      label: 'Application Received',
      desc: 'Resume uploaded and profile created',
      done: s !== '',
      active: s === 'received',
    },
    {
      label: 'AI Interview',
      desc: 'Automated screening interview',
      done: passedStatuses.includes(s),
      active: s === 'interview_in_progress',
    },
    {
      label: 'Faculty Review',
      desc: 'Your responses are reviewed by IIT Ropar faculty',
      done: ['shortlisted', 'hold', 'rejected', 'needs_review'].includes(s),
      active: s === 'completed',
    },
    {
      label: 'Final Decision',
      desc: 'Shortlisting and offer letters',
      done: s === 'shortlisted',
      active: false,
    },
  ]
})

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

async function fetchData() {
  fetchError.value = ''
  loading.value = true
  try {
    if (appId && appId !== store.applicationId) {
      localStorage.setItem('application_id', appId)
      store.applicationId = appId
    }
    await store.fetchStatus()
  } catch {
    fetchError.value = 'Failed to fetch application status.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchData()
  pollTimer = setInterval(async () => {
    if (application.value?.status === 'interview_in_progress') {
      await store.fetchStatus()
    } else {
      clearInterval(pollTimer)
    }
  }, 10000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
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

    <div class="flex-1 px-4 py-10">
      <div class="max-w-2xl mx-auto">
        <!-- Loading -->
        <div v-if="loading" class="flex items-center justify-center py-20">
          <LoadingSpinner />
        </div>

        <!-- Error -->
        <div v-else-if="fetchError" class="py-10 space-y-4">
          <ErrorAlert :message="fetchError" @dismiss="fetchError = ''" />
          <button class="btn-secondary" @click="fetchData">Retry</button>
        </div>

        <!-- Content -->
        <template v-else-if="application">
          <div class="mb-6">
            <h1 class="text-xl font-semibold text-neutral-100">Application Status</h1>
            <p class="text-neutral-500 text-sm mt-1">Application ID: <span class="font-mono text-neutral-400">{{ appId }}</span></p>
          </div>

          <!-- Status banner -->
          <div :class="['rounded-xl border p-5 mb-5', statusConfig.containerClass]">
            <div class="flex items-start gap-4">
              <div :class="['w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-lg', statusConfig.iconBg]">
                {{ statusConfig.icon }}
              </div>
              <div class="flex-1">
                <div class="flex items-center gap-3 mb-1">
                  <h2 :class="['font-semibold text-base', statusConfig.titleClass]">{{ statusConfig.title }}</h2>
                  <StatusBadge :status="application.status" />
                </div>
                <p :class="['text-sm', statusConfig.textClass]">{{ statusConfig.message }}</p>
                <router-link
                  v-if="application.status === 'interview_in_progress'"
                  :to="`/application/${appId}/interview`"
                  class="mt-3 inline-flex items-center gap-1 text-sm font-medium text-indigo-400 hover:text-indigo-300"
                >
                  Continue Interview →
                </router-link>
              </div>
            </div>
          </div>

          <!-- Application summary -->
          <div class="card mb-5">
            <h3 class="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-4">Application Summary</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide">Full Name</p>
                <p class="text-sm text-neutral-200 mt-0.5">{{ application.full_name || '—' }}</p>
              </div>
              <div>
                <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide">Email</p>
                <p class="text-sm text-neutral-200 mt-0.5">{{ application.email || '—' }}</p>
              </div>
              <div>
                <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide">College</p>
                <p class="text-sm text-neutral-200 mt-0.5">{{ application.college || '—' }}</p>
              </div>
              <div>
                <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide">Degree & Branch</p>
                <p class="text-sm text-neutral-200 mt-0.5">
                  {{ [application.degree, application.branch].filter(Boolean).join(' · ') || '—' }}
                </p>
              </div>
              <div>
                <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide">Year of Study</p>
                <p class="text-sm text-neutral-200 mt-0.5">{{ application.year_of_study ? 'Year ' + application.year_of_study : '—' }}</p>
              </div>
              <div v-if="application.cgpa != null">
                <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide">CGPA</p>
                <p class="text-sm text-neutral-200 mt-0.5">{{ application.cgpa.toFixed(2) }}</p>
              </div>
              <div v-if="application.created_at" class="col-span-2">
                <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide">Applied On</p>
                <p class="text-sm text-neutral-200 mt-0.5">{{ formatDate(application.created_at) }}</p>
              </div>
            </div>
          </div>

          <!-- What happens next -->
          <div class="card">
            <h3 class="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-4">What Happens Next</h3>
            <ol class="space-y-4">
              <li v-for="(step, i) in steps" :key="i" class="flex items-start gap-3">
                <span :class="[
                  'w-6 h-6 rounded-full text-xs flex items-center justify-center font-bold flex-shrink-0 mt-0.5',
                  step.done ? 'bg-green-900/50 text-green-400 border border-green-700' :
                  step.active ? 'bg-indigo-600 text-white' :
                  'bg-dark-600 text-neutral-500 border border-dark-400'
                ]">{{ step.done ? '✓' : i + 1 }}</span>
                <div>
                  <p :class="['text-sm font-medium', step.done || step.active ? 'text-neutral-200' : 'text-neutral-500']">{{ step.label }}</p>
                  <p class="text-xs text-neutral-600 mt-0.5">{{ step.desc }}</p>
                </div>
              </li>
            </ol>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
