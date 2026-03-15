import api from './index'

export const applicationsApi = {
  create: (data) => api.post('/applications', data),
  uploadResume: (applicationId, formData) =>
    api.post(`/applications/${applicationId}/resume`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getStatus: (applicationId) => api.get(`/applications/${applicationId}`),
  complete: (applicationId) => api.post(`/applications/${applicationId}/complete`),
}
