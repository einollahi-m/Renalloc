<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal" style="max-width: 820px; max-height: 92vh; display:flex; flex-direction:column;">
      <div class="modal-header">
        <h3>{{ editDate ? 'ویرایش آزمایش‌های ویروسی' : 'ثبت نتایج آزمایش‌های ویروسی' }}</h3>
        <button class="modal-close" type="button" @click="close"><i class="ri-close-line"></i></button>
      </div>
      <div style="overflow-y:auto; flex:1; padding: 4px 20px;">
        <dual-date-field v-model="testDate" label="تاریخ آزمایش" />
        <div class="vt-grid">
          <div v-for="test in viralTestOptions" :key="test" class="vt-row">
            <div class="vt-name">{{ test }}</div>
            <div class="vt-input"><input type="text" class="form-input" v-model="results[test]" placeholder="مقدار" @input="normalizeResult(test, $event)" /></div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" type="button" @click="close">انصراف</button>
        <button class="btn btn-primary" type="button" @click="submit">{{ editDate ? 'بروزرسانی' : 'ثبت آزمایش‌ها' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { viralTestOptions } from '../data/viralTests'
import { normalizeLocalizedDigits } from '../utils/validation'

const props = defineProps({
  visible: { type: Boolean, default: false },
  editDate: { type: String, default: null },
  existingTests: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'add', 'save'])

const testDate = ref('')
const results = reactive({})

viralTestOptions.forEach(t => results[t] = '')

watch(() => props.visible, (v) => {
  if (v) {
    testDate.value = ''
    viralTestOptions.forEach(t => results[t] = '')
    if (props.editDate) {
      testDate.value = props.editDate.split('T')[0]
      props.existingTests.forEach(t => { if (t.testName in results) results[t.testName] = t.value })
    }
  }
})

function submit() {
  if (!testDate.value) { window.toast?.add({ severity:'warning', summary:'خطا', detail:'تاریخ آزمایش الزامی است' }); return }
  const testDateIso = testDate.value + 'T00:00:00.000Z'
  const tests = viralTestOptions
    .filter(t => results[t] && String(results[t]).trim() !== '')
    .map(t => ({ category: 'آزمایش ویروسی', testName: t, value: String(results[t]).trim(), testDate: testDateIso }))
  if (!tests.length) { window.toast?.add({ severity:'warning', summary:'خطا', detail:'حداقل یک مقدار وارد کنید' }); return }
  if (props.editDate) emit('save', { date: testDateIso, tests })
  else emit('add', tests)
  emit('update:visible', false)
}

function normalizeResult(test, event) {
  results[test] = normalizeLocalizedDigits(event.target.value)
}

function close() { emit('update:visible', false) }
</script>
