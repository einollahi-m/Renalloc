<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal" style="max-width:900px;">
      <div class="modal-header">
        <h3>{{ hasExistingTyping ? 'ویرایش تایپ HLA' : 'ثبت تایپ HLA' }}</h3>
        <button class="modal-close" type="button" @click="close"><i class="ri-close-line"></i></button>
      </div>
      <div style="padding:20px;overflow-y:auto;max-height:72vh;">
        <div class="alert alert-info mb-4">
          <i class="ri-information-line"></i>
          برای هر locus حداکثر دو آلل قابل انتخاب است. خالی گذاشتن تمام locusها نیز مجاز است.
        </div>
        <div class="grid grid-2">
          <div v-for="field in fields" :key="field.key" class="form-group">
            <label class="form-label">{{ field.label }}</label>
            <checkbox-multi-select
              v-model="form[field.key]"
              :options="field.options"
              :max-selected="2"
              :ltr="true"
              placeholder="انتخاب آلل"
            />
            <label class="homozygous-option" :class="{disabled: form[field.key].length !== 1}">
              <input v-model="homozygous[field.key]" type="checkbox" :disabled="form[field.key].length !== 1" />
              هموزیگوت (دو نسخه از همین آلل)
            </label>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" type="button" @click="close">انصراف</button>
        <button class="btn btn-primary" type="button" @click="submit"><i class="ri-save-line"></i> ذخیره تایپ HLA</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { hlaOptions } from '../data/hlaOptions'

const props = defineProps({
  visible: { type: Boolean, default: false },
  initialValue: { type: Object, default: null }
})
const emit = defineEmits(['update:visible', 'save'])

const fields = [
  { key: 'hla_a', label: 'HLA-A', options: hlaOptions.hlaA },
  { key: 'hla_b', label: 'HLA-B', options: hlaOptions.hlaB },
  { key: 'hla_c', label: 'HLA-C', options: hlaOptions.hlaC },
  { key: 'hla_drb1', label: 'HLA-DRB1', options: hlaOptions.hlaDRB1 },
  { key: 'hla_dqb1', label: 'HLA-DQB1', options: hlaOptions.hlaDQB1 },
  { key: 'hla_drb', label: 'HLA-DRB3/4/5', options: hlaOptions.hlaDRB },
  { key: 'hla_dqa1', label: 'HLA-DQA1 (High-Resolution)', options: hlaOptions.hlaDQA1 },
  { key: 'hla_dpb1', label: 'HLA-DPB1 (High-Resolution)', options: hlaOptions.hlaDPB1 },
  { key: 'hla_dpa1', label: 'HLA-DPA1 (High-Resolution)', options: hlaOptions.hlaDPA1 }
]
const form = reactive(Object.fromEntries(fields.map(field => [field.key, []])))
const homozygous = reactive(Object.fromEntries(fields.map(field => [field.key, false])))
const hasExistingTyping = computed(() => Boolean(props.initialValue?.id))

watch(() => props.visible, visible => {
  if (!visible) return
  fields.forEach(field => {
    const initial = [...(props.initialValue?.[field.key] || [])]
    homozygous[field.key] = initial.length === 2 && initial[0] === initial[1]
    form[field.key] = homozygous[field.key] ? [initial[0]] : initial
  })
})

watch(
  () => fields.map(field => form[field.key].length),
  lengths => lengths.forEach((length, index) => {
    if (length !== 1) homozygous[fields[index].key] = false
  })
)

function submit() {
  emit('save', Object.fromEntries(fields.map(field => {
    const values = [...form[field.key]]
    return [field.key, homozygous[field.key] && values.length === 1 ? [values[0], values[0]] : values]
  })))
  close()
}

function close() { emit('update:visible', false) }
</script>

<style scoped>
.homozygous-option{display:flex;align-items:center;gap:7px;margin-top:7px;color:var(--text-2);font-size:12px;cursor:pointer}.homozygous-option input{accent-color:var(--color-primary)}.homozygous-option.disabled{opacity:.45;cursor:not-allowed}
</style>
