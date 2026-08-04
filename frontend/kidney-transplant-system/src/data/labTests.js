export const viralTestOptions = ['HBs Ag','IGRA','Widal Test','VDRL','Wright Test','RF [Qual]','PT & INR','CMV IgM','Toxoplasma gondii IgG','Toxoplasma gondii IgM','PTT','HSV 1&2 IgM','Coombs Wright','HSV 2 IgG','EBV Capsid IgM','VZV IgG','VZV IgM','Anti HBs','Anti HCV','CMV IgG','UA','HTLV I+II','HTLV I Ab','HIV Ab & P24 Ag']

export const routineCategories = [
  { key: 'cbc', label: 'CBC', icon: 'ri-heart-pulse-line' },
  { key: 'blood_biochem', label: 'Blood Biochemistry', icon: 'ri-line-chart-line' },
  { key: 'other_biochem', label: 'Other Biochemistry', icon: 'ri-bar-chart-line' },
  { key: 'thyroid', label: 'Thyroid', icon: 'ri-pulse-line' },
  { key: 'urine24', label: 'Urine 24H', icon: 'ri-time-line' },
  { key: 'urine', label: 'آزمایش ادرار', icon: 'ri-filter-line' },
  { key: 'female', label: 'بانوان', icon: 'ri-user-line' }
]

export const routineTestsByCategory = {
  cbc: [
    { key: 'WBC', label: 'WBC', min: 0.1, max: 50, unit: '×10⁹/L' },
    { key: 'HB', label: 'HB', min: 3, max: 22, unit: 'g/dL' },
    { key: 'Hct', label: 'Hct', min: 10, max: 70, unit: '%' },
    { key: 'platelets', label: 'Platelets', min: 5, max: 1000, unit: '×10⁹/L' }
  ],
  blood_biochem: [
    { key: 'Cr', label: 'Cr', min: 0.1, max: 25, unit: 'mg/dL' },
    { key: 'BUN', label: 'BUN', min: 1, max: 250, unit: 'mg/dL' },
    { key: 'FBS', label: 'FBS', min: 20, max: 800, unit: 'mg/dL' },
    { key: 'Uric_Acid', label: 'Uric Acid', min: 0.5, max: 25, unit: 'mg/dL' },
    { key: 'Na', label: 'Na', min: 100, max: 180, unit: 'mmol/L' },
    { key: 'K', label: 'K', min: 1.0, max: 10.0, unit: 'mmol/L' },
    { key: 'Ca', label: 'Ca', min: 4, max: 18, unit: 'mg/dL' },
    { key: 'P', label: 'P', min: 0.2, max: 20, unit: 'mg/dL' },
    { key: 'ALT', label: 'ALT', min: 1, max: 5000, unit: 'U/L' },
    { key: 'AST', label: 'AST', min: 1, max: 5000, unit: 'U/L' },
    { key: 'AlkPh', label: 'AlkPh', min: 5, max: 3000, unit: 'U/L' },
    { key: 'Tg', label: 'Tg', min: 10, max: 5000, unit: 'mg/dL' },
    { key: 'Chol', label: 'Chol', min: 40, max: 600, unit: 'mg/dL' },
    { key: 'LDL', label: 'LDL', min: 5, max: 400, unit: 'mg/dL' },
    { key: 'HDL', label: 'HDL', min: 2, max: 120, unit: 'mg/dL' },
    { key: 'HbA1c', label: 'HbA1c', min: 3, max: 20, unit: '%' }
  ],
  other_biochem: [
    { key: 'Fe', label: 'Fe (Iron)', min: 5, max: 600, unit: 'µg/dL' },
    { key: 'Ferritin', label: 'Ferritin', min: 2, max: 8000, unit: 'ng/mL' },
    { key: 'TIBC', label: 'TIBC', min: 40, max: 700, unit: 'µg/dL' },
    { key: 'CPK_total', label: 'CPK total', min: 5, max: 200000, unit: 'U/L' },
    { key: 'Vit_D3', label: 'Vit D3', min: 2, max: 300, unit: 'ng/mL' },
    { key: 'PTH', label: 'PTH', min: 1, max: 5000, unit: 'pg/mL' }
  ],
  thyroid: [
    { key: 'T3', label: 'T3', min: 10, max: 600, unit: 'ng/dL' },
    { key: 'T4', label: 'T4', min: 1, max: 35, unit: 'µg/dL' },
    { key: 'TSH', label: 'TSH', min: 0.001, max: 500, unit: 'mIU/L' }
  ],
  female: [
    { key: 'Free_Beta_HCG', label: 'Free Beta HCG', min: 0, max: 500000, unit: 'mIU/mL' }
  ]
}

export const routineCategoryLabels = {
  cbc: 'CBC', blood_biochem: 'Blood Biochemistry', other_biochem: 'Other Biochemistry',
  thyroid: 'Thyroid', urine24: 'Urine 24H', urine: 'آزمایش ادرار', female: 'بانوان'
}

export const urine24Fields = [
  { key: 'urine24_volume', label: 'Volume 24h', min: 100, max: 10000, unit: 'mL/d' },
  { key: 'urine24_cr', label: 'Cr 24h', min: 200, max: 3000, unit: 'mg/24h' },
  { key: 'urine24_protein', label: 'Protein 24h', min: 10, max: 20000, unit: 'mg/24h' }
]

export const urineAnalysisFields = [
  { key: 'urine_blood', label: 'Blood', type: 'qualitative' },
  { key: 'urine_protein', label: 'Protein', type: 'qualitative' },
  { key: 'urine_hemoglobin', label: 'Hemoglobin', type: 'qualitative' },
  { key: 'urine_glucose', label: 'Glucose', type: 'qualitative' },
  { key: 'wbc_range', label: 'W.B.C. (محدوده)', type: 'text' },
  { key: 'rbc_range', label: 'R.B.C. (محدوده)', type: 'text' }
]

export const qualitativeOptions = [
  { label: 'نامشخص', value: '' },
  { label: 'Negative', value: 'negative' },
  { label: '+', value: '+' },
  { label: '++', value: '++' },
  { label: '+++', value: '+++' }
]

export const testDefByKey = {}
Object.values(routineTestsByCategory).forEach(arr => arr.forEach(t => testDefByKey[t.key] = t))
urine24Fields.forEach(f => testDefByKey[f.key] = f)
testDefByKey['urine_culture_count'] = { key: 'urine_culture_count', min: 0, max: 100000000 }
