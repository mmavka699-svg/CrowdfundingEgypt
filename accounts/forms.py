from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class RegistrationForm(UserCreationForm):
    """Sign-up form. Collects all required fields; account starts inactive."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    mobile_phone = forms.CharField(
        max_length=20,
        required=True,
        help_text=_("Egyptian number, e.g. 01012345678 or +201012345678"),
    )
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "email",
            "mobile_phone",
            "profile_picture",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False  # must activate via email first
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(forms.Form):
    """Login form using email instead of username."""

    email = forms.EmailField(label=_("Email"))
    password = forms.CharField(widget=forms.PasswordInput, label=_("Password"))

    error_messages = {
        "invalid_login": _("Please enter a correct email and password."),
        "inactive": _("This account is inactive. Please check your email to activate it."),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                # Distinguish "wrong credentials" vs "not yet activated"
                try:
                    existing = CustomUser.objects.get(email=email)
                    if not existing.is_active:
                        raise forms.ValidationError(
                            self.error_messages["inactive"], code="inactive"
                        )
                except CustomUser.DoesNotExist:
                    pass
                raise forms.ValidationError(
                    self.error_messages["invalid_login"], code="invalid_login"
                )
        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class ProfileEditForm(forms.ModelForm):
    """
    Editable profile fields. Email is intentionally excluded (spec requirement:
    users may edit everything EXCEPT their email address).
    """

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "mobile_phone",
            "profile_picture",
            "birthdate",
            "facebook_url",
            "country",
        ]
        widgets = {
            "birthdate": forms.DateInput(attrs={"type": "date"}),
        }


class AccountDeletionForm(forms.Form):
    """
    Bonus feature: require the user's current password before permanently
    deleting their account. Paired with a JS confirmation modal in the UI.
    """

    current_password = forms.CharField(
        widget=forms.PasswordInput, label=_("Confirm your current password")
    )

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        password = self.cleaned_data["current_password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(_("Incorrect password. Account was not deleted."))
        return password
