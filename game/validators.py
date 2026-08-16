"""
Custom validators for registration fields.
"""
import re
from django.core.exceptions import ValidationError


def validate_username(value):
    """
    Username must:
    - Be at least 5 characters long
    - Contain only alphabetic characters (upper or lowercase)
    """
    if len(value) < 5:
        raise ValidationError('Username must be at least 5 characters long.')
    if not value.isalpha():
        raise ValidationError('Username must contain only letters (no numbers or special characters).')


def validate_password_strength(value):
    """
    Password must:
    - Be at least 5 characters long
    - Contain at least one alphabetic character
    - Contain at least one numeric character
    - Contain at least one of: $, %, *
    """
    if len(value) < 5:
        raise ValidationError('Password must be at least 5 characters long.')
    if not re.search(r'[A-Za-z]', value):
        raise ValidationError('Password must contain at least one letter.')
    if not re.search(r'\d', value):
        raise ValidationError('Password must contain at least one number.')
    if not re.search(r'[\$%\*]', value):
        raise ValidationError('Password must contain at least one special character: $, %, or *.')
