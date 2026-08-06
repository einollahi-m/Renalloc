from datetime import date

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ImmunologyDataMigrationTests(TransactionTestCase):
    migrate_from = ("registry", "0001_initial")
    migrate_to = (
        "registry",
        "0002_antihlaselection_antihlatest_cdcpratest_hlaselection_and_more",
    )
    users_from = ("users", "0002_user_notify_email_approvals_and_more")
    users_to = ("users", "0003_user_coordinator_level")

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from, self.users_from])
        old_apps = executor.loader.project_state([self.migrate_from, self.users_from]).apps

        Center = old_apps.get_model("users", "Center")
        User = old_apps.get_model("users", "User")
        Person = old_apps.get_model("registry", "Person")
        RecipientProfile = old_apps.get_model("registry", "RecipientProfile")
        HLATyping = old_apps.get_model("registry", "HLATyping")
        LabTest = old_apps.get_model("registry", "LabTest")

        center = Center.objects.create(name="مرکز مهاجرت داده")
        user = User.objects.create(
            username="migration-user",
            password="!",
            national_id="1234567890",
            first_name="کاربر",
            last_name="مهاجرت",
            gender="female",
            email="migration@example.com",
            mobile_phone="09121234567",
            center=center,
        )
        person = Person.objects.create(
            citizenship="iranian",
            identifier="0013548794",
            first_name="پرونده",
            last_name="قدیمی",
            gender="female",
            birth_date=date(1990, 1, 1),
            blood_group="O+",
            phone="09123456789",
            center=center,
            created_by=user,
        )
        RecipientProfile.objects.create(person=person, donor_living=True)
        HLATyping.objects.create(person=person, hla_a=["A*01", "A*02"])
        common = {
            "person": person,
            "performed_at": date(2026, 1, 31),
            "expires_at": date(2026, 7, 31),
            "created_by": user,
        }
        LabTest.objects.create(
            **common,
            kind="cdc_pra",
            category="CDC PRA",
            name="class_i",
            result={"status": "positive", "value": "25", "effective_status": "positive"},
            details={"implicitly_negative": False},
        )
        LabTest.objects.create(
            **common,
            kind="cdc_pra",
            category="CDC PRA",
            name="class_ii",
            result={"status": "negative", "value": None, "effective_status": "negative"},
            details={"implicitly_negative": False},
        )
        LabTest.objects.create(
            **common,
            kind="anti_hla",
            category="Class I",
            name="A - A*01:01",
            result=None,
            details={"class": "I", "locus": "A", "antigen": "A*01:01", "mfi": None},
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to, self.users_to])
        self.apps = executor.loader.project_state([self.migrate_to, self.users_to]).apps

    def test_existing_json_and_generic_lab_rows_are_preserved(self):
        HLASelection = self.apps.get_model("registry", "HLASelection")
        CdcPraTest = self.apps.get_model("registry", "CdcPraTest")
        AntiHlaSelection = self.apps.get_model("registry", "AntiHlaSelection")
        LabTest = self.apps.get_model("registry", "LabTest")

        self.assertEqual(
            list(HLASelection.objects.values_list("allele", flat=True)),
            ["A*01", "A*02"],
        )
        cdc = CdcPraTest.objects.get()
        self.assertEqual(cdc.class_i_status, "positive")
        self.assertEqual(cdc.expires_at, date(2026, 7, 31))
        self.assertEqual(AntiHlaSelection.objects.get().antigen, "A*01:01")
        self.assertFalse(LabTest.objects.filter(kind__in=("cdc_pra", "anti_hla")).exists())
