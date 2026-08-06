from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from registry.models import InAppNotification, RecipientProfile
from registry.workflows import transition_profile


class Command(BaseCommand):
    help = "ایجاد هشدار آزمایش‌های ایمنی نزدیک انقضا و تعلیق گیرندگان فاقد آزمایش معتبر"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=14)

    def handle(self, *args, **options):
        days = options["days"]
        if not 0 <= days <= 180:
            raise CommandError("days باید بین صفر و ۱۸۰ باشد.")
        today = timezone.localdate()
        deadline = today + timedelta(days=days)
        notified = suspended = 0
        users = get_user_model().objects.filter(is_active=True)
        recipients = RecipientProfile.objects.select_related("person").prefetch_related(
            "person__anti_hla_tests", "person__cdc_pra_tests"
        )
        for recipient in recipients:
            current = {}
            for key, manager in (
                ("Anti-HLA", recipient.person.anti_hla_tests),
                ("CDC-PRA", recipient.person.cdc_pra_tests),
            ):
                latest = manager.order_by("-performed_at", "-created_at").first()
                current[key] = latest
                if latest and today <= latest.expires_at <= deadline:
                    for user in users.filter(center_id=recipient.person.center_id):
                        _, created = InAppNotification.objects.get_or_create(
                            user=user,
                            dedupe_key=f"expiry:{key}:{latest.pk}:{latest.expires_at}",
                            defaults={
                                "kind": InAppNotification.Kind.TEST_EXPIRY,
                                "title": f"نزدیک شدن انقضای {key}",
                                "body": (
                                    f"آزمایش {key} بیمار {recipient.person.full_name} در "
                                    f"{latest.expires_at.isoformat()} منقضی می‌شود."
                                ),
                                "metadata": {
                                    "person_id": str(recipient.pk),
                                    "test_id": str(latest.pk),
                                    "expires_at": latest.expires_at.isoformat(),
                                },
                            },
                        )
                        notified += created
            invalid = any(test is None or test.expires_at < today for test in current.values())
            if invalid and recipient.status == RecipientProfile.Status.ACTIVE:
                transition_profile(
                    recipient,
                    RecipientProfile.Status.TEMPORARILY_INACTIVE,
                    None,
                    "تعلیق خودکار به‌دلیل نبود آزمایش Anti-HLA یا CDC-PRA معتبر",
                    metadata={"automated": True},
                )
                suspended += 1
        self.stdout.write(
            self.style.SUCCESS(f"notifications={notified}, suspended={suspended}")
        )

