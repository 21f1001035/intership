<script setup>
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

defineProps({
  candidates: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['view'])

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}
</script>

<template>
  <div class="bg-dark-700 border border-dark-500 rounded-xl overflow-hidden">
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <LoadingSpinner />
    </div>

    <!-- Empty state -->
    <div v-else-if="!candidates || candidates.length === 0" class="text-center py-16">
      <svg class="mx-auto h-10 w-10 text-neutral-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p class="text-neutral-500 text-sm">No applications found.</p>
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="min-w-full">
        <thead>
          <tr class="border-b border-dark-500">
            <th class="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Name</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Email</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider hidden md:table-cell">College</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider">Status</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider hidden lg:table-cell">CGPA</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-neutral-500 uppercase tracking-wider hidden lg:table-cell">Applied</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-neutral-500 uppercase tracking-wider">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-dark-500">
          <tr
            v-for="candidate in candidates"
            :key="candidate.id"
            class="hover:bg-dark-600 transition-colors duration-100 cursor-pointer"
            @click="$emit('view', candidate.id)"
          >
            <td class="px-4 py-3">
              <div class="font-medium text-neutral-100 text-sm">{{ candidate.full_name }}</div>
              <div class="text-xs text-neutral-500 mt-0.5">{{ candidate.degree }} · {{ candidate.branch }}</div>
            </td>
            <td class="px-4 py-3 text-sm text-neutral-400">{{ candidate.email }}</td>
            <td class="px-4 py-3 text-sm text-neutral-400 hidden md:table-cell">
              <div class="max-w-[180px] truncate">{{ candidate.college }}</div>
            </td>
            <td class="px-4 py-3">
              <StatusBadge :status="candidate.status" />
            </td>
            <td class="px-4 py-3 text-sm text-neutral-400 hidden lg:table-cell">
              {{ candidate.cgpa != null ? candidate.cgpa.toFixed(2) : '—' }}
            </td>
            <td class="px-4 py-3 text-sm text-neutral-500 hidden lg:table-cell">
              {{ formatDate(candidate.created_at) }}
            </td>
            <td class="px-4 py-3 text-right">
              <button
                class="text-indigo-400 hover:text-indigo-300 text-sm font-medium transition-colors duration-100"
                @click.stop="$emit('view', candidate.id)"
              >
                View →
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
