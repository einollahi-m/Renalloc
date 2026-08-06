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
            <td><span class="badge" :class="d.status==='available'?'badge-success':'badge-secondary'"><i :class="d.status==='available'?'ri-check-line':'ri-pause-line'"></i> {{ d.status === 'available' ? 'در دسترس' : 'غیرفعال' }}</span></td>
            <td @click.stop>
              <div class="flex gap-1">
                <button class="icon-btn" title="مشاهده" @click="$router.push('/donors/'+d._id)"><i class="ri-eye-line"></i></button>
              </div>
            </td>
          </tr>
          <tr v-if="loading">
            <td colspan="6"><div class="empty-state" style="border:none;background:transparent;"><i class="ri-loader-4-line"></i><h3>در حال دریافت اهداکنندگان…</h3></div></td>
          </tr>
          <tr v-else-if="loadError">
            <td colspan="6"><div class="empty-state" style="border:none;background:transparent;"><i class="ri-error-warning-line"></i><h3>{{ loadError }}</h3><button class="btn btn-secondary mt-3" @click="loadDonors">تلاش دوباره</button></div></td>
          </tr>
          <tr v-else-if="!filtered.length">
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
      <pagination-controls :pagination="pagination" @change="changePage" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { toFaDigits } from '../utils/date'
import { registryApi } from '../services/api'
import PaginationControls from '../components/PaginationControls.vue'

const search = ref('')
const showFilters = ref(false)
const filters = reactive({ donorType: '', bloodType: '' })
const toFa = toFaDigits

const donors = ref([])
const loading = ref(true)
const loadError = ref('')
const pagination = ref({page:1,pages:1,count:0,has_next:false,has_previous:false})

const filtered = computed(() => donors.value)

const activeFilterCount = computed(() => Object.values(filters).filter(v => v !== '').length)

const doSearch = () => {
  loadDonors(1)
}

const clearFilters = () => { 
  filters.donorType = ''
  filters.bloodType = '' 
  search.value = ''
  loadDonors(1)
}

const loadDonors = async (page = pagination.value.page || 1) => {
  loading.value = true
  loadError.value = ''
  try {
    const response = await registryApi.listDonors({page,page_size:25,search:search.value,donor_type:filters.donorType,blood_type:filters.bloodType})
    donors.value = response.donors || []
    pagination.value = response.pagination || pagination.value
  } catch (error) {
    loadError.value = error?.message || 'دریافت فهرست اهداکنندگان انجام نشد'
  } finally {
    loading.value = false
  }
}
const changePage=page=>loadDonors(page)

onMounted(loadDonors)

const calculateAge = (birthDate) => {
  if (!birthDate) return '—'
  return toFa(new Date().getFullYear() - new Date(birthDate).getFullYear())
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
