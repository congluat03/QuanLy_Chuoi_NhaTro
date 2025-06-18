from django.urls import path
from . import views, admin_views

app_name = 'dichvu'
urlpatterns = [
    path('dichvu', admin_views.dichvu_list, name='dichvu_list'),
    path('dichvu/thongke-dichvu', admin_views.thong_ke_dich_vu, name='thong_ke_dich_vu'),
    path('dichvu/xuat-thong-ke-dich-vu/', admin_views.export_thong_ke_dich_vu, name='export_thong_ke_dich_vu'),

    path('dichvu/view-them/', admin_views.view_them_moi_dich_vu, name='view_them_dich_vu'),
    path('dichvu/view-sua/<int:ma_dich_vu>/', admin_views.view_sua_dich_vu, name='view_sua_dich_vu'),
    path('dichvu/them/', admin_views.them_dich_vu, name='them_dich_vu'),
    path('dichvu/sua/<int:ma_dich_vu>/', admin_views.sua_dich_vu, name='sua_dich_vu'),

    path('dichvu/xoa/<int:ma_dich_vu>/', admin_views.xoa_dich_vu, name='xoa_dich_vu')

]