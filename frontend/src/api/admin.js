import api from './index'

export const adminApi = {
  login: (email, password) => api.post('/admin/login', { email, password }),
  getApplications: (params) => api.get('/admin/applications', { params }),
  getApplication: (id) => api.get(`/admin/applications/${id}`),
  getTranscript: (id) => api.get(`/admin/applications/${id}/transcript`),
  getScores: (id) => api.get(`/admin/applications/${id}/scores`),
  updateStatus: (id, status, reason) =>
    api.post(`/admin/applications/${id}/status`, { status, reason }),
  addNote: (id, noteText) =>
    api.post(`/admin/applications/${id}/notes`, { note_text: noteText }),
  getDashboardSummary: () => api.get('/admin/dashboard/summary'),
}
