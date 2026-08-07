const LOCUS_LABELS = {
  A: 'HLA-A',
  B: 'HLA-B',
  C: 'HLA-C',
  DRB1: 'HLA-DRB1',
  DQB1: 'HLA-DQB1',
  DRB: 'HLA-DRB3/4/5',
}

const DEFAULT_LOCI = ['A', 'B', 'C', 'DRB1', 'DQB1']

function normalizeList(values) {
  if (!Array.isArray(values)) return []
  const seen = new Set()
  const items = []
  values.forEach(value => {
    const text = String(value ?? '').trim()
    if (!text || seen.has(text)) return
    seen.add(text)
    items.push(text)
  })
  return items
}

function formatList(values, empty = '—') {
  const items = normalizeList(values)
  return items.length ? items.join('، ') : empty
}

function reasonText(items, empty = '—') {
  if (!Array.isArray(items) || !items.length) return empty
  return items
    .map(item => (typeof item === 'string' ? item : item?.message || item?.code || ''))
    .filter(Boolean)
    .join('، ')
}

function summaryOfLocus(locus) {
  const recipient = normalizeList(locus?.recipient ?? locus?.recipient_alleles ?? locus?.recipientValues)
  const donor = normalizeList(
    locus?.donor ?? locus?.donor_alleles ?? locus?.temporary ?? locus?.donorValues
  )
  const common = normalizeList(locus?.common ?? locus?.matches ?? locus?.shared)
  const recipientOnly = recipient.filter(value => !common.includes(value))
  const donorOnly = donor.filter(value => !common.includes(value))
  const matches = Number(locus?.matches ?? common.length ?? 0)
  const maximum = Number(locus?.maximum ?? Math.max(recipient.length, donor.length, 2))
  return { recipient, donor, common, recipientOnly, donorOnly, matches, maximum }
}

export function buildLocusTooltip(locusName, locus, { recipientLabel = 'گیرنده', donorLabel = 'اهداکننده' } = {}) {
  const label = LOCUS_LABELS[locusName] || locusName
  if (!locus) {
    return `${label}: اطلاعات ثبت نشده`
  }

  const data = summaryOfLocus(locus)
  const lines = [`${label}: ${data.matches}/${data.maximum}`]

  if (data.common.length) {
    lines.push(`مشترک: ${formatList(data.common)}`)
  }
  lines.push(`${recipientLabel}: ${formatList(data.recipient)}`)
  if (data.recipientOnly.length) {
    lines.push(`فقط ${recipientLabel}: ${formatList(data.recipientOnly)}`)
  }
  lines.push(`${donorLabel}: ${formatList(data.donor)}`)
  if (data.donorOnly.length) {
    lines.push(`فقط ${donorLabel}: ${formatList(data.donorOnly)}`)
  }

  return lines.join('\n')
}

export function buildHlaTooltip(summary, options = {}) {
  const loci = options.loci || DEFAULT_LOCI
  if (!summary) return 'جزئیات HLA ثبت نشده است.'

  const total = Number(summary.total_matches ?? summary.matches ?? 0)
  const maximum = Number(summary.maximum ?? 10)
  const percent = summary.percent != null ? ` (${summary.percent}٪)` : ''
  const lines = [`تطابق HLA: ${total}/${maximum}${percent}`]

  loci.forEach(locusName => {
    lines.push(buildLocusTooltip(locusName, summary.loci?.[locusName], options))
  })

  return lines.join('\n')
}

export function buildSimilarityChips(summary, options = {}) {
  if (!summary?.loci) return []
  const chipPrefix = options.prefix || '+'
  return Object.entries(summary.loci)
    .filter(([, locus]) => Number(locus?.matches ?? 0) > 0)
    .map(([locusName, locus]) => ({
      key: locusName,
      label: `${chipPrefix}${locusName}`,
      count: Number(locus?.matches ?? 0),
      title: buildLocusTooltip(locusName, locus, options),
    }))
}

export function buildSimpleHlaTooltip(similarity) {
  if (!similarity) return 'شباهت HLA ثبت نشده است.'
  const matches = Number(similarity.matches ?? 0)
  const maximum = Number(similarity.maximum ?? 0)
  const percent = similarity.percent != null ? `${similarity.percent}٪` : '—'
  return [`شباهت HLA: ${matches}/${maximum}`, `درصد: ${percent}`].join('\n')
}

export function buildImmuneTooltip(match) {
  if (!match) return 'جزئیات ایمونولوژیک ثبت نشده است.'

  const antiStatus = {
    clear: 'بدون mismatch',
    conditional: 'نیازمند بررسی تکمیلی',
    mismatch: 'Mismatch مستقیم',
    'insufficient-data': 'اطلاعات ناکافی',
  }[match.anti_hla_status] || match.anti_hla_status || 'بررسی‌نشده'

  const creg = match.creg_summary || {}
  const lines = [`Anti-HLA: ${antiStatus}`]

  if (creg.active_groups?.length) {
    lines.push(`CREG فعال: ${formatList(creg.active_groups)}`)
  }
  if (creg.potential_conflicts?.length) {
    lines.push(`تعارض‌های بالقوه: ${reasonText(creg.potential_conflicts)}`)
  }
  if (match.warnings?.length) {
    lines.push(`هشدارها: ${reasonText(match.warnings)}`)
  }
  if (match.rejection_reasons?.length) {
    lines.push(`دلایل رد: ${reasonText(match.rejection_reasons)}`)
  }

  return lines.join('\n')
}

export function buildCompatibilityTooltip(match) {
  if (!match) return 'جزئیات سازگاری ثبت نشده است.'
  const lines = [
    `سازگاری: ${match.compatibility_display || match.compatibility || '—'}`,
    `ABO: ${match.abo_compatible ? 'سازگار' : 'ناسازگار'}`,
  ]
  if (match.hla_summary) lines.push(buildHlaTooltip(match.hla_summary))
  lines.push(buildImmuneTooltip(match))
  return lines.join('\n')
}

export function buildMismatchSummary(summary, { recipientLabel = 'گیرنده', donorLabel = 'اهداکننده' } = {}) {
  if (!summary) return 'جزئیات HLA ثبت نشده است.'
  const data = summaryOfLocus(summary)
  const lines = []
  if (data.common.length) lines.push(`مشترک: ${formatList(data.common)}`)
  lines.push(`${recipientLabel}: ${formatList(data.recipient)}`)
  if (data.recipientOnly.length) lines.push(`فقط ${recipientLabel}: ${formatList(data.recipientOnly)}`)
  lines.push(`${donorLabel}: ${formatList(data.donor)}`)
  if (data.donorOnly.length) lines.push(`فقط ${donorLabel}: ${formatList(data.donorOnly)}`)
  return lines.join('\n')
}

export function joinReasonMessages(items) {
  return reasonText(items)
}

export function getPageSlice(items, page, pageSize) {
  const start = Math.max(0, (Number(page) - 1) * Number(pageSize))
  return items.slice(start, start + Number(pageSize))
}

export function buildLocalPagination(count, page, pageSize) {
  const pages = Math.max(1, Math.ceil(Number(count) / Number(pageSize || 1)))
  const currentPage = Math.min(Math.max(1, Number(page) || 1), pages)
  return {
    page: currentPage,
    pages,
    count: Number(count) || 0,
    has_next: currentPage < pages,
    has_previous: currentPage > 1,
  }
}
