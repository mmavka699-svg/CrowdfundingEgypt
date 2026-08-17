from datetime import datetime
import json

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Count, Sum
from django.utils import timezone

from projects.models import Category, Donation, Project

register = template.Library()


def _month_buckets(count):
    """Return [(label, year, month)] for the last `count` calendar months (oldest first)."""
    now = timezone.now()
    year, month = now.year, now.month
    buckets = []
    for _ in range(count):
        buckets.append((datetime(year, month, 1).strftime("%b"), year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(buckets))


def _series_objects(model, field, buckets):
    """Aggregate model counts per month bucket -> (labels, values)."""
    counts = {}
    qs = (
        model.objects.values_list(f"{field}__year", f"{field}__month")
        .annotate(total=Sum("amount"))
        .order_by()
    ) if hasattr(model, "amount") else (
        model.objects.values_list(f"{field}__year", f"{field}__month")
        .annotate(total=Count("pk"))
        .order_by()
    )
    for year, month, total in qs:
        counts[(year, month)] = float(total)
    labels, values = [], []
    for label, year, month in buckets:
        labels.append(label)
        values.append(counts.get((year, month), 0))
    return labels, values


@register.simple_tag
def admin_dashboard_stats():
    """Real counts + chart data used by the admin dashboard."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    now = timezone.now()
    this_month = {"year": now.year, "month": now.month}
    first_of_month = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)
    last_month = first_of_month - timezone.timedelta(days=1)

    donations_total = Donation.objects.aggregate(total=Sum("amount"))["total"] or 0
    this_sum = Donation.objects.filter(created_at__year=now.year, created_at__month=now.month).aggregate(total=Sum("amount"))["total"] or 0
    last_sum = Donation.objects.filter(created_at__year=last_month.year, created_at__month=last_month.month).aggregate(total=Sum("amount"))["total"] or 0

    users_new = User.objects.filter(date_joined__year=now.year, date_joined__month=now.month).count()
    users_prev = User.objects.filter(date_joined__year=last_month.year, date_joined__month=last_month.month).count()

    running_count = Project.objects.filter(status=Project.Status.RUNNING).count()

    donation_labels, donation_values = _series_objects(Donation, "created_at", _month_buckets(12))
    user_labels, user_values = _series_objects(User, "date_joined", _month_buckets(6))

    # donations by category (top 6)
    by_cat = (
        Donation.objects.values("project__category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:6]
    )
    by_cat = list(by_cat)
    donation_cat_labels = [c["project__category__name"] or "Other" for c in by_cat]
    donation_cat_values = [float(c["total"]) for c in by_cat]

    # running campaigns: % of target raised (top 5)
    running_qs = (
        Project.objects.filter(status=Project.Status.RUNNING)
        .annotate(raised=Sum("donations__amount"))
        .order_by("id")
    )
    campaign_progress = []
    for p in running_qs:
        raised = float(p.raised or 0)
        target = float(p.total_target)
        pct = round((raised / target) * 100) if target else 0
        campaign_progress.append({"title": p.title, "percent": min(pct, 100)})
    campaign_progress.sort(key=lambda x: x["percent"], reverse=True)
    campaign_progress = campaign_progress[:5]

    # top donors (top 5)
    top_donors = (
        Donation.objects.values("donor__first_name", "donor__last_name")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:5]
    )
    top_donors = [
        {"name": f"{d['donor__first_name']} {d['donor__last_name']}".strip() or "Anonymous",
         "total": float(d["total"])}
        for d in top_donors
    ]

    return {
        "running": running_count,
        "projects": Project.objects.count(),
        "categories": Category.objects.count(),
        "users": User.objects.count(),
        "donations": Donation.objects.count(),
        "donations_total": float(donations_total),
        "donations_this_month": float(this_sum),
        "donations_last_month": float(last_sum),
        "users_new": users_new,
        "users_prev": users_prev,
        "donation_labels": donation_labels,
        "donation_values": donation_values,
        "user_labels": user_labels,
        "user_values": user_values,
        "donation_cat_labels": donation_cat_labels,
        "donation_cat_values": donation_cat_values,
        "campaign_progress": campaign_progress,
        "top_donors": top_donors,
    }


@register.filter(name="compact_money")
def compact_money(value):
    """
    Formats monetary amounts:
    If value >= 1,000,000: formats as compact M notation (e.g., 2.5M, 1M, 1.25M).
    Else: formats with standard comma grouping (e.g., 500,000).
    """
    if value is None or value == "":
        return "0"
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)

    if val >= 1_000_000:
        val_m = val / 1_000_000
        formatted = f"{val_m:.2f}".rstrip("0").rstrip(".")
        return f"{formatted}M"
    else:
        return intcomma(int(val))


_MODEL_ICONS = {
    "CustomUser": "bi-person-circle",
    "Group": "bi-people-fill",
    "Permission": "bi-shield-check",
    "Category": "bi-folder2-open",
    "Project": "bi-rocket-takeoff",
    "ProjectImage": "bi-image",
    "Donation": "bi-heart-fill",
    "Comment": "bi-chat-left-text",
    "Rating": "bi-star-fill",
    "Report": "bi-flag-fill",
    "Site": "bi-globe2",
    "Tag": "bi-tag-fill",
    "EmailAddress": "bi-envelope-fill",
    "EmailConfirmation": "bi-envelope-check",
    "EmailConfirmation_request": "bi-envelope-check",
    "SocialAccount": "bi-person-lines-fill",
    "SocialApp": "bi-app-indicator",
    "SocialToken": "bi-key-fill",
    "Token": "bi-key-fill",
}
_DEFAULT_ICON = "bi-database"

_LUCIDE_MODEL_ICONS = {
    "CustomUser": "icon-circle-user",
    "Group": "icon-users",
    "Permission": "icon-shield-check",
    "Category": "icon-folder-open",
    "Project": "icon-rocket",
    "ProjectImage": "icon-image",
    "Donation": "icon-heart",
    "Comment": "icon-message-square",
    "Rating": "icon-star",
    "Report": "icon-flag",
    "Site": "icon-globe",
    "Tag": "icon-tag",
    "EmailAddress": "icon-mail",
    "EmailConfirmation": "icon-mail-check",
    "EmailConfirmation_request": "icon-mail-check",
    "SocialAccount": "icon-user-round",
    "SocialApp": "icon-app-window",
    "SocialToken": "icon-key-round",
    "Token": "icon-key-round",
}
_DEFAULT_LUCIDE_ICON = "icon-box"


@register.filter(name="tojson")
def tojson(value):
    """Serialize a Python value (list/dict) to a JSON string for use in templates."""
    return json.dumps(value)


@register.filter(name="model_icon")
def model_icon(object_name):
    """Return a clean bootstrap-icons class for an admin model (single line)."""
    return _MODEL_ICONS.get(object_name, _DEFAULT_ICON)


@register.filter(name="model_icon_lucide")
def model_icon_lucide(object_name):
    """Return a clean line-art (Lucide) class for an admin model (single line)."""
    return _LUCIDE_MODEL_ICONS.get(object_name, _DEFAULT_LUCIDE_ICON)


_APP_SECTIONS = {
    "account": "accounts",
    "accounts": "accounts",
    "auth": "auth",
    "projects": "projects",
    "sites": "sites",
    "socialaccount": "socialaccount",
    "taggit": "taggit",
}
_SECTION_LABELS = {
    "accounts": "Accounts",
    "auth": "Authentication &amp; Authorization",
    "projects": "Projects",
    "sites": "Sites",
    "socialaccount": "Social Accounts",
    "taggit": "Taggit",
}
_SECTION_ORDER = ["accounts", "auth", "projects", "sites", "socialaccount", "taggit"]


@register.simple_tag
def admin_nav_sections(available_apps):
    """
    Re-group Django's available_apps into clean fixed sidebar sections and
    merge related apps (account + accounts -> "Accounts") so each model shows
    exactly once under a single heading.
    """
    grouped = {}
    for app in available_apps:
        label = app.get("app_label") or ""
        key = _APP_SECTIONS.get(label, label)
        entry = grouped.setdefault(
            key,
            {
                "key": key,
                "label": _SECTION_LABELS.get(key, app.get("name") or key),
                "app_url": app.get("app_url") or "",
                "models": [],
            },
        )
        entry["models"].extend(app.get("models", []) or [])

    ordered = [key for key in _SECTION_ORDER if key in grouped]
    ordered += [key for key in grouped if key not in _SECTION_ORDER]
    return [grouped[key] for key in ordered]
