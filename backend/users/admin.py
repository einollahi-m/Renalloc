from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AccessToken, Center, User


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(User)
class CoordinatorAdmin(UserAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "national_id",
        "email",
        "mobile_phone",
        "center",
        "coordinator_level",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "coordinator_level", "is_active", "is_staff", "is_superuser", "gender", "center"
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "national_id",
        "email",
        "mobile_phone",
    )
    fieldsets = UserAdmin.fieldsets + (
        (
            "اطلاعات هماهنگ‌کننده پیوند",
            {
                "fields": (
                    "national_id", "gender", "mobile_phone", "center", "coordinator_level"
                )
            },
        ),
        (
            "تنظیمات اعلان‌ها",
            {
                "fields": (
                    "notify_email_new_match",
                    "notify_email_approvals",
                    "notify_in_app_match",
                    "notify_in_app_messages",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "اطلاعات هماهنگ‌کننده پیوند",
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "national_id",
                    "email",
                    "gender",
                    "mobile_phone",
                    "center",
                    "coordinator_level",
                ),
            },
        ),
    )


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "last_used_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "key_hash", "created_at", "expires_at", "last_used_at")

    def has_add_permission(self, request):
        return False
