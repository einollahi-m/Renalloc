<template>
  <div>
    <div class="page-header">
      <div><div class="page-title">مدیریت Cross-Match</div><div class="page-subtitle">بررسی مرکز، High-Resolution، برنامه‌ریزی و ثبت نتیجه فیزیکی</div></div>
      <button class="btn btn-secondary" @click="load"><i class="ri-refresh-line"></i> به‌روزرسانی</button>
    </div>
    <div v-if="error" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ error }}</div>
    <div class="filters card">
      <button v-for="item in filters" :key="item.value" :class="['filter-chip',{active:filter===item.value}]" @click="filter=item.value;load()">{{ item.label }}</button>
    </div>
    <div class="cross-layout">
      <section class="card list-card">
        <div v-if="loading" class="empty-state"><i class="ri-loader-4-line spin"></i><p>در حال دریافت درخواست‌ها…</p></div>
        <div v-else-if="!items.length" class="empty-state"><i class="ri-test-tube-line"></i><p>درخواستی در این وضعیت وجود ندارد.</p></div>
        <button v-for="item in items" :key="item.id" :class="['request-row',{active:selected?.id===item.id}]" @click="selectItem(item)">
          <span class="pair-icon"><i class="ri-exchange-line"></i></span>
          <span><strong>{{ item.proposal.recipient.fullName }}</strong><small>با {{ item.proposal.donor.fullName }}</small></span>
          <span class="status" :class="item.status">{{ item.status_display }}</span>
        </button>
      </section>
      <section class="card detail-card">
        <template v-if="selected">
          <div class="detail-head"><div><h3>پرونده Cross-Match</h3><small>شناسه {{ selected.id.slice(0,8) }}</small></div><span class="status" :class="selected.status">{{ selected.status_display }}</span></div>
          <div class="pair-box"><div><span>گیرنده</span><strong>{{ selected.proposal.recipient.fullName }}</strong><small>{{ blood(selected.proposal.recipient) }}</small></div><i class="ri-arrow-left-right-line"></i><div><span>اهداکننده</span><strong>{{ selected.proposal.donor.fullName }}</strong><small>{{ blood(selected.proposal.donor) }}</small></div></div>
          <div class="facts"><div><span>نتیجه مجازی</span><strong>{{ selected.proposal.compatibility_display }}</strong></div><div><span>شباهت HLA</span><strong>{{ selected.proposal.hla_summary.total_matches }} آلل</strong></div><div><span>درخواست‌کننده</span><strong>{{ selected.requested_by }}</strong></div></div>
          <div v-if="selected.patient_note" class="patient-note"><i class="ri-message-3-line"></i><div><strong>یادداشت بیمار</strong><p>{{ selected.patient_note }}</p></div></div>
          <div v-if="selected.proposal.warnings.length" class="warning-box"><i class="ri-alert-line"></i>{{ selected.proposal.warnings[0].message }}</div>
          <div class="form-group"><label class="form-label">یادداشت پزشک / نتیجه آزمایش</label><textarea v-model="note" class="form-input" rows="4" placeholder="یادداشت الزامی است"></textarea></div>
          <div class="actions">
            <template v-if="selected.proposal.decision === 'proposed'">
              <button class="btn btn-secondary" @click="decide('rejected')">رد پیشنهاد</button>
              <button class="btn btn-primary" @click="decide('approved')">تأیید مرکز</button>
            </template>
            <template v-else-if="['consultation_requested','center_review'].includes(selected.status)">
              <button class="btn btn-secondary" @click="update('cancelled')">لغو</button>
              <button class="btn btn-primary" @click="update('scheduled')">برنامه‌ریزی Cross-Match فیزیکی</button>
            </template>
            <template v-else-if="selected.status === 'scheduled'">
              <button class="btn result-positive" @click="update('positive')"><i class="ri-close-circle-line"></i> نتیجه مثبت</button>
              <button class="btn result-negative" @click="update('negative')"><i class="ri-checkbox-circle-line"></i> نتیجه منفی</button>
            </template>
            <template v-else-if="selected.status === 'awaiting_high_resolution'">
              <label class="confirmation-check"><input v-model="highResolutionConfirmed" type="checkbox"> نتیجه High-Resolution توسط آزمایشگاه بررسی و تأیید شده است.</label>
              <button class="btn btn-primary" :disabled="!highResolutionConfirmed" @click="update('negative')"><i class="ri-dna-line"></i> ثبت تأیید و نهایی‌سازی</button>
            </template>
            <div v-else class="final-state">این فرایند با نتیجه «{{ selected.status_display }}» بسته شده است.</div>
          </div>
        </template>
        <div v-else class="empty-state"><i class="ri-file-list-3-line"></i><p>یک درخواست را برای بررسی انتخاب کنید.</p></div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { registryApi } from '../services/api'

const filters=[{value:'',label:'همه'},{value:'consultation_requested',label:'مشاوره'},{value:'center_review',label:'بررسی مرکز'},{value:'scheduled',label:'برنامه‌ریزی‌شده'},{value:'awaiting_high_resolution',label:'High-Resolution'},{value:'negative',label:'منفی'},{value:'positive',label:'مثبت'}]
const filter=ref('');const items=ref([]);const selected=ref(null);const note=ref('');const highResolutionConfirmed=ref(false);const loading=ref(false);const saving=ref(false);const error=ref('')
const blood=person=>`${person.bloodType}${person.rhFactor==='positive'?'+':'-'}`
const load=async()=>{loading.value=true;error.value='';try{const response=await registryApi.listCrossmatches(filter.value);items.value=response.crossmatches;if(selected.value)selected.value=items.value.find(i=>i.id===selected.value.id)||null;if(!selected.value)selected.value=items.value[0]||null;note.value=selected.value?.physician_note||''}catch(e){error.value=e.message}finally{loading.value=false}}
const selectItem=item=>{selected.value=item;note.value=item.physician_note||'';highResolutionConfirmed.value=false}
const requireNote=()=>{if(!note.value.trim()){error.value='یادداشت پزشک الزامی است.';return false}return true}
const decide=async decision=>{if(!requireNote())return;saving.value=true;try{await registryApi.decideProposal(selected.value.proposal.id,decision,note.value);window.toast.add({severity:'success',summary:'تصمیم مرکز',detail:'تصمیم با موفقیت ثبت شد'});await load()}catch(e){error.value=e.message}finally{saving.value=false}}
const update=async status=>{if(!requireNote())return;saving.value=true;try{const response=await registryApi.updateCrossmatch(selected.value.id,status,note.value,selected.value.status==='awaiting_high_resolution'&&highResolutionConfirmed.value);window.toast.add({severity:'success',summary:'Cross-Match',detail:response.message});highResolutionConfirmed.value=false;await load()}catch(e){error.value=e.message}finally{saving.value=false}}
onMounted(load)
</script>

<style scoped>
.page-header,.filters,.detail-head,.actions{display:flex;align-items:center;justify-content:space-between;gap:12px}.page-header{align-items:flex-start;margin-bottom:20px}.page-title{font-size:23px;font-weight:900}.page-subtitle{color:var(--text-2);font-size:13px}.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:18px;box-shadow:var(--shadow-1)}.filters{justify-content:flex-start;margin-bottom:14px;overflow:auto}.filter-chip{border:1px solid var(--border);background:var(--surface);padding:7px 13px;border-radius:999px;font-family:inherit;cursor:pointer;white-space:nowrap}.filter-chip.active{background:var(--color-primary);border-color:var(--color-primary);color:#fff}.cross-layout{display:grid;grid-template-columns:minmax(330px,.8fr) minmax(440px,1.2fr);gap:16px}.request-row{width:100%;display:grid;grid-template-columns:38px 1fr auto;align-items:center;gap:10px;text-align:right;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--surface);padding:10px;margin-bottom:8px;font-family:inherit;cursor:pointer}.request-row:hover,.request-row.active{border-color:var(--color-primary);background:var(--color-primary-soft)}.request-row>span:nth-child(2){display:flex;flex-direction:column}.request-row small,.detail-head small{color:var(--text-3)}.pair-icon{width:36px;height:36px;display:grid;place-items:center;border-radius:10px;background:var(--surface-muted);color:var(--color-primary)}.status{padding:4px 9px;border-radius:999px;background:var(--surface-muted);font-size:11px;font-weight:800}.status.negative{background:#ecfdf5;color:var(--success-700)}.status.positive,.status.cancelled{background:#fef2f2;color:var(--error-700)}.status.scheduled{background:#eff6ff;color:var(--info-700)}.status.center_review,.status.consultation_requested{background:#fffbeb;color:var(--warning-700)}.detail-head{margin-bottom:16px}.detail-head h3{margin:0}.pair-box{display:grid;grid-template-columns:1fr 40px 1fr;align-items:center;text-align:center;padding:16px;border-radius:var(--radius-lg);background:var(--surface-muted);margin-bottom:12px}.pair-box div{display:flex;flex-direction:column}.pair-box span,.pair-box small{color:var(--text-2)}.pair-box i{font-size:24px;color:var(--color-primary)}.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}.facts div{padding:9px;border:1px solid var(--border);border-radius:var(--radius-md)}.facts span{display:block;color:var(--text-2);font-size:11px}.patient-note,.warning-box{display:flex;gap:9px;padding:10px;border-radius:var(--radius-md);margin-bottom:12px}.patient-note{background:#eff6ff}.patient-note p{margin:2px 0}.warning-box{background:#fffbeb;color:var(--warning-700)}.result-positive{background:#fee2e2;color:var(--error-700)}.result-negative{background:#d1fae5;color:var(--success-700)}.confirmation-check{display:flex;align-items:center;gap:8px;padding:10px;border:1px solid var(--border);border-radius:var(--radius-md);font-size:12px}.confirmation-check input{accent-color:var(--color-primary)}.final-state{padding:10px;background:var(--surface-muted);border-radius:var(--radius-md)}.empty-state{text-align:center;padding:40px;color:var(--text-2)}.empty-state i{display:block;font-size:40px;color:var(--text-3)}.spin{animation:spin 1s linear infinite}@media(max-width:900px){.cross-layout{grid-template-columns:1fr}.facts{grid-template-columns:1fr}}
</style>
