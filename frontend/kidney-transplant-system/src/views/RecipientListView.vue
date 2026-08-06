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
            <td>{{ toFa(r.nationalId) }}</td>
            <td><span class="badge badge-info">{{ r.bloodType }}{{ r.rhFactor === 'positive' ? '+' : '-' }}</span></td>
            <td>
              <div v-if="r.cpra !== null" class="flex items-center gap-2">
                <div class="progress" style="width:60px;"><div class="progress-bar" :class="r.cpra>70?'danger':r.cpra>30?'warning':'success'" :style="{width:r.cpra+'%'}"></div></div>
                <span class="font-bold">{{ toFa(r.cpra) }}٪</span>
              </div>
              <span v-else>—</span>
            </td>
            <td><span v-if="r.priorityScore !== null" class="badge badge-primary">{{ toFa(r.priorityScore) }}</span><span v-else>—</span></td>
            <td><span class="badge" :class="r.status==='active'?'badge-success':'badge-secondary'">{{ r.status === 'active' ? 'فعال' : 'غیرفعال' }}</span></td>
            <td @click.stop>
              <div class="flex gap-1">
                <button class="icon-btn" title="مشاهده" @click="$router.push('/recipients/'+r._id)"><i class="ri-eye-line"></i></button>
              </div>
            </td>
          </tr>
          <tr v-if="loading">
            <td colspan="7"><div class="empty-state" style="border:none;background:transparent;"><i class="ri-loader-4-line"></i><h3>در حال دریافت گیرندگان…</h3></div></td>
          </tr>
          <tr v-else-if="loadError">
            <td colspan="7"><div class="empty-state" style="border:none;background:transparent;"><i class="ri-error-warning-line"></i><h3>{{ loadError }}</h3><button class="btn btn-secondary mt-3" @click="loadRecipients">تلاش دوباره</button></div></td>
          </tr>
          <tr v-else-if="!filtered.length">
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
const filters = reactive({ citizenship: '', gender: '', bloodType: '', status: '' })
const toFa = toFaDigits
const recipients = ref([])
const loading = ref(true)
const loadError = ref('')
const pagination = ref({page:1,pages:1,count:0,has_next:false,has_previous:false})

const filtered = computed(() => recipients.value)

const activeFilterCount = computed(() => Object.values(filters).filter(v => v !== '').length)

const doSearch = () => {
  loadRecipients(1)
}

const clearFilters = () => {
  filters.citizenship = ''
  filters.gender = '' 
  filters.bloodType = '' 
  filters.status = '' 
  search.value = ''
  loadRecipients(1)
}

const loadRecipients = async (page = pagination.value.page || 1) => {
  loading.value = true
  loadError.value = ''
  try {
    const response = await registryApi.listRecipients({page,page_size:25,search:search.value,citizenship:filters.citizenship,gender:filters.gender,blood_type:filters.bloodType,status:filters.status})
    recipients.value = response.recipients || []
    pagination.value = response.pagination || pagination.value
  } catch (error) {
    loadError.value = error?.message || 'دریافت فهرست گیرندگان انجام نشد'
  } finally {
    loading.value = false
  }
}
const changePage=page=>loadRecipients(page)

onMounted(loadRecipients)

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
