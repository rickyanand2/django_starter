# accounts/templatetags/form_extras.py

from django import template

register = template.Library()


@register.filter
def add_class(field, css):
    attrs = field.field.widget.attrs.copy()
    existing = attrs.get("class", "")
    attrs["class"] = (existing + " " + css).strip() if existing else css
    return field.as_widget(attrs=attrs)


@register.filter
def widget_type(field):
    # e.g. "text", "password", "checkbox", "email"...
    try:
        return field.field.widget.input_type
    except Exception:
        return ""
