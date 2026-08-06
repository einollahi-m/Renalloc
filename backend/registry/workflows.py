from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    ClinicalStateEvent,
    CrossMatchRequest,
    DonorProfile,
    InAppNotification,
    MatchProposal,
    RecipientProfile,
)


RECIPIENT_TRANSITIONS = {
    RecipientProfile.Status.REGISTERED: {
        RecipientProfile.Status.PENDING_DOCUMENTS,
        RecipientProfile.Status.REMOVED,
    },
    RecipientProfile.Status.PENDING_DOCUMENTS: {
        RecipientProfile.Status.ACTIVE,
        RecipientProfile.Status.REJECTED,
        RecipientProfile.Status.TEMPORARILY_INACTIVE,
        RecipientProfile.Status.REMOVED,
    },
    RecipientProfile.Status.REJECTED: {RecipientProfile.Status.PENDING_DOCUMENTS},
    RecipientProfile.Status.ACTIVE: {
        RecipientProfile.Status.MATCH_CANDIDATE,
        RecipientProfile.Status.TEMPORARILY_INACTIVE,
        RecipientProfile.Status.REMOVED,
    },
    RecipientProfile.Status.MATCH_CANDIDATE: {
        RecipientProfile.Status.AWAITING_CROSSMATCH,
        RecipientProfile.Status.AWAITING_HIGH_RESOLUTION,
        RecipientProfile.Status.ACTIVE,
        RecipientProfile.Status.TEMPORARILY_INACTIVE,
    },
    RecipientProfile.Status.AWAITING_HIGH_RESOLUTION: {
        RecipientProfile.Status.MATCH_CANDIDATE,
        RecipientProfile.Status.AWAITING_CROSSMATCH,
        RecipientProfile.Status.ACTIVE,
    },
    RecipientProfile.Status.AWAITING_CROSSMATCH: {
        RecipientProfile.Status.READY,
        RecipientProfile.Status.ACTIVE,
        RecipientProfile.Status.AWAITING_HIGH_RESOLUTION,
    },
    RecipientProfile.Status.READY: {
        RecipientProfile.Status.TRANSPLANTED,
        RecipientProfile.Status.ACTIVE,
    },
    RecipientProfile.Status.TRANSPLANTED: {RecipientProfile.Status.FOLLOW_UP},
    RecipientProfile.Status.FOLLOW_UP: set(),
    RecipientProfile.Status.TEMPORARILY_INACTIVE: {
        RecipientProfile.Status.ACTIVE,
        RecipientProfile.Status.REMOVED,
    },
    RecipientProfile.Status.REMOVED: set(),
}

DONOR_TRANSITIONS = {
    DonorProfile.Status.REGISTERED: {
        DonorProfile.Status.MEDICAL_SCREENING,
        DonorProfile.Status.PERMANENT_DEFERRAL,
    },
    DonorProfile.Status.MEDICAL_SCREENING: {
        DonorProfile.Status.AVAILABLE,
        DonorProfile.Status.SUSPENDED,
        DonorProfile.Status.RESERVED,
        DonorProfile.Status.PERMANENT_DEFERRAL,
    },
    DonorProfile.Status.AVAILABLE: {
        DonorProfile.Status.MATCH_CANDIDATE,
        DonorProfile.Status.RESERVED,
        DonorProfile.Status.SUSPENDED,
        DonorProfile.Status.PERMANENT_DEFERRAL,
    },
    DonorProfile.Status.MATCH_CANDIDATE: {
        DonorProfile.Status.AWAITING_CROSSMATCH,
        DonorProfile.Status.AVAILABLE,
        DonorProfile.Status.SUSPENDED,
    },
    DonorProfile.Status.AWAITING_CROSSMATCH: {
        DonorProfile.Status.READY,
        DonorProfile.Status.AVAILABLE,
        DonorProfile.Status.SUSPENDED,
    },
    DonorProfile.Status.READY: {
        DonorProfile.Status.DONATED,
        DonorProfile.Status.AVAILABLE,
    },
    DonorProfile.Status.DONATED: {DonorProfile.Status.FOLLOW_UP},
    DonorProfile.Status.FOLLOW_UP: set(),
    DonorProfile.Status.RESERVED: {
        DonorProfile.Status.MATCH_CANDIDATE,
        DonorProfile.Status.AVAILABLE,
        DonorProfile.Status.SUSPENDED,
    },
    DonorProfile.Status.SUSPENDED: {
        DonorProfile.Status.MEDICAL_SCREENING,
        DonorProfile.Status.AVAILABLE,
        DonorProfile.Status.PERMANENT_DEFERRAL,
    },
    DonorProfile.Status.PERMANENT_DEFERRAL: set(),
}


def allowed_transitions(profile):
    transitions = (
        RECIPIENT_TRANSITIONS if isinstance(profile, RecipientProfile) else DONOR_TRANSITIONS
    )
    return sorted(transitions.get(profile.status, set()))


def _center_users(profile):
    center_id = profile.person.center_id
    if center_id is None:
        return get_user_model().objects.none()
    return get_user_model().objects.filter(center_id=center_id, is_active=True)


def _state_event(profile, previous_status, new_status, reason, actor, metadata=None):
    is_recipient = isinstance(profile, RecipientProfile)
    event = ClinicalStateEvent.objects.create(
        entity_type=(
            ClinicalStateEvent.EntityType.RECIPIENT
            if is_recipient
            else ClinicalStateEvent.EntityType.DONOR
        ),
        recipient=profile if is_recipient else None,
        donor=None if is_recipient else profile,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        actor=actor,
        metadata=metadata or {},
    )
    label = profile.get_status_display()
    entity_label = "گیرنده" if is_recipient else "اهداکننده"
    notifications = [
        InAppNotification(
            user=user,
            kind=InAppNotification.Kind.STATE_CHANGED,
            title=f"تغییر وضعیت {entity_label}",
            body=f"وضعیت پرونده {profile.person.full_name} به «{label}» تغییر کرد.",
            metadata={"event_id": str(event.pk), "person_id": str(profile.person_id)},
            dedupe_key=f"state:{event.pk}:{user.pk}",
        )
        for user in _center_users(profile)
        if user.pk != getattr(actor, "pk", None)
    ]
    InAppNotification.objects.bulk_create(notifications)
    return event


def record_initial_state(profile, actor):
    return _state_event(
        profile,
        "",
        profile.status,
        "ایجاد پرونده در سامانه",
        actor,
        {"initial": True},
    )


def record_priority_update(profile, actor, previous, current):
    return _state_event(
        profile,
        profile.status,
        profile.status,
        "ویرایش اولویت و شرایط اورژانسی گیرنده",
        actor,
        {"kind": "priority_update", "previous": previous, "current": current},
    )


@transaction.atomic
def transition_profile(profile, new_status, actor, reason, *, metadata=None):
    if not str(reason or "").strip():
        raise ValidationError({"reason": "دلیل تغییر وضعیت الزامی است."})
    model = profile.__class__
    locked = model.objects.select_for_update().select_related("person").get(pk=profile.pk)
    valid_statuses = set(model.Status.values)
    if new_status not in valid_statuses:
        raise ValidationError({"status": "وضعیت انتخاب‌شده معتبر نیست."})
    if new_status == locked.status:
        raise ValidationError({"status": "وضعیت جدید با وضعیت فعلی یکسان است."})
    if new_status not in allowed_transitions(locked):
        raise ValidationError(
            {"status": f"گذار از «{locked.get_status_display()}» به وضعیت درخواستی مجاز نیست."}
        )
    previous_status = locked.status
    locked.status = new_status
    update_fields = ["status", "updated_at"]
    if (
        isinstance(locked, RecipientProfile)
        and new_status == RecipientProfile.Status.ACTIVE
        and locked.waiting_since is None
    ):
        locked.waiting_since = timezone.localdate()
        update_fields.append("waiting_since")
    locked.full_clean()
    locked.save(update_fields=update_fields)
    _state_event(locked, previous_status, new_status, str(reason).strip(), actor, metadata)
    leaves_matching_pool = (
        isinstance(locked, RecipientProfile)
        and new_status in {
            RecipientProfile.Status.TEMPORARILY_INACTIVE,
            RecipientProfile.Status.REMOVED,
            RecipientProfile.Status.REJECTED,
        }
    ) or (
        isinstance(locked, DonorProfile)
        and new_status in {
            DonorProfile.Status.SUSPENDED,
            DonorProfile.Status.PERMANENT_DEFERRAL,
        }
    )
    if leaves_matching_pool:
        proposal_filter = (
            {"recipient": locked}
            if isinstance(locked, RecipientProfile)
            else {"donor": locked}
        )
        open_proposals = MatchProposal.objects.filter(
            **proposal_filter,
            decision__in={
                MatchProposal.Decision.PROPOSED,
                MatchProposal.Decision.APPROVED,
            },
        )
        CrossMatchRequest.objects.filter(
            proposal__in=open_proposals,
            status__in={
                CrossMatchRequest.Status.CONSULTATION_REQUESTED,
                CrossMatchRequest.Status.CENTER_REVIEW,
                CrossMatchRequest.Status.SCHEDULED,
                CrossMatchRequest.Status.AWAITING_HIGH_RESOLUTION,
            },
        ).update(
            status=CrossMatchRequest.Status.CANCELLED,
            physician_note="لغو خودکار پس از خروج پرونده از لیست انتظار",
            updated_at=timezone.now(),
        )
        open_proposals.update(
            decision=MatchProposal.Decision.CLOSED,
            center_note="بسته‌شدن خودکار پس از خروج پرونده از لیست انتظار",
            updated_at=timezone.now(),
        )
    if (
        isinstance(locked, RecipientProfile)
        and new_status == RecipientProfile.Status.ACTIVE
    ):
        from .tasks import match_recipient

        match_recipient.delay_on_commit(
            str(locked.pk),
            getattr(actor, "pk", None),
            "manual",
        )
    elif (
        isinstance(locked, DonorProfile)
        and new_status == DonorProfile.Status.AVAILABLE
    ):
        from .tasks import match_donor

        match_donor.delay_on_commit(
            str(locked.pk),
            getattr(actor, "pk", None),
            "donor_created",
        )
    return locked
