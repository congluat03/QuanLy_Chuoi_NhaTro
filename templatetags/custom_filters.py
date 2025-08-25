from django import template
from datetime import datetime, date

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

@register.filter
def currency_vn(value):
    """Format currency in Vietnamese style with full amount"""
    try:
        value = float(value)
        return "{:,.0f} ₫".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return "0 ₫"

@register.filter
def currency_vn_short(value):
    """Format currency in Vietnamese style with short format (K, M)"""
    try:
        value = float(value)
        if value >= 1000000:
            return "{:.1f} triệu ₫".format(value / 1000000)
        elif value >= 1000:
            return "{:.0f}K ₫".format(value / 1000)
        else:
            return "{:,.0f} ₫".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return "0 ₫"

@register.filter
def date_dd_mm_yy(value):
    """Format date to dd/mm/yy"""
    if not value:
        return "-"
    
    try:
        if isinstance(value, str):
            # Thử parse string thành date
            if 'T' in value:  # ISO format
                value = datetime.fromisoformat(value.replace('Z', '+00:00')).date()
            else:
                value = datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime):
            value = value.date()
        elif not isinstance(value, date):
            return "-"
            
        return value.strftime('%d/%m/%y')
    except (ValueError, AttributeError, TypeError):
        return "-"

@register.filter
def date_dd_mm_yyyy(value):
    """Format date to dd/mm/yyyy"""
    if not value:
        return "-"
    
    try:
        if isinstance(value, str):
            if 'T' in value:  # ISO format
                value = datetime.fromisoformat(value.replace('Z', '+00:00')).date()
            else:
                value = datetime.strptime(value, '%Y-%m-%d').date()
        elif isinstance(value, datetime):
            value = value.date()
        elif not isinstance(value, date):
            return "-"
            
        return value.strftime('%d/%m/%Y')
    except (ValueError, AttributeError, TypeError):
        return "-"

@register.filter
def datetime_dd_mm_yy_hm(value):
    """Format datetime to dd/mm/yy HH:MM"""
    if not value:
        return "-"
    
    try:
        if isinstance(value, str):
            if 'T' in value:  # ISO format
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        elif isinstance(value, date) and not isinstance(value, datetime):
            # Chỉ có date, thêm thời gian mặc định
            value = datetime.combine(value, datetime.min.time())
        elif not isinstance(value, datetime):
            return "-"
            
        return value.strftime('%d/%m/%y %H:%M')
    except (ValueError, AttributeError, TypeError):
        return "-"

@register.filter
def div(value, divisor):
    """Chia hai số"""
    try:
        value = float(value)
        divisor = float(divisor)
        if divisor == 0:
            return 0
        return value / divisor
    except (ValueError, TypeError, ZeroDivisionError):
        return 0