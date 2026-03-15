<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AdminNav from '@/components/admin/AdminNav.vue'
import CandidateTable from '@/components/admin/CandidateTable.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import { adminApi } from '@/api/admin'

const router = useRouter()
const loading = ref(true)
const fetchError = ref('')
const summary = ref(null)
const recentApplications = ref([])

const summaryCards = computed(() => {
  const s = summary.value || {}
  return [
    {
      label: 'Total',
      value: s.total ?? '—',
      bgClass: 'bg-dark-600',
      valueClass: 'text-neutral-100',
      dotClass: 'bg-neutral-400',
      iconPath: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      link: '/admin/applications',
    },
    {
      label: 'Shortlisted',
      value: s.shortlisted ?? '—',
      bgClass: 'bg-green-900/30',
      valueClass: 'text-green-400',
      dotClass: 'bg-green-500',
      iconPath: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
      link: '/admin/applications?status=shortlisted',
    },
    {
      label: 'In Progress',
      value: s.interview_in_progress ?? '—',
      bgClass: 'bg-amber-900/30',
      valueClass: 'text-amber-400',
      dotClass: 'bg-amber-500',
      iconPath: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
      link: '/admin/applications?status=interview_in_progress',
    },
    {
      label: 'Completed',
      value: s.completed ?? '—',
      bgClass: 'bg-blue-900/30',
      valueClass: 'text-blue-400',
      dotClass: 'bg-blue-500',
      iconPath: 'M5 13l4 4L19 7',
      link: '/admin/applications?status=completed',
    },
    {
      label: 'Needs Review',
      value: s.needs_review ?? '—',
      bgClass: 'bg-red-900/30',
      valueClass: 'text-red-400',
      dotClass: 'bg-red-500',
      iconPath: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      link: '/admin/applications?status=needs_review',
    },
  ]
})

async function fetchDashboard() {
  loading.value = true
  fetchError.value = ''
  try {
    const [summaryRes, appsRes] = await Promise.all([
      adminApi.getDashboardSummary(),
      adminApi.getApplications({ limit: 10, sort: '-created_at' }),
    ])
    summary.value = summaryRes.data
    recentApplications.value = appsRes.data?.items || appsRes.data || []
  } catch (e) {
    fetchError.value = e.response?.data?.detail || 'Failed to load dashboard data.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboard)
</script>

<template>
  <div class="min-h-screen bg-dark-900 flex">
    <AdminNav />

    <!-- Main content -->
    <div class="flex-1 ml-64">
      <!-- Top header -->
      <div class="bg-dark-800 border-b border-dark-500 px-8 py-5">
        <h1 class="text-base font-semibold text-neutral-100">Dashboard</h1>
        <p class="text-sm text-neutral-500 mt-0.5">Overview of the AI/ML Internship Programme</p>
      </div>

      <div class="p-8">
        <ErrorAlert :message="fetchError" @dismiss="fetchError = ''" class="mb-6" />

        <!-- Summary Cards skeleton -->
        <div v-if="loading" class="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div v-for="i in 5" :key="i" class="bg-dark-700 border border-dark-500 rounded-xl p-5 animate-pulse">
            <div class="h-2.5 bg-dark-400 rounded w-2/3 mb-3" />
            <div class="h-8 bg-dark-400 rounded w-1/3" />
          </div>
        </div>

        <!-- Summary Cards -->
        <div v-else class="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div
            v-for="card in summaryCards"
            :key="card.label"
            :class="['border border-dark-500 rounded-xl p-5 cursor-pointer hover:border-dark-400 transition-colors duration-150', card.bgClass]"
            @click="card.link && router.push(card.link)"
          >
            <div class="flex items-center justify-between mb-3">
              <p class="text-xs font-semibold text-neutral-500 uppercase tracking-wider">{{ card.label }}</p>
              <span :class="['w-1.5 h-1.5 rounded-full', card.dotClass]"></span>
            </div>
            <p :class="['text-3xl font-bold', card.valueClass]">{{ card.value }}</p>
          </div>
        </div>

        <!-- Recent Applications -->
        <div>
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-semibold text-neutral-300">Recent Applications</h2>
            <router-link
              to="/admin/applications"
              class="text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              View all →
            </router-link>
          </div>

          <CandidateTable
            :candidates="recentApplications"
            :loading="loading"
            @view="(id) => router.push(`/admin/applications/${id}`)"
          />
        </div>
      </div>
    </div>
  </div>
</template>
