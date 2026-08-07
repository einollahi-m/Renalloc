<template>
  <div v-if="loading" class="empty-state"><i class="ri-loader-4-line"></i><h3>در حال دریافت پرونده گیرنده…</h3></div>
  <div v-else-if="loadError" class="empty-state"><i class="ri-error-warning-line"></i><h3>{{ loadError }}</h3><button class="btn btn-secondary mt-3" @click="loadRecipient">تلاش دوباره</button></div>
  <div v-else class="profile-page">
    <div class="page-header">
      <div><div class="page-title">پرونده گیرنده</div><div class="page-subtitle">اطلاعات بالینی، اولویت، وضعیت و سازگاری‌سنجی در یک نمای واحد</div></div>
      <button class="btn btn-secondary" @click="$router.push('/recipients')"><i class="ri-arrow-right-line"></i> بازگشت</button>
    </div>

    <section class="profile-hero">
      <div class="profile-avatar gender-avatar" :aria-label="detail.person.gender==='female'?'خانم':'آقا'">{{ detail.person.gender==='female'?'🧕':'👨' }}</div>
      <div class="hero-identity">
        <div class="hero-title-row"><h2>{{ r.fullName }}</h2><span :class="['status-pill', statusTone(r.status)]">{{ r.statusDisplay }}</span></div>
        <div class="profile-meta">
          <span><i class="ri-profile-line"></i> {{ toFa(r.nationalId) }}</span>
          <span><i class="ri-calendar-line"></i> {{ calculateAge(r.birthDate) }} سال</span>
          <span><i class="ri-drop-line"></i> {{ bloodGroup }}</span>
          <span><i class="ri-hospital-line"></i> {{ detail.person.center?.name || 'بدون مرکز' }}</span>
        </div>
      </div>
      <div class="hero-stats">
        <div><small>اولویت بالینی</small><strong>{{ priorityLabel }}</strong><span>{{ toFa(priorityTotal) }} امتیاز</span></div>
        <div><small>آخرین CDC-PRA</small><strong>{{ (r.cdc_pra ?? r.cpra) == null ? '—' : `${toFa(r.cdc_pra ?? r.cpra)}٪` }}</strong><span>{{ latestCdc ? formatFaDate(latestCdc.performed_at) : 'ثبت نشده' }}</span></div>
        <div><small>عضویت در انتظار</small><strong>{{ waitingDays == null ? '—' : `${toFa(waitingDays)} روز` }}</strong><span>{{ r.waitingSince ? formatFaDate(r.waitingSince) : 'ثبت نشده' }}</span></div>
      </div>
      <div class="hero-actions">
        <button v-if="canManage && r.allowedTransitions?.includes('active')" class="btn btn-primary" @click="addToWaiting"><i class="ri-list-check-2"></i> افزودن به لیست انتظار</button>
        <button v-if="canManage && r.allowedTransitions?.includes('temporarily_inactive')" class="btn btn-secondary" @click="leaveWaiting"><i class="ri-pause-circle-line"></i> خروج موقت از لیست</button>
        <button v-if="canManage" class="btn btn-primary" :disabled="!r.allowedTransitions?.length" @click="openStatusModal"><i class="ri-arrow-left-right-line"></i> تغییر وضعیت</button>
        <button v-if="canManage" class="btn btn-secondary" @click="openPriorityModal"><i class="ri-scales-3-line"></i> ویرایش اولویت</button>
      </div>
    </section>

    <div v-if="antiExpiryAlert" :class="['alert', antiExpiryAlert.expired ? 'alert-danger' : 'alert-warning']">
      <i class="ri-alarm-warning-line"></i>
      <div><strong>{{ antiExpiryAlert.expired ? 'آزمایش Anti-HLA منقضی شده است' : 'اعتبار Anti-HLA رو به پایان است' }}</strong><div>{{ antiExpiryAlert.message }}</div></div>
    </div>

    <div class="tabs profile-tabs">
      <button v-for="tab in tabs" :key="tab.key" class="tab" :class="{active:activeTab===tab.key}" @click="selectTab(tab.key)"><i :class="tab.icon"></i> {{ tab.label }}<span v-if="tab.key==='matches' && matches.length" class="tab-count">{{ toFa(matches.length) }}</span></button>
    </div>

    <div v-if="activeTab==='overview'" class="overview-stack">
      <div v-if="detail.immune_alerts?.hla_anti_hla_overlaps?.length" class="alert alert-danger">
        <i class="ri-error-warning-line"></i>
        <div><strong>هم‌پوشانی HLA و Anti-HLA در پرونده</strong><div>آنتی‌ژن‌های {{ detail.immune_alerts.hla_anti_hla_overlaps.join('، ') }} هم‌زمان در HLA و Anti-HLA ثبت شده‌اند؛ پیش از تصمیم بالینی بازبینی شود.</div></div>
      </div>
      <div class="grid grid-3">
        <article class="summary-card"><i class="ri-kidney-line"></i><div><small>سابقه دیالیز</small><strong>{{ yesNo(detail.profile.has_dialysis_history) }}</strong><span>{{ dialysisLabel }}</span></div></article>
        <article class="summary-card"><i class="ri-dna-line"></i><div><small>تایپ HLA</small><strong>{{ hlaSelectionCount ? `${toFa(hlaSelectionCount)} آلل` : 'ثبت نشده' }}</strong><span>{{ detail.hla ? `به‌روزرسانی ${formatFaDate(detail.hla.updated_at)}` : 'نیازمند تکمیل' }}</span></div></article>
        <article class="summary-card"><i class="ri-checkbox-circle-line"></i><div><small>تأییدیه‌های پزشکی</small><strong>{{ toFa(approvedCount) }} از {{ toFa(detail.approvals.length) }}</strong><span>{{ detail.approvals.length ? 'تأییدیه ثبت‌شده' : 'بدون تأییدیه' }}</span></div></article>
      </div>
      <section class="form-card">
        <div class="form-card-title"><i class="ri-stethoscope-line"></i> جمع‌بندی پزشکی</div>
        <div class="info-grid">
          <div><small>نوبت پیوند</small><strong>{{ transplantCandidateLabel }}</strong></div><div><small>منبع اهدا</small><strong>{{ donorSourceLabel }}</strong></div>
          <div><small>تزریق خون</small><strong>{{ yesNo(detail.profile.has_blood_transfusion) }}</strong></div><div><small>پیوند قبلی</small><strong>{{ yesNo(detail.profile.previous_transplant) }}</strong></div>
          <div><small>حساسیت دارویی</small><strong>{{ yesNo(detail.profile.has_drug_allergy) }}</strong></div><div><small>سابقه خانوادگی کلیوی</small><strong>{{ yesNo(detail.profile.family_kidney_disease) }}</strong></div>
        </div>
      </section>
    </div>

    <section v-else-if="activeTab==='personal'" class="form-card">
      <div class="section-heading"><div class="form-card-title"><i class="ri-user-line"></i> اطلاعات فردی و تماس</div><button class="btn btn-primary btn-sm" @click="showPersonModal=true"><i class="ri-edit-line"></i> ویرایش اطلاعات مجاز</button></div>
      <div class="info-grid">
        <div><small>نام و نام خانوادگی</small><strong>{{ detail.person.full_name }}</strong></div><div><small>کد ملی / شناسه</small><strong>{{ toFa(detail.person.identifier) }}</strong></div>
        <div><small>تاریخ تولد</small><strong>{{ formatFaDate(detail.person.birth_date) }}</strong></div><div><small>جنسیت</small><strong>{{ detail.person.gender==='male' ? 'مرد' : 'زن' }}</strong></div>
        <div><small>شماره همراه</small><strong>{{ toFa(detail.person.phone) }}</strong></div><div><small>تماس اضطراری</small><strong>{{ toFa(detail.person.emergency_contact_phone || '—') }}</strong></div>
        <div><small>قد</small><strong>{{ detail.person.height_cm ? `${measurement(detail.person.height_cm)} سانتی‌متر` : '—' }}</strong></div><div><small>وزن</small><strong>{{ detail.person.weight_kg ? `${measurement(detail.person.weight_kg)} کیلوگرم` : '—' }}</strong></div>
      </div>
    </section>

    <div v-else-if="activeTab==='immunology'" class="section-stack">
      <section class="form-card">
        <div class="section-heading"><div class="form-card-title"><i class="ri-dna-line"></i> تایپ HLA</div><button class="btn btn-primary btn-sm" @click="showHlaModal=true"><i :class="detail.hla?'ri-edit-line':'ri-add-line'"></i> {{ detail.hla ? 'ویرایش' : 'افزودن' }}</button></div>
        <div v-if="detail.hla" class="hla-grid"><div v-for="field in hlaFields" :key="field.key" class="hla-item"><strong>{{ field.label }}</strong><div class="tag-row"><span v-for="(allele,index) in detail.hla[field.key]" :key="`${allele}-${index}`" class="badge badge-info">{{ allele }}</span><span v-if="!detail.hla[field.key]?.length">—</span></div></div></div>
        <div v-else class="compact-empty-state empty-state"><i class="ri-dna-line"></i><h3>تایپ HLA ثبت نشده است</h3></div>
      </section>
      <section class="form-card">
        <div class="section-heading"><div class="form-card-title"><i class="ri-shield-check-line"></i> سوابق CDC PRA</div><button class="btn btn-primary btn-sm" @click="openCdcCreate"><i class="ri-add-line"></i> آزمایش جدید</button></div>
        <div v-if="detail.cdc_pra_tests.length" class="record-list"><article v-for="test in detail.cdc_pra_tests" :key="test.id" class="record-card"><div><strong>{{ formatFaDate(test.performed_at) }}</strong><small>معتبر تا {{ formatFaDate(test.expires_at) }}</small></div><div class="tag-row"><span :class="['badge',test.class_i.status==='positive'?'badge-warning':'badge-success']">Class I: {{ statusLabel(test.class_i.status) }}<template v-if="test.class_i.value!=null">، {{ toFa(test.class_i.value) }}٪</template></span><span :class="['badge',test.class_ii.status==='positive'?'badge-warning':'badge-success']">Class II: {{ statusLabel(test.class_ii.status) }}<template v-if="test.class_ii.value!=null">، {{ toFa(test.class_ii.value) }}٪</template></span><span v-if="test.is_expired" class="badge badge-danger">منقضی</span></div><button class="icon-btn" @click="openCdcEdit(test)"><i class="ri-edit-line"></i></button></article></div>
        <div v-else class="compact-empty-state empty-state"><i class="ri-shield-check-line"></i><h3>آزمایش CDC PRA ثبت نشده است</h3></div>
      </section>
      <section class="form-card">
        <div class="section-heading"><div class="form-card-title"><i class="ri-test-tube-line"></i> سوابق Anti-HLA</div><button class="btn btn-primary btn-sm" @click="openAntiCreate"><i class="ri-add-line"></i> آزمایش جدید</button></div>
        <div v-if="detail.anti_hla_tests.length" class="record-list"><article v-for="test in detail.anti_hla_tests" :key="test.id" class="record-card"><div><strong>{{ formatFaDate(test.performed_at) }}</strong><small>معتبر تا {{ formatFaDate(test.expires_at) }}</small></div><div class="tag-row"><span v-for="item in test.selections" :key="item.id" class="badge badge-info">{{ item.antigen }}</span><span v-if="test.class_i_negative" class="badge badge-success">Class I · None</span><span v-if="test.class_ii_negative" class="badge badge-success">Class II · None</span><span v-if="test.is_expired" class="badge badge-danger">منقضی</span></div><button class="icon-btn" @click="openAntiEdit(test)"><i class="ri-edit-line"></i></button></article></div>
        <div v-else class="compact-empty-state empty-state"><i class="ri-test-tube-line"></i><h3>آزمایش Anti-HLA ثبت نشده است</h3></div>
      </section>
      <creg-table v-if="detail.immune_alerts?.has_anti_hla" :rows="detail.immune_alerts.creg_table" />
    </div>

    <lab-tests-panel v-else-if="activeTab==='labs'" :person-id="detail.person.id" :gender="detail.person.gender" :lab-tests="detail.lab_tests" @refresh="loadRecipient" />

    <approval-panel v-else-if="activeTab==='approvals'" :person-id="detail.person.id" role="recipient" :approvals="detail.approvals" @refresh="loadRecipient" />

    <div v-else-if="activeTab==='matches'" class="section-stack">
      <temporary-hla-matcher :recipient="detail" />
      <section class="form-card matching-accordion">
      <div class="accordion-result-heading" @click="serverMatchesOpen=!serverMatchesOpen"><div><div class="form-card-title"><i class="ri-exchange-2-line"></i> اهداکنندگان بررسی‌شده <span class="badge badge-info">{{ toFa(matches.length) }}</span></div><p class="section-hint">نتایج بر پایه گروه خونی، HLA، Anti-HLA و سیاست تخصیص فعال محاسبه می‌شوند.</p></div><div class="button-row" @click.stop><button v-if="matches.length" class="btn btn-secondary btn-sm" @click="exportMatches"><i class="ri-file-excel-2-line"></i> خروجی Excel</button><button class="btn btn-secondary btn-sm" :disabled="matchingLoading" @click="loadMatches"><i class="ri-refresh-line"></i> تازه‌سازی</button><button class="btn btn-primary btn-sm" :disabled="matchingLoading || r.status!=='active'" @click="enqueueMatching"><i :class="matchingLoading?'ri-loader-4-line':'ri-play-circle-line'"></i> اجرای سازگاری‌سنجی</button><button class="icon-btn" :title="serverMatchesOpen?'بستن':'باز کردن'" @click="serverMatchesOpen=!serverMatchesOpen"><i :class="serverMatchesOpen?'ri-arrow-up-s-line':'ri-arrow-down-s-line'"></i></button></div></div>
      <div v-show="serverMatchesOpen" class="accordion-result-content">
      <div v-if="matchingLoading" class="inline-loading"><i class="ri-loader-4-line"></i> در حال دریافت نتایج…</div>
      <template v-else-if="matches.length">
        <div class="match-list"><article v-for="match in paginatedMatches" :key="match.id" class="match-card"><div class="match-rank">{{ match.rank ? `#${toFa(match.rank)}` : '—' }}</div><div class="match-main"><strong>{{ donorCode(match) }}</strong><span>{{ match.donor.bloodType }}{{ match.donor.rhFactor==='positive'?'+':'-' }} · {{ match.donor.donorType==='living_related'?'زنده خویشاوند':'زنده غیرخویشاوند' }}</span><div class="tag-row"><span :class="['badge',compatibilityTone(match.compatibility)]" :title="buildCompatibilityTooltip(match)">{{ match.compatibility_display }}</span><span :class="['badge',match.abo_compatible?'badge-success':'badge-danger']">ABO {{ match.abo_compatible?'سازگار':'ناسازگار' }}</span><span class="badge badge-info tooltip-anchor" :title="buildHlaTooltip(match.hla_summary)">HLA {{ toFa(match.hla_summary?.total_matches || 0) }}/{{ toFa(10) }}</span><span v-if="match.creg_summary?.has_antibody" :class="['badge',match.creg_summary?.has_potential_conflict?'badge-warning':'badge-success']" :title="buildImmuneTooltip(match)">CREG {{ match.creg_summary?.has_potential_conflict?'بالقوه موجود':'یافت نشد' }}</span></div><div v-if="similarityChips(match.hla_summary).length" class="similarity-row"><span v-for="chip in similarityChips(match.hla_summary)" :key="chip.key" class="similarity-chip" :title="chip.title">{{ chip.label }}</span></div><small class="mismatch-line" :title="buildMismatchSummary(match.hla_summary)">{{ buildMismatchSummary(match.hla_summary) }}</small><small v-if="match.rejection_reasons?.length" class="text-danger">{{ reasonMessages(match.rejection_reasons) }}</small><small v-else-if="match.warnings?.length" class="text-warning">{{ reasonMessages(match.warnings) }}</small></div><div class="score-ring">{{ toFa(Math.round(match.final_score)) }}<small>امتیاز</small></div></article></div>
        <pagination-controls :pagination="matchPagination" @change="changeMatchPage" />
      </template>
      <div v-else class="compact-empty-state empty-state"><i class="ri-exchange-2-line"></i><h3>نتیجه‌ای ثبت نشده است</h3><p>برای گیرنده فعال، سازگاری‌سنجی را اجرا کنید.</p></div>
      </div>
      </section>
    </div>

    <section v-else-if="activeTab==='status'" class="status-layout">
      <div class="form-card status-current"><div class="form-card-title"><i class="ri-pulse-line"></i> وضعیت فعلی</div><span :class="['status-pill large',statusTone(r.status)]">{{ r.statusDisplay }}</span><p>آخرین تغییر: {{ latestEvent ? formatFaDateTime(latestEvent.created_at) : 'ثبت نشده' }}</p><div class="workflow-help">ورود به صف با وضعیت «فعال در لیست انتظار» و خروج موقت با «غیرفعال موقت» انجام می‌شود. هر تغییر نیازمند ثبت دلیل است.</div><button v-if="canManage" class="btn btn-primary" :disabled="!r.allowedTransitions?.length" @click="openStatusModal">تغییر وضعیت</button></div>
      <div class="form-card"><div class="form-card-title"><i class="ri-road-map-line"></i> وضعیت و اولویت</div><div class="tag-row"><span v-for="status in r.allowedTransitions" :key="status" class="badge badge-info">{{ recipientStatusLabels[status] || status }}</span><span v-if="!r.allowedTransitions?.length" class="text-secondary">گذار بعدی برای این وضعیت تعریف نشده است.</span></div><div class="priority-summary"><span>فوریت پزشکی: <b>{{ toFa(detail.profile.medical_urgency) }}</b> از ۱۰۰</span><span>شرایط اورژانسی: <b>{{ detail.profile.is_emergency?'بله':'خیر' }}</b></span><p v-if="detail.profile.emergency_reason">{{ detail.profile.emergency_reason }}</p></div><button v-if="canManage" class="btn btn-secondary" @click="openPriorityModal"><i class="ri-alarm-warning-line"></i> تنظیم اولویت و شرایط اورژانسی</button></div>
    </section>

    <section v-else-if="activeTab==='history'" class="form-card">
      <div class="form-card-title"><i class="ri-history-line"></i> تاریخچه تغییرات پرونده</div>
      <div v-if="detail.state_events.length" class="timeline"><article v-for="event in detail.state_events" :key="event.id"><span class="timeline-dot"></span><div><strong>{{ event.metadata?.kind==='priority_update'?'ویرایش اولویت و شرایط اورژانسی':`${event.previous_status ? `${recipientStatusLabels[event.previous_status] || event.previous_status} ← ` : ''}${recipientStatusLabels[event.new_status] || event.new_status}` }}</strong><p>{{ event.reason }}</p><small>{{ formatFaDateTime(event.created_at) }} · {{ event.actor }}</small></div></article></div>
      <div v-else class="compact-empty-state empty-state"><i class="ri-history-line"></i><h3>رویدادی ثبت نشده است</h3></div>
    </section>

    <hla-typing-modal v-model:visible="showHlaModal" :initial-value="detail.hla" @save="saveHla" />
    <cdc-pra-modal v-model:visible="showCdcModal" :test="editingCdcTest" :existing-tests="detail.cdc_pra_tests" @save="saveCdc" />
    <anti-hla-modal v-model:visible="showAntiModal" :edit-batch="editingAntiTest" @save="saveAnti" />
    <person-profile-edit-modal v-model:visible="showPersonModal" :person="detail.person" @save="savePersonProfile" />

    <div v-if="canManage && showStatusModal" class="modal-overlay" @click.self="showStatusModal=false"><div class="modal narrow"><div class="modal-header"><h3>تغییر وضعیت گیرنده</h3><button class="modal-close" @click="showStatusModal=false"><i class="ri-close-line"></i></button></div><div class="form-group"><label class="form-label">وضعیت بعدی</label><select v-model="nextStatus" class="form-input"><option value="">انتخاب کنید</option><option v-for="key in r.allowedTransitions" :key="key" :value="key">{{ recipientStatusLabels[key] || key }}</option></select></div><div class="form-group"><label class="form-label">دلیل تغییر</label><textarea v-model="statusReason" class="form-input" rows="4" placeholder="دلیل بالینی یا اجرایی تغییر وضعیت"></textarea></div><div class="modal-footer"><button class="btn btn-secondary" @click="showStatusModal=false">لغو</button><button class="btn btn-primary" :disabled="!nextStatus||!statusReason.trim()||saving" @click="saveStatus">ثبت رویداد</button></div></div></div>
    <div v-if="canManage && showPriorityModal" class="modal-overlay" @click.self="showPriorityModal=false"><div class="modal narrow"><div class="modal-header"><h3>ویرایش اولویت و شرایط اورژانسی</h3><button class="modal-close" @click="showPriorityModal=false"><i class="ri-close-line"></i></button></div><div class="alert alert-warning"><i class="ri-information-line"></i>امتیازها باید براساس مستندات بالینی ثبت شوند؛ تغییر آن‌ها Matching را دوباره در صف قرار می‌دهد.</div><div class="grid grid-2"><div class="form-group"><label class="form-label">فوریت پزشکی (۰ تا ۱۰۰)</label><input v-model.number="priorityForm.medical_urgency" class="form-input" type="number" min="0" max="100"></div><div class="form-group"><label class="form-label">محرومیت منطقه‌ای (۰ تا ۱۰۰)</label><input v-model.number="priorityForm.regional_disadvantage" class="form-input" type="number" min="0" max="100"></div></div><div class="form-group"><label class="form-label">تاریخ ورود به لیست انتظار</label><input v-model="priorityForm.waiting_since" class="form-input" type="date" dir="ltr"></div><label class="check-chip" :class="{checked:priorityForm.is_emergency}"><input v-model="priorityForm.is_emergency" type="checkbox"> دارای شرایط اورژانسی مستند</label><div v-if="priorityForm.is_emergency" class="form-group"><label class="form-label">شرح شرایط اورژانسی *</label><textarea v-model="priorityForm.emergency_reason" class="form-input" rows="4" placeholder="تشخیص، مستند بالینی و علت اولویت"></textarea></div><div class="modal-footer"><button class="btn btn-secondary" @click="showPriorityModal=false">لغو</button><button class="btn btn-primary" :disabled="saving||(priorityForm.is_emergency&&!priorityForm.emergency_reason.trim())" @click="savePriority">ذخیره اولویت</button></div></div></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { toFaDigits, formatFaDate } from '../utils/date'
import { registryApi } from '../services/api'
import { useAuth } from '../composables/useAuth'
import HlaTypingModal from '../components/HlaTypingModal.vue'
import CdcPraModal from '../components/CdcPraModal.vue'
import AntiHlaModal from '../components/AntiHlaModal.vue'
import PersonProfileEditModal from '../components/PersonProfileEditModal.vue'
import LabTestsPanel from '../components/LabTestsPanel.vue'
import ApprovalPanel from '../components/ApprovalPanel.vue'
import CregTable from '../components/CregTable.vue'
import TemporaryHlaMatcher from '../components/TemporaryHlaMatcher.vue'
import { exportExcelTable } from '../utils/excel'
import PaginationControls from '../components/PaginationControls.vue'
import { buildCompatibilityTooltip, buildHlaTooltip, buildImmuneTooltip, buildMismatchSummary, buildLocalPagination, buildSimilarityChips, getPageSlice, joinReasonMessages } from '../utils/matching'

const route = useRoute()
const { authState } = useAuth()
const detail = ref({ summary:{}, person:{}, profile:{}, hla:null, cdc_pra_tests:[], anti_hla_tests:[], lab_tests:[], approvals:[], state_events:[], immune_alerts:{} })
const matches = ref([]), loading = ref(true), matchingLoading = ref(false), saving = ref(false)
const serverMatchesOpen = ref(true)
const currentMatchPage = ref(1)
const matchPageSize = 6
const loadError = ref(''), activeTab = ref('overview')
const showHlaModal = ref(false), showCdcModal = ref(false), showAntiModal = ref(false), showPersonModal = ref(false), showStatusModal = ref(false), showPriorityModal = ref(false)
const editingCdcTest = ref(null), editingAntiTest = ref(null), nextStatus = ref(''), statusReason = ref('')
const priorityForm = ref({ medical_urgency:0, regional_disadvantage:0, waiting_since:'', is_emergency:false, emergency_reason:'' })
const toFa = toFaDigits
const r = computed(() => detail.value.summary)
const canManage = computed(() => authState.user?.can_manage_clinical_workflow === true)
const hlaFields = [{key:'hla_a',label:'HLA-A'},{key:'hla_b',label:'HLA-B'},{key:'hla_c',label:'HLA-C'},{key:'hla_drb1',label:'HLA-DRB1'},{key:'hla_dqb1',label:'HLA-DQB1'},{key:'hla_drb',label:'HLA-DRB3/4/5'}]
const tabs = [{key:'overview',label:'خلاصه پرونده',icon:'ri-dashboard-2-line'},{key:'personal',label:'اطلاعات فردی',icon:'ri-user-line'},{key:'immunology',label:'ایمونولوژی',icon:'ri-shield-check-line'},{key:'labs',label:'آزمایش‌ها',icon:'ri-flask-line'},{key:'approvals',label:'تأییدیه‌ها',icon:'ri-checkbox-circle-line'},{key:'matches',label:'سازگاری‌ها',icon:'ri-exchange-2-line'},{key:'status',label:'وضعیت',icon:'ri-pulse-line'},{key:'history',label:'تاریخچه',icon:'ri-history-line'}]
const recipientStatusLabels={registered:'ثبت‌نام اولیه',pending_documents:'در انتظار تأیید مدارک',rejected:'رد شده',active:'فعال در لیست انتظار',match_candidate:'کاندیدای تطبیق',awaiting_crossmatch:'در انتظار Cross-Match',awaiting_high_resolution:'در انتظار High-Resolution',ready:'آماده پیوند',transplanted:'پیوند انجام شد',follow_up:'پیگیری پس از پیوند',temporarily_inactive:'غیرفعال موقت',removed:'حذف از لیست انتظار'}
const bloodGroup = computed(() => `${r.value.bloodType || ''}${r.value.rhFactor==='positive'?'+':'-'}`)
const priorityTotal = computed(() => Number(detail.value.profile.medical_urgency || 0) + Number(detail.value.profile.regional_disadvantage || 0))
const priorityLabel = computed(() => priorityTotal.value >= 120 ? 'خیلی بالا' : priorityTotal.value >= 70 ? 'بالا' : priorityTotal.value >= 30 ? 'متوسط' : 'عادی')
const hlaSelectionCount = computed(() => detail.value.hla ? hlaFields.reduce((n,f)=>n+(detail.value.hla[f.key]?.length||0),0) : 0)
const approvedCount = computed(() => detail.value.approvals.filter(item=>item.status==='approved').length)
const latestCdc = computed(() => detail.value.cdc_pra_tests[0] || null)
const latestAnti = computed(() => detail.value.anti_hla_tests[0] || null)
const latestEvent = computed(() => detail.value.state_events[0] || null)
const paginatedMatches = computed(() => getPageSlice(matches.value, currentMatchPage.value, matchPageSize))
const matchPagination = computed(() => buildLocalPagination(matches.value.length, currentMatchPage.value, matchPageSize))
const similarityChips = summary => buildSimilarityChips(summary)
const waitingDays = computed(() => r.value.waitingSince ? Math.max(0,Math.floor((Date.now()-new Date(r.value.waitingSince).getTime())/86400000)) : null)
const dialysisLabel = computed(() => !detail.value.profile.has_dialysis_history ? 'بدون سابقه' : detail.value.profile.dialysis_type==='hemodialysis' ? 'همودیالیز' : 'دیالیز صفاقی')
const donorSourceLabel = computed(() => [detail.value.profile.donor_living?'زنده':'',detail.value.profile.donor_deceased?'فوت‌شده':''].filter(Boolean).join(' و ') || '—')
const transplantCandidateLabel = computed(() => ({'1st':'پیوند اول','2nd':'پیوند دوم','3rd':'پیوند سوم','4th':'پیوند چهارم'}[detail.value.profile.transplant_candidate] || '—'))
const antiExpiryAlert = computed(() => { if(!latestAnti.value) return {expired:false,message:'برای ورود امن به چرخه تطبیق، آزمایش Anti-HLA ثبت شود.'}; const days=Math.ceil((new Date(latestAnti.value.expires_at)-Date.now())/86400000); if(days<0)return{expired:true,message:`اعتبار این آزمایش ${toFa(Math.abs(days))} روز پیش پایان یافته است.`}; if(days<=14)return{expired:false,message:`تنها ${toFa(days)} روز از اعتبار این آزمایش باقی مانده است.`}; return null })

const yesNo = value => value ? 'بله' : 'خیر'
const measurement = value => toFa(Number(value).toString())
const statusLabel = value => value==='positive'?'مثبت':'منفی'
const calculateAge = date => date ? toFa(Math.max(0,new Date().getFullYear()-new Date(date).getFullYear())) : '—'
const formatFaDateTime = value => value ? `${formatFaDate(value)}، ${toFa(new Date(value).toLocaleTimeString('fa-IR',{hour:'2-digit',minute:'2-digit'}))}` : '—'
const statusTone = value => ['active','ready'].includes(value)?'is-success':['temporarily_inactive','pending_documents','awaiting_crossmatch','awaiting_high_resolution'].includes(value)?'is-warning':['rejected','removed'].includes(value)?'is-danger':'is-info'
const compatibilityTone = value => value==='compatible'?'badge-success':value==='conditional'?'badge-warning':'badge-danger'
const donorCode = match => `D-${String(match.donor._id).split('-')[0].toUpperCase()}`
const reasonMessages = items => items.map(item=>typeof item==='string'?item:item.message).join('، ')
const errorDetail = error => Object.values(error?.data?.errors || {}).flat()[0] || error?.message || 'عملیات انجام نشد'
const toast = (severity,summary,message) => window.toast?.add({severity,summary,detail:message})

async function loadRecipient(){loading.value=true;loadError.value='';try{const response=await registryApi.getRecipient(route.params.id);detail.value=response.recipient}catch(error){loadError.value=error?.message||'دریافت پرونده گیرنده انجام نشد'}finally{loading.value=false}}
async function loadMatches(){matchingLoading.value=true;try{const response=await registryApi.listMatchProposals({recipient_id:route.params.id});const seen=new Set();matches.value=response.proposals.filter(item=>{if(seen.has(item.donor._id))return false;seen.add(item.donor._id);return true});serverMatchesOpen.value=true;currentMatchPage.value=1}catch(error){toast('error','خطا',errorDetail(error))}finally{matchingLoading.value=false}}
function exportMatches(){const headers=['رتبه','کد اهداکننده','گروه خونی','نوع','وضعیت سازگاری','ABO','تطابق HLA','جزئیات HLA','Anti-HLA / CREG','دلایل/هشدارها','امتیاز'];const rows=matches.value.map(match=>[match.rank||'',donorCode(match),`${match.donor.bloodType}${match.donor.rhFactor==='positive'?'+':'-'}`,match.donor.donorType,match.compatibility_display,match.abo_compatible?'سازگار':'ناسازگار',`${match.hla_summary?.total_matches||0}/10`,buildHlaTooltip(match.hla_summary),buildImmuneTooltip(match),joinReasonMessages([...(match.rejection_reasons||[]),...(match.warnings||[])]),match.final_score]);exportExcelTable(`recipient-${route.params.id}-matches.xls`,'سازگاری‌ها',headers,rows)}
function selectTab(key){activeTab.value=key;if(key==='matches'&&!matches.value.length)loadMatches()}
async function enqueueMatching(){matchingLoading.value=true;try{const response=await registryApi.enqueueMatching({recipient_id:route.params.id});toast('success','در صف پردازش',response.message);await loadMatches();setTimeout(loadMatches,2500)}catch(error){toast('error','خطا',errorDetail(error));matchingLoading.value=false}}
async function saveHla(payload){try{await registryApi.saveHla(route.params.id,payload);toast('success','موفق','تایپ HLA ذخیره شد');await loadRecipient()}catch(error){toast('error','خطا',errorDetail(error))}}
function openCdcCreate(){editingCdcTest.value=null;showCdcModal.value=true} function openCdcEdit(test){editingCdcTest.value=test;showCdcModal.value=true}
async function saveCdc(payload){try{editingCdcTest.value?await registryApi.updateCdcPra(route.params.id,editingCdcTest.value.id,payload):await registryApi.createCdcPra(route.params.id,payload);toast('success','موفق','آزمایش CDC PRA ذخیره شد');await loadRecipient()}catch(error){toast('error','خطا',errorDetail(error))}}
function openAntiCreate(){editingAntiTest.value=null;showAntiModal.value=true} function openAntiEdit(test){editingAntiTest.value=test;showAntiModal.value=true}
async function saveAnti({testDate,records}){try{const payload={performed_at:testDate,records};editingAntiTest.value?await registryApi.updateAntiHla(route.params.id,editingAntiTest.value.id,payload):await registryApi.createAntiHla(route.params.id,payload);toast('success','موفق','آزمایش Anti-HLA ذخیره شد');await loadRecipient()}catch(error){toast('error','خطا',errorDetail(error))}}
async function savePersonProfile(payload){saving.value=true;try{await registryApi.updatePersonProfile(detail.value.person.id,payload);toast('success','اطلاعات تماس','اطلاعات مجاز پرونده ذخیره شد');showPersonModal.value=false;await loadRecipient()}catch(error){toast('error','خطا',errorDetail(error))}finally{saving.value=false}}
async function addToWaiting(){saving.value=true;try{const response=await registryApi.updateRecipientStatus(route.params.id,'active','افزودن گیرنده به لیست انتظار از پرونده کاربری');toast('success','لیست انتظار',response.message);await loadRecipient()}catch(error){toast('error','خطا',errorDetail(error))}finally{saving.value=false}}
function openStatusModal(){nextStatus.value='';statusReason.value='';showStatusModal.value=true}
async function saveStatus(){saving.value=true;try{const response=await registryApi.updateRecipientStatus(route.params.id,nextStatus.value,statusReason.value);toast('success','وضعیت',response.message);showStatusModal.value=false;await loadRecipient()}catch(error){toast('error','خطا',errorDetail(error))}finally{saving.value=false}}
function openPriorityModal(){priorityForm.value={medical_urgency:Number(detail.value.profile.medical_urgency||0),regional_disadvantage:Number(detail.value.profile.regional_disadvantage||0),waiting_since:detail.value.profile.waiting_since||'',is_emergency:Boolean(detail.value.profile.is_emergency),emergency_reason:detail.value.profile.emergency_reason||''};showPriorityModal.value=true}
async function savePriority(){saving.value=true;try{const response=await registryApi.updateRecipientPriority(route.params.id,priorityForm.value);toast('success','اولویت',response.message);showPriorityModal.value=false;await loadRecipient()}catch(error){toast('error','خطا',errorDetail(error))}finally{saving.value=false}}
async function leaveWaiting(){saving.value=true;try{const response=await registryApi.updateRecipientStatus(route.params.id,'temporarily_inactive','خروج موقت گیرنده از لیست انتظار از طریق پرونده');toast('success','لیست انتظار',response.message);await loadRecipient()}catch(error){toast('error','خطا',errorDetail(error))}finally{saving.value=false}}
const changeMatchPage = page => { currentMatchPage.value = Math.min(Math.max(1, page), matchPagination.value.pages) }
onMounted(loadRecipient)
</script>

<style scoped>
.gender-avatar{font-size:34px}.workflow-help,.priority-summary{padding:10px;background:var(--surface-muted);border-radius:var(--radius-md);color:var(--text-2);font-size:12px}.priority-summary{display:grid;gap:7px;margin:14px 0}.priority-summary p{margin:0}.accordion-result-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;cursor:pointer}.accordion-result-content{padding-top:16px;border-top:1px solid var(--border);margin-top:14px}
.profile-page,.section-stack,.overview-stack,.record-list,.match-list{display:grid;gap:16px}.profile-hero{display:grid;grid-template-columns:auto minmax(220px,1fr) minmax(340px,1.15fr) auto;align-items:center;gap:20px;padding:22px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow-1)}.hero-title-row,.section-heading,.button-row,.tag-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.hero-title-row h2{margin:0}.profile-meta{display:flex;gap:14px;flex-wrap:wrap;color:var(--text-2);margin-top:10px}.profile-meta span{display:flex;align-items:center;gap:5px}.hero-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.hero-stats>div,.summary-card{padding:12px;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--surface-2)}.hero-stats small,.hero-stats span,.summary-card small,.summary-card span,.info-grid small,.record-card small{display:block;color:var(--text-2);font-size:12px}.hero-stats strong{display:block;font-size:18px;margin:4px 0}.hero-actions{display:grid;gap:8px}.profile-tabs{overflow-x:auto}.tab-count{min-width:20px;height:20px;border-radius:99px;padding:0 5px;background:var(--color-primary-soft);display:inline-grid;place-items:center}.summary-card{display:flex;align-items:center;gap:12px}.summary-card>i{font-size:30px;color:var(--color-primary)}.summary-card strong{display:block;margin:4px 0}.info-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0;border:1px solid var(--border);border-radius:var(--radius-md);overflow:hidden}.info-grid>div{padding:14px;border-left:1px solid var(--border);border-bottom:1px solid var(--border);display:grid;gap:5px}.section-heading{justify-content:space-between;margin-bottom:16px}.section-heading .form-card-title{margin:0}.section-hint{margin:4px 0 0;color:var(--text-2);font-size:13px}.hla-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.hla-item{display:grid;gap:8px;padding:12px;border:1px solid var(--border);border-radius:var(--radius-md)}.record-card{display:grid;grid-template-columns:minmax(150px,.65fr) minmax(0,1fr) auto;align-items:center;gap:14px;padding:14px;border:1px solid var(--border);border-radius:var(--radius-md)}.record-card>div:first-child{display:grid;gap:5px}.match-card{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:16px;padding:16px;border:1px solid var(--border);border-radius:var(--radius-lg)}.match-rank{font-weight:800;color:var(--color-primary)}.match-main{display:grid;gap:7px}.match-main>span{color:var(--text-2)}.mismatch-line{display:block;color:var(--text-2);font-size:11px;white-space:pre-line}.score-ring{width:64px;height:64px;border:5px solid var(--color-primary-soft);border-top-color:var(--color-primary);border-radius:50%;display:grid;place-items:center;font-weight:800}.score-ring small{font-size:9px;font-weight:400;margin-top:-14px}.inline-loading{text-align:center;padding:30px;color:var(--text-2)}.status-layout{display:grid;grid-template-columns:.7fr 1.3fr;gap:16px}.status-current{display:grid;gap:16px;justify-items:start}.status-pill{display:inline-flex;padding:6px 10px;border-radius:999px;font-size:12px;font-weight:700}.status-pill.large{font-size:15px;padding:9px 14px}.is-success{background:#dcfce7;color:#166534}.is-warning{background:#fef3c7;color:#92400e}.is-danger{background:#fee2e2;color:#991b1b}.is-info{background:var(--color-primary-soft);color:var(--color-primary)}.timeline{display:grid}.timeline article{position:relative;display:grid;grid-template-columns:20px 1fr;gap:10px;padding-bottom:22px}.timeline article:not(:last-child)::before{content:'';position:absolute;right:7px;top:14px;bottom:0;width:2px;background:var(--border)}.timeline-dot{width:16px;height:16px;border:4px solid var(--color-primary-soft);border-radius:50%;background:var(--color-primary);z-index:1}.timeline p{margin:5px 0;color:var(--text-2)}.timeline small{color:var(--text-3)}.narrow{max-width:540px}.text-danger{color:var(--color-danger)}.text-warning{color:#a16207}.tooltip-anchor{cursor:help}.similarity-row{display:flex;flex-wrap:wrap;gap:6px}.similarity-chip{display:inline-flex;align-items:center;padding:3px 10px;border:1px solid #ef4444;border-radius:999px;background:#fff7f7;color:#dc2626;font-size:11px;font-weight:800;cursor:help}
@media(max-width:1100px){.profile-hero{grid-template-columns:auto 1fr}.hero-stats{grid-column:1/-1}.hero-actions{grid-column:1/-1;display:flex}.info-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:700px){.profile-hero{grid-template-columns:1fr}.profile-avatar{display:none}.hero-stats,.hla-grid,.info-grid,.status-layout{grid-template-columns:1fr}.record-card,.match-card{grid-template-columns:1fr}.score-ring{position:absolute;left:24px}.hero-actions{display:grid}.button-row{width:100%}.button-row .btn{flex:1}}
</style>
