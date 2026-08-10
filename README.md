# 🇪🇬 Crowd-Funding Egypt

A modern, production-ready Egyptian Crowdfunding and Donation platform built with **Django 5.1 + PostgreSQL + Bootstrap 5 / Custom CSS**. 

This document serves as the complete technical spec: system architecture, environment setup, URL mappings, security rules, and test coverage.

---

## 🌟 1. Highlights & Key Features

### 🔐 Authentication & Account Security
* **Email-Based Authentication**: Uses email addresses as the primary login identifier (`USERNAME_FIELD = "email"`).
* **Egyptian Mobile Phone Validation**: Enforces strict Egyptian phone regex validation (`^(?:\+20|0020|0)1[0125]\d{8}$`), supporting formats like `01012345678`, `+201123456789`, or `0020123456789`.
* **24-Hour Email Activation & Auto-Login**: New users register in an unverified state (`is_active=False`). Upon clicking the 24-hour expiring activation link, accounts are verified, automatically logged in without re-typing credentials, and redirected to the home page.
* **Complete Password Reset Flow**: Integrated password reset via email (`PasswordResetView` stack) featuring clean, branded HTML email templates and dynamic host detection.
* **In-App Password Change**: Allows logged-in users to securely change their password via the Edit Profile page with `PasswordChangeForm` and `update_session_auth_hash` to keep session tokens active.
* **Social Login**: Optional Facebook OAuth2 integration via `django-allauth`.
* **Custom CSRF Failure Handling**: Friendly, branded error page (`core.views.csrf_failure_view`) explaining cookie requirements and token rotation.

### 💰 Campaign & Project Management
* **Multi-Image Support**: Campaigns support multiple image uploads rendered as interactive carousels inside project cards and detail views.
* **Admin-Managed Categories**: Seeded category system (`Category` model) for structured project discovery.
* **Tagging System**: Integrated `django-taggit` for slug-based tag clouds and tagging.
* **25%-Rule Campaign Cancellation**: Creators can only cancel a campaign if total raised donations are **under 25%** of the target goal (`Project.can_be_cancelled()`). Enforced strictly at both model and view levels.
* **Self-Donation & Self-Rating Protection**: Project creators are strictly forbidden from donating to or rating their own campaigns, enforced with server-side validation.
* **Nested Comments & Community Discussion**: Threaded comment discussions supporting nested replies (`Comment.parent` self-FK).
* **AJAX Star Ratings**: Interactive 1–5 star rating system with `update_or_create` to ensure one rating per user.
* **Reporting System**: DB-level `CheckConstraint` enforcing report targets (strictly a project OR a comment).

### 🎨 Design System & Modern UI
* **Deep Emerald & Warm Coral Palette**: Deep Emerald Green (`#0F5132` / `#198754`) representing growth, hope, and trust paired with Warm Coral / Amber Orange (`#E05D38` / `#F97316`) for high-converting CTA buttons ("Donate Now").
* **Glassmorphism Navbar**: Translucent backdrop-blur sticky navbar with dynamic search autocomplete dropdown and brand icons.
* **Hero Slider & Floating Stats**: Top 5 highest-rated project carousel with glassmorphism text overlays and live community stats.
* **Modern Cards & Progress Bars**: Lift-on-hover cards (`.project-card`), category pill badges, and smooth animated gradient progress bars showing percentage raised vs. target EGP.
* **Full Dark Mode**: CSS Custom Properties (`:root` / `[data-theme="dark"]`) supporting smooth light/dark theme switching.

---

## 📁 2. Project Structure

```
crowdfunding_egypt/
├── crowdfunding_egypt/       # Project config (settings, root urls, wsgi/asgi)
├── accounts/                 # Custom user, auth, activation, profile, password management
│   ├── models.py             # CustomUser (email as USERNAME_FIELD)
│   ├── validators.py         # Egyptian phone regex validator
│   ├── tokens.py             # 24-hour expiring activation token generator
│   ├── adapters.py           # Facebook social-login adapter
│   ├── forms.py / views.py / urls.py / admin.py / tests.py
├── projects/                  # Campaigns, donations, comments, ratings, reports
│   ├── models.py              # Category, Project, ProjectImage, Donation,
│   │                          # Comment (nested), Rating, Report
│   ├── forms.py / views.py / urls.py / admin.py / tests.py
│   └── fixtures/categories.json   # Seed category fixtures
├── core/                      # Homepage, discovery, and custom error handlers
│   ├── views.py                # Home slider, search, CSRF failure handler
│   └── context_processors.py   # Global category context injector
├── templates/                  # Bootstrap 5 HTML templates
│   ├── accounts/              # Auth, profile, password reset & change templates
│   ├── core/                  # Home, about, csrf failure pages
│   ├── includes/              # Component partials (project_card.html, navbar, etc.)
│   └── projects/              # Project list, detail, creation, & donation views
├── static/                    # Custom CSS & JS assets
│   ├── css/style.css          # Design system, CSS variables, dark mode & components
│   └── js/                    # Search autocomplete, star rating, theme toggle scripts
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 🚀 3. Setup & Installation

```bash
# 1. Clone the repository & enter project directory
git clone https://github.com/mmavka699-svg/CrowdfundingEgypt.git
cd CrowdfundingEgypt

# 2. Create & activate a virtual environment
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure Environment Variables
cp .env.example .env
# Update .env with your database credentials and secret key

# 5. Run Migrations
python manage.py migrate

# 6. Load Seed Categories
python manage.py loaddata projects/fixtures/categories.json

# 7. Create Superuser (Admin)
python manage.py createsuperuser

# 8. Start Development Server
python manage.py runserver
```

> **Note on Email Testing:** By default in development, emails are printed to the console (`EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`). Check your terminal for activation links and password reset tokens.

---

## 🗺️ 4. URL Map

| URL Route | View Handler | Description |
|---|---|---|
| `/` | `core.home_view` | Homepage with hero slider, featured, latest, & categories |
| `/about/` | `core.about_view` | About platform page |
| `/accounts/register/` | `accounts.register_view` | User signup (account created inactive) |
| `/accounts/activate/<uidb64>/<token>/` | `accounts.activate_account_view` | 24h activation link with seamless auto-login |
| `/accounts/activate/resend/` | `accounts.resend_activation_view` | Resend activation email link |
| `/accounts/login/` | `accounts.login_view` | Email + password login (gated by activation) |
| `/accounts/logout/` | `accounts.logout_view` | Logout view |
| `/accounts/password-reset/` | `CustomPasswordResetView` | Forgot password email request |
| `/accounts/password-reset/done/` | `CustomPasswordResetDoneView` | Password reset email sent confirmation |
| `/accounts/password-reset/confirm/<uidb64>/<token>/` | `CustomPasswordResetConfirmView` | Password reset link target |
| `/accounts/password-reset/complete/` | `CustomPasswordResetCompleteView` | Password reset successful notification |
| `/accounts/password-change/` | `accounts.password_change_view` | In-app password change for logged-in users |
| `/accounts/profile/` | `accounts.profile_view` | View user profile, created campaigns, & donations |
| `/accounts/profile/edit/` | `accounts.profile_edit_view` | Edit user profile details (email locked) |
| `/accounts/profile/delete/` | `accounts.profile_delete_view` | Delete account with password re-authentication |
| `/projects/` | `projects.project_list_view` | Browse all active project campaigns |
| `/projects/search/?q=` | `projects.search_projects_view` | Live search by title OR tag |
| `/projects/new/` | `projects.project_create_view` | Create new campaign with image uploads |
| `/projects/category/<slug>/` | `projects.category_detail_view` | Filter projects by category |
| `/projects/tag/<slug>/` | `projects.tag_detail_view` | Filter projects by tag |
| `/projects/<slug>/` | `projects.project_detail_view` | Full project detail page with sticky donation card |
| `/projects/<slug>/edit/` | `projects.project_edit_view` | Edit campaign (creator only) |
| `/projects/<slug>/cancel/` | `projects.project_cancel_view` | Cancel campaign (creator only, <25% raised) |
| `/projects/<slug>/donate/` | `projects.donate_view` | Submit donation (creator restricted) |
| `/projects/<slug>/comment/` | `projects.comment_create_view` | Post top-level comment or nested reply |
| `/projects/<slug>/rate/` | `projects.rate_project_view` | AJAX 1–5 star rating (creator restricted) |
| `/projects/<slug>/report/` | `projects.report_project_view` | Report project campaign |

---

## 🧪 5. Testing & Verification

The application includes automated unit & integration test suites covering all business rules:

```bash
# Run full project test suite
python manage.py test

# Run accounts tests
python manage.py test accounts

# Run projects tests
python manage.py test projects
```

### Verified Test Scenarios:
1. **Signup & Activation**: Registrations create unverified users; valid 24h token activates user, auto-logs in, and redirects to home.
2. **Egyptian Phone Numbers**: Rejects non-Egyptian phone numbers (`013...`, 10 digits, etc.) and validates `010`, `011`, `012`, `015` prefixes.
3. **Self-Donation Guard**: Creators attempting to POST donations to their own campaigns are rejected server-side with error messages.
4. **Self-Rating Guard**: Creators attempting to rate their own project via AJAX receive an authorization error response.
5. **25% Cancellation Rule**: Campaigns with <25% target raised can be cancelled; campaigns reaching ≥25% reject cancellation requests.
6. **Password Management**: Full email reset flow verification + logged-in password change session persistence test.
7. **Nested Comments**: Multilevel comment thread creation and tree structure.

---

## 🛡️ 6. Production Deployment Checklist

- [ ] Set `DJANGO_DEBUG=False` and a secure cryptographically generated `DJANGO_SECRET_KEY` in `.env`.
- [ ] Configure PostgreSQL database settings (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
- [ ] Configure real SMTP email credentials (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`).
- [ ] Configure Facebook App ID & Secret for social authentication if enabled.
- [ ] Run `python manage.py collectstatic` to bundle static assets.
- [ ] Set `ALLOWED_HOSTS` to your production domain name.
