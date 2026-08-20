from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list_view, name="project_list"),
    path("search/", views.search_projects_view, name="search"),
    path("autocomplete/", views.search_autocomplete_view, name="autocomplete"),
    path("new/", views.project_create_view, name="project_create"),

    path("category/<str:slug>/", views.category_detail_view, name="category_detail"),
    path("tag/<str:slug>/", views.tag_detail_view, name="tag_detail"),

    path("<str:slug>/", views.project_detail_view, name="project_detail"),
    path("<str:slug>/edit/", views.project_edit_view, name="project_edit"),
    path("<str:slug>/cancel/", views.project_cancel_view, name="project_cancel"),
    path("<str:slug>/delete/", views.project_delete_view, name="project_delete"),
    # Donate checkout flow (route matches /<project>/donate/):
    #   GET  -> renders the multi-step donate.html stepper
    #   POST -> JSON endpoint that validates & creates the Donation on success
    path("<str:slug>/donate/", views.donate_view, name="donate"),
    path("<str:slug>/comment/", views.comment_create_view, name="comment_create"),
    path("<str:slug>/rate/", views.rate_project_view, name="rate_project"),
    path("<str:slug>/report/", views.report_project_view, name="report_project"),
    path("comment/<int:comment_id>/report/", views.report_comment_view, name="report_comment"),
]
