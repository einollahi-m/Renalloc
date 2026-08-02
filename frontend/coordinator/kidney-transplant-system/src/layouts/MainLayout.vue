<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{collapsed: collapsed}">
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-icon"><i class="ri-heart-pulse-line"></i></div>
          <div class="brand-text">سامانه پیوند کلیه</div>
        </div>
        <button class="toggle-btn" @click="collapsed = !collapsed" title="جمع/باز کردن منو">
          <i :class="collapsed ? 'ri-menu-unfold-line' : 'ri-menu-fold-line'"></i>
        </button>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="nav-section-title">منوی اصلی</div>
          <button class="nav-item" :class="{active: $route.name === 'dashboard'}" @click="$router.push('/dashboard')">
            <i class="ri-dashboard-2-line nav-icon"></i><span class="nav-label">داشبورد</span>
          </button>
          <button class="nav-item" :class="{active: $route.path.startsWith('/recipients')}" @click="$router.push('/recipients')">
            <i class="ri-user-heart-line nav-icon"></i><span class="nav-label">گیرندگان</span>
          </button>
          <button class="nav-item" :class="{active: $route.path.startsWith('/donors')}" @click="$router.push('/donors')">
            <i class="ri-hand-heart-line nav-icon"></i><span class="nav-label">اهداکنندگان</span>
          </button>
          <button class="nav-item" :class="{active: $route.path.startsWith('/matching')}" @click="$router.push('/matching')">
            <i class="ri-exchange-2-line nav-icon"></i><span class="nav-label">سازگاری‌سنجی</span>
          </button>
        </div>
      </nav>
    </aside>

    <!-- Main Content -->
    <div class="main" :class="{collapsed: collapsed}">
      <header class="topbar">
        <div class="topbar-user">
          <div class="avatar sm">{{ userInitial }}</div>
          <div class="topbar-user-text">
            <span class="topbar-user-name">{{ user.fullName }}</span>
            <span class="topbar-user-role">{{ user.role }}</span>
          </div>
        </div>
        <div class="topbar-actions">
          <div class="topbar-date">
            <span class="topbar-date-j">{{ currentDates.jalali }}</span>
            <span class="topbar-date-g" dir="ltr">{{ currentDates.gregorian }}</span>
          </div>
        </div>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getCurrentDate } from '../utils/date'

const collapsed = ref(false)
const user = { fullName: 'دکتر محمد کاظمی', role: 'هماهنگ‌کننده پیوند' }
const userInitial = computed(() => user.fullName[user.fullName.length - 1])
const currentDates = ref(getCurrentDate())

setInterval(() => {
  currentDates.value = getCurrentDate()
}, 60000)
</script>

<style scoped>
.app-shell {
  min-height: 100vh; display: flex;
  background: radial-gradient(1100px 420px at 88% -8%, rgba(14,165,233,.06), transparent 60%), var(--surface-ground);
}
.sidebar {
  width: 260px; background: var(--surface);
  border-left: 1px solid var(--border);
  display: flex; flex-direction: column;
  position: fixed; right: 0; top: 0; bottom: 0; z-index: 40;
  transition: width .3s ease; overflow: hidden;
}
.sidebar.collapsed { width: 72px; }
.sidebar.collapsed .nav-label,
.sidebar.collapsed .brand-text,
.sidebar.collapsed .nav-section-title { display: none; }
.sidebar-header {
  padding: 15px 16px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
}
.brand { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.brand-icon {
  width: 38px; height: 38px; background: var(--grad-brand);
  border-radius: var(--radius-md);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 22px; box-shadow: var(--shadow-brand); flex-shrink: 0;
}
.brand-text { font-weight: 800; font-size: 14.5px; white-space: nowrap; }
.toggle-btn {
  width: 32px; height: 32px; border-radius: var(--radius-sm);
  background: var(--surface-muted); border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  color: var(--text-2); transition: all .2s;
}
.toggle-btn:hover { background: var(--color-primary-soft); color: var(--color-primary-dark); }
.sidebar-nav { flex: 1; overflow-y: auto; padding: 10px; }
.nav-section { margin-bottom: 12px; }
.nav-section-title {
  padding: 0 12px 6px; font-size: 11px; font-weight: 700;
  color: var(--text-3); letter-spacing: .5px;
}
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 12px; border-radius: var(--radius-sm);
  color: var(--text-2); cursor: pointer; font-family: inherit;
  background: transparent; border: none; width: 100%; text-align: right;
  transition: all .2s; font-weight: 500; margin-bottom: 2px;
}
.nav-item:hover { background: var(--surface-muted); color: var(--color-primary); }
.nav-item.active {
  background: linear-gradient(135deg, var(--color-primary-soft) 0%, #cffafe 100%);
  color: var(--color-primary-dark); font-weight: 700; position: relative;
}
.nav-item.active::before {
  content: ''; position: absolute; right: 0; top: 20%; bottom: 20%;
  width: 3px; background: var(--color-primary); border-radius: 2px;
}
.nav-icon { font-size: 20px; flex-shrink: 0; }
.nav-label { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.main {
  flex: 1; margin-right: 260px;
  display: flex; flex-direction: column; min-height: 100vh;
  transition: margin-right .3s ease;
}
.main.collapsed { margin-right: 72px; }
.topbar {
  height: 62px; background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; position: sticky; top: 0; z-index: 30; gap: 16px;
}
.topbar-user { display: flex; align-items: center; gap: 10px; }
.topbar-user-text { display: flex; flex-direction: column; line-height: 1.35; }
.topbar-user-name { font-size: 13px; font-weight: 700; }
.topbar-user-role { font-size: 11.5px; color: var(--text-3); }
.topbar-actions { display: flex; align-items: center; gap: 10px; }
.topbar-date { display: flex; flex-direction: column; align-items: flex-start; line-height: 1.4; padding: 0 2px; }
.topbar-date-j { font-size: 12.5px; font-weight: 700; color: var(--text-1); }
.topbar-date-g { font-size: 11px; font-weight: 500; color: var(--text-3); }
.content { padding: 24px; flex: 1; }
.avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: var(--grad-brand); color: #fff;
  display: inline-flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.avatar.sm { width: 32px; height: 32px; font-size: 12px; }
</style>
