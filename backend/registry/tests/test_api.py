import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from registry.models import (
    AntiHlaTest,
    CdcPraTest,
    DonorProfile,
    HLASelection,
    HLATyping,
    LabTest,
    Person,
    RecipientProfile,
)
from users.models import AccessToken, Center, User


class RegistryApiTests(TestCase):
    def setUp(self):
        self.center = Center.objects.create(name="مرکز ثبت پیوند")
        self.user = User.objects.create_user(
            username="registry-coordinator",
            password="Safe-pass-9472",
            national_id="1234567890",
            first_name="مریم",
            last_name="هماهنگ‌کننده",
            gender=User.Gender.FEMALE,
            email="registry@example.com",
            mobile_phone="09121234567",
            center=self.center,
        )
        self.token, _ = AccessToken.issue(
            self.user, expires_at=timezone.now() + timedelta(hours=1)
        )

    def request_json(self, method, url, payload=None, *, authenticated=True):
        headers = (
            {"HTTP_AUTHORIZATION": f"Bearer {self.token}"} if authenticated else {}
        )
        return getattr(self.client, method.lower())(
            url,
            data=json.dumps(payload or {}),
            content_type="application/json",
            **headers,
        )

    def recipient_payload(self, identifier="0013548794"):
        return {
            "citizenship": "iranian",
            "national_id": identifier,
            "first_name": "سارا",
            "last_name": "گیرنده",
            "gender": "female",
            "birth_date": "1990-04-12",
            "blood_type": "O",
            "rh_factor": "positive",
            "phone": "۰۹۱۲۳۴۵۶۷۸۹",
            "emergency_contact_phone": "",
            "insurance": ["social_security"],
            "weight": "۷۲٫۵",
            "height": "۱۶۸",
            "is_smoker": False,
            "has_addiction": False,
            "has_alcohol": False,
            "transplant_candidate": "1st",
            "donor_living": True,
            "donor_deceased": False,
            "has_dialysis_history": False,
            "has_blood_transfusion": False,
            "has_pregnancy_history": False,
            "has_abortion_history": False,
            "previous_transplant": False,
            "has_drug_allergy": False,
            "family_kidney_disease": False,
            "hla_a": ["A*01", "A*02"],
            "hla_b": [],
            "hla_c": [],
            "hla_drb1": [],
            "hla_dqb1": [],
            "hla_drb": [],
            "cdc_pra_tests": [
                {
                    "performed_at": "2026-01-31",
                    "class_i": {"status": "positive", "value": "۲۵"},
                    "class_ii": {"status": "negative", "value": None},
                }
            ],
            "anti_hla_display": [
                {
                    "batchId": "anti-hla-1",
                    "class": "I",
                    "locus": "A",
                    "antigen": "A*01:01",
                    "testName": "A - A*01:01",
                    "value": None,
                    "testDate": "2026-01-31",
                }
            ],
            "routine_tests": [
                {
                    "category": "CBC",
                    "testName": "HB",
                    "value": "۱۲٫۸",
                    "testDate": "2026-01-31T00:00:00.000Z",
                }
            ],
            "viral_tests": [
                {
                    "category": "آزمایش ویروسی",
                    "testName": "HBs Ag",
                    "value": "negative",
                    "testDate": "2026-01-31T00:00:00.000Z",
                }
            ],
            "approvals": {},
        }

    def optional_immunology_payload(self, identifier="0499370899"):
        payload = self.recipient_payload(identifier)
        for field in ("hla_a", "hla_b", "hla_c", "hla_drb1", "hla_dqb1", "hla_drb"):
            payload[field] = []
        payload["cdc_pra_tests"] = []
        payload["anti_hla_display"] = []
        payload["routine_tests"] = []
        payload["viral_tests"] = []
        return payload

    def donor_payload(self):
        return {
            "citizenship": "iranian",
            "national_id": "0084575948",
            "first_name": "رضا",
            "last_name": "اهداکننده",
            "gender": "male",
            "birth_date": "1988-02-10",
            "blood_type": "A",
            "rh_factor": "negative",
            "phone": "09351234567",
            "emergency_contact_phone": "",
            "insurance": [],
            "is_smoker": False,
            "has_addiction": False,
            "has_alcohol": False,
            "self_diabetes_history": False,
            "self_hypertension_history": False,
            "parent_diabetes_history": False,
            "parent_hypertension_history": False,
            "has_drug_allergy": False,
            "is_related_recipient_candidate": True,
            "preferred_recipient_national_id": "0013548794",
            "recipient_relationship_group": "first_degree",
            "recipient_relationship_kind": "brother",
            "hla_a": [],
            "hla_b": [],
            "hla_c": [],
            "hla_drb1": [],
            "hla_dqb1": [],
            "hla_drb": [],
            "routine_tests": [],
            "viral_tests": [],
            "approvals": {},
        }

    def register_recipient(self, payload=None):
        response = self.request_json(
            "post", reverse("registry:recipients"), payload or self.recipient_payload()
        )
        self.assertEqual(response.status_code, 201, response.content)
        return Person.objects.get(identifier=(payload or self.recipient_payload())["national_id"])

    def test_registration_is_authenticated_normalized_and_transactional(self):
        unauthenticated = self.request_json(
            "post",
            reverse("registry:recipients"),
            self.recipient_payload(),
            authenticated=False,
        )
        self.assertEqual(unauthenticated.status_code, 401)
        person = self.register_recipient()
        self.assertTrue(RecipientProfile.objects.filter(person=person).exists())
        self.assertEqual(
            list(
                HLASelection.objects.filter(typing__person=person).values_list(
                    "allele", flat=True
                )
            ),
            ["A*01", "A*02"],
        )
        self.assertEqual(LabTest.objects.filter(person=person).count(), 2)
        self.assertEqual(CdcPraTest.objects.get(person=person).expires_at.isoformat(), "2026-07-31")
        self.assertEqual(AntiHlaTest.objects.get(person=person).expires_at.isoformat(), "2026-07-31")

        bad_payload = self.recipient_payload("1112223339")
        bad_payload["viral_tests"][0]["testDate"] = "not-a-date"
        response = self.request_json("post", reverse("registry:recipients"), bad_payload)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Person.objects.filter(identifier="1112223339").exists())

    def test_initial_cdc_hla_and_anti_hla_are_optional(self):
        person = self.register_recipient(self.optional_immunology_payload())
        self.assertFalse(HLATyping.objects.filter(person=person).exists())
        self.assertFalse(CdcPraTest.objects.filter(person=person).exists())
        self.assertFalse(AntiHlaTest.objects.filter(person=person).exists())

    def test_multiple_cdc_pra_tests_are_saved_during_initial_registration(self):
        payload = self.recipient_payload("0499370899")
        payload["cdc_pra_tests"].append(
            {
                "performed_at": "2026-03-15",
                "class_i": {"status": "negative", "value": None},
                "class_ii": {"status": "positive", "value": "۴۲٫۵"},
            }
        )

        person = self.register_recipient(payload)
        tests = list(CdcPraTest.objects.filter(person=person).order_by("performed_at"))

        self.assertEqual(len(tests), 2)
        self.assertEqual(tests[0].class_i_status, "positive")
        self.assertEqual(tests[1].class_ii_status, "positive")
        self.assertEqual(str(tests[1].class_ii_value), "42.50")
        self.assertEqual(tests[1].expires_at.isoformat(), "2026-09-15")

    def test_initial_cdc_pra_rejects_duplicate_dates_transactionally(self):
        payload = self.recipient_payload("0499370899")
        payload["cdc_pra_tests"].append(
            {
                "performed_at": "2026-01-31",
                "class_i": {"status": "negative", "value": None},
                "class_ii": {"status": "negative", "value": None},
            }
        )

        response = self.request_json("post", reverse("registry:recipients"), payload)

        self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(Person.objects.filter(identifier="0499370899").exists())

    def test_identifier_availability_and_database_uniqueness(self):
        url = reverse("registry:identifier-availability")
        response = self.client.get(
            url,
            {"citizenship": "iranian", "identifier": "۰۰۱۳۵۴۸۷۹۴"},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertTrue(response.json()["available"])
        self.register_recipient()
        response = self.client.get(
            url,
            {"citizenship": "iranian", "identifier": "0013548794"},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertFalse(response.json()["available"])
        duplicate = self.request_json(
            "post", reverse("registry:recipients"), self.recipient_payload()
        )
        self.assertEqual(duplicate.status_code, 400)

    def test_multiple_cdc_pra_tests_can_be_added_and_edited(self):
        person = self.register_recipient(self.optional_immunology_payload())
        collection = reverse("registry:cdc-pra-collection", args=[person.pk])
        first_payload = {
            "performed_at": "2026-01-10",
            "class_i": {"status": "negative", "value": None},
            "class_ii": {"status": "negative", "value": None},
        }
        second_payload = {
            "performed_at": "2026-03-10",
            "class_i": {"status": "positive", "value": "35"},
            "class_ii": {"status": "negative", "value": None},
        }
        first = self.request_json("post", collection, first_payload)
        second = self.request_json("post", collection, second_payload)
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(CdcPraTest.objects.filter(person=person).count(), 2)

        test_id = first.json()["test"]["id"]
        first_payload["class_i"] = {"status": "positive", "value": "12.5"}
        updated = self.request_json(
            "patch", reverse("registry:cdc-pra-item", args=[person.pk, test_id]), first_payload
        )
        self.assertEqual(updated.status_code, 200, updated.content)
        self.assertEqual(updated.json()["test"]["class_i"]["status"], "positive")

    def test_hla_can_be_added_later_but_rejects_invalid_or_more_than_two(self):
        person = self.register_recipient(self.optional_immunology_payload())
        url = reverse("registry:person-hla", args=[person.pk])
        valid = {field: [] for field in ("hla_a", "hla_b", "hla_c", "hla_drb1", "hla_dqb1", "hla_drb")}
        valid["hla_a"] = ["A*01", "A*02"]
        response = self.request_json("put", url, valid)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["hla"]["hla_a"], ["A*01", "A*02"])

        invalid = {**valid, "hla_a": ["A*01", "A*02", "A*03"]}
        self.assertEqual(self.request_json("put", url, invalid).status_code, 400)
        wrong_locus = {**valid, "hla_a": ["B*07"]}
        self.assertEqual(self.request_json("put", url, wrong_locus).status_code, 400)
        anti_hla_resolution = {**valid, "hla_drb1": ["DRB1*15:01"]}
        self.assertEqual(
            self.request_json("put", url, anti_hla_resolution).status_code,
            400,
        )

    def test_anti_hla_accepts_zero_to_many_controlled_selections(self):
        person = self.register_recipient(self.optional_immunology_payload())
        url = reverse("registry:anti-hla-collection", args=[person.pk])
        empty = self.request_json(
            "post",
            url,
            {
                "performed_at": "2026-02-01",
                "selections": [],
                "class_i_negative": False,
                "class_ii_negative": False,
            },
        )
        self.assertEqual(empty.status_code, 201, empty.content)
        selected = self.request_json(
            "post",
            url,
            {
                "performed_at": "2026-03-01",
                "selections": [
                    {"class": "I", "locus": "A", "antigen": "A*01:01"},
                    {"class": "II", "locus": "DRB1", "antigen": "DRB1*01:01"},
                ],
                "class_i_negative": False,
                "class_ii_negative": False,
            },
        )
        self.assertEqual(selected.status_code, 201, selected.content)
        invalid = self.request_json(
            "post",
            url,
            {
                "performed_at": "2026-04-01",
                "selections": [{"class": "I", "locus": "A", "antigen": "UNKNOWN"}],
                "class_i_negative": False,
                "class_ii_negative": False,
            },
        )
        self.assertEqual(invalid.status_code, 400)

    def test_lists_details_lookup_and_donor_use_database_records(self):
        person = self.register_recipient()
        recipient_list = self.client.get(
            reverse("registry:recipients"), HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )
        self.assertEqual(recipient_list.status_code, 200)
        self.assertEqual(recipient_list.json()["recipients"][0]["_id"], str(person.pk))
        detail = self.client.get(
            reverse("registry:recipient-detail", args=[person.pk]),
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.json()["recipient"]["cdc_pra_tests"]), 1)
        immune_alerts = detail.json()["recipient"]["immune_alerts"]
        self.assertEqual(immune_alerts["hla_anti_hla_overlaps"], ["A*01:01"])
        self.assertTrue(immune_alerts["has_hla_anti_hla_overlap"])
        self.assertIn(
            "A1C", [row["name"] for row in immune_alerts["creg_table"] if row["active"]]
        )

        lookup = self.client.get(
            reverse("registry:recipient-lookup"),
            {"identifier": "۰۰۱۳۵۴۸۷۹۴"},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(lookup.json()["recipient"]["fullName"], "سارا گیرنده")
        global_lookup = self.client.get(
            reverse("registry:person-lookup"),
            {"identifier": "0013548794"},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(global_lookup.json()["person"]["type"], "recipient")
        donor_response = self.request_json(
            "post", reverse("registry:donors"), self.donor_payload()
        )
        self.assertEqual(donor_response.status_code, 201, donor_response.content)
        donor = DonorProfile.objects.select_related("preferred_recipient__person").get()
        self.assertEqual(donor.preferred_recipient.person.identifier, "0013548794")
        donor_list = self.client.get(
            reverse("registry:donors"), HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )
        self.assertEqual(donor_list.json()["donors"][0]["nationalId"], "0084575948")

    def test_profile_edit_labs_and_approvals_are_available_without_identity_edit(self):
        person = self.register_recipient(self.optional_immunology_payload())
        profile_url = reverse("registry:person-profile", args=[person.pk])

        updated = self.request_json(
            "patch",
            profile_url,
            {"phone": "۰۹۳۵۱۲۳۴۵۶۷", "weight_kg": "۷۴٫۵"},
        )
        self.assertEqual(updated.status_code, 200, updated.content)
        person.refresh_from_db()
        self.assertEqual(person.phone, "09351234567")
        self.assertEqual(str(person.weight_kg), "74.50")

        forbidden = self.request_json("patch", profile_url, {"first_name": "نام جدید"})
        self.assertEqual(forbidden.status_code, 400, forbidden.content)
        person.refresh_from_db()
        self.assertEqual(person.first_name, "سارا")

        lab = self.request_json(
            "post",
            reverse("registry:lab-test-collection", args=[person.pk]),
            {
                "kind": "routine",
                "category": "Blood Biochemistry",
                "name": "Cr",
                "result": "۲٫۱",
                "performed_at": "2026-05-02",
            },
        )
        self.assertEqual(lab.status_code, 201, lab.content)
        lab_id = lab.json()["test"]["id"]
        edited_lab = self.request_json(
            "patch",
            reverse("registry:lab-test-item", args=[person.pk, lab_id]),
            {"result": "۱٫۹"},
        )
        self.assertEqual(edited_lab.status_code, 200, edited_lab.content)
        self.assertEqual(edited_lab.json()["test"]["result"], "1٫9")

        approval = self.request_json(
            "post",
            reverse("registry:approval-collection", args=[person.pk]),
            {
                "specialty": "nephrologist",
                "status": "on_hold",
                "doctor_name": "پزشک آزمون",
                "notes": "در انتظار بررسی",
            },
        )
        self.assertEqual(approval.status_code, 201, approval.content)
        approval_id = approval.json()["approval"]["id"]
        edited_approval = self.request_json(
            "patch",
            reverse("registry:approval-item", args=[person.pk, approval_id]),
            {
                "specialty": "nephrologist",
                "status": "approved",
                "approval_date": "2026-05-03",
                "doctor_name": "پزشک آزمون",
                "medical_code": "۱۲۳۴",
                "notes": "تأیید شد",
            },
        )
        self.assertEqual(edited_approval.status_code, 200, edited_approval.content)
        self.assertEqual(edited_approval.json()["approval"]["status"], "approved")

    def test_lab_batch_matches_registration_modal_and_replaces_one_date(self):
        person = self.register_recipient(self.optional_immunology_payload())
        url = reverse("registry:lab-test-collection", args=[person.pk])
        created = self.request_json(
            "post",
            url,
            {
                "kind": "routine",
                "tests": [
                    {"category": "Blood Biochemistry", "name": "Cr", "result": "2.1", "performed_at": "2026-06-01"},
                    {"category": "Blood Biochemistry", "name": "BUN", "result": "35", "performed_at": "2026-06-01"},
                ],
            },
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertEqual(LabTest.objects.filter(person=person).count(), 2)

        second_date = self.request_json(
            "post",
            url,
            {
                "kind": "routine",
                "tests": [
                    {"category": "Blood Biochemistry", "name": "Cr", "result": "1.8", "performed_at": "2026-06-03"},
                ],
            },
        )
        self.assertEqual(second_date.status_code, 201, second_date.content)
        self.assertEqual(LabTest.objects.filter(person=person).count(), 3)

        replaced = self.request_json(
            "post",
            url,
            {
                "kind": "routine",
                "original_date": "2026-06-01",
                "tests": [
                    {"category": "Blood Biochemistry", "name": "BUN", "result": "31", "performed_at": "2026-06-02"},
                ],
            },
        )
        self.assertEqual(replaced.status_code, 201, replaced.content)
        self.assertEqual(LabTest.objects.filter(person=person).count(), 2)
        self.assertEqual(LabTest.objects.get(person=person, name="BUN").result, "31")
        self.assertTrue(
            LabTest.objects.filter(person=person, name="Cr", performed_at="2026-06-03").exists()
        )

    def test_recipient_and_donor_lists_return_backend_pagination_metadata(self):
        self.register_recipient(self.optional_immunology_payload())
        recipients = self.client.get(
            reverse("registry:recipients"),
            {"page": 1, "page_size": 5, "search": "سارا"},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(recipients.status_code, 200, recipients.content)
        self.assertEqual(recipients.json()["pagination"]["page_size"], 5)
        self.assertEqual(recipients.json()["pagination"]["count"], 1)
        donors = self.client.get(
            reverse("registry:donors"),
            {"page": 1, "page_size": 5},
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(donors.status_code, 200, donors.content)
        self.assertIn("pagination", donors.json())

    def test_registration_and_immunology_edits_enqueue_scoped_matching(self):
        payload = self.optional_immunology_payload()
        with patch("registry.tasks.match_recipient.delay_on_commit") as recipient_task:
            person = self.register_recipient(payload)
        recipient_task.assert_called_once_with(str(person.pk), self.user.pk, "manual")

        hla_payload = {
            field: []
            for field in (
                "hla_a", "hla_b", "hla_c", "hla_drb1", "hla_dqb1", "hla_drb",
                "hla_dqa1", "hla_dpb1", "hla_dpa1",
            )
        }
        hla_payload["hla_a"] = ["A*02"]
        with patch("registry.tasks.match_recipient.delay_on_commit") as hla_task:
            response = self.request_json(
                "put", reverse("registry:person-hla", args=[person.pk]), hla_payload
            )
        self.assertEqual(response.status_code, 200, response.content)
        hla_task.assert_called_once_with(str(person.pk), None, "manual")

        with patch("registry.tasks.match_recipient.delay_on_commit") as anti_task:
            response = self.request_json(
                "post",
                reverse("registry:anti-hla-collection", args=[person.pk]),
                {
                    "performed_at": "2026-07-01",
                    "selections": [],
                    "class_i_negative": True,
                    "class_ii_negative": True,
                },
            )
        self.assertEqual(response.status_code, 201, response.content)
        anti_task.assert_called_once_with(str(person.pk), self.user.pk, "anti_hla_updated")

        with patch("registry.tasks.match_donor.delay_on_commit") as donor_task:
            donor_payload = self.donor_payload()
            donor_payload["preferred_recipient_national_id"] = person.identifier
            donor_response = self.request_json(
                "post", reverse("registry:donors"), donor_payload
            )
        self.assertEqual(donor_response.status_code, 201, donor_response.content)
        donor = DonorProfile.objects.get(person__identifier="0084575948")
        donor_task.assert_called_once_with(str(donor.pk), self.user.pk, "donor_created")
