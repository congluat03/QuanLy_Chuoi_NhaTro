from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from datetime import datetime
from .models import HoaDon
from apps.dichvu.models import ChiSoDichVu, LichSuApDungDichVu, DichVu
from apps.phongtro.models import PhongTro
from django.shortcuts import get_object_or_404
from decimal import Decimal



def hoadon_list(request):
    # Lấy tháng/năm từ request, mặc định là hiện tại
    month = int(request.GET.get('month', datetime.now().month))
    year = int(request.GET.get('year', datetime.now().year))

    # Lấy danh sách hóa đơn theo tháng/năm
    hoa_dons = HoaDon.objects.filter(
        NGAY_LAP_HDON__year=year,
        NGAY_LAP_HDON__month=month
    ).select_related('MA_PHONG').prefetch_related('khautru').order_by('MA_HOA_DON')

    # Phân trang (10 bản ghi/trang)
    paginator = Paginator(hoa_dons, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Tạo danh sách tháng để hiển thị
    month_names = [
        'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
        'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
    ]
    months = [
        {
            'month': i + 1,
            'year': year,
            'short_name': month_names[i],
            'active': i + 1 == month
        }
        for i in range(12)
    ]

    # Hàm tính tiền dịch vụ (điện, nước, khác) dựa trên ChiSoDichVu và LichSuApDungDichVu
    def calculate_service_cost(hoa_don, service_name):
        chi_so_dich_vu = ChiSoDichVu.objects.filter(
            MA_PHONG=hoa_don.MA_PHONG,
            MA_DICH_VU__TEN_DICH_VU=service_name,
            NGAY_GHI_CS__year=year,
            NGAY_GHI_CS__month=month
        ).select_related('MA_DICH_VU').first()
        
        if chi_so_dich_vu and chi_so_dich_vu.CHI_SO_MOI is not None and chi_so_dich_vu.CHI_SO_CU is not None:
            lich_su_dv = LichSuApDungDichVu.objects.filter(
                MA_DICH_VU=chi_so_dich_vu.MA_DICH_VU,
                NGAY_HUY_DV__isnull=True
            ).first()
            if lich_su_dv and lich_su_dv.GIA_DICH_VU_AD:
                usage = chi_so_dich_vu.CHI_SO_MOI - chi_so_dich_vu.CHI_SO_CU
                return usage * lich_su_dv.GIA_DICH_VU_AD
        return Decimal('0.00')

    # Thêm dữ liệu tính toán cho mỗi hóa đơn
    for hoa_don in page_obj:
        hoa_don.tien_dien = calculate_service_cost(hoa_don, 'Điện')
        hoa_don.tien_nuoc = calculate_service_cost(hoa_don, 'Nước')
        hoa_don.tien_dich_vu_khac = sum(
            calculate_service_cost(hoa_don, dv.TEN_DICH_VU)
            for dv in DichVu.objects.exclude(TEN_DICH_VU__in=['Điện', 'Nước'])
        )
        hoa_don.tong_khau_tru = sum(kt.SO_TIEN_KT or Decimal('0.00') for kt in hoa_don.khautru.all())

    # Trạng thái hóa đơn
    status_mapping = {
        'Đã thu tiền': {'text': 'Đã thu tiền', 'color': 'bg-green-600'},
        'Đang nợ': {'text': 'Đang nợ', 'color': 'bg-yellow-500'},
        'Đã hủy': {'text': 'Đã hủy', 'color': 'bg-orange-500'},
        'Chưa thu tiền': {'text': 'Chưa thu tiền', 'color': 'bg-red-600'},
    }

    context = {
        'hoa_dons': page_obj,
        'months': months,
        'current_month': f'{month:02d}/{year}',
        'year': year,
        'status_mapping': status_mapping,
    }
    return render(request, 'admin/hoadon/danhsach_hoadon.html', context)

def them_hoa_don(request):
    if request.method == 'POST':
        # Xử lý form thêm hóa đơn
        ma_phong = request.POST.get('MA_PHONG')
        loai_hoa_don = request.POST.get('LOAI_HOA_DON')
        ngay_lap_hdon = request.POST.get('NGAY_LAP_HDON')
        tien_phong = request.POST.get('TIEN_PHONG', '0')
        tien_dich_vu = request.POST.get('TIEN_DICH_VU', '0')
        tien_coc = request.POST.get('TIEN_COC', '0')
        tien_khau_tru = request.POST.get('TIEN_KHAU_TRU', '0')
        trang_thai_hdon = request.POST.get('TRANG_THAI_HDON')

        # Tính tổng tiền
        tong_tien = Decimal(tien_phong) + Decimal(tien_dich_vu) - Decimal(tien_khau_tru)

        # Tạo hóa đơn mới
        hoa_don = HoaDon.objects.create(
            MA_PHONG_id=ma_phong,
            LOAI_HOA_DON=loai_hoa_don,
            NGAY_LAP_HDON=ngay_lap_hdon,
            TIEN_PHONG=tien_phong,
            TIEN_DICH_VU=tien_dich_vu,
            TIEN_COC=tien_coc,
            TIEN_KHAU_TRU=tien_khau_tru,
            TONG_TIEN=tong_tien,
            TRANG_THAI_HDON=trang_thai_hdon
        )

        # Chuyển hướng đến trang quản lý dịch vụ/khấu trừ
        return redirect('hoa_don_dich_vu', ma_hoa_don=hoa_don.MA_HOA_DON)

    # Hiển thị form thêm
    phong_tro = PhongTro.objects.all()
    context = {
        'phong_tro': phong_tro,
        'trang_thai_choices': ['Đã thu tiền', 'Chưa thu tiền', 'Đang nợ', 'Đã hủy'],
        'loai_hoa_don_choices': ['Hóa đơn phòng', 'Hóa đơn điện', 'Hóa đơn nước', 'Hóa đơn khác'],
    }
    return render(request, 'admin/hoadon/themsua_hoadon.html', context)

def sua_hoa_don(request, ma_hoa_don):
    hoa_don = get_object_or_404(HoaDon, MA_HOA_DON=ma_hoa_don)
    
    if request.method == 'POST':
        # Xử lý form chỉnh sửa hóa đơn
        hoa_don.MA_PHONG_id = request.POST.get('MA_PHONG')
        hoa_don.LOAI_HOA_DON = request.POST.get('LOAI_HOA_DON')
        hoa_don.NGAY_LAP_HDON = request.POST.get('NGAY_LAP_HDON')
        hoa_don.TIEN_PHONG = request.POST.get('TIEN_PHONG', '0')
        hoa_don.TIEN_DICH_VU = request.POST.get('TIEN_DICH_VU', '0')
        hoa_don.TIEN_COC = request.POST.get('TIEN_COC', '0')
        hoa_don.TIEN_KHAU_TRU = request.POST.get('TIEN_KHAU_TRU', '0')
        hoa_don.TRANG_THAI_HDON = request.POST.get('TRANG_THAI_HDON')

        # Tính tổng tiền
        hoa_don.TONG_TIEN = Decimal(hoa_don.TIEN_PHONG) + Decimal(hoa_don.TIEN_DICH_VU) - Decimal(hoa_don.TIEN_KHAU_TRU)

        hoa_don.save()

        # Chuyển hướng đến trang quản lý dịch vụ/khấu trừ
        return redirect('hoa_don_dich_vu', ma_hoa_don=hoa_don.MA_HOA_DON)

    # Hiển thị form chỉnh sửa
    phong_tro = PhongTro.objects.all()
    context = {
        'hoa_don': hoa_don,
        'phong_tro': phong_tro,
        'trang_thai_choices': ['Đã thu tiền', 'Chưa thu tiền', 'Đang nợ', 'Đã hủy'],
        'loai_hoa_don_choices': ['Hóa đơn phòng', 'Hóa đơn điện', 'Hóa đơn nước', 'Hóa đơn khác'],
    }
    return render(request, 'admin/hoadon/themsua_hoadon.html', context)


