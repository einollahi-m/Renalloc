<template>
  <div class="create-person-page" @input.capture="normalizeNumericInputEvent">
    <div class="page-header">
      <div>
        <div class="page-title">ثبت گیرنده جدید</div>
        <div class="page-subtitle">اطلاعات گیرنده را در مراحل زیر وارد کنید</div>
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

    <!-- گام ۱: اطلاعات فردی -->
    <div v-if="step===0">
      <section class="form-card">
        <div class="form-card-title"><i class="ri-profile-line"></i> اطلاعات هویتی</div>
        <div class="form-grid identity-primary-grid" :class="{'is-foreign': form.citizenship==='foreign'}">
          <div class="form-group">
            <label class="form-label">تابعیت *</label>
            <div class="segmented-toggle" role="radiogroup" aria-label="تابعیت">
              <label class="toggle-option" :class="{checked: form.citizenship==='iranian'}"><input type="radio" name="recipient-citizenship" v-model="form.citizenship" value="iranian" /> ایرانی</label>
              <label class="toggle-option" :class="{checked: form.citizenship==='foreign'}"><input type="radio" name="recipient-citizenship" v-model="form.citizenship" value="foreign" /> غیر ایرانی</label>
            </div>
          </div>
          <div class="form-group identity-id-field">
            <label class="form-label">{{ form.citizenship === 'iranian' ? 'کد ملی (۱۰ رقم) *' : 'شماره گذرنامه *' }}</label>
            <div class="validation-control" :class="{'is-valid':isNationalIdValid,'is-invalid':nationalIdError}">
              <input type="text" v-model="form.national_id" class="form-input" :aria-invalid="Boolean(nationalIdError)" @input="normalizeAndValidateNationalId" @blur="validateNationalIdField" :maxlength="form.citizenship==='iranian'?10:null" :inputmode="form.citizenship==='iranian'?'numeric':'text'" :placeholder="form.citizenship==='iranian'?'مثال: ۰۰۱۳۵۴۸۷۹۴':'شماره گذرنامه'" />
              <i v-if="identifierChecking" class="ri-loader-4-line validation-icon" aria-label="در حال بررسی"></i>
              <i v-else-if="isNationalIdValid" class="ri-checkbox-circle-fill validation-icon" aria-label="معتبر"></i>
              <i v-else-if="nationalIdError" class="ri-close-circle-fill validation-icon" aria-label="نامعتبر"></i>
            </div>
            <div v-if="nationalIdError" class="field-feedback is-error">{{ nationalIdError }}</div>
            <div v-else-if="identifierChecking" class="field-feedback">در حال بررسی یکتایی شناسه…</div>
            <div v-else-if="isNationalIdValid" class="field-feedback is-success">شناسه معتبر و قابل ثبت است</div>
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
            <div class="segmented-toggle" role="radiogroup" aria-label="جنسیت">
              <label class="toggle-option" :class="{checked: form.gender==='male'}"><input type="radio" name="recipient-gender" v-model="form.gender" value="male" /> مرد</label>
              <label class="toggle-option" :class="{checked: form.gender==='female'}"><input type="radio" name="recipient-gender" v-model="form.gender" value="female" /> زن</label>
            </div>
          </div>
          <div class="form-group identity-birth-field">
            <dual-date-field v-model="form.birth_date" label="تاریخ تولد *" />
          </div>
          <div class="form-group identity-blood-field">
            <label class="form-label">گروه خونی *</label>
            <select v-model="bloodGroup" class="form-select">
              <option value="">انتخاب گروه خونی</option>
              <option v-for="b in bloodGroupOptions" :key="b" :value="b">{{ b }}</option>
            </select>
          </div>
        </div>
      </section>

      <section class="form-card">
        <div class="form-card-title"><i class="ri-phone-line"></i> اطلاعات تماس</div>
        <div class="form-grid contact-fields-grid">
          <div class="form-group">
            <label class="form-label">شماره موبایل *</label>
            <div class="validation-control" :class="{'is-valid':isPhoneValid('phone'),'is-invalid':phoneErrors.phone}">
              <input type="text" v-model="form.phone" class="form-input" :aria-invalid="Boolean(phoneErrors.phone)" @input="normalizePhone('phone',$event)" @blur="validatePhone('phone')" maxlength="11" inputmode="numeric" placeholder="مثال: ۰۹۱۲۱۲۳۴۵۶۷" />
              <i v-if="isPhoneValid('phone')" class="ri-checkbox-circle-fill validation-icon" aria-label="معتبر"></i>
              <i v-else-if="phoneErrors.phone" class="ri-close-circle-fill validation-icon" aria-label="نامعتبر"></i>
            </div>
            <div v-if="phoneErrors.phone" class="field-feedback is-error">{{ phoneErrors.phone }}</div>
            <div v-else-if="isPhoneValid('phone')" class="field-feedback is-success">شماره موبایل معتبر است</div>
          </div>
          <div class="form-group">
            <label class="form-label">شماره موبایل اضطراری</label>
            <div class="validation-control" :class="{'is-valid':isPhoneValid('emergency'),'is-invalid':phoneErrors.emergency}">
              <input type="text" v-model="form.emergency_contact_phone" class="form-input" :aria-invalid="Boolean(phoneErrors.emergency)" @input="normalizePhone('emergency',$event)" @blur="validatePhone('emergency')" maxlength="11" inputmode="numeric" placeholder="مثال: ۰۹۱۲۱۲۳۴۵۶۷" />
              <i v-if="isPhoneValid('emergency')" class="ri-checkbox-circle-fill validation-icon" aria-label="معتبر"></i>
              <i v-else-if="phoneErrors.emergency" class="ri-close-circle-fill validation-icon" aria-label="نامعتبر"></i>
            </div>
            <div v-if="phoneErrors.emergency" class="field-feedback is-error">{{ phoneErrors.emergency }}</div>
            <div v-else-if="isPhoneValid('emergency')" class="field-feedback is-success">شماره موبایل معتبر است</div>
          </div>
        </div>
      </section>

      <section class="form-card">
        <div class="form-card-title"><i class="ri-user-heart-line"></i> مشخصات فردی</div>
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
            <div class="segmented-toggle" role="radiogroup" aria-label="وضعیت تأهل">
              <label class="toggle-option" :class="{checked: form.marital_status==='single'}"><input type="radio" name="recipient-marital-status" v-model="form.marital_status" value="single" /> مجرد</label>
              <label class="toggle-option" :class="{checked: form.marital_status==='married'}"><input type="radio" name="recipient-marital-status" v-model="form.marital_status" value="married" /> متأهل</label>
            </div>
          </div>
          <div class="form-group measure-field">
            <label class="form-label" for="recipient-weight">وزن (کیلوگرم)</label>
            <input id="recipient-weight" type="text" v-model="newWeight" class="form-input" placeholder="مقدار وزن به کیلوگرم" inputmode="decimal" @keydown.up.prevent="adjustWeight(0.5)" @keydown.down.prevent="adjustWeight(-0.5)" />
          </div>
          <div class="form-group measure-field">
            <label class="form-label" for="recipient-height">قد (سانتی‌متر)</label>
            <input id="recipient-height" type="text" v-model="newHeight" class="form-input" placeholder="اندازه قد به سانتی‌متر" inputmode="numeric" />
          </div>
        </div>
        <div class="risk-disclosure" :class="{open:riskOpen}">
          <button type="button" class="risk-disclosure-trigger" :aria-expanded="riskOpen" @click="riskOpen=!riskOpen">
            <span><i class="ri-shield-flash-line"></i> رفتارهای پرخطر</span>
            <span class="risk-disclosure-summary"><i class="ri-lock-2-line"></i> اطلاعات محرمانه</span>
            <i class="ri-arrow-down-s-line risk-disclosure-caret"></i>
          </button>
          <div v-show="riskOpen" class="risk-disclosure-content">
            <div class="check-chips">
              <label class="check-chip" :class="{checked: form.is_smoker}"><input type="checkbox" v-model="form.is_smoker" /><i class="ri-cigarette-line"></i> سیگاری</label>
              <label class="check-chip" :class="{checked: form.has_addiction}"><input type="checkbox" v-model="form.has_addiction" /><i class="ri-forbid-line"></i> سابقه اعتیاد</label>
              <label class="check-chip" :class="{checked: form.has_alcohol}"><input type="checkbox" v-model="form.has_alcohol" /><i class="ri-goblet-line"></i> مصرف الکل</label>
            </div>
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
            <label class="form-label">متقاضی پیوند از *</label>
            <div class="check-chips required-choice-group" :class="{'choice-error': donorSourceError}">
              <label class="check-chip" :class="{checked: form.donor_living}"><input type="checkbox" v-model="form.donor_living" @change="donorSourceError=''" /><i class="ri-user-heart-line"></i> اهداکننده زنده</label>
              <label class="check-chip" :class="{checked: form.donor_deceased}"><input type="checkbox" v-model="form.donor_deceased" @change="donorSourceError=''" /><i class="ri-ribbon-line"></i> اهداکننده جسد</label>
            </div>
            <div v-if="donorSourceError" class="form-error">{{ donorSourceError }}</div>
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
              <input type="text" v-model="form.blood_transfusion_units" class="form-input" placeholder="تعداد واحد" inputmode="numeric" />
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
            <input v-if="hasPregnancyHistory" type="text" v-model="form.pregnancy_count" class="form-input mt-2" placeholder="تعداد بارداری" inputmode="numeric" />
          </div>
          <div class="form-group" v-if="hasPregnancyHistory">
            <label class="checkbox-wrap"><input type="checkbox" v-model="hasAbortionHistory" /> سابقه سقط</label>
            <input v-if="hasAbortionHistory" type="text" v-model="form.abortion_count" class="form-input mt-2" placeholder="تعداد سقط" inputmode="numeric" />
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
            <div class="flex justify-between items-center mb-3">
              <h4 style="margin:0;">نتایج ثبت شده</h4>
              <button class="btn btn-sm btn-primary" type="button" @click="openCdcCreate">
                <i class="ri-add-line"></i> افزودن آزمایش جدید
              </button>
            </div>
            <div v-if="!form.cdc_pra_tests.length" class="empty-state compact-empty-state">
              <i class="ri-shield-check-line"></i>
              <h3>آزمایش CDC PRA ثبت نشده است</h3>
              <p>ثبت این آزمایش برای ثبت‌نام اولیه اختیاری است.</p>
            </div>
            <div v-else class="result-batches">
              <article v-for="test in form.cdc_pra_tests" :key="test.id" class="result-batch">
                <header class="result-batch-header">
                  <div class="result-batch-date">
                    <i class="ri-calendar-check-line"></i>
                    <span>{{ formatFaDate(test.performed_at) }}</span>
                  </div>
                  <div class="record-actions">
                    <button type="button" class="record-action edit" title="ویرایش" @click="openCdcEdit(test)"><i class="ri-edit-line"></i></button>
                    <button type="button" class="record-action delete" title="حذف" @click="removeCdcTest(test)"><i class="ri-delete-bin-6-line"></i></button>
                  </div>
                </header>
                <div class="result-badges">
                  <span :class="['badge', test.class_i.status === 'positive' ? 'badge-warning' : 'badge-success']">
                    Class I: {{ cdcStatusLabel(test.class_i.status) }}<template v-if="test.class_i.value !== null && test.class_i.value !== ''">، {{ toFa(test.class_i.value) }}٪</template>
                  </span>
                  <span :class="['badge', test.class_ii.status === 'positive' ? 'badge-warning' : 'badge-success']">
                    Class II: {{ cdcStatusLabel(test.class_ii.status) }}<template v-if="test.class_ii.value !== null && test.class_ii.value !== ''">، {{ toFa(test.class_ii.value) }}٪</template>
                  </span>
                </div>
              </article>
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
              <button class="btn btn-sm btn-primary" type="button" @click="openAntiHlaCreate"><i class="ri-add-line"></i> افزودن نتیجه جدید</button>
            </div>
            <div v-if="!antiHlaBatches.length" class="empty-state compact-empty-state">
              <i class="ri-flask-line"></i>
              <h3>نتیجه‌ای ثبت نشده</h3>
            </div>
            <div v-else class="result-batches">
              <article v-for="batch in antiHlaBatches" :key="batch.id" class="result-batch">
                <header class="result-batch-header">
                  <div class="result-batch-date">
                    <i class="ri-calendar-check-line"></i>
                    <span>{{ formatFaDate(batch.testDate) }}</span>
                    <span class="badge badge-secondary">{{ toFa(batch.records.length) }} مورد</span>
                  </div>
                  <div class="record-actions">
                    <button type="button" class="record-action edit" title="ویرایش" @click="openAntiHlaEdit(batch)"><i class="ri-edit-line"></i></button>
                    <button type="button" class="record-action delete" title="حذف" @click="removeAntiHlaBatch(batch)"><i class="ri-delete-bin-6-line"></i></button>
                  </div>
                </header>
                <div class="result-badges">
                  <span v-for="record in batch.records" :key="record.key" class="anti-hla-result-badge" dir="ltr">
                    <span class="badge" :class="record.class==='I' ? 'badge-info' : 'badge-success'">Class {{ record.class }}</span>
                    <span>{{ record.antigen || record.testName.split(' - ').pop() }}</span>
                  </span>
                </div>
              </article>
            </div>
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

    <div class="form-actions sticky-form-footer">
      <button v-if="step>0" class="form-back-link" type="button" @click="prevStep">
        <i class="ri-arrow-right-line"></i> گام قبلی
      </button>
      <span v-else class="form-back-placeholder" aria-hidden="true"></span>
      <div class="form-action-end">
        <button class="btn btn-cancel" type="button" @click="cancel">
          <i class="ri-close-line"></i> انصراف
        </button>
        <button class="btn btn-primary btn-lg form-next-button" type="button" :disabled="submitting" @click="nextOrSubmit">
          <template v-if="step < 5">گام بعدی <i class="ri-arrow-left-line"></i></template>
          <template v-else-if="submitting"><i class="ri-loader-4-line"></i> در حال ثبت…</template>
          <template v-else><i class="ri-save-line"></i> تایید و ثبت گیرنده جدید</template>
        </button>
      </div>
    </div>

    <cdc-pra-modal
      v-model:visible="showCdcModal"
      :test="editingCdcTest"
      :existing-tests="form.cdc_pra_tests"
      @save="saveCdcTest"
    />
    <anti-hla-modal v-model:visible="showAntiHlaModal" :edit-batch="editingAntiHlaBatch" @save="saveAntiHlaBatch" />
    <routine-tests-modal v-model:visible="showRoutineModal" :gender="form.gender" :edit-date="editingRoutineDate" :existing-tests="editingRoutineTests" @add="addRoutineTests" @save="saveRoutineTests" />
    <viral-tests-modal v-model:visible="showViralModal" :edit-date="editingViralDate" :existing-tests="editingViralTests" @add="addViralTests" @save="saveViralTests" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { toFaDigits, formatFaDate } from '../utils/date'
import { nationalIdChecker, normalizeNationalId, normalizeIranianMobile, isValidIranianMobile, normalizeLocalizedDigits, normalizeLocalizedNumber, normalizeLocalizedSignedNumber } from '../utils/validation'
import { hlaOptions } from '../data/hlaOptions'
import { educationOptions, insuranceOptions, nationalityOptions, bloodGroupOptions, dialysisTypes, transplantCandidateOptions, esrdCauseOptions, approvalStatusOptions, specialties } from '../data/options'
import { loadFormDraft, useFormDraft } from '../composables/useFormDraft'
import { registryApi } from '../services/api'
import CdcPraModal from '../components/CdcPraModal.vue'
import AntiHlaModal from '../components/AntiHlaModal.vue'
import TestResultsList from '../components/TestResultsList.vue'

const router = useRouter()
const DRAFT_KEY = 'renalloc:recipient-create-draft'
const step = ref(0)
const steps = ['اطلاعات فردی', 'اطلاعات پزشکی پایه', 'سوابق', 'ایمونولوژی', 'آزمایش‌ها', 'تاییدیه‌ها']
const toFa = toFaDigits

const form = reactive({
  citizenship: 'iranian', national_id: '', first_name: '', last_name: '', gender: null,
  blood_type: null, rh_factor: null, phone: '', emergency_contact_phone: '',
  education: null, insurance: [], marital_status: null, nationality: '', birth_date: '',
  is_smoker: false, has_addiction: false, has_alcohol: false,
  transplant_candidate: null, donor_living: false, donor_deceased: false,
  dialysis_type: null, dialysis_start_date: null, blood_transfusion_units: null,
  pregnancy_count: null, abortion_count: null,
  previous_transplant: false, previous_transplant_details: '',
  drug_history: '', has_drug_allergy: false, drug_allergy_details: '',
  underlying_diseases: '', family_kidney_disease: false, family_kidney_disease_details: '',
  cdc_pra_tests: [],
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
const riskOpen = ref(false)
const activeSpecialty = ref('nephrologist')
const openAccordion = reactive({ cdc: true, hla: true, antiHla: true, routine: true, viral: true, approvals: true })
const showCdcModal = ref(false)
const showAntiHlaModal = ref(false)
const showRoutineModal = ref(false)
const showViralModal = ref(false)
const editingCdcTest = ref(null)
const editingAntiHlaBatch = ref(null)
const editingRoutineDate = ref(null)
const editingViralDate = ref(null)
const nationalIdError = ref('')
const nationalIdValidated = ref(false)
const identifierAvailable = ref(null)
const identifierChecking = ref(false)
const phoneErrors = reactive({ phone: '', emergency: '' })
const donorSourceError = ref('')
const submitting = ref(false)
let identifierCheckTimer = null
let identifierCheckSequence = 0

const restoredDraft = loadFormDraft(DRAFT_KEY)
if (restoredDraft?.form) {
  Object.assign(form, restoredDraft.form)
  if (!Array.isArray(form.cdc_pra_tests)) form.cdc_pra_tests = []
  const legacyCdc = restoredDraft.form.cdc_pra
  if (!form.cdc_pra_tests.length && legacyCdc && typeof legacyCdc === 'object') {
    const hasLegacyValue = Boolean(
      legacyCdc.test_date || legacyCdc.performed_at ||
      legacyCdc.class_i?.status || legacyCdc.class_i?.value != null ||
      legacyCdc.class_ii?.status || legacyCdc.class_ii?.value != null
    )
    if (hasLegacyValue) {
      form.cdc_pra_tests.push({
        id: `cdc-draft-${Date.now()}`,
        performed_at: legacyCdc.performed_at || legacyCdc.test_date || '',
        class_i: { status: legacyCdc.class_i?.status || '', value: legacyCdc.class_i?.value ?? '' },
        class_ii: { status: legacyCdc.class_ii?.status || '', value: legacyCdc.class_ii?.value ?? '' }
      })
    }
  }
  form.cdc_pra_tests = form.cdc_pra_tests.map((test, index) => ({
    id: test?.id || `cdc-draft-${Date.now()}-${index}`,
    performed_at: String(test?.performed_at || test?.test_date || '').split('T')[0],
    class_i: { status: test?.class_i?.status || '', value: test?.class_i?.value ?? '' },
    class_ii: { status: test?.class_ii?.status || '', value: test?.class_ii?.value ?? '' }
  }))
  delete form.cdc_pra
  step.value = Math.min(5, Math.max(0, Number(restoredDraft.step) || 0))
  hasDialysisHistory.value = Boolean(restoredDraft.hasDialysisHistory)
  hasBloodTransfusion.value = Boolean(restoredDraft.hasBloodTransfusion)
  hasPregnancyHistory.value = Boolean(restoredDraft.hasPregnancyHistory)
  hasAbortionHistory.value = Boolean(restoredDraft.hasAbortionHistory)
  newWeight.value = restoredDraft.newWeight ?? null
  newHeight.value = restoredDraft.newHeight ?? null
  activeSpecialty.value = restoredDraft.activeSpecialty || 'nephrologist'
  const restoredNationalId = normalizeNationalId(form.national_id)
  if (form.citizenship === 'iranian' && restoredNationalId.length === 10) {
    nationalIdValidated.value = nationalIdChecker(restoredNationalId)
    nationalIdError.value = nationalIdValidated.value ? '' : 'کد ملی نامعتبر است'
    if (nationalIdValidated.value) queueMicrotask(() => scheduleIdentifierCheck())
  }
  queueMicrotask(() => window.toast?.add({ severity: 'info', summary: 'بازیابی فرم', detail: 'اطلاعات ذخیره‌شده فرم بازیابی شد' }))
}

const { clearDraft } = useFormDraft(DRAFT_KEY, () => ({
  step: step.value,
  form,
  hasDialysisHistory: hasDialysisHistory.value,
  hasBloodTransfusion: hasBloodTransfusion.value,
  hasPregnancyHistory: hasPregnancyHistory.value,
  hasAbortionHistory: hasAbortionHistory.value,
  newWeight: newWeight.value,
  newHeight: newHeight.value,
  activeSpecialty: activeSpecialty.value
}))

const isNationalIdValid = computed(() => {
  const locallyValid = form.citizenship === 'iranian'
    ? nationalIdValidated.value
    : Boolean(String(form.national_id || '').trim())
  return locallyValid && identifierAvailable.value === true && !nationalIdError.value
})
const bloodGroup = computed({
  get: () => form.blood_type && form.rh_factor
    ? `${form.blood_type}${form.rh_factor === 'positive' ? '+' : '-'}`
    : '',
  set: value => {
    const match = /^(AB|A|B|O)([+-])$/.exec(value)
    form.blood_type = match?.[1] || null
    form.rh_factor = match?.[2] === '+' ? 'positive' : match?.[2] === '-' ? 'negative' : null
  }
})
const editingRoutineTests = computed(() => editingRoutineDate.value ? form.routine_tests.filter(test => test.testDate === editingRoutineDate.value) : [])
const editingViralTests = computed(() => editingViralDate.value ? form.viral_tests.filter(test => test.testDate === editingViralDate.value) : [])
const toDateKey = value => String(value || '').split('T')[0]
const antiHlaBatches = computed(() => {
  const groups = new Map()
  form.anti_hla_display.forEach(record => {
    const dateKey = toDateKey(record.testDate)
    const id = record.batchId || record.testDate
    const current = groups.get(dateKey)
    if (!current || current.id !== id) groups.set(dateKey, { id, dateKey, testDate: record.testDate, records: [record] })
    else current.records.push(record)
  })
  return [...groups.values()]
})

watch(hasPregnancyHistory, (v) => { if (!v) { hasAbortionHistory.value = false; form.abortion_count = null; } })
watch(() => form.citizenship, (citizenship) => {
  clearTimeout(identifierCheckTimer)
  identifierCheckSequence++
  form.national_id = ''
  nationalIdError.value = ''
  nationalIdValidated.value = false
  identifierAvailable.value = null
  identifierChecking.value = false
  if (citizenship === 'iranian') {
    form.nationality = ''
  } else {
    form.insurance = []
    form.donor_living = true
    donorSourceError.value = ''
  }
})

const normalizeNumericInputEvent = event => {
  const input = event.target
  if (!input || input.tagName !== 'INPUT') return
  const inputMode = input.getAttribute('inputmode')
  let normalized = input.value
  if (inputMode === 'numeric') normalized = toFa(normalizeLocalizedDigits(input.value).replace(/\D/g, ''))
  else if (inputMode === 'decimal') {
    const numberNormalizer = input.hasAttribute('data-allow-signed') ? normalizeLocalizedSignedNumber : normalizeLocalizedNumber
    normalized = toFa(numberNormalizer(input.value)).replace('.', '٫')
  }
  if (normalized !== input.value) input.value = normalized
}

const adjustWeight = delta => {
  const current = Number(normalizeLocalizedNumber(newWeight.value)) || 0
  newWeight.value = toFa(String(Math.max(0, Math.round((current + delta) * 2) / 2))).replace('.', '٫')
}

const normalizeAndValidateNationalId = (e) => {
  identifierAvailable.value = null
  if (form.citizenship === 'foreign') {
    form.national_id = e.target.value.trim().toUpperCase()
    nationalIdError.value = ''
    nationalIdValidated.value = false
    scheduleIdentifierCheck()
    return
  }
  const val = normalizeNationalId(e.target.value).slice(0, 10)
  form.national_id = toFa(val)
  nationalIdError.value = ''
  nationalIdValidated.value = false
  if (val.length > 0 && val.length < 10) {
    nationalIdError.value = 'کد ملی باید ۱۰ رقم باشد'
    return
  }
  if (val.length === 10) {
    const valid = nationalIdChecker(val)
    nationalIdError.value = valid ? '' : 'کد ملی نامعتبر است'
    nationalIdValidated.value = valid
    if (valid) scheduleIdentifierCheck()
  }
}

const normalizedIdentifierForApi = () => form.citizenship === 'iranian'
  ? normalizeNationalId(form.national_id)
  : String(form.national_id || '').trim().toUpperCase()

const checkIdentifierAvailability = async () => {
  const identifier = normalizedIdentifierForApi()
  const locallyValid = form.citizenship === 'iranian'
    ? nationalIdValidated.value && nationalIdChecker(identifier)
    : Boolean(identifier)
  if (!locallyValid) return false
  const sequence = ++identifierCheckSequence
  identifierChecking.value = true
  try {
    const response = await registryApi.checkIdentifier(form.citizenship, identifier)
    if (sequence !== identifierCheckSequence) return false
    identifierAvailable.value = Boolean(response.valid && response.available)
    nationalIdError.value = response.valid && !response.available
      ? 'این کد ملی یا شناسه قبلاً ثبت شده است'
      : response.valid ? '' : 'شناسه واردشده معتبر نیست'
    return identifierAvailable.value
  } catch (error) {
    if (sequence !== identifierCheckSequence) return false
    identifierAvailable.value = null
    nationalIdError.value = error?.message || 'بررسی یکتایی شناسه انجام نشد'
    return false
  } finally {
    if (sequence === identifierCheckSequence) identifierChecking.value = false
  }
}

const scheduleIdentifierCheck = () => {
  clearTimeout(identifierCheckTimer)
  const identifier = normalizedIdentifierForApi()
  const ready = form.citizenship === 'iranian'
    ? nationalIdValidated.value && identifier.length === 10
    : Boolean(identifier)
  if (!ready) return
  identifierCheckTimer = setTimeout(checkIdentifierAvailability, 450)
}

onBeforeUnmount(() => clearTimeout(identifierCheckTimer))

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
  const formKey = field === 'phone' ? 'phone' : 'emergency_contact_phone'
  form[formKey] = toFa(normalizeIranianMobile(e.target.value))
  validatePhone(field)
}

const isPhoneValid = field => {
  const formKey = field === 'phone' ? 'phone' : 'emergency_contact_phone'
  return Boolean(form[formKey]) && isValidIranianMobile(normalizeIranianMobile(form[formKey]))
}

const validatePhone = (field) => {
  const errorKey = field === 'phone' ? 'phone' : 'emergency'
  const formKey = field === 'phone' ? 'phone' : 'emergency_contact_phone'
  const val = normalizeIranianMobile(form[formKey])
  if (!val) {
    phoneErrors[errorKey] = field === 'phone' ? 'شماره موبایل الزامی است' : ''
    return field !== 'phone'
  }
  if (!isValidIranianMobile(val)) {
    phoneErrors[errorKey] = 'شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود'
    return false
  }
  phoneErrors[errorKey] = ''
  return true
}

const createLocalCdcId = () => `cdc-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
const cdcStatusLabel = status => status === 'positive' ? 'مثبت' : status === 'negative' ? 'منفی' : 'ثبت نشده'

const openCdcCreate = () => {
  editingCdcTest.value = null
  showCdcModal.value = true
}

const openCdcEdit = (test) => {
  editingCdcTest.value = test
  showCdcModal.value = true
}

const saveCdcTest = (payload) => {
  const test = {
    id: editingCdcTest.value?.id || createLocalCdcId(),
    performed_at: toDateKey(payload.performed_at),
    class_i: { ...payload.class_i },
    class_ii: { ...payload.class_ii }
  }
  const index = editingCdcTest.value
    ? form.cdc_pra_tests.findIndex(item => item.id === editingCdcTest.value.id)
    : -1
  if (index >= 0) form.cdc_pra_tests.splice(index, 1, test)
  else form.cdc_pra_tests.push(test)
  form.cdc_pra_tests.sort((left, right) => right.performed_at.localeCompare(left.performed_at))
  editingCdcTest.value = null
  window.toast?.add({ severity: 'success', summary: 'موفق', detail: 'آزمایش CDC PRA ذخیره شد' })
}

const removeCdcTest = (test) => {
  if (!window.confirm('این آزمایش CDC PRA حذف شود؟')) return
  const index = form.cdc_pra_tests.findIndex(item => item.id === test.id)
  if (index >= 0) form.cdc_pra_tests.splice(index, 1)
  window.toast?.add({ severity: 'info', summary: 'حذف شد', detail: 'آزمایش CDC PRA حذف شد' })
}

const openAntiHlaCreate = () => {
  editingAntiHlaBatch.value = null
  showAntiHlaModal.value = true
}

const openAntiHlaEdit = (batch) => {
  editingAntiHlaBatch.value = batch
  showAntiHlaModal.value = true
}

const saveAntiHlaBatch = ({ id, testDate, records }) => {
  const targetDate = toDateKey(testDate)
  const oldRecords = form.anti_hla_display.filter(record => (record.batchId || record.testDate) !== id && toDateKey(record.testDate) !== targetDate)
  form.anti_hla_display.splice(0, form.anti_hla_display.length, ...oldRecords, ...records)
  editingAntiHlaBatch.value = null
  window.toast.add({ severity: 'success', summary: 'موفق', detail: 'آنتی‌بادی‌های Anti-HLA ذخیره شدند' })
}

const removeAntiHlaBatch = (batch) => {
  if (!window.confirm('این مجموعه آنتی‌بادی حذف شود؟')) return
  const remaining = form.anti_hla_display.filter(record => (record.batchId || record.testDate) !== batch.id && toDateKey(record.testDate) !== batch.dateKey)
  form.anti_hla_display.splice(0, form.anti_hla_display.length, ...remaining)
  window.toast.add({ severity: 'info', summary: 'حذف شد', detail: 'مجموعه Anti-HLA حذف شد' })
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

const validateCdcPraTests = () => {
  const dates = new Set()
  const isValid = form.cdc_pra_tests.every(test => {
    const date = toDateKey(test.performed_at)
    if (!date || dates.has(date)) return false
    dates.add(date)
    return ['class_i', 'class_ii'].every(key => {
      const entry = test[key] || {}
      if (!['positive', 'negative'].includes(entry.status)) return false
      if (entry.status === 'negative') return true
      const value = Number(normalizeLocalizedSignedNumber(entry.value))
      return Number.isFinite(value) && value >= 0 && value <= 100
    })
  })
  if (!isValid) {
    window.toast?.add({ severity: 'warning', summary: 'خطا', detail: 'یکی از آزمایش‌های CDC PRA ناقص، نامعتبر یا دارای تاریخ تکراری است؛ آن را ویرایش کنید' })
  }
  return isValid
}

const goToStep = (idx) => { if (idx <= step.value) step.value = idx }

const nextStep = async () => {
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
    if (!(await checkIdentifierAvailability())) return
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
  }
  if (step.value === 1 && !form.donor_living && !form.donor_deceased) {
    donorSourceError.value = 'حداقل یکی از گزینه‌های اهداکننده زنده یا جسد را انتخاب کنید'
    window.toast.add({ severity: 'warning', summary: 'خطا', detail: donorSourceError.value })
    return
  }
  if (step.value === 3 && !validateCdcPraTests()) return
  if (step.value < 5) step.value++
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const submissionErrorDetail = error => {
  const values = Object.values(error?.data?.errors || {}).flat()
  return values[0] || error?.message || 'ثبت پرونده انجام نشد؛ دوباره تلاش کنید'
}

const recipientPayload = () => {
  const payload = {
    ...form,
    cdc_pra_tests: form.cdc_pra_tests.map(test => ({
      performed_at: toDateKey(test.performed_at),
      class_i: { ...test.class_i },
      class_ii: { ...test.class_ii }
    })),
    weight: newWeight.value,
    height: newHeight.value,
    has_dialysis_history: hasDialysisHistory.value,
    has_blood_transfusion: hasBloodTransfusion.value,
    has_pregnancy_history: hasPregnancyHistory.value,
    has_abortion_history: hasAbortionHistory.value
  }
  delete payload.cdc_pra
  return payload
}

const nextOrSubmit = async () => {
  if (step.value < 5) {
    await nextStep()
    return
  }
  if (!validateCdcPraTests()) return
  if (submitting.value) return
  submitting.value = true
  try {
    const response = await registryApi.createRecipient(recipientPayload())
    clearDraft()
    window.toast.add({ severity: 'success', summary: 'موفق', detail: response.message })
    await router.push('/recipients')
  } catch (error) {
    window.toast.add({ severity: 'error', summary: 'ثبت انجام نشد', detail: submissionErrorDetail(error) })
  } finally {
    submitting.value = false
  }
}

const prevStep = () => { if (step.value > 0) step.value-- }

const cancel = () => {
  if (!window.confirm('آیا از انصراف مطمئن هستید؟ اطلاعات واردشده این فرم حذف خواهد شد.')) return
  clearDraft()
  router.push('/recipients')
}

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
