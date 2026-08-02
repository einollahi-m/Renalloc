<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal anti-hla-modal">
      <div class="modal-header">
        <h3>{{ editBatch ? 'ویرایش آنتی‌بادی‌های Anti-HLA' : 'افزودن آنتی‌بادی Anti-HLA' }}</h3>
        <button class="modal-close" type="button" @click="close"><i class="ri-close-line"></i></button>
      </div>
      <div class="anti-hla-modal-body">
        <dual-date-field v-model="form.testDate" label="تاریخ آزمایش *" />
        <div class="anti-hla-columns">
          <section class="anti-hla-class-card">
            <h4><span class="badge badge-info">Class I</span> آنتی‌بادی‌های کلاس I</h4>
            <label class="anti-hla-none-option" :class="{ checked: form.classINone }">
              <input v-model="form.classINone" type="checkbox" />
              <span><strong>None</strong><small>بدون آنتی‌بادی در Class I</small></span>
            </label>
            <div v-for="field in classIFields" :key="field.key" class="form-group">
              <label class="form-label">{{ field.label }}</label>
              <checkbox-multi-select v-model="form[field.key]" :options="field.options" :max-chips="1" :ltr="true" :disabled="form.classINone" placeholder="انتخاب آنتی‌ژن" />
            </div>
          </section>
          <section class="anti-hla-class-card">
            <h4><span class="badge badge-success">Class II</span> آنتی‌بادی‌های کلاس II</h4>
            <label class="anti-hla-none-option" :class="{ checked: form.classIINone }">
              <input v-model="form.classIINone" type="checkbox" />
              <span><strong>None</strong><small>بدون آنتی‌بادی در Class II</small></span>
            </label>
            <div v-for="field in classIIFields" :key="field.key" class="form-group">
              <label class="form-label">{{ field.label }}</label>
              <checkbox-multi-select v-model="form[field.key]" :options="field.options" :max-chips="1" :ltr="true" :disabled="form.classIINone" placeholder="انتخاب آنتی‌ژن" />
            </div>
          </section>
        </div>
        <div class="anti-hla-selection-summary">
          <i class="ri-information-line"></i>
          {{ selectedCount ? `${toFa(selectedCount)} آنتی‌بادی انتخاب شده است` : 'حداقل یک آنتی‌بادی انتخاب کنید' }}
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" type="button" @click="close">انصراف</button>
        <button class="btn btn-primary" type="button" @click="submit">
          <i :class="editBatch ? 'ri-save-3-line' : 'ri-add-line'"></i>
          {{ editBatch ? 'ذخیره تغییرات' : 'ثبت آنتی‌بادی‌ها' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { toFaDigits } from '../utils/date'
import {
  antiHlaAOptions, antiHlaBOptions, antiHlaCOptions,
  antiHlaDRB1Options, antiHlaDQB1Options, antiHlaDRB345Options
} from '../data/hlaOptions'

const props = defineProps({
  visible: { type: Boolean, default: false },
  editBatch: { type: Object, default: null }
})

const emit = defineEmits(['update:visible', 'save'])
const toFa = toFaDigits
const form = reactive({
  testDate: '',
  classINone: false,
  classIINone: false,
  selectedA: [], selectedB: [], selectedC: [],
  selectedDRB1: [], selectedDQB1: [], selectedDRB345: []
})

const classIFields = [
  { key: 'selectedA', label: 'HLA-A', locus: 'A', options: antiHlaAOptions },
  { key: 'selectedB', label: 'HLA-B', locus: 'B', options: antiHlaBOptions },
  { key: 'selectedC', label: 'HLA-C', locus: 'C', options: antiHlaCOptions }
]
const classIIFields = [
  { key: 'selectedDRB1', label: 'HLA-DRB1', locus: 'DRB1', options: antiHlaDRB1Options },
  { key: 'selectedDQB1', label: 'HLA-DQB1', locus: 'DQB1', options: antiHlaDQB1Options },
  { key: 'selectedDRB345', label: 'HLA-DRB345', locus: 'DRB345', options: antiHlaDRB345Options }
]
const allFields = [...classIFields, ...classIIFields]
const selectedCount = computed(() => allFields.reduce((sum, field) => sum + form[field.key].length, 0) + Number(form.classINone) + Number(form.classIINone))

watch(() => form.classINone, selected => {
  if (selected) classIFields.forEach(field => { form[field.key] = [] })
})
watch(() => form.classIINone, selected => {
  if (selected) classIIFields.forEach(field => { form[field.key] = [] })
})

watch(() => props.visible, visible => {
  if (!visible) return
  reset()
  if (!props.editBatch) return
  form.testDate = String(props.editBatch.testDate || '').split('T')[0]
  form.classINone = props.editBatch.records.some(record => (record.isNone || record.antigen === 'None') && record.class === 'I')
  form.classIINone = props.editBatch.records.some(record => (record.isNone || record.antigen === 'None') && record.class === 'II')
  props.editBatch.records.forEach(record => {
    if (record.isNone || record.antigen === 'None') return
    const field = allFields.find(item => item.locus === record.locus)
    const antigen = record.antigen || String(record.testName || '').split(' - ').pop()
    if (field && antigen && !form[field.key].includes(antigen)) form[field.key].push(antigen)
  })
})

function reset() {
  form.testDate = ''
  form.classINone = false
  form.classIINone = false
  allFields.forEach(field => { form[field.key] = [] })
}

function submit() {
  if (!form.testDate) {
    window.toast?.add({ severity: 'warning', summary: 'خطا', detail: 'تاریخ آزمایش الزامی است' })
    return
  }
  if (!selectedCount.value) {
    window.toast?.add({ severity: 'warning', summary: 'خطا', detail: 'حداقل یک آنتی‌بادی انتخاب کنید' })
    return
  }
  const batchId = props.editBatch?.id || `anti-hla-${Date.now()}`
  const records = []
  if (form.classINone) records.push({
    key: `${batchId}-class-I-none`, batchId, class: 'I', locus: '', antigen: 'None',
    testName: 'Class I - None', value: 0, mfi: 0, antibodyCount: 0, isNone: true, testDate: form.testDate
  })
  if (form.classIINone) records.push({
    key: `${batchId}-class-II-none`, batchId, class: 'II', locus: '', antigen: 'None',
    testName: 'Class II - None', value: 0, mfi: 0, antibodyCount: 0, isNone: true, testDate: form.testDate
  })
  allFields.forEach((field, index) => {
    const className = index < classIFields.length ? 'I' : 'II'
    if ((className === 'I' && form.classINone) || (className === 'II' && form.classIINone)) return
    form[field.key].forEach(antigen => records.push({
      key: `${batchId}-${field.locus}-${antigen}`,
      batchId,
      class: className,
      locus: field.locus,
      antigen,
      testName: `${field.locus} - ${antigen}`,
      value: null,
      mfi: null,
      testDate: form.testDate
    }))
  })
  emit('save', { id: batchId, testDate: form.testDate, records })
  close()
}

function close() { emit('update:visible', false) }
</script>
