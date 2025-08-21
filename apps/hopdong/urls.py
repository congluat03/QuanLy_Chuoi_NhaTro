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

    # Chức năng mới - xác nhận hợp đồng và sinh hóa đơn
    path('hopdong/xac-nhan/<int:ma_hop_dong>/', admin_views.xac_nhan_hop_dong, name='xac_nhan_hop_dong'),
    path('hopdong/chi-tiet/<int:ma_hop_dong>/', admin_views.chi_tiet_hop_dong, name='chi_tiet_hop_dong'),
    path('hopdong/sinh-lai-hoa-don/<int:ma_hop_dong>/', admin_views.sinh_lai_hoa_don_bat_dau, name='sinh_lai_hoa_don_bat_dau'),

    path('hopdong/kiem-tra-coc-phong/<int:ma_phong>/', admin_views.kiem_tra_coc_phong, name='kiem_tra_coc_phong'),
    
    # Workflow URLs
    path('hopdong/workflow-action/', admin_views.workflow_action, name='workflow_action'),
    path('hopdong/dashboard-stats/', admin_views.dashboard_statistics, name='dashboard_statistics'),
    path('hopdong/gia-han/<int:ma_hop_dong>/', admin_views.gia_han_hop_dong, name='gia_han_hop_dong'),
    
    
    # API cho hóa đơn
    path('hopdong/api/export-invoice-pdf/<int:ma_hoa_don>/', admin_views.export_invoice_pdf, name='export_invoice_pdf'),
    path('hopdong/api/send-invoice-email/<int:ma_hoa_don>/', admin_views.send_invoice_email, name='send_invoice_email'),
    
    
    # URLs cho tạo hóa đơn bắt đầu theo hợp đồng
    path('hopdong/thiet-lap-hoa-don-bat-dau/<int:ma_hop_dong>/', admin_views.thiet_lap_hoa_don_bat_dau_hop_dong, name='thiet_lap_hoa_don_bat_dau_hop_dong'),
    path('hopdong/xoa-hoa-don-bat-dau/<int:ma_hop_dong>/', admin_views.xoa_hoa_don_bat_dau, name='xoa_hoa_don_bat_dau'),
    path('hopdong/xem-hoa-don-bat-dau/<int:ma_hop_dong>/', admin_views.xem_hoa_don_bat_dau, name='xem_hoa_don_bat_dau'),
]