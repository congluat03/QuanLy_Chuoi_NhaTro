from django.urls import path
from . import views, admin_views

app_name = 'phongtro'
urlpatterns = [
    path('phongtro', admin_views.phongtro_list, name='phongtro_list'),
    path('phong-tro/khu-vuc/<str:ma_khu_vuc>/<int:page_number>/', admin_views.phong_tro_theo_khu_vuc, name='phong_tro_theo_khu_vuc'),
    path('phongtro/view-themsua-phongtro/<int:ma_khu_vuc>/<str:loai>/', admin_views.view_themsua_phongtro, name='view_them_phong_tro'),
    path('phongtro/view-themsua-phongtro/<int:ma_khu_vuc>/<str:loai>/<int:ma_phong_tro>/', admin_views.view_themsua_phongtro, name='view_sua_phong_tro'),
    path('phongtro/them-phongtro/<str:loai>/', admin_views.them_phongtro, name='them_phongtro'),
    path('phongtro/sua-phongtro/<int:ma_phong_tro>/', admin_views.sua_phongtro, name='sua_phongtro'),
    path('phongtro/<int:ma_phong>/coc-giu-cho/', admin_views.view_coc_giu_cho, name='coc_giu_cho'),
]