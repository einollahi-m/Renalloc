from collections import Counter
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_date

from .models import (
    AntiHlaSelection,
    AntiHlaTest,
    CdcPraTest,
    DonorProfile,
    HLASelection,
    HLATyping,
    LabTest,
    MedicalApproval,
    Person,
    RecipientProfile,
)
from .choices import HLAClass, HLALocus
from .validators import normalize_digits, normalize_national_id


HLA_FIELDS = (
    "hla_a", "hla_b", "hla_c", "hla_drb1", "hla_dqb1", "hla_drb",
    "hla_dqa1", "hla_dpb1", "hla_dpa1",
)
HLA_FIELD_TO_LOCUS = {
    "hla_a": HLALocus.A,
    "hla_b": HLALocus.B,
    "hla_c": HLALocus.C,
    "hla_drb1": HLALocus.DRB1,
    "hla_dqb1": HLALocus.DQB1,
    "hla_drb": HLALocus.DRB,
    "hla_dqa1": HLALocus.DQA1,
    "hla_dpb1": HLALocus.DPB1,
    "hla_dpa1": HLALocus.DPA1,
}
APPROVAL_SPECIALTIES = {choice for choice, _label in MedicalApproval.Specialty.choices}


def _text(value):
    return str(value or "").strip()


def _boolean(payload, key, default=False):
    value = payload.get(key, default)
    if type(value) is not bool:
        raise ValidationError({key: "مقدار این فیلد باید صحیح یا غلط باشد."})
    return value


def _date(value, field_name, *, required=False):
    raw = _text(value)
    if not raw:
        if required:
            raise ValidationError({field_name: "تاریخ الزامی است."})
        return None
    parsed = parse_date(raw[:10])
    if parsed is None:
        raise ValidationError({field_name: "تاریخ معتبر نیست."})
    return parsed


def _integer(value, field_name):
    raw = normalize_digits(value).replace("٬", "").replace(",", "").strip()
    if not raw:
        return None
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        raise ValidationError({field_name: "مقدار باید عدد صحیح باشد."})
    if parsed < 0:
        raise ValidationError({field_name: "مقدار نمی‌تواند منفی باشد."})
    return parsed


def _decimal(value, field_name):
    raw = (
        normalize_digits(value)
        .replace("٫", ".")
        .replace("٬", "")
        .replace(",", "")
        .strip()
    )
    if not raw:
        return None
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        raise ValidationError({field_name: "مقدار باید عددی باشد."})


def _blood_group(payload):
    combined = _text(payload.get("blood_group"))
    if combined:
        return combined.upper()
    blood_type = _text(payload.get("blood_type")).upper()
    rh_factor = _text(payload.get("rh_factor"))
    suffix = "+" if rh_factor == "positive" else "-" if rh_factor == "negative" else ""
    return f"{blood_type}{suffix}"


def _person_data(payload, user):
    insurance = payload.get("insurance") or []
    if not isinstance(insurance, list):
        raise ValidationError({"insurance": "بیمه باید به‌صورت فهرست ارسال شود."})
    return {
        "citizenship": _text(payload.get("citizenship")) or Person.Citizenship.IRANIAN,
        "identifier": _text(payload.get("national_id") or payload.get("identifier")),
        "first_name": _text(payload.get("first_name")),
        "last_name": _text(payload.get("last_name")),
        "gender": _text(payload.get("gender")),
        "birth_date": _date(payload.get("birth_date"), "birth_date", required=True),
        "blood_group": _blood_group(payload),
        "phone": _text(payload.get("phone")),
        "emergency_contact_phone": _text(payload.get("emergency_contact_phone")),
        "nationality": _text(payload.get("nationality")),
        "education": _text(payload.get("education")),
        "insurance": [_text(item) for item in insurance if _text(item)],
        "marital_status": _text(payload.get("marital_status")),
        "weight_kg": _decimal(payload.get("weight"), "weight"),
        "height_cm": _decimal(payload.get("height"), "height"),
        "is_smoker": _boolean(payload, "is_smoker"),
        "has_addiction": _boolean(payload, "has_addiction"),
        "has_alcohol": _boolean(payload, "has_alcohol"),
        "center": user.center,
        "created_by": user,
    }


def _create_person(payload, user):
    person = Person(**_person_data(payload, user))
    person.full_clean()
    person.save()
    return person


def _validated_hla_values(payload):
    values = {}
    for field_name in HLA_FIELDS:
        alleles = payload.get(field_name) or []
        if not isinstance(alleles, list):
            raise ValidationError({field_name: "مقادیر HLA باید به‌صورت فهرست ارسال شوند."})
        values[field_name] = [_text(allele) for allele in alleles if _text(allele)]
        if len(values[field_name]) > 2:
            raise ValidationError(
                {field_name: "برای هر locus حداکثر دو آلل قابل انتخاب است."}
            )
    return values


def _save_hla_typing(person, payload, *, skip_when_empty=False):
    values = _validated_hla_values(payload)
    if skip_when_empty and not any(values.values()):
        return None
    typing = (
        HLATyping.objects.select_for_update().filter(person=person).first()
        or HLATyping.objects.create(person=person)
    )
    typing.selections.all().delete()
    for field_name, alleles in values.items():
        for allele, copy_number in Counter(alleles).items():
            selection = HLASelection(
                typing=typing,
                locus=HLA_FIELD_TO_LOCUS[field_name],
                allele=allele,
                copy_number=copy_number,
            )
            selection.full_clean()
            selection.save()
    typing.save(update_fields=["updated_at"])
    return typing


@transaction.atomic
def update_hla_typing(person, payload):
    typing = _save_hla_typing(person, payload)
    _queue_matching_for_person(person, None)
    return typing


def _queue_matching_for_person(person, user, *, anti_hla_updated=False):
    user_id = getattr(user, "pk", None)
    if RecipientProfile.objects.filter(pk=person.pk).exists():
        from .tasks import match_recipient

        match_recipient.delay_on_commit(
            str(person.pk),
            user_id,
            "anti_hla_updated" if anti_hla_updated else "manual",
        )
    elif DonorProfile.objects.filter(pk=person.pk).exists():
        from .tasks import match_donor

        match_donor.delay_on_commit(str(person.pk), user_id, "donor_created")


def _create_lab_test(
    *, person, user, kind, category, name, result, performed_at, details=None, batch_key=""
):
    test = LabTest(
        person=person,
        created_by=user,
        kind=kind,
        category=_text(category),
        name=_text(name),
        result=result,
        details=details or {},
        batch_key=_text(batch_key),
        performed_at=performed_at,
    )
    test.full_clean()
    test.save()
    return test


@transaction.atomic
def create_lab_test(person, user, payload):
    kind = _text(payload.get("kind"))
    if kind not in LabTest.Kind.values:
        raise ValidationError({"kind": "نوع آزمایش معتبر نیست."})
    performed_at = _date(payload.get("performed_at"), "performed_at", required=True)
    result = payload.get("result")
    if isinstance(result, str):
        result = normalize_digits(result).strip()
    return _create_lab_test(
        person=person,
        user=user,
        kind=kind,
        category=_text(payload.get("category")),
        name=_text(payload.get("name")),
        result=result,
        performed_at=performed_at,
        details=payload.get("details") if isinstance(payload.get("details"), dict) else {},
    )


@transaction.atomic
def update_lab_test(test, user, payload):
    locked = LabTest.objects.select_for_update().get(pk=test.pk)
    kind = _text(payload.get("kind")) or locked.kind
    if kind not in LabTest.Kind.values:
        raise ValidationError({"kind": "نوع آزمایش معتبر نیست."})
    locked.kind = kind
    locked.category = _text(payload.get("category")) or locked.category
    locked.name = _text(payload.get("name")) or locked.name
    if "result" in payload:
        result = payload.get("result")
        locked.result = normalize_digits(result).strip() if isinstance(result, str) else result
    if "performed_at" in payload:
        locked.performed_at = _date(payload.get("performed_at"), "performed_at", required=True)
        locked.expires_at = LabTest.expiry_for(locked.performed_at)
    if "details" in payload:
        if not isinstance(payload.get("details"), dict):
            raise ValidationError({"details": "جزئیات آزمایش باید یک شیء باشد."})
        locked.details = payload["details"]
    locked.full_clean()
    locked.save()
    return locked


@transaction.atomic
def save_lab_test_batch(person, user, payload):
    kind = _text(payload.get("kind"))
    if kind not in LabTest.Kind.values:
        raise ValidationError({"kind": "نوع آزمایش معتبر نیست."})
    records = payload.get("tests")
    if not isinstance(records, list) or not records or len(records) > 100:
        raise ValidationError({"tests": "بین یک تا صد نتیجه آزمایش قابل ثبت است."})
    original_date = _date(payload.get("original_date"), "original_date")
    existing = (
        {
            (test.category, test.name): test
            for test in LabTest.objects.select_for_update().filter(
                person=person, kind=kind, performed_at=original_date
            )
        }
        if original_date
        else {}
    )
    seen = set()
    saved = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValidationError({"tests": f"ردیف {index + 1} معتبر نیست."})
        category = _text(record.get("category"))
        name = _text(record.get("name") or record.get("testName"))
        key = (category, name)
        if key in seen:
            raise ValidationError({"tests": "نام آزمایش در یک نوبت نباید تکراری باشد."})
        seen.add(key)
        record_payload = {
            "kind": kind,
            "category": category,
            "name": name,
            "result": record.get("result", record.get("value")),
            "performed_at": record.get("performed_at") or record.get("testDate"),
        }
        test = existing.pop(key, None)
        saved.append(
            update_lab_test(test, user, record_payload)
            if test
            else create_lab_test(person, user, record_payload)
        )
    if original_date:
        LabTest.objects.filter(pk__in=[test.pk for test in existing.values()]).delete()
    return saved


PERSON_PROFILE_EDITABLE_FIELDS = {
    "phone",
    "emergency_contact_phone",
    "education",
    "insurance",
    "marital_status",
    "weight_kg",
    "height_cm",
    "is_smoker",
    "has_addiction",
    "has_alcohol",
}


@transaction.atomic
def update_person_profile(person, payload):
    forbidden = set(payload).difference(PERSON_PROFILE_EDITABLE_FIELDS)
    if forbidden or not payload:
        raise ValidationError(
            {
                "profile": (
                    "در این بخش فقط اطلاعات تماس و مشخصات غیرهویتی قابل ویرایش است؛ "
                    "نام، نام خانوادگی، شناسه، جنسیت و تاریخ تولد فقط توسط مدیر backend تغییر می‌کنند."
                )
            }
        )
    locked = Person.objects.select_for_update().get(pk=person.pk)
    for field, value in payload.items():
        if field in {"is_smoker", "has_addiction", "has_alcohol"}:
            if type(value) is not bool:
                raise ValidationError({field: "مقدار باید صحیح یا غلط باشد."})
            parsed = value
        elif field == "insurance":
            if not isinstance(value, list):
                raise ValidationError({field: "بیمه باید به‌صورت فهرست ارسال شود."})
            parsed = [_text(item) for item in value if _text(item)]
        elif field in {"weight_kg", "height_cm"}:
            parsed = _decimal(value, field)
        else:
            parsed = _text(value)
        setattr(locked, field, parsed)
    locked.full_clean()
    locked.save(update_fields=[*payload.keys(), "updated_at"])
    return locked


def _create_flat_tests(person, user, payload, payload_key, kind):
    records = payload.get(payload_key) or []
    if not isinstance(records, list):
        raise ValidationError({payload_key: "نتایج آزمایش باید به‌صورت فهرست ارسال شوند."})
    created = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValidationError({payload_key: f"آزمایش ردیف {index + 1} معتبر نیست."})
        field_prefix = f"{payload_key}.{index}"
        performed_at = _date(record.get("testDate"), f"{field_prefix}.testDate", required=True)
        name = _text(record.get("testName"))
        if not name:
            raise ValidationError({f"{field_prefix}.testName": "نام آزمایش الزامی است."})
        category = _text(record.get("category"))
        result = normalize_digits(record.get("value"))
        created.append(
            _create_lab_test(
                person=person,
                user=user,
                kind=kind,
                category=category,
                name=name,
                result=result,
                performed_at=performed_at,
                batch_key=f"{kind}:{performed_at.isoformat()}",
            )
        )
    return created


def _anti_hla_payload_from_records(records):
    if not isinstance(records, list):
        raise ValidationError({"records": "انتخاب‌های Anti-HLA باید فهرست باشند."})
    selections = []
    class_i_negative = False
    class_ii_negative = False
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValidationError({"records": f"ردیف {index + 1} معتبر نیست."})
        class_name = _text(record.get("class"))
        if record.get("isNone") or record.get("antigen") == "None":
            class_i_negative = class_i_negative or class_name == HLAClass.CLASS_I
            class_ii_negative = class_ii_negative or class_name == HLAClass.CLASS_II
            continue
        selections.append(
            {
                "class": class_name,
                "locus": _text(record.get("locus")),
                "antigen": _text(record.get("antigen")),
                "mfi": record.get("mfi"),
            }
        )
    return {
        "selections": selections,
        "class_i_negative": class_i_negative,
        "class_ii_negative": class_ii_negative,
    }


def _save_anti_hla_test(person, user, payload, *, instance=None):
    performed_at = _date(
        payload.get("performed_at") or payload.get("testDate"),
        "performed_at",
        required=True,
    )
    parsed = (
        _anti_hla_payload_from_records(payload.get("records") or [])
        if "records" in payload
        else {
            "selections": payload.get("selections") or [],
            "class_i_negative": _boolean(payload, "class_i_negative"),
            "class_ii_negative": _boolean(payload, "class_ii_negative"),
        }
    )
    if not isinstance(parsed["selections"], list):
        raise ValidationError({"selections": "انتخاب‌های Anti-HLA باید فهرست باشند."})
    test = instance or AntiHlaTest(person=person, created_by=user)
    test.performed_at = performed_at
    test.class_i_negative = parsed["class_i_negative"]
    test.class_ii_negative = parsed["class_ii_negative"]
    test.full_clean()
    test.save()
    test.selections.all().delete()
    for index, item in enumerate(parsed["selections"]):
        if not isinstance(item, dict):
            raise ValidationError({"selections": f"ردیف {index + 1} معتبر نیست."})
        selection = AntiHlaSelection(
            test=test,
            hla_class=_text(item.get("class") or item.get("hla_class")),
            locus=_text(item.get("locus")),
            antigen=_text(item.get("antigen")),
            mfi=_decimal(item.get("mfi"), f"selections.{index}.mfi"),
        )
        selection.full_clean()
        selection.save()
    return test


def _create_initial_anti_hla_tests(person, user, payload):
    records = payload.get("anti_hla_display") or []
    if not isinstance(records, list):
        raise ValidationError({"anti_hla_display": "نتایج Anti-HLA باید فهرست باشند."})
    groups = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValidationError({"anti_hla_display": f"ردیف {index + 1} معتبر نیست."})
        date_key = _text(record.get("testDate"))[:10]
        batch_key = _text(record.get("batchId")) or date_key
        groups.setdefault((batch_key, date_key), []).append(record)
    created = [
        _save_anti_hla_test(
            person,
            user,
            {"testDate": date_key, "records": grouped_records},
        )
        for (_batch_key, date_key), grouped_records in groups.items()
    ]
    return created


def _save_cdc_pra_test(person, user, cdc, *, instance=None, field_prefix="cdc_pra"):
    if not isinstance(cdc, dict):
        raise ValidationError({field_prefix: "اطلاعات CDC PRA معتبر نیست."})
    performed_at = _date(
        cdc.get("performed_at") or cdc.get("test_date"),
        f"{field_prefix}.performed_at",
        required=True,
    )
    parsed = {}
    implicit_flags = {}
    is_first_transplant = bool(
        hasattr(person, "recipient_profile")
        and person.recipient_profile.transplant_candidate == RecipientProfile.TransplantCandidate.FIRST
    )
    for key in ("class_i", "class_ii"):
        entry = cdc.get(key) or {}
        if not isinstance(entry, dict):
            raise ValidationError({f"{field_prefix}.{key}": "نتیجه CDC PRA معتبر نیست."})
        status = _text(entry.get("status"))
        if status not in CdcPraTest.ResultStatus.values:
            raise ValidationError({f"{field_prefix}.{key}.status": "وضعیت باید مثبت یا منفی باشد."})
        value = None
        if status == CdcPraTest.ResultStatus.POSITIVE:
            value = _decimal(entry.get("value"), f"{field_prefix}.{key}.value")
            if value is None or value < 0 or value > 100:
                raise ValidationError(
                    {f"{field_prefix}.{key}.value": "درصد PRA باید بین صفر تا صد باشد."}
                )
        implicit = bool(is_first_transplant and status == "positive" and value is not None and value <= 5)
        parsed[key] = {"status": status, "value": value}
        implicit_flags[key] = implicit
    overall_implicit = any(implicit_flags.values()) and all(
        parsed[key]["status"] == "negative" or implicit_flags[key]
        for key in ("class_i", "class_ii")
    )
    test = instance or CdcPraTest(person=person, created_by=user)
    test.performed_at = performed_at
    for key in ("class_i", "class_ii"):
        setattr(test, f"{key}_status", parsed[key]["status"])
        setattr(test, f"{key}_value", parsed[key]["value"])
        setattr(test, f"{key}_implicitly_negative", implicit_flags[key])
        setattr(
            test,
            f"{key}_effective_status",
            "negative" if implicit_flags[key] else parsed[key]["status"],
        )
    test.implicitly_negative = overall_implicit
    test.antibody_count = 0 if overall_implicit else None
    test.full_clean()
    test.save()
    return test


def _create_initial_cdc_pra_tests(person, user, payload):
    if "cdc_pra_tests" in payload:
        tests = payload.get("cdc_pra_tests")
        if not isinstance(tests, list):
            raise ValidationError({"cdc_pra_tests": "آزمایش‌های CDC PRA باید به‌صورت فهرست ارسال شوند."})
        created = []
        performed_dates = set()
        for index, cdc in enumerate(tests):
            field_prefix = f"cdc_pra_tests.{index}"
            if not isinstance(cdc, dict):
                raise ValidationError({field_prefix: "اطلاعات آزمایش CDC PRA معتبر نیست."})
            performed_at = _date(
                cdc.get("performed_at") or cdc.get("test_date"),
                f"{field_prefix}.performed_at",
                required=True,
            )
            if performed_at in performed_dates:
                raise ValidationError(
                    {f"{field_prefix}.performed_at": "برای هر تاریخ فقط یک آزمایش CDC PRA قابل ثبت است."}
                )
            performed_dates.add(performed_at)
            created.append(
                _save_cdc_pra_test(
                    person,
                    user,
                    cdc,
                    field_prefix=field_prefix,
                )
            )
        return created

    # سازگاری با کلاینت‌ها و draftهای قدیمی که تنها یک آزمایش ارسال می‌کردند.
    cdc = payload.get("cdc_pra") or {}
    if not isinstance(cdc, dict):
        raise ValidationError({"cdc_pra": "اطلاعات CDC PRA معتبر نیست."})
    entries = [cdc.get(key) or {} for key in ("class_i", "class_ii")]
    if not any(isinstance(entry, dict) and entry.get("status") for entry in entries):
        return []
    return [_save_cdc_pra_test(person, user, cdc)]


@transaction.atomic
def create_cdc_pra_test(person, user, payload):
    test = _save_cdc_pra_test(person, user, payload)
    _queue_matching_for_person(person, user)
    return test


@transaction.atomic
def update_cdc_pra_test(test, user, payload):
    locked = CdcPraTest.objects.select_for_update().get(pk=test.pk)
    updated = _save_cdc_pra_test(test.person, user, payload, instance=locked)
    _queue_matching_for_person(test.person, user)
    return updated


@transaction.atomic
def create_anti_hla_test(person, user, payload):
    test = _save_anti_hla_test(person, user, payload)
    _queue_matching_for_person(person, user, anti_hla_updated=True)
    return test


@transaction.atomic
def update_anti_hla_test(test, user, payload):
    locked = AntiHlaTest.objects.select_for_update().get(pk=test.pk)
    updated = _save_anti_hla_test(test.person, user, payload, instance=locked)
    _queue_matching_for_person(test.person, user, anti_hla_updated=True)
    return updated


def _create_approvals(person, payload, *, allowed_specialties):
    approvals = payload.get("approvals") or {}
    if not isinstance(approvals, dict):
        raise ValidationError({"approvals": "تأییدیه‌ها باید به‌صورت یک شیء ارسال شوند."})
    created = []
    for specialty, value in approvals.items():
        if specialty not in APPROVAL_SPECIALTIES or specialty not in allowed_specialties:
            raise ValidationError({f"approvals.{specialty}": "تخصص برای این پرونده مجاز نیست."})
        if not isinstance(value, dict):
            raise ValidationError({f"approvals.{specialty}": "تأییدیه معتبر نیست."})
        approval = MedicalApproval(
            person=person,
            specialty=specialty,
            status=_text(value.get("status")) or MedicalApproval.Status.ON_HOLD,
            approval_date=_date(value.get("approval_date"), f"approvals.{specialty}.approval_date"),
            doctor_name=_text(value.get("doctor_name")),
            medical_code=normalize_digits(value.get("medical_code")).strip(),
            notes=_text(value.get("notes")),
        )
        approval.full_clean()
        approval.save()
        created.append(approval)
    return created


def allowed_approval_specialties(person):
    if hasattr(person, "recipient_profile"):
        return {
            MedicalApproval.Specialty.NEPHROLOGIST,
            MedicalApproval.Specialty.DENTIST,
            MedicalApproval.Specialty.CARDIOLOGIST,
            MedicalApproval.Specialty.GASTROENTEROLOGIST,
            MedicalApproval.Specialty.UROLOGIST,
        }
    return {
        MedicalApproval.Specialty.NEPHROLOGIST,
        MedicalApproval.Specialty.CARDIOLOGIST,
        MedicalApproval.Specialty.UROLOGIST,
    }


def _save_approval(person, payload, *, instance=None):
    specialty = _text(payload.get("specialty")) or getattr(instance, "specialty", "")
    if specialty not in allowed_approval_specialties(person):
        raise ValidationError({"specialty": "این تخصص برای پرونده انتخاب‌شده مجاز نیست."})
    approval = instance or MedicalApproval(person=person, specialty=specialty)
    approval.specialty = specialty
    approval.status = _text(payload.get("status")) or approval.status
    approval.approval_date = _date(payload.get("approval_date"), "approval_date")
    approval.doctor_name = _text(payload.get("doctor_name"))
    approval.medical_code = normalize_digits(payload.get("medical_code")).strip()
    approval.notes = _text(payload.get("notes"))
    approval.full_clean()
    approval.save()
    return approval


@transaction.atomic
def create_medical_approval(person, payload):
    return _save_approval(person, payload)


@transaction.atomic
def update_medical_approval(approval, payload):
    locked = MedicalApproval.objects.select_for_update().get(pk=approval.pk)
    return _save_approval(approval.person, payload, instance=locked)


@transaction.atomic
def create_recipient(payload, user):
    person = _create_person(payload, user)
    has_dialysis = _boolean(payload, "has_dialysis_history")
    has_transfusion = _boolean(payload, "has_blood_transfusion")
    has_pregnancy = _boolean(payload, "has_pregnancy_history")
    has_abortion = _boolean(payload, "has_abortion_history")
    profile = RecipientProfile(
        person=person,
        transplant_candidate=_text(payload.get("transplant_candidate")),
        donor_living=_boolean(payload, "donor_living"),
        donor_deceased=_boolean(payload, "donor_deceased"),
        has_dialysis_history=has_dialysis,
        dialysis_type=_text(payload.get("dialysis_type")) if has_dialysis else "",
        dialysis_start_date=(
            _date(payload.get("dialysis_start_date"), "dialysis_start_date")
            if has_dialysis
            else None
        ),
        has_blood_transfusion=has_transfusion,
        blood_transfusion_units=(
            _integer(payload.get("blood_transfusion_units"), "blood_transfusion_units")
            if has_transfusion
            else None
        ),
        has_pregnancy_history=has_pregnancy,
        pregnancy_count=(
            _integer(payload.get("pregnancy_count"), "pregnancy_count")
            if has_pregnancy
            else None
        ),
        has_abortion_history=has_abortion,
        abortion_count=(
            _integer(payload.get("abortion_count"), "abortion_count")
            if has_abortion
            else None
        ),
        previous_transplant=_boolean(payload, "previous_transplant"),
        previous_transplant_details=_text(payload.get("previous_transplant_details")),
        drug_history=_text(payload.get("drug_history")),
        has_drug_allergy=_boolean(payload, "has_drug_allergy"),
        drug_allergy_details=_text(payload.get("drug_allergy_details")),
        underlying_diseases=_text(payload.get("underlying_diseases")),
        family_kidney_disease=_boolean(payload, "family_kidney_disease"),
        family_kidney_disease_details=_text(payload.get("family_kidney_disease_details")),
    )
    profile.full_clean()
    profile.save()
    from .workflows import record_initial_state

    record_initial_state(profile, user)
    _save_hla_typing(person, payload, skip_when_empty=True)
    tests = []
    tests.extend(_create_initial_cdc_pra_tests(person, user, payload))
    tests.extend(_create_initial_anti_hla_tests(person, user, payload))
    tests.extend(_create_flat_tests(person, user, payload, "routine_tests", LabTest.Kind.ROUTINE))
    tests.extend(_create_flat_tests(person, user, payload, "viral_tests", LabTest.Kind.VIRAL))
    _create_approvals(
        person,
        payload,
        allowed_specialties={
            MedicalApproval.Specialty.NEPHROLOGIST,
            MedicalApproval.Specialty.DENTIST,
            MedicalApproval.Specialty.CARDIOLOGIST,
            MedicalApproval.Specialty.GASTROENTEROLOGIST,
            MedicalApproval.Specialty.UROLOGIST,
        },
    )
    _queue_matching_for_person(person, user)
    return person, tests


def _recipient_by_identifier(value):
    identifier = normalize_digits(value).strip().upper()
    if identifier.isdigit():
        identifier = normalize_national_id(identifier)
    return (
        RecipientProfile.objects.select_related("person")
        .filter(person__identifier=identifier)
        .first()
    )


@transaction.atomic
def create_donor(payload, user):
    person = _create_person(payload, user)
    related = _boolean(payload, "is_related_recipient_candidate")
    preferred_recipient = None
    if related:
        identifier = _text(payload.get("preferred_recipient_national_id"))
        if not identifier:
            raise ValidationError(
                {"preferred_recipient_national_id": "شناسه گیرنده مورد نظر الزامی است."}
            )
        preferred_recipient = _recipient_by_identifier(identifier)
        if preferred_recipient is None:
            raise ValidationError(
                {"preferred_recipient_national_id": "گیرنده‌ای با این شناسه یافت نشد."}
            )
        requested_citizenship = _text(payload.get("citizenship")) or Person.Citizenship.IRANIAN
        if preferred_recipient.person.citizenship != requested_citizenship:
            raise ValidationError(
                {
                    "preferred_recipient_national_id": (
                        "تابعیت اهداکننده و گیرنده مورد نظر باید یکسان باشد."
                    )
                }
            )
    profile = DonorProfile(
        person=person,
        self_diabetes_history=_boolean(payload, "self_diabetes_history"),
        self_hypertension_history=_boolean(payload, "self_hypertension_history"),
        parent_diabetes_history=_boolean(payload, "parent_diabetes_history"),
        parent_hypertension_history=_boolean(payload, "parent_hypertension_history"),
        has_drug_allergy=_boolean(payload, "has_drug_allergy"),
        drug_allergy_details=_text(payload.get("drug_allergy_details")),
        is_related_recipient_candidate=related,
        preferred_recipient=preferred_recipient,
        recipient_relationship_group=_text(payload.get("recipient_relationship_group")),
        recipient_relationship_kind=_text(payload.get("recipient_relationship_kind")),
        recipient_relationship_details=_text(payload.get("recipient_relationship_details")),
    )
    profile.full_clean()
    profile.save()
    from .workflows import record_initial_state

    record_initial_state(profile, user)
    _save_hla_typing(person, payload, skip_when_empty=True)
    tests = []
    tests.extend(_create_flat_tests(person, user, payload, "routine_tests", LabTest.Kind.ROUTINE))
    tests.extend(_create_flat_tests(person, user, payload, "viral_tests", LabTest.Kind.VIRAL))
    _create_approvals(
        person,
        payload,
        allowed_specialties={
            MedicalApproval.Specialty.NEPHROLOGIST,
            MedicalApproval.Specialty.CARDIOLOGIST,
            MedicalApproval.Specialty.UROLOGIST,
        },
    )
    _queue_matching_for_person(person, user)
    return person, tests


def find_recipient(value):
    return _recipient_by_identifier(value)
