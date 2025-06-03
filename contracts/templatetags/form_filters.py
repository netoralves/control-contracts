from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css):
    try:
        return field.as_widget(attrs={"class": css})
    except AttributeError:
        return mark_safe(field)
