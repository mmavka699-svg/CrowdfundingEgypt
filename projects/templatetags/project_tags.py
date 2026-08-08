from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


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
