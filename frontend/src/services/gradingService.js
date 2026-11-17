import api from './api'

export async function listMyAssignments(params = {}) {
  const response = await api.get('/grading/assignments/me/', { params })
  return response.data.results || response.data
}

export async function claimAssignment(id) {
  const response = await api.post(`/grading/assignments/${id}/claim/`)
  return response.data
}

export async function submitAssignment(id, payload) {
  const response = await api.post(`/grading/assignments/${id}/submit/`, payload)
  return response.data
}

export async function saveAssignmentDraft(id, payload) {
  const response = await api.patch(`/grading/assignments/${id}/draft/`, payload)
  return response.data
}

export async function renewAssignmentLease(id) {
  const response = await api.post(`/grading/assignments/${id}/lease/`)
  return response.data
}

export async function listArbitrations() {
  const response = await api.get('/grading/arbitrations/')
  return response.data.results || response.data
}

export async function resolveArbitration(id, payload) {
  const response = await api.post(`/grading/arbitrations/${id}/resolve/`, payload)
  return response.data
}

export async function getGradingMetrics() {
  const response = await api.get('/grading/metrics/')
  return response.data
}

export async function listQualityReviews() {
  const response = await api.get('/grading/quality-reviews/')
  return response.data.results || response.data
}

export async function reviewQuality(id, payload) {
  const response = await api.post(`/grading/quality-reviews/${id}/review/`, payload)
  return response.data
}

export async function listReleaseApprovals() {
  const response = await api.get('/grading/release-approvals/')
  return response.data.results || response.data
}

export async function decideRelease(id, payload) {
  const response = await api.post(`/grading/release-approvals/${id}/decide/`, payload)
  return response.data
}

export async function publishRelease(id) {
  const response = await api.post(`/grading/release-approvals/${id}/publish/`)
  return response.data
}

export async function revokeRelease(id, payload = {}) {
  const response = await api.post(`/grading/release-approvals/${id}/revoke/`, payload)
  return response.data
}

export async function exportExamScores(examId) {
  const response = await api.get(`/grading/exams/${examId}/scores/export/`, { responseType: 'blob' })
  return response
}

export async function listTeacherProfiles() {
  const response = await api.get('/grading/teacher-profiles/')
  return response.data.results || response.data
}

export async function updateTeacherProfile(id, payload) {
  const response = await api.patch(`/grading/teacher-profiles/${id}/`, payload)
  return response.data
}

export async function listAuditLogs(params = {}) {
  const response = await api.get('/grading/audit-logs/', { params })
  return response.data.results || response.data
}

export async function listFailedRecognitionJobs() {
  const response = await api.get('/grading/recognition-jobs/failed/')
  return response.data.results || response.data
}

export async function retryRecognition(batchId) {
  const response = await api.post(`/grading/scan-batches/${batchId}/recognize/retry/`)
  return response.data
}

export async function listScanPageReviewQueue() {
  const response = await api.get('/grading/scan-pages/review-queue/')
  return response.data.results || response.data
}

export async function reviewScanPage(id, payload) {
  const response = await api.post(`/grading/scan-pages/${id}/review/`, payload)
  return response.data
}
