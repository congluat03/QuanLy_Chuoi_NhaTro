from django.urls import path
from . import views, admin_views

app_name = 'khachthue'
urlpatterns = [
    path('khachthue', admin_views.khachthue_list, name='khachthue_list'),

    path('khachthue/viewsua/<int:ma_khach_thue>/', admin_views.view_sua_thong_tin, name='viewsua'),
    path('khachthue/sua_khach_thue/<int:ma_khach_thue>/', admin_views.view_sua_thong_tin, name='sua_khach_thue'),

    
    path('khachthue/viewthem/', admin_views.view_them_khach_thue, name='view_them'),
    path('khachthue/them/', admin_views.view_them_khach_thue, name='them_khach_thue'),
]