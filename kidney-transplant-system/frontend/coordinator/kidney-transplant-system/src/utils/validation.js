/**
 * Validate Iranian National ID
 */
export const nationalIdChecker = (id) => {
  try {
    if (!/^\d{10}$/.test(id)) return false
    let sum = 0
    for (let i = 0; i < 9; i++) sum += parseInt(id[i]) * (10 - i)
    const remainder = sum % 11
    const lastDigit = parseInt(id[9])
    if (remainder < 2) return lastDigit === remainder
    return lastDigit === (11 - remainder)
  } catch (e) {
    return false
  }
}

/**
 * Normalize national ID input (convert Persian/Arabic digits to English)
 */
export const normalizeNationalId = (v) => {
  return String(v || '')
    .replace(/[۰-۹]/g, d => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)))
    .replace(/[٠-٩]/g, d => String('٠١٢٣٤٥٦٧٨٩'.indexOf(d)))
    .replace(/\D/g, '')
    .trim()
}

/**
 * Normalize Iranian mobile number
 */
export const normalizeIranianMobile = (v) => {
  const digits = String(v || '')
    .replace(/[۰-۹]/g, d => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)))
    .replace(/[٠-٩]/g, d => String('٠١٢٣٤٥٦٧٨٩'.indexOf(d)))
    .replace(/\D/g, '')
  if (!digits) return ''
  if (digits.length === 10 && !digits.startsWith('0')) return ('0' + digits).slice(0, 11)
  return digits.slice(0, 11)
}

/**
 * Validate Iranian mobile number format
 */
export const isValidIranianMobile = (v) => /^09\d{9}$/.test(String(v || '').trim())
