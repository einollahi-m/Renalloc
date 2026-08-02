<template>
  <div class="cms" :class="{open: open, disabled: disabled}" v-click-outside="close">
    <div class="cms-control" @click="togglePanel" tabindex="0">
      <div class="cms-values" v-if="modelValue.length">
        <span class="cms-chip" v-for="v in visibleChips" :key="v">
          {{ labelOf(v) }}
          <i class="ri-close-line" @click.stop="remove(v)"></i>
        </span>
        <span v-if="hiddenCount > 0" class="cms-chip cms-more" @click.stop="togglePanel">+{{ toFa(hiddenCount) }} …</span>
      </div>
      <span v-else class="cms-placeholder">{{ placeholder }}</span>
      <i class="ri-arrow-down-s-line cms-arrow"></i>
    </div>
    <div class="cms-panel" v-show="open && !disabled">
      <label v-for="opt in options" :key="opt.value" class="cms-option" :class="{disabled: isDisabled(opt.value)}">
        <input type="checkbox" :checked="isChecked(opt.value)" :disabled="isDisabled(opt.value)" @change="toggle(opt.value)" />
        <span :dir="ltr ? 'ltr' : 'rtl'">{{ opt.label }}</span>
      </label>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { toFaDigits } from '../utils/date'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  maxSelected: { type: Number, default: 0 },
  maxChips: { type: Number, default: 6 },
  placeholder: { type: String, default: 'انتخاب کنید' },
  disabled: { type: Boolean, default: false },
  ltr: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const toFa = toFaDigits
const isChecked = (v) => props.modelValue.includes(v)
const isDisabled = (v) => props.maxSelected > 0 && props.modelValue.length >= props.maxSelected && !props.modelValue.includes(v)
const visibleChips = computed(() => props.modelValue.slice(0, props.maxChips))
const hiddenCount = computed(() => Math.max(0, props.modelValue.length - props.maxChips))

function togglePanel() { if (!props.disabled) open.value = !open.value }
function toggle(v) {
  const cur = [...props.modelValue]
  const idx = cur.indexOf(v)
  if (idx >= 0) cur.splice(idx, 1)
  else {
    if (props.maxSelected > 0 && cur.length >= props.maxSelected) return
    cur.push(v)
  }
  emit('update:modelValue', cur)
}
function remove(v) { emit('update:modelValue', props.modelValue.filter(x => x !== v)) }
function labelOf(v) { const o = props.options.find(o => o.value === v); return o ? o.label : v }
function close() { open.value = false }
</script>

<style scoped>
.cms { position: relative; display: inline-block; width: 100%; font-family: inherit; }
.cms.disabled { opacity: .6; pointer-events: none; }
.cms-control {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  padding: 9px 12px; border-radius: var(--radius-md); border: 1px solid var(--border);
  background: var(--surface); cursor: pointer; transition: all .2s; min-height: 42px;
}
.cms-control:hover { border-color: var(--color-primary); }
.cms-control:focus-within { outline: 2px solid var(--color-primary-soft); border-color: var(--color-primary); }
.cms-values { display: flex; flex-wrap: wrap; gap: 6px; flex: 1; }
.cms-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 8px; border-radius: var(--radius-full);
  background: var(--color-primary-soft); color: var(--color-primary);
  font-size: 12px; font-weight: 600;
}
.cms-chip i { cursor: pointer; opacity: .7; transition: opacity .2s; }
.cms-chip i:hover { opacity: 1; }
.cms-chip.cms-more { background: var(--surface-muted); color: var(--text-2); cursor: pointer; }
.cms-placeholder { color: var(--text-3); font-size: 13px; }
.cms-arrow { color: var(--text-3); transition: transform .2s; }
.cms.open .cms-arrow { transform: rotate(180deg); }
.cms-panel {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-md); box-shadow: var(--shadow-3);
  z-index: 100; max-height: 240px; overflow-y: auto; padding: 6px;
}
.cms-option {
  display: flex; align-items: center; gap: 8px; padding: 7px 9px;
  border-radius: var(--radius-sm); cursor: pointer; transition: background .2s;
  font-size: 13px;
}
.cms-option:hover { background: var(--surface-muted); }
.cms-option input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--color-primary); cursor: pointer; }
.cms-option.disabled { opacity: .5; cursor: not-allowed; }
</style>
