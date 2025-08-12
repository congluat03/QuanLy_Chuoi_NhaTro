from django.urls import path
from . import views, admin_views

app_name = 'hopdong'
urlpatterns = [
    path('hopdong', admin_views.hopdong_list, name='hopdong_list'),
    path('hopdong/viewsua/<int:ma_hop_dong>/', admin_views.view_chinh_sua_hop_dong, name='view_chinh_sua_hop_dong'),
    path('hopdong/viewthem/', admin_views.view_them_hop_dong, name='view_them_hop_dong'),
    path('hopdong/sua/<int:ma_hop_dong>/', admin_views.chinh_sua_hop_dong, name='chinh_sua_hop_dong'),
    path('hopdong/them/', admin_views.them_hop_dong, name='them_hop_dong'),
    path('hopdong/xoa-hop-dong/<int:ma_hop_dong>/', admin_views.xoa_hop_dong, name='xoa_hop_dong'),
    path('hopdong/<int:hopdong_id>/', admin_views.view_contract, name='view_hopdong'),


    path('hopdong/kiem-tra-coc-phong/<int:ma_phong>/', admin_views.kiem_tra_coc_phong, name='kiem_tra_coc_phong'),
]