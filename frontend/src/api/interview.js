import api from './index'

export const interviewApi = {
  start: (applicationId) => api.post(`/interview/${applicationId}/start`),
  getState: (applicationId) => api.get(`/interview/${applicationId}`),
  sendMessage: (sessionId, messageText) =>
    api.post(`/interview/${sessionId}/message`, { message_text: messageText }),
}
