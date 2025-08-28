from django.urls import path
from . import views, admin_views

app_name = 'dungchung'
urlpatterns = [
    # Trang chủ
    path('', views.trang_chu, name='trang_chu'),
    
    # Authentication với TaiKhoan
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Authentication cũ (giữ lại để tương thích)
    path('custom-login/', views.custom_login_view, name='custom_login'),
    
    # Profile và settings
    path('profile/', views.user_profile_view, name='profile'),
    path('cap-nhat-profile/', views.cap_nhat_profile_view, name='cap_nhat_profile'),
    path('doi-mat-khau/', views.user_doi_mat_khau_view, name='doi_mat_khau'),
    
    # User views for contract and invoices
    path('hop-dong/', views.user_hop_dong_view, name='user_hop_dong'),
    path('hoa-don/', views.user_hoa_don_list_view, name='user_hoa_don_list'),
    path('hoa-don/<int:ma_hoa_don>/', views.user_hoa_don_detail_view, name='user_hoa_don_detail'),
    path('thanh-toan-hoa-don/<int:ma_hoa_don>/', views.thanh_toan_hoa_don_view, name='thanh_toan_hoa_don'),
    
    # Chatbot API
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    
    # Admin views
    path('admin-profile/', admin_views.admin_profile, name='admin_profile'),
    path('admin-logout/', admin_views.admin_logout, name='admin_logout'),
    path('admin-doi-mat-khau/', admin_views.doi_mat_khau, name='admin_doi_mat_khau'),
    path('chinh-sua-thong-tin/', admin_views.chinh_sua_thong_tin, name='chinh_sua_thong_tin'),
]