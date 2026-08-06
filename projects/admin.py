from django.contrib import admin
from .models import Category, Project, ProjectImage, Donation, Comment, Rating, Report


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "title", "creator", "category", "status", "is_featured",
        "total_target", "total_donated", "start_date", "end_date",
    ]
    list_filter = ["status", "is_featured", "category"]
    search_fields = ["title", "details", "creator__email"]
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProjectImageInline]
    actions = ["mark_as_featured", "unmark_as_featured"]

    @admin.action(description="Mark selected projects as Featured")
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="Remove Featured status")
    def unmark_as_featured(self, request, queryset):
        queryset.update(is_featured=False)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ["project", "donor", "amount", "created_at"]
    list_filter = ["created_at"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["project", "author", "parent", "created_at"]
    list_filter = ["created_at"]


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["project", "user", "stars", "created_at"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["reporter", "project", "comment", "reason", "is_resolved", "created_at"]
    list_filter = ["reason", "is_resolved"]
    actions = ["mark_resolved"]

    @admin.action(description="Mark selected reports as resolved")
    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
