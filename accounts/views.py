from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView,
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_POST

from projects.models import Project, Donation
from .forms import RegistrationForm, EmailAuthenticationForm, ProfileEditForm, AccountDeletionForm
from .models import CustomUser
from .tokens import account_activation_token, is_token_expired


# ---------------------------------------------------------------------------
# REGISTRATION + EMAIL ACTIVATION (24-hour expiring link)
# ---------------------------------------------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            _send_activation_email(request, user)
            messages.success(
                request,
                "Account created! Please check your email to activate your account. "
                "The activation link expires in 24 hours.",
            )
            return redirect("accounts:login")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def _send_activation_email(request, user):
    current_site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)

    activation_link = request.build_absolute_uri(
        reverse("accounts:activate", kwargs={"uidb64": uid, "token": token})
    )

    subject = "Activate your Crowd-Funding Egypt account"
    message = render_to_string(
        "accounts/emails/activation_email.html",
        {
            "user": user,
            "domain": current_site.domain,
            "activation_link": activation_link,
        },
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)


def activate_account_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is None:
        messages.error(request, "Invalid activation link.")
        return redirect("accounts:login")

    if user.is_active:
        messages.info(request, "This account is already activated. Please log in.")
        return redirect("accounts:login")

    # Enforce strict 24-hour expiry, independent of token validity check.
    if is_token_expired(user, token):
        messages.error(
            request,
            "This activation link has expired (links are valid for 24 hours). "
            "Please request a new one.",
        )
        return redirect("accounts:resend_activation")

    if not account_activation_token.check_token(user, token):
        messages.error(request, "Invalid or already-used activation link.")
        return redirect("accounts:login")

    user.is_active = True
    user.save(update_fields=["is_active"])
    messages.success(request, "Your account has been activated! You can now log in.")
    return redirect("accounts:login")


def resend_activation_view(request):
    """Lets a user request a fresh activation link if the old one expired."""
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        try:
            user = CustomUser.objects.get(email=email, is_active=False)
            _send_activation_email(request, user)
            messages.success(request, "A new activation link has been sent to your email.")
            return redirect("accounts:login")
        except CustomUser.DoesNotExist:
            messages.error(request, "No inactive account found with that email.")
    return render(request, "accounts/resend_activation.html")


# ---------------------------------------------------------------------------
# LOGIN / LOGOUT  (login blocked until account is_active=True)
# ---------------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            next_url = request.GET.get("next") or reverse("core:home")
            return redirect(next_url)
    else:
        form = EmailAuthenticationForm(request)

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("core:home")


# ---------------------------------------------------------------------------
# PASSWORD RESET (bonus feature) — thin wrappers around Django's built-ins
# ---------------------------------------------------------------------------
class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/emails/password_reset_email.html"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


# ---------------------------------------------------------------------------
# PROFILE: view, edit, delete
# ---------------------------------------------------------------------------
@login_required
def profile_view(request):
    """Shows user info, their created projects, and their donation history."""
    user_projects = Project.objects.filter(creator=request.user).order_by("-created_at")
    user_donations = (
        Donation.objects.filter(donor=request.user)
        .select_related("project")
        .order_by("-created_at")
    )
    return render(
        request,
        "accounts/profile.html",
        {
            "profile_user": request.user,
            "user_projects": user_projects,
            "user_donations": user_donations,
        },
    )


@login_required
def profile_edit_view(request):
    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            if not user.profile_picture or request.POST.get("profile_picture-clear"):
                user.profile_picture = "profile_pics/default.png"
            user.save()
            form.save_m2m()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
def profile_delete_view(request):
    """
    Account deletion with UI confirmation (modal, see profile_delete.html + JS)
    AND bonus re-authentication via current password before deletion.
    """
    if request.method == "POST":
        form = AccountDeletionForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = request.user
            auth_logout(request)
            user.delete()
            messages.success(request, "Your account has been permanently deleted.")
            return redirect("core:home")
    else:
        form = AccountDeletionForm(user=request.user)
    return render(request, "accounts/profile_delete.html", {"form": form})
