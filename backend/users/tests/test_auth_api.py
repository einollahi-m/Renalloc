import json
import re

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import AccessToken, Center, User


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthApiTests(TestCase):
    def setUp(self):
        self.center = Center.objects.create(name="مرکز پیوند تهران")
        self.password = "A-secure-pass-4829"
        self.user = User.objects.create_user(
            username="coordinator",
            password=self.password,
            national_id="1234567890",
            first_name="سارا",
            last_name="احمدی",
            gender=User.Gender.FEMALE,
            email="coordinator@example.com",
            mobile_phone="09121234567",
            center=self.center,
        )

    def post_json(self, url, data, token=None):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
        return self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
            **headers,
        )

    def login(self, identifier="coordinator"):
        response = self.post_json(
            reverse("users:login"),
            {"identifier": identifier, "password": self.password},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["token"]

    def test_login_accepts_username_or_email(self):
        for identifier in ("coordinator", "COORDINATOR@EXAMPLE.COM"):
            response = self.post_json(
                reverse("users:login"),
                {"identifier": identifier, "password": self.password},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["user"]["center"]["name"], self.center.name)

    def test_login_rejects_invalid_credentials(self):
        response = self.post_json(
            reverse("users:login"),
            {"identifier": self.user.email, "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 401)

    def test_profile_requires_token_and_can_be_updated(self):
        self.assertEqual(self.client.get(reverse("users:profile")).status_code, 401)
        token = self.login()
        response = self.client.patch(
            reverse("users:profile"),
            data=json.dumps({"first_name": "مریم", "mobile_phone": "09351234567"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["full_name"], "مریم احمدی")

    def test_change_password_keeps_current_token_and_updates_login(self):
        token = self.login()
        new_password = "Another-safe-pass-9382"
        response = self.post_json(
            reverse("users:change-password"),
            {"current_password": self.password, "new_password": new_password},
            token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get(
                reverse("users:profile"), HTTP_AUTHORIZATION=f"Bearer {token}"
            ).status_code,
            200,
        )
        response = self.post_json(
            reverse("users:login"),
            {"identifier": self.user.email, "password": new_password},
        )
        self.assertEqual(response.status_code, 200)

    def test_notification_preferences_are_returned_and_can_be_updated(self):
        token = self.login()
        profile_response = self.client.get(
            reverse("users:profile"), HTTP_AUTHORIZATION=f"Bearer {token}"
        )
        self.assertTrue(
            profile_response.json()["user"]["notification_preferences"][
                "email_new_match"
            ]
        )

        response = self.client.patch(
            reverse("users:notification-preferences"),
            data=json.dumps(
                {
                    "email_new_match": False,
                    "email_approvals": True,
                    "in_app_match": False,
                    "in_app_messages": True,
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        preferences = response.json()["user"]["notification_preferences"]
        self.assertFalse(preferences["email_new_match"])
        self.assertFalse(preferences["in_app_match"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.notify_email_new_match)

    def test_notification_preferences_reject_non_boolean_values(self):
        token = self.login()
        response = self.client.patch(
            reverse("users:notification-preferences"),
            data=json.dumps({"email_new_match": "false"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_logout_revokes_token(self):
        token = self.login()
        response = self.post_json(reverse("users:logout"), {}, token)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AccessToken.objects.exists())

    def test_password_reset_flow(self):
        response = self.post_json(
            reverse("users:password-reset"), {"email": self.user.email}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        match = re.search(r"uid=([^&\s]+)&token=([^\s]+)", mail.outbox[0].body)
        self.assertIsNotNone(match)
        new_password = "Reset-safe-pass-7351"
        response = self.post_json(
            reverse("users:password-reset-confirm"),
            {
                "uid": match.group(1),
                "token": match.group(2),
                "new_password": new_password,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
