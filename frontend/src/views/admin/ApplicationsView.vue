<script setup>
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AdminNav from '@/components/admin/AdminNav.vue'
import CandidateTable from '@/components/admin/CandidateTable.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import { adminApi } from '@/api/admin'

const router = useRouter()
const route = useRoute()

const applications = ref([])
const loading = ref(false)
const fetchError = ref('')
const totalCount = ref(null)
const currentPage = ref(1)
const pageSize = 20

const filters = reactive({
  status: route.query.status || '',
  search: '',
})

const searchInput = ref('')
const totalPages = computed(() => totalCount.value ? Math.ceil(totalCount.value / pageSize) : 1)

const visiblePages = computed(() => {
  const pages = []
  const start = Math.max(1, currentPage.value - 2)
  const end = Math.min(totalPages.value, currentPage.value + 2)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

const statusOptions = [
  { label: 'All', value: '' },
  { label: 'Received', value: 'received' },
  { label: 'In Progress', value: 'interview_in_progress' },
  { label: 'Completed', value: 'completed' },
  { label: 'Shortlisted', value: 'shortlisted' },
  { label: 'On Hold', value: 'hold' },
  { label: 'Rejected', value: 'rejected' },
  { label: 'Needs Review', value: 'needs_review' },
]

let searchDebounce = null

function setStatus(val) {
  filters.status = val
  currentPage.value = 1
  fetchApplications()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchApplications()
}

async function fetchApplications() {
  loading.value = true
  fetchError.value = ''
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize,
      limit: pageSize,
    }
    if (filters.status) params.status = filters.status
    if (filters.search) params.search = filters.search
    const res = await adminApi.getApplications(params)
    if (Array.isArray(res.data)) {
      applications.value = res.data
      totalCount.value = res.data.length
    } else {
      applications.value = res.data.items || []
      totalCount.value = res.data.total ?? applications.value.length
    }
  } catch (e) {
    fetchError.value = e.response?.data?.detail || 'Failed to load applications.'
  } finally {
    loading.value = false
  }
}

watch(searchInput, (val) => {
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    filters.search = val
    currentPage.value = 1
    fetchApplications()
  }, 400)
})

onMounted(fetchApplications)
</script>

<template>
  <div class="min-h-screen bg-dark-900 flex">
    <AdminNav />

    <div class="flex-1 ml-64">
      <!-- Header -->
      <div class="bg-dark-800 border-b border-dark-500 px-8 py-5">
        <h1 class="text-base font-semibold text-neutral-100">Applications</h1>
        <p class="text-sm text-neutral-500 mt-0.5">
          {{ totalCount !== null ? totalCount + ' total application' + (totalCount !== 1 ? 's' : '') : 'All submitted applications' }}
        </p>
      </div>

      <div class="p-8">
        <!-- Filters -->
        <div class="bg-dark-700 border border-dark-500 rounded-xl p-4 mb-5 flex flex-col sm:flex-row gap-3">
          <!-- Status tabs -->
          <div class="flex gap-1.5 flex-wrap">
            <button
              v-for="opt in statusOptions"
              :key="opt.value"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors duration-150',
                filters.status === opt.value
                  ? 'bg-indigo-600 text-white'
                  : 'bg-dark-600 text-neutral-400 hover:bg-dark-500 hover:text-neutral-200',
              ]"
              @click="setStatus(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>

          <!-- Search -->
          <div class="sm:ml-auto relative min-w-[220px]">
            <svg
              class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              v-model="searchInput"
              type="text"
              placeholder="Search name or email..."
              class="input-field pl-9"
            />
          </div>
        </div>

        <ErrorAlert :message="fetchError" @dismiss="fetchError = ''" class="mb-5" />

        <!-- Table -->
        <CandidateTable
          :candidates="applications"
          :loading="loading"
          @view="(id) => router.push(`/admin/applications/${id}`)"
        />

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="mt-5 flex items-center justify-between">
          <p class="text-sm text-neutral-500">
            Page {{ currentPage }} of {{ totalPages }}
          </p>
          <div class="flex gap-1.5">
            <button
              :disabled="currentPage <= 1"
              class="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium bg-dark-700 border border-dark-500 rounded-lg text-neutral-400 hover:border-dark-400 hover:text-neutral-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              @click="goToPage(currentPage - 1)"
            >
              ← Prev
            </button>
            <button
              v-for="p in visiblePages"
              :key="p"
              :class="[
                'inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors',
                p === currentPage
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-dark-700 border-dark-500 text-neutral-400 hover:border-dark-400 hover:text-neutral-200',
              ]"
              @click="goToPage(p)"
            >
              {{ p }}
            </button>
            <button
              :disabled="currentPage >= totalPages"
              class="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium bg-dark-700 border border-dark-500 rounded-lg text-neutral-400 hover:border-dark-400 hover:text-neutral-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              @click="goToPage(currentPage + 1)"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
