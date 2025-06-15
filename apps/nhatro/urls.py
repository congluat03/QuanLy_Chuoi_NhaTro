from django.urls import path
from . import views, admin_views

app_name = 'nhatro'
urlpatterns = [
    path('khuvuc', admin_views.khuvuc_list, name='khuvuc_list'),
    path('khuvuc/chitiet_khuvuc/<int:khuVucId>/', admin_views.chitiet_khuvuc, name='chitiet_khuvuc'),


    path('khuvuc/chitiet_khuvuc/<int:khuVucId>/', admin_views.chitiet_khuvuc, name='chitiet_khuvuc'),
    path('khuvuc/sua/<int:khuVucId>/', admin_views.khuvuc_sua, name='khuvuc_sua'),
    path('khuvuc/thiet-lap-dich-vu/<int:khuVucId>/', admin_views.khuvuc_thiet_lap_dich_vu, name='khuvuc_thiet_lap_dich_vu'),
    path('khuvuc/thiet-lap-nguoi-quan-ly/<int:khuVucId>/', admin_views.khuvuc_thiet_lap_nguoi_quan_ly, name='khuvuc_thiet_lap_nguoi_quan_ly'),
    path('khuvuc/them/', admin_views.khuvuc_them, name='khuvuc_them'),
]