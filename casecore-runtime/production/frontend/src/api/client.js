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
  delete: (id) => apiClient.delete(`/cases/${id}`)
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
  get: (id) => apiClient.get(`/documents/${id}`)
}

// Deposition endpoints
export const depositionApi = {
  create: (data) => apiClient.post('/deposition/sessions', data),
  get: (id) => apiClient.get(`/deposition/sessions/${id}`),
  list: (caseId) => apiClient.get(`/deposition/sessions/case/${caseId}`),
  updateTranscript: (id, transcript) => apiClient.patch(`/deposition/sessions/${id}/transcript`, { transcript_text: transcript }),
  close: (id) => apiClient.patch(`/deposition/sessions/${id}/close`, {})
}
