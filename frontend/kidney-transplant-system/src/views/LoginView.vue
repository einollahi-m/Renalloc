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
      <h2 style="font-size:21px;font-weight:900;margin-bottom:6px;">ورود به سامانه</h2>
      <div v-if="error" class="alert alert-danger"><i class="ri-error-warning-line"></i>{{ error }}</div>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">ایمیل یا نام کاربری</label>
          <div class="input-wrapper">
            <input type="text" v-model.trim="form.identifier" class="form-input" style="padding-right:42px;" placeholder="ایمیل یا نام کاربری را وارد کنید." autocomplete="username" required />
            <i class="ri-user-line input-icon"></i>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">رمز عبور</label>
          <div class="input-wrapper">
            <input :type="showPass ? 'text' : 'password'" v-model="form.password" class="form-input" style="padding-right:42px;" autocomplete="current-password" required placeholder="رمز عبور را وارد کنید."/>
            <i class="ri-lock-line input-icon"></i>
            <button type="button" @click="showPass=!showPass" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--text-3);">
              <i :class="showPass ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
            </button>
          </div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
          <label class="checkbox-wrap"><input type="checkbox" v-model="form.remember" /> مرا به خاطر بسپار</label>
          <router-link to="/forgot-password" style="color:var(--color-primary);font-size:13px;text-decoration:none;">فراموشی رمز؟</router-link>
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg" :disabled="loading">
          <i v-if="!loading" class="ri-login-box-line"></i>
          <i v-else class="ri-loader-4-line" style="animation:spin 1s linear infinite;"></i>
          <span>{{ loading ? 'در حال ورود...' : 'ورود به سامانه' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { add: addToast } = useToast()
const { login } = useAuth()

const form = reactive({ identifier: '', password: '', remember: false })
const showPass = ref(false)
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  if (!form.identifier || !form.password) {
    error.value = 'نام کاربری و رمز الزامی است'
    return 
  }
  loading.value = true
  error.value = ''
  try {
    await login(form)
    addToast({ severity: 'success', summary: 'موفق', detail: 'با موفقیت وارد شدید' })
    const redirect = String(router.currentRoute.value.query.redirect || '')
    router.push(redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/dashboard')
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  background: var(--grad-auth);
  position: relative; overflow: hidden;
  padding: 24px;
}
.auth-page::before, .auth-page::after {
  content: ''; position: absolute; border-radius: 50%;
  border: 1.5px solid rgba(255,255,255,.14); pointer-events: none;
}
.auth-page::before { width: 520px; height: 520px; top: -180px; left: -140px; }
.auth-page::after  { width: 380px; height: 380px; bottom: -140px; right: -100px; background: radial-gradient(circle, rgba(255,255,255,.08), transparent 70%); }
.auth-card {
  width: 100%; max-width: 440px;
  background: var(--surface);
  border-radius: var(--radius-xl);
  padding: 38px 40px;
  box-shadow: var(--shadow-3);
  position: relative; z-index: 1;
  animation: slideUp .45s ease;
}
.auth-card::before {
  content: ''; position: absolute; top: 0; right: 24px; left: 24px; height: 4px;
  background: var(--grad-brand); border-radius: 0 0 6px 6px;
}
.auth-brand { display: flex; align-items: center; gap: 13px; margin-bottom: 26px; }
.auth-brand-icon {
  width: 50px; height: 50px; border-radius: 14px;
  background: var(--grad-brand);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 26px; box-shadow: var(--shadow-brand);
}
.auth-brand-title { font-weight: 900; font-size: 17px; }
.auth-brand-sub { font-size: 12px; color: var(--text-3); }
</style>
