from django.urls import path
from . import views, admin_views

app_name = 'khachthue'
urlpatterns = [
    # Danh sách khách thuê
    path('khachthue', admin_views.khachthue_list, name='khachthue_list'),

    # Thêm khách thuê mới (với phòng/hợp đồng)
    path('khachthue/viewthem/', admin_views.them_khach_thue, name='view_them'),
    path('khachthue/them/', admin_views.them_khach_thue, name='them_khach_thue'),
    
    
    # Sửa thông tin cá nhân khách thuê (chỉ thông tin trong bảng khách thuê)
    path('khachthue/sua_thong_tin/<int:ma_khach_thue>/', admin_views.sua_thong_tin_khach_thue, name='sua_thong_tin_khach_thue'),

    # Rời đi và chuyển phòng (chỉ cho khách thuê không phải chủ hợp đồng)
    path('khachthue/roi_di_chuyen_phong/<int:ma_khach_thue>/', admin_views.roi_di_chuyen_phong, name='roi_di_chuyen_phong'),
    path('khachthue/roi_di/<int:ma_khach_thue>/<int:ma_lich_su>/', admin_views.roi_di, name='roi_di'),
    path('khachthue/chuyen_phong/<int:ma_khach_thue>/<int:ma_lich_su>/', admin_views.chuyen_phong, name='chuyen_phong'),

    # Các chức năng khác
    path('khachthue/xoa/<str:ma_khach_thue>/', admin_views.xoa_khach_thue, name='xoa_khach_thue'),
    path('khachthue/cccd/<str:ma_khach_thue>/', admin_views.view_cccd, name='view_CCCD'),

    # API endpoints
    path('khachthue/api/search/', admin_views.search_khach_thue, name='search_khach_thue'),
]