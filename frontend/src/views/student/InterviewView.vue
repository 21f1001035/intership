<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useApplicationStore } from '@/stores/application'
import ChatBubble from '@/components/interview/ChatBubble.vue'
import ThemeProgress from '@/components/interview/ThemeProgress.vue'
import TypingIndicator from '@/components/interview/TypingIndicator.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'

const router = useRouter()
const route = useRoute()
const appStore = useApplicationStore()

const messageText = ref('')
const sending = ref(false)
const errorMsg = ref('')
const messagesEnd = ref(null)
let pollInterval = null

const interviewState = computed(() => appStore.interviewState)
const messages = computed(() => interviewState.value?.messages || [])
const sessionId = computed(() => interviewState.value?.session_id)
const isComplete = computed(() => interviewState.value?.status === 'completed' || interviewState.value?.is_complete)
const currentTheme = computed(() => interviewState.value?.current_theme)
const completedThemes = computed(() => {
  const themes = ['motivation', 'project_deep_dive', 'ml_fundamentals', 'coding_depth', 'availability']
  const idx = themes.indexOf(currentTheme.value)
  return idx > 0 ? themes.slice(0, idx) : []
})
const turnCount = computed(() => interviewState.value?.turn_count || 0)

async function init() {
  try {
    const state = await appStore.fetchInterviewState()
    if (!state || state.status === 'not_started') {
      await appStore.startInterview()
    }
    scrollToBottom()
  } catch (e) {
    errorMsg.value = 'Failed to load interview.'
  }
}

async function send() {
  if (!messageText.value.trim() || sending.value || isComplete.value) return
  const text = messageText.value.trim()
  messageText.value = ''
  sending.value = true
  errorMsg.value = ''
  try {
    await appStore.sendMessage(sessionId.value, text)
    await nextTick()
    scrollToBottom()
  } catch (e) {
    errorMsg.value = appStore.error || 'Failed to send message.'
  } finally {
    sending.value = false
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function scrollToBottom() {
  nextTick(() => {
    messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

watch(messages, () => scrollToBottom(), { deep: true })

onMounted(async () => {
  await init()
  pollInterval = setInterval(async () => {
    if (!isComplete.value && !sending.value) {
      await appStore.fetchInterviewState()
    }
  }, 5000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div class="h-screen bg-dark-900 flex flex-col">
    <!-- Header -->
    <div class="bg-dark-800 border-b border-dark-500 px-4 py-3 flex-shrink-0">
      <div class="max-w-3xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-7 h-7 rounded-md bg-brand-red flex items-center justify-center text-white font-bold text-xs">IIT</div>
          <div>
            <span class="text-neutral-200 font-medium text-sm">AI/ML Interview</span>
            <span class="text-neutral-500 text-xs ml-2">Turn {{ turnCount }}/12</span>
          </div>
        </div>
        <div v-if="isComplete" class="flex items-center gap-2 px-3 py-1 bg-green-900/40 border border-green-800 rounded-full text-green-400 text-xs font-medium">
          <span>✓</span> Interview Complete
        </div>
      </div>
    </div>

    <!-- Theme progress -->
    <div class="bg-dark-800 border-b border-dark-500 px-4 py-2.5 flex-shrink-0">
      <div class="max-w-3xl mx-auto">
        <ThemeProgress :currentTheme="currentTheme" :completedThemes="completedThemes" />
      </div>
    </div>

    <!-- Messages -->
    <div class="flex-1 overflow-y-auto px-4 py-6">
      <div class="max-w-3xl mx-auto">
        <ErrorAlert :message="errorMsg" @dismiss="errorMsg = ''" class="mb-4" />

        <div v-if="messages.length === 0" class="flex items-center justify-center h-48">
          <div class="text-center">
            <div class="w-10 h-10 rounded-xl bg-dark-700 border border-dark-500 flex items-center justify-center mx-auto mb-3">
              <svg class="w-5 h-5 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
              </svg>
            </div>
            <p class="text-neutral-500 text-sm">Starting your interview...</p>
          </div>
        </div>

        <ChatBubble v-for="msg in messages" :key="msg.id" :message="msg" />
        <TypingIndicator v-if="sending" />

        <!-- Complete state -->
        <div v-if="isComplete" class="mt-6 p-5 bg-green-900/20 border border-green-800 rounded-xl text-center">
          <div class="text-green-400 text-base font-semibold mb-1">Interview Complete</div>
          <p class="text-neutral-400 text-sm mb-4">Thank you for completing the AI/ML internship interview. Your responses are being evaluated.</p>
          <button @click="router.push(`/application/${route.params.id}/status`)" class="btn-primary">
            View Application Status →
          </button>
        </div>

        <div ref="messagesEnd"></div>
      </div>
    </div>

    <!-- Input area (ChatGPT style) -->
    <div v-if="!isComplete" class="flex-shrink-0 border-t border-dark-500 bg-dark-900 px-4 py-4">
      <div class="max-w-3xl mx-auto">
        <div class="flex items-end gap-3 bg-dark-700 border border-dark-500 rounded-xl px-4 py-3 focus-within:border-indigo-500 transition-colors duration-150">
          <textarea
            v-model="messageText"
            @keydown="onKeydown"
            :disabled="sending || isComplete"
            placeholder="Type your response..."
            rows="1"
            class="flex-1 bg-transparent text-neutral-100 placeholder-neutral-500 text-sm resize-none focus:outline-none leading-relaxed max-h-40 overflow-y-auto"
            style="min-height: 24px"
          ></textarea>
          <button
            @click="send"
            :disabled="!messageText.trim() || sending || isComplete"
            class="w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-dark-500 disabled:cursor-not-allowed transition-colors duration-150"
          >
            <svg v-if="!sending" class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
            </svg>
            <div v-else class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          </button>
        </div>
        <p class="text-xs text-neutral-600 mt-2 text-center">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  </div>
</template>
