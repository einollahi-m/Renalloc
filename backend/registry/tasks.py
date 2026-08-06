from celery import shared_task
from django.core.management import call_command
from django.db import OperationalError

from users.models import User

from .matching import run_matching
from .models import DonorProfile, MatchingRun, RecipientProfile


TASK_RETRY_OPTIONS = {
    "autoretry_for": (OperationalError,),
    "retry_backoff": True,
    "retry_backoff_max": 600,
    "retry_jitter": True,
    "max_retries": 5,
    "acks_late": True,
}


def _user(user_id):
    return User.objects.filter(pk=user_id, is_active=True).first() if user_id else None


@shared_task(name="registry.match_recipient", **TASK_RETRY_OPTIONS)
def match_recipient(recipient_id, initiated_by_id=None, trigger=MatchingRun.Trigger.MANUAL):
    if not RecipientProfile.objects.filter(
        pk=recipient_id, status=RecipientProfile.Status.ACTIVE
    ).exists():
        return {"skipped": True, "reason": "recipient_not_active"}
    run = run_matching(
        trigger=trigger,
        initiated_by=_user(initiated_by_id),
        recipient_id=recipient_id,
    )
    return {"run_id": str(run.pk), "statistics": run.statistics}


@shared_task(name="registry.match_donor", **TASK_RETRY_OPTIONS)
def match_donor(donor_id, initiated_by_id=None, trigger=MatchingRun.Trigger.DONOR_CREATED):
    if not DonorProfile.objects.filter(
        pk=donor_id,
        status__in=(DonorProfile.Status.AVAILABLE, DonorProfile.Status.RESERVED),
    ).exists():
        return {"skipped": True, "reason": "donor_not_available"}
    run = run_matching(
        trigger=trigger,
        initiated_by=_user(initiated_by_id),
        donor_id=donor_id,
    )
    return {"run_id": str(run.pk), "statistics": run.statistics}


@shared_task(name="registry.match_national", **TASK_RETRY_OPTIONS)
def match_national(top_n=10, initiated_by_id=None):
    run = run_matching(
        trigger=MatchingRun.Trigger.NIGHTLY,
        initiated_by=_user(initiated_by_id),
        top_n=top_n,
    )
    return {"run_id": str(run.pk), "statistics": run.statistics}


@shared_task(name="registry.check_test_expiry", **TASK_RETRY_OPTIONS)
def check_test_expiry(days=14):
    call_command("check_expiring_tests", days=days)
    return {"days": days, "completed": True}

