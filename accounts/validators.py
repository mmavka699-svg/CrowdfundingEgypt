"""
Custom validators for the accounts app.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Matches Egyptian mobile numbers in either local or international format:
#   01xxxxxxxxx           (11 digits, starts with 010/011/012/015)
#   +201xxxxxxxxx         (international, +20 followed by 10/11/12/15 and 8 digits)
#   00201xxxxxxxxx        (international dialing prefix variant)
EGYPT_PHONE_REGEX = re.compile(r"^(?:\+20|0020|0)1[0125]\d{8}$")


def validate_egyptian_phone(value: str) -> None:
    """
    Raises ValidationError if `value` is not a valid Egyptian mobile number.
    Accepted formats:
        01012345678
        +201012345678
        00201012345678
    Valid carrier prefixes: 010, 011, 012, 015
    """
    cleaned = value.strip().replace(" ", "").replace("-", "")
    if not EGYPT_PHONE_REGEX.match(cleaned):
        raise ValidationError(
            _(
                "Enter a valid Egyptian mobile number "
                "(e.g. 01012345678 or +201012345678)."
            ),
            code="invalid_egyptian_phone",
        )
