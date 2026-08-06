<template>
  <div class="cms" :class="{open: open, disabled: disabled}" v-click-outside="close" @keydown.esc.stop="close">
    <button
      ref="controlRef"
      type="button"
      class="cms-control"
      :aria-expanded="open"
      aria-haspopup="listbox"
      :disabled="disabled"
      @click="togglePanel"
      @keydown.down.prevent="openPanel"
    >
      <div class="cms-values" v-if="modelValue.length">
        <span class="cms-chip" v-for="v in visibleChips" :key="v">
          {{ labelOf(v) }}
          <i class="ri-close-line" @click.stop="remove(v)"></i>
        </span>
        <span v-if="hiddenCount > 0" class="cms-chip cms-more" @click.stop="togglePanel">+{{ toFa(hiddenCount) }} …</span>
      </div>
      <span v-else class="cms-placeholder">{{ placeholder }}</span>
      <i class="ri-arrow-down-s-line cms-arrow"></i>
    </button>
    <div
      ref="panelRef"
      class="cms-panel"
      :class="{'open-up': openUp}"
      :style="{maxHeight: `${panelMaxHeight}px`}"
      v-show="open && !disabled"
      role="listbox"
      aria-multiselectable="true"
    >
      <label v-for="opt in options" :key="opt.value" class="cms-option" :class="{disabled: isDisabled(opt.value)}">
        <input type="checkbox" :checked="isChecked(opt.value)" :disabled="isDisabled(opt.value)" @change="toggle(opt.value)" />
        <span :dir="ltr ? 'ltr' : 'rtl'">{{ opt.label }}</span>
      </label>
    </div>
    <div v-if="hiddenCount > 0" class="cms-tooltip" :dir="ltr ? 'ltr' : 'rtl'" role="tooltip">
      {{ selectionSummary }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
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
const openUp = ref(false)
const panelMaxHeight = ref(280)
const controlRef = ref(null)
const panelRef = ref(null)
const toFa = toFaDigits
const isChecked = (v) => props.modelValue.includes(v)
const isDisabled = (v) => props.maxSelected > 0 && props.modelValue.length >= props.maxSelected && !props.modelValue.includes(v)
const visibleChips = computed(() => props.modelValue.slice(0, props.maxChips))
const hiddenCount = computed(() => Math.max(0, props.modelValue.length - props.maxChips))
const selectionSummary = computed(() => props.modelValue.map(labelOf).join('، '))

async function updatePlacement() {
  if (!open.value || !controlRef.value || !panelRef.value) return
  await nextTick()
  const rect = controlRef.value.getBoundingClientRect()
  const spaceBelow = window.innerHeight - rect.bottom - 16
  const spaceAbove = rect.top - 16
  const desiredHeight = Math.min(panelRef.value.scrollHeight || 280, 300)
  openUp.value = spaceBelow < desiredHeight && spaceAbove > spaceBelow
  const availableSpace = openUp.value ? spaceAbove : spaceBelow
  panelMaxHeight.value = Math.max(120, Math.min(300, availableSpace - 8))
}

async function openPanel() {
  if (props.disabled) return
  open.value = true
  await updatePlacement()
}

async function togglePanel() {
  if (props.disabled) return
  open.value = !open.value
  if (open.value) await updatePlacement()
}
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

onMounted(() => {
  window.addEventListener('resize', updatePlacement)
  window.addEventListener('scroll', updatePlacement, true)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updatePlacement)
  window.removeEventListener('scroll', updatePlacement, true)
})
</script>

<style scoped>
.cms { position: relative; display: inline-block; width: 100%; min-width: 0; font-family: inherit; }
.cms.disabled { opacity: .6; pointer-events: none; }
.cms-control {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  padding: 9px 14px; border-radius: var(--radius-md); border: 2px solid var(--border);
  width: 100%; min-width: 0; min-height: 48px; overflow: hidden;
  background: var(--surface); cursor: pointer; transition: all .2s;
  color: var(--text-1); font-family: inherit; text-align: right;
}
.cms-control:hover { border-color: var(--color-primary); }
.cms-control:focus-within { outline: 2px solid var(--color-primary-soft); border-color: var(--color-primary); }
.cms-values { display: flex; flex-wrap: nowrap; gap: 6px; flex: 1; min-width: 0; overflow: hidden; }
.cms-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 8px; border-radius: var(--radius-full);
  background: var(--color-primary-soft); color: var(--color-primary);
  max-width: 100%; overflow: hidden; white-space: nowrap;
  font-size: 12px; font-weight: 600; flex: 0 1 auto;
}
.cms-chip i { cursor: pointer; opacity: .7; transition: opacity .2s; }
.cms-chip i:hover { opacity: 1; }
.cms-chip.cms-more { background: var(--surface-muted); color: var(--text-2); cursor: pointer; flex-shrink: 0; }
.cms-placeholder { color: var(--text-3); font-size: 13px; font-weight: 400; }
.cms-arrow { color: var(--text-3); transition: transform .2s; flex-shrink: 0; }
.cms.open .cms-arrow { transform: rotate(180deg); }
.cms-panel {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-md); box-shadow: var(--shadow-3);
  z-index: 700; overflow-y: auto; overscroll-behavior: contain; padding: 6px;
}
.cms-panel.open-up { top: auto; bottom: calc(100% + 6px); }
.cms-option {
  display: flex; align-items: center; gap: 8px; padding: 7px 9px;
  border-radius: var(--radius-sm); cursor: pointer; transition: background .2s;
  font-size: 13px;
}
.cms-option:hover { background: var(--surface-muted); }
.cms-option input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--color-primary); cursor: pointer; }
.cms-option.disabled { opacity: .5; cursor: not-allowed; }
.cms-tooltip {
  position: absolute; right: 0; bottom: calc(100% + 7px); z-index: 520;
  max-width: min(340px, 90vw); padding: 7px 10px;
  border-radius: var(--radius-sm); background: var(--text-1); color: #fff;
  box-shadow: var(--shadow-2); font-size: 11.5px; line-height: 1.7;
  white-space: normal; overflow-wrap: anywhere; pointer-events: none;
  opacity: 0; visibility: hidden; transform: translateY(4px);
  transition: opacity .16s, transform .16s, visibility .16s;
}
.cms:hover .cms-tooltip, .cms:focus-within .cms-tooltip {
  opacity: 1; visibility: visible; transform: translateY(0);
}
.cms.open .cms-tooltip { opacity: 0; visibility: hidden; }
</style>
