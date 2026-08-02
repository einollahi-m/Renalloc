<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">ثبت گیرنده جدید</div>
        <div class="page-subtitle">اطلاعات گیرنده را در مراحل زیر وارد کنید</div>
      </div>
      <button class="btn btn-secondary" @click="cancel"><i class="ri-close-line"></i> انصراف</button>
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

    <!-- گام ۱: اطلاعات فردی -->
    <div v-if="step===0">
      <section class="form-card">
        <div class="form-card-title"><i class="ri-id-card-line"></i> اطلاعات هویتی</div>
        <div class="form-grid form-grid-3">
          <div class="form-group">
            <label class="form-label">تابعیت *</label>
            <div class="radio-pills">
              <label class="radio-pill" :class="{checked: form.citizenship==='iranian'}"><input type="radio" v-model="form.citizenship" value="iranian" /> ایرانی</label>
              <label class="radio-pill" :class="{checked: form.citizenship==='foreign'}"><input type="radio" v-model="form.citizenship" value="foreign" /> غیر ایرانی</label>
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
              <label class="radio-pill" :class="{checked: form.gender==='male'}"><input type="radio" v-model="form.gender" value="male" /> مرد</label>
              <label class="radio-pill" :class="{checked: form.gender==='female'}"><input type="radio" v-model="form.gender" value="female" /> زن</label>
            </div>
          </div>
          <div class="form-group">
            <dual-date-field v-model="form.birth_date" label="تاریخ تولد *" />
          </div>
          <div class="form-group">
            <label class="form-label">گروه خونی *</label>
            <div class="blood-row">
              <select v-model="form.blood_type" class="form-select">
                <option value="">انتخاب</option>
                <option v-for="b in bloodTypeOptions" :key="b" :value="b">{{ b }}</option>
              </select>
              <div class="radio-pills">
                <label class="radio-pill" :class="{checked: form.rh_factor==='positive'}"><input type="radio" v-model="form.rh_factor" value="positive" /> Rh+</label>
                <label class="radio-pill" :class="{checked: form.rh_factor==='negative'}"><input type="radio" v-model="form.rh_factor" value="negative" /> Rh-</label>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="form-card">
        <div class="form-card-title"><i class="ri-phone-line"></i> اطلاعات تماس</div>
        <div class="form-grid">
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
        <div class="form-card-title"><i class="ri-user-heart-line"></i> مشخصات فردی و سبک زندگی</div>
        <div class="form-grid form-grid-4">
          <div class="form-group">
            <label class="form-label">تحصیلات</label>
            <select v-model="form.education" class="form-select">
              <option value="">انتخاب کنید</option>
              <option v-for="e in educationOptions" :key="e.value" :value="e.value">{{ e.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">بیمه</label>
            <checkbox-multi-select v-model="form.insurance" :options="insuranceOptions" placeholder="انتخاب بیمه" />
          </div>
          <div class="form-group">
            <label class="form-label">وزن (کیلوگرم)</label>
            <input type="number" v-model="newWeight" class="form-input" placeholder="مقدار" step="0.1" />
          </div>
          <div class="form-group">
            <label class="form-label">قد (سانتی‌متر)</label>
            <input type="number" v-model="newHeight" class="form-input" placeholder="اندازه قد" />
          </div>
        </div>
        <div class="form-group" style="margin-bottom:0;">
          <label class="form-label">سبک زندگی</label>
          <div class="check-chips">
            <label class="check-chip" :class="{checked: form.is_smoker}"><input type="checkbox" v-model="form.is_smoker" /><i class="ri-cigarette-line"></i> سیگاری</label>
            <label class="check-chip" :class="{checked: form.has_addiction}"><input type="checkbox" v-model="form.has_addiction" /><i class="ri-forbid-line"></i> سابقه اعتیاد</label>
            <label class="check-chip" :class="{checked: form.has_alcohol}"><input type="checkbox" v-model="form.has_alcohol" /><i class="ri-goblet-line"></i> مصرف الکل</label>
          </div>
        </div>
      </section>
    </div>

    <!-- گام ۲: اطلاعات پزشکی پایه -->
    <div v-if="step===1">
      <section class="form-card">
        <div class="form-card-title"><i class="ri-stethoscope-line"></i> وضعیت کاندید پیوند</div>
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">کاندید پیوند</label>
            <select v-model="form.transplant_candidate" class="form-select">
              <option value="">انتخاب کنید</option>
              <option v-for="t in transplantCandidateOptions" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">متقاضی پیوند از</label>
            <div class="check-chips">
              <label class="check-chip" :class="{checked: form.donor_living}"><input type="checkbox" v-model="form.donor_living" /><i class="ri-user-heart-line"></i> اهداکننده زنده</label>
              <label class="check-chip" :class="{checked: form.donor_deceased}"><input type="checkbox" v-model="form.donor_deceased" /><i class="ri-ribbon-line"></i> اهداکننده جسد</label>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- گام ۳: سوابق پزشکی -->
    <div v-if="step===2">
      <section class="form-card">
        <div class="form-card-title"><i class="ri-drop-line"></i> دیالیز و تزریق خون</div>
        <div class="form-grid">
          <div class="form-group">
            <label class="checkbox-wrap"><input type="checkbox" v-model="hasDialysisHistory" /> سابقه دیالیز</label>
            <div v-if="hasDialysisHistory" style="margin-top:10px;">
              <select v-model="form.dialysis_type" class="form-select mb-2">
                <option value="">نوع دیالیز</option>
                <option v-for="d in dialysisTypes" :key="d.value" :value="d.value">{{ d.label }}</option>
              </select>
              <dual-date-field v-model="form.dialysis_start_date" label="تاریخ شروع دیالیز" />
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-wrap"><input type="checkbox" v-model="hasBloodTransfusion" /> سابقه تزریق خون</label>
            <div v-if="hasBloodTransfusion" style="display:flex;gap:8px;align-items:center;margin-top:10px;">
              <input type="number" v-model="form.blood_transfusion_units" class="form-input" placeholder="تعداد واحد" min="0" />
              <span>واحد</span>
            </div>
          </div>
        </div>
      </section>

      <section v-if="form.gender==='female'" class="form-card">
        <div class="form-card-title"><i class="ri-women-line"></i> سوابق زنان و زایمان</div>
        <div class="form-grid">
          <div class="form-group">
            <label class="checkbox-wrap"><input type="checkbox" v-model="hasPregnancyHistory" /> سابقه بارداری</label>
            <input v-if="hasPregnancyHistory" type="number" v-model="form.pregnancy_count" class="form-input mt-2" placeholder="تعداد بارداری" min="0" />
          </div>
          <div class="form-group" v-if="hasPregnancyHistory">
            <label class="checkbox-wrap"><input type="checkbox" v-model="hasAbortionHistory" /> سابقه سقط</label>
            <input v-if="hasAbortionHistory" type="number" v-model="form.abortion_count" class="form-input mt-2" placeholder="تعداد سقط" min="0" />
          </div>
        </div>
      </section>

      <section class="form-card">
        <div class="form-card-title"><i class="ri-file-list-line"></i> سایر سوابق پزشکی</div>
        <div class="form-grid">
          <div class="form-group">
            <label class="checkbox-wrap"><input type="checkbox" v-model="form.previous_transplant" /> سابقه پیوند قبلی</label>
            <textarea v-if="form.previous_transplant" v-model="form.previous_transplant_details" class="form-input mt-2" rows="2" placeholder="جزئیات پیوند قبلی"></textarea>
          </div>
          <div class="form-group">
            <label class="checkbox-wrap"><input type="checkbox" v-model="form.has_drug_allergy" /> حساسیت دارویی</label>
            <textarea v-if="form.has_drug_allergy" v-model="form.drug_allergy_details" class="form-input mt-2" rows="2" placeholder="نام دارو و علائم"></textarea>
          </div>
          <div class="form-group">
            <label class="checkbox-wrap"><input type="checkbox" v-model="form.family_kidney_disease" /> سابقه بیماری کلیوی در خانواده</label>
            <textarea v-if="form.family_kidney_disease" v-model="form.family_kidney_disease_details" class="form-input mt-2" rows="2" placeholder="جزئیات"></textarea>
          </div>
        </div>
      </section>
    </div>

    <!-- گام ۴: ایمونولوژی -->
    <div v-if="step===3">
      <div class="accordion mb-4">
        <div class="accordion-item" :class="{open:openAccordion.cdc}">
          <div class="accordion-header" @click="openAccordion.cdc=!openAccordion.cdc">
            <span><i class="ri-shield-check-line" style="color:var(--color-primary);"></i> CDC PRA</span>
            <i class="ri-arrow-down-s-line"></i>
          </div>
          <div class="accordion-content">
            <div class="grid grid-2">
              <div>
                <h4 style="margin-bottom:12px;">Class I</h4>
                <div class="form-group">
                  <label class="form-label">وضعیت</label>
                  <select v-model="form.cdc_pra.class_i.status" class="form-select">
                    <option value="">انتخاب کنید</option>
                    <option value="negative">منفی</option>
                    <option value="positive">مثبت</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">درصد</label>
                  <input type="number" v-model="form.cdc_pra.class_i.value" class="form-input" placeholder="٪" min="0" max="100" />
                </div>
              </div>
              <div>
                <h4 style="margin-bottom:12px;">Class II</h4>
                <div class="form-group">
                  <label class="form-label">وضعیت</label>
                  <select v-model="form.cdc_pra.class_ii.status" class="form-select">
                    <option value="">انتخاب کنید</option>
                    <option value="negative">منفی</option>
                    <option value="positive">مثبت</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">درصد</label>
                  <input type="number" v-model="form.cdc_pra.class_ii.value" class="form-input" placeholder="٪" min="0" max="100" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="accordion mb-4">
        <div class="accordion-item" :class="{open:openAccordion.hla}">
          <div class="accordion-header" @click="openAccordion.hla=!openAccordion.hla">
            <span><i class="ri-dna-line" style="color:var(--color-primary);"></i> تایپ HLA</span>
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
        <div class="accordion-item" :class="{open:openAccordion.antiHla}">
          <div class="accordion-header" @click="openAccordion.antiHla=!openAccordion.antiHla">
            <span><i class="ri-flask-line" style="color:var(--color-primary);"></i> آنتی‌بادی Anti-HLA</span>
            <i class="ri-arrow-down-s-line"></i>
          </div>
          <div class="accordion-content">
            <div class="flex justify-between items-center mb-3">
              <h4 style="margin:0;">نتایج ثبت شده</h4>
              <button class="btn btn-sm btn-primary" type="button" @click="showAntiHlaModal=true"><i class="ri-add-line"></i> افزودن نتیجه جدید</button>
            </div>
            <div v-if="!form.anti_hla_display.length" class="empty-state" style="padding:22px;">
              <i class="ri-flask-line"></i>
              <h3>نتیجه‌ای ثبت نشده</h3>
            </div>
            <table v-else class="data-table">
              <thead><tr><th>تاریخ</th><th>Locus</th><th>آنتی‌ژن</th><th>Class</th><th>MFI</th></tr></thead>
              <tbody>
                <tr v-for="t in form.anti_hla_display" :key="t.key">
                  <td>{{ formatFaDate(t.testDate) }}</td>
                  <td>{{ t.locus }}</td>
                  <td>{{ t.testName.split(' - ')[1] }}</td>
                  <td><span class="badge" :class="t.class==='I'?'badge-info':'badge-success'">{{ t.class }}</span></td>
                  <td class="font-bold">{{ t.mfi || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- گام ۵: آزمایش‌ها -->
    <div v-if="step===4">
      <div class="accordion mb-4">
        <div class="accordion-item" :class="{open:openAccordion.routine}">
          <div class="accordion-header" @click="openAccordion.routine=!openAccordion.routine">
            <span><i class="ri-flask-line" style="color:var(--color-primary);"></i> آزمایش‌های پیوند</span>
            <i class="ri-arrow-down-s-line"></i>
          </div>
          <div class="accordion-content">
            <div class="flex justify-between items-center mb-3">
              <h4 style="margin:0;">نتایج ثبت شده</h4>
              <button class="btn btn-sm btn-primary" type="button" @click="showRoutineModal=true"><i class="ri-add-line"></i> افزودن آزمایش جدید</button>
            </div>
            <div v-if="!form.routine_tests.length" class="empty-state" style="padding:22px;">
              <i class="ri-flask-line"></i>
              <h3>آزمایش ثبت نشده</h3>
            </div>
            <table v-else class="data-table">
              <thead><tr><th>تاریخ</th><th>دسته</th><th>نام آزمایش</th><th>مقدار</th></tr></thead>
              <tbody>
                <tr v-for="t in form.routine_tests" :key="t.testDate+t.category+t.testName">
                  <td>{{ formatFaDate(t.testDate) }}</td>
                  <td>{{ t.category }}</td>
                  <td>{{ t.testName }}</td>
                  <td class="font-bold">{{ t.value }}</td>
                </tr>
              </tbody>
            </table>
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
              <button class="btn btn-sm btn-primary" type="button" @click="showViralModal=true"><i class="ri-add-line"></i> افزودن آزمایش جدید</button>
            </div>
            <div v-if="!form.viral_tests.length" class="empty-state" style="padding:22px;">
              <i class="ri-virus-line"></i>
              <h3>آزمایش ثبت نشده</h3>
            </div>
            <table v-else class="data-table">
              <thead><tr><th>تاریخ</th><th>نام آزمایش</th><th>نتیجه</th></tr></thead>
              <tbody>
                <tr v-for="t in form.viral_tests" :key="t.testDate+t.testName">
                  <td>{{ formatFaDate(t.testDate) }}</td>
                  <td>{{ t.testName }}</td>
                  <td class="font-bold">{{ t.value }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- گام ۶: تاییدیه‌ها -->
    <div v-if="step===5">
      <div class="accordion">
        <div class="accordion-item" :class="{open:openAccordion.approvals}">
          <div class="accordion-header" @click="openAccordion.approvals=!openAccordion.approvals">
            <span><i class="ri-checkbox-circle-line" style="color:var(--color-primary);"></i> تاییدیه‌های پزشکی</span>
            <i class="ri-arrow-down-s-line"></i>
          </div>
          <div class="accordion-content">
            <div class="specialties-header">
              <button v-for="spec in specialties" :key="spec.key" type="button" class="specialty-tab"
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
                  <input type="text" v-model="form.approvals[activeSpecialty].medical_code" class="form-input" placeholder="کد نظام پزشکی" />
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

    <div class="form-actions">
      <button class="btn btn-secondary" @click="prevStep" :disabled="step===0">
        <i class="ri-arrow-right-line"></i> گام قبل
      </button>
      <div class="flex gap-2">
        <button class="btn btn-secondary" @click="cancel">لغو</button>
        <button class="btn btn-primary" @click="nextOrSubmit">
          <template v-if="step<5">گام بعد <i class="ri-arrow-left-line"></i></template>
          <template v-else><i class="ri-save-line"></i> ثبت گیرنده</template>
        </button>
      </div>
    </div>

    <routine-tests-modal v-model:visible="showRoutineModal" :gender="form.gender" @add="addRoutineTests" />
    <viral-tests-modal v-model:visible="showViralModal" @add="addViralTests" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { toFaDigits, formatFaDate } from '../utils/date'
import { nationalIdChecker, normalizeNationalId, normalizeIranianMobile, isValidIranianMobile } from '../utils/validation'
import { mockRecipients } from '../data/mockData'
import { hlaOptions, antiHlaAOptions, antiHlaBOptions, antiHlaCOptions, antiHlaDRB1Options, antiHlaDQB1Options, antiHlaDRB345Options } from '../data/hlaOptions'
import { educationOptions, insuranceOptions, nationalityOptions, bloodTypeOptions, dialysisTypes, transplantCandidateOptions, esrdCauseOptions, approvalStatusOptions, specialties } from '../data/options'

const router = useRouter()
const step = ref(0)
const steps = ['اطلاعات فردی', 'پزشکی پایه', 'سوابق', 'ایمونولوژی', 'آزمایش‌ها', 'تاییدیه‌ها']
const toFa = toFaDigits

const form = reactive({
  citizenship: 'iranian', national_id: '', first_name: '', last_name: '', gender: null,
  blood_type: null, rh_factor: null, phone: '', emergency_contact_phone: '',
  education: null, insurance: [], nationality: '', birth_date: '',
  is_smoker: false, has_addiction: false, has_alcohol: false,
  transplant_candidate: null, donor_living: false, donor_deceased: false,
  dialysis_type: null, dialysis_start_date: null, blood_transfusion_units: null,
  pregnancy_count: null, abortion_count: null,
  previous_transplant: false, previous_transplant_details: '',
  drug_history: '', has_drug_allergy: false, drug_allergy_details: '',
  underlying_diseases: '', family_kidney_disease: false, family_kidney_disease_details: '',
  cdc_pra: { class_i: { status: null, value: null }, class_ii: { status: null, value: null } },
  hla_a: [], hla_b: [], hla_c: [], hla_drb1: [], hla_dqb1: [], hla_drb: [],
  anti_hla_display: [], routine_tests: [], viral_tests: [],
  approvals: {
    nephrologist: { status: 'on_hold', approval_date: '', doctor_name: '', medical_code: '', notes: '' },
    dentist: { status: 'on_hold', approval_date: '', doctor_name: '', medical_code: '', notes: '' },
    cardiologist: { status: 'on_hold', approval_date: '', doctor_name: '', medical_code: '', notes: '' },
    gastroenterologist: { status: 'on_hold', approval_date: '', doctor_name: '', medical_code: '', notes: '' },
    urologist: { status: 'on_hold', approval_date: '', doctor_name: '', medical_code: '', notes: '' }
  }
})

const hasDialysisHistory = ref(false)
const hasBloodTransfusion = ref(false)
const hasPregnancyHistory = ref(false)
const hasAbortionHistory = ref(false)
const newWeight = ref(null)
const newHeight = ref(null)
const activeSpecialty = ref('nephrologist')
const openAccordion = reactive({ cdc: true, hla: true, antiHla: true, routine: true, viral: true, approvals: true })
const showAntiHlaModal = ref(false)
const showRoutineModal = ref(false)
const showViralModal = ref(false)
const antiHlaForm = reactive({ testDate: '', selectedA: [], selectedB: [], selectedC: [], selectedDRB1: [], selectedDQB1: [], selectedDRB345: [] })
const nationalIdError = ref('')
const nationalIdChecking = ref(false)
const nationalIdValidated = ref(false)
const phoneErrors = reactive({ phone: '', emergency: '' })

const isNationalIdValid = computed(() => form.citizenship === 'iranian' && nationalIdValidated.value && !nationalIdError.value)

watch(hasPregnancyHistory, (v) => { if (!v) { hasAbortionHistory.value = false; form.abortion_count = null; } })

const normalizeAndValidateNationalId = (e) => {
  if (form.citizenship === 'foreign') {
    form.national_id = e.target.value.trim().toUpperCase()
    nationalIdError.value = ''
    nationalIdValidated.value = false
    return
  }
  const val = normalizeNationalId(e.target.value).slice(0, 10)
  form.national_id = val
  nationalIdError.value = ''
  nationalIdValidated.value = false
  if (val.length > 0 && val.length < 10) {
    nationalIdError.value = 'کد ملی باید ۱۰ رقم باشد'
    return
  }
  if (val.length === 10) {
    nationalIdChecking.value = true
    setTimeout(() => {
      const valid = nationalIdChecker(val)
      nationalIdError.value = valid ? '' : 'کد ملی نامعتبر است'
      nationalIdValidated.value = valid
      nationalIdChecking.value = false
    }, 300)
  }
}

const validateNationalIdField = () => {
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
  const key = field === 'phone' ? 'phone' : 'emergency'
  const val = normalizeIranianMobile(form[key])
  if (!val) {
    phoneErrors[key] = ''
    return true
  }
  if (!isValidIranianMobile(val)) {
    phoneErrors[key] = 'شماره موبایل باید ۱۱ رقم و با 09 شروع شود'
    return false
  }
  phoneErrors[key] = ''
  return true
}

const addAntiHlaAntibodies = () => {
  if (!antiHlaForm.testDate) {
    window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'تاریخ آزمایش الزامی است' })
    return
  }
  const add = (locus, selected, cls) => {
    selected.forEach(antigen => {
      form.anti_hla_display.push({
        key: `${antiHlaForm.testDate}-${locus}-${antigen}`,
        class: cls, locus,
        testName: `${locus} - ${antigen}`,
        value: null, mfi: null,
        testDate: antiHlaForm.testDate
      })
    })
  }
  add('A', antiHlaForm.selectedA, 'I')
  add('B', antiHlaForm.selectedB, 'I')
  add('C', antiHlaForm.selectedC, 'I')
  add('DRB1', antiHlaForm.selectedDRB1, 'II')
  add('DQB1', antiHlaForm.selectedDQB1, 'II')
  add('DRB345', antiHlaForm.selectedDRB345, 'II')
  showAntiHlaModal.value = false
  antiHlaForm.selectedA = []
  antiHlaForm.selectedB = []
  antiHlaForm.selectedC = []
  antiHlaForm.selectedDRB1 = []
  antiHlaForm.selectedDQB1 = []
  antiHlaForm.selectedDRB345 = []
  antiHlaForm.testDate = ''
  window.toast.add({ severity: 'success', summary: 'موفق', detail: 'آنتی‌بادی‌ها ثبت شدند' })
}

const addRoutineTests = (tests) => {
  if (!tests || !tests.length) return
  const existingSet = new Set(form.routine_tests.map(t => `${t.testDate}|${t.category}|${t.testName}`))
  const newTests = tests.filter(t => !existingSet.has(`${t.testDate}|${t.category}|${t.testName}`))
  form.routine_tests.push(...newTests)
  window.toast.add({ severity: 'success', summary: 'موفق', detail: `${toFa(newTests.length)} آزمایش ثبت شد` })
}

const addViralTests = (tests) => {
  if (!tests || !tests.length) return
  const existingSet = new Set(form.viral_tests.map(t => `${t.testDate}|${t.testName}`))
  const newTests = tests.filter(t => !existingSet.has(`${t.testDate}|${t.testName}`))
  form.viral_tests.push(...newTests)
  window.toast.add({ severity: 'success', summary: 'موفق', detail: `${toFa(newTests.length)} آزمایش ویروسی ثبت شد` })
}

const goToStep = (idx) => { if (idx <= step.value) step.value = idx }

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
    if (!form.birth_date) {
      window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'تاریخ تولد الزامی است' })
      return
    }
    if (!form.blood_type || !form.rh_factor) {
      window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'گروه خونی الزامی است' })
      return
    }
    if (!validatePhone('phone') || !validatePhone('emergency')) return
  }
  if (step.value < 5) step.value++
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const nextOrSubmit = () => {
  if (step.value < 5) {
    nextStep()
    return
  }
  window.toast.add({ severity: 'success', summary: 'موفق', detail: 'گیرنده با موفقیت ثبت شد' })
  setTimeout(() => router.push('/recipients'), 800)
}

const prevStep = () => { if (step.value > 0) step.value-- }

const cancel = () => router.push('/recipients')

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
