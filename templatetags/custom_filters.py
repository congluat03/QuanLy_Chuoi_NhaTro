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
@register.filter
def filter_dich_vu(lich_su_qs, ma_dich_vu):
    return lich_su_qs.filter(MA_DICH_VU__MA_DICH_VU=ma_dich_vu, NGAY_HUY_DV__isnull=True).first()