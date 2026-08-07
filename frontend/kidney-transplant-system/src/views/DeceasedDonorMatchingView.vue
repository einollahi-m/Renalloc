<template>
  <div class="deceased-page">
    <div class="page-header">
      <div>
        <div class="page-title">سازگاری‌سنجی اهداکننده جسد</div>
        <div class="page-subtitle">رتبه‌بندی سریع گیرندگان فعال متقاضی کلیه از اهداکننده جسد</div>
      </div>
      <button v-if="results.length" class="btn btn-secondary" @click="exportExcel">
        <i class="ri-file-excel-2-line"></i> خروجی Excel
      </button>
    </div>
    <div class="clinical-banner"><i class="ri-alarm-warning-line"></i><div><strong>ابزار پشتیبان تصمیم بالینی</strong><span>تنها گیرندگان فعال، هم‌تابعیت و دارای درخواست اهداکننده جسد بررسی می‌شوند. تأیید آزمایشگاه و Cross-Match فیزیکی الزامی است.</span></div></div>
    <section class="form-card donor-input-card">
      <div class="form-card-title"><i class="ri-heart-add-line"></i> اطلاعات اهداکننده جسد</div>
      <div class="base-grid"><div class="form-group"><label class="form-label">تابعیت *</label><select v-model="form.citizenship" class="form-input"><option value="iranian">ایرانی</option><option value="foreign">غیر ایرانی</option></select></div><div class="form-group"><label class="form-label">گروه خونی *</label><select v-model="form.blood_group" class="form-input"><option value="">انتخاب کنید</option><option v-for="group in bloodGroupOptions" :key="group" :value="group">{{ group }}</option></select></div><div class="form-group"><label class="form-label">تعداد نتایج</label><select v-model.number="form.top_n" class="form-input"><option :value="10">۱۰</option><option :value="25">۲۵</option><option :value="50">۵۰</option><option :value="100">۱۰۰</option></select></div></div>
      <div class="hla-grid"><div v-for="field in fields" :key="field.key" class="form-group"><label class="form-label">{{ field.label }}</label><checkbox-multi-select v-model="form[field.key]" :options="field.options" :max-selected="2" :max-chips="2" :ltr="true" placeholder="حداکثر دو آلل"></checkbox-multi-select></div></div>
      <div class="run-row"><span>نتایج بر اساس HLA، زمان انتظار، فوریت، CDC-PRA، سن و محرومیت منطقه‌ای امتیازدهی می‌شوند.</span><button class="btn btn-primary btn-lg" :disabled="loading||!canRun" @click="run"><i :class="loading?'ri-loader-4-line spin':'ri-flashlight-line'"></i>{{ loading?'در حال محاسبه…':'محاسبه بهترین تطابق‌ها' }}</button></div>
    </section>
    <div v-if="error" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ error }}</div>
    <div v-if="statistics" class="stats-grid"><div><small>زمان پاسخ</small><strong>{{ toFa(statistics.elapsed_ms) }} ms</strong></div><div><small>افراد ارزیابی‌شده</small><strong>{{ toFa(statistics.evaluated_candidates) }}</strong></div><div><small>ردشده ایمنی</small><strong>{{ toFa(statistics.rejected_candidates) }}</strong></div><div><small>نسخه سیاست</small><strong>v{{ toFa(statistics.policy_version) }}</strong></div></div>
    <section v-if="results.length" class="form-card results-card">
      <div class="results-heading">
        <div class="form-card-title"><i class="ri-trophy-line"></i> بهترین گیرندگان</div>
        <span>{{ toFa(results.length) }} نتیجه</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>رتبه</th>
              <th>گیرنده</th>
              <th>خون/تابعیت</th>
              <th>زمان انتظار</th>
              <th>فوریت</th>
              <th>CDC-PRA</th>
              <th>HLA</th>
              <th>Anti-HLA / CREG</th>
              <th>امتیاز</th>
              <th>پرونده</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in paginatedResults" :key="item.rank">
              <td><span class="rank">{{ toFa(item.rank) }}</span></td>
              <td>
                <strong>{{ item.recipient.full_name || item.recipient.anonymous_code }}</strong>
                <small>{{ item.recipient.center || 'مرکز نامشخص' }}</small>
              </td>
              <td>
                <span dir="ltr">{{ item.recipient.blood_group }}</span>
                <small>{{ item.recipient.citizenship === 'iranian' ? 'ایرانی' : 'غیر ایرانی' }}</small>
              </td>
              <td>{{ toFa(item.waiting_days) }} روز</td>
              <td>{{ toFa(item.medical_urgency) }}</td>
              <td>{{ toFa(item.cdc_pra ?? item.cpra) }}٪</td>
              <td>
                <span class="tooltip-anchor" :title="buildHlaTooltip(item.hla_summary)">
                  {{ toFa(item.hla_summary?.total_matches || 0) }}/{{ toFa(10) }}
                </span>
                <div v-if="similarityChips(item.hla_summary).length" class="similarity-row">
                  <span v-for="chip in similarityChips(item.hla_summary)" :key="chip.key" class="similarity-chip" :title="chip.title">{{ chip.label }}</span>
                </div>
              </td>
              <td>
                <span class="tooltip-anchor" :class="['badge', immuneTone(item)]" :title="buildImmuneTooltip(item)">
                  {{ immuneLabel(item) }}
                </span>
                <small v-if="item.creg_summary?.active_groups?.length">{{ item.creg_summary.active_groups.join('، ') }}</small>
              </td>
              <td><strong class="score">{{ toFa(Math.round(item.final_score)) }}</strong></td>
              <td>
                <button v-if="item.recipient.can_view_profile" class="icon-btn" @click="$router.push(`/recipients/${item.recipient.id}`)">
                  <i class="ri-eye-line"></i>
                </button>
                <span v-else>—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <pagination-controls :pagination="paginationState" @change="changePage" />
    </section>
    <div v-else-if="statistics&&!loading" class="empty-state"><i class="ri-user-search-line"></i><h3>گیرنده سازگاری یافت نشد</h3><p>تابعیت، گروه خونی، HLA و اعتبار آزمایش‌های گیرندگان بررسی شد.</p></div>
  </div>
</template>
<script setup>
import { computed, reactive, ref } from 'vue'
import CheckboxMultiSelect from '../components/CheckboxMultiSelect.vue'
import PaginationControls from '../components/PaginationControls.vue'
import { hlaOptions } from '../data/hlaOptions'
import { bloodGroupOptions } from '../data/options'
import { registryApi } from '../services/api'
import { toFaDigits } from '../utils/date'
import { exportExcelTable } from '../utils/excel'
import { buildHlaTooltip, buildImmuneTooltip, buildLocalPagination, buildSimilarityChips, getPageSlice, joinReasonMessages } from '../utils/matching'

const toFa = toFaDigits
const loading = ref(false)
const error = ref('')
const results = ref([])
const statistics = ref(null)
const currentPage = ref(1)
const pageSize = 10
const form=reactive({citizenship:'iranian',blood_group:'',top_n:25,hla_a:[],hla_b:[],hla_c:[],hla_drb1:[],hla_dqb1:[],hla_drb:[]})
const fields=[{key:'hla_a',label:'HLA-A',options:hlaOptions.hlaA},{key:'hla_b',label:'HLA-B',options:hlaOptions.hlaB},{key:'hla_c',label:'HLA-C',options:hlaOptions.hlaC},{key:'hla_drb1',label:'HLA-DRB1',options:hlaOptions.hlaDRB1},{key:'hla_dqb1',label:'HLA-DQB1',options:hlaOptions.hlaDQB1},{key:'hla_drb',label:'HLA-DRB3/4/5',options:hlaOptions.hlaDRB}]
const canRun=computed(()=>form.blood_group&&fields.some(field=>form[field.key].length))
const paginatedResults = computed(() => getPageSlice(results.value, currentPage.value, pageSize))
const paginationState = computed(() => buildLocalPagination(results.value.length, currentPage.value, pageSize))
const similarityChips = summary => buildSimilarityChips(summary)
async function run(){loading.value=true;error.value='';results.value=[];statistics.value=null;currentPage.value=1;try{const response=await registryApi.matchDeceasedDonor({...form});results.value=response.matches;statistics.value=response.statistics;window.toast?.add({severity:'success',summary:'Matching',detail:`${response.matches.length} گیرنده برتر آماده شد`})}catch(err){error.value=err.message}finally{loading.value=false}}
const immuneTone=item=>item.anti_hla_status==='mismatch'||item.anti_hla_status==='insufficient-data'?'badge-danger':item.creg_summary?.has_potential_conflict?'badge-warning':'badge-success'
const immuneLabel=item=>item.anti_hla_status==='mismatch'?'تعارض مستقیم':item.anti_hla_status==='insufficient-data'?'اطلاعات ناکافی':item.creg_summary?.has_potential_conflict?'CREG بالقوه':'بدون تعارض'
function exportExcel(){const headers=['رتبه','گیرنده','مرکز','گروه خونی','تابعیت','روز انتظار','فوریت','CDC-PRA','تطابق HLA','جزئیات HLA','وضعیت Anti-HLA/CREG','دلایل/هشدارها','امتیاز'];const rows=results.value.map(item=>[item.rank,item.recipient.full_name||item.recipient.anonymous_code,item.recipient.center,item.recipient.blood_group,item.recipient.citizenship,item.waiting_days,item.medical_urgency,item.cdc_pra ?? item.cpra,`${item.hla_summary.total_matches}/10`,buildHlaTooltip(item.hla_summary),buildImmuneTooltip(item),joinReasonMessages([...(item.rejection_reasons||[]),...(item.warnings||[])]),item.final_score]);exportExcelTable(`deceased-donor-matches-${new Date().toISOString().slice(0,10)}.xls`,'سازگاری‌ها',headers,rows)}
const changePage=page=>{currentPage.value=Math.min(Math.max(1,page),paginationState.value.pages)}
</script>
<style scoped>
.deceased-page{display:grid;gap:16px}.clinical-banner{display:flex;gap:10px;padding:14px;border:1px solid #f59e0b;background:#fffbeb;color:#92400e;border-radius:var(--radius-lg)}.clinical-banner i{font-size:24px}.clinical-banner span{display:block;margin-top:3px;font-size:12px}.donor-input-card{display:grid;gap:16px}.base-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.hla-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.run-row,.results-heading{display:flex;justify-content:space-between;align-items:center;gap:14px}.run-row span{color:var(--text-2);font-size:12px}.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.stats-grid>div{padding:14px;border:1px solid var(--border);background:var(--surface);border-radius:var(--radius-md)}.stats-grid small,.stats-grid strong{display:block}.stats-grid small{color:var(--text-2)}.stats-grid strong{font-size:20px;margin-top:4px}.results-card{display:grid;gap:12px}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;white-space:nowrap}th,td{padding:11px;border-bottom:1px solid var(--border);text-align:right}th{font-size:11px;color:var(--text-2);background:var(--surface-muted)}td small{display:block;color:var(--text-2);margin-top:3px}.rank{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--color-primary-soft);color:var(--color-primary);font-weight:800}.score{font-size:19px;color:var(--color-primary)}.tooltip-anchor{cursor:help}.similarity-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.similarity-chip{display:inline-flex;align-items:center;padding:3px 10px;border:1px solid #ef4444;border-radius:999px;background:#fff7f7;color:#dc2626;font-size:11px;font-weight:800;cursor:help}.spin{animation:spin 1s linear infinite}@media(max-width:800px){.base-grid,.hla-grid,.stats-grid{grid-template-columns:repeat(2,1fr)}.run-row{align-items:stretch;flex-direction:column}.run-row .btn{width:100%}}@media(max-width:520px){.base-grid,.hla-grid,.stats-grid{grid-template-columns:1fr}}
</style>
