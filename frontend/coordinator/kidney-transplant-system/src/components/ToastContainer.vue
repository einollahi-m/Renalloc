<template>
  <div class="toast-container">
    <transition-group name="slide">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="t.type">
        <i :class="t.icon" :style="{ color: t.color }"></i>
        <div style="flex:1;">
          <div class="font-bold">{{ t.title }}</div>
          <div class="text-sm text-secondary">{{ t.detail }}</div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { toasts } from '../composables/useToast'
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 78px;
  left: 24px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.toast {
  background: var(--surface);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  box-shadow: var(--shadow-3);
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 280px;
  animation: slideInLeft .3s;
  border-right: 4px solid;
}
.toast.success { border-color: var(--color-success); }
.toast.error { border-color: var(--color-error); }
.toast.warning { border-color: var(--color-warning); }
.toast.info { border-color: var(--color-info); }
</style>
