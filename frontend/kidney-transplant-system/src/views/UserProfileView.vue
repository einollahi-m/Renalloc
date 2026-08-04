<template>
  <div class="user-profile-page">
    <div class="page-header">
      <div>
        <div class="page-title">پروفایل کاربری</div>
        <div class="page-subtitle">مشخصات حساب و نحوه دریافت اعلان‌ها را مدیریت کنید</div>
      </div>
    </div>

    <section class="profile-settings-card">
      <div class="settings-card-header">
        <div>
          <h2><i class="ri-user-settings-line"></i> مشخصات کاربری</h2>
          <p>اطلاعات پایه حساب هماهنگ‌کننده پیوند</p>
        </div>
        <button v-if="!editing" type="button" class="btn btn-outline" @click="startEditing">
          <i class="ri-edit-line"></i> ویرایش اطلاعات کاربری
        </button>
      </div>

      <div class="profile-identity-strip">
        <div class="profile-user-avatar">{{ profile.fullName.slice(-1) }}</div>
        <div>
          <h3>{{ profile.fullName }}</h3>
          <span>{{ profile.role }}</span>
        </div>
      </div>

      <div v-if="!editing" class="profile-info-grid">
        <div class="profile-info-item"><span>نام و نام خانوادگی</span><strong>{{ profile.fullName }}</strong></div>
        <div class="profile-info-item"><span>سمت سازمانی</span><strong>{{ profile.role }}</strong></div>
        <div class="profile-info-item"><span>ایمیل</span><strong dir="ltr">{{ profile.email }}</strong></div>
        <div class="profile-info-item"><span>شماره تماس</span><strong dir="ltr">{{ profile.phone }}</strong></div>
      </div>

      <div v-else class="profile-edit-form">
        <div class="form-grid">
          <div class="form-group"><label class="form-label">نام و نام خانوادگی</label><input v-model="draft.fullName" class="form-input" /></div>
          <div class="form-group"><label class="form-label">سمت سازمانی</label><input v-model="draft.role" class="form-input" /></div>
          <div class="form-group"><label class="form-label">ایمیل</label><input v-model="draft.email" type="email" dir="ltr" class="form-input" /></div>
          <div class="form-group"><label class="form-label">شماره تماس</label><input v-model="draft.phone" dir="ltr" maxlength="11" class="form-input profile-phone-input" /></div>
        </div>
        <div class="profile-edit-actions">
          <button type="button" class="btn btn-secondary" @click="editing=false">لغو</button>
          <button type="button" class="btn btn-primary" @click="saveProfile"><i class="ri-save-3-line"></i> ذخیره تغییرات</button>
        </div>
      </div>
    </section>

    <section class="profile-settings-card">
      <div class="settings-card-header">
        <div>
          <h2><i class="ri-notification-3-line"></i> تنظیمات اعلان‌ها</h2>
          <p>کانال‌ها و رویدادهایی را که مایل به دریافت آن‌ها هستید انتخاب کنید</p>
        </div>
      </div>

      <div class="notification-settings-grid">
        <section class="notification-channel-card">
          <div class="notification-channel-title"><i class="ri-mail-line"></i><div><h3>اعلان‌های ایمیل</h3><span>ارسال به {{ profile.email }}</span></div></div>
          <label class="notification-option">
            <div><strong>هشدارهای تطابق جدید</strong><span>اطلاع‌رسانی هنگام یافتن تطابق تازه</span></div>
            <input type="checkbox" v-model="notifications.emailNewMatch" />
          </label>
          <label class="notification-option">
            <div><strong>یادآوری تأییدیه‌ها</strong><span>یادآوری تأییدیه‌های پزشکی در انتظار</span></div>
            <input type="checkbox" v-model="notifications.emailApprovals" />
          </label>
        </section>

        <section class="notification-channel-card">
          <div class="notification-channel-title"><i class="ri-notification-badge-line"></i><div><h3>اعلان‌های درون‌برنامه‌ای</h3><span>نمایش اعلان در سامانه</span></div></div>
          <label class="notification-option">
            <div><strong>هشدارهای تطابق</strong><span>نمایش فوری رویدادهای سازگاری‌سنجی</span></div>
            <input type="checkbox" v-model="notifications.inAppMatch" />
          </label>
          <label class="notification-option">
            <div><strong>پیام‌های جدید</strong><span>اطلاع‌رسانی دریافت پیام تازه</span></div>
            <input type="checkbox" v-model="notifications.inAppMessages" />
          </label>
        </section>
      </div>
      <div class="notification-save-row">
        <button type="button" class="btn btn-primary" @click="saveNotifications"><i class="ri-save-3-line"></i> ذخیره تنظیمات اعلان‌ها</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'

const editing = ref(false)
const profile = reactive({
  fullName: 'دکتر محمد کاظمی',
  role: 'هماهنگ‌کننده پیوند',
  email: 'coordinator@demo.com',
  phone: '09121234567'
})
const draft = reactive({ ...profile })
const notifications = reactive({ emailNewMatch: true, emailApprovals: true, inAppMatch: true, inAppMessages: true })

function startEditing() {
  Object.assign(draft, profile)
  editing.value = true
}

function saveProfile() {
  if (!draft.fullName.trim() || !draft.email.trim()) {
    window.toast?.add({ severity: 'warning', summary: 'خطا', detail: 'نام و ایمیل را کامل وارد کنید' })
    return
  }
  Object.assign(profile, draft)
  editing.value = false
  window.toast?.add({ severity: 'success', summary: 'موفق', detail: 'اطلاعات کاربری ذخیره شد' })
}

function saveNotifications() {
  window.toast?.add({ severity: 'success', summary: 'موفق', detail: 'تنظیمات اعلان‌ها ذخیره شد' })
}
</script>

<style scoped>
.user-profile-page { max-width: 1120px; margin-inline: auto; }
.profile-settings-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-xl); padding: 24px; margin-bottom: 20px; box-shadow: var(--shadow-1); }
.settings-card-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.settings-card-header h2 { display: flex; align-items: center; gap: 9px; margin: 0 0 3px; font-size: 17px; }
.settings-card-header h2 i { color: var(--color-primary); font-size: 21px; }
.settings-card-header p { margin: 0; color: var(--text-2); font-size: 12.5px; }
.profile-identity-strip { display: flex; align-items: center; gap: 14px; padding: 16px; border-radius: var(--radius-lg); background: linear-gradient(135deg, var(--color-primary-soft), #eff6ff); margin-bottom: 18px; }
.profile-user-avatar { width: 58px; height: 58px; border-radius: 18px; background: var(--grad-brand); color: #fff; display: grid; place-items: center; font-size: 22px; font-weight: 900; box-shadow: var(--shadow-brand); }
.profile-identity-strip h3 { margin: 0 0 2px; font-size: 16px; }
.profile-identity-strip span { color: var(--text-2); font-size: 12.5px; }
.profile-info-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.profile-info-item { display: flex; flex-direction: column; gap: 3px; padding: 13px 15px; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--surface-ground); }
.profile-info-item span { color: var(--text-3); font-size: 11.5px; }
.profile-info-item strong { font-size: 13px; }
.profile-edit-form { padding-top: 2px; }
.profile-edit-actions, .notification-save-row { display: flex; justify-content: flex-end; gap: 8px; }
.profile-phone-input { max-width: 220px; }
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
.notification-save-row { margin-top: 18px; }
@media (max-width: 768px) {
  .settings-card-header { flex-direction: column; }
  .profile-info-grid, .notification-settings-grid { grid-template-columns: 1fr; }
}
</style>
