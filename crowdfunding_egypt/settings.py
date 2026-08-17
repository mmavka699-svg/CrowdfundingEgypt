"""
Django settings for Crowd-Funding Egypt project.
Production-oriented configuration. Secrets are pulled from environment
variables — never hard-code credentials.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# SECURITY
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ---------------------------------------------------------------------------
# APPLICATIONS
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # required by django-allauth
    "django.contrib.humanize",

    # Third-party
    "django_filters",
    "taggit",                 # tagging for projects
    "allauth",                # bonus: social login
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.facebook",  # bonus: Facebook OAuth2
    "widget_tweaks",

    # Local apps
    "accounts",
    "projects",
    "core",
    "chatbot",
    
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "crowdfunding_egypt.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
"context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "core.context_processors.categories_processor",  # inject categories site-wide (navbar)
        ],
        },
    },
]

WSGI_APPLICATION = "crowdfunding_egypt.wsgi.application"

# ---------------------------------------------------------------------------
# DATABASE - PostgreSQL (required by spec)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "crowdfunding_egypt"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {
            "sslmode": "disable",
        },
    }
}

# ---------------------------------------------------------------------------
# CUSTOM USER MODEL
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.CustomUser"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# django-allauth (Facebook social login - bonus feature)
# ---------------------------------------------------------------------------
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = "none"  # we handle activation manually via our own token flow
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"
LOGIN_URL = "accounts:login"

SOCIALACCOUNT_PROVIDERS = {
    "facebook": {
        "METHOD": "oauth2",
        "SCOPE": ["email", "public_profile"],
        "FIELDS": ["id", "email", "first_name", "last_name", "picture"],
        "APP": {
            "client_id": os.environ.get("FACEBOOK_CLIENT_ID", ""),
            "secret": os.environ.get("FACEBOOK_CLIENT_SECRET", ""),
        },
    }
}
SOCIALACCOUNT_ADAPTER = "accounts.adapters.SocialAccountAdapter"

# ---------------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC & MEDIA FILES
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# EMAIL (activation links, password reset)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"  # console in dev
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Crowd-Funding Egypt <no-reply@crowdfunding-eg.com>")

# Custom setting consumed by accounts.tokens.ActivationTokenGenerator
ACCOUNT_ACTIVATION_TIMEOUT_HOURS = 24

# ---------------------------------------------------------------------------
# CRISPY / MESSAGES
# ---------------------------------------------------------------------------
MESSAGE_TAGS = {
    10: "info", 20: "info", 25: "success", 30: "warning", 40: "danger",
}

# ---------------------------------------------------------------------------
# CSRF — Custom failure view (user-friendly on stale tokens, no security bypass)
# ---------------------------------------------------------------------------
CSRF_FAILURE_VIEW = "core.views.csrf_failure_view"


GOOGLE_API_KEY   = os.getenv("GOOGLE_API_KEY" , None)