<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">داشبورد</div>
        <div class="page-subtitle">نمای کلی سامانه</div>
      </div>
    </div>
    <div class="card">
      <div class="empty-state">
        <i class="ri-dashboard-2-line"></i>
        <h3>داشبورد در حال طراحی است</h3>
        <p>شاخص‌ها، نمودارها و گزارش‌های این بخش پس از تعیین نیازمندی‌ها و داده‌های نهایی اضافه خواهند شد.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 22px; gap: 16px;
}
.page-title { font-size: 23px; font-weight: 900; margin-bottom: 3px; }
.page-subtitle { color: var(--text-2); font-size: 13px; }
.card {
  background: var(--surface); border-radius: var(--radius-lg);
  border: 1px solid var(--border); padding: 20px;
  box-shadow: var(--shadow-1); transition: all .2s;
}
.empty-state {
  padding: 46px 20px; text-align: center;
  border: 2px dashed var(--border-strong); border-radius: var(--radius-lg);
  background: var(--surface-muted); transition: border-color .2s;
}
.empty-state:hover { border-color: var(--color-primary-light); }
.empty-state i { font-size: 44px; color: var(--text-3); margin-bottom: 12px; display: block; }
.empty-state h3 { font-size: 15.5px; margin-bottom: 5px; font-weight: 800; }
.empty-state p { font-size: 13px; color: var(--text-2); margin: 0; max-width: 420px; margin-inline: auto; }
</style>
