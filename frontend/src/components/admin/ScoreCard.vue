<script setup>
import { computed } from 'vue'

const props = defineProps({
  scores: {
    type: Object,
    default: null,
  },
  recommendation: {
    type: Object,
    default: null,
  },
})

const dimensionConfig = [
  { key: 'motivation_score', label: 'Motivation' },
  { key: 'technical_depth_score', label: 'Technical Depth' },
  { key: 'ml_knowledge_score', label: 'ML Knowledge' },
  { key: 'communication_score', label: 'Communication' },
  { key: 'problem_solving_score', label: 'Problem Solving' },
  { key: 'project_quality_score', label: 'Project Quality' },
]

const dimensions = computed(() => {
  if (!props.scores) return []
  return dimensionConfig
    .map((d) => ({
      ...d,
      value: props.scores[d.key] ?? null,
      note: props.scores[d.key + '_note'] || null,
    }))
    .filter((d) => d.value !== null)
})

const overallScore = computed(() => {
  return props.scores?.overall_score ?? props.recommendation?.overall_score ?? null
})

const recommendationClass = computed(() => {
  const label = props.recommendation?.label?.toLowerCase() || ''
  if (label.includes('strong') || label.includes('recommend')) return 'bg-green-900/40 text-green-400 border border-green-800'
  if (label.includes('consider') || label.includes('maybe')) return 'bg-amber-900/40 text-amber-400 border border-amber-800'
  if (label.includes('not') || label.includes('reject')) return 'bg-red-900/40 text-red-400 border border-red-800'
  return 'bg-neutral-700 text-neutral-300 border border-neutral-600'
})

function scoreBarColor(value) {
  if (value === null) return 'bg-dark-400'
  if (value >= 8) return 'bg-green-500'
  if (value >= 6) return 'bg-indigo-500'
  if (value >= 4) return 'bg-amber-500'
  return 'bg-red-500'
}
</script>

<template>
  <div class="space-y-5">
    <!-- Overall Score -->
    <div class="bg-dark-700 border border-dark-500 rounded-xl p-6 text-center">
      <p class="text-xs font-semibold text-neutral-500 uppercase tracking-widest mb-3">Overall Score</p>
      <div class="text-6xl font-bold text-neutral-100 mb-1">
        {{ overallScore !== null ? overallScore : '—' }}
      </div>
      <div class="text-neutral-500 text-sm mb-4">out of 10</div>

      <div v-if="recommendation">
        <span :class="['inline-flex items-center px-4 py-1.5 rounded-full text-sm font-semibold', recommendationClass]">
          {{ recommendation.label }}
        </span>
        <div v-if="recommendation.confidence" class="text-xs text-neutral-500 mt-2">
          Confidence: {{ Math.round(recommendation.confidence * 100) }}%
        </div>
      </div>
    </div>

    <!-- Authenticity Warning -->
    <div
      v-if="scores?.authenticity_flag"
      class="flex items-start gap-3 bg-red-900/30 border border-red-800 rounded-xl p-4"
    >
      <svg class="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd"
          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
          clip-rule="evenodd" />
      </svg>
      <div>
        <p class="font-semibold text-red-300 text-sm">Authenticity Concern Flagged</p>
        <p class="text-red-400 text-sm mt-1">
          The AI detected potential issues with response authenticity. Manual review recommended.
        </p>
      </div>
    </div>

    <!-- Dimension Scores -->
    <div v-if="dimensions.length > 0" class="bg-dark-700 border border-dark-500 rounded-xl overflow-hidden">
      <div class="px-5 py-4 border-b border-dark-500">
        <h3 class="text-xs font-semibold text-neutral-500 uppercase tracking-wider">Dimension Scores</h3>
      </div>
      <div class="p-5 space-y-4">
        <div v-for="dim in dimensions" :key="dim.key">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-sm font-medium text-neutral-300">{{ dim.label }}</span>
            <span class="text-sm font-bold text-neutral-100">
              {{ dim.value !== null ? dim.value : '—' }}<span class="text-neutral-500 font-normal">/10</span>
            </span>
          </div>
          <div class="w-full bg-dark-500 rounded-full h-1.5">
            <div
              :class="['h-1.5 rounded-full transition-all duration-500', scoreBarColor(dim.value)]"
              :style="{ width: dim.value !== null ? (dim.value / 10 * 100) + '%' : '0%' }"
            />
          </div>
          <p v-if="dim.note" class="text-xs text-neutral-500 mt-1">{{ dim.note }}</p>
        </div>
      </div>
    </div>

    <!-- Narrative Summary -->
    <div v-if="recommendation?.narrative" class="bg-dark-700 border border-dark-500 rounded-xl p-5">
      <h3 class="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-3">AI Summary</h3>
      <p class="text-sm text-neutral-300 leading-relaxed">{{ recommendation.narrative }}</p>
    </div>
  </div>
</template>
