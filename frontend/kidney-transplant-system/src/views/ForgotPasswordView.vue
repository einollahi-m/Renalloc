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
      <h2>فراموشی رمز عبور</h2>
      <p class="auth-description">ایمیل حساب خود را وارد کنید تا لینک تعیین رمز جدید برایتان ارسال شود.</p>

      <div v-if="message" class="alert alert-success"><i class="ri-checkbox-circle-line"></i>{{ message }}</div>
      <div v-if="error" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ error }}</div>

      <form v-if="!message" @submit.prevent="submit">
        <div class="form-group">
          <label class="form-label">ایمیل</label>
          <div class="input-wrapper">
            <input v-model.trim="email" type="email" dir="ltr" class="form-input auth-input" placeholder="name@example.com" autocomplete="email" required />
            <i class="ri-mail-line input-icon"></i>
          </div>
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg" :disabled="loading">
          <i :class="loading ? 'ri-loader-4-line spinning' : 'ri-mail-send-line'"></i>
          {{ loading ? 'در حال ارسال...' : 'ارسال لینک بازیابی' }}
        </button>
      </form>
      <router-link class="back-link" to="/login"><i class="ri-arrow-right-line"></i> بازگشت به صفحه ورود</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authApi } from '../services/api'

const email = ref('')
const loading = ref(false)
const error = ref('')
const message = ref('')

async function submit() {
  loading.value = true
  error.value = ''
  try {
    const response = await authApi.requestPasswordReset(email.value)
    message.value = response.message
  } catch (requestError) {
    error.value = requestError.message
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
.auth-input { padding-right: 42px; }
.back-link { display: flex; align-items: center; justify-content: center; gap: 5px; color: var(--color-primary); font-size: 13px; text-decoration: none; margin-top: 20px; }
.spinning { animation: spin 1s linear infinite; }
@media (max-width: 520px) { .auth-card { padding: 32px 24px; } }
</style>
