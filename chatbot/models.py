"""
chatbot/models.py — ChatLog model for auditing chatbot interactions.

Stores every chatbot interaction for admin review.
Sensitive donor data (amounts, payment methods) is NOT stored —
only the conversational text and metadata.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ChatLog(models.Model):
    """
    Audit log for every chatbot interaction.

    Fields:
      - user:             The authenticated user who sent the message.
      - message:          The user's input (truncated to 500 chars).
      - response_snippet: First 200 chars of the AI's response (for review).
      - intent:           The classified intent (e.g., 'campaign_search', 'injection').
      - was_refused:      True when the message was flagged as off-topic or injection.
      - created_at:       Timestamp of the interaction.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_logs",
    )
    message = models.CharField(
        _("user message"),
        max_length=500,
        help_text=_("The user's input, truncated to 500 characters."),
    )
    response_snippet = models.CharField(
        _("response snippet"),
        max_length=200,
        blank=True,
        help_text=_("First 200 characters of the AI response."),
    )
    intent = models.CharField(
        _("classified intent"),
        max_length=30,
        blank=True,
        default="general",
        help_text=_("The intent category detected from the user's message."),
    )
    was_refused = models.BooleanField(
        _("was refused"),
        default=False,
        help_text=_("Whether this message was flagged as off-topic or prompt injection."),
    )
    error_details = models.TextField(
        _("error details"),
        blank=True,
        default="",
        help_text=_("Full stack trace or error message when an error occurs."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Chat Log")
        verbose_name_plural = _("Chat Logs")

    def __str__(self):
        status = "⚠️ REFUSED" if self.was_refused else "✓"
        return f"[{status}] {self.user} — {self.message[:50]}"
