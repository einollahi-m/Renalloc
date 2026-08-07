from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q


MANAGER_GROUP_NAME = "مدیر پرونده‌های پیوند"


class Command(BaseCommand):
    help = "اعطای دسترسی پنل Django Admin برای مدیریت پرونده‌های پیوند"

    def add_arguments(self, parser):
        parser.add_argument(
            "identity",
            help="نام کاربری یا ایمیل کاربر موجود",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        identity = str(options["identity"]).strip()
        user_model = get_user_model()
        user = user_model.objects.filter(
            Q(username__iexact=identity) | Q(email__iexact=identity)
        ).first()
        if user is None:
            raise CommandError("کاربری با این نام کاربری یا ایمیل یافت نشد.")

        group, _created = Group.objects.get_or_create(name=MANAGER_GROUP_NAME)
        permissions = Permission.objects.filter(
            content_type__app_label="registry",
            codename__regex=r"^(view|change|delete)_",
        )
        group.permissions.set(permissions)
        user.groups.add(group)
        if not user.is_staff:
            user.is_staff = True
            user.save(update_fields=("is_staff",))

        self.stdout.write(
            self.style.SUCCESS(
                f"دسترسی مدیر پرونده‌ها برای {user.username} فعال شد؛ مسیر ورود: /admin/"
            )
        )
