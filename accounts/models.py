import os
import uuid

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .validators import validate_egyptian_phone


def profile_picture_path(instance, filename):
    """Store profile pictures under media/profile_pics/<uuid>.<ext> to avoid collisions."""
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("profile_pics", new_filename)


class CustomUserManager(BaseUserManager):
    """Manager for CustomUser using email as the unique identifier instead of username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        # Regular users must activate via email before login
        extra_fields.setdefault("is_active", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)  # superusers skip activation

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model, authenticated by email instead of username.
    Covers: First/Last Name, Email, Password, Profile Picture, Mobile Phone
    (Egyptian-validated), plus optional Birthdate / Facebook URL / Country.
    """

    class Country(models.TextChoices):
        EGYPT = "EG", _("Egypt")
        SAUDI_ARABIA = "SA", _("Saudi Arabia")
        UAE = "AE", _("United Arab Emirates")
        OTHER = "OT", _("Other")

    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    email = models.EmailField(_("email address"), unique=True)

    mobile_phone = models.CharField(
        _("mobile phone"),
        max_length=20,
        validators=[validate_egyptian_phone],
        help_text=_("Must be a valid 11-digit Egyptian mobile number."),
    )

    profile_picture = models.ImageField(
        _("profile picture"),
        upload_to=profile_picture_path,
        blank=True,
        null=True,
        default="profile_pics/default.png",
    )

    # Optional additional fields
    birthdate = models.DateField(_("birthdate"), blank=True, null=True)
    facebook_url = models.URLField(_("Facebook profile URL"), blank=True, null=True)
    country = models.CharField(
        _("country"), max_length=2, choices=Country.choices, blank=True, null=True
    )

    wallet_balance = models.DecimalField(
        _("wallet balance"), max_digits=12, decimal_places=2, default=0.00
    )

    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_("Designates whether this account has been activated via email."),
    )
    is_staff = models.BooleanField(_("staff status"), default=False)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "mobile_phone"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def save(self, *args, **kwargs):
        if not self.profile_picture:
            self.profile_picture = "profile_pics/default.png"
        super().save(*args, **kwargs)

    @property
    def avatar_url(self):
        """Safe profile picture URL getter. Falls back to default.png if picture is empty/cleared."""
        if self.profile_picture and hasattr(self.profile_picture, "name") and self.profile_picture.name:
            try:
                return self.profile_picture.url
            except ValueError:
                pass
        return f"{settings.MEDIA_URL}profile_pics/default.png"

    @property
    def total_donations_amount(self):
        """Sum of all donations made by this user (used on profile page)."""
        from django.db.models import Sum
        return self.donations.aggregate(total=Sum("amount"))["total"] or 0

class WalletTransaction(models.Model):
    class TransactionType(models.TextChoices):
        CREDIT = "credit", _("Credit (Deposit/Refund)")
        DEBIT = "debit", _("Debit (Withdrawal/Donation)")
        
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet_transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.amount} EGP for {self.user}"
