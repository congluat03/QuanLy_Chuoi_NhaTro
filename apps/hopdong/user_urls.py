"""
URL routing cho User Frontend (không phải admin)
"""
from django.urls import path
from . import views

app_name = 'user_hopdong'

urlpatterns = [
    # Views cho user
    path('hop-dong/', views.hop_dong_user_list, name='hop_dong_list'),
    path('hop-dong/<int:ma_hop_dong>/', views.hop_dong_user_detail, name='hop_dong_detail'),
    
    # URL cho khách hàng xác nhận hợp đồng
    path('xac-nhan/<int:ma_hop_dong>/', views.xac_nhan_hop_dong_khach_hang, name='xac_nhan_hop_dong_khach_hang'),
    path('xac-nhan/<int:ma_hop_dong>/success/', views.xac_nhan_thanh_cong, name='xac_nhan_thanh_cong'),
    
    # URL cho khách hàng xem hóa đơn
    path('hoa-don/<int:ma_hoa_don>/', views.xem_hoa_don, name='xem_hoa_don'),
    path('hoa-don/<int:ma_hoa_don>/pdf/', views.xuat_hoa_don_pdf, name='xuat_hoa_don_pdf'),
    
    # URL cho thông tin hợp đồng của khách
    path('thong-tin/<int:ma_hop_dong>/', views.thong_tin_hop_dong, name='thong_tin_hop_dong'),
    
    # API cho user
    path('api/<str:action>/', views.hop_dong_user_api, name='user_api'),
]