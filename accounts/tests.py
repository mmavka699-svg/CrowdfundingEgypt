from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.tokens import account_activation_token

User = get_user_model()


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_scenario_a_new_user_signup_and_email_activation_flow(self):
        """
        Signup -> Check Email waiting page -> Click activation link -> Auto-login -> Home page
        """
        # 1. Submit Registration Form
        signup_data = {
            "first_name": "Ahmed",
            "last_name": "Hassan",
            "email": "ahmed@example.com",
            "mobile_phone": "01012345678",
            "password1": "StrongP@ss123",
            "password2": "StrongP@ss123",
        }
        response = self.client.post(reverse("accounts:register"), signup_data)

        # Must redirect to /accounts/check-email/
        self.assertRedirects(response, reverse("accounts:check_email"))

        # User is created but inactive
        user = User.objects.get(email="ahmed@example.com")
        self.assertFalse(user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)

        # Check-email page renders properly
        check_response = self.client.get(reverse("accounts:check_email"))
        self.assertEqual(check_response.status_code, 200)
        self.assertContains(check_response, "Check Your Inbox")
        self.assertContains(check_response, "ahmed@example.com")

        # 2. Click Activation Link
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_url = reverse("accounts:activate", kwargs={"uidb64": uid, "token": token})

        activate_response = self.client.get(activation_url)

        # Must redirect straight to Home page
        self.assertRedirects(activate_response, reverse("core:home"))

        # User must now be active and authenticated in session without manual login
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(int(self.client.session.get("_auth_user_id")), user.pk)

    def test_scenario_b_invalid_token_blocks_login(self):
        """Activation link with invalid token shows error and does NOT log user in."""
        user = User.objects.create_user(
            email="invalid@example.com",
            password="StrongP@ss123",
            first_name="Invalid",
            last_name="Test",
            mobile_phone="01112345678",
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_url = reverse("accounts:activate", kwargs={"uidb64": uid, "token": "invalid-token-123"})

        response = self.client.get(activation_url)
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_scenario_c_expired_token_redirects_to_resend(self):
        """Activation link older than 24h shows expired error and redirects to resend."""
        from django.utils.http import int_to_base36

        user = User.objects.create_user(
            email="expired@example.com",
            password="StrongP@ss123",
            first_name="Expired",
            last_name="Test",
            mobile_phone="01212345678",
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Calculate timestamp 25 hours in the past (in base36)
        current_ts = account_activation_token._num_seconds(account_activation_token._now())
        expired_ts = current_ts - (25 * 3600)
        expired_ts_b36 = int_to_base36(expired_ts)
        expired_token = f"{expired_ts_b36}-fakehash123456"

        activation_url = reverse("accounts:activate", kwargs={"uidb64": uid, "token": expired_token})

        response = self.client.get(activation_url)
        self.assertRedirects(response, reverse("accounts:resend_activation"))
        self.assertNotIn("_auth_user_id", self.client.session)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_scenario_d_already_verified_account_graceful_handling(self):
        """Opening activation link for an already active user logs them in and redirects to home."""
        user = User.objects.create_user(
            email="active@example.com",
            password="StrongP@ss123",
            first_name="Active",
            last_name="Test",
            mobile_phone="01512345678",
        )
        user.is_active = True
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_url = reverse("accounts:activate", kwargs={"uidb64": uid, "token": token})

        response = self.client.get(activation_url)
        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(int(self.client.session.get("_auth_user_id")), user.pk)

    def test_scenario_e_normal_existing_login(self):
        """Active user can log in with their email and password."""
        user = User.objects.create_user(
            email="login@example.com",
            password="StrongP@ss123",
            first_name="Login",
            last_name="User",
            mobile_phone="01099998888",
        )
        user.is_active = True
        user.save()

        response = self.client.post(
            reverse("accounts:login"),
            {"email": "login@example.com", "password": "StrongP@ss123"},
        )
        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(int(self.client.session.get("_auth_user_id")), user.pk)

    def test_scenario_f_logout(self):
        """Authenticated user can log out safely."""
        user = User.objects.create_user(
            email="logout@example.com",
            password="StrongP@ss123",
            first_name="Logout",
            last_name="User",
            mobile_phone="01077776666",
        )
        user.is_active = True
        user.save()

        self.client.force_login(user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("core:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_scenario_g_password_reset_flow(self):
        """Password reset request view renders and handles submission."""
        user = User.objects.create_user(
            email="reset@example.com",
            password="StrongP@ss123",
            first_name="Reset",
            last_name="User",
            mobile_phone="01055554444",
        )
        user.is_active = True
        user.save()

        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "reset@example.com"},
        )
        self.assertRedirects(response, reverse("accounts:password_reset_done"))


from django.core import mail
from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.validators import validate_egyptian_phone


class EgyptianPhoneValidatorTest(TestCase):
    def test_valid_11_digit_phone_numbers(self):
        valid_numbers = [
            "01012345678",
            "01198765432",
            "01200000000",
            "01555555555",
            "+201012345678",
            "00201012345678",
            "010 1234 5678",
            "010-1234-5678",
        ]
        for number in valid_numbers:
            with self.subTest(number=number):
                try:
                    validate_egyptian_phone(number)
                except ValidationError:
                    self.fail(f"validate_egyptian_phone failed unexpectedly for valid input: {number}")

    def test_invalid_phone_numbers_raises_11_digit_error(self):
        invalid_numbers = [
            "0101234567",       # 10 digits
            "010123456789",     # 12 digits
            "01312345678",      # 013 is not a valid carrier prefix
            "abcdefghijk",      # letters
            "12345",            # too short
        ]
        for number in invalid_numbers:
            with self.subTest(number=number):
                with self.assertRaises(ValidationError) as cm:
                    validate_egyptian_phone(number)
                self.assertIn(
                    "Please enter a valid 11-digit Egyptian mobile number.",
                    cm.exception.messages,
                )


class PasswordResetFlowTests(TestCase):
    """Full end-to-end tests for the forgot-password flow."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="resetflow@example.com",
            password="OldP@ss1234",
            first_name="Reset",
            last_name="Flow",
            mobile_phone="01012345678",
        )
        self.user.is_active = True
        self.user.save()

    def test_reset_page_loads(self):
        resp = self.client.get(reverse("accounts:password_reset"))
        self.assertEqual(resp.status_code, 200)

    def test_submit_valid_email_redirects_to_done(self):
        resp = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "resetflow@example.com"},
        )
        self.assertRedirects(resp, reverse("accounts:password_reset_done"))

    def test_email_contains_valid_reset_link(self):
        self.client.post(
            reverse("accounts:password_reset"),
            {"email": "resetflow@example.com"},
        )
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body
        self.assertIn("password-reset/confirm/", email_body)

    def test_full_reset_flow_changes_password(self):
        """Submit email → get token → set new password → old fails, new works."""
        self.client.post(
            reverse("accounts:password_reset"),
            {"email": "resetflow@example.com"},
        )
        email_body = mail.outbox[0].body
        # Extract the reset URL from the email
        import re
        match = re.search(r"(https?://\S*password-reset/confirm/\S+/)", email_body)
        self.assertIsNotNone(match, "Reset link not found in email")
        reset_url = match.group(1)
        # Extract uidb64 and token from URL
        parts = reset_url.rstrip("/").split("/")
        token = parts[-1]
        uidb64 = parts[-2]

        confirm_url = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": token},
        )
        # GET the confirm page (Django redirects to set-password URL internally)
        resp = self.client.get(confirm_url, follow=True)
        self.assertEqual(resp.status_code, 200)

        # POST the new password (Django uses internal token URL after redirect)
        # The confirm view redirects token URL to /set-password/ internally
        set_pw_url = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": "set-password"},
        )
        resp = self.client.post(
            set_pw_url,
            {"new_password1": "BrandNewP@ss99", "new_password2": "BrandNewP@ss99"},
        )
        self.assertRedirects(resp, reverse("accounts:password_reset_complete"))

        # Old password no longer works
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("OldP@ss1234"))
        # New password works
        self.assertTrue(self.user.check_password("BrandNewP@ss99"))

    def test_reset_mismatched_passwords_rejected(self):
        self.client.post(
            reverse("accounts:password_reset"),
            {"email": "resetflow@example.com"},
        )
        email_body = mail.outbox[0].body
        import re
        match = re.search(r"(https?://\S*password-reset/confirm/\S+/)", email_body)
        reset_url = match.group(1)
        parts = reset_url.rstrip("/").split("/")
        token = parts[-1]
        uidb64 = parts[-2]

        confirm_url = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": token},
        )
        self.client.get(confirm_url, follow=True)

        set_pw_url = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": "set-password"},
        )
        resp = self.client.post(
            set_pw_url,
            {"new_password1": "BrandNewP@ss99", "new_password2": "DifferentP@ss99"},
        )
        # Should stay on the form (200) with errors
        self.assertEqual(resp.status_code, 200)
        # Password not changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldP@ss1234"))

    def test_reset_weak_password_rejected(self):
        self.client.post(
            reverse("accounts:password_reset"),
            {"email": "resetflow@example.com"},
        )
        email_body = mail.outbox[0].body
        import re
        match = re.search(r"(https?://\S*password-reset/confirm/\S+/)", email_body)
        reset_url = match.group(1)
        parts = reset_url.rstrip("/").split("/")
        token = parts[-1]
        uidb64 = parts[-2]

        self.client.get(
            reverse("accounts:password_reset_confirm",
                    kwargs={"uidb64": uidb64, "token": token}),
            follow=True,
        )
        set_pw_url = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": "set-password"},
        )
        resp = self.client.post(
            set_pw_url,
            {"new_password1": "123", "new_password2": "123"},
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldP@ss1234"))

    def test_invalid_token_shows_error(self):
        resp = self.client.get(
            reverse("accounts:password_reset_confirm",
                    kwargs={"uidb64": "BADUID", "token": "bad-token"}),
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "invalid")

    def test_reset_complete_page_loads(self):
        resp = self.client.get(reverse("accounts:password_reset_complete"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Password Reset Complete")

    def test_done_page_loads(self):
        resp = self.client.get(reverse("accounts:password_reset_done"))
        self.assertEqual(resp.status_code, 200)


class PasswordChangeTests(TestCase):
    """Tests for the logged-in password change feature."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="pwchange@example.com",
            password="OldP@ss1234",
            first_name="PW",
            last_name="Change",
            mobile_phone="01112345678",
        )
        self.user.is_active = True
        self.user.save()
        self.client.force_login(self.user)

    def test_password_change_page_loads(self):
        resp = self.client.get(reverse("accounts:password_change"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Change Password")

    def test_correct_current_and_valid_new_password_succeeds(self):
        resp = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "OldP@ss1234",
                "new_password1": "BrandNewP@ss99",
                "new_password2": "BrandNewP@ss99",
            },
        )
        self.assertRedirects(resp, reverse("accounts:profile_edit"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewP@ss99"))

    def test_user_stays_logged_in_after_password_change(self):
        self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "OldP@ss1234",
                "new_password1": "BrandNewP@ss99",
                "new_password2": "BrandNewP@ss99",
            },
        )
        # User should still be authenticated
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_incorrect_current_password_rejected(self):
        resp = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "WrongPassword99!",
                "new_password1": "BrandNewP@ss99",
                "new_password2": "BrandNewP@ss99",
            },
        )
        self.assertEqual(resp.status_code, 200)  # stays on form
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldP@ss1234"))

    def test_mismatched_new_passwords_rejected(self):
        resp = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "OldP@ss1234",
                "new_password1": "BrandNewP@ss99",
                "new_password2": "DifferentP@ss99",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldP@ss1234"))

    def test_weak_password_rejected(self):
        resp = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "OldP@ss1234",
                "new_password1": "123",
                "new_password2": "123",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldP@ss1234"))

    def test_can_login_with_new_password_after_logout(self):
        self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "OldP@ss1234",
                "new_password1": "BrandNewP@ss99",
                "new_password2": "BrandNewP@ss99",
            },
        )
        self.client.post(reverse("accounts:logout"))
        resp = self.client.post(
            reverse("accounts:login"),
            {"email": "pwchange@example.com", "password": "BrandNewP@ss99"},
        )
        self.assertRedirects(resp, reverse("core:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_profile_edit_has_password_section(self):
        resp = self.client.get(reverse("accounts:profile_edit"))
        self.assertContains(resp, "Change Password")
        self.assertContains(resp, "Forgot password?")

    def test_forgot_password_link_points_to_reset(self):
        resp = self.client.get(reverse("accounts:password_change"))
        self.assertContains(resp, reverse("accounts:password_reset"))

    def test_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("accounts:password_change"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

