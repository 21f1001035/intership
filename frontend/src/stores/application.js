import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { applicationsApi } from '@/api/applications'
import { interviewApi } from '@/api/interview'

export const useApplicationStore = defineStore('application', () => {
  const applicationId = ref(localStorage.getItem('application_id') || null)
  const applicationToken = ref(localStorage.getItem('application_token') || null)
  const applicationData = ref(null)
  const interviewState = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const hasApplication = computed(() => !!applicationId.value)
  const interviewComplete = computed(() => interviewState.value?.status === 'completed')

  function setApplication(id, token) {
    applicationId.value = id
    applicationToken.value = token
    localStorage.setItem('application_id', id)
    localStorage.setItem('application_token', token)
  }

  async function createApplication(formData) {
    isLoading.value = true
    error.value = null
    try {
      const res = await applicationsApi.create(formData)
      setApplication(res.data.id, res.data.application_token)
      applicationData.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to submit application'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function uploadResume(file) {
    isLoading.value = true
    error.value = null
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await applicationsApi.uploadResume(applicationId.value, formData)
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to upload resume'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchStatus() {
    if (!applicationId.value) return
    try {
      const res = await applicationsApi.getStatus(applicationId.value)
      applicationData.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to fetch status'
    }
  }

  async function startInterview() {
    isLoading.value = true
    error.value = null
    try {
      const res = await interviewApi.start(applicationId.value)
      await fetchInterviewState()
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to start interview'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function fetchInterviewState() {
    try {
      const res = await interviewApi.getState(applicationId.value)
      interviewState.value = res.data
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to fetch interview'
    }
  }

  async function sendMessage(sessionId, messageText) {
    try {
      const res = await interviewApi.sendMessage(sessionId, messageText)
      await fetchInterviewState()
      return res.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'Failed to send message'
      throw e
    }
  }

  return {
    applicationId,
    applicationToken,
    applicationData,
    interviewState,
    isLoading,
    error,
    hasApplication,
    interviewComplete,
    createApplication,
    uploadResume,
    fetchStatus,
    startInterview,
    fetchInterviewState,
    sendMessage,
  }
})
