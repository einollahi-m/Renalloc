<template>
  <div v-if="!tests.length" class="empty-state compact-empty-state">
    <i :class="icon"></i>
    <h3>{{ emptyTitle }}</h3>
  </div>
  <div v-else class="result-batches">
    <article v-for="group in groupedTests" :key="group.date" class="result-batch">
      <header class="result-batch-header">
        <div class="result-batch-date">
          <i class="ri-calendar-check-line"></i>
          <span>{{ formatFaDate(group.date) }}</span>
          <span class="badge badge-secondary">{{ toFa(group.items.length) }} مورد</span>
        </div>
        <button type="button" class="record-action edit" title="ویرایش آزمایش‌های این تاریخ" @click="$emit('edit', group.date)">
          <i class="ri-edit-line"></i>
        </button>
      </header>
      <div class="result-badges">
        <span v-for="test in group.items" :key="test.category + test.testName" class="test-result-badge">
          <span v-if="showCategory" class="test-result-category">{{ test.category }}</span>
          <strong dir="ltr">{{ test.testName }}</strong>
          <span class="test-result-value" dir="ltr">{{ test.value }}</span>
          <button type="button" title="ویرایش" @click="$emit('edit', group.date)"><i class="ri-edit-line"></i></button>
          <button type="button" class="delete" title="حذف" @click="$emit('remove', test)"><i class="ri-close-line"></i></button>
        </span>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatFaDate, toFaDigits } from '../utils/date'

const props = defineProps({
  tests: { type: Array, default: () => [] },
  showCategory: { type: Boolean, default: false },
  emptyTitle: { type: String, default: 'آزمایشی ثبت نشده است' },
  icon: { type: String, default: 'ri-flask-line' }
})

defineEmits(['edit', 'remove'])

const toFa = toFaDigits
const groupedTests = computed(() => {
  const groups = new Map()
  props.tests.forEach(test => {
    if (!groups.has(test.testDate)) groups.set(test.testDate, [])
    groups.get(test.testDate).push(test)
  })
  return [...groups.entries()].map(([date, items]) => ({ date, items }))
})
</script>
