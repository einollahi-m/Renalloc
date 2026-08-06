<template>
  <div v-if="pagination.pages>1" class="pagination-controls">
    <button class="btn btn-secondary btn-sm" :disabled="!pagination.has_previous" @click="$emit('change',pagination.page-1)"><i class="ri-arrow-right-s-line"></i> قبلی</button>
    <span>صفحه {{ toFa(pagination.page) }} از {{ toFa(pagination.pages) }} · {{ toFa(pagination.count) }} رکورد</span>
    <button class="btn btn-secondary btn-sm" :disabled="!pagination.has_next" @click="$emit('change',pagination.page+1)">بعدی <i class="ri-arrow-left-s-line"></i></button>
  </div>
</template>
<script setup>
import { toFaDigits } from '../utils/date'
defineProps({pagination:{type:Object,default:()=>({page:1,pages:1,count:0,has_next:false,has_previous:false})}})
defineEmits(['change'])
const toFa=toFaDigits
</script>
<style scoped>
.pagination-controls{display:flex;align-items:center;justify-content:center;gap:14px;padding:14px;border-top:1px solid var(--border);background:var(--surface)}.pagination-controls span{color:var(--text-2);font-size:12px}@media(max-width:520px){.pagination-controls{gap:8px}.pagination-controls span{font-size:10px}}
</style>
