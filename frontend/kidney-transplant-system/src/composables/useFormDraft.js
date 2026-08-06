import { onBeforeUnmount, watch } from 'vue'

export const FORM_DRAFT_TTL_MS = 8 * 60 * 60 * 1000

const getStorage = () => {
  try {
    return window.sessionStorage
  } catch {
    return null
  }
}

export function loadFormDraft(storageKey) {
  const storage = getStorage()
  if (!storage) return null
  try {
    const raw = storage.getItem(storageKey)
    if (!raw) return null
    const payload = JSON.parse(raw)
    if (payload.version !== 1 || !payload.expiresAt || Date.now() >= payload.expiresAt) {
      storage.removeItem(storageKey)
      return null
    }
    return payload.data || null
  } catch {
    storage.removeItem(storageKey)
    return null
  }
}

export function useFormDraft(storageKey, source, { ttlMs = FORM_DRAFT_TTL_MS, debounceMs = 300 } = {}) {
  const storage = getStorage()
  let active = true
  let saveTimer = null

  const saveDraft = () => {
    if (!active || !storage) return
    try {
      const now = Date.now()
      storage.setItem(storageKey, JSON.stringify({
        version: 1,
        savedAt: now,
        expiresAt: now + ttlMs,
        data: source()
      }))
    } catch {
      // Storage can be unavailable or full; the form must remain usable either way.
    }
  }

  const scheduleSave = () => {
    if (!active) return
    window.clearTimeout(saveTimer)
    saveTimer = window.setTimeout(saveDraft, debounceMs)
  }

  const stop = watch(source, scheduleSave, { deep: true })

  const clearDraft = () => {
    active = false
    window.clearTimeout(saveTimer)
    stop()
    try { storage?.removeItem(storageKey) } catch { /* no-op */ }
  }

  onBeforeUnmount(() => {
    window.clearTimeout(saveTimer)
    if (active) saveDraft()
    stop()
  })

  return { clearDraft, saveDraft }
}
