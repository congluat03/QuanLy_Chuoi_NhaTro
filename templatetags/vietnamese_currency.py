# apps/hoadon/templatetags/vietnamese_currency.py
from django import template

register = template.Library()

@register.filter
def vnd(value):
    try:
        value = float(value)
        return "{:,.0f} ₫".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return "0 ₫"
