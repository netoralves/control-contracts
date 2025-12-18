from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css):
    try:
        return field.as_widget(attrs={"class": css})
    except AttributeError:
        return mark_safe(field)


@register.filter(name="replace")
def replace(value, arg):
    """
    Replaces underscores with spaces in a string.
    Usage: {{ value|replace:"_" }} -> replaces _ with space
    For more complex replacements, use a custom tag.
    """
    if not value:
        return value
    
    try:
        if isinstance(value, str):
            # Se o argumento for apenas um caractere, substitui por espaço
            if len(arg) == 1:
                return value.replace(arg, ' ')
            # Se o argumento contém dois pontos, usa como separador old:new
            elif ':' in arg:
                old, new = arg.split(':', 1)
                return value.replace(old, new)
            else:
                return value.replace(arg, ' ')
        return str(value).replace(arg, ' ')
    except Exception:
        return value
