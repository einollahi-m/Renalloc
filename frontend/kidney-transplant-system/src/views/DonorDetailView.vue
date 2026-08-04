<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">{{ d.fullName }}</div>
        <div class="page-subtitle">پرونده اهداکننده پیوند کلیه</div>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-secondary" @click="$router.push('/donors')"><i class="ri-arrow-right-line"></i> بازگشت</button>
        <button class="btn btn-primary"><i class="ri-edit-line"></i> ویرایش</button>
      </div>
    </div>

    <div class="profile-header donor">
      <div class="profile-avatar">{{ d.fullName[0] }}</div>
      <div class="profile-info">
        <h2>{{ d.fullName }}</h2>
        <div class="profile-meta">
          <div class="profile-meta-item"><i class="ri-id-card-line"></i> {{ d.nationalId }}</div>
          <div class="profile-meta-item"><i class="ri-calendar-line"></i> {{ calculateAge(d.birthDate) }} سال</div>
          <div class="profile-meta-item"><i class="ri-drop-line"></i> {{ d.bloodType }}{{ d.rhFactor === 'positive' ? '+' : '-' }}</div>
          <div class="profile-meta-item"><i class="ri-hand-heart-line"></i> {{ d.donorType === 'living_related' ? 'زنده خویشاوند' : d.donorType === 'living_unrelated' ? 'زنده غیرخویشاوند' : 'فوت شده' }}</div>
          <div class="profile-meta-item" v-if="d.relationship"><i class="ri-links-line"></i> {{ d.relationship }}</div>
        </div>
      </div>
    </div>

    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key" class="tab" :class="{active:activeTab===tab.key}" @click="activeTab=tab.key">
        <i :class="tab.icon"></i> {{ tab.label }}
      </button>
    </div>

    <div v-if="activeTab==='overview'" class="grid grid-3">
      <div v-for="ph in overviewBlocks" :key="ph.title" class="placeholder-tile">
        <i :class="ph.icon"></i>
        <h3>{{ ph.title }}</h3>
        <p>{{ ph.desc }}</p>
      </div>
    </div>
    <div v-else class="tab-placeholder">
      <div class="tab-placeholder-icon"><i :class="activeTabObj.icon"></i></div>
      <h3>{{ activeTabObj.label }}</h3>
      <p>محتوای این بخش پس از طراحی نهایی تکمیل خواهد شد.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { formatFaDate } from '../utils/date'
import { mockDonors } from '../data/mockData'

const route = useRoute()
const d = computed(() => mockDonors.find(x => x._id === route.params.id) || mockDonors[0])
const activeTab = ref('overview')
const tabs = [
  { key: 'overview', label: 'خلاصه پرونده', icon: 'ri-dashboard-2-line' },
  { key: 'personal', label: 'اطلاعات فردی', icon: 'ri-user-line' },
  { key: 'medical', label: 'سوابق پزشکی', icon: 'ri-stethoscope-line' },
  { key: 'hla', label: 'تایپ HLA', icon: 'ri-dna-line' },
  { key: 'labs', label: 'آزمایش‌ها', icon: 'ri-flask-line' },
  { key: 'approvals', label: 'تاییدیه‌ها', icon: 'ri-checkbox-circle-line' }
]
const activeTabObj = computed(() => tabs.find(t => t.key === activeTab.value) || tabs[0])
const overviewBlocks = [
  { title: 'شاخص‌های اهدا', desc: 'نوع اهدا، نسبت با گیرنده و وضعیت در دسترس بودن', icon: 'ri-hand-heart-line' },
  { title: 'خلاصه پزشکی', desc: 'چکیده سوابق و ارزیابی‌های بالینی اهداکننده', icon: 'ri-file-text-line' },
  { title: 'اقدامات اخیر', desc: 'آخرین آزمایش‌ها و تاییدیه‌های ثبت‌شده', icon: 'ri-history-line' }
]
const calculateAge = (birthDate) => birthDate ? new Date().getFullYear() - new Date(birthDate).getFullYear() : '—'
</script>
