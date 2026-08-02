<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{collapsed:collapsed}">
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-icon"><i class="ri-heart-pulse-line"></i></div>
          <div class="brand-text">سامانه پیوند کلیه</div>
        </div>
        <button class="toggle-btn" @click="collapsed=!collapsed" title="جمع/باز کردن منو">
          <i :class="collapsed ? 'ri-menu-unfold-line' : 'ri-menu-fold-line'"></i>
        </button>
      </div>
      <div class="lookup-section">
        <button class="lookup-btn" @click="openLookupModal">
          <i class="ri-search-2-line" style="font-size:18px;"></i>
          <span>استعلام با کد ملی</span>
        </button>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="nav-section-title">منوی اصلی</div>
          <button class="nav-item" :class="{active:$route.name==='dashboard'}" @click="$router.push('/dashboard')">
            <i class="ri-dashboard-2-line nav-icon"></i><span class="nav-label">داشبورد</span>
          </button>
          <button class="nav-item" :class="{active:$route.path.startsWith('/recipients')}" @click="$router.push('/recipients')">
            <i class="ri-user-heart-line nav-icon"></i><span class="nav-label">گیرندگان</span>
          </button>
          <button class="nav-item" :class="{active:$route.path.startsWith('/donors')}" @click="$router.push('/donors')">
            <i class="ri-hand-heart-line nav-icon"></i><span class="nav-label">اهداکنندگان</span>
          </button>
          <button class="nav-item" :class="{active:$route.path.startsWith('/matching')}" @click="$router.push('/matching')">
            <i class="ri-exchange-2-line nav-icon"></i><span class="nav-label">سازگاری‌سنجی</span>
          </button>
          <button class="nav-item" :class="{active:$route.path==='/waiting-list/recipients'}" @click="$router.push('/waiting-list/recipients')">
            <i class="ri-list-check-2 nav-icon"></i><span class="nav-label">لیست انتظار گیرندگان</span>
          </button>
        </div>
      </nav>
    </aside>

    <div class="main" :class="{collapsed:collapsed}">
      <header class="topbar">
        <div class="topbar-actions">
          <div class="topbar-date">
            <span class="topbar-date-j">{{ currentDates.jalali }}</span>
            <span class="topbar-date-g" dir="ltr">{{ currentDates.gregorian }}</span>
          </div>
          <div class="topbar-divider"></div>
          <button class="icon-btn" title="اعلان‌ها">
            <i class="ri-notification-3-line"></i>
            <span class="notif-badge">3</span>
          </button>
          <div class="user-dropdown">
            <button class="icon-btn user-btn" @click="showUserMenu = !showUserMenu" title="پروفایل کاربری">
              <div class="avatar sm">{{ user.fullName[user.fullName.length - 4] }}</div>
              <i class="ri-arrow-down-s-line"></i>
            </button>
            <div v-if="showUserMenu" class="dropdown-menu" @click.self="showUserMenu = false">
              <button class="dropdown-item" @click="goToProfile"><i class="ri-user-line"></i> پروفایل کاربری</button>
              <button class="dropdown-item" @click="logout"><i class="ri-logout-box-line"></i> خروج از سیستم</button>
            </div>
          </div>
        </div>
      </header>
      <main class="content">
        <router-view v-slot="{Component}">
          <transition name="slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- National ID Lookup Modal -->
    <div v-if="lookupModal" class="modal-overlay" @click.self="lookupModal=false">
      <div class="modal">
        <div class="modal-header">
          <h3>استعلام با کد ملی</h3>
          <button class="modal-close" @click="lookupModal=false"><i class="ri-close-line"></i></button>
        </div>
        <div v-if="lookupError" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ lookupError }}</div>
        <div class="form-group">
          <label class="form-label">کد ملی (۱۰ رقم)</label>
          <input type="text" v-model="lookupNationalId" class="form-input" placeholder="مثال: 1234567891" @input="normalizeLookup" maxlength="10" inputmode="numeric" />
          <div v-if="lookupNationalId && lookupNationalId.length < 10" class="form-error text-xs">کد ملی باید ۱۰ رقم باشد</div>
        </div>
        <div v-if="lookupResult" class="lookup-result">
          <div class="lookup-result-header">
            <i class="ri-check-double-line" style="color:var(--color-success);font-size:24px;"></i>
            <div>
              <div class="font-bold">{{ lookupResult.fullName }}</div>
              <div class="text-sm text-secondary">{{ lookupResult.type === 'recipient' ? 'گیرنده' : 'اهداکننده' }} پیدا شد</div>
            </div>
          </div>
          <div class="lookup-info">
            <div class="lookup-info-item"><div class="label">کد ملی</div><div class="value">{{ lookupResult.nationalId }}</div></div>
            <div class="lookup-info-item"><div class="label">گروه خونی</div><div class="value">{{ lookupResult.bloodType }}{{ lookupResult.rhFactor === 'positive' ? '+' : '-' }}</div></div>
            <div class="lookup-info-item"><div class="label">جنسیت</div><div class="value">{{ lookupResult.gender === 'male' ? 'مرد' : 'زن' }}</div></div>
            <div class="lookup-info-item"><div class="label">تاریخ تولد</div><div class="value">{{ formatFaDate(lookupResult.birthDate) }}</div></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="lookupModal=false">لغو</button>
          <button class="btn btn-primary" @click="viewProfile" :disabled="!lookupResult"><i class="ri-eye-line"></i> نمایش پرونده</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getCurrentDate, formatFaDate } from '../utils/date'
import { normalizeNationalId, nationalIdChecker } from '../utils/validation'
import { mockRecipients, mockDonors } from '../data/mockData'
import { useRouter } from 'vue-router'

const router = useRouter()
const collapsed = ref(false)
const currentDates = ref(getCurrentDate())
const lookupModal = ref(false)
const lookupNationalId = ref('')
const lookupError = ref('')
const lookupResult = ref(null)
const showUserMenu = ref(false)
const user = { fullName: 'دکتر محمد کاظمی', role: 'هماهنگ‌کننده پیوند' }

const normalizeLookup = (e) => {
  lookupNationalId.value = normalizeNationalId(e.target.value)
  lookupError.value = ''
  lookupResult.value = null
  if (lookupNationalId.value.length === 10) {
    if (!nationalIdChecker(lookupNationalId.value)) { lookupError.value = 'کد ملی نامعتبر است'; return; }
    const found = mockRecipients.find(r => r.nationalId === lookupNationalId.value)
    if (found) { lookupResult.value = { ...found, type: 'recipient' }; }
    else {
      const donorFound = mockDonors.find(d => d.nationalId === lookupNationalId.value)
      if (donorFound) lookupResult.value = { ...donorFound, type: 'donor' };
      else lookupError.value = 'فردی با این کد ملی یافت نشد'
    }
  }
}
const viewProfile = () => {
  if (!lookupResult.value) return
  const type = lookupResult.value.type
  const id = lookupResult.value._id
  lookupModal.value = false
  router.push(type === 'recipient' ? `/recipients/${id}` : `/donors/${id}`)
}
const openLookupModal = () => {
  lookupNationalId.value = ''
  lookupError.value = ''
  lookupResult.value = null
  lookupModal.value = true
}
const goToProfile = () => {
  showUserMenu.value = false
  // TODO: navigate to user profile page
  window.toast.add({ severity: 'info', summary: 'اطلاعات', detail: 'صفحه پروفایل کاربری به زودی اضافه می‌شود' })
}
const logout = () => {
  showUserMenu.value = false
  // TODO: implement logout logic
  window.toast.add({ severity: 'info', summary: 'خروج', detail: 'عملیات خروج از سیستم' })
}
setInterval(() => { currentDates.value = getCurrentDate(); }, 60000)
</script>
