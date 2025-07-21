# common/validators.py

from django.core.exceptions import ValidationError

def validate_logo_size(file):
    max_size = 2 * 1024 * 1024  # 2MB
    if file.size > max_size:
        raise ValidationError("Logo file size must be under 2MB.")
