import * as jalaali from 'jalaali-js'

/**
 * Convert Gregorian date to Jalali
 */
export const gregorianToJalali = (gy, gm, gd) => {
  if (jalaali?.toJalaali) {
    const r = jalaali.toJalaali(gy, gm, gd)
    return { jy: r.jy, jm: r.jm, jd: r.jd }
  }
  // Fallback implementation
  const g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
  let gy2 = gm > 2 ? gy + 1 : gy
  let days = 355666 + 365 * gy + Math.floor((gy2 + 3) / 4) - Math.floor((gy2 + 99) / 100) + Math.floor((gy2 + 399) / 400) + gd + g_d_m[gm - 1]
  let jy = -1595 + 33 * Math.floor(days / 12053)
  days %= 12053
  jy += 4 * Math.floor(days / 1461)
  days %= 1461
  if (days > 365) {
    jy += Math.floor((days - 1) / 365)
    days = (days - 1) % 365
  }
  const jm = days < 186 ? 1 + Math.floor(days / 31) : 7 + Math.floor((days - 186) / 30)
  const jd = 1 + (days < 186 ? days % 31 : (days - 186) % 30)
  return { jy, jm, jd }
}

/**
 * Convert Jalali date to Gregorian
 */
export const jalaliToGregorian = (jy, jm, jd) => {
  if (jalaali?.toGregorian) {
    const r = jalaali.toGregorian(jy, jm, jd)
    return { gy: r.gy, gm: r.gm, gd: r.gd }
  }
  // Fallback implementation
  let jy2 = jy + 1595
  let days = -355668 + 365 * jy2 + Math.floor(jy2 / 33) * 8 + Math.floor(((jy2 % 33) + 3) / 4) + jd + (jm < 7 ? (jm - 1) * 31 : (jm - 7) * 30 + 186)
  let gy = 400 * Math.floor(days / 146097)
  days %= 146097
  if (days > 36524) {
    gy += 100 * Math.floor(--days / 36524)
    days %= 36524
    if (days >= 365) days++
  }
  gy += 4 * Math.floor(days / 1461)
  days %= 1461
  if (days > 365) {
    gy += Math.floor((days - 1) / 365)
    days = (days - 1) % 365
  }
  let gd = days + 1
  const g_d_m = [0, 31, ((gy % 4 === 0 && gy % 100 !== 0) || (gy % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  let gm
  for (gm = 0; gm < 13 && gd > g_d_m[gm]; gm++) gd -= g_d_m[gm]
  return { gy, gm, gd }
}

/**
 * Convert Jalali string (YYYY-MM-DD) to Gregorian string
 */
export const jalaliStrToGregorian = (str) => {
  if (!str || !/^\d{4}-\d{2}-\d{2}$/.test(str)) return ''
  const [jy, jm, jd] = str.split('-').map(Number)
  const r = jalaliToGregorian(jy, jm, jd)
  if (!r || !r.gy) return ''
  const pad = n => String(n).padStart(2, '0')
  return `${r.gy}-${pad(r.gm)}-${pad(r.gd)}`
}

/**
 * Convert Gregorian string (YYYY-MM-DD) to Jalali string
 */
export const gregorianStrToJalali = (str) => {
  if (!str || !/^\d{4}-\d{2}-\d{2}$/.test(str)) return ''
  const [gy, gm, gd] = str.split('-').map(Number)
  const r = gregorianToJalali(gy, gm, gd)
  if (!r || !r.jy) return ''
  const pad = n => String(n).padStart(2, '0')
  return `${r.jy}-${pad(r.jm)}-${pad(r.jd)}`
}

/**
 * Get length of a Jalali month
 */
export const jMonthLength = (jy, jm) => {
  if (jalaali?.jalaaliMonthLength) return jalaali.jalaaliMonthLength(jy, jm)
  if (jm <= 6) return 31
  if (jm <= 11) return 30
  const g = jalaliToGregorian(jy, 12, 30)
  const back = gregorianToJalali(g.gy, g.gm, g.gd)
  return back.jy === jy ? 30 : 29
}

/**
 * Convert digits to Persian/Farsi
 */
export const toFaDigits = (v) => String(v).replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d])

/**
 * Pad number with leading zero
 */
export const pad2 = n => String(n).padStart(2, '0')

/**
 * Jalali months names
 */
export const JALALI_MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']

/**
 * Gregorian months names in Persian
 */
export const GREGORIAN_MONTHS_FA = ['ژانویه', 'فوریه', 'مارس', 'آوریل', 'مه', 'ژوئن', 'ژوئیه', 'اوت', 'سپتامبر', 'اکتبر', 'نوامبر', 'دسامبر']

/**
 * Weekday names in Persian
 */
export const WEEKDAYS_FA = ['یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه']

/**
 * Weekday letters (for calendar headers)
 */
export const WEEKDAY_LETTERS = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']

/**
 * Get current date in both Gregorian and Jalali formats
 */
export const getCurrentDate = () => {
  const now = new Date()
  const j = gregorianToJalali(now.getFullYear(), now.getMonth() + 1, now.getDate())
  return {
    gregorian: toFaDigits(`${now.getFullYear()}/${pad2(now.getMonth() + 1)}/${pad2(now.getDate())}`),
    jalali: `${WEEKDAYS_FA[now.getDay()]} ${toFaDigits(j.jy)}/${toFaDigits(j.jm)}/${toFaDigits(j.jd)}`
  }
}

/**
 * Format date string to Persian Jalali format
 */
export const formatFaDate = (dateStr) => {
  if (!dateStr) return '—'
  try {
    const [y, m, d] = String(dateStr).slice(0, 10).split('-').map(Number)
    const j = gregorianToJalali(y, m, d)
    return `${toFaDigits(j.jy)}/${toFaDigits(j.jm)}/${toFaDigits(j.jd)}`
  } catch (e) {
    return dateStr
  }
}
