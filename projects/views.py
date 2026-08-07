from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from taggit.models import Tag

from .forms import (
    ProjectForm, ProjectImageUploadForm, DonationForm,
    CommentForm, RatingForm, ReportForm,
)
from .models import Project, ProjectImage, Category, Donation, Comment, Rating, Report


# ---------------------------------------------------------------------------
# LIST / SEARCH / CATEGORY BROWSE
# ---------------------------------------------------------------------------
def project_list_view(request):
    projects = Project.objects.filter(status=Project.Status.RUNNING).select_related(
        "category", "creator"
    )
    paginator = Paginator(projects, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "projects/project_list.html", {"page_obj": page_obj})


def search_projects_view(request):
    """Search bar: search projects by Title OR Tag."""
    query = request.GET.get("q", "").strip()
    results = Project.objects.none()
    if query:
        results = (
            Project.objects.filter(
                Q(title__icontains=query) | Q(tags__name__icontains=query),
                status=Project.Status.RUNNING,
            )
            .distinct()
            .select_related("category", "creator")
        )
    paginator = Paginator(results, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request, "projects/search_results.html", {"page_obj": page_obj, "query": query}
    )


def category_detail_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    projects = Project.objects.filter(
        category=category, status=Project.Status.RUNNING
    ).select_related("creator")
    paginator = Paginator(projects, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request, "projects/category_detail.html", {"category": category, "page_obj": page_obj}
    )


def tag_detail_view(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    projects = Project.objects.filter(tags__slug=slug, status=Project.Status.RUNNING)
    paginator = Paginator(projects, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "projects/tag_detail.html", {"tag": tag, "page_obj": page_obj})


# ---------------------------------------------------------------------------
# CREATE / EDIT
# ---------------------------------------------------------------------------
@login_required
def project_create_view(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        image_form = ProjectImageUploadForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.save()
            form.save_m2m()  # tags

            images = request.FILES.getlist("images")
            for idx, img in enumerate(images):
                ProjectImage.objects.create(project=project, image=img, is_cover=(idx == 0))

            messages.success(request, "Your project has been created!")
            return redirect(project.get_absolute_url())
    else:
        form = ProjectForm()
        image_form = ProjectImageUploadForm()

    return render(
        request, "projects/project_form.html", {"form": form, "image_form": image_form}
    )


@login_required
def project_edit_view(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if project.creator_id != request.user.id:
        return HttpResponseForbidden("You may not edit this project.")

    if request.method == "POST":
        # Snapshot old values before binding form
        old_values = {
            "title": project.title,
            "details": project.details,
            "category": project.category_id,
            "start_date": project.start_date,
            "end_date": project.end_date,
        }
        old_tag_ids = set(project.tags.values_list("id", flat=True))

        form = ProjectForm(request.POST, instance=project)
        image_form = ProjectImageUploadForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            saved_project = form.save()
            images = request.FILES.getlist("images")

            # Detect which fields changed
            edited = set(saved_project.edited_fields or [])

            if old_values["title"] != saved_project.title:
                edited.add("title")
            if old_values["details"] != saved_project.details:
                edited.add("details")
            if old_values["category"] != saved_project.category_id:
                edited.add("category")
            if old_values["start_date"] != saved_project.start_date:
                edited.add("dates")
            if old_values["end_date"] != saved_project.end_date:
                edited.add("dates")

            new_tag_ids = set(saved_project.tags.values_list("id", flat=True))
            if old_tag_ids != new_tag_ids:
                edited.add("tags")

            if images:
                edited.add("images")
                for img in images:
                    ProjectImage.objects.create(project=saved_project, image=img)

            saved_project.edited_fields = sorted(edited)
            saved_project.save(update_fields=["edited_fields"])

            messages.success(request, "Project updated.")
            return redirect(saved_project.get_absolute_url())
    else:
        form = ProjectForm(instance=project)
        image_form = ProjectImageUploadForm()

    return render(
        request,
        "projects/project_form.html",
        {"form": form, "image_form": image_form, "project": project},
    )


# ---------------------------------------------------------------------------
# CANCELLATION  (creator only, ONLY IF donations < 25% of target)
# ---------------------------------------------------------------------------
@login_required
@require_POST
def project_cancel_view(request, slug):
    project = get_object_or_404(Project, slug=slug)

    if project.creator_id != request.user.id:
        return HttpResponseForbidden("Only the project creator can cancel this project.")

    if not project.can_be_cancelled():
        messages.error(
            request,
            "This project cannot be cancelled: donations have reached 25% or more "
            "of the total target.",
        )
        return redirect(project.get_absolute_url())

    project.cancel()
    messages.success(request, "Your project has been cancelled.")
    return redirect(project.get_absolute_url())


# ---------------------------------------------------------------------------
# DELETE PROJECT  (creator only)
# ---------------------------------------------------------------------------
@login_required
@require_POST
def project_delete_view(request, slug):
    project = get_object_or_404(Project, slug=slug)

    if project.creator_id != request.user.id:
        return HttpResponseForbidden("Only the project creator can delete this project.")

    project_title = project.title
    project.delete()
    messages.success(request, f'Project "{project_title}" has been deleted successfully.')
    return redirect("accounts:profile")


# ---------------------------------------------------------------------------
# DETAIL VIEW  (carousel, avg rating, related projects by tags, comments, etc.)
# ---------------------------------------------------------------------------
def project_detail_view(request, slug):
    project = get_object_or_404(
        Project.objects.select_related("category", "creator").prefetch_related("images", "tags"),
        slug=slug,
    )

    top_level_comments = (
        project.comments.filter(parent__isnull=True)
        .select_related("author")
        .prefetch_related("replies__author")
        .order_by("-created_at")
    )

    donation_form = DonationForm()
    comment_form = CommentForm()
    rating_form = RatingForm()
    report_form = ReportForm()

    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(project=project, user=request.user).first()

    # Related projects: 4 projects sharing at least one tag, excluding itself.
    project_tag_ids = project.tags.values_list("id", flat=True)
    related_projects = (
        Project.objects.filter(tags__in=project_tag_ids, status=Project.Status.RUNNING)
        .exclude(pk=project.pk)
        .distinct()
        .annotate(shared_tags=Count("tags"))
        .order_by("-shared_tags")[:4]
    )

    context = {
        "project": project,
        "images": project.images.all(),
        "comments": top_level_comments,
        "donation_form": donation_form,
        "comment_form": comment_form,
        "rating_form": rating_form,
        "report_form": report_form,
        "user_rating": user_rating,
        "related_projects": related_projects,
        "can_cancel": (
            request.user.is_authenticated
            and project.creator_id == request.user.id
            and project.can_be_cancelled()
        ),
    }
    return render(request, "projects/project_detail.html", context)


# ---------------------------------------------------------------------------
# DONATE
# ---------------------------------------------------------------------------
@login_required
@require_POST
def donate_view(request, slug):
    project = get_object_or_404(Project, slug=slug)

    if not project.is_running:
        messages.error(request, "This project is not currently accepting donations.")
        return redirect(project.get_absolute_url())

    form = DonationForm(request.POST)
    if form.is_valid():
        donation = form.save(commit=False)
        donation.project = project
        donation.donor = request.user
        donation.save()
        messages.success(request, f"Thank you! You donated {donation.amount} EGP.")
    else:
        messages.error(request, "Please enter a valid donation amount.")
    return redirect(project.get_absolute_url())


# ---------------------------------------------------------------------------
# COMMENTS  (+ bonus nested replies)
# ---------------------------------------------------------------------------
@login_required
@require_POST
def comment_create_view(request, slug):
    project = get_object_or_404(Project, slug=slug)
    form = CommentForm(request.POST)
    parent_id = request.POST.get("parent_id")

    if form.is_valid():
        comment = form.save(commit=False)
        comment.project = project
        comment.author = request.user
        if parent_id:
            comment.parent = get_object_or_404(Comment, pk=parent_id, project=project)
        comment.save()
        messages.success(request, "Comment posted.")
    else:
        messages.error(request, "Comment cannot be empty.")
    return redirect(project.get_absolute_url() + "#comments")


# ---------------------------------------------------------------------------
# RATING  (AJAX endpoint - 1 to 5 stars, one per user, upsert)
# ---------------------------------------------------------------------------
@login_required
@require_POST
def rate_project_view(request, slug):
    project = get_object_or_404(Project, slug=slug)
    try:
        stars = int(request.POST.get("stars", 0))
    except ValueError:
        stars = 0

    if stars < 1 or stars > 5:
        return JsonResponse({"success": False, "error": "Rating must be between 1 and 5."}, status=400)

    rating, _created = Rating.objects.update_or_create(
        project=project, user=request.user, defaults={"stars": stars}
    )

    return JsonResponse(
        {
            "success": True,
            "average_rating": project.average_rating,
            "ratings_count": project.ratings_count,
            "your_rating": rating.stars,
        }
    )


# ---------------------------------------------------------------------------
# REPORTING  (project OR comment)
# ---------------------------------------------------------------------------
@login_required
@require_POST
def report_project_view(request, slug):
    project = get_object_or_404(Project, slug=slug)
    form = ReportForm(request.POST)
    if form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.project = project
        report.save()
        messages.success(request, "Thanks — this project has been reported to our moderators.")
    else:
        messages.error(request, "Please select a reason for the report.")
    return redirect(project.get_absolute_url())


@login_required
@require_POST
def report_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    form = ReportForm(request.POST)
    if form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.comment = comment
        report.save()
        messages.success(request, "Thanks — this comment has been reported to our moderators.")
    else:
        messages.error(request, "Please select a reason for the report.")
    return redirect(comment.project.get_absolute_url() + "#comments")
