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


@register.filter
def format_number(value):
    """Format a number: int if whole, decimal if fractional, empty if None."""
    if value is None:
        return ""
    try:
        f = float(value)
        return str(int(f)) if f == int(f) else str(f)
    except (ValueError, TypeError):
        return str(value)


@register.filter
def dim_error_class(value):
    """Return error CSS class when a dimension/weight/cpack value is 0 or missing."""
    if value is None or value == "":
        return "lot-input-missing"
    try:
        if float(value) == 0:
            return "lot-input-missing"
    except (ValueError, TypeError):
        pass
    return ""


@register.filter
def show_ref(field):
    """Show original ref only when changed and original > 0."""
    if not field.get("changed"):
        return False
    orig = field.get("original")
    if orig is None or orig == "":
        return False
    try:
        return float(orig) > 0
    except (ValueError, TypeError):
        return bool(orig)


CPACK_MAP = {
    "1": ("NF", "cpack-nf"),
    "2": ("LF", "cpack-lf"),
    "3": ("F", "cpack-f"),
    "4": ("VF", "cpack-vf"),
    "PBO": ("PBO", "cpack-pbo"),
}


@register.filter
def cpack_label(value):
    """Return the display label for a cpack value."""
    if value is None or value == "":
        return "—"
    label, _ = CPACK_MAP.get(str(value), (str(value), ""))
    return label


@register.filter
def cpack_class(value):
    """Return the CSS class for a cpack value."""
    if value is None or value == "":
        return ""
    _, cls = CPACK_MAP.get(str(value), ("", ""))
    return cls
