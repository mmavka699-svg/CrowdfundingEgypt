from django.db.models import Avg, Count, Sum, F, Q
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone
from decimal import Decimal

from projects.models import Project, Category


def _active_qs(today):
    """
    Base QuerySet for projects eligible to appear in public discovery sections:
    - Status = RUNNING
    - start_date <= today <= end_date
    - NOT fully funded (total_donated < total_target)
    Uses a DB-level annotation so no Python-side per-row evaluation is needed.
    """
    return (
        Project.objects
        .annotate(
            total_donated_sum=Coalesce(Sum("donations__amount"), Decimal("0.00"))
        )
        .filter(
            status=Project.Status.RUNNING,
            start_date__lte=today,
            end_date__gte=today,
        )
        .filter(total_donated_sum__lt=F("total_target"))
    )


def home_view(request):
    today = timezone.localdate()
    active_qs = _active_qs(today)

    # Top Slider: Top 5 highest-rated currently active, unfunded projects.
    top_rated_projects = (
        active_qs.annotate(avg_rating=Avg("ratings__stars"), rating_count=Count("ratings"))
        .filter(rating_count__gt=0 , avg_rating__gt=0)
        .order_by("-avg_rating", "-rating_count")[:5]
    )
    # Fallback: if not enough rated projects yet, pad with newest active ones.
    if top_rated_projects.count() < 5:
        extra_needed = 5 - top_rated_projects.count()
        existing_ids = list(top_rated_projects.values_list("id", flat=True))
        fallback = active_qs.exclude(id__in=existing_ids).order_by("-created_at")[:extra_needed]
        top_rated_projects = list(top_rated_projects) + list(fallback)

    # Latest Projects: 8 most recently created (still active & not fully funded).
    latest_projects = active_qs.order_by("-created_at")[:8]

    # Featured Projects: hand-picked by Admin (still active & not fully funded).
    featured_projects = active_qs.filter(is_featured=True).order_by("-created_at")[:5]

    # Categories section.
    categories = Category.objects.annotate(project_count=Count("projects")).order_by("name")

    # Real dynamic platform statistics calculated from the database
    from projects.models import Donation, Rating
    total_raised_val = Donation.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_projects_count = Project.objects.count()
    active_backers_count = Donation.objects.values("donor").distinct().count()

    avg_rating_val = Rating.objects.aggregate(avg=Avg("stars"))["avg"]
    if avg_rating_val:
        satisfaction_pct = int(round((float(avg_rating_val) / 5.0) * 100))
    else:
        satisfaction_pct = 100

    from projects.templatetags.project_tags import compact_money
    total_raised_display = f"{compact_money(total_raised_val)} EGP"

    stats = {
        "total_raised": int(total_raised_val),
        "total_raised_display": total_raised_display,
        "total_projects": total_projects_count,
        "active_backers": active_backers_count,
        "satisfaction_rate": satisfaction_pct,
    }

    context = {
        "top_rated_projects": top_rated_projects,
        "latest_projects": latest_projects,
        "featured_projects": featured_projects,
        "categories": categories,
        "stats": stats,
    }
    return render(request, "core/home.html", context)


def about_view(request):
    return render(request, "core/about.html")
