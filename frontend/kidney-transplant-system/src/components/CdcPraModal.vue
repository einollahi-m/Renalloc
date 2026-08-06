<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal cdc-pra-modal" role="dialog" aria-modal="true" aria-labelledby="cdc-pra-modal-title">
      <div class="modal-header">
        <h3 id="cdc-pra-modal-title">
          <i class="ri-shield-check-line"></i>
          {{ test ? 'ویرایش آزمایش CDC PRA' : 'افزودن آزمایش CDC PRA' }}
        </h3>
        <button class="modal-close" type="button" aria-label="بستن" @click="close"><i class="ri-close-line"></i></button>
      </div>

      <div class="cdc-pra-modal-body">
        <div class="cdc-pra-modal-note">
          <i class="ri-information-line"></i>
          هر نوبت آزمایش را با تاریخ و نتیجه مستقل Class I و Class II ثبت کنید.
        </div>

        <div class="form-group cdc-pra-date-field">
          <dual-date-field v-model="form.performed_at" label="تاریخ انجام آزمایش *" />
          <div v-if="errors.performed_at" class="form-error">{{ errors.performed_at }}</div>
        </div>

        <div class="cdc-pra-columns">
          <section v-for="item in classes" :key="item.key" class="cdc-pra-card">
            <h4><span class="badge" :class="item.badgeClass">{{ item.label }}</span> نتیجه آزمایش</h4>

            <div class="form-group">
              <label class="form-label">وضعیت نتیجه *</label>
              <div class="segmented-toggle cdc-status-options" role="radiogroup" :aria-label="`نتیجه ${item.label}`">
                <label class="toggle-option" :class="{checked:form[item.key].status==='positive'}">
                  <input v-model="form[item.key].status" type="radio" :name="`detail-cdc-${item.key}`" value="positive" />
                  مثبت
                </label>
                <label class="toggle-option" :class="{checked:form[item.key].status==='negative'}">
                  <input v-model="form[item.key].status" type="radio" :name="`detail-cdc-${item.key}`" value="negative" />
                  منفی
                </label>
              </div>
            </div>

            <div v-if="form[item.key].status==='positive'" class="form-group cdc-value-field">
              <label class="form-label">درصد PRA (۰ تا ۱۰۰) *</label>
              <div class="input-with-suffix" :class="{'form-error-border': errors[item.key]}">
                <input
                  :value="form[item.key].value"
                  type="text"
                  inputmode="decimal"
                  class="form-input"
                  placeholder="مقدار"
                  :aria-invalid="Boolean(errors[item.key])"
                  @input="normalizeValue(item.key, $event)"
                  @blur="validateClass(item.key)"
                />
                <span>٪</span>
              </div>
            </div>
            <div v-if="errors[item.key]" class="form-error">{{ errors[item.key] }}</div>
          </section>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" type="button" @click="close">انصراف</button>
        <button class="btn btn-primary" type="button" @click="submit">
          <i :class="test ? 'ri-save-3-line' : 'ri-add-line'"></i>
          {{ test ? 'ذخیره تغییرات' : 'ثبت آزمایش' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { toFaDigits } from '../utils/date'
import { normalizeLocalizedSignedNumber } from '../utils/validation'

const props = defineProps({
  visible: { type: Boolean, default: false },
  test: { type: Object, default: null },
  existingTests: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'save'])
const classes = [
  { key: 'class_i', label: 'Class I', badgeClass: 'badge-info' },
  { key: 'class_ii', label: 'Class II', badgeClass: 'badge-success' }
]
const form = reactive({
  performed_at: '',
  class_i: { status: '', value: '' },
  class_ii: { status: '', value: '' }
})
const errors = reactive({ performed_at: '', class_i: '', class_ii: '' })
const dateKey = value => String(value || '').split('T')[0]

watch(() => props.visible, visible => {
  if (!visible) return
  form.performed_at = dateKey(props.test?.performed_at || props.test?.test_date)
  classes.forEach(({ key }) => {
    form[key].status = props.test?.[key]?.status || ''
    form[key].value = props.test?.[key]?.value == null
      ? ''
      : toFaDigits(props.test[key].value).replace('.', '٫')
    errors[key] = ''
  })
  errors.performed_at = ''
})

classes.forEach(({ key }) => {
  watch(() => form[key].status, status => {
    errors[key] = ''
    if (status !== 'positive') form[key].value = ''
  })
})

watch(() => form.performed_at, () => { errors.performed_at = '' })

function normalizeValue(key, event) {
  const value = normalizeLocalizedSignedNumber(event.target.value)
  form[key].value = toFaDigits(value).replace('.', '٫')
  validateClass(key)
}

function validateDate() {
  const performedAt = dateKey(form.performed_at)
  if (!performedAt) {
    errors.performed_at = 'تاریخ انجام آزمایش الزامی است'
    return false
  }
  const duplicate = props.existingTests.some(existing => (
    existing.id !== props.test?.id && dateKey(existing.performed_at || existing.test_date) === performedAt
  ))
  if (duplicate) {
    errors.performed_at = 'برای این تاریخ قبلاً یک آزمایش CDC PRA ثبت شده است'
    return false
  }
  errors.performed_at = ''
  return true
}

function validateClass(key) {
  const entry = form[key]
  if (!entry.status) {
    errors[key] = 'وضعیت این کلاس را مشخص کنید'
    return false
  }
  if (entry.status === 'positive') {
    const normalized = normalizeLocalizedSignedNumber(entry.value)
    const value = Number(normalized)
    if (!normalized || !Number.isFinite(value) || value < 0 || value > 100) {
      errors[key] = 'مقدار باید عددی بین ۰ تا ۱۰۰ باشد'
      return false
    }
  }
  errors[key] = ''
  return true
}

function submit() {
  const validDate = validateDate()
  const validClasses = classes.map(({ key }) => validateClass(key)).every(Boolean)
  if (!validDate || !validClasses) return

  emit('save', {
    performed_at: dateKey(form.performed_at),
    class_i: normalizedEntry('class_i'),
    class_ii: normalizedEntry('class_ii')
  })
  close()
}

function normalizedEntry(key) {
  const entry = form[key]
  return {
    status: entry.status,
    value: entry.status === 'positive' ? normalizeLocalizedSignedNumber(entry.value) : null
  }
}

function close() { emit('update:visible', false) }
</script>
