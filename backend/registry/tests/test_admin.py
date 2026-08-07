from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from registry.management.commands.grant_registry_manager import MANAGER_GROUP_NAME
from registry.models import (
    DonorProfile,
    HLATyping,
    LabTest,
    Person,
    RecipientProfile,
    SensitiveDataAccessLog,
)
from users.models import Center, User


class RegistryAdminTests(TestCase):
    def setUp(self):
        self.center = Center.objects.create(name="مرکز مدیریت")
        self.manager = User.objects.create_user(
            username="registry-manager",
            password="Safe-pass-9472",
            national_id="1234567890",
            first_name="مدیر",
            last_name="پرونده‌ها",
            gender=User.Gender.FEMALE,
            email="manager@example.com",
            mobile_phone="09121234567",
            center=self.center,
        )

    def make_person(self, identifier, name):
        return Person.objects.create(
            citizenship=Person.Citizenship.FOREIGN,
            identifier=identifier,
            first_name=name,
            last_name="آزمایشی",
            gender=Person.Gender.MALE,
            birth_date=date(1990, 1, 1),
            blood_group="O+",
            phone="09123456789",
            nationality="ایرانی",
            center=self.center,
            created_by=self.manager,
        )

    def grant_manager_access(self):
        output = StringIO()
        call_command("grant_registry_manager", self.manager.username, stdout=output)
        self.manager.refresh_from_db()
        return output.getvalue()

    def test_management_command_grants_staff_registry_permissions(self):
        output = self.grant_manager_access()

        self.assertTrue(self.manager.is_staff)
        self.assertTrue(self.manager.groups.filter(name=MANAGER_GROUP_NAME).exists())
        self.assertTrue(self.manager.has_perm("registry.view_recipientprofile"))
        self.assertTrue(self.manager.has_perm("registry.change_donorprofile"))
        self.assertTrue(self.manager.has_perm("registry.delete_recipientprofile"))
        self.assertFalse(self.manager.has_perm("users.delete_user"))
        self.assertIn("/admin/", output)

    def test_manager_dashboard_is_simplified_and_profile_deletion_works(self):
        self.grant_manager_access()
        recipient = RecipientProfile.objects.create(
            person=self.make_person("ADMIN-REC-1", "گیرنده"),
            donor_living=True,
            status=RecipientProfile.Status.REMOVED,
        )
        donor = DonorProfile.objects.create(
            person=self.make_person("ADMIN-DON-1", "اهداکننده"),
            status=DonorProfile.Status.SUSPENDED,
        )
        HLATyping.objects.create(person=recipient.person)
        LabTest.objects.create(
            person=recipient.person,
            kind=LabTest.Kind.ROUTINE,
            category="CBC",
            name="HB",
            result="12.4",
            performed_at=date(2026, 8, 1),
            created_by=self.manager,
        )
        access_log = SensitiveDataAccessLog.objects.create(
            user=self.manager,
            person=recipient.person,
            purpose="admin deletion test",
        )
        self.client.force_login(self.manager)

        dashboard = self.client.get(reverse("admin:index"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "مدیریت پرونده‌های پیوند")
        self.assertContains(dashboard, "گیرندگان")
        self.assertContains(dashboard, "اهداکنندگان")
        self.assertNotContains(dashboard, "تایپ‌های HLA")

        recipient_delete = self.client.post(
            reverse("admin:registry_recipientprofile_delete", args=(recipient.pk,)),
            {"post": "yes"},
            follow=True,
        )
        donor_delete = self.client.post(
            reverse("admin:registry_donorprofile_delete", args=(donor.pk,)),
            {"post": "yes"},
            follow=True,
        )

        self.assertEqual(recipient_delete.status_code, 200)
        self.assertEqual(donor_delete.status_code, 200)
        self.assertFalse(RecipientProfile.objects.filter(pk=recipient.pk).exists())
        self.assertFalse(DonorProfile.objects.filter(pk=donor.pk).exists())
        self.assertFalse(Person.objects.filter(pk=recipient.pk).exists())
        self.assertFalse(Person.objects.filter(pk=donor.pk).exists())
        self.assertFalse(HLATyping.objects.filter(pk=recipient.pk).exists())
        self.assertFalse(LabTest.objects.filter(person_id=recipient.pk).exists())

        # The access audit survives deletion without retaining a blocking FK.
        access_log.refresh_from_db()
        self.assertIsNone(access_log.person_id)
        self.assertEqual(access_log.person_identifier, "ADMIN-REC-1")

        replacement = self.make_person("ADMIN-REC-1", "ثبت مجدد")
        self.assertNotEqual(replacement.pk, recipient.pk)
