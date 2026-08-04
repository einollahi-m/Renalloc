<template>
  <div class="create-person-page" @input.capture="normalizeNumericInputEvent">
    <div class="page-header">
      <div>
        <div class="page-title">ثبت اهداکننده جدید</div>
        <div class="page-subtitle">اطلاعات اهداکننده را در مراحل زیر وارد کنید</div>
      </div>
    </div>

    <div class="card mb-4">
      <div class="stepper">
        <button v-for="(s, idx) in steps" :key="idx" type="button" class="step-item" :class="{active:step===idx, done:step>idx}" @click="goToStep(idx)">
          <div class="step-number">
            <i v-if="step>idx" class="ri-check-line"></i>
            <span v-else>{{ toFa(idx+1) }}</span>
          </div>
          <span>{{ s }}</span>
        </button>
      </div>
    </div>

    <div v-if="step < 3" class="form-actions form-actions-top">
      <button class="btn btn-secondary" type="button" @click="prevStep" :disabled="step===0">
        <i class="ri-arrow-right-line"></i> گام قبلی
      </button>
      <div class="flex gap-2">
        <button class="btn btn-secondary" type="button" @click="cancel">انصراف</button>
        <button class="btn btn-primary" type="button" @click="nextOrSubmit">
          گام بعدی <i class="ri-arrow-left-line"></i>
        </button>
      </div>
    </div>

    <!-- گام ۱: اطلاعات فردی -->
    <div v-if="step===0">
      <section class="form-card">
        <div class="form-card-title"><i class="ri-id-card-line"></i> اطلاعات هویتی</div>
        <div class="form-grid identity-primary-grid">
          <div class="form-group">
            <label class="form-label">تابعیت *</label>
            <div class="radio-pills">
              <label class="radio-pill" :class="{checked: form.citizenship==='iranian'}"><input type="radio" name="donor-citizenship" v-model="form.citizenship" value="iranian" /> ایرانی</label>
              <label class="radio-pill" :class="{checked: form.citizenship==='foreign'}"><input type="radio" name="donor-citizenship" v-model="form.citizenship" value="foreign" /> غیر ایرانی</label>
            </div>
          </div>
          <div class="form-group">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
              <label class="form-label" style="margin:0;">{{ form.citizenship === 'iranian' ? 'کد ملی (۱۰ رقم) *' : 'شماره گذرنامه *' }}</label>
              <span v-if="nationalIdError" class="text-danger text-xs">{{ nationalIdError }}</span>
              <span v-else-if="isNationalIdValid" class="text-success text-xs">✓ معتبر</span>
            </div>
            <div class="input-group">
              <input type="text" v-model="form.national_id" class="form-input" :class="{'form-error-border':nationalIdError}" @input="normalizeAndValidateNationalId" @blur="validateNationalIdField" :maxlength="form.citizenship==='iranian'?10:null" :inputmode="form.citizenship==='iranian'?'numeric':'text'" :placeholder="form.citizenship==='iranian'?'کد ملی':'شماره پاسپورت'" />
              <div class="input-addon">
                <i v-if="nationalIdChecking" class="ri-loader-4-line" style="animation:spin 1s linear infinite;"></i>
                <i v-else-if="isNationalIdValid" class="ri-check-line" style="color:var(--color-success);"></i>
                <i v-else-if="nationalIdError" class="ri-error-warning-line" style="color:var(--color-error);"></i>
              </div>
            </div>
          </div>
          <div class="form-group" v-if="form.citizenship==='foreign'">
            <label class="form-label">ملیت *</label>
            <select v-model="form.nationality" class="form-select">
              <option value="">انتخاب کنید</option>
              <option v-for="n in nationalityOptions" :key="n" :value="n">{{ n }}</option>
            </select>
          </div>
        </div>
        <div class="form-grid identity-details-grid">
          <div class="form-group">
            <label class="form-label">نام *</label>
            <input type="text" v-model="form.first_name" class="form-input" placeholder="نام" />
          </div>
          <div class="form-group">
            <label class="form-label">نام خانوادگی *</label>
            <input type="text" v-model="form.last_name" class="form-input" placeholder="نام خانوادگی" />
          </div>
          <div class="form-group">
            <label class="form-label">جنسیت *</label>
            <div class="radio-pills">
              <label class="radio-pill" :class="{checked: form.gender==='male'}"><input type="radio" name="donor-gender" v-model="form.gender" value="male" /> مرد</label>
              <label class="radio-pill" :class="{checked: form.gender==='female'}"><input type="radio" name="donor-gender" v-model="form.gender" value="female" /> زن</label>
            </div>
          </div>
          <div class="form-group identity-birth-field">
            <dual-date-field v-model="form.birth_date" label="تاریخ تولد *" />
          </div>
          <div class="form-group identity-blood-field">
            <label class="form-label">گروه خونی *</label>
            <div class="blood-row">
              <select v-model="form.blood_type" class="form-select">
                <option value="">انتخاب</option>
                <option v-for="b in bloodTypeOptions" :key="b" :value="b">{{ b }}</option>
              </select>
              <div class="rh-choice-field">
                <span class="form-label">Rh</span>
                <div class="radio-pills radio-stack">
                  <label class="radio-pill" :class="{checked: form.rh_factor==='positive'}"><input type="radio" name="donor-rh" v-model="form.rh_factor" value="positive" /> مثبت</label>
                  <label class="radio-pill" :class="{checked: form.rh_factor==='negative'}"><input type="radio" name="donor-rh" v-model="form.rh_factor" value="negative" /> منفی</label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="form-card">
        <div class="form-card-title"><i class="ri-phone-line"></i> اطلاعات تماس</div>
        <div class="form-grid contact-fields-grid">
          <div class="form-group">
            <label class="form-label">شماره موبایل</label>
            <input type="text" v-model="form.phone" class="form-input" :class="{'form-error-border':phoneErrors.phone}" @input="normalizePhone('phone',$event)" @blur="validatePhone('phone')" maxlength="11" inputmode="numeric" placeholder="09xxxxxxxxx" />
            <div v-if="phoneErrors.phone" class="form-error text-xs">{{ phoneErrors.phone }}</div>
          </div>
          <div class="form-group">
            <label class="form-label">شماره موبایل اضطراری</label>
            <input type="text" v-model="form.emergency_contact_phone" class="form-input" :class="{'form-error-border':phoneErrors.emergency}" @input="normalizePhone('emergency',$event)" @blur="validatePhone('emergency')" maxlength="11" inputmode="numeric" placeholder="09xxxxxxxxx" />
            <div v-if="phoneErrors.emergency" class="form-error text-xs">{{ phoneErrors.emergency }}</div>
          </div>
        </div>
      </section>

      <section class="form-card">
        <div class="form-card-title"><i class="ri-user-heart-line"></i> مشخصات فردی و رفتارهای پرخطر</div>
        <div class="form-grid personal-profile-grid">
          <div class="form-group">
            <label class="form-label">تحصیلات</label>
            <select v-model="form.education" class="form-select">
              <option value="">انتخاب کنید</option>
              <option v-for="e in educationOptions" :key="e.value" :value="e.value">{{ e.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">بیمه</label>
            <checkbox-multi-select v-model="form.insurance" :options="insuranceOptions" :max-chips="1" placeholder="انتخاب بیمه" :disabled="form.citizenship==='foreign'" />
          </div>
          <div class="form-group marital-status-field">
            <label class="form-label">وضعیت تأهل</label>
            <div class="radio-pills radio-stack">
              <label class="radio-pill" :class="{checked: form.marital_status==='single'}"><input type="radio" name="donor-marital-status" v-model="form.marital_status" value="single" /> مجرد</label>
              <label class="radio-pill" :class="{checked: form.marital_status==='married'}"><input type="radio" name="donor-marital-status" v-model="form.marital_status" value="married" /> متأهل</label>
            </div>
          </div>
          <div class="form-group measures-field">
            <div class="measure-label-row">
              <label class="form-label" for="donor-weight">وزن (کیلوگرم)</label>
              <label class="form-label" for="donor-height">قد (سانتی‌متر)</label>
            </div>
            <div class="measure-input-pair">
              <input id="donor-weight" type="text" v-model="newWeight" class="form-input" placeholder="72.5" inputmode="decimal" @keydown.up.prevent="adjustWeight(0.5)" @keydown.down.prevent="adjustWeight(-0.5)" />
              <input id="donor-height" type="text" v-model="newHeight" class="form-input" placeholder="175" inputmode="numeric" />
            </div>
          </div>
        </div>
        <div class="form-group risk-behaviors-field">
          <label class="form-label">رفتارهای پرخطر</label>
          <div class="check-chips">
            <label class="check-chip" :class="{checked: form.is_smoker}"><input type="checkbox" v-model="form.is_smoker" /><i class="ri-cigarette-line"></i> سیگاری</label>
            <label class="check-chip" :class="{checked: form.has_addiction}"><input type="checkbox" v-model="form.has_addiction" /><i class="ri-forbid-line"></i> سابقه اعتیاد</label>
            <label class="check-chip" :class="{checked: form.has_alcohol}"><input type="checkbox" v-model="form.has_alcohol" /><i class="ri-goblet-line"></i> مصرف الکل</label>
          </div>
        </div>
      </section>
    </div>

    <!-- گام ۲: سوابق پزشکی -->
    <div v-if="step===1">
      <div class="grid grid-2 mb-4">
        <section class="form-card" style="margin-bottom:0;">
          <div class="form-card-title"><i class="ri-heart-line"></i> وضعیت پزشکی اهداکننده</div>
          <div class="check-chips">
            <label class="check-chip" :class="{checked: form.self_diabetes_history}"><input type="checkbox" v-model="form.self_diabetes_history" /><i class="ri-drop-line"></i> دیابت</label>
            <label class="check-chip" :class="{checked: form.self_hypertension_history}"><input type="checkbox" v-model="form.self_hypertension_history" /><i class="ri-pulse-line"></i> فشار خون</label>
          </div>
        </section>
        <section class="form-card" style="margin-bottom:0;">
          <div class="form-card-title"><i class="ri-team-line"></i> سابقه والدین</div>
          <div class="check-chips">
            <label class="check-chip" :class="{checked: form.parent_diabetes_history}"><input type="checkbox" v-model="form.parent_diabetes_history" /><i class="ri-drop-line"></i> دیابت در والدین</label>
            <label class="check-chip" :class="{checked: form.parent_hypertension_history}"><input type="checkbox" v-model="form.parent_hypertension_history" /><i class="ri-pulse-line"></i> فشار خون در والدین</label>
          </div>
        </section>
      </div>

      <section class="form-card">
        <div class="form-card-title"><i class="ri-capsule-line"></i> حساسیت دارویی</div>
        <label class="checkbox-wrap mb-2"><input type="checkbox" v-model="form.has_drug_allergy" /> سابقه آلرژی دارویی</label>
        <textarea v-if="form.has_drug_allergy" v-model="form.drug_allergy_details" class="form-input" rows="3" placeholder="نام دارو، علائم و توضیحات"></textarea>
      </section>

      <section class="form-card">
        <div class="form-card-title"><i class="ri-links-line"></i> گیرنده مورد نظر (خویشاوند یا دوست)</div>
        <label class="checkbox-wrap mb-3"><input type="checkbox" v-model="form.is_related_recipient_candidate" /> کاندید اهدا به خویشاوندان یا دوستان</label>
        <div v-if="form.is_related_recipient_candidate" class="form-grid">
          <div class="form-group">
            <label class="form-label">{{ form.citizenship === 'iranian' ? 'کد ملی گیرنده' : 'شماره پاسپورت گیرنده' }}</label>
            <input type="text" v-model="form.preferred_recipient_national_id" class="form-input" @input="normalizeRecipientIdentifier" :maxlength="form.citizenship==='iranian'?10:null" inputmode="numeric" :placeholder="form.citizenship==='iranian'?'کد ملی':'شماره پاسپورت'" />
          </div>
          <div class="form-group">
            <label class="form-label">&nbsp;</label>
            <button class="btn btn-primary" type="button" @click="lookupRecipientByNationalId" :disabled="!form.preferred_recipient_national_id">
              <i class="ri-search-line"></i> جستجوی گیرنده
            </button>
          </div>
        </div>
        <div v-if="recipientSummary" class="lookup-result">
          <div class="lookup-result-header">
            <i class="ri-check-double-line" style="color:var(--color-success);font-size:24px;"></i>
            <div>
              <div class="font-bold">{{ recipientSummary.fullName }}</div>
              <div class="text-sm text-secondary">گیرنده منتخب</div>
            </div>
          </div>
          <div class="lookup-info">
            <div class="lookup-info-item"><div class="label">کد ملی</div><div class="value">{{ recipientSummary.nationalId }}</div></div>
            <div class="lookup-info-item"><div class="label">گروه خونی</div><div class="value">{{ recipientSummary.bloodType }}{{ recipientSummary.rhFactor === 'positive' ? '+' : '-' }}</div></div>
            <div class="lookup-info-item"><div class="label">جنسیت</div><div class="value">{{ recipientSummary.gender === 'male' ? 'مرد' : 'زن' }}</div></div>
            <div class="lookup-info-item"><div class="label">وضعیت</div><div class="value">{{ recipientSummary.status === 'active' ? 'فعال' : 'غیرفعال' }}</div></div>
          </div>
          <div v-if="form.is_related_recipient_candidate" class="mt-3">
            <div class="form-group">
              <label class="form-label">نسبت</label>
              <select v-model="form.recipient_relationship_group" class="form-select">
                <option value="">انتخاب کنید</option>
                <option value="first_degree">درجه اول</option>
                <option value="second_degree">درجه دوم</option>
                <option value="stranger">غریبه</option>
              </select>
            </div>
            <div v-if="form.recipient_relationship_group==='first_degree'" class="form-group">
              <label class="form-label">نسبت خویشاوندی</label>
              <select v-model="form.recipient_relationship_kind" class="form-select">
                <option value="">انتخاب کنید</option>
                <option value="father">پدر</option>
                <option value="mother">مادر</option>
                <option value="brother">برادر</option>
                <option value="sister">خواهر</option>
                <option value="child">فرزند</option>
                <option value="spouse">همسر</option>
              </select>
            </div>
            <div v-if="form.recipient_relationship_group==='second_degree'" class="form-group">
              <label class="form-label">نسبت درجه دوم</label>
              <input type="text" v-model="form.recipient_relationship_details" class="form-input" placeholder="مثلاً عمه، دایی، خواهرزاده..." />
            </div>
          </div>
        </div>
        <div v-if="recipientLookupMessage" class="alert alert-warning mt-3" style="margin-bottom:0;"><i class="ri-information-line"></i>{{ recipientLookupMessage }}</div>
      </section>
    </div>

    <!-- گام ۳: آزمایش‌ها -->
    <div v-if="step===2">
      <div class="accordion mb-4">
        <div class="accordion-item" :class="{open:openAccordion.hla}">
          <div class="accordion-header" @click="openAccordion.hla=!openAccordion.hla">
            <span><i class="ri-dna-line" style="color:var(--color-primary);"></i> اطلاعات HLA</span>
            <i class="ri-arrow-down-s-line"></i>
          </div>
          <div class="accordion-content">
            <div class="grid grid-2">
              <div>
                <h4 style="margin-bottom:12px;">HLA Class I</h4>
                <div class="form-group">
                  <label class="form-label">HLA-A</label>
                  <checkbox-multi-select v-model="form.hla_a" :options="hlaOptions.hlaA" :max-selected="2" :ltr="true" placeholder="انتخاب آلل" />
                </div>
                <div class="form-group">
                  <label class="form-label">HLA-B</label>
                  <checkbox-multi-select v-model="form.hla_b" :options="hlaOptions.hlaB" :max-selected="2" :ltr="true" placeholder="انتخاب آلل" />
                </div>
                <div class="form-group" style="margin-bottom:0;">
                  <label class="form-label">HLA-C</label>
                  <checkbox-multi-select v-model="form.hla_c" :options="hlaOptions.hlaC" :max-selected="2" :ltr="true" placeholder="انتخاب آلل" />
                </div>
              </div>
              <div>
                <h4 style="margin-bottom:12px;">HLA Class II</h4>
                <div class="form-group">
                  <label class="form-label">HLA-DRB1</label>
                  <checkbox-multi-select v-model="form.hla_drb1" :options="hlaOptions.hlaDRB1" :max-selected="2" :ltr="true" placeholder="انتخاب آلل" />
                </div>
                <div class="form-group">
                  <label class="form-label">HLA-DQB1</label>
                  <checkbox-multi-select v-model="form.hla_dqb1" :options="hlaOptions.hlaDQB1" :max-selected="2" :ltr="true" placeholder="انتخاب آلل" />
                </div>
                <div class="form-group" style="margin-bottom:0;">
                  <label class="form-label">HLA-DRB</label>
                  <checkbox-multi-select v-model="form.hla_drb" :options="hlaOptions.hlaDRB" :max-selected="2" :ltr="true" placeholder="انتخاب آلل" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="accordion mb-4">
        <div class="accordion-item" :class="{open:openAccordion.routine}">
          <div class="accordion-header" @click="openAccordion.routine=!openAccordion.routine">
            <span><i class="ri-flask-line" style="color:var(--color-primary);"></i> آزمایش‌های پیوند</span>
            <i class="ri-arrow-down-s-line"></i>
          </div>
          <div class="accordion-content">
            <div class="flex justify-between items-center mb-3">
              <h4 style="margin:0;">نتایج ثبت شده</h4>
              <button class="btn btn-sm btn-primary" type="button" @click="openRoutineCreate"><i class="ri-add-line"></i> افزودن آزمایش جدید</button>
            </div>
            <test-results-list :tests="form.routine_tests" :show-category="true" empty-title="آزمایش پیوند ثبت نشده" @edit="openRoutineEdit" @remove="removeRoutineTest" />
          </div>
        </div>
      </div>

      <div class="accordion">
        <div class="accordion-item" :class="{open:openAccordion.viral}">
          <div class="accordion-header" @click="openAccordion.viral=!openAccordion.viral">
            <span><i class="ri-virus-line" style="color:var(--color-primary);"></i> آزمایش‌های ویروسی</span>
            <i class="ri-arrow-down-s-line"></i>
          </div>
          <div class="accordion-content">
            <div class="flex justify-between items-center mb-3">
              <h4 style="margin:0;">نتایج ثبت شده</h4>
              <button class="btn btn-sm btn-primary" type="button" @click="openViralCreate"><i class="ri-add-line"></i> افزودن آزمایش جدید</button>
            </div>
            <test-results-list :tests="form.viral_tests" icon="ri-virus-line" empty-title="آزمایش ویروسی ثبت نشده" @edit="openViralEdit" @remove="removeViralTest" />
          </div>
        </div>
      </div>
    </div>

    <!-- گام ۴: تاییدیه‌ها -->
    <div v-if="step===3">
      <div class="accordion">
        <div class="accordion-item" :class="{open:openAccordion.approvals}">
          <div class="accordion-header" @click="openAccordion.approvals=!openAccordion.approvals">
            <span><i class="ri-checkbox-circle-line" style="color:var(--color-primary);"></i> تاییدیه‌های پزشکی</span>
            <i class="ri-arrow-down-s-line"></i>
          </div>
          <div class="accordion-content">
            <div class="specialties-header">
              <button v-for="spec in donorSpecialties" :key="spec.key" type="button" class="specialty-tab"
                :class="{ active: activeSpecialty === spec.key, [getApprovalClass(spec.key)]: true }"
                @click="activeSpecialty = spec.key">
                <i :class="getApprovalIcon(spec.key)"></i>
                <span>{{ spec.label }}</span>
              </button>
            </div>
            <div v-if="activeSpecialty" class="specialty-detail" :class="getApprovalClass(activeSpecialty)">
              <div class="form-group">
                <label class="form-label">وضعیت تایید</label>
                <div class="radio-pills" style="max-width:420px;">
                  <label v-for="s in approvalStatusOptions" :key="s.value" class="radio-pill" :class="{checked: form.approvals[activeSpecialty].status===s.value}">
                    <input type="radio" v-model="form.approvals[activeSpecialty].status" :value="s.value" /> {{ s.label }}
                  </label>
                </div>
              </div>
              <dual-date-field v-model="form.approvals[activeSpecialty].approval_date" label="تاریخ تایید" />
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">نام پزشک</label>
                  <input type="text" v-model="form.approvals[activeSpecialty].doctor_name" class="form-input" placeholder="نام پزشک" />
                </div>
                <div class="form-group">
                  <label class="form-label">کد نظام پزشکی</label>
                  <input type="text" v-model="form.approvals[activeSpecialty].medical_code" class="form-input" placeholder="کد نظام پزشکی" inputmode="numeric" />
                </div>
              </div>
              <div class="form-group" style="margin-bottom:0;">
                <label class="form-label">توضیحات</label>
                <textarea v-model="form.approvals[activeSpecialty].notes" class="form-input" rows="3" placeholder="توضیحات..."></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="step===3" class="form-actions">
      <button class="btn btn-secondary" type="button" @click="prevStep">
        <i class="ri-arrow-right-line"></i> گام قبلی
      </button>
      <div class="flex gap-2">
        <button class="btn btn-secondary" type="button" @click="cancel">انصراف</button>
        <button class="btn btn-primary" type="button" @click="nextOrSubmit">
          <i class="ri-save-line"></i> تایید و ثبت اهدا کننده جدید
        </button>
      </div>
    </div>

    <routine-tests-modal v-model:visible="showRoutineModal" :gender="form.gender" :edit-date="editingRoutineDate" :existing-tests="editingRoutineTests" @add="addRoutineTests" @save="saveRoutineTests" />
    <viral-tests-modal v-model:visible="showViralModal" :edit-date="editingViralDate" :existing-tests="editingViralTests" @add="addViralTests" @save="saveViralTests" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { toFaDigits, formatFaDate } from '../utils/date'
import { nationalIdChecker, normalizeNationalId, normalizeIranianMobile, isValidIranianMobile, normalizeLocalizedDigits, normalizeLocalizedNumber } from '../utils/validation'
import { mockRecipients } from '../data/mockData'
import { hlaOptions } from '../data/hlaOptions'
import { educationOptions, insuranceOptions, nationalityOptions, bloodTypeOptions, approvalStatusOptions, donorSpecialties } from '../data/options'
import TestResultsList from '../components/TestResultsList.vue'

const router = useRouter()
const step = ref(0)
const steps = ['اطلاعات فردی', 'سوابق پزشکی', 'آزمایش‌ها', 'تاییدیه‌ها']
const toFa = toFaDigits

const form = reactive({
  citizenship: 'iranian', national_id: '', first_name: '', last_name: '', gender: null,
  blood_type: null, rh_factor: null, phone: '', emergency_contact_phone: '',
  education: null, insurance: [], marital_status: null, nationality: '', birth_date: '',
  is_smoker: false, has_addiction: false, has_alcohol: false,
  self_diabetes_history: false, self_hypertension_history: false,
  parent_diabetes_history: false, parent_hypertension_history: false,
  has_drug_allergy: false, drug_allergy_details: '',
  is_related_recipient_candidate: false,
  preferred_recipient_national_id: '',
  recipient_relationship_group: null,
  recipient_relationship_kind: null,
  recipient_relationship_details: '',
  hla_a: [], hla_b: [], hla_c: [], hla_drb1: [], hla_dqb1: [], hla_drb: [],
  routine_tests: [], viral_tests: [],
  approvals: {
    nephrologist: { status: 'on_hold', approval_date: '', doctor_name: '', medical_code: '', notes: '' },
    cardiologist: { status: 'on_hold', approval_date: '', doctor_name: '', medical_code: '', notes: '' },
    urologist: { status: 'on_hold', approval_date: '', doctor_name: '', medical_code: '', notes: '' }
  }
})

const newWeight = ref(null)
const newHeight = ref(null)
const activeSpecialty = ref('nephrologist')
const openAccordion = reactive({ hla: true, routine: true, viral: true, approvals: true })
const showRoutineModal = ref(false)
const showViralModal = ref(false)
const editingRoutineDate = ref(null)
const editingViralDate = ref(null)
const nationalIdError = ref('')
const nationalIdChecking = ref(false)
const nationalIdValidated = ref(false)
const phoneErrors = reactive({ phone: '', emergency: '' })
const recipientSummary = ref(null)
const recipientLookupMessage = ref('')
let nationalIdValidationToken = 0

const isNationalIdValid = computed(() => form.citizenship === 'iranian' && nationalIdValidated.value && !nationalIdError.value)
const editingRoutineTests = computed(() => editingRoutineDate.value ? form.routine_tests.filter(test => test.testDate === editingRoutineDate.value) : [])
const editingViralTests = computed(() => editingViralDate.value ? form.viral_tests.filter(test => test.testDate === editingViralDate.value) : [])

watch(() => form.citizenship, (citizenship) => {
  nationalIdValidationToken++
  form.national_id = ''
  nationalIdError.value = ''
  nationalIdChecking.value = false
  nationalIdValidated.value = false
  if (citizenship === 'iranian') form.nationality = ''
  else form.insurance = []
})

const normalizeNumericInputEvent = event => {
  const input = event.target
  if (!input || input.tagName !== 'INPUT') return
  const inputMode = input.getAttribute('inputmode')
  let normalized = input.value
  if (inputMode === 'numeric') normalized = normalizeLocalizedDigits(input.value).replace(/\D/g, '')
  else if (inputMode === 'decimal') normalized = normalizeLocalizedNumber(input.value)
  if (normalized !== input.value) input.value = normalized
}

const adjustWeight = delta => {
  const current = Number(normalizeLocalizedNumber(newWeight.value)) || 0
  newWeight.value = String(Math.max(0, Math.round((current + delta) * 2) / 2))
}

const normalizeAndValidateNationalId = (e) => {
  const validationToken = ++nationalIdValidationToken
  if (form.citizenship === 'foreign') {
    form.national_id = e.target.value.trim().toUpperCase()
    nationalIdError.value = ''
    nationalIdChecking.value = false
    nationalIdValidated.value = false
    return
  }
  const val = normalizeNationalId(e.target.value).slice(0, 10)
  form.national_id = val
  nationalIdError.value = ''
  nationalIdChecking.value = false
  nationalIdValidated.value = false
  if (val.length > 0 && val.length < 10) {
    nationalIdError.value = 'کد ملی باید ۱۰ رقم باشد'
    return
  }
  if (val.length === 10) {
    nationalIdChecking.value = true
    setTimeout(() => {
      if (validationToken !== nationalIdValidationToken || form.citizenship !== 'iranian' || form.national_id !== val) return
      const valid = nationalIdChecker(val)
      nationalIdError.value = valid ? '' : 'کد ملی نامعتبر است'
      nationalIdValidated.value = valid
      nationalIdChecking.value = false
    }, 300)
  }
}

const validateNationalIdField = () => {
  nationalIdValidationToken++
  nationalIdChecking.value = false
  if (form.citizenship !== 'iranian') {
    nationalIdError.value = ''
    nationalIdValidated.value = false
    return true
  }
  const nationalId = normalizeNationalId(form.national_id)
  if (!nationalId) {
    nationalIdError.value = 'کد ملی را وارد کنید'
    nationalIdValidated.value = false
    return false
  }
  if (!/^\d{10}$/.test(nationalId)) {
    nationalIdError.value = 'کد ملی باید ۱۰ رقم باشد'
    nationalIdValidated.value = false
    return false
  }
  const valid = nationalIdChecker(nationalId)
  nationalIdError.value = valid ? '' : 'کد ملی نامعتبر است'
  nationalIdValidated.value = valid
  return valid
}

const normalizePhone = (field, e) => {
  form[field === 'phone' ? 'phone' : 'emergency_contact_phone'] = normalizeIranianMobile(e.target.value)
  phoneErrors[field] = ''
}

const validatePhone = (field) => {
  const errorKey = field === 'phone' ? 'phone' : 'emergency'
  const formKey = field === 'phone' ? 'phone' : 'emergency_contact_phone'
  const val = normalizeIranianMobile(form[formKey])
  if (!val) {
    phoneErrors[errorKey] = ''
    return true
  }
  if (!isValidIranianMobile(val)) {
    phoneErrors[errorKey] = 'شماره موبایل باید ۱۱ رقم و با 09 شروع شود'
    return false
  }
  phoneErrors[errorKey] = ''
  return true
}

const normalizeRecipientIdentifier = (e) => {
  form.preferred_recipient_national_id = normalizeNationalId(e.target.value).slice(0, 10)
  recipientSummary.value = null
  recipientLookupMessage.value = ''
}

const lookupRecipientByNationalId = () => {
  const query = normalizeNationalId(form.preferred_recipient_national_id).trim().toUpperCase()
  if (!query) {
    window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'کد ملی گیرنده را وارد کنید' })
    return
  }
  if (form.citizenship === 'iranian' && !/^\d{10}$/.test(query)) {
    recipientLookupMessage.value = 'کد ملی باید ۱۰ رقم باشد'
    recipientSummary.value = null
    return
  }
  if (form.citizenship === 'iranian' && !nationalIdChecker(query)) {
    recipientLookupMessage.value = 'کد ملی نامعتبر است'
    recipientSummary.value = null
    return
  }
  const found = mockRecipients.find(r => r.nationalId === query)
  if (found) {
    recipientSummary.value = found
    recipientLookupMessage.value = ''
  } else {
    recipientSummary.value = null
    recipientLookupMessage.value = 'گیرنده‌ای با این کد ملی یافت نشد'
  }
}

const addRoutineTests = (tests) => {
  if (!tests || !tests.length) return
  const existingSet = new Set(form.routine_tests.map(t => `${t.testDate}|${t.category}|${t.testName}`))
  const newTests = tests.filter(t => !existingSet.has(`${t.testDate}|${t.category}|${t.testName}`))
  form.routine_tests.push(...newTests)
  window.toast.add({ severity: 'success', summary: 'موفق', detail: `${toFa(newTests.length)} آزمایش ثبت شد` })
}

const openRoutineCreate = () => {
  editingRoutineDate.value = null
  showRoutineModal.value = true
}

const openRoutineEdit = (date) => {
  editingRoutineDate.value = date
  showRoutineModal.value = true
}

const saveRoutineTests = ({ tests }) => {
  const remaining = form.routine_tests.filter(test => test.testDate !== editingRoutineDate.value)
  form.routine_tests.splice(0, form.routine_tests.length, ...remaining, ...tests)
  editingRoutineDate.value = null
  window.toast.add({ severity: 'success', summary: 'موفق', detail: 'آزمایش‌ها ویرایش شدند' })
}

const removeRoutineTest = (test) => {
  const index = form.routine_tests.indexOf(test)
  if (index >= 0) form.routine_tests.splice(index, 1)
}

const addViralTests = (tests) => {
  if (!tests || !tests.length) return
  const existingSet = new Set(form.viral_tests.map(t => `${t.testDate}|${t.testName}`))
  const newTests = tests.filter(t => !existingSet.has(`${t.testDate}|${t.testName}`))
  form.viral_tests.push(...newTests)
  window.toast.add({ severity: 'success', summary: 'موفق', detail: `${toFa(newTests.length)} آزمایش ویروسی ثبت شد` })
}

const openViralCreate = () => {
  editingViralDate.value = null
  showViralModal.value = true
}

const openViralEdit = (date) => {
  editingViralDate.value = date
  showViralModal.value = true
}

const saveViralTests = ({ tests }) => {
  const remaining = form.viral_tests.filter(test => test.testDate !== editingViralDate.value)
  form.viral_tests.splice(0, form.viral_tests.length, ...remaining, ...tests)
  editingViralDate.value = null
  window.toast.add({ severity: 'success', summary: 'موفق', detail: 'آزمایش‌های ویروسی ویرایش شدند' })
}

const removeViralTest = (test) => {
  const index = form.viral_tests.indexOf(test)
  if (index >= 0) form.viral_tests.splice(index, 1)
}

const goToStep = (idx) => {
  if (idx <= step.value) step.value = idx
}

const nextStep = () => {
  if (step.value === 0) {
    if (!form.first_name || !form.last_name) {
      window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'نام و نام خانوادگی الزامی است' })
      return
    }
    if (!form.national_id) {
      window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'کد ملی/پاسپورت الزامی است' })
      return
    }
    if (form.citizenship === 'iranian' && !validateNationalIdField()) return
    if (!form.gender) {
      window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'انتخاب جنسیت الزامی است' })
      return
    }
    if (!form.birth_date) {
      window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'تاریخ تولد الزامی است' })
      return
    }
    if (!form.blood_type || !form.rh_factor) {
      window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'گروه خونی الزامی است' })
      return
    }
    if (!validatePhone('phone') || !validatePhone('emergency')) return
    if (form.is_related_recipient_candidate && !form.preferred_recipient_national_id) {
      window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'کد ملی گیرنده مورد نظر الزامی است' })
      return
    }
  }
  if (step.value < 3) step.value++
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const nextOrSubmit = () => {
  if (step.value < 3) {
    nextStep()
    return
  }
  window.toast.add({ severity: 'success', summary: 'موفق', detail: 'اهداکننده با موفقیت ثبت شد' })
  setTimeout(() => router.push('/donors'), 800)
}

const prevStep = () => {
  if (step.value > 0) step.value--
}

const cancel = () => router.push('/donors')

const getApprovalClass = (s) => {
  const status = form.approvals[s]?.status
  if (status === 'approved') return 'approved'
  if (status === 'rejected') return 'rejected'
  return 'on-hold'
}

const getApprovalIcon = (s) => {
  const status = form.approvals[s]?.status
  if (status === 'approved') return 'ri-check-circle-line'
  if (status === 'rejected') return 'ri-close-circle-line'
  return 'ri-time-line'
}
</script>
