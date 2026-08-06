from django.core.management.base import BaseCommand, CommandError

from registry.matching import run_matching
from registry.models import MatchingRun


class Command(BaseCommand):
    help = "اجرای Batch موتور ملی Matching و ذخیره Top-N پیشنهادها"

    def add_arguments(self, parser):
        parser.add_argument("--top-n", type=int, default=10)
        parser.add_argument("--recipient", dest="recipient_id")
        parser.add_argument("--donor", dest="donor_id")

    def handle(self, *args, **options):
        top_n = options["top_n"]
        if not 1 <= top_n <= 100:
            raise CommandError("top-n باید بین ۱ و ۱۰۰ باشد.")
        run = run_matching(
            trigger=MatchingRun.Trigger.NIGHTLY,
            top_n=top_n,
            recipient_id=options.get("recipient_id"),
            donor_id=options.get("donor_id"),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Matching run {run.pk} completed: {run.statistics.get('proposals', 0)} proposals"
            )
        )

