<script setup>
import { computed } from 'vue'

const props = defineProps({ status: String })

const config = {
  received: { label: 'Received', class: 'bg-neutral-700 text-neutral-300 border-neutral-600' },
  interview_in_progress: { label: 'In Progress', class: 'bg-amber-900/40 text-amber-400 border-amber-800' },
  completed: { label: 'Completed', class: 'bg-blue-900/40 text-blue-400 border-blue-800' },
  shortlisted: { label: 'Shortlisted', class: 'bg-green-900/40 text-green-400 border-green-800' },
  hold: { label: 'On Hold', class: 'bg-orange-900/40 text-orange-400 border-orange-800' },
  rejected: { label: 'Rejected', class: 'bg-red-900/40 text-red-400 border-red-800' },
  needs_review: { label: 'Needs Review', class: 'bg-purple-900/40 text-purple-400 border-purple-800' },
}

const badge = computed(() => config[props.status] || { label: props.status, class: 'bg-neutral-700 text-neutral-300 border-neutral-600' })
</script>

<template>
  <span :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border', badge.class]">
    {{ badge.label }}
  </span>
</template>
