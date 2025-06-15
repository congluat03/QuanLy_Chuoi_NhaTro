from django import template

register = template.Library()

@register.filter
def lookup(dict, key):
    return dict.get(key)
@register.filter
def split(value, delimiter):
    """Chia chuỗi thành danh sách dựa trên delimiter."""
    return value.split(delimiter)
@register.filter
def map(iterable, key):
    """Lấy giá trị của key từ danh sách dictionary."""
    try:
        return [item[key] for item in iterable]
    except (TypeError, KeyError):
        return []