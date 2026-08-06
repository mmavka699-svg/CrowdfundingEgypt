"""
Secure, time-limited tokens for account activation.

Django's PasswordResetTokenGenerator hashes the user's pk, timestamp and a
state field (here: is_active) - once the token is used and the account is
activated, the same token becomes invalid automatically because `is_active`
changes. We extend it to enforce a strict 24-hour expiry window regardless
of Django's default PASSWORD_RESET_TIMEOUT setting.
"""
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Generates & validates tokens used in the "activate your account" email."""

    def _make_hash_value(self, user, timestamp):
        # Including is_active means the token is invalidated the moment
        # the account is activated (prevents reuse of the same link).
        return f"{user.pk}{timestamp}{user.is_active}"

    def _num_seconds(self, dt):
        import datetime
        return int((dt - datetime.datetime(2001, 1, 1)).total_seconds())


account_activation_token = AccountActivationTokenGenerator()


def is_token_expired(user, token) -> bool:
    """
    Returns True if the token is older than ACCOUNT_ACTIVATION_TIMEOUT_HOURS
    (default: 24 hours), independent of PASSWORD_RESET_TIMEOUT.
    """
    from django.utils.http import base36_to_int
    from django.utils import timezone

    timeout_hours = getattr(settings, "ACCOUNT_ACTIVATION_TIMEOUT_HOURS", 24)
    try:
        ts_b36 = token.split("-")[0]
        timestamp = base36_to_int(ts_b36)
    except (ValueError, IndexError):
        return True

    token_time = account_activation_token._num_seconds(
        account_activation_token._now()
    )
    seconds_elapsed = token_time - timestamp
    return seconds_elapsed > timeout_hours * 3600
