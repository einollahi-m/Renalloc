from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from time import perf_counter

from users.api import api_error, endpoint, validation_errors

from .choices import (
    ANTI_HLA_VALUES_BY_LOCUS,
    HLA_VALUES_BY_LOCUS,
    LAB_CATEGORY_CHOICES,
    ROUTINE_TEST_NAMES,
    VIRAL_TEST_NAMES,
)
from .creg import table_for_antibodies
from .models import (
    AllocationPolicy,
    AntiHlaTest,
    ClinicalStateEvent,
    CdcPraTest,
    CrossMatchRequest,
    DonorProfile,
    HLATyping,
    InAppNotification,
    LabTest,
    MatchProposal,
    MatchingRun,
    MedicalApproval,
    Person,
    RecipientProfile,
    SensitiveDataAccessLog,
)
from .matching import active_policy, evaluate_pair, low_resolution, rank_deceased_donor, run_matching
from .tasks import match_donor, match_national, match_recipient
from .services import (
    create_anti_hla_test,
    create_cdc_pra_test,
    create_donor,
    create_lab_test,
    create_medical_approval,
    create_recipient,
    find_recipient,
    update_anti_hla_test,
    update_cdc_pra_test,
    update_hla_typing,
    update_lab_test,
    save_lab_test_batch,
    update_medical_approval,
    update_person_profile,
)
from .workflows import allowed_transitions, record_priority_update, transition_profile
from .validators import (
    is_valid_iranian_national_id,
    normalize_digits,
    normalize_national_id,
)


HLA_LOCUS_TO_FIELD = {
    "A": "hla_a",
    "B": "hla_b",
    "C": "hla_c",
    "DRB1": "hla_drb1",
    "DQB1": "hla_dqb1",
    "DRB": "hla_drb",
    "DQA1": "hla_dqa1",
    "DPB1": "hla_dpb1",
    "DPA1": "hla_dpa1",
}


def serialize_person(person):
    blood_type = person.blood_group[:-1]
    rh_factor = "positive" if person.blood_group.endswith("+") else "negative"
    return {
        "id": str(person.pk),
        "citizenship": person.citizenship,
        "identifier": person.identifier,
        "national_id": person.identifier,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "full_name": person.full_name,
        "gender": person.gender,
        "birth_date": person.birth_date.isoformat(),
        "blood_group": person.blood_group,
        "blood_type": blood_type,
        "rh_factor": rh_factor,
        "phone": person.phone,
        "emergency_contact_phone": person.emergency_contact_phone,
        "nationality": person.nationality,
        "education": person.education,
        "insurance": person.insurance,
        "marital_status": person.marital_status,
        "weight_kg": str(person.weight_kg) if person.weight_kg is not None else None,
        "height_cm": str(person.height_cm) if person.height_cm is not None else None,
        "is_smoker": person.is_smoker,
        "has_addiction": person.has_addiction,
        "has_alcohol": person.has_alcohol,
        "is_active": person.is_active,
        "center": (
            {"id": person.center_id, "name": person.center.name} if person.center else None
        ),
        "created_at": person.created_at.isoformat(),
        "updated_at": person.updated_at.isoformat(),
    }


def serialize_hla(person):
    result = {field_name: [] for field_name in HLA_LOCUS_TO_FIELD.values()}
    try:
        typing = person.hla_typing
    except HLATyping.DoesNotExist:
        return None
    for selection in typing.selections.all():
        result[HLA_LOCUS_TO_FIELD[selection.locus]].extend(
            [selection.allele] * selection.copy_number
        )
    return {
        "id": str(typing.pk),
        **result,
        "updated_at": typing.updated_at.isoformat(),
    }


def serialize_lab_test(test):
    return {
        "id": str(test.pk),
        "kind": test.kind,
        "category": test.category,
        "name": test.name,
        "result": test.result,
        "performed_at": test.performed_at.isoformat(),
        "expires_at": test.expires_at.isoformat(),
        "is_expired": test.is_expired,
    }


def serialize_cdc_pra(test):
    return {
        "id": str(test.pk),
        "performed_at": test.performed_at.isoformat(),
        "expires_at": test.expires_at.isoformat(),
        "is_expired": test.is_expired,
        "class_i": {
            "status": test.class_i_status,
            "value": str(test.class_i_value) if test.class_i_value is not None else None,
            "effective_status": test.class_i_effective_status,
            "is_implicitly_negative": test.class_i_implicitly_negative,
        },
        "class_ii": {
            "status": test.class_ii_status,
            "value": str(test.class_ii_value) if test.class_ii_value is not None else None,
            "effective_status": test.class_ii_effective_status,
            "is_implicitly_negative": test.class_ii_implicitly_negative,
        },
        "implicitly_negative": test.implicitly_negative,
        "antibody_count": test.antibody_count,
    }


def serialize_anti_hla(test):
    selections = [
        {
            "id": selection.pk,
            "class": selection.hla_class,
            "locus": selection.locus,
            "antigen": selection.antigen,
            "mfi": str(selection.mfi) if selection.mfi is not None else None,
        }
        for selection in test.selections.all()
    ]
    records = [
        {
            "key": f"{test.pk}-{item['locus']}-{item['antigen']}",
            "batchId": str(test.pk),
            "class": item["class"],
            "locus": item["locus"],
            "antigen": item["antigen"],
            "testName": f"{item['locus']} - {item['antigen']}",
            "value": None,
            "mfi": item["mfi"],
            "testDate": test.performed_at.isoformat(),
        }
        for item in selections
    ]
    if test.class_i_negative:
        records.append(
            {
                "key": f"{test.pk}-class-I-none",
                "batchId": str(test.pk),
                "class": "I",
                "locus": "",
                "antigen": "None",
                "testName": "Class I - None",
                "isNone": True,
                "testDate": test.performed_at.isoformat(),
            }
        )
    if test.class_ii_negative:
        records.append(
            {
                "key": f"{test.pk}-class-II-none",
                "batchId": str(test.pk),
                "class": "II",
                "locus": "",
                "antigen": "None",
                "testName": "Class II - None",
                "isNone": True,
                "testDate": test.performed_at.isoformat(),
            }
        )
    return {
        "id": str(test.pk),
        "performed_at": test.performed_at.isoformat(),
        "testDate": test.performed_at.isoformat(),
        "expires_at": test.expires_at.isoformat(),
        "is_expired": test.is_expired,
        "class_i_negative": test.class_i_negative,
        "class_ii_negative": test.class_ii_negative,
        "selections": selections,
        "records": records,
    }


def latest_cpra(person):
    test = person.cdc_pra_tests.order_by("-performed_at", "-created_at").first()
    if test is None:
        return None
    values = []
    for prefix in ("class_i", "class_ii"):
        if getattr(test, f"{prefix}_effective_status") == CdcPraTest.ResultStatus.POSITIVE:
            value = getattr(test, f"{prefix}_value")
            if value is not None:
                values.append(float(value))
    return max(values, default=0)


def serialize_recipient_summary(person):
    profile = person.recipient_profile
    base = serialize_person(person)
    return {
        "_id": base["id"],
        "fullName": base["full_name"],
        "nationalId": base["national_id"],
        "birthDate": base["birth_date"],
        "gender": base["gender"],
        "bloodType": base["blood_type"],
        "rhFactor": base["rh_factor"],
        "phone": base["phone"],
        "status": profile.status,
        "statusDisplay": profile.get_status_display(),
        "allowedTransitions": allowed_transitions(profile),
        "waitingSince": profile.waiting_since.isoformat() if profile.waiting_since else None,
        "medicalUrgency": profile.medical_urgency,
        "regionalDisadvantage": profile.regional_disadvantage,
        "isEmergency": profile.is_emergency,
        "emergencyReason": profile.emergency_reason,
        "cpra": latest_cpra(person),
        "priorityScore": None,
        "citizenship": base["citizenship"],
    }


def serialize_donor_summary(person):
    profile = person.donor_profile
    related = profile.is_related_recipient_candidate
    donor_type = (
        "living_related"
        if related and profile.recipient_relationship_group != DonorProfile.RelationshipGroup.STRANGER
        else "living_unrelated"
    )
    relationship = (
        profile.get_recipient_relationship_kind_display()
        if profile.recipient_relationship_kind
        else profile.recipient_relationship_details
    )
    base = serialize_person(person)
    return {
        "_id": base["id"],
        "fullName": base["full_name"],
        "nationalId": base["national_id"],
        "birthDate": base["birth_date"],
        "gender": base["gender"],
        "bloodType": base["blood_type"],
        "rhFactor": base["rh_factor"],
        "phone": base["phone"],
        "donorType": donor_type,
        "relationship": relationship or None,
        "status": profile.status,
        "statusDisplay": profile.get_status_display(),
        "allowedTransitions": allowed_transitions(profile),
        "citizenship": base["citizenship"],
    }


def serialize_approval(approval):
    return {
        "id": approval.pk,
        "specialty": approval.specialty,
        "specialty_display": approval.get_specialty_display(),
        "status": approval.status,
        "status_display": approval.get_status_display(),
        "approval_date": (
            approval.approval_date.isoformat() if approval.approval_date else None
        ),
        "doctor_name": approval.doctor_name,
        "medical_code": approval.medical_code,
        "notes": approval.notes,
    }


def serialize_approvals(person):
    return [serialize_approval(approval) for approval in person.medical_approvals.all()]


def serialize_recipient_detail(person):
    profile = person.recipient_profile
    latest_anti = person.anti_hla_tests.first()
    antibody_antigens = (
        [selection.antigen for selection in latest_anti.selections.all()]
        if latest_anti
        else []
    )
    hla_values = []
    try:
        hla_values = [selection.allele for selection in person.hla_typing.selections.all()]
    except HLATyping.DoesNotExist:
        pass
    hla_low = {low_resolution(value) for value in hla_values}
    overlaps = sorted(
        {
            antibody
            for antibody in antibody_antigens
            if low_resolution(antibody) in hla_low
        }
    )
    return {
        "person": serialize_person(person),
        "summary": serialize_recipient_summary(person),
        "profile": {
            "status": profile.status,
            "status_display": profile.get_status_display(),
            "allowed_transitions": allowed_transitions(profile),
            "waiting_since": profile.waiting_since.isoformat() if profile.waiting_since else None,
            "medical_urgency": profile.medical_urgency,
            "regional_disadvantage": profile.regional_disadvantage,
            "is_emergency": profile.is_emergency,
            "emergency_reason": profile.emergency_reason,
            "transplant_candidate": profile.transplant_candidate,
            "donor_living": profile.donor_living,
            "donor_deceased": profile.donor_deceased,
            "has_dialysis_history": profile.has_dialysis_history,
            "dialysis_type": profile.dialysis_type,
            "dialysis_start_date": (
                profile.dialysis_start_date.isoformat()
                if profile.dialysis_start_date
                else None
            ),
            "has_blood_transfusion": profile.has_blood_transfusion,
            "blood_transfusion_units": profile.blood_transfusion_units,
            "previous_transplant": profile.previous_transplant,
            "has_drug_allergy": profile.has_drug_allergy,
            "family_kidney_disease": profile.family_kidney_disease,
        },
        "hla": serialize_hla(person),
        "cdc_pra_tests": [serialize_cdc_pra(test) for test in person.cdc_pra_tests.all()],
        "anti_hla_tests": [serialize_anti_hla(test) for test in person.anti_hla_tests.all()],
        "lab_tests": [serialize_lab_test(test) for test in person.lab_tests.all()],
        "approvals": serialize_approvals(person),
        "immune_alerts": {
            "hla_anti_hla_overlaps": overlaps,
            "has_hla_anti_hla_overlap": bool(overlaps),
            "has_anti_hla": bool(antibody_antigens),
            "creg_table": table_for_antibodies(antibody_antigens),
        },
        "state_events": serialize_state_events(profile.state_events.all()[:50]),
    }


def serialize_donor_detail(person):
    profile = person.donor_profile
    preferred = profile.preferred_recipient.person if profile.preferred_recipient else None
    return {
        "person": serialize_person(person),
        "summary": serialize_donor_summary(person),
        "profile": {
            "status": profile.status,
            "status_display": profile.get_status_display(),
            "allowed_transitions": allowed_transitions(profile),
            "self_diabetes_history": profile.self_diabetes_history,
            "self_hypertension_history": profile.self_hypertension_history,
            "parent_diabetes_history": profile.parent_diabetes_history,
            "parent_hypertension_history": profile.parent_hypertension_history,
            "has_drug_allergy": profile.has_drug_allergy,
            "is_related_recipient_candidate": profile.is_related_recipient_candidate,
            "preferred_recipient": serialize_person(preferred) if preferred else None,
            "recipient_relationship_group": profile.recipient_relationship_group,
            "recipient_relationship_kind": profile.recipient_relationship_kind,
            "recipient_relationship_details": profile.recipient_relationship_details,
        },
        "hla": serialize_hla(person),
        "lab_tests": [serialize_lab_test(test) for test in person.lab_tests.all()],
        "approvals": serialize_approvals(person),
        "state_events": serialize_state_events(profile.state_events.all()[:50]),
    }


def serialize_state_events(events):
    return [
        {
            "id": str(event.pk),
            "previous_status": event.previous_status,
            "new_status": event.new_status,
            "reason": event.reason,
            "actor": event.actor.full_name if event.actor else "سیستم",
            "metadata": event.metadata,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


def _log_hla_access(request, person, purpose):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",", 1)[0].strip()
    source_ip = forwarded or request.META.get("REMOTE_ADDR") or None
    SensitiveDataAccessLog.objects.create(
        user=request.api_user,
        person=person,
        purpose=purpose,
        source_ip=source_ip,
    )


def _mutation_error(exc):
    if isinstance(exc, ValidationError):
        return api_error(
            "اطلاعات ارسال‌شده کامل یا معتبر نیست.",
            errors=validation_errors(exc),
        )
    return api_error("این رکورد قبلاً ثبت شده است.", status=409)


def _handle_creation(create, request, role):
    try:
        person, _tests = create(request.data, request.api_user)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse(
        {
            "message": (
                "گیرنده با موفقیت ثبت شد."
                if role == "recipient"
                else "اهداکننده با موفقیت ثبت شد."
            ),
            role: serialize_person(person),
        },
        status=201,
    )


def _visible_people(user):
    query = Person.objects.all()
    if not user.is_staff:
        query = query.filter(center_id=user.center_id)
    return query


def _can_access_person(user, person):
    return bool(user.is_staff or (user.center_id and user.center_id == person.center_id))


def _level_one_forbidden(request):
    if request.api_user.can_manage_clinical_workflow:
        return None
    return api_error(
        "تغییر وضعیت و اولویت فقط برای هماهنگ‌کننده پیوند سطح یک مجاز است.",
        status=403,
    )


def _paginated_payload(request, queryset, serialize, key):
    try:
        page_size = min(100, max(5, int(request.GET.get("page_size", 25))))
    except (TypeError, ValueError):
        page_size = 25
    paginator = Paginator(queryset, page_size)
    page = paginator.get_page(request.GET.get("page", 1))
    return {
        key: [serialize(item) for item in page.object_list],
        "pagination": {
            "page": page.number,
            "page_size": page_size,
            "count": paginator.count,
            "pages": paginator.num_pages,
            "has_next": page.has_next(),
            "has_previous": page.has_previous(),
        },
    }


@endpoint("GET", "POST", authenticated=True)
def recipients(request):
    if request.method == "POST":
        return _handle_creation(create_recipient, request, "recipient")
    people = (
        _visible_people(request.api_user).filter(recipient_profile__isnull=False)
        .select_related("center", "recipient_profile")
        .prefetch_related("cdc_pra_tests")
    )
    search = str(request.GET.get("search", "")).strip()
    if search:
        people = people.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(identifier__icontains=normalize_digits(search))
            | Q(phone__icontains=normalize_digits(search))
        )
    for field in ("citizenship", "gender"):
        if value := request.GET.get(field):
            people = people.filter(**{field: value})
    if blood_type := request.GET.get("blood_type"):
        people = people.filter(blood_group__in=(f"{blood_type}+", f"{blood_type}-"))
    if status := request.GET.get("status"):
        people = (
            people.exclude(recipient_profile__status=RecipientProfile.Status.ACTIVE)
            if status == "inactive"
            else people.filter(recipient_profile__status=status)
        )
    return JsonResponse(
        _paginated_payload(request, people, serialize_recipient_summary, "recipients")
    )


@endpoint("GET", authenticated=True)
def recipient_detail(request, person_id):
    person = (
        Person.objects.filter(pk=person_id, recipient_profile__isnull=False)
        .select_related("center", "recipient_profile", "hla_typing")
        .prefetch_related(
            "hla_typing__selections",
            "cdc_pra_tests",
            "anti_hla_tests__selections",
            "lab_tests",
            "medical_approvals",
        )
        .first()
    )
    if person is None:
        return api_error("گیرنده یافت نشد.", status=404)
    if not _can_access_person(request.api_user, person):
        return api_error("به این پرونده دسترسی ندارید.", status=403)
    _log_hla_access(request, person, "مشاهده پرونده کامل گیرنده")
    return JsonResponse({"recipient": serialize_recipient_detail(person)})


@endpoint("GET", "POST", authenticated=True)
def donors(request):
    if request.method == "POST":
        return _handle_creation(create_donor, request, "donor")
    people = _visible_people(request.api_user).filter(donor_profile__isnull=False).select_related(
        "center", "donor_profile"
    )
    search = str(request.GET.get("search", "")).strip()
    if search:
        people = people.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(identifier__icontains=normalize_digits(search))
            | Q(phone__icontains=normalize_digits(search))
        )
    if blood_type := request.GET.get("blood_type"):
        people = people.filter(blood_group__in=(f"{blood_type}+", f"{blood_type}-"))
    if status := request.GET.get("status"):
        people = people.filter(donor_profile__status=status)
    if donor_type := request.GET.get("donor_type"):
        if donor_type == "deceased":
            people = people.none()
        elif donor_type in {"living_related", "living_unrelated"}:
            people = people.filter(
                donor_profile__is_related_recipient_candidate=(donor_type == "living_related")
            )
    return JsonResponse(_paginated_payload(request, people, serialize_donor_summary, "donors"))


@endpoint("GET", authenticated=True)
def donor_detail(request, person_id):
    person = (
        Person.objects.filter(pk=person_id, donor_profile__isnull=False)
        .select_related(
            "center",
            "donor_profile",
            "donor_profile__preferred_recipient__person",
            "hla_typing",
        )
        .prefetch_related("hla_typing__selections", "lab_tests", "medical_approvals")
        .first()
    )
    if person is None:
        return api_error("اهداکننده یافت نشد.", status=404)
    if not _can_access_person(request.api_user, person):
        return api_error("به این پرونده دسترسی ندارید.", status=403)
    _log_hla_access(request, person, "مشاهده پرونده کامل اهداکننده")
    return JsonResponse({"donor": serialize_donor_detail(person)})


@endpoint("GET", authenticated=True)
def identifier_availability(request):
    citizenship = request.GET.get("citizenship", Person.Citizenship.IRANIAN)
    raw_identifier = request.GET.get("identifier", "")
    identifier = normalize_digits(raw_identifier).strip().upper()
    valid = bool(identifier)
    if citizenship == Person.Citizenship.IRANIAN:
        identifier = normalize_national_id(identifier)
        valid = is_valid_iranian_national_id(identifier)
    if citizenship not in Person.Citizenship.values:
        return api_error("نوع تابعیت معتبر نیست.")
    available = valid and not Person.objects.filter(identifier=identifier).exists()
    return JsonResponse({"valid": valid, "available": available})


@endpoint("GET", authenticated=True)
def recipient_lookup(request):
    identifier = request.GET.get("identifier", "").strip()
    if not identifier:
        return api_error("کد ملی یا شناسه گیرنده الزامی است.")
    profile = find_recipient(identifier)
    if profile is None:
        return api_error("گیرنده‌ای با این شناسه یافت نشد.", status=404)
    if not _can_access_person(request.api_user, profile.person):
        return api_error("به این پرونده دسترسی ندارید.", status=403)
    return JsonResponse({"recipient": serialize_recipient_summary(profile.person)})


@endpoint("GET", authenticated=True)
def person_lookup(request):
    identifier = normalize_digits(request.GET.get("identifier", "")).strip().upper()
    if identifier.isdigit():
        identifier = normalize_national_id(identifier)
    if not identifier:
        return api_error("کد ملی یا شناسه فرد الزامی است.")
    person = _visible_people(request.api_user).filter(identifier=identifier).select_related(
        "recipient_profile", "donor_profile"
    ).first()
    if person is None:
        return api_error("فردی با این شناسه یافت نشد.", status=404)
    if hasattr(person, "recipient_profile"):
        return JsonResponse(
            {"person": {**serialize_recipient_summary(person), "type": "recipient"}}
        )
    if hasattr(person, "donor_profile"):
        return JsonResponse(
            {"person": {**serialize_donor_summary(person), "type": "donor"}}
        )
    return api_error("برای این فرد پرونده بالینی یافت نشد.", status=404)


def _person_or_404(person_id, *, recipient_only=False, user=None):
    query = Person.objects.filter(pk=person_id)
    if user is not None and not user.is_staff:
        query = query.filter(center_id=user.center_id)
    if recipient_only:
        query = query.filter(recipient_profile__isnull=False)
    return query.select_related("recipient_profile").first()


@endpoint("GET", "PUT", authenticated=True)
def person_hla(request, person_id):
    person = _person_or_404(person_id, user=request.api_user)
    if person is None:
        return api_error("فرد یافت نشد.", status=404)
    if not _can_access_person(request.api_user, person):
        return api_error("به این پرونده دسترسی ندارید.", status=403)
    if request.method == "GET":
        _log_hla_access(request, person, "مشاهده مستقیم تایپ HLA")
        return JsonResponse({"hla": serialize_hla(person)})
    try:
        update_hla_typing(person, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    person.refresh_from_db()
    return JsonResponse({"message": "تایپ HLA ذخیره شد.", "hla": serialize_hla(person)})


@endpoint("PATCH", authenticated=True)
def person_profile(request, person_id):
    person = _person_or_404(person_id, user=request.api_user)
    if person is None:
        return api_error("فرد یافت نشد.", status=404)
    try:
        person = update_person_profile(person, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse(
        {"message": "اطلاعات تماس و مشخصات غیرهویتی ذخیره شد.", "person": serialize_person(person)}
    )


@endpoint("GET", "POST", authenticated=True)
def lab_test_collection(request, person_id):
    person = _person_or_404(person_id, user=request.api_user)
    if person is None:
        return api_error("فرد یافت نشد.", status=404)
    if request.method == "GET":
        return JsonResponse({"lab_tests": [serialize_lab_test(test) for test in person.lab_tests.all()]})
    try:
        if "tests" in request.data:
            tests = save_lab_test_batch(person, request.api_user, request.data)
            return JsonResponse(
                {
                    "message": "مجموعه نتایج آزمایش ذخیره شد.",
                    "tests": [serialize_lab_test(test) for test in tests],
                },
                status=201,
            )
        test = create_lab_test(person, request.api_user, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse(
        {"message": "نتیجه آزمایش ثبت شد.", "test": serialize_lab_test(test)}, status=201
    )


@endpoint("PATCH", authenticated=True)
def lab_test_item(request, person_id, test_id):
    test = LabTest.objects.filter(pk=test_id, person_id=person_id).select_related("person").first()
    if test is None:
        return api_error("آزمایش یافت نشد.", status=404)
    if not _can_access_person(request.api_user, test.person):
        return api_error("به این پرونده دسترسی ندارید.", status=403)
    try:
        test = update_lab_test(test, request.api_user, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse({"message": "نتیجه آزمایش ویرایش شد.", "test": serialize_lab_test(test)})


@endpoint("GET", "POST", authenticated=True)
def approval_collection(request, person_id):
    person = _person_or_404(person_id, user=request.api_user)
    if person is None:
        return api_error("فرد یافت نشد.", status=404)
    if request.method == "GET":
        return JsonResponse({"approvals": serialize_approvals(person)})
    try:
        approval = create_medical_approval(person, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse(
        {"message": "تأییدیه پزشکی ثبت شد.", "approval": serialize_approval(approval)},
        status=201,
    )


@endpoint("PATCH", authenticated=True)
def approval_item(request, person_id, approval_id):
    approval = MedicalApproval.objects.filter(
        pk=approval_id, person_id=person_id
    ).select_related("person", "person__recipient_profile", "person__donor_profile").first()
    if approval is None:
        return api_error("تأییدیه یافت نشد.", status=404)
    if not _can_access_person(request.api_user, approval.person):
        return api_error("به این پرونده دسترسی ندارید.", status=403)
    try:
        approval = update_medical_approval(approval, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse(
        {"message": "تأییدیه پزشکی ویرایش شد.", "approval": serialize_approval(approval)}
    )


@endpoint("GET", "POST", authenticated=True)
def cdc_pra_collection(request, person_id):
    person = _person_or_404(person_id, recipient_only=True, user=request.api_user)
    if person is None:
        return api_error("گیرنده یافت نشد.", status=404)
    if request.method == "GET":
        tests = person.cdc_pra_tests.all()
        return JsonResponse({"cdc_pra_tests": [serialize_cdc_pra(test) for test in tests]})
    try:
        test = create_cdc_pra_test(person, request.api_user, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse(
        {"message": "آزمایش CDC PRA ثبت شد.", "test": serialize_cdc_pra(test)},
        status=201,
    )


@endpoint("PATCH", authenticated=True)
def cdc_pra_item(request, person_id, test_id):
    test = CdcPraTest.objects.filter(pk=test_id, person_id=person_id).select_related("person").first()
    if test is None:
        return api_error("آزمایش CDC PRA یافت نشد.", status=404)
    if not _can_access_person(request.api_user, test.person):
        return api_error("به این پرونده دسترسی ندارید.", status=403)
    try:
        test = update_cdc_pra_test(test, request.api_user, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse({"message": "آزمایش CDC PRA ویرایش شد.", "test": serialize_cdc_pra(test)})


@endpoint("GET", "POST", authenticated=True)
def anti_hla_collection(request, person_id):
    person = _person_or_404(person_id, recipient_only=True, user=request.api_user)
    if person is None:
        return api_error("گیرنده یافت نشد.", status=404)
    if request.method == "GET":
        tests = person.anti_hla_tests.prefetch_related("selections")
        return JsonResponse({"anti_hla_tests": [serialize_anti_hla(test) for test in tests]})
    try:
        test = create_anti_hla_test(person, request.api_user, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse(
        {"message": "آزمایش Anti-HLA ثبت شد.", "test": serialize_anti_hla(test)},
        status=201,
    )


@endpoint("PATCH", authenticated=True)
def anti_hla_item(request, person_id, test_id):
    test = AntiHlaTest.objects.filter(pk=test_id, person_id=person_id).select_related("person").first()
    if test is None:
        return api_error("آزمایش Anti-HLA یافت نشد.", status=404)
    if not _can_access_person(request.api_user, test.person):
        return api_error("به این پرونده دسترسی ندارید.", status=403)
    try:
        test = update_anti_hla_test(test, request.api_user, request.data)
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse({"message": "آزمایش Anti-HLA ویرایش شد.", "test": serialize_anti_hla(test)})


def serialize_proposal(proposal, *, patient_view=False):
    base = {
        "id": str(proposal.pk),
        "rank": proposal.rank,
        "compatibility": proposal.compatibility,
        "compatibility_display": proposal.get_compatibility_display(),
        "decision": proposal.decision,
        "decision_display": proposal.get_decision_display(),
        "final_score": float(proposal.final_score),
        "abo_compatible": proposal.abo_compatible,
        "citizenship_compatible": (
            proposal.donor.person.citizenship == proposal.recipient.person.citizenship
        ),
        "anti_hla_status": proposal.anti_hla_status,
        "warnings": proposal.warnings,
        "creg_summary": proposal.score_breakdown.get("creg_summary", {}),
        "created_at": proposal.created_at.isoformat(),
    }
    if patient_view:
        consultation = proposal.crossmatch_requests.order_by("-created_at").first()
        return {
            **base,
            "donor": {
                "anonymous_code": f"D-{str(proposal.donor_id).split('-')[0].upper()}",
                "blood_group": proposal.donor.person.blood_group,
                "status": proposal.donor.status,
                "status_display": proposal.donor.get_status_display(),
            },
            "immune_summary": (
                "نیازمند بررسی تکمیلی"
                if proposal.compatibility == MatchProposal.Compatibility.CONDITIONAL
                else "بدون مشکل شناسایی‌شده"
            ),
            "hla_similarity": {
                "matches": proposal.hla_summary.get("total_matches", 0),
                "maximum": 10,
                "percent": proposal.hla_summary.get("percent", 0),
            },
            "requires_physical_crossmatch": True,
            "consultation": (
                {
                    "status": consultation.status,
                    "status_display": consultation.get_status_display(),
                }
                if consultation
                else None
            ),
            "can_request_consultation": bool(
                proposal.decision == MatchProposal.Decision.PROPOSED and consultation is None
            ),
        }
    return {
        **base,
        "recipient": serialize_recipient_summary(proposal.recipient.person),
        "donor": serialize_donor_summary(proposal.donor.person),
        "hla_summary": proposal.hla_summary,
        "score_breakdown": proposal.score_breakdown,
        "rejection_reasons": proposal.rejection_reasons,
        "center_note": proposal.center_note,
        "run_id": str(proposal.run_id),
    }


def serialize_crossmatch(item):
    return {
        "id": str(item.pk),
        "proposal": serialize_proposal(item.proposal),
        "status": item.status,
        "status_display": item.get_status_display(),
        "patient_note": item.patient_note,
        "physician_note": item.physician_note,
        "scheduled_at": item.scheduled_at.isoformat() if item.scheduled_at else None,
        "result_at": item.result_at.isoformat() if item.result_at else None,
        "requested_by": item.requested_by.full_name,
        "reviewed_by": item.reviewed_by.full_name if item.reviewed_by else None,
        "created_at": item.created_at.isoformat(),
    }


def _profile_for_user(model, person_id, user):
    query = model.objects.filter(pk=person_id).select_related("person")
    if not user.is_staff:
        query = query.filter(person__center_id=user.center_id)
    return query.first()


@endpoint("POST", authenticated=True)
def recipient_status(request, person_id):
    if forbidden := _level_one_forbidden(request):
        return forbidden
    profile = _profile_for_user(RecipientProfile, person_id, request.api_user)
    if profile is None:
        return api_error("گیرنده یافت نشد.", status=404)
    try:
        profile = transition_profile(
            profile,
            str(request.data.get("status", "")),
            request.api_user,
            request.data.get("reason", ""),
        )
    except ValidationError as exc:
        return _mutation_error(exc)
    return JsonResponse(
        {"message": "وضعیت گیرنده تغییر کرد.", "recipient": serialize_recipient_summary(profile.person)}
    )


@endpoint("PATCH", authenticated=True)
@transaction.atomic
def recipient_priority(request, person_id):
    if forbidden := _level_one_forbidden(request):
        return forbidden
    profile = _profile_for_user(RecipientProfile, person_id, request.api_user)
    if profile is None:
        return api_error("گیرنده یافت نشد.", status=404)
    allowed = {
        "medical_urgency",
        "regional_disadvantage",
        "waiting_since",
        "is_emergency",
        "emergency_reason",
    }
    if not set(request.data).issubset(allowed) or not request.data:
        return api_error("فیلدهای اولویت معتبر نیستند.")
    profile = RecipientProfile.objects.select_for_update().select_related("person").get(pk=profile.pk)
    previous_priority = {
        "medical_urgency": profile.medical_urgency,
        "regional_disadvantage": profile.regional_disadvantage,
        "waiting_since": profile.waiting_since.isoformat() if profile.waiting_since else None,
        "is_emergency": profile.is_emergency,
        "emergency_reason": profile.emergency_reason,
    }
    for field, value in request.data.items():
        if field == "waiting_since":
            value = value or None
        elif field == "is_emergency" and type(value) is not bool:
            return api_error("مقدار وضعیت اورژانسی باید صحیح یا غلط باشد.")
        elif field == "emergency_reason":
            value = str(value or "").strip()
        setattr(profile, field, value)
    if not profile.is_emergency:
        profile.emergency_reason = ""
    try:
        profile.full_clean()
        update_fields = set(request.data) | {"emergency_reason", "updated_at"}
        profile.save(update_fields=update_fields)
    except (ValidationError, ValueError) as exc:
        if isinstance(exc, ValidationError):
            return _mutation_error(exc)
        return api_error("مقادیر اولویت معتبر نیستند.")
    current_priority = {
        "medical_urgency": profile.medical_urgency,
        "regional_disadvantage": profile.regional_disadvantage,
        "waiting_since": profile.waiting_since.isoformat() if profile.waiting_since else None,
        "is_emergency": profile.is_emergency,
        "emergency_reason": profile.emergency_reason,
    }
    record_priority_update(profile, request.api_user, previous_priority, current_priority)
    match_recipient.delay_on_commit(str(profile.pk), request.api_user.pk, "manual")
    return JsonResponse({"message": "اولویت و شرایط اورژانسی گیرنده ذخیره شد.", "recipient": serialize_recipient_summary(profile.person)})


@endpoint("POST", authenticated=True)
def donor_status(request, person_id):
    if forbidden := _level_one_forbidden(request):
        return forbidden
    profile = _profile_for_user(DonorProfile, person_id, request.api_user)
    if profile is None:
        return api_error("اهداکننده یافت نشد.", status=404)
    try:
        profile = transition_profile(
            profile,
            str(request.data.get("status", "")),
            request.api_user,
            request.data.get("reason", ""),
        )
    except ValidationError as exc:
        return _mutation_error(exc)
    return JsonResponse(
        {"message": "وضعیت اهداکننده تغییر کرد.", "donor": serialize_donor_summary(profile.person)}
    )


@endpoint("POST", authenticated=True)
def matching_preview(request):
    recipient = RecipientProfile.objects.filter(pk=request.data.get("recipient_id")).select_related(
        "person", "person__hla_typing"
    ).prefetch_related(
        "person__hla_typing__selections",
        "person__anti_hla_tests__selections",
        "person__cdc_pra_tests",
    ).first()
    donor = DonorProfile.objects.filter(pk=request.data.get("donor_id")).select_related(
        "person", "person__hla_typing", "preferred_recipient"
    ).prefetch_related("person__hla_typing__selections").first()
    if recipient is None or donor is None:
        return api_error("گیرنده یا اهداکننده یافت نشد.", status=404)
    if not _can_access_person(request.api_user, recipient.person):
        return api_error("به پرونده گیرنده دسترسی ندارید.", status=403)
    result = evaluate_pair(recipient, donor, check_state=False)
    _log_hla_access(request, recipient.person, "پیش‌نمایش Matching")
    _log_hla_access(request, donor.person, "پیش‌نمایش Matching")
    return JsonResponse(
        {
            "result": result,
            "recipient": serialize_recipient_summary(recipient.person),
            "donor": serialize_donor_summary(donor.person),
        }
    )


@endpoint("POST", authenticated=True)
def deceased_donor_matching(request):
    citizenship = str(request.data.get("citizenship", "")).strip()
    blood_group = str(request.data.get("blood_group", "")).strip().upper()
    if citizenship not in Person.Citizenship.values:
        return api_error("تابعیت اهداکننده جسد معتبر نیست.")
    if blood_group not in Person.BloodGroup.values:
        return api_error("گروه خونی اهداکننده جسد معتبر نیست.")
    hla_by_locus = {}
    errors = {}
    for locus, field in HLA_LOCUS_TO_FIELD.items():
        alleles = request.data.get(field) or []
        if not isinstance(alleles, list) or len(alleles) > 2:
            errors[field] = ["برای هر locus حداکثر دو آلل قابل ارسال است."]
            continue
        invalid = [allele for allele in alleles if allele not in HLA_VALUES_BY_LOCUS.get(locus, ())]
        if invalid:
            errors[field] = ["یک یا چند آلل انتخاب‌شده معتبر نیست."]
        hla_by_locus[locus] = alleles
    if errors:
        return api_error("تایپ HLA معتبر نیست.", errors=errors)
    if not any(hla_by_locus.values()):
        return api_error("حداقل یک آلل HLA برای اهداکننده جسد وارد کنید.")
    try:
        top_n = min(100, max(1, int(request.data.get("top_n", 25))))
    except (TypeError, ValueError):
        return api_error("تعداد نتایج معتبر نیست.")

    started = perf_counter()
    ranked = rank_deceased_donor(
        citizenship=citizenship,
        blood_group=blood_group,
        hla_by_locus=hla_by_locus,
        top_n=top_n,
    )
    items = []
    for rank, (recipient, result) in enumerate(ranked["items"], start=1):
        person = recipient.person
        can_view = _can_access_person(request.api_user, person)
        items.append(
            {
                "rank": rank,
                "recipient": {
                    "id": str(person.pk) if can_view else None,
                    "anonymous_code": f"R-{str(person.pk).split('-')[0].upper()}",
                    "full_name": person.full_name if can_view else None,
                    "citizenship": person.citizenship,
                    "blood_group": person.blood_group,
                    "birth_date": person.birth_date.isoformat(),
                    "center": person.center.name if person.center else None,
                    "can_view_profile": can_view,
                },
                "waiting_since": (
                    recipient.waiting_since.isoformat() if recipient.waiting_since else None
                ),
                "waiting_days": result["score_breakdown"]["waiting_days"],
                "medical_urgency": recipient.medical_urgency,
                "regional_disadvantage": recipient.regional_disadvantage,
                "cpra": result["score_breakdown"]["cpra_difficulty"],
                "compatibility": result["compatibility"],
                "final_score": result["final_score"],
                "hla_summary": result["hla_summary"],
                "anti_hla_status": result["anti_hla_status"],
                "creg_summary": result["creg_summary"],
                "warnings": result["warnings"],
            }
        )
    return JsonResponse(
        {
            "matches": items,
            "statistics": {
                "evaluated_candidates": ranked["evaluated_candidates"],
                "rejected_candidates": ranked["rejected_candidates"],
                "candidate_limit": ranked["candidate_limit"],
                "returned": len(items),
                "elapsed_ms": round((perf_counter() - started) * 1000, 2),
                "policy_version": ranked["policy"].version,
            },
            "notice": (
                "این خروجی ابزار پشتیبان تصمیم است و جایگزین Cross-Match فیزیکی و "
                "تأیید تیم پیوند نیست. فقط گیرندگان فعالِ متقاضی اهداکننده جسد و هم‌تابعیت بررسی شدند."
            ),
        }
    )


@endpoint("POST", authenticated=True)
def matching_run(request):
    recipient_id = request.data.get("recipient_id")
    donor_id = request.data.get("donor_id")
    if not request.api_user.is_staff and not recipient_id:
        return api_error("اجرای ملی Matching فقط برای مدیر ملی مجاز است.", status=403)
    if recipient_id:
        recipient = _profile_for_user(RecipientProfile, recipient_id, request.api_user)
        if recipient is None:
            return api_error("گیرنده فعال یا قابل دسترس یافت نشد.", status=404)
    try:
        top_n = min(50, max(1, int(request.data.get("top_n", 10))))
    except (TypeError, ValueError):
        return api_error("Top-N باید یک عدد معتبر باشد.")
    run = run_matching(
        trigger=MatchingRun.Trigger.MANUAL,
        initiated_by=request.api_user,
        top_n=top_n,
        recipient_id=recipient_id,
        donor_id=donor_id,
    )
    proposals = run.proposals.select_related(
        "recipient__person", "donor__person", "run"
    ).prefetch_related("recipient__person__cdc_pra_tests")
    return JsonResponse(
        {
            "message": "Matching با موفقیت اجرا شد.",
            "run": {"id": str(run.pk), "status": run.status, "statistics": run.statistics},
            "proposals": [serialize_proposal(proposal) for proposal in proposals],
        },
        status=201,
    )


@endpoint("POST", authenticated=True)
def matching_enqueue(request):
    """Publish a scoped matching job and return immediately."""
    recipient_id = request.data.get("recipient_id")
    donor_id = request.data.get("donor_id")
    if recipient_id and donor_id:
        return api_error("در هر درخواست فقط یک گیرنده یا یک اهداکننده قابل انتخاب است.")

    if recipient_id:
        recipient = _profile_for_user(RecipientProfile, recipient_id, request.api_user)
        if recipient is None:
            return api_error("گیرنده قابل دسترس یافت نشد.", status=404)
        if recipient.status != RecipientProfile.Status.ACTIVE:
            return api_error("سازگاری‌سنجی فقط برای گیرنده فعال در لیست انتظار قابل اجرا است.")
        task = match_recipient.delay(str(recipient.pk), request.api_user.pk, MatchingRun.Trigger.MANUAL)
        scope = "recipient"
    elif donor_id:
        donor = _profile_for_user(DonorProfile, donor_id, request.api_user)
        if donor is None:
            return api_error("اهداکننده قابل دسترس یافت نشد.", status=404)
        if donor.status not in {DonorProfile.Status.AVAILABLE, DonorProfile.Status.RESERVED}:
            return api_error("سازگاری‌سنجی فقط برای اهداکننده در دسترس یا رزروشده قابل اجرا است.")
        task = match_donor.delay(str(donor.pk), request.api_user.pk, MatchingRun.Trigger.MANUAL)
        scope = "donor"
    else:
        if not request.api_user.is_staff:
            return api_error("اجرای ملی سازگاری‌سنجی فقط برای مدیر ملی مجاز است.", status=403)
        task = match_national.delay(10, request.api_user.pk)
        scope = "national"

    return JsonResponse(
        {
            "message": "درخواست سازگاری‌سنجی در صف پردازش قرار گرفت.",
            "task": {"id": task.id, "scope": scope, "status": "queued"},
        },
        status=202,
    )


@endpoint("GET", authenticated=True)
def match_proposals(request):
    query = MatchProposal.objects.select_related(
        "run", "recipient__person", "donor__person"
    ).prefetch_related("recipient__person__cdc_pra_tests")
    if not request.api_user.is_staff:
        query = query.filter(recipient__person__center_id=request.api_user.center_id)
    recipient_id = request.GET.get("recipient_id")
    if recipient_id:
        query = query.filter(recipient_id=recipient_id)
    decision = request.GET.get("decision")
    if decision:
        query = query.filter(decision=decision)
    return JsonResponse({"proposals": [serialize_proposal(item) for item in query[:250]]})


@endpoint("GET", authenticated=True)
def donor_matches(request, person_id):
    donor = _profile_for_user(DonorProfile, person_id, request.api_user)
    if donor is None:
        return api_error("اهداکننده یافت نشد.", status=404)
    query = MatchProposal.objects.filter(donor=donor).select_related(
        "recipient__person", "recipient__person__center"
    ).order_by("-created_at", "rank", "-final_score")
    matches = []
    seen_recipients = set()
    for proposal in query:
        if proposal.recipient_id in seen_recipients:
            continue
        seen_recipients.add(proposal.recipient_id)
        recipient_person = proposal.recipient.person
        can_view = _can_access_person(request.api_user, recipient_person)
        matches.append(
            {
                "id": str(proposal.pk),
                "recipient": {
                    "anonymous_code": f"R-{str(proposal.recipient_id).split('-')[0].upper()}",
                    "id": str(recipient_person.pk) if can_view else None,
                    "full_name": recipient_person.full_name if can_view else None,
                    "blood_group": recipient_person.blood_group,
                    "center": recipient_person.center.name if recipient_person.center else None,
                    "can_view_profile": can_view,
                },
                "rank": proposal.rank,
                "compatibility": proposal.compatibility,
                "compatibility_display": proposal.get_compatibility_display(),
                "decision": proposal.decision,
                "decision_display": proposal.get_decision_display(),
                "final_score": float(proposal.final_score),
                "abo_compatible": proposal.abo_compatible,
                "anti_hla_status": proposal.anti_hla_status,
                "creg_summary": proposal.score_breakdown.get("creg_summary", {}),
                "hla_summary": proposal.hla_summary,
                "warnings": proposal.warnings,
                "rejection_reasons": proposal.rejection_reasons,
                "created_at": proposal.created_at.isoformat(),
            }
        )
        if len(matches) == 50:
            break
    return JsonResponse({"matches": matches})


@endpoint("GET", authenticated=True)
def patient_matches(request, person_id):
    recipient = _profile_for_user(RecipientProfile, person_id, request.api_user)
    if recipient is None:
        return api_error("گیرنده یافت نشد.", status=404)
    query = MatchProposal.objects.filter(
        recipient=recipient,
        compatibility__in=(MatchProposal.Compatibility.COMPATIBLE, MatchProposal.Compatibility.CONDITIONAL),
    ).exclude(decision__in=(MatchProposal.Decision.REJECTED, MatchProposal.Decision.CLOSED)).select_related(
        "donor__person"
    ).prefetch_related("crossmatch_requests").order_by("-created_at", "rank")
    unique = []
    seen_donors = set()
    for proposal in query:
        if proposal.donor_id in seen_donors:
            continue
        seen_donors.add(proposal.donor_id)
        unique.append(proposal)
        if len(unique) == 10:
            break
    return JsonResponse(
        {
            "recipient": {
                "id": str(recipient.pk),
                "status": recipient.status,
                "status_display": recipient.get_status_display(),
            },
            "matches": [serialize_proposal(item, patient_view=True) for item in unique],
            "disclaimer": "این فهرست پیشنهاد پزشکی قطعی نیست. ثبت درخواست فقط برای مشاوره است و Cross-Match پس از تأیید مرکز انجام می‌شود.",
        }
    )


@endpoint("POST", authenticated=True)
def request_consultation(request, proposal_id):
    proposal = MatchProposal.objects.select_related(
        "recipient__person", "donor__person"
    ).filter(pk=proposal_id).first()
    if proposal is None:
        return api_error("پیشنهاد تطبیق یافت نشد.", status=404)
    if not _can_access_person(request.api_user, proposal.recipient.person):
        return api_error("به این پیشنهاد دسترسی ندارید.", status=403)
    if proposal.decision != MatchProposal.Decision.PROPOSED:
        return api_error("این پیشنهاد دیگر در وضعیت قابل درخواست نیست.")
    try:
        item = CrossMatchRequest.objects.create(
            proposal=proposal,
            recipient=proposal.recipient,
            donor=proposal.donor,
            requested_by=request.api_user,
            patient_note=str(request.data.get("patient_note", "")).strip(),
        )
    except IntegrityError:
        return api_error("برای این پیشنهاد یک درخواست باز وجود دارد.", status=409)
    return JsonResponse(
        {"message": "درخواست مشاوره برای بررسی مرکز ثبت شد.", "crossmatch": serialize_crossmatch(item)},
        status=201,
    )


def _restore_pool_states(proposal, actor, reason):
    if proposal.recipient.status in {
        RecipientProfile.Status.MATCH_CANDIDATE,
        RecipientProfile.Status.AWAITING_CROSSMATCH,
        RecipientProfile.Status.AWAITING_HIGH_RESOLUTION,
        RecipientProfile.Status.READY,
    }:
        proposal.recipient = transition_profile(
            proposal.recipient, RecipientProfile.Status.ACTIVE, actor, reason
        )
    if proposal.donor.status in {
        DonorProfile.Status.MATCH_CANDIDATE,
        DonorProfile.Status.AWAITING_CROSSMATCH,
        DonorProfile.Status.READY,
    }:
        proposal.donor = transition_profile(
            proposal.donor, DonorProfile.Status.AVAILABLE, actor, reason
        )


@endpoint("PATCH", authenticated=True)
@transaction.atomic
def proposal_decision(request, proposal_id):
    proposal = MatchProposal.objects.select_for_update().select_related(
        "recipient__person", "donor__person"
    ).filter(pk=proposal_id).first()
    if proposal is None:
        return api_error("پیشنهاد تطبیق یافت نشد.", status=404)
    if not _can_access_person(request.api_user, proposal.recipient.person):
        return api_error("به این پیشنهاد دسترسی ندارید.", status=403)
    decision = request.data.get("decision")
    note = str(request.data.get("note", "")).strip()
    if decision not in {MatchProposal.Decision.APPROVED, MatchProposal.Decision.REJECTED}:
        return api_error("تصمیم باید تأیید یا رد باشد.")
    if not note:
        return api_error("ثبت یادداشت پزشک برای تصمیم الزامی است.")
    if proposal.decision != MatchProposal.Decision.PROPOSED:
        return api_error("برای این پیشنهاد قبلاً تصمیم ثبت شده است.")
    proposal.decision = decision
    proposal.center_note = note
    proposal.decided_by = request.api_user
    proposal.decided_at = timezone.now()
    proposal.save(update_fields=("decision", "center_note", "decided_by", "decided_at", "updated_at"))
    if decision == MatchProposal.Decision.APPROVED:
        recipient = transition_profile(
            proposal.recipient,
            RecipientProfile.Status.MATCH_CANDIDATE,
            request.api_user,
            "تأیید پیشنهاد Matching توسط مرکز",
            metadata={"proposal_id": str(proposal.pk)},
        )
        donor = transition_profile(
            proposal.donor,
            DonorProfile.Status.MATCH_CANDIDATE,
            request.api_user,
            "انتخاب به‌عنوان کاندیدای اهدا",
            metadata={"proposal_id": str(proposal.pk)},
        )
        recipient = transition_profile(
            recipient,
            RecipientProfile.Status.AWAITING_CROSSMATCH,
            request.api_user,
            "پیشنهاد Matching تأیید و Cross-Match فیزیکی درخواست شد",
            metadata={"proposal_id": str(proposal.pk)},
        )
        donor = transition_profile(
            donor,
            DonorProfile.Status.AWAITING_CROSSMATCH,
            request.api_user,
            "در انتظار Cross-Match با گیرنده منتخب",
            metadata={"proposal_id": str(proposal.pk)},
        )
        item = proposal.crossmatch_requests.filter(
            status__in=(
                CrossMatchRequest.Status.CONSULTATION_REQUESTED,
                CrossMatchRequest.Status.CENTER_REVIEW,
            )
        ).first()
        if item:
            item.status = CrossMatchRequest.Status.CENTER_REVIEW
            item.reviewed_by = request.api_user
            item.physician_note = note
            item.save(update_fields=("status", "reviewed_by", "physician_note", "updated_at"))
        else:
            CrossMatchRequest.objects.create(
                proposal=proposal,
                recipient=proposal.recipient,
                donor=proposal.donor,
                status=CrossMatchRequest.Status.CENTER_REVIEW,
                requested_by=request.api_user,
                reviewed_by=request.api_user,
                physician_note=note,
            )
    return JsonResponse({"message": "تصمیم مرکز ثبت شد.", "proposal": serialize_proposal(proposal)})


@endpoint("GET", authenticated=True)
def crossmatch_requests(request):
    query = CrossMatchRequest.objects.select_related(
        "proposal__run", "recipient__person", "donor__person", "requested_by", "reviewed_by"
    ).prefetch_related("recipient__person__cdc_pra_tests")
    if not request.api_user.is_staff:
        query = query.filter(recipient__person__center_id=request.api_user.center_id)
    status = request.GET.get("status")
    if status:
        query = query.filter(status=status)
    return JsonResponse({"crossmatches": [serialize_crossmatch(item) for item in query[:250]]})


@endpoint("PATCH", authenticated=True)
@transaction.atomic
def crossmatch_result(request, request_id):
    # Lock only the request row. PostgreSQL rejects FOR UPDATE against the
    # nullable side of the reviewed_by outer join.
    item = CrossMatchRequest.objects.select_for_update(of=("self",)).select_related(
        "proposal__run", "recipient__person", "donor__person", "requested_by", "reviewed_by"
    ).prefetch_related("recipient__person__cdc_pra_tests").filter(pk=request_id).first()
    if item is None:
        return api_error("درخواست Cross-Match یافت نشد.", status=404)
    if not _can_access_person(request.api_user, item.recipient.person):
        return api_error("به این درخواست دسترسی ندارید.", status=403)
    status = request.data.get("status")
    note = str(request.data.get("physician_note", "")).strip()
    if status not in {
        CrossMatchRequest.Status.SCHEDULED,
        CrossMatchRequest.Status.NEGATIVE,
        CrossMatchRequest.Status.POSITIVE,
        CrossMatchRequest.Status.CANCELLED,
    }:
        return api_error("وضعیت Cross-Match معتبر نیست.")
    if not note:
        return api_error("یادداشت پزشک الزامی است.")
    proposal = item.proposal
    if status == CrossMatchRequest.Status.SCHEDULED:
        if item.status not in {CrossMatchRequest.Status.CENTER_REVIEW, CrossMatchRequest.Status.CONSULTATION_REQUESTED}:
            return api_error("این درخواست قابل برنامه‌ریزی نیست.")
        if proposal.decision != MatchProposal.Decision.APPROVED:
            return api_error("پیشنهاد ابتدا باید توسط مرکز تأیید شود.")
        if item.donor.status == DonorProfile.Status.MATCH_CANDIDATE:
            item.donor = transition_profile(
                item.donor,
                DonorProfile.Status.AWAITING_CROSSMATCH,
                request.api_user,
                "Cross-Match برنامه‌ریزی شد",
            )
        item.scheduled_at = timezone.now()
    elif status in {CrossMatchRequest.Status.NEGATIVE, CrossMatchRequest.Status.POSITIVE}:
        allowed_result_states = {CrossMatchRequest.Status.SCHEDULED}
        if status == CrossMatchRequest.Status.NEGATIVE:
            allowed_result_states.add(CrossMatchRequest.Status.AWAITING_HIGH_RESOLUTION)
        if item.status not in allowed_result_states:
            return api_error("ثبت نتیجه فقط برای Cross-Match برنامه‌ریزی‌شده مجاز است.")
        if (
            status == CrossMatchRequest.Status.NEGATIVE
            and item.status == CrossMatchRequest.Status.SCHEDULED
            and proposal.compatibility == MatchProposal.Compatibility.CONDITIONAL
        ):
            transition_profile(
                item.recipient,
                RecipientProfile.Status.AWAITING_HIGH_RESOLUTION,
                request.api_user,
                "Cross-Match فیزیکی منفی؛ درخواست تایپ High-Resolution اهداکننده",
                metadata={"proposal_id": str(proposal.pk)},
            )
            item.status = CrossMatchRequest.Status.AWAITING_HIGH_RESOLUTION
            item.physician_note = note
            item.reviewed_by = request.api_user
            item.save(update_fields=("status", "physician_note", "reviewed_by", "updated_at"))
            return JsonResponse(
                {
                    "message": "نتیجه فیزیکی منفی ثبت شد؛ تکمیل تایپ High-Resolution اهداکننده الزامی است.",
                    "crossmatch": serialize_crossmatch(item),
                }
            )
        if (
            status == CrossMatchRequest.Status.NEGATIVE
            and item.status == CrossMatchRequest.Status.AWAITING_HIGH_RESOLUTION
        ):
            reevaluated = evaluate_pair(item.recipient, item.donor, check_state=False)
            resolution_warnings = [
                warning
                for warning in reevaluated["warnings"]
                if warning["code"] in {"resolution_mismatch", "incomplete_donor_resolution"}
            ]
            donor_is_high_resolution = all(
                ":" in conflict.get("donor", "")
                for warning in resolution_warnings
                for conflict in warning.get("conflicts", [])
            ) and not any(warning["code"] == "incomplete_donor_resolution" for warning in resolution_warnings)
            if (
                reevaluated["compatibility"] == MatchProposal.Compatibility.INCOMPATIBLE
                or not donor_is_high_resolution
            ):
                return api_error(
                    "تایپ High-Resolution اهداکننده کامل نشده یا هنوز mismatch ایمنی وجود دارد."
                )
            item.recipient = transition_profile(
                item.recipient,
                RecipientProfile.Status.AWAITING_CROSSMATCH,
                request.api_user,
                "تایپ High-Resolution تکمیل و بدون mismatch قطعی تأیید شد",
            )
        item.result_at = timezone.now()
        if status == CrossMatchRequest.Status.NEGATIVE:
            transition_profile(
                item.recipient, RecipientProfile.Status.READY, request.api_user, "نتیجه Cross-Match منفی"
            )
            transition_profile(
                item.donor, DonorProfile.Status.READY, request.api_user, "نتیجه Cross-Match منفی"
            )
            proposal.decision = MatchProposal.Decision.CROSSMATCH_NEGATIVE
        else:
            _restore_pool_states(proposal, request.api_user, "نتیجه Cross-Match مثبت؛ بازگشت به استخر")
            proposal.decision = MatchProposal.Decision.CROSSMATCH_POSITIVE
        proposal.save(update_fields=("decision", "updated_at"))
    else:
        _restore_pool_states(proposal, request.api_user, "لغو فرایند Cross-Match")
    item.status = status
    item.physician_note = note
    item.reviewed_by = request.api_user
    item.save(
        update_fields=(
            "status", "physician_note", "reviewed_by", "scheduled_at", "result_at", "updated_at"
        )
    )
    return JsonResponse({"message": "وضعیت Cross-Match ذخیره شد.", "crossmatch": serialize_crossmatch(item)})


def serialize_policy(policy):
    return {
        "id": policy.pk,
        "name": policy.name,
        "version": policy.version,
        "is_active": policy.is_active,
        "hla_weight": float(policy.hla_weight),
        "waiting_time_weight": float(policy.waiting_time_weight),
        "urgency_weight": float(policy.urgency_weight),
        "cpra_weight": float(policy.cpra_weight),
        "age_weight": float(policy.age_weight),
        "regional_weight": float(policy.regional_weight),
        "locus_weights": policy.locus_weights,
        "high_cpra_threshold": policy.high_cpra_threshold,
        "high_cpra_hla_discount": float(policy.high_cpra_hla_discount),
    }


@endpoint("GET", "PATCH", authenticated=True)
def allocation_policy(request):
    policy = active_policy()
    if request.method == "GET":
        return JsonResponse({"policy": serialize_policy(policy)})
    if not request.api_user.is_staff:
        return api_error("ویرایش ضرایب فقط برای مدیر ملی مجاز است.", status=403)
    editable = {
        "name", "hla_weight", "waiting_time_weight", "urgency_weight", "cpra_weight",
        "age_weight", "regional_weight", "locus_weights", "high_cpra_threshold",
        "high_cpra_hla_discount",
    }
    values = {field: request.data[field] for field in editable if field in request.data}
    policy_name = values.pop("name", policy.name)
    next_policy = AllocationPolicy(
        **values,
        name=policy_name,
        version=policy.version + 1,
        is_active=False,
        created_by=request.api_user,
    )
    try:
        next_policy.full_clean()
        with transaction.atomic():
            policy.is_active = False
            policy.save(update_fields=("is_active", "updated_at"))
            next_policy.is_active = True
            next_policy.save()
    except (ValidationError, IntegrityError) as exc:
        return _mutation_error(exc)
    return JsonResponse({"message": "نسخه جدید سیاست تخصیص فعال شد.", "policy": serialize_policy(next_policy)})


@endpoint("GET", authenticated=True)
def national_report(request):
    if not request.api_user.is_staff:
        return api_error("گزارش ملی فقط برای مدیر ملی قابل مشاهده است.", status=403)
    return JsonResponse(
        {
            "recipients_by_status": dict(
                RecipientProfile.objects.values_list("status").annotate(total=Count("pk"))
            ),
            "donors_by_status": dict(
                DonorProfile.objects.values_list("status").annotate(total=Count("pk"))
            ),
            "matches_by_compatibility": dict(
                MatchProposal.objects.values_list("compatibility").annotate(total=Count("pk"))
            ),
            "crossmatches_by_status": dict(
                CrossMatchRequest.objects.values_list("status").annotate(total=Count("pk"))
            ),
            "latest_run": (
                {
                    "id": str(run.pk),
                    "status": run.status,
                    "statistics": run.statistics,
                    "started_at": run.started_at.isoformat(),
                }
                if (run := MatchingRun.objects.first())
                else None
            ),
        }
    )


@endpoint("GET", "PATCH", authenticated=True)
def notifications(request):
    query = InAppNotification.objects.filter(user=request.api_user)
    if request.method == "PATCH":
        ids = request.data.get("ids") or []
        if not isinstance(ids, list):
            return api_error("شناسه اعلان‌ها باید فهرست باشد.")
        query.filter(pk__in=ids, read_at__isnull=True).update(read_at=timezone.now())
    items = [
        {
            "id": item.pk,
            "kind": item.kind,
            "title": item.title,
            "body": item.body,
            "metadata": item.metadata,
            "read_at": item.read_at.isoformat() if item.read_at else None,
            "created_at": item.created_at.isoformat(),
        }
        for item in query[:100]
    ]
    return JsonResponse({"notifications": items, "unread": query.filter(read_at__isnull=True).count()})


@endpoint("GET", authenticated=True)
def registry_options(request):
    return JsonResponse(
        {
            "hla": {str(locus): values for locus, values in HLA_VALUES_BY_LOCUS.items()},
            "anti_hla": {
                str(locus): values for locus, values in ANTI_HLA_VALUES_BY_LOCUS.items()
            },
            "approvals": dict(MedicalApproval.Specialty.choices),
            "approval_statuses": dict(MedicalApproval.Status.choices),
            "lab_categories": dict(LAB_CATEGORY_CHOICES),
            "routine_test_names": list(ROUTINE_TEST_NAMES),
            "viral_test_names": list(VIRAL_TEST_NAMES),
            "recipient_statuses": dict(RecipientProfile.Status.choices),
            "donor_statuses": dict(DonorProfile.Status.choices),
            "crossmatch_statuses": dict(CrossMatchRequest.Status.choices),
        }
    )
    InAppNotification,
    MatchProposal,
    MatchingRun,
