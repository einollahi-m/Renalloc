<template>
  <section class="form-card approval-panel">
    <div class="panel-heading"><div><div class="form-card-title"><i class="ri-checkbox-circle-line"></i> تأییدیه‌های پزشکی</div><p>همان گردش ثبت‌نام؛ تخصص را انتخاب و وضعیت و مشخصات پزشک را ثبت کنید.</p></div><span :class="['badge',currentRecord?'badge-info':'badge-warning']">{{ currentRecord?'ثبت‌شده':'ثبت‌نشده' }}</span></div>
    <div class="specialties-header"><button v-for="spec in allSpecialties" :key="spec.key" type="button" class="specialty-tab" :class="[{active:activeSpecialty===spec.key},approvalClass(recordFor(spec.key)?.status)]" @click="selectSpecialty(spec.key)"><i :class="approvalIcon(recordFor(spec.key)?.status)"></i><span>{{ spec.label }}</span></button></div>
    <div v-if="activeSpecialty" class="specialty-detail" :class="approvalClass(form.status)">
      <div class="form-group"><label class="form-label">وضعیت تأیید</label><div class="radio-pills"><label v-for="item in statusOptions" :key="item.value" class="radio-pill" :class="{checked:form.status===item.value}"><input v-model="form.status" type="radio" :value="item.value">{{ item.label }}</label></div></div>
      <dual-date-field v-model="form.approval_date" label="تاریخ تأیید" />
      <div class="form-grid"><div class="form-group"><label class="form-label">نام پزشک</label><input v-model="form.doctor_name" class="form-input" placeholder="نام پزشک"></div><div class="form-group"><label class="form-label">کد نظام پزشکی</label><input v-model="form.medical_code" class="form-input" inputmode="numeric" placeholder="کد نظام پزشکی"></div></div>
      <div class="form-group"><label class="form-label">توضیحات</label><textarea v-model="form.notes" class="form-input" rows="3" placeholder="توضیحات..."></textarea></div>
      <div class="save-row"><button class="btn btn-primary" :disabled="saving" @click="save"><i :class="saving?'ri-loader-4-line':'ri-save-line'"></i>{{ currentRecord?'ویرایش تأییدیه':'افزودن تأییدیه' }}</button></div>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { registryApi } from '../services/api'
import { specialties, donorSpecialties, approvalStatusOptions } from '../data/options'
import DualDateField from './DualDateField.vue'
const props=defineProps({personId:{type:String,required:true},role:{type:String,default:'recipient'},approvals:{type:Array,default:()=>[]}})
const emit=defineEmits(['refresh'])
const allSpecialties=computed(()=>props.role==='donor'?donorSpecialties:specialties)
const activeSpecialty=ref(allSpecialties.value[0]?.key||''),saving=ref(false)
const form=reactive({status:'on_hold',approval_date:'',doctor_name:'',medical_code:'',notes:''})
const statusOptions=approvalStatusOptions
const recordFor=key=>props.approvals.find(item=>item.specialty===key)||null
const currentRecord=computed(()=>recordFor(activeSpecialty.value))
function populate(){const item=currentRecord.value;Object.assign(form,{status:item?.status||'on_hold',approval_date:item?.approval_date||'',doctor_name:item?.doctor_name||'',medical_code:item?.medical_code||'',notes:item?.notes||''})}
function selectSpecialty(key){activeSpecialty.value=key;populate()}
watch(()=>props.approvals,populate,{deep:true,immediate:true})
const approvalClass=status=>status==='approved'?'is-approved':status==='rejected'?'is-rejected':'is-pending'
const approvalIcon=status=>status==='approved'?'ri-checkbox-circle-line':status==='rejected'?'ri-close-circle-line':'ri-time-line'
async function save(){saving.value=true;try{const payload={specialty:activeSpecialty.value,...form};const response=currentRecord.value?await registryApi.updateApproval(props.personId,currentRecord.value.id,payload):await registryApi.createApproval(props.personId,payload);window.toast?.add({severity:'success',summary:'تأییدیه',detail:response.message});emit('refresh')}catch(error){window.toast?.add({severity:'error',summary:'خطا',detail:error.message})}finally{saving.value=false}}
</script>

<style scoped>
.approval-panel{display:grid;gap:16px}.panel-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.panel-heading .form-card-title{margin:0}.panel-heading p{margin:4px 0 0;color:var(--text-2);font-size:12px}.specialties-header{display:flex;gap:8px;overflow:auto;padding-bottom:4px}.specialty-tab{min-width:135px;display:grid;justify-items:center;gap:5px;padding:12px;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--surface);cursor:pointer}.specialty-tab i{font-size:23px}.specialty-tab.active{border-color:var(--color-primary);box-shadow:0 0 0 2px var(--color-primary-soft)}.specialty-tab.is-approved{color:#166534;background:#f0fdf4}.specialty-tab.is-rejected{color:#991b1b;background:#fef2f2}.specialty-tab.is-pending{color:#92400e;background:#fffbeb}.specialty-detail{padding:18px;border-right:4px solid #f59e0b;background:var(--surface-muted);border-radius:var(--radius-md)}.specialty-detail.is-approved{border-right-color:#22c55e}.specialty-detail.is-rejected{border-right-color:#ef4444}.radio-pills{display:flex;gap:8px;flex-wrap:wrap}.radio-pill{padding:8px 12px;border:1px solid var(--border);border-radius:999px;cursor:pointer;background:var(--surface)}.radio-pill.checked{border-color:var(--color-primary);background:var(--color-primary-soft);color:var(--color-primary)}.radio-pill input{margin-left:5px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.save-row{display:flex;justify-content:flex-end}@media(max-width:600px){.form-grid{grid-template-columns:1fr}.panel-heading{flex-direction:column}}
</style>
