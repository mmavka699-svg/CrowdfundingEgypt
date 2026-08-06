from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "first_name", "last_name", "mobile_phone", "is_active", "is_staff", "date_joined"]
    list_filter = ["is_active", "is_staff", "country"]
    search_fields = ["email", "first_name", "last_name", "mobile_phone"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {
            "fields": (
                "first_name", "last_name", "mobile_phone", "profile_picture",
                "birthdate", "facebook_url", "country",
            )
        }),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "mobile_phone", "password1", "password2"),
        }),
    )
