from django.urls import path
from . import views, admin_views, view_new

app_name = 'hopdong'
urlpatterns = [
    path('hopdong', admin_views.hopdong_list, name='hopdong_list'),
    path('hopdong/viewsua/<int:ma_hop_dong>/', admin_views.view_chinh_sua_hop_dong, name='view_chinh_sua_hop_dong'),
    path('hopdong/viewthem/', admin_views.view_them_hop_dong, name='view_them_hop_dong'),
    
    # 3 chức năng chỉnh sửa riêng biệt mới
    path('hopdong/sua-thongtin/<int:ma_hop_dong>/', admin_views.sua_thongtin_hopdong, name='sua_thongtin_hopdong'),
    path('hopdong/sua-khachthue/<int:ma_hop_dong>/', admin_views.sua_khachthue_hopdong, name='sua_khachthue_hopdong'),
    path('hopdong/sua-dichvu/<int:ma_hop_dong>/', admin_views.sua_dichvu_hopdong, name='sua_dichvu_hopdong'),
    path('hopdong/api/tim-khach-thue/', admin_views.tim_khach_thue_ajax, name='tim_khach_thue_ajax'),
    path('hopdong/them/', admin_views.them_hop_dong, name='them_hop_dong'),
    path('hopdong/xoa-hop-dong/<int:ma_hop_dong>/', admin_views.xoa_hop_dong, name='xoa_hop_dong'),
    path('hopdong/<int:hopdong_id>/', admin_views.view_contract, name='view_hopdong'),

    # Chức năng mới - xác nhận hợp đồng và sinh hóa đơn
    path('hopdong/xac-nhan/<int:ma_hop_dong>/', view_new.xac_nhan_hop_dong, name='xac_nhan_hop_dong'),
    path('hopdong/chi-tiet/<int:ma_hop_dong>/', admin_views.chi_tiet_hop_dong, name='chi_tiet_hop_dong'),

    path('hopdong/kiem-tra-coc-phong/<int:ma_phong>/', admin_views.kiem_tra_coc_phong, name='kiem_tra_coc_phong'),
    path('hopdong/lay-thong-tin-phong/<int:ma_phong>/', admin_views.lay_thong_tin_phong, name='lay_thong_tin_phong'),
    path('hopdong/tim-khach-thue-co-san/', admin_views.tim_khach_thue_co_san, name='tim_khach_thue_co_san'),
    
    # Workflow URLs - removed workflow_action, using direct endpoints
    path('hopdong/dashboard-stats/', admin_views.dashboard_statistics, name='dashboard_statistics'),
    path('hopdong/gia-han/<int:ma_hop_dong>/', view_new.gia_han_hop_dong, name='gia_han_hop_dong'),
    path('hopdong/bao-ket-thuc/<int:ma_hop_dong>/', view_new.bao_ket_thuc_som, name='bao_ket_thuc_som'),
    path('hopdong/huy-bao-ket-thuc/<int:ma_hop_dong>/', view_new.huy_bao_ket_thuc, name='huy_bao_ket_thuc'),
    
    # Kết thúc hợp đồng - trang mới
    path('hopdong/ket-thuc/<int:ma_hop_dong>/', view_new.view_ket_thuc_hop_dong, name='view_ket_thuc_hop_dong'),
    path('hopdong/ket-thuc-hop-dong/<int:ma_hop_dong>/', view_new.thuc_hien_ket_thuc_hop_dong, name='thuc_hien_ket_thuc_hop_dong'),
    path('hopdong/api/cong-no/<int:ma_hop_dong>/', view_new.api_cong_no_hop_dong, name='api_cong_no_hop_dong'),
    path('hopdong/api/tinh-toan-ket-thuc/<int:ma_hop_dong>/', view_new.api_tinh_toan_ket_thuc, name='api_tinh_toan_ket_thuc'),
    path('hopdong/api/dich-vu/<int:ma_hop_dong>/', view_new.api_lay_dich_vu_hop_dong, name='api_lay_dich_vu_hop_dong'),
    
    
    # API cho hóa đơn
    path('hopdong/api/export-invoice-pdf/<int:ma_hoa_don>/', admin_views.export_invoice_pdf, name='export_invoice_pdf'),
    path('hopdong/api/send-invoice-email/<int:ma_hoa_don>/', admin_views.send_invoice_email, name='send_invoice_email'),
    
    
]