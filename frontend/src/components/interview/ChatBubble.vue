<script setup>
import { computed } from 'vue'

const props = defineProps({
  message: Object,  // { sender_type, message_text, theme, turn_number, created_at }
})

const isBot = computed(() => props.message.sender_type === 'bot')

const formattedTime = computed(() => {
  if (!props.message.created_at) return ''
  return new Date(props.message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
})

const themeLabel = {
  motivation: 'Motivation',
  project_deep_dive: 'Project Deep Dive',
  ml_fundamentals: 'ML Fundamentals',
  coding_depth: 'Coding Depth',
  availability: 'Availability',
}
</script>

<template>
  <div :class="['flex gap-3 mb-6', isBot ? 'flex-row' : 'flex-row-reverse']">
    <!-- Avatar -->
    <div :class="['w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold', isBot ? 'bg-indigo-600 text-white' : 'bg-dark-500 text-neutral-300']">
      {{ isBot ? 'AI' : 'You' }}
    </div>
    <!-- Bubble -->
    <div :class="['max-w-[75%]', isBot ? 'items-start' : 'items-end', 'flex flex-col gap-1']">
      <!-- Theme tag (bot only) -->
      <span v-if="isBot && message.theme && message.theme !== 'complete'" class="text-xs text-indigo-400 font-medium">
        {{ themeLabel[message.theme] || message.theme }}
      </span>
      <div :class="['px-4 py-3 rounded-2xl text-sm leading-relaxed', isBot ? 'bg-dark-700 text-neutral-100 rounded-tl-sm' : 'bg-indigo-600 text-white rounded-tr-sm']">
        {{ message.message_text }}
      </div>
      <span class="text-xs text-neutral-600">{{ formattedTime }}</span>
    </div>
  </div>
</template>
