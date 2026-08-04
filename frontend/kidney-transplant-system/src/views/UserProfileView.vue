<template>
  <div class="user-profile-page">
    <div class="page-header">
      <div>
        <div class="page-title">پروفایل کاربری</div>
        <div class="page-subtitle">مشخصات حساب و رمز عبور خود را مدیریت کنید</div>
      </div>
    </div>

    <section class="profile-settings-card">
      <div class="settings-card-header">
        <div>
          <h2><i class="ri-user-settings-line"></i> مشخصات کاربری</h2>
          <p>اطلاعات حساب هماهنگ‌کننده پیوند ثبت‌شده در سامانه</p>
        </div>
        <button v-if="!editing" type="button" class="btn btn-outline" @click="startEditing">
          <i class="ri-edit-line"></i> ویرایش اطلاعات کاربری
        </button>
      </div>

      <div v-if="loadingProfile" class="profile-loading"><i class="ri-loader-4-line"></i> در حال دریافت اطلاعات...</div>
      <template v-else>
        <div v-if="profileError" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ profileError }}</div>
        <div class="profile-identity-strip">
          <div class="profile-user-avatar">{{ userInitial }}</div>
          <div>
            <h3>{{ profile.full_name || profile.username }}</h3>
            <span>هماهنگ‌کننده پیوند<span v-if="profile.center"> — {{ profile.center.name }}</span></span>
          </div>
        </div>

        <div v-if="!editing" class="profile-info-grid">
          <div class="profile-info-item"><span>نام</span><strong>{{ profile.first_name || '—' }}</strong></div>
          <div class="profile-info-item"><span>نام خانوادگی</span><strong>{{ profile.last_name || '—' }}</strong></div>
          <div class="profile-info-item"><span>کد ملی</span><strong dir="ltr">{{ profile.national_id }}</strong></div>
          <div class="profile-info-item"><span>نام کاربری</span><strong dir="ltr">{{ profile.username }}</strong></div>
          <div class="profile-info-item"><span>جنسیت</span><strong>{{ profile.gender_display }}</strong></div>
          <div class="profile-info-item"><span>ایمیل</span><strong dir="ltr">{{ profile.email }}</strong></div>
          <div class="profile-info-item"><span>شماره همراه</span><strong dir="ltr">{{ profile.mobile_phone }}</strong></div>
          <div class="profile-info-item"><span>مرکز</span><strong>{{ profile.center?.name || 'تعیین نشده' }}</strong></div>
        </div>

        <form v-else class="profile-edit-form" @submit.prevent="saveProfile">
          <div class="form-grid">
            <div class="form-group"><label class="form-label">نام</label><input v-model.trim="draft.first_name" class="form-input" required /></div>
            <div class="form-group"><label class="form-label">نام خانوادگی</label><input v-model.trim="draft.last_name" class="form-input" required /></div>
            <div class="form-group"><label class="form-label">کد ملی</label><input v-model.trim="draft.national_id" dir="ltr" inputmode="numeric" maxlength="10" pattern="[0-9]{10}" class="form-input" required /></div>
            <div class="form-group"><label class="form-label">نام کاربری</label><input v-model.trim="draft.username" dir="ltr" autocomplete="username" class="form-input" required /></div>
            <div class="form-group">
              <label class="form-label">جنسیت</label>
              <select v-model="draft.gender" class="form-select" required>
                <option value="male">مرد</option>
                <option value="female">زن</option>
              </select>
            </div>
            <div class="form-group"><label class="form-label">ایمیل</label><input v-model.trim="draft.email" type="email" dir="ltr" autocomplete="email" class="form-input" required /></div>
            <div class="form-group"><label class="form-label">شماره همراه</label><input v-model.trim="draft.mobile_phone" dir="ltr" inputmode="tel" maxlength="11" pattern="09[0-9]{9}" autocomplete="tel" class="form-input" required /></div>
            <div class="form-group"><label class="form-label">مرکز</label><input :value="profile.center?.name || 'تعیین نشده'" class="form-input" disabled /><small class="field-hint">مرکز فقط توسط مدیر سیستم تغییر می‌کند.</small></div>
          </div>
          <div class="profile-edit-actions">
            <button type="button" class="btn btn-secondary" :disabled="savingProfile" @click="cancelEditing">لغو</button>
            <button type="submit" class="btn btn-primary" :disabled="savingProfile"><i :class="savingProfile ? 'ri-loader-4-line spinning' : 'ri-save-3-line'"></i> {{ savingProfile ? 'در حال ذخیره...' : 'ذخیره تغییرات' }}</button>
          </div>
        </form>
      </template>
    </section>

    <section class="profile-settings-card">
      <div class="settings-card-header">
        <div>
          <h2><i class="ri-notification-3-line"></i> تنظیمات اعلان‌ها</h2>
          <p>کانال‌ها و رویدادهایی را که مایل به دریافت آن‌ها هستید انتخاب کنید</p>
        </div>
      </div>

      <div v-if="notificationError" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ notificationError }}</div>
      <div class="notification-settings-grid">
        <section class="notification-channel-card">
          <div class="notification-channel-title">
            <i class="ri-mail-line"></i>
            <div><h3>اعلان‌های ایمیل</h3><span>ارسال به {{ profile.email || 'ایمیل ثبت‌شده' }}</span></div>
          </div>
          <label class="notification-option">
            <div><strong>هشدارهای تطابق جدید</strong><span>اطلاع‌رسانی هنگام یافتن تطابق تازه</span></div>
            <input v-model="notifications.email_new_match" type="checkbox" :disabled="loadingProfile || savingNotifications" />
          </label>
          <label class="notification-option">
            <div><strong>یادآوری تأییدیه‌ها</strong><span>یادآوری تأییدیه‌های پزشکی در انتظار</span></div>
            <input v-model="notifications.email_approvals" type="checkbox" :disabled="loadingProfile || savingNotifications" />
          </label>
        </section>

        <section class="notification-channel-card">
          <div class="notification-channel-title">
            <i class="ri-notification-badge-line"></i>
            <div><h3>اعلان‌های درون‌برنامه‌ای</h3><span>نمایش اعلان در سامانه</span></div>
          </div>
          <label class="notification-option">
            <div><strong>هشدارهای تطابق</strong><span>نمایش فوری رویدادهای سازگاری‌سنجی</span></div>
            <input v-model="notifications.in_app_match" type="checkbox" :disabled="loadingProfile || savingNotifications" />
          </label>
          <label class="notification-option">
            <div><strong>پیام‌های جدید</strong><span>اطلاع‌رسانی دریافت پیام تازه</span></div>
            <input v-model="notifications.in_app_messages" type="checkbox" :disabled="loadingProfile || savingNotifications" />
          </label>
        </section>
      </div>
      <div class="notification-save-row">
        <button type="button" class="btn btn-primary" :disabled="loadingProfile || savingNotifications" @click="saveNotifications">
          <i :class="savingNotifications ? 'ri-loader-4-line spinning' : 'ri-save-3-line'"></i>
          {{ savingNotifications ? 'در حال ذخیره...' : 'ذخیره تنظیمات اعلان‌ها' }}
        </button>
      </div>
    </section>

    <section class="profile-settings-card password-card">
      <div class="settings-card-header">
        <div>
          <h2><i class="ri-lock-password-line"></i> تغییر رمز عبور</h2>
          <p>برای امنیت حساب، تغییر رمز تنها پس از درخواست شما انجام می‌شود</p>
        </div>
        <button v-if="!showPasswordForm" type="button" class="btn btn-outline" @click="openPasswordForm">
          <i class="ri-key-2-line"></i> درخواست تغییر رمز عبور
        </button>
      </div>
      <div v-if="!showPasswordForm" class="password-request-hint">
        <i class="ri-shield-keyhole-line"></i>
        <span>برای نمایش فرم امن تغییر رمز، ابتدا دکمهٔ درخواست تغییر رمز عبور را بزنید.</span>
      </div>
      <div v-if="showPasswordForm && passwordError" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ passwordError }}</div>
      <form v-if="showPasswordForm" @submit.prevent="changePassword">
        <div class="form-grid password-grid">
          <div class="form-group"><label class="form-label">رمز عبور فعلی</label><input v-model="passwordForm.currentPassword" type="password" dir="ltr" autocomplete="current-password" class="form-input" required /></div>
          <div class="form-group"><label class="form-label">رمز عبور جدید</label><input v-model="passwordForm.newPassword" type="password" dir="ltr" minlength="8" autocomplete="new-password" class="form-input" required /></div>
          <div class="form-group"><label class="form-label">تکرار رمز عبور جدید</label><input v-model="passwordForm.confirmPassword" type="password" dir="ltr" minlength="8" autocomplete="new-password" class="form-input" required /></div>
        </div>
        <div class="profile-edit-actions">
          <button type="button" class="btn btn-secondary" :disabled="savingPassword" @click="closePasswordForm">لغو</button>
          <button type="submit" class="btn btn-primary" :disabled="savingPassword"><i :class="savingPassword ? 'ri-loader-4-line spinning' : 'ri-key-2-line'"></i> {{ savingPassword ? 'در حال تغییر...' : 'تغییر رمز عبور' }}</button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { authApi } from '../services/api'
import { useAuth } from '../composables/useAuth'

const { authState, setUser } = useAuth()
const editing = ref(false)
const loadingProfile = ref(false)
const savingProfile = ref(false)
const savingPassword = ref(false)
const savingNotifications = ref(false)
const showPasswordForm = ref(false)
const profileError = ref('')
const passwordError = ref('')
const notificationError = ref('')
const profile = reactive({})
const draft = reactive({})
const notifications = reactive({
  email_new_match: true,
  email_approvals: true,
  in_app_match: true,
  in_app_messages: true
})
const passwordForm = reactive({ currentPassword: '', newPassword: '', confirmPassword: '' })
const userInitial = computed(() => profile.full_name?.trim().charAt(0) || profile.username?.charAt(0) || 'ک')

function applyProfile(user) {
  Object.assign(profile, user)
  if (user.notification_preferences) {
    Object.assign(notifications, user.notification_preferences)
  }
  setUser(user)
}

function firstRequestError(requestError) {
  const errors = requestError.data?.errors
  return errors ? Object.values(errors).flat()[0] : requestError.message
}

async function loadProfile() {
  if (authState.user) applyProfile(authState.user)
  loadingProfile.value = !authState.user
  profileError.value = ''
  try {
    const { user } = await authApi.getProfile()
    applyProfile(user)
  } catch (requestError) {
    profileError.value = requestError.message
  } finally {
    loadingProfile.value = false
  }
}

function startEditing() {
  Object.assign(draft, {
    national_id: profile.national_id,
    first_name: profile.first_name,
    last_name: profile.last_name,
    username: profile.username,
    gender: profile.gender,
    email: profile.email,
    mobile_phone: profile.mobile_phone
  })
  profileError.value = ''
  editing.value = true
}

function cancelEditing() {
  profileError.value = ''
  editing.value = false
}

async function saveProfile() {
  savingProfile.value = true
  profileError.value = ''
  try {
    const response = await authApi.updateProfile(draft)
    applyProfile(response.user)
    editing.value = false
    window.toast?.add({ severity: 'success', summary: 'موفق', detail: response.message })
  } catch (requestError) {
    profileError.value = firstRequestError(requestError)
  } finally {
    savingProfile.value = false
  }
}

async function saveNotifications() {
  savingNotifications.value = true
  notificationError.value = ''
  try {
    const response = await authApi.updateNotificationPreferences({ ...notifications })
    applyProfile(response.user)
    window.toast?.add({ severity: 'success', summary: 'موفق', detail: response.message })
  } catch (requestError) {
    notificationError.value = firstRequestError(requestError)
  } finally {
    savingNotifications.value = false
  }
}

function openPasswordForm() {
  passwordError.value = ''
  showPasswordForm.value = true
}

function closePasswordForm() {
  passwordError.value = ''
  Object.assign(passwordForm, { currentPassword: '', newPassword: '', confirmPassword: '' })
  showPasswordForm.value = false
}

async function changePassword() {
  passwordError.value = ''
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordError.value = 'رمز عبور جدید و تکرار آن یکسان نیستند.'
    return
  }
  savingPassword.value = true
  try {
    const response = await authApi.changePassword({
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword
    })
    Object.assign(passwordForm, { currentPassword: '', newPassword: '', confirmPassword: '' })
    showPasswordForm.value = false
    window.toast?.add({ severity: 'success', summary: 'موفق', detail: response.message })
  } catch (requestError) {
    passwordError.value = firstRequestError(requestError)
  } finally {
    savingPassword.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.user-profile-page { max-width: 1120px; margin-inline: auto; }
.profile-settings-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-xl); padding: 24px; margin-bottom: 20px; box-shadow: var(--shadow-1); }
.settings-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.settings-card-header h2 { display: flex; align-items: center; gap: 9px; margin: 0 0 3px; font-size: 17px; }
.settings-card-header h2 i { color: var(--color-primary); font-size: 21px; }
.settings-card-header p { margin: 0; color: var(--text-2); font-size: 12.5px; }
.profile-loading { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 180px; color: var(--text-2); }
.profile-loading i, .spinning { animation: spin 1s linear infinite; }
.profile-identity-strip { display: flex; align-items: center; gap: 14px; padding: 16px; border-radius: var(--radius-lg); background: linear-gradient(135deg, var(--color-primary-soft), #eff6ff); margin-bottom: 18px; }
.profile-user-avatar { width: 58px; height: 58px; border-radius: 18px; background: var(--grad-brand); color: #fff; display: grid; place-items: center; font-size: 22px; font-weight: 900; box-shadow: var(--shadow-brand); }
.profile-identity-strip h3 { margin: 0 0 2px; font-size: 16px; }
.profile-identity-strip span { color: var(--text-2); font-size: 12.5px; }
.profile-info-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.profile-info-item { display: flex; flex-direction: column; gap: 3px; padding: 13px 15px; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--surface-ground); }
.profile-info-item span { color: var(--text-3); font-size: 11.5px; }
.profile-info-item strong { font-size: 13px; overflow-wrap: anywhere; }
.profile-edit-form { padding-top: 2px; }
.profile-edit-actions, .notification-save-row { display: flex; justify-content: flex-end; gap: 8px; margin-top: 18px; }
.field-hint { display: block; margin-top: 5px; color: var(--text-3); font-size: 11px; }
.password-card { max-width: 100%; }
.password-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.password-request-hint { display: flex; align-items: center; gap: 10px; padding: 15px 16px; border: 1px dashed var(--border-strong); border-radius: var(--radius-lg); color: var(--text-2); background: var(--surface-ground); font-size: 12.5px; }
.password-request-hint i { color: var(--color-primary); font-size: 22px; }
.notification-settings-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.notification-channel-card { padding: 16px; border: 1px solid var(--border); border-radius: var(--radius-lg); background: var(--surface-ground); }
.notification-channel-title { display: flex; align-items: center; gap: 11px; padding-bottom: 13px; margin-bottom: 4px; border-bottom: 1px solid var(--border); }
.notification-channel-title > i { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 11px; background: var(--color-primary-soft); color: var(--color-primary-dark); font-size: 19px; }
.notification-channel-title h3 { margin: 0; font-size: 14px; }
.notification-channel-title span { color: var(--text-3); font-size: 11px; }
.notification-option { display: flex; justify-content: space-between; align-items: center; gap: 14px; padding: 13px 4px; cursor: pointer; border-bottom: 1px solid var(--border); }
.notification-option:last-child { border-bottom: 0; }
.notification-option div { display: flex; flex-direction: column; }
.notification-option strong { font-size: 13px; }
.notification-option span { font-size: 11.5px; color: var(--text-2); }
.notification-option input { appearance: none; width: 38px; height: 22px; flex-shrink: 0; border-radius: 20px; background: var(--border-strong); position: relative; cursor: pointer; transition: background .2s; }
.notification-option input::after { content: ''; position: absolute; top: 3px; right: 3px; width: 16px; height: 16px; border-radius: 50%; background: #fff; box-shadow: var(--shadow-1); transition: transform .2s; }
.notification-option input:checked { background: var(--color-primary); }
.notification-option input:checked::after { transform: translateX(-16px); }
.notification-option input:disabled { cursor: wait; opacity: .6; }
@media (max-width: 900px) { .password-grid { grid-template-columns: 1fr; } }
@media (max-width: 768px) {
  .settings-card-header { flex-direction: column; }
  .profile-info-grid, .notification-settings-grid { grid-template-columns: 1fr; }
}
</style>
