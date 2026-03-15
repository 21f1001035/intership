<script setup>
import { computed } from 'vue'
import ChatBubble from '@/components/interview/ChatBubble.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
})

const groupedMessages = computed(() => {
  if (!props.messages || props.messages.length === 0) return []

  const groups = []
  let currentTheme = null
  let currentGroup = null

  for (const msg of props.messages) {
    const theme = msg.theme || 'general'
    if (theme !== currentTheme) {
      currentTheme = theme
      currentGroup = { theme, messages: [] }
      groups.push(currentGroup)
    }
    currentGroup.messages.push(msg)
  }

  return groups
})

function formatTheme(theme) {
  return theme.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
</script>

<template>
  <div class="space-y-2">
    <div v-if="!messages || messages.length === 0" class="text-center py-12 text-neutral-500 text-sm">
      No transcript available.
    </div>

    <template v-else>
      <template v-for="(group, idx) in groupedMessages" :key="idx">
        <!-- Theme section header -->
        <div class="flex items-center gap-3 my-5">
          <div class="h-px flex-1 bg-dark-500" />
          <span class="text-xs font-semibold text-neutral-500 uppercase tracking-widest px-3 py-1 rounded-full bg-dark-600 border border-dark-400">
            {{ formatTheme(group.theme) }}
          </span>
          <div class="h-px flex-1 bg-dark-500" />
        </div>

        <ChatBubble
          v-for="msg in group.messages"
          :key="msg.id || msg.created_at"
          :message="msg"
        />
      </template>
    </template>
  </div>
</template>
