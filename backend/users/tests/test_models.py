from django.contrib import admin
from django.test import TestCase

from users.models import Center, User


class UserModelTests(TestCase):
    def test_models_are_registered_in_admin(self):
        self.assertIn(User, admin.site._registry)
        self.assertIn(Center, admin.site._registry)

    def test_center_string_representation(self):
        center = Center(name="مرکز پیوند شیراز")
        self.assertEqual(str(center), "مرکز پیوند شیراز")
