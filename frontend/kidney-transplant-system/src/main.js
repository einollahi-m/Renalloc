import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import clickOutside from './directives/clickOutside'
import './styles/main.css'

// ایمپورت کامپوننت‌های گلوبال
import DualDateField from './components/DualDateField.vue'
import CheckboxMultiSelect from './components/CheckboxMultiSelect.vue'
import RoutineTestsModal from './components/RoutineTestsModal.vue'
import ViralTestsModal from './components/ViralTestsModal.vue'

import { useToast } from './composables/useToast'

const app = createApp(App)
app.use(router)
app.directive('click-outside', clickOutside)

// رجیستر کردن کامپوننت‌ها به صورت گلوبال
app.component('dual-date-field', DualDateField)
app.component('checkbox-multi-select', CheckboxMultiSelect)
app.component('routine-tests-modal', RoutineTestsModal)
app.component('viral-tests-modal', ViralTestsModal)

// ایجاد toast گلوبال برای سازگاری با کدهای استخراج شده از front.txt
const { add } = useToast()
window.toast = { add }

window.addEventListener('auth:unauthorized', () => {
  if (router.currentRoute.value.meta.requiresAuth) {
    router.push({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
  }
})

app.mount('#app')
