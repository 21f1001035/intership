<script setup>
const props = defineProps({
  currentTheme: String,
  completedThemes: Array,
})

const themes = [
  { key: 'motivation', label: 'Motivation', short: '01' },
  { key: 'project_deep_dive', label: 'Project', short: '02' },
  { key: 'ml_fundamentals', label: 'ML Basics', short: '03' },
  { key: 'coding_depth', label: 'Coding', short: '04' },
  { key: 'availability', label: 'Availability', short: '05' },
]
</script>

<template>
  <div class="flex items-center gap-1 flex-wrap">
    <template v-for="(theme, i) in themes" :key="theme.key">
      <div :class="[
        'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200',
        completedThemes?.includes(theme.key) ? 'bg-green-900/40 text-green-400 border border-green-800' :
        currentTheme === theme.key ? 'bg-indigo-600 text-white' :
        'bg-dark-600 text-neutral-500 border border-dark-500'
      ]">
        <span v-if="completedThemes?.includes(theme.key)">✓</span>
        <span>{{ theme.label }}</span>
      </div>
      <div v-if="i < themes.length - 1" class="w-3 h-px bg-dark-500 hidden sm:block"></div>
    </template>
  </div>
</template>
