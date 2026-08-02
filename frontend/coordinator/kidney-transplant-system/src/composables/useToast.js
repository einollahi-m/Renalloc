import { ref } from 'vue'

const toasts = ref([])

export const useToast = () => {
  const add = ({ severity, summary, detail, life = 3500 }) => {
    const iconMap = {
      success: 'ri-check-line',
      error: 'ri-error-warning-line',
      warning: 'ri-alert-line',
      info: 'ri-information-line'
    }
    const colorMap = {
      success: '#10b981',
      error: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6'
    }
    const id = Date.now() + Math.random()
    toasts.value.push({
      id,
      title: summary,
      detail,
      type: severity,
      icon: iconMap[severity],
      color: colorMap[severity]
    })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, life)
  }

  return { toasts, add }
}

export { toasts }
