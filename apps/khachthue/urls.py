from django.urls import path
from . import views, admin_views

app_name = 'khachthue'
urlpatterns = [
    path('khachthue', admin_views.khachthue_list, name='khachthue_list'),

    path('khachthue/viewsua/<int:ma_khach_thue>/<int:maphong>', admin_views.sua_khach_thue, name='viewsua'),
    path('khachthue/sua_khach_thue/<int:ma_khach_thue>/', admin_views.sua_khach_thue, name='sua_khach_thue'),

    
    path('khachthue/viewthem/', admin_views.them_khach_thue, name='view_them'),
    path('khachthue/them/', admin_views.them_khach_thue, name='them_khach_thue'),
    path('khachthue/xoa/<str:ma_khach_thue>/', admin_views.xoa_khach_thue, name='xoa_khach_thue'),
    path('khachthue/viewCCCD/<str:ma_khach_thue>', admin_views.view_cccd, name='view_CCCD'),
]