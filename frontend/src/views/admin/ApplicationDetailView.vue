<script setup>
import { ref, onMounted, watch, h } from 'vue'
import { useRoute } from 'vue-router'
import AdminNav from '@/components/admin/AdminNav.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ErrorAlert from '@/components/common/ErrorAlert.vue'
import ScoreCard from '@/components/admin/ScoreCard.vue'
import TranscriptViewer from '@/components/admin/TranscriptViewer.vue'
import { adminApi } from '@/api/admin'

const route = useRoute()
const appId = route.params.id

const loading = ref(true)
const fetchError = ref('')
const application = ref(null)
const activeTab = ref('overview')

const newStatus = ref('')
const statusReason = ref('')
const statusUpdating = ref(false)
const statusMsg = ref(null)

const newNote = ref('')
const noteAdding = ref(false)
const noteMsg = ref(null)

const showRawText = ref(false)

const transcript = ref([])
const transcriptLoading = ref(false)
const transcriptError = ref('')

const scoresData = ref(null)
const scoresLoading = ref(false)
const scoresError = ref('')

const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'resume', label: 'Resume' },
  { key: 'transcript', label: 'Transcript' },
  { key: 'scores', label: 'Scores' },
]

// Inline helper component
const DetailField = {
  props: ['label', 'value'],
  setup(props) {
    return () => h('div', [
      h('p', { class: 'text-xs text-neutral-500 font-medium uppercase tracking-wide mb-1' }, props.label),
      h('p', { class: 'text-sm text-neutral-200 font-medium' }, props.value || '—'),
    ])
  },
}

// Resume section component
const ResumeSection = {
  props: ['title', 'iconPath'],
  setup(props, { slots }) {
    return () => h('div', { class: 'bg-dark-700 border border-dark-500 rounded-xl overflow-hidden' }, [
      h('div', { class: 'px-5 py-4 border-b border-dark-500 flex items-center gap-2' }, [
        h('svg', { class: 'w-4 h-4 text-indigo-400', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor' }, [
          h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: props.iconPath }),
        ]),
        h('h3', { class: 'text-xs font-semibold text-neutral-400 uppercase tracking-widest' }, props.title),
      ]),
      h('div', { class: 'p-5 space-y-3' }, slots.default?.()),
    ])
  },
}

async function fetchApplication() {
  loading.value = true
  fetchError.value = ''
  try {
    const res = await adminApi.getApplication(appId)
    application.value = res.data
  } catch (e) {
    fetchError.value = e.response?.data?.detail || 'Failed to load application.'
  } finally {
    loading.value = false
  }
}

async function fetchTranscript() {
  transcriptLoading.value = true
  transcriptError.value = ''
  try {
    const res = await adminApi.getTranscript(appId)
    transcript.value = res.data?.messages || res.data || []
  } catch (e) {
    transcriptError.value = e.response?.data?.detail || 'Failed to load transcript.'
  } finally {
    transcriptLoading.value = false
  }
}

async function fetchScores() {
  scoresLoading.value = true
  scoresError.value = ''
  try {
    const res = await adminApi.getScores(appId)
    scoresData.value = res.data
  } catch (e) {
    scoresError.value = e.response?.data?.detail || 'No scores available yet.'
  } finally {
    scoresLoading.value = false
  }
}

async function handleStatusUpdate() {
  if (!newStatus.value) return
  statusUpdating.value = true
  statusMsg.value = null
  try {
    await adminApi.updateStatus(appId, newStatus.value, statusReason.value || undefined)
    application.value.status = newStatus.value
    statusMsg.value = { type: 'success', text: 'Status updated successfully.' }
    newStatus.value = ''
    statusReason.value = ''
    await fetchApplication()
  } catch (e) {
    statusMsg.value = { type: 'error', text: e.response?.data?.detail || 'Failed to update status.' }
  } finally {
    statusUpdating.value = false
  }
}

async function handleAddNote() {
  const text = newNote.value.trim()
  if (!text) return
  noteAdding.value = true
  noteMsg.value = null
  try {
    await adminApi.addNote(appId, text)
    newNote.value = ''
    noteMsg.value = { type: 'success', text: 'Note added.' }
    await fetchApplication()
  } catch (e) {
    noteMsg.value = { type: 'error', text: e.response?.data?.detail || 'Failed to add note.' }
  } finally {
    noteAdding.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

watch(activeTab, (tab) => {
  if (tab === 'transcript' && transcript.value.length === 0 && !transcriptLoading.value) {
    fetchTranscript()
  }
  if (tab === 'scores' && !scoresData.value && !scoresLoading.value) {
    fetchScores()
  }
})

onMounted(fetchApplication)
</script>

<template>
  <div class="min-h-screen bg-dark-900 flex">
    <AdminNav />

    <div class="flex-1 ml-64">
      <!-- Top header -->
      <div class="bg-dark-800 border-b border-dark-500 px-8 py-5">
        <div class="flex items-center gap-2 mb-2 text-sm">
          <router-link
            to="/admin/applications"
            class="text-neutral-500 hover:text-indigo-400 transition-colors"
          >
            Applications
          </router-link>
          <span class="text-neutral-600">/</span>
          <span class="text-neutral-400">{{ application?.full_name || appId }}</span>
        </div>
        <div v-if="application" class="flex items-center gap-3">
          <h1 class="text-base font-semibold text-neutral-100">{{ application.full_name }}</h1>
          <StatusBadge :status="application.status" />
        </div>
        <div v-else-if="loading" class="h-6 w-48 bg-dark-600 rounded animate-pulse" />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <LoadingSpinner />
      </div>

      <!-- Error -->
      <div v-else-if="fetchError" class="p-8">
        <ErrorAlert :message="fetchError" @dismiss="fetchError = ''" />
      </div>

      <!-- Content -->
      <div v-else-if="application" class="p-8">
        <!-- Tabs -->
        <div class="flex border-b border-dark-500 mb-6">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="[
              'px-5 py-3 text-sm font-medium border-b-2 transition-colors duration-150 -mb-px',
              activeTab === tab.key
                ? 'border-indigo-500 text-neutral-100'
                : 'border-transparent text-neutral-500 hover:text-neutral-300',
            ]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- OVERVIEW TAB -->
        <div v-if="activeTab === 'overview'" class="space-y-5">
          <!-- Candidate profile -->
          <div class="bg-dark-700 border border-dark-500 rounded-xl overflow-hidden">
            <div class="px-5 py-4 border-b border-dark-500">
              <h3 class="text-xs font-semibold text-neutral-500 uppercase tracking-widest">Candidate Profile</h3>
            </div>
            <div class="p-5 grid grid-cols-2 md:grid-cols-3 gap-5">
              <component :is="DetailField" label="Full Name" :value="application.full_name" />
              <component :is="DetailField" label="Email" :value="application.email" />
              <component :is="DetailField" label="Phone" :value="application.phone || '—'" />
              <component :is="DetailField" label="College / University" :value="application.college" class="col-span-2" />
              <component :is="DetailField" label="Degree" :value="application.degree" />
              <component :is="DetailField" label="Branch / Department" :value="application.branch" class="md:col-span-2" />
              <component :is="DetailField" label="Year of Study" :value="application.year_of_study ? 'Year ' + application.year_of_study : '—'" />
              <component :is="DetailField" label="CGPA" :value="application.cgpa != null ? application.cgpa.toFixed(2) : '—'" />
              <component :is="DetailField" label="Applied On" :value="formatDate(application.created_at)" />
              <div v-if="application.linkedin_url">
                <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide mb-1">LinkedIn</p>
                <a :href="application.linkedin_url" target="_blank" class="text-sm text-indigo-400 hover:text-indigo-300 truncate block">
                  {{ application.linkedin_url }}
                </a>
              </div>
              <div v-if="application.github_url">
                <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide mb-1">GitHub</p>
                <a :href="application.github_url" target="_blank" class="text-sm text-indigo-400 hover:text-indigo-300 truncate block">
                  {{ application.github_url }}
                </a>
              </div>
            </div>
            <div v-if="application.statement_of_interest" class="px-5 pb-5">
              <p class="text-xs text-neutral-500 font-medium uppercase tracking-wide mb-2">Statement of Interest</p>
              <p class="text-sm text-neutral-300 leading-relaxed bg-dark-600 rounded-lg p-4 border border-dark-400">
                {{ application.statement_of_interest }}
              </p>
            </div>
          </div>

          <!-- Status update -->
          <div class="bg-dark-700 border border-dark-500 rounded-xl p-5">
            <h3 class="text-xs font-semibold text-neutral-500 uppercase tracking-widest mb-4">Update Status</h3>
            <div class="flex flex-col sm:flex-row gap-3">
              <select v-model="newStatus" class="input-field flex-1">
                <option value="">Select new status</option>
                <option value="received">Received</option>
                <option value="interview_in_progress">Interview In Progress</option>
                <option value="completed">Completed</option>
                <option value="shortlisted">Shortlisted</option>
                <option value="hold">On Hold</option>
                <option value="rejected">Rejected</option>
                <option value="needs_review">Needs Review</option>
              </select>
              <input
                v-model="statusReason"
                type="text"
                placeholder="Reason (optional)"
                class="input-field flex-1"
              />
              <button
                :disabled="!newStatus || statusUpdating"
                class="btn-primary flex-shrink-0 flex items-center gap-2"
                @click="handleStatusUpdate"
              >
                <LoadingSpinner v-if="statusUpdating" />
                Update
              </button>
            </div>
            <p v-if="statusMsg" :class="['text-sm mt-2', statusMsg.type === 'error' ? 'text-red-400' : 'text-green-400']">
              {{ statusMsg.text }}
            </p>

            <!-- Status history -->
            <div v-if="application.status_history?.length" class="mt-4">
              <p class="text-xs text-neutral-500 font-semibold uppercase tracking-wide mb-2">Status History</p>
              <div class="space-y-2">
                <div
                  v-for="(entry, i) in application.status_history"
                  :key="i"
                  class="flex items-start gap-3 text-sm"
                >
                  <StatusBadge :status="entry.status" />
                  <span class="text-neutral-500 text-xs mt-0.5">{{ formatDate(entry.changed_at || entry.timestamp) }}</span>
                  <span v-if="entry.reason" class="text-neutral-400 text-xs mt-0.5 italic">— {{ entry.reason }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Notes -->
          <div class="bg-dark-700 border border-dark-500 rounded-xl p-5">
            <h3 class="text-xs font-semibold text-neutral-500 uppercase tracking-widest mb-4">Reviewer Notes</h3>
            <div v-if="application.notes?.length" class="space-y-3 mb-4">
              <div
                v-for="(note, i) in application.notes"
                :key="i"
                class="bg-amber-900/20 border border-amber-800/50 rounded-lg px-4 py-3"
              >
                <p class="text-sm text-neutral-200">{{ note.note_text }}</p>
                <p class="text-xs text-neutral-500 mt-1">{{ formatDate(note.created_at) }}</p>
              </div>
            </div>
            <div v-else class="text-sm text-neutral-500 mb-4">No notes yet.</div>
            <div class="flex gap-3">
              <textarea
                v-model="newNote"
                rows="2"
                placeholder="Add a note..."
                class="input-field flex-1 resize-none"
              />
              <button
                :disabled="!newNote.trim() || noteAdding"
                class="btn-primary flex-shrink-0 self-end flex items-center gap-2"
                @click="handleAddNote"
              >
                <LoadingSpinner v-if="noteAdding" />
                Add
              </button>
            </div>
            <p v-if="noteMsg" :class="['text-sm mt-2', noteMsg.type === 'error' ? 'text-red-400' : 'text-green-400']">
              {{ noteMsg.text }}
            </p>
          </div>
        </div>

        <!-- RESUME TAB -->
        <div v-if="activeTab === 'resume'" class="space-y-5">
          <div v-if="!application.resume_data" class="text-center py-12 text-neutral-500">
            <svg class="mx-auto w-10 h-10 mb-3 text-neutral-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-sm">No resume data available yet.</p>
          </div>
          <template v-else>
            <component
              :is="ResumeSection"
              v-if="application.resume_data.education?.length"
              title="Education"
              icon-path="M12 14l9-5-9-5-9 5 9 5z"
            >
              <div v-for="(ed, i) in application.resume_data.education" :key="i" class="bg-dark-600 rounded-lg p-4 border border-dark-400">
                <p class="font-semibold text-neutral-200 text-sm">{{ ed.degree }} — {{ ed.institution }}</p>
                <p class="text-xs text-neutral-500 mt-0.5">{{ [ed.year, ed.cgpa ? 'CGPA: ' + ed.cgpa : null].filter(Boolean).join(' · ') }}</p>
              </div>
            </component>

            <component
              :is="ResumeSection"
              v-if="application.resume_data.skills?.length"
              title="Skills"
              icon-path="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            >
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="skill in application.resume_data.skills"
                  :key="skill"
                  class="px-3 py-1 bg-indigo-900/40 border border-indigo-800 text-indigo-300 text-xs font-medium rounded-full"
                >
                  {{ skill }}
                </span>
              </div>
            </component>

            <component
              :is="ResumeSection"
              v-if="application.resume_data.projects?.length"
              title="Projects"
              icon-path="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
            >
              <div v-for="(proj, i) in application.resume_data.projects" :key="i" class="bg-dark-600 rounded-lg p-4 border border-dark-400">
                <p class="font-semibold text-neutral-200 text-sm">{{ proj.name || proj.title }}</p>
                <p v-if="proj.technologies" class="text-xs text-indigo-400 mt-0.5 font-medium">{{ Array.isArray(proj.technologies) ? proj.technologies.join(', ') : proj.technologies }}</p>
                <p v-if="proj.description" class="text-xs text-neutral-400 mt-1 leading-relaxed">{{ proj.description }}</p>
              </div>
            </component>

            <component
              :is="ResumeSection"
              v-if="application.resume_data.experience?.length"
              title="Experience"
              icon-path="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            >
              <div v-for="(exp, i) in application.resume_data.experience" :key="i" class="bg-dark-600 rounded-lg p-4 border border-dark-400">
                <p class="font-semibold text-neutral-200 text-sm">{{ exp.role || exp.title }} — {{ exp.company || exp.organization }}</p>
                <p class="text-xs text-neutral-500 mt-0.5">{{ exp.duration || exp.period }}</p>
                <p v-if="exp.description" class="text-xs text-neutral-400 mt-1 leading-relaxed">{{ exp.description }}</p>
              </div>
            </component>

            <!-- Raw text -->
            <div v-if="application.resume_data.raw_text" class="bg-dark-700 border border-dark-500 rounded-xl overflow-hidden">
              <button
                class="w-full px-5 py-4 flex items-center justify-between text-sm font-medium text-neutral-400 hover:text-neutral-200 hover:bg-dark-600 transition-colors"
                @click="showRawText = !showRawText"
              >
                Raw Resume Text
                <svg :class="['w-4 h-4 transition-transform', showRawText ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div v-if="showRawText" class="border-t border-dark-500 p-5">
                <pre class="text-xs text-neutral-400 whitespace-pre-wrap font-mono leading-relaxed bg-dark-800 p-4 rounded-lg border border-dark-500 overflow-x-auto">{{ application.resume_data.raw_text }}</pre>
              </div>
            </div>
          </template>
        </div>

        <!-- TRANSCRIPT TAB -->
        <div v-if="activeTab === 'transcript'">
          <div v-if="transcriptLoading" class="flex items-center justify-center py-16">
            <LoadingSpinner />
          </div>
          <div v-else-if="transcriptError" class="py-8">
            <ErrorAlert :message="transcriptError" @dismiss="transcriptError = ''" />
          </div>
          <div v-else-if="!transcript || transcript.length === 0" class="text-center py-12 text-neutral-500 text-sm">
            No interview transcript available yet.
          </div>
          <div v-else class="bg-dark-700 border border-dark-500 rounded-xl p-6">
            <TranscriptViewer :messages="transcript" />
          </div>
        </div>

        <!-- SCORES TAB -->
        <div v-if="activeTab === 'scores'">
          <div v-if="scoresLoading" class="flex items-center justify-center py-16">
            <LoadingSpinner />
          </div>
          <div v-else-if="scoresError" class="py-8">
            <ErrorAlert :message="scoresError" @dismiss="scoresError = ''" />
          </div>
          <div v-else-if="!scoresData" class="text-center py-12 text-neutral-500 text-sm">
            No scores available. The interview may not be complete yet.
          </div>
          <div v-else>
            <ScoreCard
              :scores="scoresData.scores || scoresData"
              :recommendation="scoresData.recommendation || scoresData"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
