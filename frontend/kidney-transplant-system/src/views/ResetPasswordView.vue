<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-brand-icon"><i class="ri-heart-pulse-line"></i></div>
        <div>
          <div class="auth-brand-title">سامانه جامع پیوند کلیه</div>
          <div class="auth-brand-sub">رجیستری ملی اهدا و پیوند</div>
        </div>
      </div>
      <h2>تعیین رمز عبور جدید</h2>
      <p class="auth-description">رمز جدید باید دست‌کم ۸ نویسه و غیرقابل حدس باشد.</p>

      <div v-if="message" class="alert alert-success"><i class="ri-checkbox-circle-line"></i>{{ message }}</div>
      <div v-if="error" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ error }}</div>

      <form v-if="hasResetParams && !message" @submit.prevent="submit">
        <div class="form-group">
          <label class="form-label">رمز عبور جدید</label>
          <input v-model="form.newPassword" type="password" dir="ltr" class="form-input" minlength="8" autocomplete="new-password" required />
        </div>
        <div class="form-group">
          <label class="form-label">تکرار رمز عبور جدید</label>
          <input v-model="form.confirmPassword" type="password" dir="ltr" class="form-input" minlength="8" autocomplete="new-password" required />
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg" :disabled="loading">
          <i :class="loading ? 'ri-loader-4-line spinning' : 'ri-lock-password-line'"></i>
          {{ loading ? 'در حال ثبت...' : 'ثبت رمز عبور جدید' }}
        </button>
      </form>
      <router-link class="back-link" to="/login"><i class="ri-arrow-right-line"></i> بازگشت به صفحه ورود</router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { authApi } from '../services/api'

const route = useRoute()
const loading = ref(false)
const error = ref('')
const message = ref('')
const form = reactive({ newPassword: '', confirmPassword: '' })
const hasResetParams = computed(() => Boolean(route.query.uid && route.query.token))

if (!hasResetParams.value) error.value = 'لینک بازیابی کامل نیست؛ دوباره درخواست بازیابی رمز ثبت کنید.'

function firstFieldError(requestError) {
  const errors = requestError.data?.errors
  return errors ? Object.values(errors).flat()[0] : requestError.message
}

async function submit() {
  error.value = ''
  if (form.newPassword !== form.confirmPassword) {
    error.value = 'رمز عبور جدید و تکرار آن یکسان نیستند.'
    return
  }
  loading.value = true
  try {
    const response = await authApi.confirmPasswordReset({
      uid: route.query.uid,
      token: route.query.token,
      new_password: form.newPassword
    })
    message.value = response.message
  } catch (requestError) {
    error.value = firstFieldError(requestError)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--grad-auth); padding: 24px; }
.auth-card { width: 100%; max-width: 440px; background: var(--surface); border-radius: var(--radius-xl); padding: 38px 40px; box-shadow: var(--shadow-3); position: relative; }
.auth-card::before { content: ''; position: absolute; top: 0; right: 24px; left: 24px; height: 4px; background: var(--grad-brand); border-radius: 0 0 6px 6px; }
.auth-brand { display: flex; align-items: center; gap: 13px; margin-bottom: 26px; }
.auth-brand-icon { width: 50px; height: 50px; border-radius: 14px; background: var(--grad-brand); display: grid; place-items: center; color: #fff; font-size: 26px; box-shadow: var(--shadow-brand); }
.auth-brand-title { font-weight: 900; font-size: 17px; }
.auth-brand-sub { font-size: 12px; color: var(--text-3); }
h2 { font-size: 21px; font-weight: 900; margin: 0 0 6px; }
.auth-description { color: var(--text-2); margin: 0 0 20px; font-size: 13px; line-height: 1.8; }
.back-link { display: flex; align-items: center; justify-content: center; gap: 5px; color: var(--color-primary); font-size: 13px; text-decoration: none; margin-top: 20px; }
.spinning { animation: spin 1s linear infinite; }
@media (max-width: 520px) { .auth-card { padding: 32px 24px; } }
</style>
