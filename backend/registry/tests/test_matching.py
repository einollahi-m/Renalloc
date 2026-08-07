import json
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from registry.matching import abo_compatible, evaluate_pair, run_matching
from registry.models import (
    AntiHlaSelection,
    AntiHlaTest,
    CdcPraTest,
    ClinicalStateEvent,
    CrossMatchRequest,
    DonorProfile,
    HLASelection,
    HLATyping,
    MatchProposal,
    MatchingRun,
    Person,
    RecipientProfile,
)
from registry.workflows import allowed_transitions, transition_profile
from users.models import AccessToken, Center, User


class MatchingEngineTests(TestCase):
    def setUp(self):
        self.center = Center.objects.create(name="مرکز Matching")
        self.user = User.objects.create_user(
            username="matching-user",
            password="Safe-pass-8765",
            national_id="1234567890",
            first_name="هماهنگ",
            last_name="Matching",
            gender=User.Gender.FEMALE,
            email="matching@example.com",
            mobile_phone="09121234567",
            center=self.center,
            coordinator_level=User.CoordinatorLevel.LEVEL_ONE,
        )
        self.token, _ = AccessToken.issue(
            self.user, expires_at=timezone.now() + timedelta(hours=1)
        )
        self.recipient = self.make_recipient("REC-1", "A+")
        self.donor = self.make_donor("DON-1", "O-")

    def make_person(self, identifier, blood_group, first_name):
        return Person.objects.create(
            citizenship=Person.Citizenship.FOREIGN,
            identifier=identifier,
            first_name=first_name,
            last_name="آزمون",
            gender=Person.Gender.MALE,
            birth_date=date(1990, 1, 1),
            blood_group=blood_group,
            phone="09123456789",
            nationality="ایرانی",
            center=self.center,
            created_by=self.user,
        )

    def make_recipient(self, identifier, blood_group):
        person = self.make_person(identifier, blood_group, "گیرنده")
        profile = RecipientProfile.objects.create(
            person=person,
            donor_living=True,
            status=RecipientProfile.Status.ACTIVE,
            waiting_since=timezone.localdate() - timedelta(days=600),
            medical_urgency=70,
            regional_disadvantage=30,
        )
        today = timezone.localdate()
        CdcPraTest.objects.create(
            person=person,
            performed_at=today,
            class_i_status="negative",
            class_i_effective_status="negative",
            class_ii_status="negative",
            class_ii_effective_status="negative",
            created_by=self.user,
        )
        AntiHlaTest.objects.create(
            person=person,
            performed_at=today,
            class_i_negative=True,
            class_ii_negative=True,
            created_by=self.user,
        )
        return profile

    def make_donor(self, identifier, blood_group):
        person = self.make_person(identifier, blood_group, "اهداکننده")
        return DonorProfile.objects.create(
            person=person,
            status=DonorProfile.Status.AVAILABLE,
        )

    def set_hla(self, profile, values):
        typing = HLATyping.objects.create(person=profile.person)
        for locus, allele, copies in values:
            HLASelection.objects.create(
                typing=typing, locus=locus, allele=allele, copy_number=copies
            )
        return typing

    def request_json(self, method, url, payload=None):
        return getattr(self.client, method.lower())(
            url,
            data=json.dumps(payload or {}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

    def test_abo_filter_ignores_rh_and_applies_donor_direction(self):
        self.assertTrue(abo_compatible("O-", "A+"))
        self.assertTrue(abo_compatible("A+", "AB-"))
        self.assertFalse(abo_compatible("AB-", "A+"))
        self.assertFalse(abo_compatible("B+", "O-"))

    def test_homozygous_copy_number_scores_two_matches(self):
        self.set_hla(self.recipient, [("A", "A*02", 2)])
        self.set_hla(self.donor, [("A", "A*02", 2)])

        result = evaluate_pair(self.recipient, self.donor)

        self.assertEqual(result["compatibility"], MatchProposal.Compatibility.COMPATIBLE)
        self.assertEqual(result["hla_summary"]["loci"]["A"]["matches"], 2)
        self.assertEqual(result["hla_summary"]["loci"]["A"]["common"], ["A*02", "A*02"])

    def test_resolution_mismatch_is_conditional_but_exact_antigen_is_rejected(self):
        anti = self.recipient.person.anti_hla_tests.get()
        anti.class_i_negative = False
        anti.save(update_fields=("class_i_negative",))
        AntiHlaSelection.objects.create(
            test=anti,
            hla_class="I",
            locus="A",
            antigen="A*02:01",
        )
        donor_typing = self.set_hla(self.donor, [("A", "A*02", 1)])

        conditional = evaluate_pair(self.recipient, self.donor)
        self.assertEqual(conditional["compatibility"], MatchProposal.Compatibility.CONDITIONAL)
        self.assertEqual(conditional["warnings"][0]["code"], "resolution_mismatch")

        selection = donor_typing.selections.get()
        selection.allele = "A*02:01"
        selection.save(update_fields=("allele",))
        rejected = evaluate_pair(self.recipient, self.donor)
        self.assertEqual(rejected["compatibility"], MatchProposal.Compatibility.INCOMPATIBLE)
        self.assertIn("anti_hla_mismatch", [item["code"] for item in rejected["rejection_reasons"]])

    def test_citizenship_mismatch_is_rejected(self):
        self.donor.person.citizenship = Person.Citizenship.IRANIAN
        self.donor.person.nationality = ""
        self.donor.person.save(update_fields=("citizenship", "nationality"))
        self.set_hla(self.recipient, [("A", "A*03", 1)])
        self.set_hla(self.donor, [("A", "A*03", 1)])

        result = evaluate_pair(self.recipient, self.donor)
        self.assertEqual(result["compatibility"], MatchProposal.Compatibility.INCOMPATIBLE)
        self.assertFalse(result["citizenship_compatible"])
        self.assertIn(
            "citizenship_incompatible", [item["code"] for item in result["rejection_reasons"]]
        )

    def test_creg_related_antigen_is_reported_as_potential_warning(self):
        anti = self.recipient.person.anti_hla_tests.get()
        anti.class_i_negative = False
        anti.save(update_fields=("class_i_negative",))
        AntiHlaSelection.objects.create(
            test=anti, hla_class="I", locus="A", antigen="A*23:01"
        )
        self.set_hla(self.recipient, [("A", "A*03", 1)])
        self.set_hla(self.donor, [("A", "A*24", 1)])

        result = evaluate_pair(self.recipient, self.donor)
        self.assertEqual(result["compatibility"], MatchProposal.Compatibility.CONDITIONAL)
        self.assertTrue(result["creg_summary"]["has_potential_conflict"])
        self.assertIn("A2", result["creg_summary"]["active_groups"])
        self.assertIn("creg_potential_conflict", [item["code"] for item in result["warnings"]])

    def test_recipient_self_hla_anti_hla_overlap_is_conditional_not_rejected(self):
        anti = self.recipient.person.anti_hla_tests.get()
        anti.class_i_negative = False
        anti.save(update_fields=("class_i_negative",))
        AntiHlaSelection.objects.create(
            test=anti, hla_class="I", locus="A", antigen="A*02:01"
        )
        self.set_hla(self.recipient, [("A", "A*02", 1)])
        self.set_hla(self.donor, [("A", "A*02:01", 1)])

        result = evaluate_pair(self.recipient, self.donor)

        self.assertEqual(result["compatibility"], MatchProposal.Compatibility.CONDITIONAL)
        self.assertTrue(result["self_hla_anti_hla_overlap"])
        self.assertNotIn("anti_hla_mismatch", [item["code"] for item in result["rejection_reasons"]])
        self.assertIn(
            "self_hla_anti_hla_overlap", [item["code"] for item in result["warnings"]]
        )

    def test_priority_emergency_update_is_auditable_and_requeues_matching(self):
        with patch("registry.api.match_recipient.delay_on_commit") as task:
            response = self.request_json(
                "patch",
                reverse("registry:recipient-priority", args=[self.recipient.pk]),
                {
                    "medical_urgency": 95,
                    "regional_disadvantage": 20,
                    "waiting_since": self.recipient.waiting_since.isoformat(),
                    "is_emergency": True,
                    "emergency_reason": "شرایط اورژانسی مستند آزمون",
                },
            )
        self.assertEqual(response.status_code, 200, response.content)
        self.recipient.refresh_from_db()
        self.assertTrue(self.recipient.is_emergency)
        self.assertEqual(self.recipient.medical_urgency, 95)
        self.assertTrue(
            ClinicalStateEvent.objects.filter(
                recipient=self.recipient, metadata__kind="priority_update"
            ).exists()
        )
        task.assert_called_once_with(str(self.recipient.pk), self.user.pk, "manual")

    def test_deceased_donor_endpoint_only_ranks_opted_in_same_citizenship_recipients(self):
        self.recipient.donor_deceased = True
        self.recipient.save(update_fields=("donor_deceased",))
        self.set_hla(self.recipient, [("A", "A*03", 1)])

        response = self.request_json(
            "post",
            reverse("registry:deceased-donor-matching"),
            {
                "citizenship": Person.Citizenship.FOREIGN,
                "blood_group": "O-",
                "hla_a": ["A*03"],
                "top_n": 10,
            },
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["statistics"]["evaluated_candidates"], 1)
        self.assertEqual(len(response.json()["matches"]), 1)
        self.assertEqual(
            response.json()["matches"][0]["recipient"]["id"], str(self.recipient.pk)
        )

    def test_expired_immunology_excludes_recipient_from_proposals(self):
        self.set_hla(self.recipient, [("A", "A*03", 1)])
        self.set_hla(self.donor, [("A", "A*03", 1)])
        anti = self.recipient.person.anti_hla_tests.get()
        anti.performed_at = timezone.localdate() - timedelta(days=220)
        anti.save()

        result = evaluate_pair(self.recipient, self.donor)
        run = run_matching(trigger=MatchingRun.Trigger.MANUAL, initiated_by=self.user)

        self.assertEqual(result["compatibility"], MatchProposal.Compatibility.INCOMPATIBLE)
        self.assertIn("anti_hla_not_current", [item["code"] for item in result["rejection_reasons"]])
        self.assertEqual(run.proposals.count(), 0)

    def test_status_transition_records_actor_reason_and_rejects_invalid_jump(self):
        pending = self.make_recipient("REC-2", "O+")
        pending.status = RecipientProfile.Status.PENDING_DOCUMENTS
        pending.waiting_since = None
        pending.save(update_fields=("status", "waiting_since"))

        active = transition_profile(
            pending,
            RecipientProfile.Status.ACTIVE,
            self.user,
            "مدارک و آزمایش‌ها تأیید شد",
        )

        event = ClinicalStateEvent.objects.filter(recipient=active).latest("created_at")
        self.assertEqual(event.previous_status, RecipientProfile.Status.PENDING_DOCUMENTS)
        self.assertEqual(event.new_status, RecipientProfile.Status.ACTIVE)
        self.assertEqual(event.actor, self.user)
        self.assertTrue(active.waiting_since)

    def test_removed_recipient_can_return_to_waiting_list_and_matching_queue(self):
        self.recipient.status = RecipientProfile.Status.REMOVED
        self.recipient.save(update_fields=("status",))

        self.assertIn(
            RecipientProfile.Status.ACTIVE,
            allowed_transitions(self.recipient),
        )
        self.assertIn(
            RecipientProfile.Status.PENDING_DOCUMENTS,
            allowed_transitions(self.recipient),
        )

        with patch("registry.tasks.match_recipient.delay_on_commit") as matching_task:
            restored = transition_profile(
                self.recipient,
                RecipientProfile.Status.ACTIVE,
                self.user,
                "بازگشت مجدد گیرنده به لیست انتظار",
            )

        self.assertEqual(restored.status, RecipientProfile.Status.ACTIVE)
        matching_task.assert_called_once_with(str(restored.pk), self.user.pk, "manual")
        event = ClinicalStateEvent.objects.filter(recipient=restored).latest("created_at")
        self.assertEqual(event.previous_status, RecipientProfile.Status.REMOVED)
        self.assertEqual(event.new_status, RecipientProfile.Status.ACTIVE)

    def test_waiting_list_and_available_transitions_publish_scoped_tasks(self):
        recipient = self.make_recipient("REC-QUEUE", "O+")
        recipient.status = RecipientProfile.Status.PENDING_DOCUMENTS
        recipient.waiting_since = None
        recipient.save(update_fields=("status", "waiting_since"))
        donor = self.make_donor("DON-QUEUE", "O+")
        donor.status = DonorProfile.Status.MEDICAL_SCREENING
        donor.save(update_fields=("status",))

        with patch("registry.tasks.match_recipient.delay_on_commit") as recipient_task:
            transition_profile(recipient, RecipientProfile.Status.ACTIVE, self.user, "تأیید ورود")
        with patch("registry.tasks.match_donor.delay_on_commit") as donor_task:
            transition_profile(donor, DonorProfile.Status.AVAILABLE, self.user, "تأیید غربالگری")

        recipient_task.assert_called_once_with(str(recipient.pk), self.user.pk, "manual")
        donor_task.assert_called_once_with(str(donor.pk), self.user.pk, "donor_created")

    def test_level_two_cannot_change_status_or_priority(self):
        level_two = User.objects.create_user(
            username="level-two",
            password="Safe-pass-1234",
            national_id="1112223339",
            first_name="هماهنگ",
            last_name="سطح دو",
            gender=User.Gender.MALE,
            email="level-two@example.com",
            mobile_phone="09120000000",
            center=self.center,
            coordinator_level=User.CoordinatorLevel.LEVEL_TWO,
        )
        token, _ = AccessToken.issue(level_two, expires_at=timezone.now() + timedelta(hours=1))
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        status_response = self.client.post(
            reverse("registry:recipient-status", args=[self.recipient.pk]),
            data=json.dumps({"status": "temporarily_inactive", "reason": "آزمون"}),
            content_type="application/json",
            **headers,
        )
        priority_response = self.client.patch(
            reverse("registry:recipient-priority", args=[self.recipient.pk]),
            data=json.dumps({"medical_urgency": 90}),
            content_type="application/json",
            **headers,
        )
        donor_response = self.client.post(
            reverse("registry:donor-status", args=[self.donor.pk]),
            data=json.dumps({"status": "suspended", "reason": "آزمون"}),
            content_type="application/json",
            **headers,
        )

        self.assertEqual(status_response.status_code, 403)
        self.assertEqual(priority_response.status_code, 403)
        self.assertEqual(donor_response.status_code, 403)

    def test_profile_matching_endpoint_only_enqueues_the_selected_entity(self):
        with patch(
            "registry.api.match_recipient.delay", return_value=SimpleNamespace(id="task-recipient")
        ) as queued:
            response = self.request_json(
                "post",
                reverse("registry:matching-enqueue"),
                {"recipient_id": str(self.recipient.pk)},
            )

        self.assertEqual(response.status_code, 202, response.content)
        self.assertEqual(response.json()["task"]["id"], "task-recipient")
        queued.assert_called_once_with(
            str(self.recipient.pk), self.user.pk, MatchingRun.Trigger.MANUAL
        )

    def test_center_approval_and_crossmatch_result_drive_both_state_machines(self):
        self.set_hla(self.recipient, [("A", "A*03", 1)])
        self.set_hla(self.donor, [("A", "A*03", 1)])
        run = run_matching(
            trigger=MatchingRun.Trigger.MANUAL,
            initiated_by=self.user,
            recipient_id=self.recipient.pk,
        )
        proposal = run.proposals.get()

        approved = self.request_json(
            "patch",
            reverse("registry:proposal-decision", args=[proposal.pk]),
            {"decision": "approved", "note": "از نظر بالینی قابل بررسی است"},
        )
        self.assertEqual(approved.status_code, 200, approved.content)
        request = CrossMatchRequest.objects.get(proposal=proposal)
        self.recipient.refresh_from_db()
        self.donor.refresh_from_db()
        self.assertEqual(self.recipient.status, RecipientProfile.Status.AWAITING_CROSSMATCH)
        self.assertEqual(self.donor.status, DonorProfile.Status.AWAITING_CROSSMATCH)

        scheduled = self.request_json(
            "patch",
            reverse("registry:crossmatch-result", args=[request.pk]),
            {"status": "scheduled", "physician_note": "نمونه‌گیری انجام شد"},
        )
        self.assertEqual(scheduled.status_code, 200, scheduled.content)
        negative = self.request_json(
            "patch",
            reverse("registry:crossmatch-result", args=[request.pk]),
            {"status": "negative", "physician_note": "Cross-Match فیزیکی منفی است"},
        )
        self.assertEqual(negative.status_code, 200, negative.content)
        self.recipient.refresh_from_db()
        self.donor.refresh_from_db()
        proposal.refresh_from_db()
        self.assertEqual(self.recipient.status, RecipientProfile.Status.READY)
        self.assertEqual(self.donor.status, DonorProfile.Status.READY)
        self.assertEqual(proposal.decision, MatchProposal.Decision.CROSSMATCH_NEGATIVE)

    def test_conditional_match_requires_physical_negative_then_high_resolution(self):
        anti = self.recipient.person.anti_hla_tests.get()
        anti.class_i_negative = False
        anti.save(update_fields=("class_i_negative",))
        AntiHlaSelection.objects.create(
            test=anti, hla_class="I", locus="A", antigen="A*02:01"
        )
        donor_typing = self.set_hla(self.donor, [("A", "A*02", 1)])
        run = run_matching(
            trigger=MatchingRun.Trigger.MANUAL,
            initiated_by=self.user,
            recipient_id=self.recipient.pk,
        )
        proposal = run.proposals.get()
        self.assertEqual(proposal.compatibility, MatchProposal.Compatibility.CONDITIONAL)
        self.request_json(
            "patch",
            reverse("registry:proposal-decision", args=[proposal.pk]),
            {"decision": "approved", "note": "مشروط به Cross-Match فیزیکی"},
        )
        request = CrossMatchRequest.objects.get(proposal=proposal)
        self.request_json(
            "patch",
            reverse("registry:crossmatch-result", args=[request.pk]),
            {"status": "scheduled", "physician_note": "نمونه‌گیری شد"},
        )

        physical_negative = self.request_json(
            "patch",
            reverse("registry:crossmatch-result", args=[request.pk]),
            {"status": "negative", "physician_note": "نتیجه فیزیکی منفی"},
        )
        self.assertEqual(physical_negative.status_code, 200, physical_negative.content)
        request.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(request.status, CrossMatchRequest.Status.AWAITING_HIGH_RESOLUTION)
        self.assertEqual(
            self.recipient.status, RecipientProfile.Status.AWAITING_HIGH_RESOLUTION
        )

        premature = self.request_json(
            "patch",
            reverse("registry:crossmatch-result", args=[request.pk]),
            {"status": "negative", "physician_note": "بدون تایپ تکمیلی"},
        )
        self.assertEqual(premature.status_code, 400, premature.content)

        finalized = self.request_json(
            "patch",
            reverse("registry:crossmatch-result", args=[request.pk]),
            {
                "status": "negative",
                "physician_note": "High-Resolution تکمیل و توسط آزمایشگاه تأیید شد",
                "high_resolution_confirmed": True,
            },
        )
        self.assertEqual(finalized.status_code, 200, finalized.content)
        self.recipient.refresh_from_db()
        self.donor.refresh_from_db()
        self.assertEqual(self.recipient.status, RecipientProfile.Status.READY)
        self.assertEqual(self.donor.status, DonorProfile.Status.READY)
