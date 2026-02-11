# core/templatetags/ui_extras.py
from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css):
    """
    Append one or more CSS classes to a form field widget.
    Usage: {{ form.email|add_class:"form-control is-invalid" }}
    """
    widget = field.field.widget
    existing = widget.attrs.get("class", "")
    new_value = (existing + " " + css).strip() if existing else css
    # merge other existing attrs while overriding class
    attrs = {**widget.attrs, "class": new_value}
    return field.as_widget(attrs=attrs)


@register.filter(name="attr")
def attr(field, arg):
    """
    Set/override a single attribute on a widget.
    Usage: {{ form.email|attr:"placeholder:you@example.com" }}
    """
    try:
        key, value = arg.split(":", 1)
    except ValueError:
        return field
    attrs = {**field.field.widget.attrs, key: value}
    return field.as_widget(attrs=attrs)
