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
