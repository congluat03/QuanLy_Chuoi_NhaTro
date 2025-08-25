from django.urls import path
from . import user_views

app_name = 'user_phongtro'

urlpatterns = [
    # Tìm kiếm và xem phòng
    path('tim-phong/', user_views.tim_phong, name='tim_phong'),
    path('chi-tiet-phong/<int:ma_phong>/', user_views.chi_tiet_phong, name='chi_tiet_phong'),
    
    # Đặt phòng
    path('dat-phong/<int:ma_phong>/', user_views.dat_phong, name='dat_phong'),
    path('xac-nhan-dat-phong/<int:ma_dat_phong>/', user_views.xac_nhan_dat_phong, name='xac_nhan_dat_phong'),
    
    # Tra cứu
    path('tra-cuu-dat-phong/', user_views.tra_cuu_dat_phong, name='tra_cuu_dat_phong'),
    
    # API endpoints
    path('api/phong-autocomplete/', user_views.api_phong_autocomplete, name='api_phong_autocomplete'),
    path('api/location-autocomplete/', user_views.api_location_autocomplete, name='api_location_autocomplete'),
    path('api/phong-info/<int:ma_phong>/', user_views.api_phong_info, name='api_phong_info'),
    
    # Location API endpoints
    path('api/provinces/', user_views.api_provinces, name='api_provinces'),
    path('api/districts/<str:province_code>/', user_views.api_districts, name='api_districts'),
    path('api/wards/<str:province_code>/<str:district_code>/', user_views.api_wards, name='api_wards'),
]