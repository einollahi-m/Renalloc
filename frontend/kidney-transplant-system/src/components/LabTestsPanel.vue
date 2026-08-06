<template>
  <section class="form-card lab-panel">
    <div class="panel-heading"><div><div class="form-card-title"><i class="ri-flask-line"></i> آزمایش‌های روتین و ویروسی</div><p>نتایج بر اساس نوع، دسته‌بندی و تاریخ آزمایش نمایش داده می‌شوند.</p></div><button class="btn btn-primary btn-sm" @click="openCreate"><i class="ri-add-line"></i> افزودن آزمایش</button></div>
    <div class="sub-tabs"><button :class="{active:activeKind==='routine'}" @click="activeKind='routine'"><i class="ri-test-tube-line"></i>روتین <span>{{ routineTests.length }}</span></button><button :class="{active:activeKind==='viral'}" @click="activeKind='viral'"><i class="ri-virus-line"></i>ویروسی <span>{{ viralTests.length }}</span></button></div>

    <template v-if="activeKind==='routine'">
      <div v-if="routineCategories.length" class="category-tabs"><button v-for="category in routineCategories" :key="category" :class="{active:activeCategory===category}" @click="activeCategory=category">{{ category }}</button></div>
      <div v-if="routineRows.length" class="table-wrap"><table><thead><tr><th>تاریخ آزمایش</th><th>نام آزمایش</th><th>نتیجه</th><th>اعتبار</th><th>عملیات نوبت</th></tr></thead><tbody><tr v-for="test in routineRows" :key="test.id"><td>{{ formatFaDate(test.performed_at) }}</td><td><strong>{{ test.name }}</strong></td><td dir="ltr">{{ displayResult(test.result) }}</td><td><span :class="['badge',test.is_expired?'badge-danger':'badge-success']">{{ test.is_expired?'منقضی':formatFaDate(test.expires_at) }}</span></td><td><button class="icon-btn" title="ویرایش تمام نتایج این تاریخ" @click="openRoutineEdit(test.performed_at)"><i class="ri-edit-line"></i></button></td></tr></tbody></table></div>
      <div v-else class="empty-state compact-empty-state"><i class="ri-flask-line"></i><h3>آزمایش روتین در این دسته ثبت نشده است</h3></div>
    </template>

    <template v-else>
      <div v-if="viralTests.length" class="table-wrap"><table><thead><tr><th>تاریخ آزمایش</th><th>نام آزمایش</th><th>نتیجه</th><th>اعتبار</th><th>عملیات نوبت</th></tr></thead><tbody><tr v-for="test in viralTests" :key="test.id"><td>{{ formatFaDate(test.performed_at) }}</td><td><strong>{{ test.name }}</strong></td><td dir="ltr">{{ displayResult(test.result) }}</td><td><span :class="['badge',test.is_expired?'badge-danger':'badge-success']">{{ test.is_expired?'منقضی':formatFaDate(test.expires_at) }}</span></td><td><button class="icon-btn" title="ویرایش تمام نتایج این تاریخ" @click="openViralEdit(test.performed_at)"><i class="ri-edit-line"></i></button></td></tr></tbody></table></div>
      <div v-else class="empty-state compact-empty-state"><i class="ri-virus-line"></i><h3>آزمایش ویروسی ثبت نشده است</h3></div>
    </template>

    <routine-tests-modal v-model:visible="showRoutineModal" :gender="gender" :edit-date="editingRoutineDate" :existing-tests="editingRoutineTests" @add="addRoutineTests" @save="saveRoutineTests" />
    <viral-tests-modal v-model:visible="showViralModal" :edit-date="editingViralDate" :existing-tests="editingViralTests" @add="addViralTests" @save="saveViralTests" />
    <div v-if="showTypeModal" class="modal-overlay" @click.self="showTypeModal=false"><div class="modal narrow"><div class="modal-header"><h3>نوع آزمایش</h3><button class="modal-close" @click="showTypeModal=false"><i class="ri-close-line"></i></button></div><div class="type-picker"><button class="choice-card" @click="chooseCreate('routine')"><i class="ri-test-tube-line"></i><strong>آزمایش روتین</strong><span>فرم کامل دسته‌بندی‌شده مشابه ثبت‌نام</span></button><button class="choice-card" @click="chooseCreate('viral')"><i class="ri-virus-line"></i><strong>آزمایش ویروسی</strong><span>ثبت هم‌زمان نتایج یک نوبت</span></button></div></div></div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { registryApi } from '../services/api'
import { formatFaDate } from '../utils/date'
import RoutineTestsModal from './RoutineTestsModal.vue'
import ViralTestsModal from './ViralTestsModal.vue'

const props=defineProps({personId:{type:String,required:true},gender:{type:String,default:'female'},labTests:{type:Array,default:()=>[]}})
const emit=defineEmits(['refresh'])
const activeKind=ref('routine'),activeCategory=ref(''),showTypeModal=ref(false),showRoutineModal=ref(false),showViralModal=ref(false),editingRoutineDate=ref(null),editingViralDate=ref(null),saving=ref(false)
const routineTests=computed(()=>props.labTests.filter(test=>test.kind==='routine'))
const viralTests=computed(()=>props.labTests.filter(test=>test.kind==='viral'))
const routineCategories=computed(()=>[...new Set(routineTests.value.map(test=>test.category))])
watch(routineCategories,categories=>{if(!categories.includes(activeCategory.value))activeCategory.value=categories[0]||''},{immediate:true})
const routineRows=computed(()=>routineTests.value.filter(test=>test.category===activeCategory.value))
const toModalRows=tests=>tests.map(test=>({id:test.id,category:test.category,testName:test.name,value:test.result,testDate:test.performed_at}))
const editingRoutineTests=computed(()=>toModalRows(routineTests.value.filter(test=>test.performed_at===editingRoutineDate.value)))
const editingViralTests=computed(()=>toModalRows(viralTests.value.filter(test=>test.performed_at===editingViralDate.value)))
const displayResult=value=>typeof value==='object'?JSON.stringify(value):value
const notify=(severity,message)=>window.toast?.add({severity,summary:severity==='success'?'موفق':'خطا',detail:message})
function openCreate(){showTypeModal.value=true}
function chooseCreate(kind){showTypeModal.value=false;if(kind==='routine'){editingRoutineDate.value=null;showRoutineModal.value=true}else{editingViralDate.value=null;showViralModal.value=true}}
function openRoutineEdit(date){editingRoutineDate.value=date;showRoutineModal.value=true}
function openViralEdit(date){editingViralDate.value=date;showViralModal.value=true}
async function saveBatch(kind,tests,originalDate=null){saving.value=true;try{await registryApi.saveLabTestBatch(props.personId,{kind,original_date:originalDate,tests:tests.map(test=>({category:test.category,name:test.testName,result:test.value,performed_at:String(test.testDate).slice(0,10)}))});notify('success','نتایج آزمایش ذخیره شدند');emit('refresh')}catch(error){notify('error',error.message)}finally{saving.value=false}}
const addRoutineTests=tests=>saveBatch('routine',tests)
const saveRoutineTests=({tests})=>saveBatch('routine',tests,editingRoutineDate.value)
const addViralTests=tests=>saveBatch('viral',tests)
const saveViralTests=({tests})=>saveBatch('viral',tests,editingViralDate.value)
</script>

<style scoped>
.lab-panel{display:grid;gap:14px}.panel-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}.panel-heading .form-card-title{margin:0}.panel-heading p{margin:4px 0 0;color:var(--text-2);font-size:12px}.sub-tabs,.category-tabs{display:flex;gap:7px;flex-wrap:wrap}.sub-tabs button,.category-tabs button{display:flex;gap:6px;align-items:center;padding:8px 12px;border:1px solid var(--border);border-radius:999px;background:var(--surface);cursor:pointer}.sub-tabs button.active{background:var(--color-primary);color:#fff;border-color:var(--color-primary)}.sub-tabs span{font-size:10px;padding:1px 5px;border-radius:999px;background:rgba(127,127,127,.18)}.category-tabs{padding:10px;background:var(--surface-muted);border-radius:var(--radius-md)}.category-tabs button.active{border-color:#0f766e;background:#ccfbf1;color:#115e59;font-weight:800}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;white-space:nowrap}th,td{padding:11px;border-bottom:1px solid var(--border);text-align:right}th{background:var(--surface-muted);font-size:12px;color:var(--text-2)}.type-picker{display:grid;grid-template-columns:1fr 1fr;gap:12px}.choice-card{display:grid;justify-items:center;gap:7px;padding:22px;border:1px solid var(--border);border-radius:var(--radius-lg);background:var(--surface);cursor:pointer}.choice-card:hover{border-color:var(--color-primary);background:var(--color-primary-soft)}.choice-card i{font-size:34px;color:var(--color-primary)}.choice-card span{font-size:11px;color:var(--text-2)}.narrow{max-width:560px}@media(max-width:600px){.panel-heading{align-items:flex-start;flex-direction:column}.type-picker{grid-template-columns:1fr}}
</style>
