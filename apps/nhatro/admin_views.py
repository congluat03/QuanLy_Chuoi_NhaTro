from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import KhuVuc, NhaTro
from apps.dichvu.models import DichVu, LichSuApDungDichVu
from apps.thanhvien.models import NguoiQuanLy, LichSuQuanLy
from django.http import HttpResponse
from django.contrib import messages

def khuvuc_list(request):
    # Lấy danh sách dịch vụ và khu vực
    dich_vus = DichVu.objects.order_by('MA_DICH_VU')
    khu_vucs = KhuVuc.objects.order_by('MA_KHU_VUC')
    
    # Phân trang: 10 mục mỗi trang
    dich_vus_paginator = Paginator(dich_vus, 8)
    khu_vucs_paginator = Paginator(khu_vucs, 8)
    
    # Lấy số trang riêng cho khu vực và dịch vụ
    dich_vu_page_number = request.GET.get('dich_vu_page')
    khu_vuc_page_number = request.GET.get('khu_vuc_page')
    
    dich_vus_page = dich_vus_paginator.get_page(dich_vu_page_number)
    khu_vucs_page = khu_vucs_paginator.get_page(khu_vuc_page_number)
    
    context = {
        'dich_vus': dich_vus_page,
        'khu_vucs': khu_vucs_page,
    }
    return render(request, 'admin/khuvuc/danhsach_khuvuc.html', context)

def khuvuc_sua(request, khuVucId):
    try:
        khu_vuc = KhuVuc.objects.get(MA_KHU_VUC=khuVucId)
    except KhuVuc.DoesNotExist:
        messages.error(request, "Khu vực không tồn tại.")
        return redirect('dashboard_khuvuc')  # Thay bằng tên URL đúng trong hệ thống của bạn

    if request.method == "POST":
        ten_khu_vuc = request.POST.get("TEN_KHU_VUC")
        cap1 = request.POST.get("DV_HANH_CHINH_CAP1")
        cap2 = request.POST.get("DV_HANH_CHINH_CAP2")
        cap3 = request.POST.get("DV_HANH_CHINH_CAP3")

        khu_vuc.TEN_KHU_VUC = ten_khu_vuc
        khu_vuc.DV_HANH_CHINH_CAP1 = cap1
        khu_vuc.DV_HANH_CHINH_CAP2 = cap2
        khu_vuc.DV_HANH_CHINH_CAP3 = cap3
        khu_vuc.save()

        messages.success(request, "Cập nhật khu vực thành công.")
        return redirect("nhatro:khuvuc_list")

    return render(request, 'admin/khuvuc/themsua_khuvuc.html', {'khu_vuc': khu_vuc})
def khuvuc_them(request):
    if request.method == "POST":
        ten_khu_vuc = request.POST.get("TEN_KHU_VUC")
        cap1 = request.POST.get("DV_HANH_CHINH_CAP1")
        cap2 = request.POST.get("DV_HANH_CHINH_CAP2")
        cap3 = request.POST.get("DV_HANH_CHINH_CAP3")
        trang_thai = 'đang hoạt động' # Mặc định là 1 (hoạt động)
        # Lấy nhà trọ mặc định hoặc từ user đang đăng nhập
        nha_tro = get_object_or_404(NhaTro, pk=1)

        khu_vuc = KhuVuc.objects.create(
            MA_NHA_TRO=nha_tro,
            TEN_KHU_VUC=ten_khu_vuc,
            TRANG_THAI_KV=trang_thai,
            DV_HANH_CHINH_CAP1=cap1,
            DV_HANH_CHINH_CAP2=cap2,
            DV_HANH_CHINH_CAP3=cap3
        )

        messages.success(request, "Thêm khu vực thành công.")
        return redirect("nhatro:khuvuc_list")

    return render(request, 'admin/khuvuc/themsua_khuvuc.html', {'khu_vuc': None})

def xoa_khuvuc(request, ma_khu_vuc):
    khu_vuc = get_object_or_404(KhuVuc, MA_KHU_VUC=ma_khu_vuc)
    
    if request.method == 'POST':
        # Kiểm tra xem khu vực có phòng trọ liên quan không
        if khu_vuc.ds_phongtro.exists():
            messages.error(request, f"Khu vực '{khu_vuc.TEN_KHU_VUC}' không thể xóa vì đang có phòng trọ liên quan. Vui lòng xóa các phòng trọ trước khi xóa khu vực.")
            return redirect('nhatro:khuvuc_list')
        
        # Xóa khu vực (các dịch vụ liên quan sẽ tự động bị xóa do on_delete=models.CASCADE)
        khu_vuc_name = khu_vuc.TEN_KHU_VUC or f"Khu vực {khu_vuc.MA_KHU_VUC}"
        khu_vuc.delete()
        messages.success(request, f"Khu vực '{khu_vuc_name}' đã được xóa thành công.")
        return redirect('nhatro:khuvuc_list')
    
    # Nếu không phải POST, hiển thị trang xác nhận xóa
    context = {
        'khu_vuc': khu_vuc,
    }
    return redirect('nhatro:khuvuc_list')






def khuvuc_thiet_lap_dich_vu(request, khuVucId):
    if request.method == 'POST':
        makhuvuc = request.POST.get('MA_KHU_VUC')
        for ma_ap_dung_dv in request.POST.getlist('MA_AP_DUNG_DV'):
            dich_vu_khu_vuc = get_object_or_404(LichSuApDungDichVu, MA_AP_DUNG_DV=ma_ap_dung_dv)
            dich_vu_khu_vuc.GIA_DICH_VU_AD = request.POST.get(f'GIA_DICH_VU_AD[{ma_ap_dung_dv}]')
            dich_vu_khu_vuc.LOAI_DICH_VU_AD = request.POST.get(f'LOAI_DICH_VU_AD[{ma_ap_dung_dv}]')
            dich_vu_khu_vuc.NGAY_AP_DUNG_DV = request.POST.get(f'NGAY_AP_DUNG_DV[{ma_ap_dung_dv}]')
            dich_vu_khu_vuc.NGAY_HUY_DV = request.POST.get(f'NGAY_HUY_DV[{ma_ap_dung_dv}]') or None
            dich_vu_khu_vuc.save()
        return redirect('nhatro:chitiet_khuvuc', MA_KHU_VUC=makhuvuc)  # Adjusted URL namespace
    return HttpResponse(status=405)

def khuvuc_thiet_lap_nguoi_quan_ly(request, khuVucId):
    if request.method == 'POST':
        makhuvuc = request.POST.get('MA_KHU_VUC')
        khu_vuc = get_object_or_404(KhuVuc, MA_KHU_VUC=makhuvuc)
        ma_quan_ly = request.POST.get('MA_QUAN_LY')
        ngay_bat_dau_ql = request.POST.get('NGAY_BAT_DAU_QL')
        ngay_ket_thuc_ql = request.POST.get('NGAY_KET_THUC_QL') or None
        ly_do_ket_thuc = request.POST.get('LY_DO_KET_THUC') or None
        
        # Create or update LichSuQuanLy record
        LichSuQuanLy.objects.update_or_create(
            MA_KHU_VUC=khu_vuc,
            MA_QUAN_LY_id=ma_quan_ly,
            defaults={
                'NGAY_BAT_DAU_QL': ngay_bat_dau_ql,
                'NGAY_KET_THUC_QL': ngay_ket_thuc_ql,
                'LY_DO_KET_THUC': ly_do_ket_thuc,
            }
        )
        return redirect('nhatro:chitiet_khuvuc', MA_KHU_VUC=makhuvuc)
    return HttpResponse(status=405)


def chitiet_khuvuc(request, khuVucId):
    # Tìm khu vực theo MA_KHU_VUC
    khu_vuc = get_object_or_404(KhuVuc, MA_KHU_VUC=khuVucId)
    so_luong_phong_tro = khu_vuc.ds_phongtro.count()
    dich_vu_khu_vucs = LichSuApDungDichVu.objects.filter(MA_KHU_VUC=khuVucId).select_related('MA_DICH_VU').order_by('-MA_AP_DUNG_DV')
    quan_lys = NguoiQuanLy.objects.all()  # Lấy danh sách quản lý cho select

    context = {
        'khu_vuc': khu_vuc,
        'so_luong_phong_tro': so_luong_phong_tro,
        'dich_vu_khu_vucs': dich_vu_khu_vucs,
        'quan_lys': quan_lys,
    }
    return render(request, 'admin/khuvuc/chitiet_khuvuc.html', context)
