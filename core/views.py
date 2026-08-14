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
            status__in=[Project.Status.RUNNING, Project.Status.COMING_SOON],
            end_date__gte=today,
        )
        .filter(total_donated_sum__lt=F("total_target"))
    )


def home_view(request):
    today = timezone.localdate()
    active_qs = _active_qs(today)

    # Top Slider: Top 5 highest-rated currently active, unfunded projects (must have rating > 0).
    top_rated_projects = (
        active_qs.annotate(avg_rating=Avg("ratings__stars"), rating_count=Count("ratings"))
        .filter(rating_count__gt=0 , avg_rating__gt=0)
        .filter(rating_count__gt=0, avg_rating__gt=0)
        .order_by("-avg_rating", "-rating_count")[:5]
    )

    # Latest Projects: 8 most recently created (still active & not fully funded).
    latest_projects = active_qs.order_by("-created_at")[:5]

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

def verification_view(request):
    return render(request, "core/verification.html")

def fees_view(request):
    return render(request, "core/fees.html")

def refund_view(request):
    return render(request, "core/refund.html")

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from projects.models import Report, Project
import re

@login_required
def report_view(request):
    if request.method == "POST":
        project_url = request.POST.get("project_url", "")
        reason = request.POST.get("reason")
        details = request.POST.get("details")

        if project_url and reason and details:
            # Try to extract slug from URL
            match = re.search(r'/projects/([^/]+)/?', project_url)
            project = None
            if match:
                slug = match.group(1)
                project = Project.objects.filter(slug=slug).first()

            if project:
                valid_reasons = [r[0] for r in Report.Reason.choices]
                if reason not in valid_reasons:
                    reason = Report.Reason.OTHER

                Report.objects.create(
                    reporter=request.user,
                    project=project,
                    reason=reason,
                    details=details
                )
                messages.success(request, "Your report has been submitted successfully. Thank you for helping keep the platform safe!")
                return redirect("core:home")
            else:
                messages.error(request, "Could not find a project with that URL. Please ensure it is a valid project link.")
        else:
            messages.error(request, "Please fill out all required fields.")

    return render(request, "core/report.html")


def csrf_failure_view(request, reason=""):
    """
    Custom CSRF failure handler. Instead of showing Django's raw 403 page,
    render a styled template that explains the issue and offers a retry link.
    This keeps CSRF protection fully enabled — no tokens are bypassed.
    """
    from django.http import HttpResponseForbidden
    from django.template.loader import render_to_string

    html = render_to_string(
        "core/csrf_failure.html",
        {"reason": reason, "referrer": request.META.get("HTTP_REFERER", "/")},
        request=request,
    )
    return HttpResponseForbidden(html)
