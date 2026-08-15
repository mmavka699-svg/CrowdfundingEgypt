from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Registration & activation
    path("register/", views.register_view, name="register"),
    path("check-email/", views.check_email_view, name="check_email"),
    path("verification-sent/", views.check_email_view, name="verification_sent"),
    path("activate/<uidb64>/<token>/", views.activate_account_view, name="activate"),
    path("activate/resend/", views.resend_activation_view, name="resend_activation"),

    # Login / logout
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Password reset (bonus)
    path("password-reset/", views.CustomPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        views.CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),

    # Password change (logged-in)
    path("password-change/", views.password_change_view, name="password_change"),

    # Profile
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("profile/delete/", views.profile_delete_view, name="profile_delete"),

    # Wallet
    path("wallet/charge/", views.charge_wallet_view, name="charge_wallet"),
    path("wallet/history/", views.wallet_history_view, name="wallet_history"),
]
