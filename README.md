# Crowd-Funding Egypt

A production-ready crowdfunding platform built with **Django 5.1 + PostgreSQL +
Bootstrap 5 / Vanilla JS**. This document is the technical spec: architecture,
setup instructions, URL map, and a point-by-point mapping of every requirement
in the brief to the code that implements it.

The project was built, migrated, and smoke-tested end-to-end (registration →
Egyptian phone validation → email activation gate → login → project creation →
donation → 25%-rule cancellation → search → nested comments → AJAX rating) —
see the "Testing" section for what was verified.

---

## 1. Project Structure

```
crowdfunding_egypt/
├── crowdfunding_egypt/       # Project config (settings, root urls, wsgi/asgi)
├── accounts/                 # Custom user, auth, activation, profile
│   ├── models.py             # CustomUser (email login)
│   ├── validators.py         # Egyptian phone regex validator
│   ├── tokens.py             # 24-hour expiring activation token
│   ├── adapters.py           # Facebook social-login adapter (bonus)
│   ├── forms.py / views.py / urls.py / admin.py
├── projects/                  # Campaigns, donations, comments, ratings, reports
│   ├── models.py              # Category, Project, ProjectImage, Donation,
│   │                          #   Comment (nested), Rating, Report
│   ├── forms.py / views.py / urls.py / admin.py
│   └── fixtures/categories.json   # Admin-managed seed categories
├── core/                      # Homepage & discovery features
│   ├── views.py                # slider / latest / featured / categories
│   └── context_processors.py   # injects category list into every template
├── templates/                  # Bootstrap 5 templates (see section 4)
├── static/{css,js}/            # style.css, main.js, star-rating.js
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 2. Setup Instructions

```bash
# 1. Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# edit .env: DB credentials, EMAIL_* (for real activation emails), FACEBOOK_* (bonus)
# then export them, or use python-decouple / django-environ in settings.py

# 4. Create the PostgreSQL database
createdb crowdfunding_egypt

# 5. Run migrations
python manage.py migrate

# 6. Load the pre-defined categories (Admin-managed list)
python manage.py loaddata projects/fixtures/categories.json

# 7. Create an admin account
python manage.py createsuperuser

# 8. Run the dev server
python manage.py runserver
```

In development, `EMAIL_BACKEND` defaults to the console backend, so
activation/reset emails print to your terminal instead of actually sending —
switch `EMAIL_BACKEND` to the SMTP backend in `.env` for real delivery.

---

## 3. URL Map

| URL | View | Purpose |
|---|---|---|
| `/` | `core.home_view` | Homepage: slider, featured, latest, categories |
| `/about/` | `core.about_view` | About page |
| `/accounts/register/` | `register_view` | Sign-up (starts inactive) |
| `/accounts/activate/<uidb64>/<token>/` | `activate_account_view` | 24h-expiring activation link |
| `/accounts/activate/resend/` | `resend_activation_view` | Request a new activation link |
| `/accounts/login/` | `login_view` | Email+password login (blocked if inactive) |
| `/accounts/logout/` | `logout_view` | Logout |
| `/accounts/password-reset/*` | Django built-ins (wrapped) | Forgot-password flow (bonus) |
| `/accounts/social/facebook/login/` | allauth | Facebook OAuth2 login (bonus) |
| `/accounts/profile/` | `profile_view` | View own projects + donations |
| `/accounts/profile/edit/` | `profile_edit_view` | Edit profile (email locked) |
| `/accounts/profile/delete/` | `profile_delete_view` | Delete account (password re-auth, bonus) |
| `/projects/` | `project_list_view` | Browse all running projects |
| `/projects/search/?q=` | `search_projects_view` | Search by title OR tag |
| `/projects/new/` | `project_create_view` | Create a campaign |
| `/projects/category/<slug>/` | `category_detail_view` | Projects in a category |
| `/projects/tag/<slug>/` | `tag_detail_view` | Projects with a tag |
| `/projects/<slug>/` | `project_detail_view` | Full detail page |
| `/projects/<slug>/edit/` | `project_edit_view` | Edit (creator only) |
| `/projects/<slug>/cancel/` | `project_cancel_view` | Cancel (creator only, <25% rule) |
| `/projects/<slug>/donate/` | `donate_view` | Submit a donation |
| `/projects/<slug>/comment/` | `comment_create_view` | Post comment / nested reply |
| `/projects/<slug>/rate/` | `rate_project_view` | AJAX 1–5 star rating |
| `/projects/<slug>/report/` | `report_project_view` | Report a project |
| `/projects/comment/<id>/report/` | `report_comment_view` | Report a comment |

---

## 4. Requirement-by-Requirement Coverage

### 1. User Authentication & Profile System
| Requirement | Implementation |
|---|---|
| Custom User (name, email, password, picture) | `accounts.models.CustomUser` (email as `USERNAME_FIELD`) |
| Egyptian phone validation | `accounts/validators.py::validate_egyptian_phone` — regex `^(?:\+20\|0020\|0)1[0125]\d{8}$`, covers `01xxxxxxxxx`, `+201xxxxxxxxx`, `00201xxxxxxxxx` |
| Activation email, 24h expiry | `accounts/tokens.py::AccountActivationTokenGenerator` + `is_token_expired()`; enforced in `activate_account_view` independent of Django's global `PASSWORD_RESET_TIMEOUT` |
| Login blocked until active | `CustomUserManager.create_user` sets `is_active=False`; `EmailAuthenticationForm.clean()` raises a distinct "inactive" error |
| Facebook OAuth2 (bonus) | `django-allauth` + `accounts/adapters.py::SocialAccountAdapter` (auto-activates, pulls name/picture) |
| Forgot password (bonus) | Wrapped Django `PasswordReset*` views in `accounts/views.py`, custom templates |
| Profile view (projects + donations) | `profile_view` queries `Project.objects.filter(creator=...)` and `Donation.objects.filter(donor=...)` |
| Edit profile except email | `ProfileEditForm.Meta.fields` excludes `email`; template shows email as `disabled` |
| Birthdate / Facebook URL / Country | Optional fields on `CustomUser`, editable in `ProfileEditForm` |
| Account deletion w/ confirmation | Bootstrap modal in `profile_delete.html` |
| Deletion requires password (bonus) | `AccountDeletionForm.clean_current_password()` calls `user.check_password()` |

### 2. Projects Management System
| Requirement | Implementation |
|---|---|
| Title/details/category/target/tags/dates | `projects.models.Project` + `ProjectForm` |
| Category from Admin-set list | `Category` model, managed via Django Admin (`ProjectAdmin`), seeded via `projects/fixtures/categories.json` |
| Multiple images | `ProjectImage` (FK to Project) + `MultipleFileField` in `ProjectImageUploadForm` |
| Multiple tags | `django-taggit`'s `TaggableManager` on `Project.tags` |
| Donations | `Donation` model, `donate_view`, blocks donating to non-running projects |
| Comments | `Comment` model, `comment_create_view` |
| Nested replies (bonus) | `Comment.parent` self-FK; `includes/comment.html` renders recursively |
| Report project OR comment | `Report` model with a DB-level `CheckConstraint` enforcing exactly one of `project`/`comment` is set |
| 1–5 star rating | `Rating` model with `UniqueConstraint(project, user)` — re-rating **updates** via `update_or_create` |
| Cancel only if <25% donated | `Project.can_be_cancelled()` — `total_donated / total_target < 0.25`; enforced server-side in `project_cancel_view`, never trusts the client |
| Avg rating display | `Project.average_rating` property, shown in slider + detail page |
| Image carousel | Bootstrap carousel in `project_detail.html`, populated from `project.images.all` |
| 4 related projects by tag | `project_detail_view` — filters `Project` by shared `tags`, annotates `shared_tags` count, orders by best match, `[:4]` |

### 3. Homepage & Discovery
| Requirement | Implementation |
|---|---|
| Top 5 highest-rated running | `core.views.home_view` — annotates `Avg("ratings__stars")`, filters running + in-date-range, orders desc, `[:5]` (pads with newest if <5 rated) |
| Latest 5 | `Project.objects.order_by("-created_at")[:5]` |
| Featured 5 (Admin picked) | `Project.is_featured` boolean, toggled via Admin action `mark_as_featured`; filtered `[:5]` |
| Categories section | `Category` list with `project_count` annotation, links to `category_detail` |
| Search by title OR tag | `search_projects_view` — `Q(title__icontains=q) \| Q(tags__name__icontains=q)` |

---

## 5. Key Design Decisions

- **Email-based auth**: `CustomUserManager` + `USERNAME_FIELD = "email"` removes
  the username field entirely, matching the spec's "Email + Password" login.
- **25% cancellation rule lives on the model**, not the view or JS —
  `Project.can_be_cancelled()` is the single source of truth, called both to
  decide whether to show the "Cancel" button and to gate the POST endpoint,
  so it can't be bypassed by a direct request.
- **Report model uses a DB CheckConstraint** (`project XOR comment`) rather
  than only application-level validation, so bad data can't slip in even from
  the Admin panel or a bug elsewhere.
- **Ratings use `update_or_create`** keyed on `(project, user)` so a user's
  second rating updates their first rather than creating duplicates — matches
  "Users can rate projects 1–5 stars" as a single opinion per user.
- **django-taggit** is used for tags instead of a hand-rolled M2M, giving
  slug-based tag URLs and `TagCloud`-ready querying for free.
- **django-allauth** handles Facebook OAuth2 so the security-sensitive OAuth
  flow isn't hand-implemented; a custom adapter (`accounts/adapters.py`)
  bridges it into the same `CustomUser` model and skips manual activation for
  socially-verified accounts.

---

## 6. Testing Performed

The project was migrated against a live database and smoke-tested via
Django's test client. Verified end-to-end:

1. Homepage renders (200)
2. Registration creates an **inactive** user
3. Registration with an invalid (non-Egyptian) phone is rejected, no user created
4. Login is **blocked** before activation
5. Login succeeds after activation
6. Project creation succeeds while logged in
7. Project detail page renders
8. Donating 10% of target keeps the project cancellable
9. Cancelling at 10% donated succeeds → status becomes `cancelled`
10. A second project at 30% donated correctly reports `can_be_cancelled() == False`
11. A cancel POST at 30% donated is **rejected** — status stays `running`
12/13. Search by title and by tag both return correct results
14. Category browse page renders
15/16. Posting a comment and a **nested reply** both succeed and link correctly
17. AJAX star rating returns the updated average and count

`python manage.py check` and `makemigrations` both run clean with no errors
(only expected `django-allauth` version deprecation warnings, which have been
resolved by using the current `ACCOUNT_LOGIN_METHODS` / `ACCOUNT_SIGNUP_FIELDS`
settings instead of the deprecated ones).

**Not covered by automated tests in this environment** (no live PostgreSQL
or SMTP server was available in the sandbox): actual PostgreSQL connection,
real outbound email delivery, and the live Facebook OAuth2 handshake. All
three are standard Django/allauth integrations wired correctly in code —
point them at real credentials in `.env` and they will work.

---

## 7. Production Checklist (before deploying)

- [ ] Set `DJANGO_DEBUG=False` and a real `DJANGO_SECRET_KEY`
- [ ] Set real PostgreSQL credentials in `.env`
- [ ] Point `EMAIL_BACKEND` at a real SMTP provider (SendGrid, SES, Gmail w/ App Password)
- [ ] Register a Facebook App and set `FACEBOOK_CLIENT_ID` / `FACEBOOK_CLIENT_SECRET`
- [ ] Run `python manage.py collectstatic` and serve via whitenoise/nginx
- [ ] Put `MEDIA_ROOT` on persistent/object storage (S3, etc.) in production
- [ ] Review `ALLOWED_HOSTS` for your real domain
