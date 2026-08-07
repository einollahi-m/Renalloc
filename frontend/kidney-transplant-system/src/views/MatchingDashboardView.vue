<template>
  <div class="matching-page">
    <div class="page-header">
      <div>
        <div class="page-title">موتور ملی سازگاری‌سنجی</div>
        <div class="page-subtitle">فیلتر ABO و Anti-HLA، امتیاز تطبیقی HLA و رتبه‌بندی قابل توضیح</div>
      </div>
      <button class="btn btn-secondary" :disabled="!selectedRecipient" @click="openPatientView">
        <i class="ri-user-heart-line"></i> پیش‌نمایش بیمار
      </button>
    </div>

    <div v-if="error" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ error }}</div>

    <section class="card matching-toolbar">
      <div class="form-group grow">
        <label class="form-label">گیرنده</label>
        <select v-model="recipientId" class="form-input" @change="loadExisting">
          <option value="">انتخاب گیرنده</option>
          <option v-for="item in recipients" :key="item._id" :value="item._id">
            {{ item.fullName }} — {{ item.bloodType }}{{ item.rhFactor === 'positive' ? '+' : '-' }} — {{ item.statusDisplay }}
          </option>
        </select>
      </div>
      <div class="toolbar-actions">
        <button class="btn btn-primary" :disabled="loading || !canRun" @click="executeMatching">
          <i :class="loading ? 'ri-loader-4-line spin' : 'ri-play-circle-line'"></i>
          {{ loading ? 'در حال محاسبه…' : 'اجرای Top 10' }}
        </button>
      </div>
      <div v-if="selectedRecipient && !canRun" class="readiness-warning">
        <i class="ri-information-line"></i>
        گیرنده باید در وضعیت «فعال در لیست انتظار» باشد. وضعیت را در صفحه لیست انتظار تغییر دهید.
      </div>
    </section>

    <div v-if="runStats" class="stats-grid">
      <div class="stat"><span>جفت بررسی‌شده</span><strong>{{ runStats.evaluated_pairs }}</strong></div>
      <div class="stat"><span>رد ایمنی/بالینی</span><strong>{{ runStats.rejected_pairs }}</strong></div>
      <div class="stat"><span>سازگار مشروط</span><strong>{{ runStats.conditional_pairs }}</strong></div>
      <div class="stat"><span>پیشنهاد نهایی</span><strong>{{ runStats.proposals }}</strong></div>
    </div>

    <div class="matching-layout">
      <section class="card results-card">
        <div class="section-head">
          <div>
            <h3>پیشنهادهای رتبه‌بندی‌شده</h3>
            <p>سیستم پیشنهاد می‌دهد؛ تصمیم نهایی با پزشک و مرکز است.</p>
          </div>
          <span class="badge badge-info">{{ proposals.length }} پیشنهاد</span>
        </div>

        <div v-if="!recipientId" class="empty-state compact-empty-state">
          <i class="ri-user-search-line"></i><p>ابتدا یک گیرنده انتخاب کنید.</p>
        </div>
        <div v-else-if="!loading && !proposals.length" class="empty-state compact-empty-state">
          <i class="ri-shield-cross-line"></i>
          <p>پیشنهادی موجود نیست. پس از تکمیل آزمایش‌ها و فعال‌سازی گیرنده، Matching را اجرا کنید.</p>
        </div>
        <div v-else class="proposal-list">
          <button
            v-for="proposal in paginatedProposals"
            :key="proposal.id"
            class="proposal-row"
            :class="{ active: selectedProposal?.id === proposal.id }"
            :title="buildCompatibilityTooltip(proposal)"
            @click="selectedProposal = proposal"
          >
            <span class="rank">{{ proposal.rank }}</span>
            <span class="proposal-main">
              <strong>{{ proposal.donor.fullName }}</strong>
              <small>{{ proposal.donor.bloodType }}{{ proposal.donor.rhFactor === 'positive' ? '+' : '-' }} · {{ proposal.donor.statusDisplay }}</small>
              <div v-if="similarityChips(proposal.hla_summary).length" class="similarity-row">
                <span
                  v-for="chip in similarityChips(proposal.hla_summary)"
                  :key="chip.key"
                  class="similarity-chip"
                  :title="chip.title"
                >
                  {{ chip.label }}
                </span>
              </div>
            </span>
            <span class="compatibility" :class="proposal.compatibility">
              {{ proposal.compatibility_display }}
            </span>
            <span class="score">{{ fa(Math.round(proposal.final_score)) }}</span>
          </button>
        </div>
        <pagination-controls :pagination="proposalPagination" @change="changePage" />
      </section>

      <section class="card detail-card">
        <template v-if="selectedProposal">
          <div class="section-head">
            <div><h3>چرا این رتبه؟</h3><p>نسخه سیاست: {{ selectedProposal.score_breakdown.policy_version }}</p></div>
            <span class="compatibility" :class="selectedProposal.compatibility">{{ selectedProposal.compatibility_display }}</span>
          </div>

          <div class="abo-line">
            <span><i class="ri-drop-line"></i> گروه خونی</span>
            <strong class="ok">سازگار — Rh نادیده گرفته شده</strong>
          </div>
          <div class="abo-line">
            <span><i class="ri-shield-check-line"></i> Anti-HLA</span>
            <strong :class="selectedProposal.compatibility === 'compatible' ? 'ok' : 'warn'" :title="buildImmuneTooltip(selectedProposal)">
              {{ antiLabel(selectedProposal.anti_hla_status) }}
            </strong>
          </div>

          <div class="hla-grid">
            <div v-for="locus in loci" :key="locus" class="hla-locus" :title="buildLocusTooltip(locus, selectedProposal.hla_summary?.loci?.[locus])">
              <span>{{ locus }} <small v-if="locus === 'C'">فرعی</small></span>
              <strong>{{ selectedProposal.hla_summary.loci[locus]?.matches || 0 }}/2</strong>
              <em>{{ (selectedProposal.hla_summary.loci[locus]?.common || []).join('، ') || 'بدون آلل مشترک' }}</em>
              <small class="mismatch-line">{{ buildMismatchSummary(selectedProposal.hla_summary.loci[locus]) }}</small>
            </div>
          </div>
          <div class="hla-total">
            جمع: {{ selectedProposal.hla_summary.total_matches }} آلل مشترک
            (کلاس I: {{ selectedProposal.hla_summary.class_i_matches }}، کلاس II: {{ selectedProposal.hla_summary.class_ii_matches }})
          </div>
          <div v-if="similarityChips(selectedProposal.hla_summary).length" class="similarity-row detail-similarity">
            <span
              v-for="chip in similarityChips(selectedProposal.hla_summary)"
              :key="chip.key"
              class="similarity-chip"
              :title="chip.title"
            >
              {{ chip.label }}
            </span>
          </div>

          <div v-if="selectedProposal.warnings.length" class="warning-list">
            <div v-for="warning in selectedProposal.warnings" :key="warning.code">
              <i class="ri-alert-line"></i><span>{{ warning.message }}</span>
            </div>
          </div>

          <details class="score-details">
            <summary>اجزای امتیاز عدالت و سازگاری</summary>
            <div class="score-components">
              <span>HLA خام <b>{{ fa(Math.round(selectedProposal.score_breakdown.hla_raw)) }}</b></span>
              <span>HLA تطبیقی <b>{{ fa(Math.round(selectedProposal.score_breakdown.hla_adaptive)) }}</b></span>
              <span>زمان انتظار <b>{{ fa(Math.round(selectedProposal.score_breakdown.waiting_time)) }}</b></span>
              <span>فوریت <b>{{ fa(selectedProposal.score_breakdown.medical_urgency) }}</b></span>
              <span>سختی CDC-PRA <b>{{ fa(Math.round(selectedProposal.score_breakdown.cdc_pra_difficulty ?? selectedProposal.score_breakdown.cpra_difficulty)) }}</b></span>
              <span>منطقه محروم <b>{{ fa(selectedProposal.score_breakdown.regional_disadvantage) }}</b></span>
            </div>
          </details>

          <template v-if="selectedProposal.decision === 'proposed'">
            <div class="form-group decision-note">
              <label class="form-label">یادداشت و دلیل تصمیم پزشک</label>
              <textarea v-model="decisionNote" class="form-input" rows="3" placeholder="دلیل تأیید یا رد را ثبت کنید"></textarea>
            </div>
            <div class="decision-actions">
              <button class="btn btn-secondary danger-text" :disabled="saving" @click="decide('rejected')">رد پیشنهاد</button>
              <button class="btn btn-primary" :disabled="saving" @click="decide('approved')">تأیید و ارجاع به Cross-Match</button>
            </div>
          </template>
          <div v-else class="decision-state">تصمیم ثبت‌شده: <strong>{{ selectedProposal.decision_display }}</strong></div>
        </template>
        <div v-else class="empty-state compact-empty-state">
          <i class="ri-file-search-line"></i><p>برای مشاهده جزئیات، یک پیشنهاد را انتخاب کنید.</p>
        </div>
      </section>
    </div>

    <section class="card transparency-card">
      <div class="section-head"><div><h3>بررسی دلیل رد/قبول یک جفت</h3><p>برای شفافیت بالینی، حتی جفت‌های ردشده قابل توضیح‌اند.</p></div></div>
      <div class="preview-controls">
        <select v-model="donorId" class="form-input"><option value="">انتخاب اهداکننده</option><option v-for="item in donors" :key="item._id" :value="item._id">{{ item.fullName }} — {{ item.bloodType }}{{ item.rhFactor === 'positive' ? '+' : '-' }}</option></select>
        <button class="btn btn-secondary" :disabled="!recipientId || !donorId || previewLoading" @click="previewPair">بررسی جفت</button>
      </div>
      <div v-if="preview" class="preview-result" :class="preview.compatibility">
        <strong>{{ compatibilityLabel(preview.compatibility) }}</strong>
        <div v-for="reason in preview.rejection_reasons" :key="reason.code"><i class="ri-close-circle-line"></i>{{ reason.message }}</div>
        <div v-for="warning in preview.warnings" :key="warning.code"><i class="ri-alert-line"></i>{{ warning.message }}</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { registryApi } from '../services/api'
import { toFaDigits } from '../utils/date'
import PaginationControls from '../components/PaginationControls.vue'
import { buildCompatibilityTooltip, buildImmuneTooltip, buildLocusTooltip, buildMismatchSummary, buildLocalPagination, buildSimilarityChips, getPageSlice } from '../utils/matching'

const router = useRouter()
const recipients = ref([])
const donors = ref([])
const recipientId = ref('')
const donorId = ref('')
const proposals = ref([])
const selectedProposal = ref(null)
const runStats = ref(null)
const loading = ref(false)
const previewLoading = ref(false)
const saving = ref(false)
const error = ref('')
const preview = ref(null)
const decisionNote = ref('')
const loci = ['A', 'B', 'C', 'DRB1', 'DQB1']
const fa = (value) => toFaDigits(value)

const selectedRecipient = computed(() => recipients.value.find(item => item._id === recipientId.value))
const canRun = computed(() => selectedRecipient.value?.status === 'active')
const currentPage = ref(1)
const pageSize = 5
const paginatedProposals = computed(() => getPageSlice(proposals.value, currentPage.value, pageSize))
const proposalPagination = computed(() => buildLocalPagination(proposals.value.length, currentPage.value, pageSize))
const similarityChips = summary => buildSimilarityChips(summary)

const loadExisting = async () => {
  selectedProposal.value = null
  preview.value = null
  runStats.value = null
  currentPage.value = 1
  if (!recipientId.value) { proposals.value = []; return }
  try {
    const response = await registryApi.listMatchProposals({ recipient_id: recipientId.value })
    const seen = new Set()
    proposals.value = response.proposals.filter(item => {
      if (seen.has(item.donor._id)) return false
      seen.add(item.donor._id)
      return true
    }).slice(0, 10)
    selectedProposal.value = proposals.value[0] || null
  } catch (e) { error.value = e.message }
}

const executeMatching = async () => {
  loading.value = true; error.value = ''; decisionNote.value = ''
  try {
    const response = await registryApi.runMatching(recipientId.value, 10)
    proposals.value = response.proposals
    runStats.value = response.run.statistics
    selectedProposal.value = proposals.value[0] || null
    currentPage.value = 1
    window.toast.add({ severity: 'success', summary: 'Matching', detail: response.message })
  } catch (e) { error.value = e.message } finally { loading.value = false }
}

const previewPair = async () => {
  previewLoading.value = true; error.value = ''
  try { preview.value = (await registryApi.previewMatch(recipientId.value, donorId.value)).result }
  catch (e) { error.value = e.message } finally { previewLoading.value = false }
}

const decide = async (decision) => {
  if (!decisionNote.value.trim()) { error.value = 'یادداشت و دلیل تصمیم پزشک الزامی است.'; return }
  saving.value = true; error.value = ''
  try {
    const response = await registryApi.decideProposal(selectedProposal.value.id, decision, decisionNote.value)
    const index = proposals.value.findIndex(item => item.id === selectedProposal.value.id)
    proposals.value[index] = response.proposal
    selectedProposal.value = response.proposal
    window.toast.add({ severity: 'success', summary: 'تصمیم مرکز', detail: response.message })
  } catch (e) { error.value = e.message } finally { saving.value = false }
}

const openPatientView = () => router.push(`/patient-portal/matches?recipient=${recipientId.value}`)
const antiLabel = status => ({ clear: 'بدون mismatch', conditional: 'نیازمند Cross-Match و High-Resolution', 'insufficient-data': 'اطلاعات ناکافی', mismatch: 'Mismatch' }[status] || 'بررسی‌نشده')
const compatibilityLabel = status => ({ compatible: 'سازگار', conditional: 'سازگار مشروط', incompatible: 'ناسازگار', 'insufficient-data': 'اطلاعات ناکافی' }[status] || status)
const changePage = page => { currentPage.value = Math.min(Math.max(1, page), proposalPagination.value.pages) }

onMounted(async () => {
  try {
    const [recipientResponse, donorResponse] = await Promise.all([
      registryApi.listRecipients({page_size:100}), registryApi.listDonors({page_size:100})
    ])
    recipients.value = recipientResponse.recipients
    donors.value = donorResponse.donors
  } catch (e) { error.value = e.message }
})
</script>

<style scoped>
.page-header,.section-head,.matching-toolbar,.toolbar-actions,.abo-line,.decision-actions,.preview-controls{display:flex;align-items:center;justify-content:space-between;gap:14px}.page-header{align-items:flex-start;margin-bottom:20px}.page-title{font-size:23px;font-weight:900}.page-subtitle,.section-head p{color:var(--text-2);font-size:13px;margin:2px 0 0}.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px;box-shadow:var(--shadow-1)}.matching-toolbar{flex-wrap:wrap;margin-bottom:16px}.grow{flex:1;min-width:280px;margin:0}.readiness-warning{width:100%;padding:9px 12px;border-radius:var(--radius-md);background:#fffbeb;color:var(--warning-700)}.spin{animation:spin 1s linear infinite}.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}.stat{padding:14px 16px;border:1px solid var(--border);border-radius:var(--radius-lg);background:var(--surface)}.stat span{display:block;color:var(--text-2);font-size:12px}.stat strong{font-size:22px}.matching-layout{display:grid;grid-template-columns:minmax(340px,.85fr) minmax(440px,1.15fr);gap:16px;margin-bottom:16px}.section-head{margin-bottom:16px;align-items:flex-start}.section-head h3{margin:0;font-size:16px}.proposal-list{display:flex;flex-direction:column;gap:8px}.proposal-row{display:grid;grid-template-columns:34px 1fr auto 46px;align-items:center;gap:10px;width:100%;padding:11px;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--surface);font-family:inherit;text-align:right;cursor:pointer}.proposal-row:hover,.proposal-row.active{border-color:var(--color-primary);background:var(--color-primary-soft)}.rank{width:30px;height:30px;display:grid;place-items:center;border-radius:50%;background:var(--surface-muted);font-weight:900}.proposal-main{display:flex;flex-direction:column}.proposal-main small{color:var(--text-2)}.similarity-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.detail-similarity{margin-top:10px}.similarity-chip{display:inline-flex;align-items:center;padding:3px 10px;border:1px solid #ef4444;border-radius:999px;background:#fff7f7;color:#dc2626;font-size:11px;font-weight:800;cursor:help}.score{font-weight:900;font-size:18px;color:var(--color-primary-dark)}.compatibility{padding:4px 9px;border-radius:999px;font-size:12px;font-weight:800}.compatibility.compatible,.preview-result.compatible{background:#ecfdf5;color:var(--success-700)}.compatibility.conditional,.preview-result.conditional{background:#fffbeb;color:var(--warning-700)}.compatibility.incompatible,.preview-result.incompatible{background:#fef2f2;color:var(--error-700)}.abo-line{padding:10px 0;border-bottom:1px solid var(--border)}.abo-line span{display:flex;gap:7px}.ok{color:var(--success-700)}.warn{color:var(--warning-700)}.hla-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:16px 0}.hla-locus{display:grid;grid-template-columns:1fr auto;gap:2px 10px;padding:10px;border-radius:var(--radius-md);background:var(--surface-muted)}.hla-locus span{font-weight:800}.hla-locus small{color:var(--text-3);font-weight:400}.hla-locus strong{direction:ltr}.hla-locus em{grid-column:1/-1;font-style:normal;font-size:12px;color:var(--text-2);direction:ltr;text-align:right}.hla-total{padding:11px;border-radius:var(--radius-md);background:#eff6ff;color:var(--info-700);font-weight:700}.warning-list{display:flex;flex-direction:column;gap:7px;margin-top:12px}.warning-list div{display:flex;gap:7px;padding:9px;border-radius:var(--radius-md);background:#fffbeb;color:var(--warning-700)}.score-details{margin-top:14px}.score-details summary{cursor:pointer;font-weight:700}.score-components{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.score-components span{padding:8px;background:var(--surface-muted);border-radius:8px;font-size:12px}.score-components b{display:block;font-size:16px}.decision-note{margin-top:16px}.danger-text{color:var(--error-700)}.decision-state{margin-top:16px;padding:10px;background:var(--surface-muted);border-radius:var(--radius-md)}.transparency-card{margin-top:0}.preview-controls select{flex:1}.preview-result{margin-top:14px;padding:12px;border-radius:var(--radius-md)}.preview-result div{display:flex;gap:7px;margin-top:6px}.empty-state{padding:35px;text-align:center;border:2px dashed var(--border);border-radius:var(--radius-lg);color:var(--text-2)}.empty-state i{display:block;font-size:34px;color:var(--text-3)}@media(max-width:950px){.matching-layout{grid-template-columns:1fr}.stats-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:600px){.stats-grid,.score-components{grid-template-columns:1fr}.proposal-row{grid-template-columns:30px 1fr auto}.proposal-row .score{display:none}}
</style>
