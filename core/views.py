from django.db.models import Avg, Count
from django.shortcuts import render
from django.utils import timezone

from projects.models import Project, Category


def home_view(request):
    today = timezone.localdate()
    running_qs = Project.objects.filter(
        status=Project.Status.RUNNING, start_date__lte=today, end_date__gte=today
    )

    # Top Slider: Top 5 highest-rated currently running projects.
    top_rated_projects = (
        running_qs.annotate(avg_rating=Avg("ratings__stars"), rating_count=Count("ratings"))
        .filter(rating_count__gt=0)
        .order_by("-avg_rating", "-rating_count")[:5]
    )
    # Fallback: if not enough rated projects yet, pad with newest running ones.
    if top_rated_projects.count() < 5:
        extra_needed = 5 - top_rated_projects.count()
        existing_ids = list(top_rated_projects.values_list("id", flat=True))
        fallback = running_qs.exclude(id__in=existing_ids).order_by("-created_at")[:extra_needed]
        top_rated_projects = list(top_rated_projects) + list(fallback)

    # Latest Projects: 5 most recently created.
    latest_projects = Project.objects.order_by("-created_at")[:5]

    # Featured Projects: hand-picked by Admin.
    featured_projects = running_qs.filter(is_featured=True).order_by("-created_at")[:5]

    # Categories section.
    categories = Category.objects.annotate(project_count=Count("projects")).order_by("name")

    context = {
        "top_rated_projects": top_rated_projects,
        "latest_projects": latest_projects,
        "featured_projects": featured_projects,
        "categories": categories,
    }
    return render(request, "core/home.html", context)


def about_view(request):
    return render(request, "core/about.html")
