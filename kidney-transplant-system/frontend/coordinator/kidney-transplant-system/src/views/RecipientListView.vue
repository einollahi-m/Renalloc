<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">گیرندگان</div>
        <div class="page-subtitle">فهرست گیرندگان ثبت‌شده در سامانه</div>
      </div>
      <button class="btn btn-primary" @click="$router.push('/recipients/new')">
        <i class="ri-user-add-line"></i> گیرنده جدید
      </button>
    </div>

    <div class="card mb-4">
      <div class="list-search-row">
        <div class="list-search-input">
          <i class="ri-search-2-line"></i>
          <input type="text" v-model="search" class="form-input" placeholder="جستجو با نام، کد ملی یا شماره تماس…" @keyup.enter="doSearch" />
        </div>
        <button class="btn btn-primary" @click="doSearch"><i class="ri-search-line"></i> جستجو</button>
        <button class="btn btn-secondary" :class="{'btn-filter-active': showFilters}" @click="showFilters=!showFilters">
          <i class="ri-filter-3-line"></i> فیلترها
          <span v-if="activeFilterCount" class="filter-badge">{{ toFa(activeFilterCount) }}</span>
        </button>
      </div>
      <transition name="collapse">
        <div v-if="showFilters" class="list-filters">
          <div class="list-filters-head">
            <span class="list-filters-title"><i class="ri-filter-3-line"></i> فیلترهای جستجو</span>
            <button class="btn btn-sm btn-secondary" @click="clearFilters"><i class="ri-filter-off-line"></i> حذف همه فیلترها</button>
          </div>
          <div class="list-filters-grid">
            <div class="filter-item">
              <label>تابعیت</label>
              <select v-model="filters.citizenship" class="form-select">
                <option value="">همه</option>
                <option value="iranian">ایرانی</option>
                <option value="foreign">غیر ایرانی</option>
              </select>
            </div>
            <div class="filter-item">
              <label>جنسیت</label>
              <select v-model="filters.gender" class="form-select">
                <option value="">همه</option>
                <option value="male">مرد</option>
                <option value="female">زن</option>
              </select>
            </div>
            <div class="filter-item">
              <label>گروه خونی</label>
              <select v-model="filters.bloodType" class="form-select">
                <option value="">همه</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="AB">AB</option>
                <option value="O">O</option>
              </select>
            </div>
            <div class="filter-item">
              <label>وضعیت</label>
              <select v-model="filters.status" class="form-select">
                <option value="">همه</option>
                <option value="active">فعال</option>
                <option value="inactive">غیرفعال</option>
              </select>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <div class="card" style="padding:0; overflow:hidden;">
      <table class="data-table">
        <thead>
          <tr>
            <th>گیرنده</th><th>کد ملی</th><th>گروه خونی</th><th>cPRA</th>
            <th>امتیاز اولویت</th><th>وضعیت</th><th>عملیات</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in filtered" :key="r._id" @click="$router.push('/recipients/'+r._id)" style="cursor:pointer;">
            <td>
              <div class="identity-cell">
                <div class="avatar">{{ r.fullName[0] }}</div>
                <div class="identity-cell-text">
                  <div class="identity-name">{{ r.fullName }}</div>
                  <div class="identity-subline">{{ calculateAge(r.birthDate) }} سال · {{ r.gender === 'male' ? 'مرد' : 'زن' }}</div>
                </div>
              </div>
            </td>
            <td style="font-family:monospace;">{{ r.nationalId }}</td>
            <td><span class="badge badge-info">{{ r.bloodType }}{{ r.rhFactor === 'positive' ? '+' : '-' }}</span></td>
            <td>
              <div class="flex items-center gap-2">
                <div class="progress" style="width:60px;"><div class="progress-bar" :class="r.cpra>70?'danger':r.cpra>30?'warning':'success'" :style="{width:r.cpra+'%'}"></div></div>
                <span class="font-bold">{{ r.cpra }}%</span>
              </div>
            </td>
            <td><span class="badge badge-primary">{{ r.priorityScore }}</span></td>
            <td><span class="badge" :class="r.status==='active'?'badge-success':'badge-secondary'">{{ r.status === 'active' ? 'فعال' : 'غیرفعال' }}</span></td>
            <td @click.stop>
              <div class="flex gap-1">
                <button class="icon-btn" title="مشاهده" @click="$router.push('/recipients/'+r._id)"><i class="ri-eye-line"></i></button>
                <button class="icon-btn" title="ویرایش"><i class="ri-edit-line"></i></button>
              </div>
            </td>
          </tr>
          <tr v-if="!filtered.length">
            <td colspan="7">
              <div class="empty-state" style="border:none; background:transparent;">
                <i class="ri-search-eye-line"></i>
                <h3>نتیجه‌ای یافت نشد</h3>
                <p>عبارت جستجو یا فیلترها را تغییر دهید</p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { toFaDigits } from '../utils/date'

const router = useRouter()
const search = ref('')
const showFilters = ref(false)
const filters = reactive({ citizenship: '', gender: '', bloodType: '', status: '' })
const toFa = toFaDigits

// Mock data for recipients
const mockRecipients = [
  { _id: 'r1', fullName: 'علی احمدی', nationalId: '1234567891', birthDate: '1975-03-15', gender: 'male', bloodType: 'O', rhFactor: 'positive', phone: '09123456789', status: 'active', cpra: 22.5, priorityScore: 78.5, citizenship: 'iranian' },
  { _id: 'r2', fullName: 'مریم حسینی', nationalId: '1111111111', birthDate: '1990-07-22', gender: 'female', bloodType: 'A', rhFactor: 'positive', phone: '09132345678', status: 'active', cpra: 68.5, priorityScore: 85.2, citizenship: 'iranian' },
  { _id: 'r3', fullName: 'رضا محمدی', nationalId: '2222222222', birthDate: '1970-11-08', gender: 'male', bloodType: 'B', rhFactor: 'negative', phone: '09153456789', status: 'active', cpra: 10, priorityScore: 92, citizenship: 'iranian' },
  { _id: 'r4', fullName: 'زهرا کریمی', nationalId: '9876543210', birthDate: '1998-01-30', gender: 'female', bloodType: 'AB', rhFactor: 'positive', phone: '09164567890', status: 'inactive', cpra: 5, priorityScore: 65.8, citizenship: 'iranian' },
  { _id: 'r5', fullName: 'حسین عباسی', nationalId: '5555555555', birthDate: '1965-05-12', gender: 'male', bloodType: 'O', rhFactor: 'negative', phone: '09175678901', status: 'active', cpra: 75, priorityScore: 95.5, citizenship: 'foreign', nationality: 'عراق' }
]

const filtered = computed(() => {
  return mockRecipients.filter(r => {
    if (search.value && !r.fullName.includes(search.value) && !r.nationalId.includes(search.value) && !r.phone.includes(search.value)) return false
    if (filters.citizenship && r.citizenship !== filters.citizenship) return false
    if (filters.gender && r.gender !== filters.gender) return false
    if (filters.bloodType && r.bloodType !== filters.bloodType) return false
    if (filters.status && r.status !== filters.status) return false
    return true
  })
})

const activeFilterCount = computed(() => Object.values(filters).filter(v => v !== '').length)

const doSearch = () => {
  // Show toast with result count
  const event = new CustomEvent('toast', { 
    detail: { severity: 'info', summary: 'جستجو', detail: `${toFa(filtered.value.length)} نتیجه یافت شد` } 
  })
  window.dispatchEvent(event)
}

const clearFilters = () => { 
  filters.citizenship = ''
  filters.gender = '' 
  filters.bloodType = '' 
  filters.status = '' 
}

const calculateAge = (birthDate) => {
  if (!birthDate) return '—'
  return new Date().getFullYear() - new Date(birthDate).getFullYear()
}
</script>

<style scoped>
.filter-item label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text-2);
}
</style>
