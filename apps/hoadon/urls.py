from django.urls import path
from . import views, admin_views

app_name = 'hoadon'
urlpatterns = [
    path('hoadon', admin_views.hoadon_list, name='hoadon_list'),
    path('hoadon/them/', admin_views.them_hoa_don, name='them_hoa_don'),
    # Chỉnh sửa hóa đơn
    path('hoadon/sua/<int:ma_hoa_don>', admin_views.sua_hoa_don, name='sua_hoa_don'),

    path('hoadon/lay-thong-tin-phong/<int:ma_phong>/', admin_views.lay_thong_tin_phong, name='lay_thong_tin_phong'),

    # # Quản lý dịch vụ và khấu trừ
    # path('hoa-don/<int:ma_hoa_don>/dich-vu/', views.hoa_don_dich_vu, name='hoa_don_dich_vu'),
    # # Lưu khấu trừ
    # path('hoa-don/<int:ma_hoa_don>/khau-tru/save/', views.save_khau_tru, name='save_khau_tru'),
    # # Cập nhật chỉ số dịch vụ
    # path('api/chi-so-dich-vu/<int:ma_chi_so>/update/', views.update_chi_so_dich_vu, name='update_chi_so_dich_vu'),
    # # Cập nhật khấu trừ
    # path('api/khau-tru/<int:ma_khau_tru>/update/', views.update_khau_tru, name='update_khau_tru'),
]