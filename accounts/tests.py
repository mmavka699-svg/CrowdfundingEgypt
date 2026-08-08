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
