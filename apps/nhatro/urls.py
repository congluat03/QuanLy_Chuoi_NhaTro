from django.urls import path
from . import views, admin_views

app_name = 'nhatro'
urlpatterns = [
    path('khuvuc', admin_views.khuvuc_list, name='khuvuc_list'),
    path('khuvuc/chitiet_khuvuc/<int:khuVucId>/', admin_views.chitiet_khuvuc, name='chitiet_khuvuc'),


    path('khuvuc/chitiet_khuvuc/<int:khuVucId>/', admin_views.chitiet_khuvuc, name='chitiet_khuvuc'),
    path('khuvuc/sua/<int:khuVucId>/', admin_views.khuvuc_sua, name='khuvuc_sua'),
    path('khuvuc/them/', admin_views.khuvuc_them, name='khuvuc_them'),
    path('khuvuc/xoa/<int:ma_khu_vuc>/', admin_views.xoa_khuvuc, name='xoa_khuvuc'),

    path("khuvuc/thiet-lap-dich-vu/<int:khu_vuc_id>/", admin_views.thiet_lap_dich_vu, name="thiet_lap_dich_vu"),
    path("khuvuc/thiet-lap-dich-vu/<int:khu_vuc_id>/<int:dich_vu_id>/", admin_views.thiet_lap_dich_vu, name="capnhat_dichvu_khuvuc"),
    
    path('khuvuc/thiet-lap-nguoi-quan-ly/<int:khuVucId>/', admin_views.thietlap_nguoiquanly, name='khuvuc_thiet_lap_nguoi_quan_ly'),
    path('khuvuc/thiet-lap-nguoi-quan-ly/', admin_views.thietlap_nguoiquanly, name='thietlap_nguoiquanly'),
    path('khuvuc/dung_quanly/<int:khuVucId>/', admin_views.dung_quanly, name='dung_quanly'),
]