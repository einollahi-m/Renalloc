import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from registry.choices import HLA_VALUES_BY_LOCUS, HLALocus
from registry.models import (
    AntiHlaSelection,
    AntiHlaTest,
    CdcPraTest,
    DonorProfile,
    HLATyping,
    HLASelection,
    LabTest,
    MedicalApproval,
    Person,
    RecipientProfile,
)
from users.models import Center


def iranian_national_id(serial):
    """Create a deterministic checksum-valid 10 digit identifier."""
    body = f"{serial:09d}"[-9:]
    remainder = sum(int(digit) * (10 - index) for index, digit in enumerate(body)) % 11
    check_digit = remainder if remainder < 2 else 11 - remainder
    return f"{body}{check_digit}"


class Command(BaseCommand):
    help = "Create deterministic, clearly labelled fake recipients and donors."

    def add_arguments(self, parser):
        parser.add_argument("--recipients", type=int, default=100)
        parser.add_argument("--donors", type=int, default=100)
        parser.add_argument("--seed", type=int, default=1405)

    @transaction.atomic
    def handle(self, *args, **options):
        recipient_count = max(0, options["recipients"])
        donor_count = max(0, options["donors"])
        rng = random.Random(options["seed"])
        center, _ = Center.objects.get_or_create(name="مرکز داده آزمایشی Renalloc")
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username="renalloc-fake-seed",
            defaults={
                "first_name": "کاربر",
                "last_name": "داده آزمایشی",
                "national_id": "9000000001",
                "email": "fake-seed@renalloc.invalid",
                "gender": user_model.Gender.FEMALE,
                "mobile_phone": "09190000001",
                "center": center,
                "coordinator_level": user_model.CoordinatorLevel.LEVEL_ONE,
                "is_active": False,
            },
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=("password",))

        created_recipients = sum(
            self._create_recipient(index, rng, center, user)
            for index in range(1, recipient_count + 1)
        )
        created_donors = sum(
            self._create_donor(index, rng, center, user)
            for index in range(1, donor_count + 1)
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Fake registry ready: {recipient_count} recipients and {donor_count} donors "
                f"({created_recipients} + {created_donors} newly created)."
            )
        )

    def _create_person(self, *, role, index, center, user, rng):
        is_iranian = index % 4 != 0
        serial_base = 730_000_000 if role == "R" else 731_000_000
        identifier = (
            iranian_national_id(serial_base + index)
            if is_iranian
            else f"FAKE-{role}-PASSPORT-{index:04d}"
        )
        person, created = Person.objects.get_or_create(
            identifier=identifier,
            defaults={
                "citizenship": Person.Citizenship.IRANIAN if is_iranian else Person.Citizenship.FOREIGN,
                "nationality": "" if is_iranian else rng.choice(("افغانستان", "عراق", "پاکستان")),
                "first_name": "گیرنده آزمایشی" if role == "R" else "اهداکننده آزمایشی",
                "last_name": f"شماره {index:03d}",
                "gender": Person.Gender.FEMALE if index % 2 == 0 else Person.Gender.MALE,
                "birth_date": date(1965 + index % 35, index % 12 + 1, index % 27 + 1),
                "blood_group": rng.choice(tuple(Person.BloodGroup.values)),
                "phone": f"091{'7' if role == 'R' else '8'}{index:07d}",
                "emergency_contact_phone": "",
                "education": rng.choice(("", Person.Education.DIPLOMA, Person.Education.BACHELOR)),
                "insurance": ["sample-insurance"],
                "marital_status": rng.choice(tuple(Person.MaritalStatus.values)),
                "weight_kg": 52 + index % 44,
                "height_cm": 150 + index % 37,
                "center": center,
                "created_by": user,
            },
        )
        return person, created

    def _create_hla(self, person, rng):
        typing, _ = HLATyping.objects.get_or_create(person=person)
        if typing.selections.exists():
            return
        for locus in (HLALocus.A, HLALocus.B, HLALocus.C, HLALocus.DRB1, HLALocus.DQB1):
            low_resolution = [item for item in HLA_VALUES_BY_LOCUS[locus] if ":" not in item]
            for allele in rng.sample(low_resolution, k=2):
                HLASelection.objects.create(typing=typing, locus=locus, allele=allele)

    def _create_recipient(self, index, rng, center, user):
        person, person_created = self._create_person(
            role="R", index=index, center=center, user=user, rng=rng
        )
        profile, profile_created = RecipientProfile.objects.get_or_create(
            person=person,
            defaults={
                "status": RecipientProfile.Status.ACTIVE,
                "waiting_since": timezone.localdate() - timedelta(days=30 + index * 9),
                "medical_urgency": 20 + index % 81,
                "regional_disadvantage": index % 46,
                "transplant_candidate": RecipientProfile.TransplantCandidate.FIRST,
                "donor_living": index % 3 != 0,
                "donor_deceased": index % 3 != 1,
                "has_dialysis_history": index % 5 != 0,
                "dialysis_type": RecipientProfile.DialysisType.HEMODIALYSIS,
            },
        )
        self._create_hla(person, rng)
        today = timezone.localdate()
        CdcPraTest.objects.get_or_create(
            person=person,
            performed_at=today,
            defaults={
                "class_i_status": "negative",
                "class_i_effective_status": "negative",
                "class_ii_status": "negative",
                "class_ii_effective_status": "negative",
                "created_by": user,
            },
        )
        anti, anti_created = AntiHlaTest.objects.get_or_create(
            person=person,
            performed_at=today,
            defaults={
                "class_i_negative": index % 5 != 0,
                "class_ii_negative": True,
                "created_by": user,
            },
        )
        if anti_created and index % 5 == 0:
            AntiHlaSelection.objects.create(
                test=anti,
                hla_class="I",
                locus="A",
                antigen="A*23:01" if index % 10 else "A*02:01",
                mfi=2500 + index * 10,
            )
        LabTest.objects.get_or_create(
            person=person,
            kind=LabTest.Kind.ROUTINE,
            category="Blood Biochemistry",
            name="Cr",
            performed_at=today,
            defaults={"result": round(2 + index / 15, 2), "created_by": user},
        )
        MedicalApproval.objects.get_or_create(
            person=person,
            specialty=MedicalApproval.Specialty.NEPHROLOGIST,
            defaults={
                "status": MedicalApproval.Status.APPROVED,
                "approval_date": today,
                "doctor_name": "پزشک داده آزمایشی",
            },
        )
        return int(person_created or profile_created)

    def _create_donor(self, index, rng, center, user):
        person, person_created = self._create_person(
            role="D", index=index, center=center, user=user, rng=rng
        )
        profile, profile_created = DonorProfile.objects.get_or_create(
            person=person,
            defaults={
                "status": DonorProfile.Status.AVAILABLE,
                "self_diabetes_history": False,
                "self_hypertension_history": False,
                "parent_diabetes_history": index % 9 == 0,
                "parent_hypertension_history": index % 7 == 0,
            },
        )
        self._create_hla(person, rng)
        today = timezone.localdate()
        LabTest.objects.get_or_create(
            person=person,
            kind=LabTest.Kind.VIRAL,
            category="آزمایش ویروسی",
            name="HBs Ag",
            performed_at=today,
            defaults={"result": "negative", "created_by": user},
        )
        MedicalApproval.objects.get_or_create(
            person=person,
            specialty=MedicalApproval.Specialty.NEPHROLOGIST,
            defaults={
                "status": MedicalApproval.Status.APPROVED,
                "approval_date": today,
                "doctor_name": "پزشک داده آزمایشی",
            },
        )
        return int(person_created or profile_created)
