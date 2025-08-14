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
    path('admin-profile/', admin_views.admin_profile, name='admin_profile'),
    path('admin-logout/', admin_views.admin_logout, name='admin_logout'),
    path('doi-mat-khau/', admin_views.doi_mat_khau, name='doi_mat_khau'),
    path('chinh-sua-thong-tin/', admin_views.chinh_sua_thong_tin, name='chinh_sua_thong_tin'),
]