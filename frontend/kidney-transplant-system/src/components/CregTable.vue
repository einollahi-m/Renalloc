<template>
  <section v-if="rows?.length" class="creg-card">
    <div class="creg-heading"><div><h3><i class="ri-node-tree"></i> جدول CREG</h3><p>گروه‌های بالقوه مرتبط با Anti-HLA با رنگ نارنجی مشخص شده‌اند.</p></div><div class="legend"><span><i class="exact"></i>Anti-HLA مستقیم</span><span><i class="potential"></i>CREG بالقوه</span></div></div>
    <div class="creg-table"><div class="creg-header"><strong>CREG</strong><strong>Antigens Included</strong></div><div v-for="row in rows" :key="row.name" :class="['creg-row',{active:row.active}]"><strong>{{ row.name }}</strong><div><span v-for="antigen in row.antigens" :key="antigen.name" :class="{exact:antigen.exact,potential:row.active&&!antigen.exact}">{{ antigen.name }}</span></div></div></div>
    <div class="clinical-note"><i class="ri-information-line"></i>CREG یک هشدار بالقوه است؛ تصمیم نهایی همچنان به ارزیابی آزمایشگاه و Cross-Match فیزیکی نیاز دارد.</div>
  </section>
</template>
<script setup>
defineProps({rows:{type:Array,default:()=>[]}})
</script>
<style scoped>
.creg-card{padding:16px;border:1px solid var(--border);border-radius:var(--radius-lg);background:#f0fdfa}.creg-heading{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:12px}.creg-heading h3{margin:0}.creg-heading p{margin:4px 0 0;color:var(--text-2);font-size:12px}.legend{display:flex;gap:10px;flex-wrap:wrap;font-size:11px}.legend span{display:flex;align-items:center;gap:4px}.legend i{width:12px;height:12px;border-radius:3px}.legend .exact{background:#fecaca}.legend .potential{background:#fed7aa}.creg-table{border:1px solid #0f172a;border-radius:7px;overflow:hidden}.creg-header,.creg-row{display:grid;grid-template-columns:75px 1fr;gap:6px;padding:5px;border-bottom:1px solid #cbd5e1}.creg-header{background:#86ef8a;text-align:center}.creg-row:last-child{border-bottom:0}.creg-row>strong{display:grid;place-items:center;background:#86ef8a;border:1px solid #0f172a;border-radius:5px}.creg-row>div{display:flex;gap:5px;flex-wrap:wrap}.creg-row span{padding:4px 7px;border:1px solid #0f172a;border-radius:5px;background:#fff}.creg-row span.potential{background:#fed7aa;border-color:#ea580c}.creg-row span.exact{background:#fecaca;border-color:#dc2626;font-weight:800}.clinical-note{display:flex;gap:7px;margin-top:10px;color:#0f766e;font-size:11px}.clinical-note i{font-size:16px}@media(max-width:600px){.creg-heading{flex-direction:column}.creg-header,.creg-row{grid-template-columns:58px 1fr}}
</style>
