from projects.models import Category, Project
from taggit.models import Tag


def categories_processor(request):
    """Makes category list and search project suggestions available in every template."""
    categories = Category.objects.all().order_by("name")
    project_titles = list(Project.objects.filter(status=Project.Status.RUNNING).values_list("title", flat=True))
    tag_names = list(Tag.objects.values_list("name", flat=True))
    return {
        "nav_categories": categories,
        "nav_search_suggestions": project_titles + tag_names,
    }
