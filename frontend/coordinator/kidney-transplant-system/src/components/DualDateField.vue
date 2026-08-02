<template>
  <div class="dp" :class="{open}" v-click-outside="close">
    <label class="form-label" v-if="label">{{ label }}</label>
    <div class="dp-mode">
      <button type="button" class="dp-mode-btn" :class="{active: mode==='jalali'}" @click="setMode('jalali')">شمسی (جلالی)</button>
      <button type="button" class="dp-mode-btn" :class="{active: mode==='gregorian'}" @click="setMode('gregorian')">میلادی</button>
    </div>
    <div class="dp-field" @click="togglePanel" tabindex="0" @keydown.enter.prevent="togglePanel" @keydown.esc="open=false">
      <i class="ri-calendar-2-line dp-field-icon"></i>
      <input class="dp-display" :value="displayValue" readonly :placeholder="mode==='jalali' ? '۱۴۰۵/۰۵/۱۰' : '2026-08-01'" :dir="mode==='jalali' ? 'rtl' : 'ltr'" />
      <button v-if="modelValue" type="button" class="dp-clear" @click.stop="clear" title="پاک کردن"><i class="ri-close-circle-line"></i></button>
      <i class="ri-arrow-down-s-line dp-caret" :class="{rotated: open}"></i>
    </div>
    <div class="dp-equiv" v-if="modelValue">
      <span v-if="mode==='jalali'">معادل میلادی: <b dir="ltr">{{ modelValue }}</b></span>
      <span v-else>معادل شمسی: <b>{{ jalaliDisplay }}</b></span>
    </div>
    <transition name="dp-pop">
      <div v-if="open" class="dp-panel">
        <div class="dp-nav">
          <button type="button" class="dp-nav-btn" @click="prevMonth" title="ماه قبل"><i class="ri-arrow-right-s-line"></i></button>
          <select class="dp-select" v-model="viewM">
            <option v-for="(m,i) in monthNames" :key="i" :value="i+1">{{ m }}</option>
          </select>
          <select class="dp-select" v-model="viewY">
            <option v-for="y in yearRange" :key="y" :value="y">{{ mode==='jalali' ? toFa(y) : y }}</option>
          </select>
          <button type="button" class="dp-nav-btn" @click="nextMonth" title="ماه بعد"><i class="ri-arrow-left-s-line"></i></button>
        </div>
        <div class="dp-weekdays">
          <span v-for="(w,i) in weekdays" :key="i" :class="{'dp-weekday-holiday': i===6}">{{ w }}</span>
        </div>
        <div class="dp-grid">
          <button v-for="(c,i) in cells" :key="i" type="button" class="dp-day"
            :class="{muted: !c.inMonth, today: c.isToday, selected: c.iso===modelValue}"
            @click="pick(c)">{{ c.label }}</button>
        </div>
        <div class="dp-footer">
          <button type="button" class="dp-today-btn" @click="pickToday"><i class="ri-calendar-check-line"></i> امروز</button>
          <button type="button" class="dp-clear-btn" @click="clear">پاک کردن</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { gregorianToJalali, jalaliToGregorian, JALALI_MONTHS, GREGORIAN_MONTHS_FA, WEEKDAY_LETTERS, toFaDigits, pad2 } from '../utils/date'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const mode = ref('jalali')
const open = ref(false)
const viewY = ref(1405)
const viewM = ref(5)
const toFa = toFaDigits

const isoOf = (gy, gm, gd) => `${gy}-${pad2(gm)}-${pad2(gd)}`
const todayIso = () => { const n = new Date(); return isoOf(n.getFullYear(), n.getMonth() + 1, n.getDate()) }

const jalaliDisplay = computed(() => {
  if (!props.modelValue || !/^\d{4}-\d{2}-\d{2}$/.test(props.modelValue)) return ''
  const [gy, gm, gd] = props.modelValue.split('-').map(Number)
  const j = gregorianToJalali(gy, gm, gd)
  return `${toFa(j.jy)}/${toFa(j.jm)}/${toFa(j.jd)}`
})

const displayValue = computed(() => mode.value === 'jalali' ? jalaliDisplay.value : (props.modelValue || ''))

function syncView() {
  const base = (props.modelValue && /^\d{4}-\d{2}-\d{2}$/.test(props.modelValue)) ? props.modelValue : todayIso()
  const [gy, gm, gd] = base.split('-').map(Number)
  if (mode.value === 'jalali') {
    const j = gregorianToJalali(gy, gm, gd)
    viewY.value = j.jy; viewM.value = j.jm
  } else {
    viewY.value = gy; viewM.value = gm
  }
}

function togglePanel() { if (open.value) { open.value = false } else { syncView(); open.value = true } }
function close() { open.value = false }
function setMode(m) { mode.value = m; if (open.value) syncView() }

const cells = computed(() => {
  const out = []
  let firstG
  if (mode.value === 'jalali') firstG = jalaliToGregorian(viewY.value, viewM.value, 1)
  else firstG = { gy: viewY.value, gm: viewM.value, gd: 1 }
  const firstDate = new Date(firstG.gy, firstG.gm - 1, firstG.gd)
  const offset = (firstDate.getDay() + 1) % 7
  const start = new Date(firstDate)
  start.setDate(start.getDate() - offset)
  const tIso = todayIso()
  for (let i = 0; i < 42; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    const gy = d.getFullYear(), gm = d.getMonth() + 1, gd = d.getDate()
    const iso = isoOf(gy, gm, gd)
    let inMonth, label
    if (mode.value === 'jalali') {
      const j = gregorianToJalali(gy, gm, gd)
      inMonth = (j.jy === viewY.value && j.jm === viewM.value)
      label = toFa(j.jd)
    } else {
      inMonth = (gm === viewM.value)
      label = String(gd)
    }
    out.push({ iso, label, inMonth, isToday: iso === tIso })
  }
  return out
})

const monthNames = computed(() => mode.value === 'jalali' ? JALALI_MONTHS : GREGORIAN_MONTHS_FA)
const yearRange = computed(() => {
  const arr = []
  if (mode.value === 'jalali') { for (let y = 1300; y <= 1500; y++) arr.push(y) }
  else { for (let y = 1900; y <= 2100; y++) arr.push(y) }
  return arr
})
const weekdays = WEEKDAY_LETTERS

function pick(c) { emit('update:modelValue', c.iso); open.value = false }
function pickToday() { emit('update:modelValue', todayIso()); open.value = false }
function clear() { emit('update:modelValue', '') }
function prevMonth() { if (viewM.value === 1) { viewM.value = 12; viewY.value-- } else viewM.value-- }
function nextMonth() { if (viewM.value === 12) { viewM.value = 1; viewY.value++ } else viewM.value++ }
</script>

<style scoped>
.dp { position: relative; width: 100%; max-width: 220px; }
.dp-mode { display: inline-flex; background: var(--surface-muted); border-radius: 9px; padding: 3px; gap: 2px; margin-bottom: 8px; }
.dp-mode-btn {
  border: none; background: transparent; padding: 5px 18px; border-radius: 7px;
  font-family: inherit; font-size: 12px; font-weight: 600; color: var(--text-2);
  cursor: pointer; transition: all .2s;
}
.dp-mode-btn.active { background: var(--color-primary); color: #fff; box-shadow: 0 2px 6px rgba(14,165,233,.35); }
.dp-field {
  display: flex; align-items: center; gap: 8px;
  border: 2px solid var(--border); border-radius: var(--radius-md);
  padding: 9px 12px; background: var(--surface); cursor: pointer; transition: all .2s;
}
.dp-field:hover { border-color: var(--color-primary-light); }
.dp.open .dp-field { border-color: var(--color-primary); box-shadow: 0 0 0 4px rgba(14,165,233,.12); }
.dp-field-icon { color: var(--color-primary); font-size: 18px; }
.dp-display {
  flex: 1; min-width: 0; border: none; background: transparent; outline: none;
  text-align: center; font-family: inherit; font-size: 14px; font-weight: 700;
  color: var(--text-1); cursor: pointer;
}
.dp-display::placeholder { color: var(--text-3); font-weight: 400; }
.dp-clear { border: none; background: transparent; cursor: pointer; color: var(--text-3); font-size: 17px; padding: 0; line-height: 1; transition: color .2s; }
.dp-clear:hover { color: var(--color-error); }
.dp-caret { color: var(--text-3); transition: transform .2s; }
.dp-caret.rotated { transform: rotate(180deg); }
.dp-equiv { font-size: 11.5px; color: var(--text-3); margin-top: 5px; }
.dp-equiv b { color: var(--text-2); font-weight: 600; }
.dp-panel {
  position: absolute; top: calc(100% + 6px); right: 0; width: 302px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); box-shadow: var(--shadow-3);
  z-index: 500; padding: 12px;
}
.dp-nav { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }
.dp-nav-btn {
  width: 30px; height: 30px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: var(--surface-muted);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: var(--text-2); transition: all .2s; flex-shrink: 0;
}
.dp-nav-btn:hover { background: var(--color-primary); border-color: var(--color-primary); color: #fff; }
.dp-select {
  flex: 1; padding: 6px 8px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface); font-family: inherit; font-size: 12.5px; font-weight: 600;
  cursor: pointer; outline: none; color: var(--text-1);
}
.dp-select:focus { border-color: var(--color-primary); }
.dp-weekdays { display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; margin-bottom: 4px; }
.dp-weekdays span { font-size: 11px; font-weight: 700; color: var(--text-3); padding: 4px 0; }
.dp-weekday-holiday { color: var(--color-error) !important; }
.dp-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
.dp-day {
  aspect-ratio: 1; border: none; background: transparent; border-radius: 9px;
  font-family: inherit; font-size: 13px; font-weight: 500; cursor: pointer;
  color: var(--text-1); transition: all .15s;
  display: flex; align-items: center; justify-content: center;
}
.dp-day:hover { background: var(--color-primary-soft); color: var(--color-primary-dark); transform: scale(1.1); }
.dp-day.muted { color: var(--text-3); opacity: .45; }
.dp-day.today { border: 1.5px solid var(--color-primary); font-weight: 800; }
.dp-day.selected { background: var(--grad-brand); color: #fff; font-weight: 700; box-shadow: var(--shadow-brand); }
.dp-day.selected:hover { color: #fff; }
.dp-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border); }
.dp-today-btn {
  display: inline-flex; align-items: center; gap: 6px;
  border: none; background: var(--color-primary-soft); color: var(--color-primary-dark);
  padding: 6px 14px; border-radius: var(--radius-sm);
  font-family: inherit; font-size: 12px; font-weight: 700; cursor: pointer; transition: all .2s;
}
.dp-today-btn:hover { background: var(--color-primary); color: #fff; }
.dp-clear-btn {
  border: none; background: transparent; color: var(--text-3);
  font-family: inherit; font-size: 12px; font-weight: 600; cursor: pointer; transition: color .2s;
}
.dp-clear-btn:hover { color: var(--color-error); }
.dp-pop-enter-active, .dp-pop-leave-active { transition: all .18s ease; transform-origin: top center; }
.dp-pop-enter-from, .dp-pop-leave-to { opacity: 0; transform: translateY(-6px) scale(.97); }
</style>
