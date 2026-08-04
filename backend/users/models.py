import hashlib
import secrets

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower


class Center(models.Model):
    name = models.CharField("نام مرکز", max_length=255, unique=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ ویرایش", auto_now=True)

    class Meta:
        verbose_name = "مرکز"
        verbose_name_plural = "مراکز"
        ordering = ("name",)

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = "male", "مرد"
        FEMALE = "female", "زن"

    first_name = models.CharField("نام", max_length=150)
    last_name = models.CharField("نام خانوادگی", max_length=150)
    national_id = models.CharField(
        "کد ملی",
        max_length=10,
        unique=True,
        validators=[RegexValidator(r"^[0-9]{10}$", "کد ملی باید دقیقاً ۱۰ رقم باشد.")],
    )
    email = models.EmailField("ایمیل", unique=True)
    gender = models.CharField("جنسیت", max_length=6, choices=Gender.choices)
    mobile_phone = models.CharField(
        "شماره همراه",
        max_length=11,
        validators=[RegexValidator(r"^09[0-9]{9}$", "شماره همراه معتبر نیست.")],
    )
    center = models.ForeignKey(
        Center,
        verbose_name="مرکز",
        related_name="coordinators",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    notify_email_new_match = models.BooleanField(
        "ایمیل تطابق جدید", default=True
    )
    notify_email_approvals = models.BooleanField(
        "ایمیل یادآوری تأییدیه‌ها", default=True
    )
    notify_in_app_match = models.BooleanField(
        "اعلان درون‌برنامه‌ای تطابق", default=True
    )
    notify_in_app_messages = models.BooleanField(
        "اعلان درون‌برنامه‌ای پیام‌ها", default=True
    )

    REQUIRED_FIELDS = [
        "email",
        "national_id",
        "first_name",
        "last_name",
        "gender",
        "mobile_phone",
    ]

    class Meta(AbstractUser.Meta):
        verbose_name = "کاربر (هماهنگ‌کننده پیوند)"
        verbose_name_plural = "کاربران (هماهنگ‌کنندگان پیوند)"
        constraints = [
            models.UniqueConstraint(Lower("username"), name="users_username_ci_unique"),
            models.UniqueConstraint(Lower("email"), name="users_email_ci_unique"),
        ]

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email).lower()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return self.get_full_name().strip() or self.username


class AccessToken(models.Model):
    user = models.ForeignKey(
        User, related_name="access_tokens", on_delete=models.CASCADE
    )
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    @staticmethod
    def hash_key(raw_key):
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def issue(cls, user, expires_at):
        raw_key = secrets.token_urlsafe(32)
        token = cls.objects.create(
            user=user, key_hash=cls.hash_key(raw_key), expires_at=expires_at
        )
        return raw_key, token

    def __str__(self):
        return f"token:{self.user_id}:{self.created_at.isoformat()}"
