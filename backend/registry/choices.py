from django.db import models


class HLALocus(models.TextChoices):
    A = "A", "HLA-A"
    B = "B", "HLA-B"
    C = "C", "HLA-C"
    DRB1 = "DRB1", "HLA-DRB1"
    DQB1 = "DQB1", "HLA-DQB1"
    DRB = "DRB", "HLA-DRB"


class AntiHLALocus(models.TextChoices):
    A = "A", "HLA-A"
    B = "B", "HLA-B"
    C = "C", "HLA-C"
    DRB1 = "DRB1", "HLA-DRB1"
    DQB1 = "DQB1", "HLA-DQB1"
    DRB = "DRB", "HLA-DRB3/4/5"
    DQA1 = "DQA1", "HLA-DQA1"
    DPB1 = "DPB1", "HLA-DPB1"
    DPA1 = "DPA1", "HLA-DPA1"


class HLAClass(models.TextChoices):
    CLASS_I = "I", "Class I"
    CLASS_II = "II", "Class II"


HLA_VALUES_BY_LOCUS = {
    HLALocus.A: "A*01 A*02 A*03 A*11 A*23 A*24 A*25 A*26 A*29 A*30 A*31 A*32 A*33 A*34 A*36 A*43 A*66 A*68 A*69 A*74 A*80".split(),
    HLALocus.B: "B*07 B*08 B*13 B*14 B*15 B*18 B*27 B*35 B*37 B*38 B*39 B*40 B*41 B*42 B*44 B*45 B*46 B*47 B*48 B*49 B*50 B*51 B*52 B*53 B*54 B*55 B*56 B*57 B*58 B*59 B*67 B*73 B*78 B*81 B*82 B*83".split(),
    HLALocus.C: "C*01 C*02 C*03 C*04 C*05 C*06 C*07 C*08 C*12 C*14 C*15 C*16 C*17 C*18".split(),
    HLALocus.DRB1: "DRB1*01 DRB1*03 DRB1*04 DRB1*07 DRB1*08 DRB1*09 DRB1*10 DRB1*11 DRB1*12 DRB1*13 DRB1*14 DRB1*15 DRB1*16".split(),
    HLALocus.DQB1: "DQB1*02 DQB1*03 DQB1*04 DQB1*05 DQB1*06".split(),
    HLALocus.DRB: ["DRB3", "DRB4", "DRB5", "سایر"],
}


ANTI_HLA_VALUES_BY_LOCUS = {
    AntiHLALocus.A: "A*01:01 A*02:01 A*02:02 A*02:03 A*02:05 A*03:01 A*11:01 A*11:02 A*23:01 A*24:02 A*24:03 A*25:01 A*26:01 A*29:01 A*29:02 A*30:01 A*31:01 A*32:01 A*33:01 A*33:03 A*34:02 A*36:01 A*43:01 A*66:01 A*66:02 A*68:01 A*68:02 A*69:01 A*74:01 A*80:01".split(),
    AntiHLALocus.B: "B*07:02 B*07:03 B*08:01 B*13:02 B*14:01 B*14:02 B*15:01 B*15:02 B*15:03 B*15:12 B*15:13 B*15:16 B*15:18 B*18:01 B*27:03 B*27:05 B*27:08 B*35:01 B*35:08 B*37:01 B*38:01 B*39:01 B*40:01 B*40:02 B*41:01 B*42:01 B*44:02 B*44:03 B*45:01 B*46:01 B*47:01 B*48:01 B*49:01 B*50:01 B*51:01 B*52:01 B*53:01 B*54:01 B*55:01 B*55:04 B*56:01 B*57:01 B*58:01 B*59:01 B*67:01 B*73:01 B*78:01 B*81:01 B*82:02 B*83:01".split(),
    AntiHLALocus.C: "C*01:02 C*02:02 C*03:02 C*03:03 C*03:04 C*04:01 C*04:03 C*05:01 C*06:02 C*07:01 C*07:02 C*08:01 C*08:02 C*12:02 C*14:02 C*15:02 C*16:01 C*17:01 C*18:01".split(),
    AntiHLALocus.DRB1: "DRB1*01:01 DRB1*01:02 DRB1*01:03 DRB1*03:01 DRB1*03:02 DRB1*03:03 DRB1*04:01 DRB1*04:02 DRB1*04:03 DRB1*04:04 DRB1*04:05 DRB1*07:01 DRB1*08:01 DRB1*08:02 DRB1*09:01 DRB1*10:01 DRB1*11:01 DRB1*11:03 DRB1*11:04 DRB1*12:01 DRB1*12:02 DRB1*13:01 DRB1*13:03 DRB1*13:05 DRB1*14:01 DRB1*14:03 DRB1*14:04 DRB1*15:01 DRB1*15:02 DRB1*15:03 DRB1*16:01 DRB1*16:02".split(),
    AntiHLALocus.DQB1: "DQB1*02:01 DQB1*02:02 DQB1*03:01 DQB1*03:02 DQB1*03:03 DQB1*04:01 DQB1*04:02 DQB1*05:01 DQB1*05:02 DQB1*05:03 DQB1*06:01 DQB1*06:02 DQB1*06:03 DQB1*06:04".split(),
    AntiHLALocus.DRB: "DRB3*01:01 DRB3*02:02 DRB3*03:01 DRB4*01:01 DRB5*01:01 DRB5*02:02".split(),
    AntiHLALocus.DQA1: "DQA1*01:01 DQA1*01:02 DQA1*01:03 DQA1*01:04 DQA1*02:01 DQA1*03:01 DQA1*03:02 DQA1*04:01 DQA1*05:01 DQA1*06:01".split(),
    AntiHLALocus.DPB1: "DPB1*01:01 DPB1*02:01 DPB1*03:01 DPB1*04:01 DPB1*04:02 DPB1*05:01 DPB1*06:01 DPB1*09:01 DPB1*11:01 DPB1*13:01 DPB1*14:01 DPB1*15:01 DPB1*17:01 DPB1*18:01 DPB1*19:01 DPB1*28:01".split(),
    AntiHLALocus.DPA1: "DPA1*01:03 DPA1*02:01 DPA1*02:02 DPA1*03:01 DPA1*04:01".split(),
}


def _choice_union(values_by_group):
    return tuple((value, value) for values in values_by_group.values() for value in values)


HLA_ALLELE_CHOICES = _choice_union(HLA_VALUES_BY_LOCUS)
ANTI_HLA_ANTIGEN_CHOICES = _choice_union(ANTI_HLA_VALUES_BY_LOCUS)


class RoutineCategory(models.TextChoices):
    CBC = "CBC", "CBC"
    BLOOD_BIOCHEM = "Blood Biochemistry", "Blood Biochemistry"
    OTHER_BIOCHEM = "Other Biochemistry", "Other Biochemistry"
    THYROID = "Thyroid", "Thyroid"
    URINE_24 = "Urine 24H", "Urine 24H"
    URINE = "آزمایش ادرار", "آزمایش ادرار"
    FEMALE = "بانوان", "بانوان"


ROUTINE_TEST_NAMES = (
    "WBC", "HB", "Hct", "platelets", "Cr", "BUN", "FBS", "Uric_Acid", "Na", "K",
    "Ca", "P", "ALT", "AST", "AlkPh", "Tg", "Chol", "LDL", "HDL", "HbA1c", "Fe",
    "Ferritin", "TIBC", "CPK_total", "Vit_D3", "PTH", "T3", "T4", "TSH",
    "Free_Beta_HCG", "urine24_result", "urine24_volume", "urine24_cr", "urine24_protein",
    "urine_blood", "urine_protein", "urine_hemoglobin", "urine_glucose", "wbc_range",
    "rbc_range", "Urine Culture", "urine_culture_count",
)

VIRAL_TEST_NAMES = (
    "HBs Ag", "IGRA", "Widal Test", "VDRL", "Wright Test", "RF [Qual]", "PT & INR",
    "CMV IgM", "Toxoplasma gondii IgG", "Toxoplasma gondii IgM", "PTT", "HSV 1&2 IgM",
    "Coombs Wright", "HSV 2 IgG", "EBV Capsid IgM", "VZV IgG", "VZV IgM", "Anti HBs",
    "Anti HCV", "CMV IgG", "UA", "HTLV I+II", "HTLV I Ab", "HIV Ab & P24 Ag",
)

LAB_TEST_NAME_CHOICES = tuple((value, value) for value in (*ROUTINE_TEST_NAMES, *VIRAL_TEST_NAMES))
LAB_CATEGORY_CHOICES = (*RoutineCategory.choices, ("آزمایش ویروسی", "آزمایش ویروسی"))
