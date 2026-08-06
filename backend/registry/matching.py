from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .choices import HLAClass
from .creg import evaluate_creg
from .models import (
    AllocationPolicy,
    AntiHlaTest,
    CdcPraTest,
    DonorProfile,
    InAppNotification,
    MatchProposal,
    MatchingRun,
    RecipientProfile,
)


ABO_DONOR_TO_RECIPIENT = {
    "O": {"O", "A", "B", "AB"},
    "A": {"A", "AB"},
    "B": {"B", "AB"},
    "AB": {"AB"},
}
SCORED_LOCI = ("A", "B", "C", "DRB1", "DQB1")
CLASS_I_LOCI = {"A", "B", "C"}


def abo_group(value):
    return str(value or "").replace("+", "").replace("-", "").upper()


def abo_compatible(donor_blood_group, recipient_blood_group):
    donor = abo_group(donor_blood_group)
    recipient = abo_group(recipient_blood_group)
    return recipient in ABO_DONOR_TO_RECIPIENT.get(donor, set())


def low_resolution(allele):
    return str(allele or "").split(":", 1)[0].upper()


def active_policy():
    policy = AllocationPolicy.objects.filter(is_active=True).first()
    if policy is not None:
        return policy
    policy = AllocationPolicy(name="سیاست ملی پیش‌فرض", version=1, is_active=True)
    policy.full_clean()
    policy.save()
    return policy


def _latest_current(queryset, on_date):
    return queryset.filter(expires_at__gte=on_date).order_by("-performed_at", "-created_at").first()


def _latest_any(queryset):
    return queryset.order_by("-performed_at", "-created_at").first()


def _cpra(test):
    if test is None:
        return 0.0
    values = []
    for prefix in ("class_i", "class_ii"):
        if getattr(test, f"{prefix}_effective_status") == CdcPraTest.ResultStatus.POSITIVE:
            value = getattr(test, f"{prefix}_value")
            if value is not None:
                values.append(float(value))
    return max(values, default=0.0)


def _hla_by_locus(person):
    result = defaultdict(Counter)
    try:
        selections = person.hla_typing.selections.all()
    except AttributeError:
        return result
    for selection in selections:
        result[selection.locus][selection.allele] += selection.copy_number
    return result


def _reason(code, message, **details):
    return {"code": code, "message": message, **details}


def _anti_hla_evaluation(anti_test, donor_hla):
    exact = []
    conditional = []
    missing_loci = []
    selections = list(anti_test.selections.all())
    for selection in selections:
        donor_alleles = donor_hla.get(selection.locus, Counter())
        if not donor_alleles:
            missing_loci.append(selection.locus)
            continue
        for allele in donor_alleles:
            if allele.upper() == selection.antigen.upper():
                exact.append(
                    {"locus": selection.locus, "antibody": selection.antigen, "donor": allele}
                )
            elif low_resolution(allele) == low_resolution(selection.antigen):
                conditional.append(
                    {"locus": selection.locus, "antibody": selection.antigen, "donor": allele}
                )
    if exact:
        return "mismatch", exact, conditional, sorted(set(missing_loci))
    if conditional or missing_loci:
        return "conditional", exact, conditional, sorted(set(missing_loci))
    return "clear", exact, conditional, []


def _self_hla_antibody_lows(recipient_hla, anti_test):
    """Return antibodies whose low-resolution antigen is also the recipient's own HLA."""
    recipient_low = {
        (locus, low_resolution(allele))
        for locus, alleles in recipient_hla.items()
        for allele in alleles
    }
    return {
        (selection.locus, low_resolution(selection.antigen))
        for selection in anti_test.selections.all()
        if (selection.locus, low_resolution(selection.antigen)) in recipient_low
    }


def _hla_similarity(recipient_hla, donor_hla, policy):
    loci = {}
    weighted_matches = 0.0
    weighted_max = 0.0
    class_i = 0
    class_ii = 0
    for locus in SCORED_LOCI:
        recipient = recipient_hla.get(locus, Counter())
        donor = donor_hla.get(locus, Counter())
        recipient_low = Counter()
        donor_low = Counter()
        for allele, copies in recipient.items():
            recipient_low[low_resolution(allele)] += copies
        for allele, copies in donor.items():
            donor_low[low_resolution(allele)] += copies
        common_counter = recipient_low & donor_low
        matches = sum(common_counter.values())
        common = []
        for allele, copies in sorted(common_counter.items()):
            common.extend([allele] * copies)
        weight = float(policy.locus_weights.get(locus, 1))
        weighted_matches += matches * weight
        weighted_max += 2 * weight
        if locus in CLASS_I_LOCI:
            class_i += matches
        else:
            class_ii += matches
        loci[locus] = {
            "matches": matches,
            "maximum": 2,
            "common": common,
            "secondary": locus == "C",
            "recipient": list(recipient.elements()),
            "donor": list(donor.elements()),
        }
    percent = (weighted_matches / weighted_max * 100) if weighted_max else 0
    return {
        "loci": loci,
        "class_i_matches": class_i,
        "class_ii_matches": class_ii,
        "total_matches": class_i + class_ii,
        "weighted_matches": round(weighted_matches, 3),
        "weighted_maximum": round(weighted_max, 3),
        "percent": round(percent, 3),
    }


def _age_on(birth_date, today):
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def _score(recipient, hla, cpra, policy, today):
    waiting_days = max(0, (today - (recipient.waiting_since or today)).days)
    waiting = min(100.0, waiting_days / (365 * 5) * 100)
    age = _age_on(recipient.person.birth_date, today)
    age_priority = max(0.0, min(100.0, (65 - age) / 47 * 100))
    sensitization = max(0.0, min(100.0, cpra))
    threshold = max(1, policy.high_cpra_threshold)
    discount = float(policy.high_cpra_hla_discount) * min(1, sensitization / threshold)
    adaptive_hla = 100 - ((100 - hla["percent"]) * (1 - discount))
    components = {
        "hla_raw": round(hla["percent"], 3),
        "hla_adaptive": round(adaptive_hla, 3),
        "waiting_time": round(waiting, 3),
        "waiting_days": waiting_days,
        "medical_urgency": recipient.medical_urgency,
        "cpra_difficulty": round(sensitization, 3),
        "age_priority": round(age_priority, 3),
        "regional_disadvantage": recipient.regional_disadvantage,
        "adaptive_discount": round(discount, 3),
        "policy_version": policy.version,
    }
    final = (
        adaptive_hla * float(policy.hla_weight)
        + waiting * float(policy.waiting_time_weight)
        + recipient.medical_urgency * float(policy.urgency_weight)
        + sensitization * float(policy.cpra_weight)
        + age_priority * float(policy.age_weight)
        + recipient.regional_disadvantage * float(policy.regional_weight)
    )
    return round(final, 4), components


def evaluate_pair(recipient, donor, *, policy=None, on_date=None, check_state=True):
    policy = policy or active_policy()
    today = on_date or timezone.localdate()
    reasons = []
    warnings = []

    if check_state and recipient.status != RecipientProfile.Status.ACTIVE:
        reasons.append(
            _reason("recipient_not_active", "گیرنده در وضعیت «فعال در لیست انتظار» نیست.")
        )
    donor_allowed = donor.status in {DonorProfile.Status.AVAILABLE, DonorProfile.Status.RESERVED}
    if check_state and not donor_allowed:
        reasons.append(_reason("donor_not_available", "اهداکننده در استخر Matching در دسترس نیست."))
    if donor.preferred_recipient_id and donor.preferred_recipient_id != recipient.pk:
        reasons.append(
            _reason(
                "donor_reserved_for_other_recipient",
                "این اهداکننده برای گیرنده دیگری رزرو شده است.",
            )
        )
    citizenship_compatible = donor.person.citizenship == recipient.person.citizenship
    if not citizenship_compatible:
        reasons.append(
            _reason(
                "citizenship_incompatible",
                "طبق سیاست تخصیص، اهداکننده ایرانی فقط با گیرنده ایرانی و اهداکننده غیرایرانی فقط با گیرنده غیرایرانی بررسی می‌شود.",
                donor_citizenship=donor.person.citizenship,
                recipient_citizenship=recipient.person.citizenship,
            )
        )

    abo_ok = abo_compatible(donor.person.blood_group, recipient.person.blood_group)
    if not abo_ok:
        reasons.append(
            _reason(
                "abo_incompatible",
                f"گروه خونی {donor.person.blood_group} نمی‌تواند به {recipient.person.blood_group} اهدا کند؛ Rh در این تصمیم لحاظ نشده است.",
            )
        )

    current_anti = _latest_current(recipient.person.anti_hla_tests, today)
    latest_anti = current_anti or _latest_any(recipient.person.anti_hla_tests)
    if current_anti is None:
        message = (
            "آزمایش Anti-HLA گیرنده منقضی شده است."
            if latest_anti
            else "آزمایش Anti-HLA معتبر برای گیرنده ثبت نشده است."
        )
        reasons.append(_reason("anti_hla_not_current", message))

    current_cdc = _latest_current(recipient.person.cdc_pra_tests, today)
    latest_cdc = current_cdc or _latest_any(recipient.person.cdc_pra_tests)
    if current_cdc is None:
        message = (
            "آزمایش CDC-PRA گیرنده منقضی شده است."
            if latest_cdc
            else "آزمایش CDC-PRA معتبر برای گیرنده ثبت نشده است."
        )
        reasons.append(_reason("cdc_pra_not_current", message))

    recipient_hla = _hla_by_locus(recipient.person)
    donor_hla = _hla_by_locus(donor.person)
    if not donor_hla:
        reasons.append(
            _reason("donor_hla_missing", "تایپ HLA اهداکننده ثبت نشده و فیلتر ایمنی قابل اجرا نیست.")
        )

    anti_status = "not_evaluated"
    creg_summary = {
        "has_antibody": False,
        "antibody_antigens": [],
        "active_groups": [],
        "donor_antigens": [],
        "potential_conflicts": [],
        "has_potential_conflict": False,
    }
    if current_anti is not None and donor_hla:
        anti_status, exact, conditional, missing_loci = _anti_hla_evaluation(
            current_anti, donor_hla
        )
        self_overlap_lows = _self_hla_antibody_lows(recipient_hla, current_anti)
        self_overlap_conflicts = [
            conflict
            for conflict in [*exact, *conditional]
            if (conflict["locus"], low_resolution(conflict["antibody"])) in self_overlap_lows
        ]
        exact = [
            conflict
            for conflict in exact
            if (conflict["locus"], low_resolution(conflict["antibody"])) not in self_overlap_lows
        ]
        conditional = [
            conflict
            for conflict in conditional
            if (conflict["locus"], low_resolution(conflict["antibody"])) not in self_overlap_lows
        ]
        if exact:
            reasons.append(
                _reason(
                    "anti_hla_mismatch",
                    "آنتی‌ژن اهداکننده در فهرست Anti-HLA گیرنده وجود دارد.",
                    conflicts=exact,
                )
            )
        if self_overlap_conflicts:
            warnings.append(
                _reason(
                    "self_hla_anti_hla_overlap",
                    "آنتی‌ژن هم‌زمان در HLA و Anti-HLA گیرنده ثبت شده است؛ نتیجه مشروط به بازبینی آزمایشگاه، تایپ High-Resolution و Cross-Match فیزیکی است.",
                    conflicts=self_overlap_conflicts,
                )
            )
            if not exact:
                anti_status = "conditional"
        if conditional:
            warnings.append(
                _reason(
                    "resolution_mismatch",
                    "تطابق در سطح low-resolution دیده شد؛ Cross-Match فیزیکی و تایپ high-resolution الزامی است.",
                    conflicts=conditional,
                )
            )
        if missing_loci:
            warnings.append(
                _reason(
                    "incomplete_donor_resolution",
                    "برای رد قطعی واکنش آنتی‌بادی، تکمیل تایپ HLA اهداکننده لازم است.",
                    loci=missing_loci,
                )
            )
        creg_summary = evaluate_creg(
            (selection.antigen for selection in current_anti.selections.all()),
            (
                allele
                for locus in CLASS_I_LOCI
                for allele in donor_hla.get(locus, Counter()).elements()
            ),
        )
        if creg_summary["has_potential_conflict"]:
            warnings.append(
                _reason(
                    "creg_potential_conflict",
                    "یک یا چند آنتی‌ژن اهداکننده در CREG مرتبط با Anti-HLA گیرنده قرار دارد؛ بررسی آزمایشگاه و Cross-Match الزامی است.",
                    conflicts=creg_summary["potential_conflicts"],
                    groups=creg_summary["active_groups"],
                )
            )
            if anti_status == "clear":
                anti_status = "conditional"

    hla = _hla_similarity(recipient_hla, donor_hla, policy)
    if not recipient_hla:
        warnings.append(_reason("recipient_hla_missing", "HLA گیرنده ثبت نشده و امتیاز شباهت صفر است."))
    cpra = _cpra(current_cdc)
    score, breakdown = _score(recipient, hla, cpra, policy, today)
    breakdown["creg_summary"] = creg_summary

    compatibility = MatchProposal.Compatibility.INCOMPATIBLE
    if not reasons:
        compatibility = (
            MatchProposal.Compatibility.CONDITIONAL
            if anti_status == "conditional"
            else MatchProposal.Compatibility.COMPATIBLE
        )
    return {
        "compatibility": compatibility,
        "abo_compatible": abo_ok,
        "citizenship_compatible": citizenship_compatible,
        "anti_hla_status": anti_status,
        "creg_summary": creg_summary,
        "self_hla_anti_hla_overlap": any(
            warning["code"] == "self_hla_anti_hla_overlap" for warning in warnings
        ),
        "hla_summary": hla,
        "final_score": score,
        "score_breakdown": breakdown,
        "rejection_reasons": reasons,
        "warnings": warnings,
        "tests": {
            "anti_hla": (
                {
                    "id": str(current_anti.pk),
                    "performed_at": current_anti.performed_at.isoformat(),
                    "expires_at": current_anti.expires_at.isoformat(),
                }
                if current_anti
                else None
            ),
            "cdc_pra": (
                {
                    "id": str(current_cdc.pk),
                    "performed_at": current_cdc.performed_at.isoformat(),
                    "expires_at": current_cdc.expires_at.isoformat(),
                    "cpra": cpra,
                }
                if current_cdc
                else None
            ),
        },
    }


def matching_queryset_recipient(recipient_id=None):
    query = RecipientProfile.objects.filter(status=RecipientProfile.Status.ACTIVE)
    if recipient_id:
        query = query.filter(pk=recipient_id)
    return query.select_related("person", "person__hla_typing").prefetch_related(
        "person__hla_typing__selections",
        "person__anti_hla_tests__selections",
        "person__cdc_pra_tests",
    )


def matching_queryset_donor(donor_id=None):
    query = DonorProfile.objects.filter(
        status__in=(DonorProfile.Status.AVAILABLE, DonorProfile.Status.RESERVED)
    )
    if donor_id:
        query = query.filter(pk=donor_id)
    return query.select_related("person", "person__hla_typing", "preferred_recipient").prefetch_related(
        "person__hla_typing__selections"
    )


class _TemporarySelections:
    def __init__(self, selections):
        self._selections = selections

    def all(self):
        return self._selections


def rank_deceased_donor(*, citizenship, blood_group, hla_by_locus, top_n=25):
    """Rank a bounded, prefiltered candidate window for a deceased donor."""
    allowed_abo = ABO_DONOR_TO_RECIPIENT.get(abo_group(blood_group), set())
    allowed_blood_groups = [f"{group}{rh}" for group in allowed_abo for rh in ("+", "-")]
    candidate_limit = int(getattr(settings, "DECEASED_MATCH_CANDIDATE_LIMIT", 5000))
    query = (
        matching_queryset_recipient()
        .filter(
            donor_deceased=True,
            person__citizenship=citizenship,
            person__blood_group__in=allowed_blood_groups,
        )
        .order_by("-medical_urgency", "waiting_since")[:candidate_limit]
    )
    selections = [
        SimpleNamespace(locus=locus, allele=allele, copy_number=1)
        for locus, alleles in hla_by_locus.items()
        for allele in alleles
    ]
    donor = SimpleNamespace(
        status=DonorProfile.Status.AVAILABLE,
        preferred_recipient_id=None,
        person=SimpleNamespace(
            citizenship=citizenship,
            blood_group=blood_group,
            hla_typing=SimpleNamespace(selections=_TemporarySelections(selections)),
        ),
    )
    policy = active_policy()
    ranked = []
    rejected = 0
    for recipient in query:
        result = evaluate_pair(recipient, donor, policy=policy)
        if result["compatibility"] == MatchProposal.Compatibility.INCOMPATIBLE:
            rejected += 1
            continue
        ranked.append((recipient, result))
    ranked.sort(key=lambda item: item[1]["final_score"], reverse=True)
    return {
        "items": ranked[:top_n],
        "evaluated_candidates": len(ranked) + rejected,
        "rejected_candidates": rejected,
        "candidate_limit": candidate_limit,
        "policy": policy,
    }


@transaction.atomic
def run_matching(*, trigger=MatchingRun.Trigger.MANUAL, initiated_by=None, top_n=10, recipient_id=None, donor_id=None):
    policy = active_policy()
    run = MatchingRun.objects.create(trigger=trigger, policy=policy, initiated_by=initiated_by)
    recipients = list(matching_queryset_recipient(recipient_id))
    donors = list(matching_queryset_donor(donor_id))
    proposal_rows = []
    evaluated = rejected = conditional = 0
    rejection_reason_counts = Counter()
    try:
        for recipient in recipients:
            compatible = []
            for donor in donors:
                evaluated += 1
                result = evaluate_pair(recipient, donor, policy=policy)
                if result["compatibility"] == MatchProposal.Compatibility.INCOMPATIBLE:
                    rejected += 1
                    rejection_reason_counts.update(
                        reason["code"] for reason in result["rejection_reasons"]
                    )
                    continue
                conditional += result["compatibility"] == MatchProposal.Compatibility.CONDITIONAL
                compatible.append((donor, result))
            compatible.sort(key=lambda item: item[1]["final_score"], reverse=True)
            for rank, (donor, result) in enumerate(compatible[:top_n], start=1):
                proposal_rows.append(
                    MatchProposal(
                        run=run,
                        recipient=recipient,
                        donor=donor,
                        rank=rank,
                        compatibility=result["compatibility"],
                        final_score=Decimal(str(result["final_score"])),
                        abo_compatible=result["abo_compatible"],
                        anti_hla_status=result["anti_hla_status"],
                        hla_summary=result["hla_summary"],
                        score_breakdown=result["score_breakdown"],
                        rejection_reasons=result["rejection_reasons"],
                        warnings=result["warnings"],
                    )
                )
        MatchProposal.objects.bulk_create(proposal_rows)
        run.status = MatchingRun.Status.COMPLETED
        run.finished_at = timezone.now()
        run.statistics = {
            "recipients": len(recipients),
            "donors": len(donors),
            "evaluated_pairs": evaluated,
            "rejected_pairs": rejected,
            "conditional_pairs": conditional,
            "proposals": len(proposal_rows),
            "top_n": top_n,
            "rejection_reasons": dict(rejection_reason_counts),
        }
        run.save(update_fields=("status", "finished_at", "statistics"))
    except Exception as exc:
        run.status = MatchingRun.Status.FAILED
        run.error = str(exc)
        run.finished_at = timezone.now()
        run.save(update_fields=("status", "error", "finished_at"))
        raise

    user_model = get_user_model()
    notifications = []
    for proposal in MatchProposal.objects.filter(run=run).select_related("recipient__person"):
        for user in user_model.objects.filter(
            center_id=proposal.recipient.person.center_id,
            is_active=True,
            notify_in_app_match=True,
        ):
            notifications.append(
                InAppNotification(
                    user=user,
                    kind=InAppNotification.Kind.NEW_MATCH,
                    title="پیشنهاد تطبیق جدید",
                    body=f"یک اهداکننده رتبه {proposal.rank} برای {proposal.recipient.person.full_name} شناسایی شد.",
                    metadata={"proposal_id": str(proposal.pk), "run_id": str(run.pk)},
                    dedupe_key=f"match:{proposal.pk}:{user.pk}",
                )
            )
    InAppNotification.objects.bulk_create(notifications, ignore_conflicts=True)
    return run
