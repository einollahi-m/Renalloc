<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">اهداکنندگان</div>
        <div class="page-subtitle">فهرست اهداکنندگان ثبت‌شده در سامانه</div>
      </div>
      <button class="btn btn-primary" @click="$router.push('/donors/new')">
        <i class="ri-user-add-line"></i> اهداکننده جدید
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
              <label>نوع اهداکننده</label>
              <select v-model="filters.donorType" class="form-select">
                <option value="">همه</option>
                <option value="living_related">زنده خویشاوند</option>
                <option value="living_unrelated">زنده غیر خویشاوند</option>
                <option value="deceased">فوت شده</option>
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
          </div>
        </div>
      </transition>
    </div>

    <div class="card" style="padding:0; overflow:hidden;">
      <table class="data-table">
        <thead>
          <tr><th>اهداکننده</th><th>نوع</th><th>گروه خونی</th><th>نسبت</th><th>وضعیت</th><th>عملیات</th></tr>
        </thead>
        <tbody>
          <tr v-for="d in filtered" :key="d._id" @click="$router.push('/donors/'+d._id)" style="cursor:pointer;">
            <td>
              <div class="identity-cell">
                <div class="avatar donor">{{ d.fullName[0] }}</div>
                <div class="identity-cell-text">
                  <div class="identity-name">{{ d.fullName }}</div>
                  <div class="identity-subline">{{ calculateAge(d.birthDate) }} سال · {{ d.gender === 'male' ? 'مرد' : 'زن' }}</div>
                </div>
              </div>
            </td>
            <td><span class="badge" :class="d.donorType==='living_related'?'badge-success':d.donorType==='living_unrelated'?'badge-info':'badge-warning'">{{ d.donorType==='living_related'?'زنده خویشاوند':d.donorType==='living_unrelated'?'زنده غیرخویشاوند':'فوت شده' }}</span></td>
            <td><span class="badge badge-info">{{ d.bloodType }}{{ d.rhFactor === 'positive' ? '+' : '-' }}</span></td>
            <td>{{ d.relationship || '—' }}</td>
            <td><span class="badge badge-success"><i class="ri-check-line"></i> در دسترس</span></td>
            <td @click.stop>
              <div class="flex gap-1">
                <button class="icon-btn" title="مشاهده" @click="$router.push('/donors/'+d._id)"><i class="ri-eye-line"></i></button>
                <button class="icon-btn" title="ویرایش"><i class="ri-edit-line"></i></button>
              </div>
            </td>
          </tr>
          <tr v-if="!filtered.length">
            <td colspan="6">
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
const filters = reactive({ donorType: '', bloodType: '' })
const toFa = toFaDigits

// Mock data for donors
const mockDonors = [
  { _id: 'd1', fullName: 'محمد رضایی', nationalId: '6666666666', birthDate: '1990-08-25', gender: 'male', bloodType: 'A', rhFactor: 'positive', donorType: 'living_related', status: 'available', relationship: 'برادر' },
  { _id: 'd2', fullName: 'فاطمه نوری', nationalId: '7777777777', birthDate: '1985-12-10', gender: 'female', bloodType: 'O', rhFactor: 'positive', donorType: 'living_unrelated', status: 'available', relationship: 'همسر' },
  { _id: 'd3', fullName: 'احمد موسوی', nationalId: '8888888888', birthDate: '1978-04-18', gender: 'male', bloodType: 'B', rhFactor: 'positive', donorType: 'living_related', status: 'available', relationship: 'پدر' },
  { _id: 'd4', fullName: 'سعید جعفری', nationalId: '9999999999', birthDate: '1988-09-05', gender: 'male', bloodType: 'O', rhFactor: 'negative', donorType: 'living_related', status: 'available', relationship: 'برادر' },
  { _id: 'd5', fullName: 'مرحوم کاظمی', nationalId: '0000000000', birthDate: '1975-02-28', gender: 'male', bloodType: 'A', rhFactor: 'positive', donorType: 'deceased', status: 'available', relationship: null }
]

const filtered = computed(() => {
  return mockDonors.filter(d => {
    if (search.value && !d.fullName.includes(search.value) && !d.nationalId.includes(search.value)) return false
    if (filters.donorType && d.donorType !== filters.donorType) return false
    if (filters.bloodType && d.bloodType !== filters.bloodType) return false
    return true
  })
})

const activeFilterCount = computed(() => Object.values(filters).filter(v => v !== '').length)

const doSearch = () => {
  const event = new CustomEvent('toast', { 
    detail: { severity: 'info', summary: 'جستجو', detail: `${toFa(filtered.value.length)} نتیجه یافت شد` } 
  })
  window.dispatchEvent(event)
}

const clearFilters = () => { 
  filters.donorType = ''
  filters.bloodType = '' 
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
