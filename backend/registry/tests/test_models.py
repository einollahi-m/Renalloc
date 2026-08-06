from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from registry.models import HLASelection, HLATyping, LabTest, Person, add_calendar_months
from users.models import Center, User


class LabTestValidityTests(TestCase):
    def setUp(self):
        self.center = Center.objects.create(name="مرکز آزمون مدل")
        self.user = User.objects.create_user(
            username="model-coordinator",
            password="Safe-pass-3854",
            national_id="1234567890",
            first_name="هماهنگ",
            last_name="کننده",
            gender=User.Gender.FEMALE,
            email="model@example.com",
            mobile_phone="09121234567",
            center=self.center,
        )
        self.person = Person(
            citizenship=Person.Citizenship.IRANIAN,
            identifier="0013548794",
            first_name="علی",
            last_name="آزمایشی",
            gender=Person.Gender.MALE,
            birth_date=date(1990, 1, 1),
            blood_group=Person.BloodGroup.O_POSITIVE,
            phone="09123456789",
            created_by=self.user,
            center=self.center,
        )
        self.person.full_clean()
        self.person.save()

    def test_six_calendar_months_handles_end_of_month(self):
        self.assertEqual(add_calendar_months(date(2024, 8, 31), 6), date(2025, 2, 28))
        self.assertEqual(add_calendar_months(date(2024, 2, 29), 6), date(2024, 8, 29))

    def test_lab_test_stores_expiry_and_validity_querysets_use_it(self):
        test = LabTest.objects.create(
            person=self.person,
            created_by=self.user,
            kind=LabTest.Kind.ROUTINE,
            category="CBC",
            name="HB",
            result="12.8",
            performed_at=date(2024, 8, 31),
        )
        self.assertEqual(test.expires_at, date(2025, 2, 28))
        self.assertEqual(list(LabTest.objects.valid_on(date(2025, 2, 28))), [test])
        self.assertEqual(list(LabTest.objects.expired_on(date(2025, 3, 1))), [test])

    def test_hla_typing_has_no_expiry_field(self):
        typing = HLATyping.objects.create(person=self.person)
        first = HLASelection(typing=typing, locus="A", allele="A*01")
        first.full_clean()
        first.save()
        second = HLASelection(typing=typing, locus="A", allele="A*02")
        second.full_clean()
        second.save()
        self.assertEqual(
            list(typing.selections.values_list("allele", flat=True)),
            ["A*01", "A*02"],
        )
        self.assertNotIn("expires_at", {field.name for field in HLATyping._meta.fields})

    def test_hla_selection_uses_choices_and_limits_each_locus_to_two(self):
        typing = HLATyping.objects.create(person=self.person)
        for allele in ("A*01", "A*02"):
            selection = HLASelection(typing=typing, locus="A", allele=allele)
            selection.full_clean()
            selection.save()
        with self.assertRaises(ValidationError):
            HLASelection(typing=typing, locus="A", allele="A*03").full_clean()
        with self.assertRaises(ValidationError):
            HLASelection(typing=typing, locus="B", allele="A*01").full_clean()
