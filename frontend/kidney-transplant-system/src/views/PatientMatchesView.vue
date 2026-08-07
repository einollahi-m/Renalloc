<template>
  <div class="patient-page">
    <div class="page-header">
      <div>
        <div class="page-title">پورتال پیشنهادهای بیمار</div>
        <div class="page-subtitle">نمای ساده و ناشناس؛ تصمیم‌گیری و Cross-Match فقط با تأیید پزشک و مرکز</div>
      </div>
    </div>
    <div v-if="error" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ error }}</div>
    <section class="card selector-card">
      <label class="form-label">پرونده گیرنده</label>
      <select v-model="recipientId" class="form-input" @change="loadMatches">
        <option value="">انتخاب گیرنده</option>
        <option v-for="item in recipients" :key="item._id" :value="item._id">{{ item.fullName }} — {{ item.statusDisplay }}</option>
      </select>
    </section>
    <div v-if="disclaimer" class="patient-disclaimer"><i class="ri-information-line"></i>{{ disclaimer }}</div>
    <div v-if="loading" class="card loading-state"><i class="ri-loader-4-line"></i> در حال دریافت پیشنهادها…</div>
    <div v-else-if="recipientId && !matches.length" class="card empty-state">
      <i class="ri-heart-search-line"></i><h3>پیشنهاد فعالی وجود ندارد</h3><p>مرکز درمانی پس از تکمیل بررسی‌ها Matching را اجرا می‌کند.</p>
    </div>
    <div v-else class="patient-grid">
      <article v-for="item in paginatedMatches" :key="item.id" class="patient-match-card">
        <div class="card-head">
          <div class="anonymous-avatar"><i class="ri-shield-user-line"></i></div>
          <div><h3>اهداکننده {{ item.donor.anonymous_code }}</h3><span>هویت اهداکننده محرمانه است</span></div>
          <span class="status" :class="item.compatibility" :title="buildSimpleHlaTooltip(item.hla_similarity)">{{ item.compatibility_display }}</span>
        </div>
        <div class="simple-facts">
          <div><i class="ri-drop-line"></i><span>گروه خونی</span><strong>{{ item.donor.blood_group }} — سازگار</strong></div>
          <div><i class="ri-shield-check-line"></i><span>سازگاری ایمنی</span><strong>{{ item.immune_summary }}</strong></div>
          <div><i class="ri-dna-line"></i><span>شباهت HLA</span><strong :title="buildSimpleHlaTooltip(item.hla_similarity)">{{ item.hla_similarity.matches }} از {{ item.hla_similarity.maximum }} آلل</strong><div v-if="similarityChips(item.hla_summary).length" class="similarity-row"><span v-for="chip in similarityChips(item.hla_summary)" :key="chip.key" class="similarity-chip" :title="chip.title">{{ chip.label }}</span></div></div>
          <div><i class="ri-checkbox-circle-line"></i><span>وضعیت</span><strong>{{ item.donor.status_display }}</strong></div>
        </div>
        <div class="crossmatch-note"><i class="ri-test-tube-line"></i>پیش از هر اقدام، Cross-Match فیزیکی الزامی است.</div>
        <div v-if="item.warnings.length" class="conditional-note"><i class="ri-alert-line"></i>{{ item.warnings[0].message }}</div>
        <button class="btn btn-primary full" :disabled="requesting === item.id || !item.can_request_consultation" @click="consult(item)">
          <i class="ri-user-voice-line"></i>{{ item.can_request_consultation ? 'درخواست مشاوره با پزشک' : (item.consultation?.status_display || item.decision_display) }}
        </button>
      </article>
      <pagination-controls :pagination="paginationState" @change="changePage" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { registryApi } from '../services/api'
import PaginationControls from '../components/PaginationControls.vue'
import { buildLocalPagination, buildSimpleHlaTooltip, buildSimilarityChips, getPageSlice } from '../utils/matching'

const route = useRoute()
const recipients = ref([])
const recipientId = ref(String(route.query.recipient || ''))
const matches = ref([])
const disclaimer = ref('')
const loading = ref(false)
const requesting = ref('')
const error = ref('')
const currentPage = ref(1)
const pageSize = 4
const paginatedMatches = computed(() => getPageSlice(matches.value, currentPage.value, pageSize))
const paginationState = computed(() => buildLocalPagination(matches.value.length, currentPage.value, pageSize))
const similarityChips = summary => buildSimilarityChips(summary)

const loadMatches = async () => {
  matches.value = []; disclaimer.value = ''; error.value = ''
  currentPage.value = 1
  if (!recipientId.value) return
  loading.value = true
  try {
    const response = await registryApi.getPatientMatches(recipientId.value)
    matches.value = response.matches
    disclaimer.value = response.disclaimer
  } catch (e) { error.value = e.message } finally { loading.value = false }
}
const changePage = page => { currentPage.value = Math.min(Math.max(1, page), paginationState.value.pages) }

const consult = async item => {
  const note = window.prompt('در صورت تمایل، پرسش یا توضیح کوتاهی برای پزشک بنویسید:', '')
  if (note === null) return
  requesting.value = item.id; error.value = ''
  try {
    const response = await registryApi.requestConsultation(item.id, note)
    item.can_request_consultation = false
    item.consultation = { status: 'consultation_requested', status_display: 'درخواست مشاوره ثبت شد' }
    window.toast.add({ severity: 'success', summary: 'درخواست مشاوره', detail: response.message })
  } catch (e) { error.value = e.message } finally { requesting.value = '' }
}

onMounted(async () => {
  try {
    recipients.value = (await registryApi.listRecipients({page_size:100})).recipients
    if (recipientId.value) await loadMatches()
  } catch (e) { error.value = e.message }
})
</script>

<style scoped>
.page-header{margin-bottom:20px}.page-title{font-size:23px;font-weight:900}.page-subtitle{color:var(--text-2);font-size:13px}.card,.patient-match-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px;box-shadow:var(--shadow-1)}.selector-card{margin-bottom:14px}.selector-card select{max-width:650px}.patient-disclaimer,.crossmatch-note,.conditional-note{display:flex;align-items:flex-start;gap:8px;padding:11px 13px;border-radius:var(--radius-md);margin-bottom:14px}.patient-disclaimer{background:#eff6ff;color:var(--info-700)}.patient-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.card-head{display:grid;grid-template-columns:46px 1fr auto;align-items:center;gap:11px;margin-bottom:16px}.anonymous-avatar{width:46px;height:46px;display:grid;place-items:center;border-radius:13px;background:var(--color-primary-soft);color:var(--color-primary-dark);font-size:24px}.card-head h3{margin:0}.card-head span{font-size:11px;color:var(--text-3)}.status{padding:4px 9px;border-radius:999px;font-weight:800!important}.status.compatible{background:#ecfdf5;color:var(--success-700)}.status.conditional{background:#fffbeb;color:var(--warning-700)}.simple-facts{display:grid;gap:8px;margin-bottom:14px}.simple-facts div{display:grid;grid-template-columns:24px 1fr auto;gap:7px;padding:10px;background:var(--surface-muted);border-radius:var(--radius-md)}.simple-facts i{color:var(--color-primary);font-size:18px}.simple-facts span{color:var(--text-2)}.crossmatch-note{background:#eff6ff;color:var(--info-700)}.conditional-note{background:#fffbeb;color:var(--warning-700)}.full{width:100%;justify-content:center}.loading-state,.empty-state{text-align:center}.loading-state i{display:inline-block;animation:spin 1s linear infinite}.empty-state i{font-size:40px;color:var(--text-3)}.similarity-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.similarity-chip{display:inline-flex;align-items:center;padding:3px 10px;border:1px solid #ef4444;border-radius:999px;background:#fff7f7;color:#dc2626;font-size:11px;font-weight:800;cursor:help}@media(max-width:800px){.patient-grid{grid-template-columns:1fr}}
</style>
