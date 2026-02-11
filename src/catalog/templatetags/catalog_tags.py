from django import template

register = template.Library()


@register.filter
def override_diff(override_val, initial_val):
    """Return 'changed' CSS class if override value differs from initial value."""
    if override_val is None and initial_val is None:
        return ""
    if override_val != initial_val:
        return "changed"
    return ""


@register.filter
def format_dimension(value):
    """Format a dimension value, returning '—' for None."""
    if value is None:
        return "—"
    return f"{value:g}"


@register.filter
def display_val(value):
    """Display a value, showing '—' for None/empty."""
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return value
