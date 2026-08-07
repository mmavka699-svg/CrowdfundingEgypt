import os
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager


# ---------------------------------------------------------------------------
# CATEGORY  (pre-defined list, managed by Admins only)
# ---------------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("projects:category_detail", kwargs={"slug": self.slug})


# ---------------------------------------------------------------------------
# PROJECT
# ---------------------------------------------------------------------------
class Project(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", _("Running")
        CANCELLED = "cancelled", _("Cancelled")
        ENDED = "ended", _("Ended")

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects"
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    details = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="projects"
    )
    tags = TaggableManager(blank=True)  # multiple tags support

    total_target = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("1.00"))],
        help_text=_("Total financial target in EGP"),
    )

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RUNNING)
    is_featured = models.BooleanField(
        default=False, help_text=_("Hand-picked by Admin to appear in the Featured section")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Track which sections of the project have been edited by the creator
    edited_fields = models.JSONField(
        default=list, blank=True,
        help_text=_("List of field names that were edited after creation (e.g. ['title', 'details', 'images'])"),
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)[:260]
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("projects:project_detail", kwargs={"slug": self.slug})

    # ---- Derived / computed properties used across templates & views -----
    @property
    def total_donated(self):
        agg = self.donations.aggregate(total=models.Sum("amount"))
        return agg["total"] or Decimal("0.00")

    @property
    def remaining_amount(self):
        remaining = self.total_target - self.total_donated
        return max(remaining, Decimal("0.00"))

    @property
    def progress_percentage(self):
        if self.total_target <= 0:
            return 0
        pct = (self.total_donated / self.total_target) * 100
        return min(round(pct, 1), 100)

    @property
    def is_running(self):
        today = timezone.localdate()
        return (
            self.status == self.Status.RUNNING
            and self.start_date <= today <= self.end_date
        )

    @property
    def days_left(self):
        today = timezone.localdate()
        delta = (self.end_date - today).days
        return max(delta, 0)

    @property
    def average_rating(self):
        agg = self.ratings.aggregate(avg=models.Avg("stars"))
        return round(agg["avg"] or 0, 1)

    @property
    def ratings_count(self):
        return self.ratings.count()

    def can_be_cancelled(self):
        """
        Spec rule: creator may cancel ONLY IF total donations received are
        LESS THAN 25% of the total target.
        """
        if self.total_target <= 0:
            return False
        donated_ratio = self.total_donated / self.total_target
        return donated_ratio < Decimal("0.25")

    def cancel(self):
        if not self.can_be_cancelled():
            raise ValueError(
                "Project cannot be cancelled: donations have reached 25% or more of the target."
            )
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])


def project_image_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join("project_images", str(instance.project.id), new_filename)


class ProjectImage(models.Model):
    """Supports multiple image uploads per project (carousel on the detail page)."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=project_image_upload_path)
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_cover", "uploaded_at"]

    def __str__(self):
        return f"Image for {self.project.title}"


# ---------------------------------------------------------------------------
# DONATION
# ---------------------------------------------------------------------------
class Donation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="donations")
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="donations"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("1.00"))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.donor} donated {self.amount} EGP to {self.project}"


# ---------------------------------------------------------------------------
# COMMENT  (with bonus nested replies)
# ---------------------------------------------------------------------------
class Comment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField()
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )  # bonus: nested replies
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.project}"

    @property
    def is_reply(self):
        return self.parent_id is not None


# ---------------------------------------------------------------------------
# RATING  (1-5 stars, one rating per user per project)
# ---------------------------------------------------------------------------
class Rating(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings"
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "user"], name="unique_rating_per_user_project")
        ]

    def __str__(self):
        return f"{self.user} rated {self.project} {self.stars}/5"


# ---------------------------------------------------------------------------
# REPORT  (against a Project OR a Comment - not both)
# ---------------------------------------------------------------------------
class Report(models.Model):
    class Reason(models.TextChoices):
        SPAM = "spam", _("Spam")
        INAPPROPRIATE = "inappropriate", _("Inappropriate content")
        FRAUD = "fraud", _("Fraud / Scam")
        OTHER = "other", _("Other")

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                # NOTE: Django 5.1+ renamed this kwarg from `check` to `condition`.
                # If pinning to Django < 5.1, change `condition=` back to `check=`.
                condition=(
                    models.Q(project__isnull=False, comment__isnull=True)
                    | models.Q(project__isnull=True, comment__isnull=False)
                ),
                name="report_targets_project_xor_comment",
            )
        ]

    def __str__(self):
        target = self.project or self.comment
        return f"Report by {self.reporter} on {target}"
