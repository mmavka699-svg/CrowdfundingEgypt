from projects.models import Category


def categories_processor(request):
    """Makes the category list available in every template (navbar dropdown, footer, etc.)."""
    return {"nav_categories": Category.objects.all().order_by("name")}
