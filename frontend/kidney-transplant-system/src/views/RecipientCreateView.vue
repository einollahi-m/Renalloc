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

    <div v-if="step < 5" class="form-actions form-actions-top">
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
              <label class="radio-pill" :class="{checked: form.citizenship==='iranian'}"><input type="radio" name="recipient-citizenship" v-model="form.citizenship" value="iranian" /> ایرانی</label>
              <label class="radio-pill" :class="{checked: form.citizenship==='foreign'}"><input type="radio" name="recipient-citizenship" v-model="form.citizenship" value="foreign" /> غیر ایرانی</label>
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
              <label class="radio-pill" :class="{checked: form.gender==='male'}"><input type="radio" name="recipient-gender" v-model="form.gender" value="male" /> مرد</label>
              <label class="radio-pill" :class="{checked: form.gender==='female'}"><input type="radio" name="recipient-gender" v-model="form.gender" value="female" /> زن</label>
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
                  <label class="radio-pill" :class="{checked: form.rh_factor==='positive'}"><input type="radio" name="recipient-rh" v-model="form.rh_factor" value="positive" /> مثبت</label>
                  <label class="radio-pill" :class="{checked: form.rh_factor==='negative'}"><input type="radio" name="recipient-rh" v-model="form.rh_factor" value="negative" /> منفی</label>
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
              <label class="radio-pill" :class="{checked: form.marital_status==='single'}"><input type="radio" name="recipient-marital-status" v-model="form.marital_status" value="single" /> مجرد</label>
              <label class="radio-pill" :class="{checked: form.marital_status==='married'}"><input type="radio" name="recipient-marital-status" v-model="form.marital_status" value="married" /> متأهل</label>
            </div>
          </div>
          <div class="form-group measures-field">
            <div class="measure-label-row">
              <label class="form-label" for="recipient-weight">وزن (کیلوگرم)</label>
              <label class="form-label" for="recipient-height">قد (سانتی‌متر)</label>
            </div>
            <div class="measure-input-pair">
              <input id="recipient-weight" type="text" v-model="newWeight" class="form-input" placeholder="مقدار وزن" inputmode="decimal" @keydown.up.prevent="adjustWeight(0.5)" @keydown.down.prevent="adjustWeight(-0.5)" />
              <input id="recipient-height" type="text" v-model="newHeight" class="form-input" placeholder="مقدار قد" inputmode="numeric" />
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
              <label class="check-chip" :class="{checked: form.donor_deceased, disabled: form.citizenship==='foreign'}"><input type="checkbox" v-model="form.donor_deceased" :disabled="form.citizenship==='foreign'" @change="donorSourceError=''" /><i class="ri-ribbon-line"></i> اهداکننده جسد</label>
            </div>
            <div v-if="form.citizenship==='foreign'" class="recipient-donor-source-hint">برای گیرنده غیر ایرانی فقط اهداکننده زنده قابل انتخاب است.</div>
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
            <div class="grid grid-2 cdc-pra-grid">
              <section v-for="item in cdcPraClasses" :key="item.key" class="cdc-pra-card">
                <h4>{{ item.label }}</h4>
                <div class="radio-pills cdc-status-options">
                  <label class="radio-pill" :class="{checked: form.cdc_pra[item.key].status==='positive'}">
                    <input type="radio" :name="`cdc-${item.key}`" v-model="form.cdc_pra[item.key].status" value="positive" /> مثبت
                  </label>
                  <label class="radio-pill" :class="{checked: form.cdc_pra[item.key].status==='negative'}">
                    <input type="radio" :name="`cdc-${item.key}`" v-model="form.cdc_pra[item.key].status" value="negative" /> منفی
                  </label>
                </div>
                <div v-if="form.cdc_pra[item.key].status==='positive'" class="form-group cdc-value-field">
                  <label class="form-label">درصد PRA (۰ تا ۱۰۰) *</label>
                  <div class="input-with-suffix">
                    <input type="text" inputmode="decimal" :value="form.cdc_pra[item.key].value" class="form-input" :class="{'form-error-border': cdcPraErrors[item.key]}" placeholder="مثال: ۲۵" @input="normalizeCdcValue(item.key, $event)" />
                    <span>٪</span>
                  </div>
                  <div v-if="cdcPraErrors[item.key]" class="form-error">{{ cdcPraErrors[item.key] }}</div>
                  <div v-else-if="isCdcPraClassImplicit(item.key)" class="cdc-class-implicit-note">
                    <i class="ri-check-double-line"></i> مقدار مؤثر این کلاس: منفی
                  </div>
                </div>
                <div v-else-if="cdcPraErrors[item.key]" class="form-error">{{ cdcPraErrors[item.key] }}</div>
              </section>
            </div>
            <div v-if="cdcPraImplicitlyNegative" class="alert alert-success cdc-implicit-alert">
              <i class="ri-information-line"></i>
              <span>برای پیوند اول، مقدار CDC PRA در بازهٔ ۰ تا ۵ به‌صورت ضمنی منفی و تعداد آنتی‌بادی صفر در نظر گرفته می‌شود.</span>
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
            <div v-if="cdcPraImplicitlyNegative" class="alert alert-success">
              <i class="ri-shield-check-line"></i>
              <span>CDC PRA به‌صورت ضمنی منفی است؛ آنتی‌بادی صفر ثبت می‌شود و نیازی به ارائه Anti-HLA نیست.</span>
            </div>
            <div v-else class="flex justify-between items-center mb-3">
              <h4 style="margin:0;">نتایج ثبت شده</h4>
              <button class="btn btn-sm btn-primary" type="button" @click="openAntiHlaCreate"><i class="ri-add-line"></i> افزودن نتیجه جدید</button>
            </div>
            <div v-if="!cdcPraImplicitlyNegative && !antiHlaBatches.length" class="empty-state compact-empty-state">
              <i class="ri-flask-line"></i>
              <h3>نتیجه‌ای ثبت نشده</h3>
            </div>
            <div v-else-if="!cdcPraImplicitlyNegative" class="result-batches">
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
                    <strong v-if="!record.isNone">{{ record.locus }}</strong>
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

    <div v-if="step===5" class="form-actions">
      <button class="btn btn-secondary" type="button" @click="prevStep">
        <i class="ri-arrow-right-line"></i> گام قبلی
      </button>
      <div class="flex gap-2">
        <button class="btn btn-secondary" type="button" @click="cancel">انصراف</button>
        <button class="btn btn-primary" type="button" @click="nextOrSubmit">
          <i class="ri-save-line"></i> تایید و ثبت گیرنده جدید
        </button>
      </div>
    </div>

    <anti-hla-modal v-model:visible="showAntiHlaModal" :edit-batch="editingAntiHlaBatch" @save="saveAntiHlaBatch" />
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
import { educationOptions, insuranceOptions, nationalityOptions, bloodTypeOptions, dialysisTypes, transplantCandidateOptions, esrdCauseOptions, approvalStatusOptions, specialties } from '../data/options'
import AntiHlaModal from '../components/AntiHlaModal.vue'
import TestResultsList from '../components/TestResultsList.vue'

const router = useRouter()
const step = ref(0)
const steps = ['اطلاعات فردی', 'اطلاعات پزشکی پایه', 'سوابق', 'ایمونولوژی', 'آزمایش‌ها', 'تاییدیه‌ها']
const toFa = toFaDigits
const cdcPraClasses = [
  { key: 'class_i', label: 'Class I' },
  { key: 'class_ii', label: 'Class II' }
]

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
  cdc_pra: {
    class_i: { status: null, value: null, effective_status: null, is_implicitly_negative: false },
    class_ii: { status: null, value: null, effective_status: null, is_implicitly_negative: false },
    implicitly_negative: false,
    antibody_count: null
  },
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
const editingAntiHlaBatch = ref(null)
const editingRoutineDate = ref(null)
const editingViralDate = ref(null)
const nationalIdError = ref('')
const nationalIdChecking = ref(false)
const nationalIdValidated = ref(false)
const phoneErrors = reactive({ phone: '', emergency: '' })
const donorSourceError = ref('')
const cdcPraErrors = reactive({ class_i: '', class_ii: '' })
let nationalIdValidationToken = 0

const isNationalIdValid = computed(() => form.citizenship === 'iranian' && nationalIdValidated.value && !nationalIdError.value)
const editingRoutineTests = computed(() => editingRoutineDate.value ? form.routine_tests.filter(test => test.testDate === editingRoutineDate.value) : [])
const editingViralTests = computed(() => editingViralDate.value ? form.viral_tests.filter(test => test.testDate === editingViralDate.value) : [])
const toDateKey = value => String(value || '').split('T')[0]
const isCdcPraClassImplicit = key => {
  const entry = form.cdc_pra[key]
  const value = Number(entry.value)
  return form.transplant_candidate === '1st' && entry.status === 'positive' && entry.value !== '' && entry.value != null && Number.isFinite(value) && value >= 0 && value <= 5
}
const cdcPraImplicitlyNegative = computed(() => {
  if (form.transplant_candidate !== '1st') return false
  const entries = cdcPraClasses.map(item => form.cdc_pra[item.key])
  const hasLowPositive = cdcPraClasses.some(item => isCdcPraClassImplicit(item.key))
  return hasLowPositive && entries.every((entry, index) => entry.status === 'negative' || isCdcPraClassImplicit(cdcPraClasses[index].key))
})
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
cdcPraClasses.forEach(item => {
  watch(() => form.cdc_pra[item.key].status, status => {
    cdcPraErrors[item.key] = ''
    if (status !== 'positive') form.cdc_pra[item.key].value = null
  })
})
watch(() => form.citizenship, (citizenship) => {
  nationalIdValidationToken++
  form.national_id = ''
  nationalIdError.value = ''
  nationalIdChecking.value = false
  nationalIdValidated.value = false
  if (citizenship === 'iranian') {
    form.nationality = ''
  } else {
    form.insurance = []
    form.donor_living = true
    form.donor_deceased = false
    donorSourceError.value = ''
  }
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

const normalizeCdcValue = (key, event) => {
  const normalized = normalizeLocalizedNumber(event.target.value)
  form.cdc_pra[key].value = normalized
  cdcPraErrors[key] = ''
}

const validateCdcPra = () => {
  let valid = true
  cdcPraClasses.forEach(item => {
    const entry = form.cdc_pra[item.key]
    cdcPraErrors[item.key] = ''
    if (!entry.status) {
      cdcPraErrors[item.key] = `وضعیت ${item.label} را مشخص کنید`
      valid = false
      return
    }
    if (entry.status === 'positive') {
      const value = Number(entry.value)
      if (entry.value === '' || entry.value == null || !Number.isFinite(value) || value < 0 || value > 100) {
        cdcPraErrors[item.key] = 'درصد باید عددی بین ۰ تا ۱۰۰ باشد'
        valid = false
      }
    }
  })
  if (valid) {
    cdcPraClasses.forEach(item => {
      const entry = form.cdc_pra[item.key]
      entry.is_implicitly_negative = isCdcPraClassImplicit(item.key)
      entry.effective_status = entry.is_implicitly_negative ? 'negative' : entry.status
    })
    form.cdc_pra.implicitly_negative = cdcPraImplicitlyNegative.value
    form.cdc_pra.antibody_count = cdcPraImplicitlyNegative.value ? 0 : null
    if (cdcPraImplicitlyNegative.value) form.anti_hla_display.splice(0)
  }
  if (!valid) window.toast.add({ severity: 'warning', summary: 'خطا', detail: 'مقادیر CDC PRA را کامل و معتبر وارد کنید' })
  return valid
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
  if (step.value === 3 && !validateCdcPra()) return
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
