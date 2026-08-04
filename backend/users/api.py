import json
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt

from .models import AccessToken, Center


User = get_user_model()
EDITABLE_PROFILE_FIELDS = {
    "national_id",
    "first_name",
    "last_name",
    "username",
    "gender",
    "email",
    "mobile_phone",
}
NOTIFICATION_FIELDS = {
    "email_new_match": "notify_email_new_match",
    "email_approvals": "notify_email_approvals",
    "in_app_match": "notify_in_app_match",
    "in_app_messages": "notify_in_app_messages",
}


def api_error(message, *, status=400, errors=None):
    payload = {"message": message}
    if errors:
        payload["errors"] = errors
    return JsonResponse(payload, status=status)


def parse_json(request):
    if not request.body:
        return {}
    try:
        value = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("بدنهٔ درخواست باید JSON معتبر باشد.")
    if not isinstance(value, dict):
        raise ValueError("بدنهٔ درخواست باید یک شیء JSON باشد.")
    return value


def get_bearer_token(request):
    authorization = request.headers.get("Authorization", "")
    scheme, separator, raw_key = authorization.partition(" ")
    if separator and scheme.lower() == "bearer" and raw_key:
        return raw_key.strip()
    return None


def authenticate_token(request):
    raw_key = get_bearer_token(request)
    if not raw_key:
        return None, None

    now = timezone.now()
    token = (
        AccessToken.objects.select_related("user", "user__center")
        .filter(key_hash=AccessToken.hash_key(raw_key), expires_at__gt=now)
        .first()
    )
    if token is None or not token.user.is_active:
        return None, None

    if token.last_used_at is None or token.last_used_at < now - timedelta(minutes=5):
        AccessToken.objects.filter(pk=token.pk).update(last_used_at=now)
    return token.user, token


def endpoint(*methods, authenticated=False):
    allowed_methods = {method.upper() for method in methods}

    def decorator(view):
        @csrf_exempt
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method not in allowed_methods:
                return api_error("متد درخواست مجاز نیست.", status=405)
            try:
                request.data = parse_json(request)
            except ValueError as exc:
                return api_error(str(exc))

            if authenticated:
                request.api_user, request.api_token = authenticate_token(request)
                if request.api_user is None:
                    return api_error(
                        "نشست شما معتبر نیست؛ لطفاً دوباره وارد شوید.", status=401
                    )
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def serialize_user(user):
    return {
        "id": user.pk,
        "national_id": user.national_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "username": user.username,
        "gender": user.gender,
        "gender_display": user.get_gender_display(),
        "email": user.email,
        "mobile_phone": user.mobile_phone,
        "center": (
            {"id": user.center_id, "name": user.center.name} if user.center else None
        ),
        "is_staff": user.is_staff,
        "notification_preferences": {
            key: getattr(user, model_field)
            for key, model_field in NOTIFICATION_FIELDS.items()
        },
    }


def validation_errors(exc):
    if hasattr(exc, "message_dict"):
        return {
            key: [str(message) for message in messages]
            for key, messages in exc.message_dict.items()
        }
    return {"non_field_errors": [str(message) for message in exc.messages]}


@endpoint("POST")
def login(request):
    identifier = str(request.data.get("identifier", "")).strip()
    password = request.data.get("password", "")
    remember = bool(request.data.get("remember", False))
    if not identifier or not password:
        return api_error("ایمیل یا نام کاربری و رمز عبور الزامی است.")

    user = authenticate(request, username=identifier, password=password)
    if user is None:
        return api_error("ایمیل/نام کاربری یا رمز عبور صحیح نیست.", status=401)

    now = timezone.now()
    ttl = (
        timedelta(days=settings.AUTH_REMEMBER_TOKEN_TTL_DAYS)
        if remember
        else timedelta(hours=settings.AUTH_TOKEN_TTL_HOURS)
    )
    AccessToken.objects.filter(expires_at__lte=now).delete()
    raw_key, token = AccessToken.issue(user, expires_at=now + ttl)
    return JsonResponse(
        {
            "token": raw_key,
            "expires_at": token.expires_at.isoformat(),
            "user": serialize_user(user),
        }
    )


@endpoint("POST", authenticated=True)
def logout(request):
    request.api_token.delete()
    return JsonResponse({"message": "با موفقیت از سامانه خارج شدید."})


@endpoint("GET", "PATCH", authenticated=True)
def profile(request):
    user = request.api_user
    if request.method == "GET":
        return JsonResponse({"user": serialize_user(user)})

    supplied_fields = EDITABLE_PROFILE_FIELDS.intersection(request.data.keys())
    for field in supplied_fields:
        value = request.data[field]
        if isinstance(value, str):
            value = value.strip()
        setattr(user, field, value)

    try:
        user.full_clean(exclude=["password", "last_login", "date_joined"])
        with transaction.atomic():
            user.save(update_fields=[*supplied_fields])
    except ValidationError as exc:
        return api_error(
            "اطلاعات واردشده معتبر نیست.", errors=validation_errors(exc)
        )
    except IntegrityError:
        return api_error(
            "کد ملی، نام کاربری یا ایمیل قبلاً استفاده شده است."
        )

    user.refresh_from_db()
    return JsonResponse(
        {"message": "اطلاعات کاربری ذخیره شد.", "user": serialize_user(user)}
    )


@endpoint("POST", authenticated=True)
def change_password(request):
    current_password = request.data.get("current_password", "")
    new_password = request.data.get("new_password", "")
    if not current_password or not new_password:
        return api_error("رمز عبور فعلی و رمز عبور جدید الزامی است.")
    if not request.api_user.check_password(current_password):
        return api_error("رمز عبور فعلی صحیح نیست.")

    try:
        validate_password(new_password, user=request.api_user)
    except ValidationError as exc:
        return api_error(
            "رمز عبور جدید شرایط لازم را ندارد.",
            errors={"new_password": [str(message) for message in exc.messages]},
        )

    request.api_user.set_password(new_password)
    request.api_user.save(update_fields=["password"])
    request.api_user.access_tokens.exclude(pk=request.api_token.pk).delete()
    return JsonResponse({"message": "رمز عبور با موفقیت تغییر کرد."})


@endpoint("PATCH", authenticated=True)
def notification_preferences(request):
    unknown_fields = set(request.data) - set(NOTIFICATION_FIELDS)
    if unknown_fields:
        return api_error("یک یا چند گزینهٔ اعلان شناخته‌شده نیست.")
    if not request.data:
        return api_error("حداقل یک گزینهٔ اعلان باید ارسال شود.")
    if any(type(value) is not bool for value in request.data.values()):
        return api_error("مقدار گزینه‌های اعلان باید صحیح یا غلط باشد.")

    update_fields = []
    for key, value in request.data.items():
        model_field = NOTIFICATION_FIELDS[key]
        setattr(request.api_user, model_field, value)
        update_fields.append(model_field)
    request.api_user.save(update_fields=update_fields)

    return JsonResponse(
        {
            "message": "تنظیمات اعلان‌ها ذخیره شد.",
            "user": serialize_user(request.api_user),
        }
    )


@endpoint("POST")
def password_reset(request):
    email = str(request.data.get("email", "")).strip()
    if not email:
        return api_error("ایمیل الزامی است.")

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user and user.has_usable_password():
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/#/reset-password?uid={uid}&token={token}"
        send_mail(
            "بازیابی رمز عبور سامانه پیوند کلیه",
            (
                f"{user.full_name} عزیز،\n\n"
                "برای تعیین رمز عبور جدید، پیوند زیر را باز کنید:\n"
                f"{reset_url}\n\n"
                "اگر این درخواست را ثبت نکرده‌اید، این پیام را نادیده بگیرید."
            ),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

    # The response is deliberately identical for existing and unknown accounts.
    return JsonResponse(
        {
            "message": "اگر حساب فعالی با این ایمیل وجود داشته باشد، لینک بازیابی ارسال می‌شود."
        }
    )


@endpoint("POST")
def password_reset_confirm(request):
    uid = str(request.data.get("uid", ""))
    token = str(request.data.get("token", ""))
    new_password = request.data.get("new_password", "")
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        return api_error("لینک بازیابی نامعتبر یا منقضی شده است.", status=400)

    try:
        validate_password(new_password, user=user)
    except ValidationError as exc:
        return api_error(
            "رمز عبور جدید شرایط لازم را ندارد.",
            errors={"new_password": [str(message) for message in exc.messages]},
        )

    user.set_password(new_password)
    user.save(update_fields=["password"])
    user.access_tokens.all().delete()
    return JsonResponse({"message": "رمز عبور جدید ثبت شد؛ اکنون وارد شوید."})


@endpoint("GET", authenticated=True)
def centers(request):
    # Read-only helper for future forms; center management remains in Django Admin.
    values = Center.objects.values("id", "name")
    return JsonResponse({"centers": list(values)})
