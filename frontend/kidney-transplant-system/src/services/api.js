const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status, data = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

export function getAuthToken() {
  return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
}

export function storeAuthToken(token, remember) {
  clearAuthToken()
  const storage = remember ? localStorage : sessionStorage
  storage.setItem('auth_token', token)
}

export function clearAuthToken() {
  localStorage.removeItem('auth_token')
  sessionStorage.removeItem('auth_token')
}

async function request(path, { method = 'GET', body, authenticated = true } = {}) {
  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const token = getAuthToken()
  if (authenticated && token) headers.Authorization = `Bearer ${token}`

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body)
    })
  } catch {
    throw new ApiError('ارتباط با سرور برقرار نشد. لطفاً دوباره تلاش کنید.', 0)
  }

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (response.status === 401 && authenticated) {
      clearAuthToken()
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    throw new ApiError(data.message || 'خطایی در انجام درخواست رخ داد.', response.status, data)
  }
  return data
}

export const authApi = {
  login(credentials) {
    return request('/auth/login/', { method: 'POST', body: credentials, authenticated: false })
  },
  logout() {
    return request('/auth/logout/', { method: 'POST', body: {} })
  },
  getProfile() {
    return request('/auth/me/')
  },
  updateProfile(profile) {
    return request('/auth/me/', { method: 'PATCH', body: profile })
  },
  changePassword(passwords) {
    return request('/auth/change-password/', { method: 'POST', body: passwords })
  },
  updateNotificationPreferences(preferences) {
    return request('/auth/notification-preferences/', {
      method: 'PATCH',
      body: preferences
    })
  },
  requestPasswordReset(email) {
    return request('/auth/password-reset/', {
      method: 'POST',
      body: { email },
      authenticated: false
    })
  },
  confirmPasswordReset(payload) {
    return request('/auth/password-reset/confirm/', {
      method: 'POST',
      body: payload,
      authenticated: false
    })
  }
}

export const registryApi = {
  listRecipients(params = {}) {
    const query = new URLSearchParams(Object.entries(params).filter(([,value]) => value !== '' && value != null))
    return request(`/registry/recipients/${query.size ? `?${query}` : ''}`)
  },
  getRecipient(id) {
    return request(`/registry/recipients/${id}/`)
  },
  createRecipient(payload) {
    return request('/registry/recipients/', { method: 'POST', body: payload })
  },
  listDonors(params = {}) {
    const query = new URLSearchParams(Object.entries(params).filter(([,value]) => value !== '' && value != null))
    return request(`/registry/donors/${query.size ? `?${query}` : ''}`)
  },
  getDonor(id) {
    return request(`/registry/donors/${id}/`)
  },
  createDonor(payload) {
    return request('/registry/donors/', { method: 'POST', body: payload })
  },
  checkIdentifier(citizenship, identifier) {
    const params = new URLSearchParams({ citizenship, identifier })
    return request(`/registry/identifier-availability/?${params}`)
  },
  lookupRecipient(identifier) {
    return request(`/registry/recipients/lookup/?identifier=${encodeURIComponent(identifier)}`)
  },
  lookupPerson(identifier) {
    return request(`/registry/people/lookup/?identifier=${encodeURIComponent(identifier)}`)
  },
  updatePersonProfile(personId, payload) {
    return request(`/registry/people/${personId}/profile/`, { method: 'PATCH', body: payload })
  },
  saveHla(personId, payload) {
    return request(`/registry/people/${personId}/hla/`, { method: 'PUT', body: payload })
  },
  createCdcPra(personId, payload) {
    return request(`/registry/people/${personId}/cdc-pra/`, { method: 'POST', body: payload })
  },
  updateCdcPra(personId, testId, payload) {
    return request(`/registry/people/${personId}/cdc-pra/${testId}/`, { method: 'PATCH', body: payload })
  },
  createAntiHla(personId, payload) {
    return request(`/registry/people/${personId}/anti-hla/`, { method: 'POST', body: payload })
  },
  updateAntiHla(personId, testId, payload) {
    return request(`/registry/people/${personId}/anti-hla/${testId}/`, { method: 'PATCH', body: payload })
  },
  createLabTest(personId, payload) {
    return request(`/registry/people/${personId}/labs/`, { method: 'POST', body: payload })
  },
  saveLabTestBatch(personId, payload) {
    return request(`/registry/people/${personId}/labs/`, { method: 'POST', body: payload })
  },
  updateLabTest(personId, testId, payload) {
    return request(`/registry/people/${personId}/labs/${testId}/`, { method: 'PATCH', body: payload })
  },
  createApproval(personId, payload) {
    return request(`/registry/people/${personId}/approvals/`, { method: 'POST', body: payload })
  },
  updateApproval(personId, approvalId, payload) {
    return request(`/registry/people/${personId}/approvals/${approvalId}/`, { method: 'PATCH', body: payload })
  },
  updateRecipientStatus(personId, status, reason) {
    return request(`/registry/recipients/${personId}/status/`, {
      method: 'POST', body: { status, reason }
    })
  },
  updateRecipientPriority(personId, payload) {
    return request(`/registry/recipients/${personId}/priority/`, { method: 'PATCH', body: payload })
  },
  updateDonorStatus(personId, status, reason) {
    return request(`/registry/donors/${personId}/status/`, {
      method: 'POST', body: { status, reason }
    })
  },
  previewMatch(recipientId, donorId) {
    return request('/registry/matching/preview/', {
      method: 'POST', body: { recipient_id: recipientId, donor_id: donorId }
    })
  },
  matchDeceasedDonor(payload) {
    return request('/registry/matching/deceased-donor/', { method: 'POST', body: payload })
  },
  runMatching(recipientId, topN = 10) {
    return request('/registry/matching/runs/', {
      method: 'POST', body: { recipient_id: recipientId, top_n: topN }
    })
  },
  enqueueMatching(payload) {
    return request('/registry/matching/enqueue/', { method: 'POST', body: payload })
  },
  listMatchProposals(params = {}) {
    const query = new URLSearchParams(params)
    return request(`/registry/matching/proposals/${query.size ? `?${query}` : ''}`)
  },
  getPatientMatches(personId) {
    return request(`/registry/recipients/${personId}/matches/`)
  },
  getDonorMatches(personId) {
    return request(`/registry/donors/${personId}/matches/`)
  },
  requestConsultation(proposalId, patientNote = '') {
    return request(`/registry/matching/proposals/${proposalId}/consultation/`, {
      method: 'POST', body: { patient_note: patientNote }
    })
  },
  decideProposal(proposalId, decision, note) {
    return request(`/registry/matching/proposals/${proposalId}/decision/`, {
      method: 'PATCH', body: { decision, note }
    })
  },
  listCrossmatches(status = '') {
    const query = status ? `?status=${encodeURIComponent(status)}` : ''
    return request(`/registry/matching/crossmatches/${query}`)
  },
  updateCrossmatch(id, status, physicianNote, highResolutionConfirmed = false) {
    return request(`/registry/matching/crossmatches/${id}/`, {
      method: 'PATCH', body: {
        status,
        physician_note: physicianNote,
        high_resolution_confirmed: highResolutionConfirmed
      }
    })
  },
  getAllocationPolicy() {
    return request('/registry/matching/policy/')
  },
  getNationalReport() {
    return request('/registry/reports/national/')
  },
  getNotifications() {
    return request('/registry/notifications/')
  }
}
