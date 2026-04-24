/**
 * API client wrapper for backend communication
 */

const API_BASE = '/api'

export const apiClient = {
  async get(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`)
    if (!response.ok) throw new Error(`API error: ${response.status}`)
    return response.json()
  },

  async post(endpoint, data) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error(`API error: ${response.status}`)
    return response.json()
  },

  async patch(endpoint, data) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error(`API error: ${response.status}`)
    return response.json()
  },

  async delete(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error(`API error: ${response.status}`)
    return response.ok
  }
}

// Case endpoints
export const caseApi = {
  list: () => apiClient.get('/cases'),
  get: (id) => apiClient.get(`/cases/${id}`),
  create: (data) => apiClient.post('/cases', data),
  update: (id, data) => apiClient.patch(`/cases/${id}`, data),
  delete: (id) => apiClient.delete(`/cases/${id}`),

  // Lifecycle
  progress: (id) => apiClient.get(`/cases/${id}/progress`),
  stateEvents: (id) => apiClient.get(`/cases/${id}/state-events`),
  analysisRuns: (id) => apiClient.get(`/cases/${id}/analysis-runs`),
  saveDraft: (id, data) => apiClient.post(`/cases/${id}/save-draft`, {
    return_to_dashboard: false,
    actor_id: data?.actor_id || 'attorney:unknown',
    actor_type: data?.actor_type || 'ATTORNEY',
    name: data?.name,
    court: data?.court,
    plaintiff: data?.plaintiff,
    defendant: data?.defendant,
    reason: data?.reason || 'save-draft',
  }),
  saveAndReturn: (id, data) => apiClient.post(`/cases/${id}/save-draft`, {
    return_to_dashboard: true,
    actor_id: data?.actor_id || 'attorney:unknown',
    actor_type: data?.actor_type || 'ATTORNEY',
    name: data?.name,
    court: data?.court,
    plaintiff: data?.plaintiff,
    defendant: data?.defendant,
    reason: data?.reason || 'save-and-return',
  }),
  markReady: (id, actorId, reason) => apiClient.post(`/cases/${id}/mark-ready`, {
    actor_id: actorId || 'attorney:unknown',
    actor_type: 'ATTORNEY',
    reason,
  }),
  submitForAnalysis: (id, actorId, role) => apiClient.post(`/cases/${id}/submit-for-analysis`, {
    actor_id: actorId || 'attorney:unknown',
    actor_type: 'ATTORNEY',
    role: role || 'lead_attorney',
  }),
  returnToIntake: (id, actorId, reason) => apiClient.post(`/cases/${id}/return-to-intake`, {
    actor_id: actorId || 'attorney:unknown',
    actor_type: 'ATTORNEY',
    reason: reason || 'returned to intake',
  }),
}

// Weapon endpoints
export const weaponApi = {
  list: (caseId) => apiClient.get(`/weapons?case_id=${caseId}`),
  get: (id) => apiClient.get(`/weapons/${id}`),
  update: (id, data) => apiClient.patch(`/weapons/${id}`, data),
  simulate: (id) => apiClient.post(`/weapons/${id}/simulate`, {}),
  deploy: (id) => apiClient.post(`/weapons/${id}/deploy`, {})
}

// Strategy endpoints
export const strategyApi = {
  list: (caseId) => apiClient.get(`/strategies/case/${caseId}`),
  get: (id) => apiClient.get(`/strategies/${id}`)
}

// COA endpoints
export const coaApi = {
  list: (caseId) => apiClient.get(`/coas/case/${caseId}`),
  get: (id) => apiClient.get(`/coas/${id}`)
}

// Document endpoints
export const documentApi = {
  list: (caseId) => apiClient.get(`/documents/case/${caseId}`),
  get: (id) => apiClient.get(`/documents/${id}`),
  ingestStatus: (caseId) => apiClient.get(`/documents/case/${caseId}/ingest-status`),
  archives: (caseId) => apiClient.get(`/documents/case/${caseId}/archives`),
  uploadConfig: () => apiClient.get('/documents/upload-config'),
  checkHashes: (caseId, sha256_list) =>
    apiClient.post(`/documents/case/${caseId}/check-hashes`, { sha256_list }),
  delete: (docId) => apiClient.delete(`/documents/${docId}`),
  // uploadFiles + uploadZip are implemented in UploadPanel (XHR per file for
  // per-file progress), not through the simple fetch wrapper.
}

// Actor endpoints
export const actorApi = {
  list: (caseId) => apiClient.get(`/actors/case/${caseId}`),
  get: (id) => apiClient.get(`/actors/${id}`),
  create: (data) => apiClient.post('/actors/', data),
  update: (id, data) => apiClient.patch(`/actors/${id}`, data),
  delete: (id) => apiClient.delete(`/actors/${id}`),
  merge: (sourceIds, targetId) =>
    apiClient.post('/actors/merge', { source_actor_ids: sourceIds, target_actor_id: targetId }),
  mentions: (id) => apiClient.get(`/actors/${id}/mentions`),
}

// Analysis (intake → brain pipeline output)
export const analysisApi = {
  get: (caseId) => apiClient.get(`/cases/${caseId}/analysis`),
}

// Timeline endpoints
export const timelineApi = {
  get: (caseId, { source, event_type } = {}) => {
    const params = new URLSearchParams()
    if (source) params.set('source', source)
    if (event_type) params.set('event_type', event_type)
    const qs = params.toString()
    return apiClient.get(`/timeline/${caseId}${qs ? `?${qs}` : ''}`)
  },
  build: (caseId, replace = true) =>
    apiClient.post(`/timeline/${caseId}/build`, { replace }),
}

// Legal Library endpoints
export const legalLibraryApi = {
  stats: () => apiClient.get('/legal-library/stats'),
  list: ({ code, q, limit = 200, offset = 0 } = {}) => {
    const params = new URLSearchParams()
    if (code) params.set('code', code)
    if (q) params.set('q', q)
    params.set('limit', String(limit))
    params.set('offset', String(offset))
    return apiClient.get(`/legal-library/records?${params.toString()}`)
  },
  get: (recordId) => apiClient.get(`/legal-library/records/${encodeURIComponent(recordId)}`),
}

// Interview endpoints
export const interviewApi = {
  create: (caseId, mode = 'GUIDED_QUESTIONS') =>
    apiClient.post('/interviews/', { case_id: caseId, mode }),
  getForCase: (caseId) => apiClient.get(`/interviews/case/${caseId}`),
  get: (id) => apiClient.get(`/interviews/${id}`),
  switchMode: (id, mode) => apiClient.patch(`/interviews/${id}/mode`, { mode }),
  updateNarrative: (id, narrative_text) =>
    apiClient.patch(`/interviews/${id}/narrative`, { narrative_text }),
  updateQuestion: (questionId, answer_text) =>
    apiClient.patch(`/interviews/questions/${questionId}`, { answer_text }),
  progress: (id) => apiClient.get(`/interviews/${id}/progress`),
  complete: (id, actorId) => apiClient.post(`/interviews/${id}/complete`, { actor_id: actorId }),
}

// Deposition endpoints
export const depositionApi = {
  create: (data) => apiClient.post('/deposition/sessions', data),
  get: (id) => apiClient.get(`/deposition/sessions/${id}`),
  list: (caseId) => apiClient.get(`/deposition/sessions/case/${caseId}`),
  updateTranscript: (id, transcript) => apiClient.patch(`/deposition/sessions/${id}/transcript`, { transcript_text: transcript }),
  close: (id) => apiClient.patch(`/deposition/sessions/${id}/close`, {})
}

// Case-scoped authority decision endpoints (provisional CACI governance)
export const caseAuthorityApi = {
  // Legal Library — all provisional candidates
  library: () => apiClient.get('/case-authority/library/provisional'),
  // Case-to-authority map (attorney review surface)
  map: (caseId) => apiClient.get(`/case-authority/case/${caseId}/map`),
  // Resolver (tri-signal block)
  resolve: (caseId, caciId) => apiClient.get(`/case-authority/resolve/case/${caseId}/caci/${caciId}`),
  // Decisions
  listCaseDecisions: (caseId, activeOnly = true) =>
    apiClient.get(`/case-authority/decisions/case/${caseId}?active_only=${activeOnly}`),
  history: (caseId, caciId) =>
    apiClient.get(`/case-authority/decisions/case/${caseId}/caci/${caciId}/history`),
  accept: (caseId, caciId, pinnedRecordId, attorneyId, role, rationale) =>
    apiClient.post('/case-authority/decisions', {
      case_id: caseId,
      caci_id: caciId,
      state: 'ACCEPTED',
      pinned_record_id: pinnedRecordId,
      decided_by_actor_type: 'ATTORNEY',
      decided_by_actor_id: attorneyId,
      decided_by_role: role,
      rationale: rationale,
      source_event: 'ui:accept',
    }),
  reject: (caseId, caciId, attorneyId, role, rationale) =>
    apiClient.post('/case-authority/decisions', {
      case_id: caseId,
      caci_id: caciId,
      state: 'REJECTED',
      pinned_record_id: null,
      decided_by_actor_type: 'ATTORNEY',
      decided_by_actor_id: attorneyId,
      decided_by_role: role,
      rationale: rationale,
      source_event: 'ui:reject',
    }),
  replace: (caseId, caciId, attorneyId, role, replacement, rationale) =>
    apiClient.post('/case-authority/decisions', {
      case_id: caseId,
      caci_id: caciId,
      state: 'REPLACED',
      pinned_record_id: null,
      replacement,
      decided_by_actor_type: 'ATTORNEY',
      decided_by_actor_id: attorneyId,
      decided_by_role: role,
      rationale: rationale,
      source_event: 'ui:replace',
    }),
}
