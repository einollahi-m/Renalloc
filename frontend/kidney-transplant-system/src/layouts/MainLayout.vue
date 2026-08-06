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
          <button class="nav-item" :class="{active:$route.path==='/waiting-list/recipients'}" @click="$router.push('/waiting-list/recipients')">
            <i class="ri-user-follow-line nav-icon"></i><span class="nav-label">لیست انتظار گیرندگان</span>
          </button>
          <button class="nav-item" :class="{active:$route.path==='/waiting-list/donors'}" @click="$router.push('/waiting-list/donors')">
            <i class="ri-list-check-2 nav-icon"></i><span class="nav-label">لیست انتظار اهداکنندگان</span>
          </button>
          <button class="nav-item" :class="{active:$route.path==='/matching/deceased-donor'}" @click="$router.push('/matching/deceased-donor')">
            <i class="ri-heart-add-line nav-icon"></i><span class="nav-label">Matching اهداکننده جسد</span>
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
          <button class="icon-btn" title="اعلان‌ها" @click="showNotifications=!showNotifications">
            <i class="ri-notification-3-line"></i>
            <span v-if="unreadNotifications" class="notif-badge">{{ toFa(unreadNotifications) }}</span>
          </button>
          <div v-if="showNotifications" class="notifications-popover">
            <strong>اعلان‌ها</strong>
            <div v-if="!notifications.length" class="notification-empty">اعلان جدیدی ندارید.</div>
            <div v-for="item in notifications.slice(0,8)" :key="item.id" class="notification-item" :class="{unread:!item.read_at}"><i class="ri-information-line"></i><div><b>{{ item.title }}</b><span>{{ item.body }}</span></div></div>
          </div>
          <div class="user-dropdown">
            <button class="icon-btn user-btn" @click="showUserMenu = !showUserMenu" title="پروفایل کاربری">
              <div class="avatar sm">{{ userInitial }}</div>
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
          <input type="text" v-model="lookupNationalId" class="form-input" placeholder="مثال: ۱۲۳۴۵۶۷۸۹۱" @input="normalizeLookup" maxlength="10" inputmode="numeric" />
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
            <div class="lookup-info-item"><div class="label">کد ملی</div><div class="value">{{ toFa(lookupResult.nationalId) }}</div></div>
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
import { ref, computed, onMounted } from 'vue'
import { getCurrentDate, formatFaDate, toFaDigits } from '../utils/date'
import { normalizeNationalId, nationalIdChecker } from '../utils/validation'
import { registryApi } from '../services/api'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { authState, logout: logoutUser } = useAuth()
const collapsed = ref(false)
const currentDates = ref(getCurrentDate())
const lookupModal = ref(false)
const lookupNationalId = ref('')
const lookupError = ref('')
const lookupResult = ref(null)
const showUserMenu = ref(false)
const showNotifications = ref(false)
const notifications = ref([])
const unreadNotifications = ref(0)
let lookupSequence = 0
const toFa = toFaDigits
const userInitial = computed(() => authState.user?.full_name?.trim().charAt(0) || 'ک')

const normalizeLookup = async (e) => {
  const normalizedId = normalizeNationalId(e.target.value)
  const sequence = ++lookupSequence
  lookupNationalId.value = toFa(normalizedId)
  lookupError.value = ''
  lookupResult.value = null
  if (normalizedId.length === 10) {
    if (!nationalIdChecker(normalizedId)) { lookupError.value = 'کد ملی نامعتبر است'; return; }
    try {
      const response = await registryApi.lookupPerson(normalizedId)
      if (sequence === lookupSequence) lookupResult.value = response.person
    } catch (error) {
      if (sequence === lookupSequence) lookupError.value = error?.message || 'جستجوی فرد انجام نشد'
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
  router.push('/profile')
}
const logout = async () => {
  showUserMenu.value = false
  await logoutUser()
  window.toast.add({ severity: 'info', summary: 'خروج', detail: 'با موفقیت از سامانه خارج شدید' })
  router.push('/login')
}
onMounted(async()=>{try{const response=await registryApi.getNotifications();notifications.value=response.notifications;unreadNotifications.value=response.unread}catch{notifications.value=[]}})
setInterval(() => { currentDates.value = getCurrentDate(); }, 60000)
</script>

<style scoped>
.notifications-popover{position:absolute;top:54px;left:70px;width:min(370px,calc(100vw - 30px));max-height:430px;overflow:auto;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:var(--shadow-3);padding:12px;z-index:60}.notifications-popover>strong{display:block;padding:3px 5px 9px}.notification-item{display:flex;gap:8px;padding:9px;border-top:1px solid var(--border);color:var(--text-2)}.notification-item.unread{background:var(--color-primary-soft);color:var(--text-1)}.notification-item i{color:var(--color-primary);font-size:18px}.notification-item div{display:flex;flex-direction:column}.notification-item span{font-size:12px}.notification-empty{padding:20px;text-align:center;color:var(--text-3)}
</style>
