# 🇪🇬 Crowd-Funding Egypt

A modern, production-ready Egyptian Crowdfunding and Donation platform built with **Django 6.1 + SQLite + Bootstrap 5 / Custom CSS**. 

This project is deployed on **PythonAnywhere** and integrates powerful features like a **Wallet System**, **Facebook OAuth2**, and a **Google Gemini AI Chatbot**.

---

## 🌟 1. Highlights & Key Features

### 🔐 Authentication & Account Security
* **Email-Based Authentication**: Uses email addresses as the primary login identifier (`USERNAME_FIELD = "email"`).
* **Egyptian Mobile Phone Validation**: Enforces strict Egyptian phone regex validation (`^(?:\+20|0020|0)1[0125]\d{8}$`).
* **24-Hour Email Activation & Auto-Login**: New users register in an unverified state (`is_active=False`). Clicking the activation link verifies the account and automatically logs them in.
* **Social Login**: Fully integrated Facebook OAuth2 login via `django-allauth`, properly configured to bypass standard email verification and sync profile pictures.
* **Wallet System**: Every user has a built-in virtual wallet for tracking donations and refunds.
* **Complete Password Management**: Includes email-based password resets and secure in-app password changes.

### 🤖 AI Chatbot Assistant
* **Google Gemini Integration**: A floating chatbot powered by the `google-generativeai` SDK.
* **Context-Aware Assistance**: Answers questions about the platform, campaigns, and guides users on how to navigate the site.

### 💰 Campaign & Project Management
* **Multi-Image Support**: Campaigns support multiple image uploads rendered as interactive carousels.
* **Arabic Unicode Slugs**: Full support for creating projects with Arabic titles and URLs.
* **Dynamic Target & Progress**: Progress bars instantly reflect wallet donations vs. targets.
* **25%-Rule Campaign Cancellation**: Creators can only cancel a campaign if total raised donations are **under 25%** of the target goal. Canceling automatically issues **Wallet Refunds** to all donors.
* **Self-Donation & Self-Rating Protection**: Project creators are strictly forbidden from donating to or rating their own campaigns.
* **AJAX Star Ratings**: Interactive 1–5 star rating system that instantly updates the page via AJAX without requiring a full reload.
* **Nested Comments**: Threaded comment discussions supporting nested replies.

### 🎨 Design System & Modern UI
* **Deep Emerald & Warm Coral Palette**: Deep Emerald Green (`#0F5132`) paired with Warm Coral / Amber Orange (`#F97316`) for high-converting CTA buttons.
* **Glassmorphism Navbar**: Translucent backdrop-blur sticky navbar with dynamic search autocomplete dropdown.
* **Mobile-First Layout**: Fully responsive campaign cards and detail pages tailored for mobile screens.
* **Full Dark Mode**: CSS Custom Properties (`:root` / `[data-theme="dark"]`) supporting smooth light/dark theme switching.

---

## 📁 2. Project Structure

```
crowdfunding_egypt/
├── crowdfunding_egypt/       # Project config (settings, root urls, wsgi/asgi)
├── accounts/                 # Custom user, wallet, activation, password management
├── projects/                 # Campaigns, donations, comments, ratings, reports
├── core/                     # Homepage, search, and custom error handlers
├── chatbot/                  # Gemini AI Chatbot integration and API endpoints
├── templates/                # Bootstrap 5 HTML templates
├── static/                   # Custom CSS (glassmorphism/dark mode) & JS assets
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 🚀 3. Local Setup & Installation

```bash
# 1. Clone the repository & enter project directory
git clone https://github.com/mmavka699-svg/CrowdfundingEgypt.git
cd CrowdfundingEgypt

# 2. Create & activate a virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure Environment Variables
cp .env.example .env
# Edit .env and fill in:
# - DJANGO_SECRET_KEY
# - EMAIL_HOST_USER & EMAIL_HOST_PASSWORD
# - FACEBOOK_CLIENT_ID & FACEBOOK_CLIENT_SECRET
# - GOOGLE_API_KEY (for Gemini Chatbot)

# 5. Run Migrations (Uses SQLite by default)
python manage.py migrate

# 6. Load Seed Categories
python manage.py loaddata projects/fixtures/categories.json

# 7. Create Superuser (Admin)
python manage.py createsuperuser

# 8. Start Development Server
python manage.py runserver
```

> **Note on Email Testing:** By default in development, emails are printed to the console if no SMTP credentials are provided. Check your terminal for activation links.

---

## ☁️ 4. PythonAnywhere Deployment Guide

The project is optimized for deployment on the PythonAnywhere free tier using SQLite.

1. Create a PythonAnywhere account and open a Bash console.
2. Clone the repo and set up the virtual environment (as shown in Step 3 above).
3. Create your `.env` file via the PythonAnywhere file manager and set:
   ```env
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=yourusername.pythonanywhere.com
   ```
4. Configure the **Web Tab**:
   - Set the Virtualenv path to `/home/yourusername/CrowdfundingEgypt/venv`.
   - Add Static File mappings:
     - `/static/` -> `/home/yourusername/CrowdfundingEgypt/staticfiles`
     - `/media/` -> `/home/yourusername/CrowdfundingEgypt/media`
5. Edit your WSGI file (from the Web tab) to load `.env`:
   ```python
   import os, sys
   from pathlib import Path
   from dotenv import load_dotenv

   project_home = '/home/yourusername/CrowdfundingEgypt'
   load_dotenv(dotenv_path=Path(project_home) / '.env')
   if project_home not in sys.path: sys.path.insert(0, project_home)
   os.environ['DJANGO_SETTINGS_MODULE'] = 'crowdfunding_egypt.settings'
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
6. Run `python manage.py collectstatic` in the console.
7. Click the green **Reload** button on the Web tab!

---

## 🛡️ 5. Facebook OAuth Configuration

If you are deploying to a live domain, you **must** update the Facebook Developer Console:
1. Go to your App -> **Use cases** -> **Authentication**.
2. Click **Customize** and ensure both `email` and `public_profile` permissions are added.
3. Under **Facebook Login Settings**, add your Valid OAuth Redirect URIs:
   - `https://yourdomain.com/`
   - `https://yourdomain.com/accounts/social/facebook/login/callback/`
4. Log into your live Django Admin Panel, go to **Sites**, and update the default `example.com` site to match your live domain exactly.
