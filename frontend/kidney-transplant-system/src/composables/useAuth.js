import { reactive } from 'vue'
import { authApi, clearAuthToken, getAuthToken, storeAuthToken } from '../services/api'

const authState = reactive({
  user: null,
  initialized: false,
  loading: false
})

let pendingInitialization = null

async function ensureAuthenticated(forceValidation = false) {
  if (!getAuthToken()) {
    authState.user = null
    authState.initialized = true
    return false
  }
  if (!forceValidation && authState.initialized && authState.user) return true
  if (pendingInitialization) return pendingInitialization

  authState.loading = true
  pendingInitialization = authApi.getProfile()
    .then(({ user }) => {
      authState.user = user
      authState.initialized = true
      return true
    })
    .catch(() => {
      clearAuthToken()
      authState.user = null
      authState.initialized = true
      return false
    })
    .finally(() => {
      authState.loading = false
      pendingInitialization = null
    })
  return pendingInitialization
}

async function login(credentials) {
  const data = await authApi.login(credentials)
  storeAuthToken(data.token, credentials.remember)
  authState.user = data.user
  authState.initialized = true
  return data.user
}

async function logout() {
  try {
    if (getAuthToken()) await authApi.logout()
  } finally {
    clearAuthToken()
    authState.user = null
    authState.initialized = true
  }
}

function setUser(user) {
  authState.user = user
  authState.initialized = true
}

window.addEventListener('auth:unauthorized', () => {
  authState.user = null
  authState.initialized = true
})

export function useAuth() {
  return { authState, ensureAuthenticated, login, logout, setUser }
}
