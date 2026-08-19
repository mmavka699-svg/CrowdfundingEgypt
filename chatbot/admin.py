"""
chatbot/admin.py — Admin registration for the ChatLog model.

Provides list display, filtering, and search for reviewing
chatbot interactions in the Django admin panel.
"""

from django.contrib import admin

from .models import ChatLog


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ("user", "short_message", "intent", "was_refused", "created_at")
    list_filter = ("was_refused", "intent", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name", "message")
    readonly_fields = ("user", "message", "response_snippet", "intent", "was_refused", "created_at")
    date_hierarchy = "created_at"
    list_per_page = 50

    def short_message(self, obj):
        """Truncated message for the list view."""
        return obj.message[:80] + ("…" if len(obj.message) > 80 else "")
    short_message.short_description = "Message"

    def has_add_permission(self, request):
        # Chat logs are created programmatically, not manually
        return False

    def has_change_permission(self, request, obj=None):
        # Logs are read-only audit records
        return False
