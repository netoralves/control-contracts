# contracts/templatetags/math_extras.py
from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def multiply(value, arg):
    """Multiply value by arg."""
    try:
        if value is None:
            return Decimal("0")
        return Decimal(str(value)) * Decimal(str(arg))
    except Exception:
        return Decimal("0")


@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    try:
        if value is None:
            return Decimal("0")
        return Decimal(str(value)) - Decimal(str(arg))
    except Exception:
        return Decimal("0")


@register.filter
def currency_br(value):
    """Format numbers as Brazilian Real currency."""
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return "R$ 0,00"

    quantized = number.quantize(Decimal("0.01"))
    formatted = f"{quantized:,.2f}"
    formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"
