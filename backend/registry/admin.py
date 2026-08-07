from django.contrib import admin
from django.contrib.admin.utils import get_deleted_objects
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    AllocationPolicy,
    AntiHlaSelection,
    AntiHlaTest,
    ClinicalStateEvent,
    CdcPraTest,
    CrossMatchRequest,
    DonorProfile,
    HLASelection,
    HLATyping,
    InAppNotification,
    LabTest,
    MatchProposal,
    MatchingRun,
    MedicalApproval,
    Person,
    RecipientProfile,
    SensitiveDataAccessLog,
)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "first_name",
        "last_name",
        "blood_group",
        "phone",
        "center",
        "created_at",
    )
    list_filter = ("citizenship", "gender", "blood_group", "center")
    search_fields = ("identifier", "first_name", "last_name", "phone")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50

    @admin.display(description="نقش پرونده")
    def clinical_roles(self, obj):
        roles = []
        if hasattr(obj, "recipient_profile"):
            roles.append("گیرنده")
        if hasattr(obj, "donor_profile"):
            roles.append("اهداکننده")
        return "، ".join(roles) or "بدون نقش"

    def get_list_display(self, request):
        return (*super().get_list_display(request), "clinical_roles")


class ClinicalProfileAdminMixin:
    """Shared manager-facing presentation for recipient and donor records."""

    list_select_related = ("person", "person__center")
    list_per_page = 50
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="کد ملی / شناسه", ordering="person__identifier")
    def identifier(self, obj):
        return obj.person.identifier

    @admin.display(description="نام و نام خانوادگی", ordering="person__last_name")
    def person_link(self, obj):
        url = reverse("admin:registry_person_change", args=(obj.person_id,))
        return format_html('<a href="{}">{}</a>', url, obj.person.full_name)

    @admin.display(description="مرکز", ordering="person__center__name")
    def center(self, obj):
        return obj.person.center or "—"

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            action, name, _description = actions["delete_selected"]
            actions["delete_selected"] = (
                action,
                name,
                "حذف کامل پرونده‌های انتخاب‌شده و داده‌های وابسته",
            )
        return actions

    def get_deleted_objects(self, objs, request):
        person_ids = [obj.person_id for obj in objs]
        people = Person.objects.filter(pk__in=person_ids)
        return get_deleted_objects(people, request, self.admin_site)

    def delete_model(self, request, obj):
        # A clinical profile is not an independent account: deleting it from
        # the manager UI must remove its Person and all CASCADE-owned clinical
        # data, otherwise the unique identifier blocks re-registration.
        obj.person.delete()

    def delete_queryset(self, request, queryset):
        person_ids = list(queryset.values_list("person_id", flat=True))
        Person.objects.filter(pk__in=person_ids).delete()


class AdvancedAdminMixin:
    """Keep specialist/audit tools off the simplified manager dashboard."""

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(RecipientProfile)
class RecipientProfileAdmin(ClinicalProfileAdminMixin, admin.ModelAdmin):
    list_display = (
        "identifier",
        "person_link",
        "center",
        "status",
        "waiting_since",
        "medical_urgency",
        "is_emergency",
        "transplant_candidate",
    )
    list_filter = (
        "status",
        "is_emergency",
        "transplant_candidate",
        "donor_living",
        "donor_deceased",
        "person__center",
    )
    search_fields = ("person__identifier", "person__first_name", "person__last_name")
    date_hierarchy = "created_at"
    fieldsets = (
        (
            "مدیریت لیست انتظار",
            {
                "fields": (
                    "person",
                    "status",
                    "waiting_since",
                    "medical_urgency",
                    "regional_disadvantage",
                    "is_emergency",
                    "emergency_reason",
                )
            },
        ),
        (
            "جزئیات بالینی",
            {
                "classes": ("collapse",),
                "fields": (
                    "transplant_candidate",
                    "donor_living",
                    "donor_deceased",
                    "has_dialysis_history",
                    "dialysis_type",
                    "dialysis_start_date",
                    "has_blood_transfusion",
                    "blood_transfusion_units",
                    "has_pregnancy_history",
                    "pregnancy_count",
                    "has_abortion_history",
                    "abortion_count",
                    "previous_transplant",
                    "previous_transplant_details",
                    "drug_history",
                    "has_drug_allergy",
                    "drug_allergy_details",
                    "underlying_diseases",
                    "family_kidney_disease",
                    "family_kidney_disease_details",
                ),
            },
        ),
        ("اطلاعات سیستمی", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )


@admin.register(DonorProfile)
class DonorProfileAdmin(ClinicalProfileAdminMixin, admin.ModelAdmin):
    list_display = (
        "identifier",
        "person_link",
        "center",
        "status",
        "is_related_recipient_candidate",
        "preferred_recipient",
    )
    list_filter = ("status", "is_related_recipient_candidate", "person__center")
    search_fields = ("person__identifier", "person__first_name", "person__last_name")
    date_hierarchy = "created_at"
    fieldsets = (
        ("مدیریت لیست انتظار", {"fields": ("person", "status")}),
        (
            "جزئیات بالینی و ارتباط با گیرنده",
            {
                "classes": ("collapse",),
                "fields": (
                    "self_diabetes_history",
                    "self_hypertension_history",
                    "parent_diabetes_history",
                    "parent_hypertension_history",
                    "has_drug_allergy",
                    "drug_allergy_details",
                    "is_related_recipient_candidate",
                    "preferred_recipient",
                    "recipient_relationship_group",
                    "recipient_relationship_kind",
                    "recipient_relationship_details",
                ),
            },
        ),
        ("اطلاعات سیستمی", {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )


@admin.register(HLATyping)
class HLATypingAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("person", "updated_at")
    search_fields = ("person__identifier", "person__first_name", "person__last_name")


@admin.register(HLASelection)
class HLASelectionAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("typing", "locus", "allele", "copy_number")
    list_filter = ("locus",)
    search_fields = ("typing__person__identifier", "allele")


@admin.register(LabTest)
class LabTestAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = (
        "person",
        "kind",
        "name",
        "performed_at",
        "expires_at",
        "is_expired",
    )
    list_filter = ("kind", "performed_at", "expires_at")
    search_fields = ("person__identifier", "person__first_name", "person__last_name", "name")
    readonly_fields = ("expires_at", "created_at", "updated_at")


@admin.register(CdcPraTest)
class CdcPraTestAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = (
        "person",
        "performed_at",
        "class_i_status",
        "class_ii_status",
        "expires_at",
        "is_expired",
    )
    list_filter = ("class_i_status", "class_ii_status", "performed_at", "expires_at")
    search_fields = ("person__identifier", "person__first_name", "person__last_name")
    readonly_fields = ("expires_at", "created_at", "updated_at")


@admin.register(AntiHlaTest)
class AntiHlaTestAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("person", "performed_at", "expires_at", "is_expired")
    list_filter = ("performed_at", "expires_at")
    search_fields = ("person__identifier", "person__first_name", "person__last_name")
    readonly_fields = ("expires_at", "created_at", "updated_at")


@admin.register(AntiHlaSelection)
class AntiHlaSelectionAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("test", "hla_class", "locus", "antigen", "mfi")
    list_filter = ("hla_class", "locus")
    search_fields = ("test__person__identifier", "antigen")


@admin.register(MedicalApproval)
class MedicalApprovalAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("person", "specialty", "status", "approval_date", "doctor_name")
    list_filter = ("specialty", "status")
    search_fields = ("person__identifier", "doctor_name", "medical_code")


@admin.register(ClinicalStateEvent)
class ClinicalStateEventAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("entity_type", "previous_status", "new_status", "actor", "created_at")
    list_filter = ("entity_type", "new_status", "created_at")
    search_fields = ("recipient__person__identifier", "donor__person__identifier", "reason")
    readonly_fields = tuple(field.name for field in ClinicalStateEvent._meta.fields)


@admin.register(AllocationPolicy)
class AllocationPolicyAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("name", "version", "is_active", "updated_at")
    list_filter = ("is_active",)


@admin.register(MatchingRun)
class MatchingRunAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("id", "trigger", "status", "policy", "started_at", "finished_at")
    list_filter = ("trigger", "status")
    readonly_fields = ("started_at", "finished_at")


@admin.register(MatchProposal)
class MatchProposalAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("recipient", "donor", "compatibility", "decision", "rank", "final_score")
    list_filter = ("compatibility", "decision")
    search_fields = ("recipient__person__identifier", "donor__person__identifier")


@admin.register(CrossMatchRequest)
class CrossMatchRequestAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("recipient", "donor", "status", "requested_by", "created_at")
    list_filter = ("status", "created_at")


@admin.register(InAppNotification)
class InAppNotificationAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = ("user", "kind", "title", "read_at", "created_at")
    list_filter = ("kind", "read_at")


@admin.register(SensitiveDataAccessLog)
class SensitiveDataAccessLogAdmin(AdvancedAdminMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "person_reference",
        "data_type",
        "purpose",
        "source_ip",
        "created_at",
    )
    list_filter = ("data_type", "created_at")
    search_fields = ("person_identifier", "person__identifier", "user__username")
    readonly_fields = tuple(field.name for field in SensitiveDataAccessLog._meta.fields)

    @admin.display(description="شناسه فرد", ordering="person_identifier")
    def person_reference(self, obj):
        return obj.person or obj.person_identifier or "—"
    ClinicalStateEvent,
    CrossMatchRequest,
    InAppNotification,
    MatchProposal,
    MatchingRun,
