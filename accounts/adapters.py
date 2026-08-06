"""
Bonus Feature: Facebook Social Login (OAuth2) via django-allauth.

This adapter makes sure that users who sign in with Facebook are:
  1. Auto-activated (is_active=True) since Facebook already verified their identity.
  2. Populated with first/last name + profile picture pulled from the Facebook graph
     response, so the profile is not left half-empty.
  3. Still required to add a valid Egyptian mobile_phone afterwards (prompted once,
     since it is a REQUIRED_FIELD on CustomUser but Facebook does not provide it).
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        # Facebook has already verified the user's identity -> skip our email activation flow.
        user.is_active = True
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        extra_data = sociallogin.account.extra_data
        picture = extra_data.get("picture", {}).get("data", {}).get("url")
        if picture:
            # Stored as a reference URL; a background task could download &
            # attach it to `profile_picture` (ImageField) if a local copy is needed.
            user.facebook_url = f"https://facebook.com/{extra_data.get('id')}"
            user.save(update_fields=["facebook_url"])
        return user
