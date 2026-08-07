from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list_view, name="project_list"),
    path("search/", views.search_projects_view, name="search"),
    path("new/", views.project_create_view, name="project_create"),

    path("category/<slug:slug>/", views.category_detail_view, name="category_detail"),
    path("tag/<slug:slug>/", views.tag_detail_view, name="tag_detail"),

    path("<slug:slug>/", views.project_detail_view, name="project_detail"),
    path("<slug:slug>/edit/", views.project_edit_view, name="project_edit"),
    path("<slug:slug>/cancel/", views.project_cancel_view, name="project_cancel"),
    path("<slug:slug>/delete/", views.project_delete_view, name="project_delete"),
    path("<slug:slug>/donate/", views.donate_view, name="donate"),
    path("<slug:slug>/comment/", views.comment_create_view, name="comment_create"),
    path("<slug:slug>/rate/", views.rate_project_view, name="rate_project"),
    path("<slug:slug>/report/", views.report_project_view, name="report_project"),
    path("comment/<int:comment_id>/report/", views.report_comment_view, name="report_comment"),
]
