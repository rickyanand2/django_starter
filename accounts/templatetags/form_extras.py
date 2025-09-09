# accounts/templatetags/form_extras.py
from django import template
from django.forms.boundfield import BoundField

register = template.Library()


@register.filter
def add_class(field, css):
    """Add CSS class to a form field widget safely."""
    if not isinstance(field, BoundField):
        # If someone passes a string or non-field, just return it as-is
        return field
    attrs = field.field.widget.attrs.copy()
    existing = attrs.get("class", "")
    attrs["class"] = (existing + " " + css).strip() if existing else css
    return field.as_widget(attrs=attrs)
