/**
 * Validate Iranian National ID
 */
export const nationalIdChecker = (id) => {
  try {
    if (!/^\d{10}$/.test(id)) return false
    if (/^(\d)\1{9}$/.test(id)) return false
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

/**
 * Convert Persian and Arabic digits inside any input to Latin digits.
 * Text is preserved so it can also be used for qualitative lab results.
 */
export const normalizeLocalizedDigits = (v) => String(v ?? '')
  .replace(/[۰-۹]/g, d => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d)))
  .replace(/[٠-٩]/g, d => String('٠١٢٣٤٥٦٧٨٩'.indexOf(d)))
  .replace(/٫/g, '.')
  .replace(/٬/g, ',')

/**
 * Normalize a localized positive decimal number to one Latin representation.
 */
export const normalizeLocalizedNumber = (v) => {
  const normalized = normalizeLocalizedDigits(v)
    .replace(/[,\s]/g, '')
    .replace(/[^0-9.]/g, '')
  const [integer = '', ...decimals] = normalized.split('.')
  return decimals.length ? `${integer}.${decimals.join('')}` : integer
}

/**
 * Normalize a localized signed decimal while preserving one leading minus.
 */
export const normalizeLocalizedSignedNumber = (v) => {
  const compact = normalizeLocalizedDigits(v)
    .replace(/[,\s]/g, '')
    .replace(/[^0-9.\-]/g, '')
  const negative = compact.startsWith('-')
  const unsigned = compact.replace(/-/g, '')
  const [integer = '', ...decimals] = unsigned.split('.')
  const number = decimals.length ? `${integer}.${decimals.join('')}` : integer
  return `${negative ? '-' : ''}${number}`
}

/**
 * Normalize ranges used by urine microscopy fields, for example ۱-۳ → 1-3.
 */
export const normalizeLocalizedNumberRange = (v) => {
  const normalized = normalizeLocalizedDigits(v)
    .replace(/[–—]/g, '-')
    .replace(/\s/g, '')
    .replace(/[^0-9.\-]/g, '')
  const parts = normalized.split('-').slice(0, 2)
  return parts.map(part => normalizeLocalizedNumber(part)).join('-')
}
