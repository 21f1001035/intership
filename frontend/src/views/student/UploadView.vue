<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useApplicationStore } from '@/stores/application'
import ErrorAlert from '@/components/common/ErrorAlert.vue'

const router = useRouter()
const route = useRoute()
const appStore = useApplicationStore()

const file = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const serverError = ref('')

function onFileDrop(e) {
  dragging.value = false
  const f = e.dataTransfer.files[0]
  if (f && f.type === 'application/pdf') {
    file.value = f
    serverError.value = ''
  } else {
    serverError.value = 'Only PDF files are accepted.'
  }
}

function onFileSelect(e) {
  const f = e.target.files[0]
  if (f) {
    file.value = f
    serverError.value = ''
  }
}

async function upload() {
  if (!file.value) return
  if (file.value.size > 10 * 1024 * 1024) {
    serverError.value = 'File size must be under 10 MB.'
    return
  }
  uploading.value = true
  serverError.value = ''
  try {
    await appStore.uploadResume(file.value)
    router.push(`/application/${route.params.id}/interview`)
  } catch (e) {
    serverError.value = appStore.error || 'Upload failed. Please try again.'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-dark-900 flex flex-col">
    <div class="bg-dark-800 border-b border-dark-500 px-6 py-4">
      <div class="max-w-2xl mx-auto flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-brand-red flex items-center justify-center text-white font-bold text-xs flex-shrink-0">IIT</div>
        <div>
          <div class="text-neutral-100 font-semibold text-sm">IIT Ropar</div>
          <div class="text-neutral-500 text-xs">AI/ML Internship Screening</div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex items-center justify-center px-4 py-16">
      <div class="max-w-lg w-full">
        <!-- Step indicator -->
        <div class="flex items-center gap-2 mb-8 text-sm">
          <span class="flex items-center justify-center w-6 h-6 rounded-full bg-green-900/50 text-green-400 border border-green-700 text-xs">✓</span>
          <span class="text-neutral-500">Application</span>
          <div class="flex-1 h-px bg-dark-500"></div>
          <span class="flex items-center justify-center w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold">2</span>
          <span class="text-neutral-200 font-medium">Resume</span>
          <div class="flex-1 h-px bg-dark-500"></div>
          <span class="flex items-center justify-center w-6 h-6 rounded-full bg-dark-600 text-neutral-500 text-xs border border-dark-400">3</span>
          <span class="text-neutral-500">Interview</span>
        </div>

        <div class="mb-6">
          <h1 class="text-xl font-semibold text-neutral-100">Upload Your Resume</h1>
          <p class="text-neutral-400 text-sm mt-1">We'll extract your profile to personalise the interview.</p>
        </div>

        <ErrorAlert :message="serverError" @dismiss="serverError = ''" class="mb-4" />

        <!-- Drop zone -->
        <div
          @dragover.prevent="dragging = true"
          @dragleave="dragging = false"
          @drop.prevent="onFileDrop"
          :class="['border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors duration-150', dragging ? 'border-indigo-500 bg-indigo-900/10' : file ? 'border-green-700 bg-green-900/10' : 'border-dark-400 hover:border-dark-300']"
          @click="$refs.fileInput.click()"
        >
          <input ref="fileInput" type="file" accept=".pdf" class="hidden" @change="onFileSelect" />
          <div v-if="!file">
            <div class="w-12 h-12 rounded-xl bg-dark-600 flex items-center justify-center mx-auto mb-4">
              <svg class="w-6 h-6 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
              </svg>
            </div>
            <p class="text-neutral-300 font-medium text-sm">Drop your PDF here or click to browse</p>
            <p class="text-neutral-600 text-xs mt-1">PDF only · Maximum 10 MB</p>
          </div>
          <div v-else class="flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-xl bg-green-900/40 flex items-center justify-center mx-auto">
              <svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <p class="text-neutral-200 font-medium text-sm">{{ file.name }}</p>
            <p class="text-neutral-500 text-xs">{{ (file.size / 1024 / 1024).toFixed(2) }} MB</p>
            <button @click.stop="file = null" class="text-xs text-red-400 hover:text-red-300 mt-1">Remove</button>
          </div>
        </div>

        <button
          :disabled="!file || uploading"
          @click="upload"
          class="btn-primary w-full mt-4 py-3 flex items-center justify-center gap-2"
        >
          <svg v-if="!uploading" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>
          </svg>
          <div v-else class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          {{ uploading ? 'Processing resume...' : 'Upload & Continue' }}
        </button>
      </div>
    </div>
  </div>
</template>
