<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal" style="max-width: 900px; max-height: 92vh; display:flex; flex-direction:column;">
      <div class="modal-header">
        <h3>{{ editDate ? 'ویرایش آزمایش‌های پیوند' : 'ثبت آزمایش‌های پیوند' }}</h3>
        <button class="modal-close" type="button" @click="close"><i class="ri-close-line"></i></button>
      </div>
      <div style="overflow-y:auto; flex:1; padding: 4px 20px;">
        <dual-date-field v-model="testDate" label="تاریخ آزمایش" />
        <div class="rt-categories">
          <button v-for="cat in visibleCategories" :key="cat.key" type="button" class="rt-cat-btn" :class="{active: activeCategory===cat.key}" @click="activeCategory=cat.key">
            <i :class="cat.icon"></i><span>{{ cat.label }}</span>
          </button>
        </div>
        <div v-if="isNumericCategory" class="rt-grid">
          <div v-for="test in currentCategoryTests" :key="test.key" class="rt-row">
            <div class="rt-label"><span>{{ test.label }}</span><small v-if="test.unit">({{ test.unit }})</small></div>
            <div class="rt-input-group">
              <input type="text" class="form-input" v-model="formValues[test.key]" placeholder="مقدار" dir="ltr" style="text-align:center;" @input="validateField(test.key)" />
              <small v-if="errors[test.key]" class="rt-error">{{ errors[test.key] }}</small>
              <small v-else class="rt-hint">{{ test.min }} – {{ test.max }}</small>
            </div>
          </div>
        </div>
        <div v-if="activeCategory==='urine24'" class="rt-panel">
          <div class="rt-result-row">
            <span class="rt-result-label">نتیجه:</span>
            <label class="checkbox-wrap"><input type="radio" v-model="formValues.urine24_result" value="" /> نامشخص</label>
            <label class="checkbox-wrap"><input type="radio" v-model="formValues.urine24_result" value="negative" /> منفی</label>
            <label class="checkbox-wrap"><input type="radio" v-model="formValues.urine24_result" value="positive" /> مثبت</label>
          </div>
          <div v-if="formValues.urine24_result==='positive'" class="rt-grid">
            <div v-for="field in urine24Fields" :key="field.key" class="rt-row">
              <div class="rt-label"><span>{{ field.label }}</span><small v-if="field.unit">({{ field.unit }})</small></div>
              <div class="rt-input-group">
                <input type="text" class="form-input" v-model="formValues[field.key]" placeholder="مقدار" dir="ltr" style="text-align:center;" @input="validateField(field.key)" />
                <small v-if="errors[field.key]" class="rt-error">{{ errors[field.key] }}</small>
                <small v-else class="rt-hint">{{ field.min }} – {{ field.max }}</small>
              </div>
            </div>
          </div>
        </div>
        <div v-if="activeCategory==='urine'" class="rt-panel">
          <h4 class="rt-subtitle">Urine Analysis</h4>
          <div class="rt-urine-grid">
            <div v-for="item in urineAnalysisFields" :key="item.key" class="rt-urine-item">
              <label>{{ item.label }}</label>
              <input v-if="item.type==='text'" type="text" class="form-input" v-model="formValues[item.key]" placeholder="مقدار-مقدار" dir="ltr" />
              <select v-else class="form-select" v-model="formValues[item.key]">
                <option v-for="opt in qualitativeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
          </div>
          <hr style="margin:16px 0; border:none; border-top:1px solid var(--border);" />
          <h4 class="rt-subtitle">Urine Culture</h4>
          <div class="rt-result-row">
            <span class="rt-result-label">نتیجه:</span>
            <label class="checkbox-wrap"><input type="radio" v-model="formValues.urine_culture_result" value="" /> نامشخص</label>
            <label class="checkbox-wrap"><input type="radio" v-model="formValues.urine_culture_result" value="positive" /> مثبت</label>
            <label class="checkbox-wrap"><input type="radio" v-model="formValues.urine_culture_result" value="negative" /> منفی</label>
          </div>
          <div v-if="formValues.urine_culture_result==='positive'" class="rt-row" style="margin-top:10px;">
            <div class="rt-label"><span>Count</span><small>(CFU/mL)</small></div>
            <div class="rt-input-group">
              <input type="text" class="form-input" v-model="formValues.urine_culture_count" placeholder="تعداد کلونی" dir="ltr" style="text-align:center;" @input="validateField('urine_culture_count')" />
              <small v-if="errors.urine_culture_count" class="rt-error">{{ errors.urine_culture_count }}</small>
              <small v-else class="rt-hint">0 – 100000000</small>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" type="button" @click="close">انصراف</button>
        <button class="btn btn-primary" type="button" @click="submit">{{ editDate ? 'بروزرسانی آزمایش‌ها' : 'ثبت آزمایش‌ها' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { routineCategories, routineCategoryLabels, routineTestsByCategory, testDefByKey, urine24Fields, urineAnalysisFields, qualitativeOptions } from '../data/routineTests'

const props = defineProps({
  visible: { type: Boolean, default: false },
  editDate: { type: String, default: null },
  existingTests: { type: Array, default: () => [] },
  gender: { type: String, default: 'female' }
})

const emit = defineEmits(['update:visible', 'add', 'save'])

const testDate = ref('')
const activeCategory = ref('cbc')
const formValues = reactive({})
const errors = reactive({})

Object.values(routineTestsByCategory).forEach(arr => arr.forEach(t => formValues[t.key] = ''))
urine24Fields.forEach(f => formValues[f.key] = '')
urineAnalysisFields.forEach(f => formValues[f.key] = '')
formValues.urine24_result = ''
formValues.urine_culture_result = ''
formValues.urine_culture_count = ''

const visibleCategories = computed(() => props.gender === 'male' ? routineCategories.filter(c => c.key !== 'female') : routineCategories)
const currentCategoryTests = computed(() => routineTestsByCategory[activeCategory.value] || [])
const isNumericCategory = computed(() => ['cbc','blood_biochem','other_biochem','thyroid','female'].includes(activeCategory.value))

watch(() => props.visible, (v) => {
  if (v) {
    testDate.value = ''
    activeCategory.value = 'cbc'
    Object.values(routineTestsByCategory).forEach(arr => arr.forEach(t => formValues[t.key] = ''))
    urine24Fields.forEach(f => formValues[f.key] = '')
    urineAnalysisFields.forEach(f => formValues[f.key] = '')
    formValues.urine24_result = ''
    formValues.urine_culture_result = ''
    formValues.urine_culture_count = ''
    Object.keys(errors).forEach(k => errors[k] = '')
    if (props.editDate) populateForEdit()
  }
})

function populateForEdit() {
  testDate.value = props.editDate.split('T')[0]
  for (const t of props.existingTests) {
    const catKey = Object.keys(routineTestsByCategory).find(k => routineCategoryLabels[k] === t.category)
    if (catKey) {
      const test = routineTestsByCategory[catKey].find(x => x.key === t.testName)
      if (test) formValues[test.key] = t.value
    } else if (t.category === 'Urine 24H') {
      if (t.testName === 'urine24_result') formValues.urine24_result = t.value
      else if (t.testName in formValues) formValues[t.testName] = t.value
    } else if (t.category === 'آزمایش ادرار') {
      if (t.testName === 'Urine Culture') formValues.urine_culture_result = t.value
      else if (t.testName in formValues) formValues[t.testName] = t.value
    }
  }
}

function validateField(key) {
  const def = testDefByKey[key]
  const raw = formValues[key]
  errors[key] = ''
  if (raw === '' || raw == null) return true
  const normalized = String(raw).replace(/[٬,]/g, '').replace(/٫/g, '.').replace(/[^0-9.\-eE]/g, '')
  if (normalized === '' || isNaN(Number(normalized))) { errors[key] = 'مقدار عددی وارد کنید'; return false }
  const num = parseFloat(normalized)
  if (def && def.min != null && num < def.min) { errors[key] = `کمتر از حد مجاز (${def.min})`; return false }
  if (def && def.max != null && num > def.max) { errors[key] = `بیشتر از حد مجاز (${def.max})`; return false }
  return true
}

function submit() {
  if (!testDate.value) { window.toast?.add({ severity:'warning', summary:'خطا', detail:'تاریخ آزمایش الزامی است' }); return }
  let valid = true
  let firstBadCat = null
  for (const catKey of Object.keys(routineTestsByCategory)) {
    for (const t of routineTestsByCategory[catKey]) {
      if (formValues[t.key] !== '' && formValues[t.key] != null) {
        if (!validateField(t.key)) { valid = false; if (!firstBadCat) firstBadCat = catKey }
      }
    }
  }
  for (const f of urine24Fields) {
    if (formValues[f.key] !== '' && formValues[f.key] != null && !validateField(f.key)) { valid = false; if (!firstBadCat) firstBadCat = 'urine24' }
  }
  if (formValues.urine_culture_count !== '' && formValues.urine_culture_count != null && !validateField('urine_culture_count')) { valid = false; if (!firstBadCat) firstBadCat = 'urine' }
  if (!valid) {
    if (firstBadCat) activeCategory.value = firstBadCat
    window.toast?.add({ severity:'warning', summary:'خطا', detail:'مقادیر وارد شده معتبر نیستند' })
    return
  }
  const testDateIso = testDate.value + 'T00:00:00.000Z'
  const tests = []
  for (const catKey of Object.keys(routineTestsByCategory)) {
    const catLabel = routineCategoryLabels[catKey]
    for (const t of routineTestsByCategory[catKey]) {
      const v = formValues[t.key]
      if (v !== '' && v != null) tests.push({ category: catLabel, testName: t.key, value: String(v), testDate: testDateIso })
    }
  }
  if (formValues.urine24_result === 'positive' || formValues.urine24_result === 'negative') {
    tests.push({ category: 'Urine 24H', testName: 'urine24_result', value: formValues.urine24_result, testDate: testDateIso })
    if (formValues.urine24_result === 'positive') {
      for (const f of urine24Fields) {
        if (formValues[f.key] !== '' && formValues[f.key] != null) tests.push({ category: 'Urine 24H', testName: f.key, value: String(formValues[f.key]), testDate: testDateIso })
      }
    }
  }
  for (const item of urineAnalysisFields) {
    const v = formValues[item.key]
    if (v !== '' && v != null) tests.push({ category: 'آزمایش ادرار', testName: item.key, value: String(v), testDate: testDateIso })
  }
  if (formValues.urine_culture_result === 'positive' || formValues.urine_culture_result === 'negative') {
    tests.push({ category: 'آزمایش ادرار', testName: 'Urine Culture', value: formValues.urine_culture_result, testDate: testDateIso })
    if (formValues.urine_culture_result === 'positive' && formValues.urine_culture_count !== '' && formValues.urine_culture_count != null) {
      tests.push({ category: 'آزمایش ادرار', testName: 'urine_culture_count', value: String(formValues.urine_culture_count), testDate: testDateIso })
    }
  }
  if (!tests.length) { window.toast?.add({ severity:'warning', summary:'خطا', detail:'حداقل یک مقدار آزمایش وارد کنید' }); return }
  if (props.editDate) emit('save', { date: testDateIso, tests })
  else emit('add', tests)
  emit('update:visible', false)
}

function close() { emit('update:visible', false) }
</script>
