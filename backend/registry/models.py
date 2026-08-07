import uuid
from calendar import monthrange
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from users.models import Center

from .choices import (
    ANTI_HLA_ANTIGEN_CHOICES,
    ANTI_HLA_VALUES_BY_LOCUS,
    HLA_ALLELE_CHOICES,
    HLA_VALUES_BY_LOCUS,
    LAB_CATEGORY_CHOICES,
    LAB_TEST_NAME_CHOICES,
    ROUTINE_TEST_NAMES,
    VIRAL_TEST_NAMES,
    AntiHLALocus,
    HLAClass,
    HLALocus,
    RoutineCategory,
)
from .validators import (
    normalize_digits,
    normalize_mobile,
    normalize_national_id,
    validate_iranian_mobile,
    validate_iranian_national_id,
)


def add_calendar_months(value, months):
    """Add calendar months while keeping end-of-month dates valid."""
    target_month = value.month - 1 + months
    year = value.year + target_month // 12
    month = target_month % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def default_locus_weights():
    return {"A": 1, "B": 1, "C": 0.5, "DRB1": 1, "DQB1": 1}


class Person(models.Model):
    class Citizenship(models.TextChoices):
        IRANIAN = "iranian", "ایرانی"
        FOREIGN = "foreign", "غیر ایرانی"

    class Gender(models.TextChoices):
        MALE = "male", "مرد"
        FEMALE = "female", "زن"

    class BloodGroup(models.TextChoices):
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"

    class Education(models.TextChoices):
        BELOW_DIPLOMA = "below_diploma", "زیر دیپلم"
        DIPLOMA = "diploma", "دیپلم"
        BACHELOR = "bachelor", "کاردانی/کارشناسی"
        POSTGRADUATE = "postgraduate", "تحصیلات تکمیلی"

    class MaritalStatus(models.TextChoices):
        SINGLE = "single", "مجرد"
        MARRIED = "married", "متأهل"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizenship = models.CharField(max_length=8, choices=Citizenship.choices)
    identifier = models.CharField(
        "کد ملی یا شماره گذرنامه", max_length=40, unique=True
    )
    first_name = models.CharField("نام", max_length=150)
    last_name = models.CharField("نام خانوادگی", max_length=150)
    gender = models.CharField("جنسیت", max_length=6, choices=Gender.choices)
    birth_date = models.DateField("تاریخ تولد")
    blood_group = models.CharField(
        "گروه خونی و Rh", max_length=3, choices=BloodGroup.choices
    )
    phone = models.CharField(
        "شماره موبایل", max_length=11, validators=[validate_iranian_mobile]
    )
    emergency_contact_phone = models.CharField(
        "شماره موبایل اضطراری",
        max_length=11,
        blank=True,
        validators=[validate_iranian_mobile],
    )
    nationality = models.CharField("ملیت", max_length=100, blank=True)
    education = models.CharField(
        "تحصیلات", max_length=20, choices=Education.choices, blank=True
    )
    insurance = models.JSONField("بیمه‌ها", default=list, blank=True)
    marital_status = models.CharField(
        "وضعیت تأهل", max_length=10, choices=MaritalStatus.choices, blank=True
    )
    weight_kg = models.DecimalField(
        "وزن (کیلوگرم)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(500)],
    )
    height_cm = models.DecimalField(
        "قد (سانتی‌متر)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
    )
    is_smoker = models.BooleanField("سیگاری", default=False)
    has_addiction = models.BooleanField("سابقه اعتیاد", default=False)
    has_alcohol = models.BooleanField("مصرف الکل", default=False)
    is_active = models.BooleanField("فعال", default=True)
    center = models.ForeignKey(
        Center,
        related_name="registered_people",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="registered_people",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "فرد"
        verbose_name_plural = "افراد"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("last_name", "first_name"), name="registry_person_name_idx"),
            models.Index(fields=("center", "created_at"), name="registry_person_center_idx"),
        ]

    def clean(self):
        super().clean()
        self.identifier = str(self.identifier or "").strip().upper()
        self.phone = normalize_mobile(self.phone)
        self.emergency_contact_phone = normalize_mobile(self.emergency_contact_phone)

        errors = {}
        if self.citizenship == self.Citizenship.IRANIAN:
            self.identifier = normalize_national_id(self.identifier)
            try:
                validate_iranian_national_id(self.identifier)
            except ValidationError as exc:
                errors["identifier"] = exc.messages
            self.nationality = ""
        elif not self.nationality:
            errors["nationality"] = ["ملیت برای فرد غیر ایرانی الزامی است."]

        if self.birth_date and self.birth_date > timezone.localdate():
            errors["birth_date"] = ["تاریخ تولد نمی‌تواند در آینده باشد."]
        if not isinstance(self.insurance, list):
            errors["insurance"] = ["بیمه باید به‌صورت فهرست ارسال شود."]
        if errors:
            raise ValidationError(errors)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.full_name} ({self.identifier})"


class RecipientProfile(models.Model):
    class Status(models.TextChoices):
        REGISTERED = "registered", "ثبت‌نام اولیه"
        PENDING_DOCUMENTS = "pending_documents", "در انتظار تأیید مدارک"
        REJECTED = "rejected", "رد شده"
        ACTIVE = "active", "فعال در لیست انتظار"
        MATCH_CANDIDATE = "match_candidate", "کاندیدای تطبیق"
        AWAITING_CROSSMATCH = "awaiting_crossmatch", "در انتظار Cross-Match"
        AWAITING_HIGH_RESOLUTION = "awaiting_high_resolution", "در انتظار High-Resolution"
        READY = "ready", "آماده پیوند"
        TRANSPLANTED = "transplanted", "پیوند انجام شد"
        FOLLOW_UP = "follow_up", "پیگیری پس از پیوند"
        TEMPORARILY_INACTIVE = "temporarily_inactive", "غیرفعال موقت"
        REMOVED = "removed", "حذف از لیست انتظار"

    class TransplantCandidate(models.TextChoices):
        FIRST = "1st", "پیوند اول"
        SECOND = "2nd", "پیوند دوم"
        THIRD = "3rd", "پیوند سوم"
        FOURTH = "4th", "پیوند چهارم"

    class DialysisType(models.TextChoices):
        HEMODIALYSIS = "hemodialysis", "همودیالیز"
        PERITONEAL = "peritoneal", "دیالیز صفاقی"

    person = models.OneToOneField(
        Person,
        primary_key=True,
        related_name="recipient_profile",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PENDING_DOCUMENTS
    )
    waiting_since = models.DateField(null=True, blank=True)
    medical_urgency = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    regional_disadvantage = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_emergency = models.BooleanField(default=False)
    emergency_reason = models.TextField(blank=True)
    transplant_candidate = models.CharField(
        max_length=3, choices=TransplantCandidate.choices, blank=True
    )
    donor_living = models.BooleanField(default=False)
    donor_deceased = models.BooleanField(default=False)
    has_dialysis_history = models.BooleanField(default=False)
    dialysis_type = models.CharField(
        max_length=20, choices=DialysisType.choices, blank=True
    )
    dialysis_start_date = models.DateField(null=True, blank=True)
    has_blood_transfusion = models.BooleanField(default=False)
    blood_transfusion_units = models.PositiveSmallIntegerField(null=True, blank=True)
    has_pregnancy_history = models.BooleanField(default=False)
    pregnancy_count = models.PositiveSmallIntegerField(null=True, blank=True)
    has_abortion_history = models.BooleanField(default=False)
    abortion_count = models.PositiveSmallIntegerField(null=True, blank=True)
    previous_transplant = models.BooleanField(default=False)
    previous_transplant_details = models.TextField(blank=True)
    drug_history = models.TextField(blank=True)
    has_drug_allergy = models.BooleanField(default=False)
    drug_allergy_details = models.TextField(blank=True)
    underlying_diseases = models.TextField(blank=True)
    family_kidney_disease = models.BooleanField(default=False)
    family_kidney_disease_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پرونده گیرنده"
        verbose_name_plural = "پرونده‌های گیرندگان"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(donor_living=True) | models.Q(donor_deceased=True),
                name="registry_recipient_has_donor_source",
            )
        ]
        indexes = [
            models.Index(fields=("status", "waiting_since"), name="registry_rec_wait_idx"),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if not self.donor_living and not self.donor_deceased:
            errors["donor_living"] = ["حداقل یک منبع اهداکننده باید انتخاب شود."]
        if self.is_emergency and not str(self.emergency_reason or "").strip():
            errors["emergency_reason"] = ["شرح شرایط اورژانسی الزامی است."]
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"گیرنده: {self.person}"


class DonorProfile(models.Model):
    class Status(models.TextChoices):
        REGISTERED = "registered", "ثبت‌نام اولیه"
        MEDICAL_SCREENING = "medical_screening", "در غربالگری پزشکی"
        AVAILABLE = "available", "در دسترس برای Matching"
        MATCH_CANDIDATE = "match_candidate", "کاندیدای اهدا"
        AWAITING_CROSSMATCH = "awaiting_crossmatch", "در انتظار Cross-Match"
        READY = "ready", "آماده عمل"
        DONATED = "donated", "اهدا انجام شد"
        FOLLOW_UP = "follow_up", "پیگیری پس از اهدا"
        RESERVED = "reserved", "رزرو شده برای گیرنده خاص"
        SUSPENDED = "suspended", "معلق"
        PERMANENT_DEFERRAL = "permanent_deferral", "منع دائم پزشکی"

    class RelationshipGroup(models.TextChoices):
        FIRST_DEGREE = "first_degree", "درجه اول"
        SECOND_DEGREE = "second_degree", "درجه دوم"
        STRANGER = "stranger", "غریبه"

    class RelationshipKind(models.TextChoices):
        FATHER = "father", "پدر"
        MOTHER = "mother", "مادر"
        BROTHER = "brother", "برادر"
        SISTER = "sister", "خواهر"
        CHILD = "child", "فرزند"
        SPOUSE = "spouse", "همسر"

    person = models.OneToOneField(
        Person,
        primary_key=True,
        related_name="donor_profile",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.MEDICAL_SCREENING
    )
    self_diabetes_history = models.BooleanField(default=False)
    self_hypertension_history = models.BooleanField(default=False)
    parent_diabetes_history = models.BooleanField(default=False)
    parent_hypertension_history = models.BooleanField(default=False)
    has_drug_allergy = models.BooleanField(default=False)
    drug_allergy_details = models.TextField(blank=True)
    is_related_recipient_candidate = models.BooleanField(default=False)
    preferred_recipient = models.ForeignKey(
        RecipientProfile,
        related_name="preferred_donors",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    recipient_relationship_group = models.CharField(
        max_length=20, choices=RelationshipGroup.choices, blank=True
    )
    recipient_relationship_kind = models.CharField(
        max_length=12, choices=RelationshipKind.choices, blank=True
    )
    recipient_relationship_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پرونده اهداکننده"
        verbose_name_plural = "پرونده‌های اهداکنندگان"
        indexes = [
            models.Index(fields=("status", "updated_at"), name="registry_donor_status_idx"),
        ]

    def __str__(self):
        return f"اهداکننده: {self.person}"


class HLATyping(models.Model):
    person = models.OneToOneField(
        Person,
        primary_key=True,
        related_name="hla_typing",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تایپ HLA"
        verbose_name_plural = "تایپ‌های HLA"

    def __str__(self):
        return f"HLA: {self.person}"


class HLASelection(models.Model):
    typing = models.ForeignKey(
        HLATyping, related_name="selections", on_delete=models.CASCADE
    )
    locus = models.CharField(max_length=4, choices=HLALocus.choices)
    allele = models.CharField(max_length=20, choices=HLA_ALLELE_CHOICES)
    copy_number = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(2)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "آلل انتخاب‌شده HLA"
        verbose_name_plural = "آلل‌های انتخاب‌شده HLA"
        ordering = ("locus", "allele")
        constraints = [
            models.UniqueConstraint(
                fields=("typing", "locus", "allele"),
                name="registry_hla_selection_unique",
            )
        ]
        indexes = [
            models.Index(fields=("locus", "allele", "typing"), name="registry_hla_inverted_idx"),
        ]

    def clean(self):
        super().clean()
        if self.allele not in HLA_VALUES_BY_LOCUS.get(self.locus, ()):
            raise ValidationError(
                {"allele": "آلل انتخاب‌شده برای این locus معتبر نیست."}
            )
        if self.typing_id:
            existing_copies = sum(
                self.__class__.objects.filter(
                    typing_id=self.typing_id, locus=self.locus
                )
                .exclude(pk=self.pk)
                .values_list("copy_number", flat=True)
            )
            if existing_copies + self.copy_number > 2:
                raise ValidationError(
                    {"allele": "برای هر locus حداکثر دو آلل قابل انتخاب است."}
                )

    def __str__(self):
        return f"{self.locus}: {self.allele}"


class LabTestQuerySet(models.QuerySet):
    def valid_on(self, date=None):
        return self.filter(expires_at__gte=date or timezone.localdate())

    def expired_on(self, date=None):
        return self.filter(expires_at__lt=date or timezone.localdate())


class ExpiringTestMixin:
    VALIDITY_MONTHS = 6

    @classmethod
    def expiry_for(cls, performed_at):
        return add_calendar_months(performed_at, cls.VALIDITY_MONTHS)

    def clean(self):
        super().clean()
        if self.performed_at:
            expected = self.expiry_for(self.performed_at)
            if self.expires_at and self.expires_at != expected:
                raise ValidationError(
                    {"expires_at": "تاریخ اعتبار باید دقیقاً شش ماه پس از آزمایش باشد."}
                )
            self.expires_at = expected

    def save(self, *args, **kwargs):
        if self.performed_at:
            self.expires_at = self.expiry_for(self.performed_at)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.expires_at < timezone.localdate()


class LabTest(ExpiringTestMixin, models.Model):

    class Kind(models.TextChoices):
        ROUTINE = "routine", "آزمایش روتین"
        VIRAL = "viral", "آزمایش ویروسی"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(
        Person, related_name="lab_tests", on_delete=models.CASCADE
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    category = models.CharField(max_length=120, choices=LAB_CATEGORY_CHOICES)
    name = models.CharField(max_length=160, choices=LAB_TEST_NAME_CHOICES)
    result = models.JSONField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    batch_key = models.CharField(max_length=160, blank=True)
    performed_at = models.DateField()
    expires_at = models.DateField(editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="registered_lab_tests",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LabTestQuerySet.as_manager()

    class Meta:
        verbose_name = "نتیجه آزمایش"
        verbose_name_plural = "نتایج آزمایش‌ها"
        ordering = ("-performed_at", "kind", "category", "name")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expires_at__gte=models.F("performed_at")),
                name="registry_lab_expiry_after_performed",
            ),
            models.UniqueConstraint(
                fields=("person", "kind", "performed_at", "category", "name"),
                name="registry_lab_result_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=("person", "kind", "expires_at"),
                name="registry_lab_validity_idx",
            )
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.kind == self.Kind.ROUTINE:
            if self.name not in ROUTINE_TEST_NAMES:
                errors["name"] = ["نام آزمایش روتین معتبر نیست."]
            if self.category not in RoutineCategory.values:
                errors["category"] = ["دسته‌بندی آزمایش روتین معتبر نیست."]
        elif self.kind == self.Kind.VIRAL:
            if self.name not in VIRAL_TEST_NAMES:
                errors["name"] = ["نام آزمایش ویروسی معتبر نیست."]
            if self.category != "آزمایش ویروسی":
                errors["category"] = ["دسته‌بندی آزمایش ویروسی معتبر نیست."]
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.get_kind_display()} - {self.name} - {self.person}"


class CdcPraTest(ExpiringTestMixin, models.Model):
    class ResultStatus(models.TextChoices):
        POSITIVE = "positive", "مثبت"
        NEGATIVE = "negative", "منفی"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(
        Person, related_name="cdc_pra_tests", on_delete=models.CASCADE
    )
    performed_at = models.DateField()
    expires_at = models.DateField(editable=False)
    class_i_status = models.CharField(max_length=8, choices=ResultStatus.choices)
    class_i_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    class_i_effective_status = models.CharField(
        max_length=8, choices=ResultStatus.choices
    )
    class_i_implicitly_negative = models.BooleanField(default=False)
    class_ii_status = models.CharField(max_length=8, choices=ResultStatus.choices)
    class_ii_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    class_ii_effective_status = models.CharField(
        max_length=8, choices=ResultStatus.choices
    )
    class_ii_implicitly_negative = models.BooleanField(default=False)
    implicitly_negative = models.BooleanField(default=False)
    antibody_count = models.PositiveSmallIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="registered_cdc_pra_tests",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "آزمایش CDC PRA"
        verbose_name_plural = "آزمایش‌های CDC PRA"
        ordering = ("-performed_at", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("person", "performed_at"),
                name="registry_cdc_person_date_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(expires_at__gte=models.F("performed_at")),
                name="registry_cdc_expiry_after_performed",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        for prefix in ("class_i", "class_ii"):
            status = getattr(self, f"{prefix}_status")
            value = getattr(self, f"{prefix}_value")
            if status == self.ResultStatus.POSITIVE and value is None:
                errors[f"{prefix}_value"] = ["برای نتیجه مثبت، درصد PRA الزامی است."]
            if status == self.ResultStatus.NEGATIVE and value is not None:
                setattr(self, f"{prefix}_value", None)
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"CDC PRA - {self.performed_at} - {self.person}"


class AntiHlaTest(ExpiringTestMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(
        Person, related_name="anti_hla_tests", on_delete=models.CASCADE
    )
    performed_at = models.DateField()
    expires_at = models.DateField(editable=False)
    class_i_negative = models.BooleanField(default=False)
    class_ii_negative = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="registered_anti_hla_tests",
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "آزمایش Anti-HLA"
        verbose_name_plural = "آزمایش‌های Anti-HLA"
        ordering = ("-performed_at", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("person", "performed_at"),
                name="registry_anti_hla_person_date_unique",
            ),
            models.CheckConstraint(
                condition=models.Q(expires_at__gte=models.F("performed_at")),
                name="registry_anti_hla_expiry_after_performed",
            ),
        ]

    def __str__(self):
        return f"Anti-HLA - {self.performed_at} - {self.person}"


class AntiHlaSelection(models.Model):
    test = models.ForeignKey(
        AntiHlaTest, related_name="selections", on_delete=models.CASCADE
    )
    hla_class = models.CharField(max_length=2, choices=HLAClass.choices)
    locus = models.CharField(max_length=4, choices=AntiHLALocus.choices)
    antigen = models.CharField(max_length=20, choices=ANTI_HLA_ANTIGEN_CHOICES)
    mfi = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "آنتی‌ژن انتخاب‌شده Anti-HLA"
        verbose_name_plural = "آنتی‌ژن‌های انتخاب‌شده Anti-HLA"
        ordering = ("hla_class", "locus", "antigen")
        constraints = [
            models.UniqueConstraint(
                fields=("test", "locus", "antigen"),
                name="registry_anti_hla_selection_unique",
            )
        ]
        indexes = [
            models.Index(
                fields=("locus", "antigen", "test"),
                name="registry_antihla_inv_idx",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.antigen not in ANTI_HLA_VALUES_BY_LOCUS.get(self.locus, ()):
            errors["antigen"] = ["آنتی‌ژن برای این locus معتبر نیست."]
        expected_class = (
            HLAClass.CLASS_I
            if self.locus in {AntiHLALocus.A, AntiHLALocus.B, AntiHLALocus.C}
            else HLAClass.CLASS_II
        )
        if self.hla_class != expected_class:
            errors["hla_class"] = ["کلاس HLA با locus انتخاب‌شده سازگار نیست."]
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.locus}: {self.antigen}"


class MedicalApproval(models.Model):
    class Status(models.TextChoices):
        APPROVED = "approved", "تأیید"
        REJECTED = "rejected", "رد"
        ON_HOLD = "on_hold", "در انتظار"

    class Specialty(models.TextChoices):
        NEPHROLOGIST = "nephrologist", "نفرولوژیست"
        DENTIST = "dentist", "دندانپزشک"
        CARDIOLOGIST = "cardiologist", "متخصص قلب"
        GASTROENTEROLOGIST = "gastroenterologist", "متخصص گوارش"
        UROLOGIST = "urologist", "اورولوژیست"

    person = models.ForeignKey(
        Person, related_name="medical_approvals", on_delete=models.CASCADE
    )
    specialty = models.CharField(max_length=24, choices=Specialty.choices)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ON_HOLD
    )
    approval_date = models.DateField(null=True, blank=True)
    doctor_name = models.CharField(max_length=200, blank=True)
    medical_code = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تأییدیه پزشکی"
        verbose_name_plural = "تأییدیه‌های پزشکی"
        constraints = [
            models.UniqueConstraint(
                fields=("person", "specialty"),
                name="registry_person_specialty_approval_unique",
            )
        ]

    def __str__(self):
        return f"{self.get_specialty_display()} - {self.person}"


class ClinicalStateEvent(models.Model):
    class EntityType(models.TextChoices):
        RECIPIENT = "recipient", "گیرنده"
        DONOR = "donor", "اهداکننده"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=12, choices=EntityType.choices)
    recipient = models.ForeignKey(
        RecipientProfile,
        related_name="state_events",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    donor = models.ForeignKey(
        DonorProfile,
        related_name="state_events",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    previous_status = models.CharField(max_length=32, blank=True)
    new_status = models.CharField(max_length=32)
    reason = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="clinical_state_events",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "رویداد تغییر وضعیت"
        verbose_name_plural = "رویدادهای تغییر وضعیت"
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(entity_type="recipient", recipient__isnull=False, donor__isnull=True)
                    | models.Q(entity_type="donor", recipient__isnull=True, donor__isnull=False)
                ),
                name="registry_state_event_one_entity",
            )
        ]
        indexes = [
            models.Index(fields=("entity_type", "created_at"), name="registry_state_event_idx"),
        ]


class AllocationPolicy(models.Model):
    name = models.CharField(max_length=120)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=False)
    hla_weight = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.35"))
    waiting_time_weight = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.20"))
    urgency_weight = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.20"))
    cpra_weight = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.15"))
    age_weight = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.05"))
    regional_weight = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.05"))
    locus_weights = models.JSONField(default=default_locus_weights)
    high_cpra_threshold = models.PositiveSmallIntegerField(default=80)
    high_cpra_hla_discount = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal("0.60")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="allocation_policies",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سیاست تخصیص"
        verbose_name_plural = "سیاست‌های تخصیص"
        ordering = ("-version",)
        constraints = [
            models.UniqueConstraint(
                fields=("is_active",),
                condition=models.Q(is_active=True),
                name="registry_one_active_policy",
            )
        ]

    def clean(self):
        super().clean()
        weight_fields = (
            "hla_weight",
            "waiting_time_weight",
            "urgency_weight",
            "cpra_weight",
            "age_weight",
            "regional_weight",
        )
        total = sum((getattr(self, field) for field in weight_fields), start=0)
        if abs(total - Decimal("1")) > Decimal("0.0001"):
            raise ValidationError({"hla_weight": "جمع ضرایب سیاست تخصیص باید برابر یک باشد."})
        if not isinstance(self.locus_weights, dict):
            raise ValidationError({"locus_weights": "ضرایب locus باید یک شیء باشد."})

    def __str__(self):
        return f"{self.name} v{self.version}"


class MatchingRun(models.Model):
    class Trigger(models.TextChoices):
        NIGHTLY = "nightly", "شبانه"
        DONOR_CREATED = "donor_created", "ثبت اهداکننده"
        ANTI_HLA_UPDATED = "anti_hla_updated", "تغییر Anti-HLA"
        MANUAL = "manual", "دستی"

    class Status(models.TextChoices):
        RUNNING = "running", "در حال اجرا"
        COMPLETED = "completed", "تکمیل شده"
        FAILED = "failed", "ناموفق"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trigger = models.CharField(max_length=24, choices=Trigger.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RUNNING)
    policy = models.ForeignKey(
        AllocationPolicy, related_name="matching_runs", on_delete=models.PROTECT
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="matching_runs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    statistics = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-started_at",)


class MatchProposal(models.Model):
    class Compatibility(models.TextChoices):
        COMPATIBLE = "compatible", "سازگار"
        CONDITIONAL = "conditional", "سازگار مشروط"
        INCOMPATIBLE = "incompatible", "ناسازگار"

    class Decision(models.TextChoices):
        PROPOSED = "proposed", "پیشنهاد شده"
        APPROVED = "approved", "تأیید مرکز"
        REJECTED = "rejected", "رد مرکز"
        CROSSMATCH_NEGATIVE = "crossmatch_negative", "Cross-Match منفی"
        CROSSMATCH_POSITIVE = "crossmatch_positive", "Cross-Match مثبت"
        CLOSED = "closed", "بسته شده"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(MatchingRun, related_name="proposals", on_delete=models.CASCADE)
    recipient = models.ForeignKey(
        RecipientProfile, related_name="match_proposals", on_delete=models.CASCADE
    )
    donor = models.ForeignKey(
        DonorProfile, related_name="match_proposals", on_delete=models.CASCADE
    )
    compatibility = models.CharField(max_length=16, choices=Compatibility.choices)
    decision = models.CharField(max_length=24, choices=Decision.choices, default=Decision.PROPOSED)
    rank = models.PositiveIntegerField(null=True, blank=True)
    final_score = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    abo_compatible = models.BooleanField(default=False)
    anti_hla_status = models.CharField(max_length=16)
    hla_summary = models.JSONField(default=dict)
    score_breakdown = models.JSONField(default=dict)
    rejection_reasons = models.JSONField(default=list, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    center_note = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="decided_match_proposals",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پیشنهاد تطبیق"
        verbose_name_plural = "پیشنهادهای تطبیق"
        ordering = ("recipient_id", "rank", "-final_score")
        constraints = [
            models.UniqueConstraint(
                fields=("run", "recipient", "donor"), name="registry_run_pair_unique"
            )
        ]
        indexes = [
            models.Index(
                fields=("recipient", "compatibility", "decision", "rank"),
                name="registry_match_rec_idx",
            ),
            models.Index(
                fields=("donor", "compatibility", "decision"),
                name="registry_match_donor_idx",
            ),
        ]


class CrossMatchRequest(models.Model):
    class Status(models.TextChoices):
        CONSULTATION_REQUESTED = "consultation_requested", "درخواست مشاوره"
        CENTER_REVIEW = "center_review", "در بررسی مرکز"
        SCHEDULED = "scheduled", "برنامه‌ریزی شده"
        AWAITING_HIGH_RESOLUTION = "awaiting_high_resolution", "در انتظار High-Resolution"
        NEGATIVE = "negative", "منفی"
        POSITIVE = "positive", "مثبت"
        CANCELLED = "cancelled", "لغو شده"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proposal = models.ForeignKey(
        MatchProposal, related_name="crossmatch_requests", on_delete=models.PROTECT
    )
    recipient = models.ForeignKey(
        RecipientProfile, related_name="crossmatch_requests", on_delete=models.PROTECT
    )
    donor = models.ForeignKey(
        DonorProfile, related_name="crossmatch_requests", on_delete=models.PROTECT
    )
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.CONSULTATION_REQUESTED
    )
    patient_note = models.TextField(blank=True)
    physician_note = models.TextField(blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="requested_crossmatches",
        on_delete=models.PROTECT,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reviewed_crossmatches",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    result_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("proposal",),
                condition=models.Q(
                    status__in=(
                        "consultation_requested",
                        "center_review",
                        "scheduled",
                        "awaiting_high_resolution",
                    )
                ),
                name="registry_one_open_crossmatch",
            )
        ]


class InAppNotification(models.Model):
    class Kind(models.TextChoices):
        NEW_MATCH = "new_match", "تطبیق جدید"
        STATE_CHANGED = "state_changed", "تغییر وضعیت"
        TEST_EXPIRY = "test_expiry", "انقضای آزمایش"
        CROSSMATCH = "crossmatch", "Cross-Match"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="registry_notifications", on_delete=models.CASCADE
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    title = models.CharField(max_length=200)
    body = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    dedupe_key = models.CharField(max_length=200, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "dedupe_key"),
                condition=~models.Q(dedupe_key=""),
                name="registry_notification_dedupe",
            )
        ]


class SensitiveDataAccessLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sensitive_data_accesses",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    person = models.ForeignKey(
        Person,
        related_name="sensitive_data_accesses",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    person_identifier = models.CharField(max_length=40, blank=True, db_index=True)
    data_type = models.CharField(max_length=32, default="HLA")
    purpose = models.CharField(max_length=120)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("person", "data_type", "created_at"), name="registry_sensitive_log_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.person_id:
            self.person_identifier = self.person.identifier
        super().save(*args, **kwargs)
