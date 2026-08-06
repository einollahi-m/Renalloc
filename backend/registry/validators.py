import re

from django.core.exceptions import ValidationError


PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_digits(value):
    return str("" if value is None else value).translate(PERSIAN_DIGITS)


def normalize_national_id(value):
    return re.sub(r"\D", "", normalize_digits(value))


def is_valid_iranian_national_id(value):
    national_id = normalize_national_id(value)
    if not re.fullmatch(r"\d{10}", national_id):
        return False
    if len(set(national_id)) == 1:
        return False
    checksum = sum(int(national_id[index]) * (10 - index) for index in range(9)) % 11
    expected = checksum if checksum < 2 else 11 - checksum
    return int(national_id[-1]) == expected


def validate_iranian_national_id(value):
    if not is_valid_iranian_national_id(value):
        raise ValidationError("کد ملی معتبر نیست.", code="invalid_national_id")


def normalize_mobile(value):
    digits = re.sub(r"\D", "", normalize_digits(value))
    if len(digits) == 10 and not digits.startswith("0"):
        digits = f"0{digits}"
    return digits


def validate_iranian_mobile(value):
    if not re.fullmatch(r"09\d{9}", normalize_mobile(value)):
        raise ValidationError(
            "شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود.",
            code="invalid_mobile",
        )
