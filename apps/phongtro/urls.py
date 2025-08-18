from django.urls import path
from . import views, admin_views

app_name = 'phongtro'
urlpatterns = [
    path('phongtro/', admin_views.phongtro_list, name='phongtro_list'),
    # path('phongtro/<str:ma_khu_vuc>/<int:page_number>/', admin_views.phongtro_list, name='phong_tro_theo_khu_vuc'),
    path('phongtro/view-themsua-phongtro/<int:ma_khu_vuc>/<str:loai>/', admin_views.phongtro_list, name='view_them_phong_tro'),
    path('phongtro/view-themsua-phongtro/<int:ma_khu_vuc>/<str:loai>/<int:ma_phong_tro>/', admin_views.view_themsua_phongtro, name='view_sua_phong_tro'),
    
    path('phongtro/them-phongtro/', admin_views.them_phongtro, name='them_phongtro'),
    path('phongtro/sua-phongtro/<int:ma_phong_tro>/', admin_views.sua_phongtro, name='sua_phongtro'),
    path('phongtro/coc-giu-cho/<int:ma_phong>/', admin_views.view_coc_giu_cho, name='coc_giu_cho'),

    path('phongtro/ghi-so-dich-vu/<int:ma_phong_tro>/', admin_views.ghi_so_dich_vu, name='ghi_so_dich_vu'),

    path('phongtro/xoa-phongtro/<int:ma_phong_tro>/', admin_views.xoa_phong_tro, name='xoa_phongtro'),


    path('phongtro/lap-hop-dong/<int:ma_phong>/', admin_views.view_lap_hop_dong, name='lap_hop_dong'),
    
    # URLs for tin đăng phòng
    path('tin-dang/', admin_views.dang_tin_list, name='dang_tin_list'),
    path('tin-dang/tao/', admin_views.dang_tin_create, name='dang_tin_create'),
    path('tin-dang/<int:ma_tin_dang>/', admin_views.dang_tin_detail, name='dang_tin_detail'),
    path('tin-dang/<int:ma_tin_dang>/sua/', admin_views.dang_tin_edit, name='dang_tin_edit'),
    path('tin-dang/<int:ma_tin_dang>/xoa/', admin_views.dang_tin_delete, name='dang_tin_delete'),
    path('tin-dang/<int:ma_tin_dang>/toggle-status/', admin_views.dang_tin_toggle_status, name='dang_tin_toggle_status'),
]