<script setup>
const props = defineProps({ message: String })
const emit = defineEmits(['dismiss'])
</script>

<template>
  <div v-if="message" class="flex items-start gap-3 bg-red-900/30 border border-red-800 text-red-300 px-4 py-3 rounded-lg text-sm">
    <svg class="w-4 h-4 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
    </svg>
    <span class="flex-1">{{ message }}</span>
    <button @click="emit('dismiss')" class="text-red-400 hover:text-red-200 ml-2">✕</button>
  </div>
</template>
