from django.contrib import admin

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


@admin.register(RecipientProfile)
class RecipientProfileAdmin(admin.ModelAdmin):
    list_display = ("person", "status", "waiting_since", "medical_urgency", "transplant_candidate")
    list_filter = ("status", "transplant_candidate", "donor_living", "donor_deceased")
    search_fields = ("person__identifier", "person__first_name", "person__last_name")


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ("person", "status", "is_related_recipient_candidate", "preferred_recipient")
    list_filter = ("status", "is_related_recipient_candidate")
    search_fields = ("person__identifier", "person__first_name", "person__last_name")


@admin.register(HLATyping)
class HLATypingAdmin(admin.ModelAdmin):
    list_display = ("person", "updated_at")
    search_fields = ("person__identifier", "person__first_name", "person__last_name")


@admin.register(HLASelection)
class HLASelectionAdmin(admin.ModelAdmin):
    list_display = ("typing", "locus", "allele", "copy_number")
    list_filter = ("locus",)
    search_fields = ("typing__person__identifier", "allele")


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
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
class CdcPraTestAdmin(admin.ModelAdmin):
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
class AntiHlaTestAdmin(admin.ModelAdmin):
    list_display = ("person", "performed_at", "expires_at", "is_expired")
    list_filter = ("performed_at", "expires_at")
    search_fields = ("person__identifier", "person__first_name", "person__last_name")
    readonly_fields = ("expires_at", "created_at", "updated_at")


@admin.register(AntiHlaSelection)
class AntiHlaSelectionAdmin(admin.ModelAdmin):
    list_display = ("test", "hla_class", "locus", "antigen", "mfi")
    list_filter = ("hla_class", "locus")
    search_fields = ("test__person__identifier", "antigen")


@admin.register(MedicalApproval)
class MedicalApprovalAdmin(admin.ModelAdmin):
    list_display = ("person", "specialty", "status", "approval_date", "doctor_name")
    list_filter = ("specialty", "status")
    search_fields = ("person__identifier", "doctor_name", "medical_code")


@admin.register(ClinicalStateEvent)
class ClinicalStateEventAdmin(admin.ModelAdmin):
    list_display = ("entity_type", "previous_status", "new_status", "actor", "created_at")
    list_filter = ("entity_type", "new_status", "created_at")
    search_fields = ("recipient__person__identifier", "donor__person__identifier", "reason")
    readonly_fields = tuple(field.name for field in ClinicalStateEvent._meta.fields)


@admin.register(AllocationPolicy)
class AllocationPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "is_active", "updated_at")
    list_filter = ("is_active",)


@admin.register(MatchingRun)
class MatchingRunAdmin(admin.ModelAdmin):
    list_display = ("id", "trigger", "status", "policy", "started_at", "finished_at")
    list_filter = ("trigger", "status")
    readonly_fields = ("started_at", "finished_at")


@admin.register(MatchProposal)
class MatchProposalAdmin(admin.ModelAdmin):
    list_display = ("recipient", "donor", "compatibility", "decision", "rank", "final_score")
    list_filter = ("compatibility", "decision")
    search_fields = ("recipient__person__identifier", "donor__person__identifier")


@admin.register(CrossMatchRequest)
class CrossMatchRequestAdmin(admin.ModelAdmin):
    list_display = ("recipient", "donor", "status", "requested_by", "created_at")
    list_filter = ("status", "created_at")


@admin.register(InAppNotification)
class InAppNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "title", "read_at", "created_at")
    list_filter = ("kind", "read_at")


@admin.register(SensitiveDataAccessLog)
class SensitiveDataAccessLogAdmin(admin.ModelAdmin):
    list_display = ("user", "person", "data_type", "purpose", "source_ip", "created_at")
    list_filter = ("data_type", "created_at")
    readonly_fields = tuple(field.name for field in SensitiveDataAccessLog._meta.fields)
    ClinicalStateEvent,
    CrossMatchRequest,
    InAppNotification,
    MatchProposal,
    MatchingRun,
