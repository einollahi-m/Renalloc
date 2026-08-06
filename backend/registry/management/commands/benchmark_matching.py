import json
import random
import time
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError

from registry.matching import ABO_DONOR_TO_RECIPIENT


class Command(BaseCommand):
    help = "بنچمارک بدون داده شخصی با نمونه‌گیری و برون‌یابی به مقیاس ملی"

    def add_arguments(self, parser):
        parser.add_argument("--recipients", type=int, default=5_000_000)
        parser.add_argument("--donors", type=int, default=1_000_000)
        parser.add_argument("--sample-size", type=int, default=100_000)
        parser.add_argument("--seed", type=int, default=1405)

    def handle(self, *args, **options):
        national_recipients = options["recipients"]
        national_donors = options["donors"]
        sample_size = options["sample_size"]
        if min(national_recipients, national_donors, sample_size) <= 0:
            raise CommandError("همه اندازه‌ها باید مثبت باشند.")
        sample_size = min(sample_size, 1_000_000)
        rng = random.Random(options["seed"])
        blood_groups = ("O", "A", "B", "AB")
        antigens = tuple(f"A*{value:02d}" for value in range(1, 81))

        started = time.perf_counter()
        anti_index = defaultdict(set)
        blood_index = defaultdict(set)
        for recipient_id in range(sample_size):
            recipient_group = rng.choices(blood_groups, (35, 30, 25, 10))[0]
            blood_index[recipient_group].add(recipient_id)
            for antigen in rng.sample(antigens, rng.randint(0, 8)):
                anti_index[antigen].add(recipient_id)
        index_seconds = time.perf_counter() - started

        started = time.perf_counter()
        eligible_counts = []
        donor_sample = max(1, min(sample_size // 100, 10_000))
        for _ in range(donor_sample):
            donor_blood = rng.choices(blood_groups, (35, 30, 25, 10))[0]
            donor_hla = rng.sample(antigens, 2)
            sensitized = anti_index[donor_hla[0]] | anti_index[donor_hla[1]]
            abo_candidates = set().union(
                *(blood_index[group] for group in ABO_DONOR_TO_RECIPIENT[donor_blood])
            )
            eligible = len(abo_candidates - sensitized)
            eligible_counts.append(eligible)
        query_seconds = time.perf_counter() - started
        average_ratio = sum(eligible_counts) / (len(eligible_counts) * sample_size)
        brute_force_pairs = national_recipients * national_donors
        estimated_candidates = int(brute_force_pairs * average_ratio)
        report = {
            "seed": options["seed"],
            "sample_recipients": sample_size,
            "sample_donors": donor_sample,
            "national_recipients": national_recipients,
            "national_donors": national_donors,
            "brute_force_pairs": brute_force_pairs,
            "estimated_pairs_after_abo_and_anti_hla": estimated_candidates,
            "estimated_reduction_percent": round((1 - average_ratio) * 100, 3),
            "inverted_index_keys": len(anti_index),
            "index_build_seconds": round(index_seconds, 4),
            "sample_query_seconds": round(query_seconds, 4),
            "queries_per_second": round(donor_sample / query_seconds, 2) if query_seconds else None,
            "note": "نتیجه برون‌یابی نمونه مصنوعی است و جایگزین Load Test زیرساخت production نیست.",
        }
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
