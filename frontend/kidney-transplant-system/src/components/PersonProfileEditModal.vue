<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal profile-edit-modal">
      <div class="modal-header"><h3><i class="ri-user-settings-line"></i> ویرایش اطلاعات پروفایل</h3><button class="modal-close" @click="close"><i class="ri-close-line"></i></button></div>
      <div class="identity-note"><i class="ri-lock-2-line"></i><div><strong>اطلاعات هویتی فقط توسط مدیر backend قابل تغییر است.</strong><span>نام، نام خانوادگی، کد ملی/شناسه، جنسیت و تاریخ تولد در این فرم قفل هستند.</span></div></div>
      <div class="form-grid immutable-grid">
        <div class="form-group"><label class="form-label">نام و نام خانوادگی</label><input :value="person.full_name" class="form-input" disabled></div>
        <div class="form-group"><label class="form-label">کد ملی / شناسه</label><input :value="person.identifier" class="form-input" disabled></div>
        <div class="form-group"><label class="form-label">جنسیت</label><input :value="person.gender==='male'?'مرد':'زن'" class="form-input" disabled></div>
        <div class="form-group"><label class="form-label">تاریخ تولد</label><input :value="person.birth_date" class="form-input" disabled></div>
      </div>
      <div class="form-grid">
        <div class="form-group"><label class="form-label">شماره همراه *</label><input v-model="form.phone" class="form-input" inputmode="numeric" maxlength="11"><small v-if="errors.phone" class="form-error">{{ errors.phone }}</small></div>
        <div class="form-group"><label class="form-label">شماره تماس اضطراری</label><input v-model="form.emergency_contact_phone" class="form-input" inputmode="numeric" maxlength="11"><small v-if="errors.emergency_contact_phone" class="form-error">{{ errors.emergency_contact_phone }}</small></div>
        <div class="form-group"><label class="form-label">تحصیلات</label><select v-model="form.education" class="form-input"><option value="">ثبت نشده</option><option v-for="item in educationOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select></div>
        <div class="form-group"><label class="form-label">وضعیت تأهل</label><select v-model="form.marital_status" class="form-input"><option value="">ثبت نشده</option><option value="single">مجرد</option><option value="married">متأهل</option></select></div>
        <div class="form-group"><label class="form-label">قد (سانتی‌متر)</label><input v-model="form.height_cm" type="number" min="0" max="300" class="form-input"></div>
        <div class="form-group"><label class="form-label">وزن (کیلوگرم)</label><input v-model="form.weight_kg" type="number" min="0" max="500" step="0.1" class="form-input"></div>
      </div>
      <div class="form-group"><label class="form-label">بیمه‌ها</label><div class="check-row"><label v-for="item in insuranceOptions" :key="item.value" class="check-chip" :class="{checked:form.insurance.includes(item.value)}"><input type="checkbox" :value="item.value" v-model="form.insurance">{{ item.label }}</label></div></div>
      <div class="check-row"><label class="check-chip" :class="{checked:form.is_smoker}"><input type="checkbox" v-model="form.is_smoker">سیگاری</label><label class="check-chip" :class="{checked:form.has_addiction}"><input type="checkbox" v-model="form.has_addiction">سابقه اعتیاد</label><label class="check-chip" :class="{checked:form.has_alcohol}"><input type="checkbox" v-model="form.has_alcohol">مصرف الکل</label></div>
      <div class="modal-footer"><button class="btn btn-secondary" @click="close">لغو</button><button class="btn btn-primary" @click="submit"><i class="ri-save-line"></i> ذخیره اطلاعات</button></div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { educationOptions, insuranceOptions } from '../data/options'
import { normalizeIranianMobile, isValidIranianMobile } from '../utils/validation'

const props=defineProps({visible:Boolean,person:{type:Object,default:()=>({})}})
const emit=defineEmits(['update:visible','save'])
const form=reactive({phone:'',emergency_contact_phone:'',education:'',insurance:[],marital_status:'',weight_kg:'',height_cm:'',is_smoker:false,has_addiction:false,has_alcohol:false})
const errors=reactive({phone:'',emergency_contact_phone:''})
watch(()=>props.visible,value=>{if(!value)return;Object.assign(form,{phone:props.person.phone||'',emergency_contact_phone:props.person.emergency_contact_phone||'',education:props.person.education||'',insurance:[...(props.person.insurance||[])],marital_status:props.person.marital_status||'',weight_kg:props.person.weight_kg||'',height_cm:props.person.height_cm||'',is_smoker:Boolean(props.person.is_smoker),has_addiction:Boolean(props.person.has_addiction),has_alcohol:Boolean(props.person.has_alcohol)});errors.phone='';errors.emergency_contact_phone=''})
function validate(){form.phone=normalizeIranianMobile(form.phone);form.emergency_contact_phone=normalizeIranianMobile(form.emergency_contact_phone);errors.phone=isValidIranianMobile(form.phone)?'':'شماره همراه معتبر نیست';errors.emergency_contact_phone=!form.emergency_contact_phone||isValidIranianMobile(form.emergency_contact_phone)?'':'شماره اضطراری معتبر نیست';return !errors.phone&&!errors.emergency_contact_phone}
function submit(){if(!validate())return;emit('save',{...form,insurance:[...form.insurance]});close()}
function close(){emit('update:visible',false)}
</script>

<style scoped>
.profile-edit-modal{max-width:780px;max-height:92vh;overflow:auto}.identity-note{display:flex;gap:10px;padding:12px;margin-bottom:16px;border:1px solid #fbbf24;background:#fffbeb;border-radius:var(--radius-md);color:#92400e}.identity-note i{font-size:22px}.identity-note span{display:block;font-size:12px;margin-top:3px}.immutable-grid{padding:12px;background:var(--surface-muted);border-radius:var(--radius-md);margin-bottom:16px}.check-row{display:flex;gap:8px;flex-wrap:wrap}.check-chip{padding:8px 11px;border:1px solid var(--border);border-radius:999px;cursor:pointer}.check-chip.checked{border-color:var(--color-primary);background:var(--color-primary-soft);color:var(--color-primary)}.check-chip input{margin-left:5px}.form-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}@media(max-width:650px){.form-grid{grid-template-columns:1fr}}
</style>
