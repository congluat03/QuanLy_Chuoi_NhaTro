from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from datetime import datetime
from django.utils import timezone
from .models import HoaDon, KhauTru
from apps.dichvu.models import ChiSoDichVu, LichSuApDungDichVu, DichVu
from apps.phongtro.models import PhongTro
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.db.models import Q
from apps.hopdong.models import HopDong
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.contrib import messages



def get_phongtro_list():
    return PhongTro.objects.filter(
        Q(hopdong__TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc', 'Đã xác nhận'])
    ).distinct()
def get_dich_vu_ap_dung(ma_khu_vuc, ma_phong, current_month=None):
    errors = []
    dich_vu_list = []

    try:
        # Thiết lập current_month nếu không được cung cấp
        if current_month is None:
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = current_month + relativedelta(months=1)

        # Lấy danh sách dịch vụ áp dụng
        dich_vu_ap_dung, dich_vu_errors = LichSuApDungDichVu.get_dich_vu_ap_dung(ma_khu_vuc)
        if dich_vu_errors:
            errors.extend(dich_vu_errors)
            return [], errors

        # Tính toán chi tiết dịch vụ
        for dv in dich_vu_ap_dung:
            chi_so_data, chi_so_errors = ChiSoDichVu.tinh_chi_so_dich_vu(dv, ma_phong, current_month, next_month)
            if chi_so_errors:
                errors.extend(chi_so_errors)
                continue
            if chi_so_data:
                dich_vu_list.append(chi_so_data)
        return dich_vu_list, errors

    except Exception as e:
        errors.append(f"Lỗi xử lý dịch vụ áp dụng: {str(e)}")
        return [], errors
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
        try:
            with transaction.atomic():
                # Lấy dữ liệu từ form
                data = {
                    'MA_PHONG': request.POST.get('MA_PHONG'),
                    'LOAI_HOA_DON': request.POST.get('LOAI_HOA_DON'),
                    'NGAY_LAP_HDON': request.POST.get('NGAY_LAP_HDON'),
                    'TRANG_THAI_HDON': request.POST.get('TRANG_THAI_HDON'),
                    'TIEN_PHONG': request.POST.get('TIEN_PHONG'),
                    'TIEN_DICH_VU': request.POST.get('TIEN_DICH_VU'),
                    'TIEN_COC': request.POST.get('TIEN_COC'),
                    'TIEN_KHAU_TRU': request.POST.get('TIEN_KHAU_TRU'),
                    'TONG_TIEN': request.POST.get('TONG_TIEN')
                }
                

                chi_so_dich_vu_list = []
                index = 0
                while f'chi_so_dich_vu[{index}][MA_CHI_SO]' in request.POST:
                    chi_so = {
                        'MA_DICH_VU': request.POST.get(f'chi_so_dich_vu[{index}][MA_DICH_VU]', ''),
                        'MA_CHI_SO': request.POST.get(f'chi_so_dich_vu[{index}][MA_CHI_SO]', ''),
                        'CHI_SO_CU': request.POST.get(f'chi_so_dich_vu[{index}][CHI_SO_CU]', '0'),
                        'CHI_SO_MOI': request.POST.getlist(f'chi_so_dich_vu[{index}][CHI_SO_MOI]')[0],
                        'SO_DICH_VU': request.POST.get(f'chi_so_dich_vu[{index}][SO_DICH_VU]', '0'),
                        'THANH_TIEN': request.POST.get(f'chi_so_dich_vu[{index}][THANH_TIEN]', '0')
                    }
                    chi_so_dich_vu_list.append(chi_so)
                    index += 1
                # return JsonResponse({'chi_so_dich_vu': chi_so_dich_vu_list})
                # return JsonResponse(dict(request.POST))
                # Lấy danh sách khấu trừ
                khau_tru_list = []
                index = 0
                while f'khautru[{index}][NGAYKHAUTRU]' in request.POST:
                    khau_tru = {
                        'NGAYKHAUTRU': request.POST.get(f'khautru[{index}][NGAYKHAUTRU]', ''),
                        'LOAI_KHAU_TRU': request.POST.get(f'khautru[{index}][LOAI_KHAU_TRU]', ''),
                        'SO_TIEN_KT': request.POST.get(f'khautru[{index}][SO_TIEN_KT]', '0'),
                        'LY_DO_KHAU_TRU': request.POST.get(f'khautru[{index}][LY_DO_KHAU_TRU]', '')
                    }
                    khau_tru_list.append(khau_tru)
                    index += 1
                # return JsonResponse({'khau_tru_list': khau_tru_list})
                # Gọi phương thức model để tạo hóa đơn
                hoa_don, errors = HoaDon.validate_and_create(data, chi_so_dich_vu_list, khau_tru_list)

                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return render(request, 'admin/hoadon/themsua_hoadon.html', {
                        'phong_tro': PhongTro.objects.all(),
                        'chi_so_dich_vu': chi_so_dich_vu_list,
                        'khau_tru': khau_tru_list,
                        'form_data': data
                    })

                messages.success(request, 'Thêm hóa đơn thành công!')
                return redirect('hoadon:hoadon_list')

        except Exception as e:
            messages.error(request, f'Lỗi khi thêm hóa đơn: {str(e)}')
            return render(request, 'admin/hoadon/themsua_hoadon.html', {
                'phong_tro': PhongTro.objects.all(),
                'chi_so_dich_vu': chi_so_dich_vu_list,
                'khau_tru': khau_tru_list,
                'form_data': data
            })


    # Hiển thị form thêm
    phong_tro = get_phongtro_list()
    
    context = {
        'phong_tro': phong_tro,
        'trang_thai_choices': ['Đã thu tiền', 'Chưa thu tiền', 'Đang nợ', 'Đã hủy'],
        'loai_hoa_don_choices': ['Hóa đơn phòng', 'Hóa đơn điện', 'Hóa đơn nước', 'Hóa đơn khác'],
    }
    return render(request, 'admin/hoadon/themsua_hoadon.html', context)

def sua_hoa_don(request, ma_hoa_don):
    hoa_don = get_object_or_404(HoaDon, MA_HOA_DON=ma_hoa_don)
    phong = PhongTro.objects.get(MA_PHONG=hoa_don.MA_PHONG.MA_PHONG)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Lấy dữ liệu từ form
                data = {
                    'MA_PHONG': request.POST.get('MA_PHONG'),
                    'LOAI_HOA_DON': request.POST.get('LOAI_HOA_DON'),
                    'NGAY_LAP_HDON': request.POST.get('NGAY_LAP_HDON'),
                    'TRANG_THAI_HDON': request.POST.get('TRANG_THAI_HDON'),
                    'TIEN_PHONG': request.POST.get('TIEN_PHONG'),
                    'TIEN_DICH_VU': request.POST.get('TIEN_DICH_VU'),
                    'TIEN_COC': request.POST.get('TIEN_COC'),
                    'TIEN_KHAU_TRU': request.POST.get('TIEN_KHAU_TRU'),
                    'TONG_TIEN': request.POST.get('TONG_TIEN')
                }

                chi_so_dich_vu_list = []
                index = 0
                while f'chi_so_dich_vu[{index}][MA_CHI_SO]' in request.POST:
                    ma_chi_so = request.POST.get(f'chi_so_dich_vu[{index}][MA_CHI_SO]', '')
                    # Bỏ qua nếu ma_chi_so rỗng, None, hoặc "None"
                    if not ma_chi_so or ma_chi_so == 'None':
                        index += 1
                        continue
                    chi_so = {
                        'MA_DICH_VU': request.POST.get(f'chi_so_dich_vu[{index}][MA_DICH_VU]', ''),
                        'MA_CHI_SO': request.POST.get(f'chi_so_dich_vu[{index}][MA_CHI_SO]', ''),
                        'CHI_SO_CU': request.POST.get(f'chi_so_dich_vu[{index}][CHI_SO_CU]', '0'),
                        'CHI_SO_MOI': request.POST.get(f'chi_so_dich_vu[{index}][CHI_SO_MOI]', '0'),
                        'SO_DICH_VU': request.POST.get(f'chi_so_dich_vu[{index}][SO_DICH_VU]', '0'),
                        'THANH_TIEN': request.POST.get(f'chi_so_dich_vu[{index}][THANH_TIEN]', '0')
                    }
                    chi_so_dich_vu_list.append(chi_so)
                    index += 1
                # return JsonResponse({'chi_so_dich_vu': chi_so_dich_vu_list})
                # return JsonResponse(dict(request.POST))
                


                khau_tru_list = []
                index = 0
                while f'khautru[{index}][NGAYKHAUTRU]' in request.POST:
                    ngay_str = request.POST.get(f'khautru[{index}][NGAYKHAUTRU]', '')
                    try:
                        ngay_khau_tru = datetime.strptime(ngay_str, "%Y-%m-%d").date() if ngay_str else None
                    except ValueError:
                        ngay_khau_tru = None
                    khau_tru = {
                        'MA_KHAU_TRU': request.POST.get(f'khautru[{index}][MA_KHAU_TRU]', ''),
                        'NGAYKHAUTRU': ngay_khau_tru,
                        'LOAI_KHAU_TRU': request.POST.get(f'khautru[{index}][LOAI_KHAU_TRU]', ''),
                        'SO_TIEN_KT': request.POST.get(f'khautru[{index}][SO_TIEN_KT]', '0'),
                        'LY_DO_KHAU_TRU': request.POST.get(f'khautru[{index}][LY_DO_KHAU_TRU]', '')
                        
                    }
                    khau_tru_list.append(khau_tru)
                    index += 1
                # return JsonResponse({'khau_tru_list': khau_tru_list})

                # Gọi phương thức model để cập nhật hóa đơn
                hoa_don, errors = HoaDon.validate_and_update(hoa_don, data, chi_so_dich_vu_list, khau_tru_list)

                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return render(request, 'admin/hoadon/themsua_hoadon.html', {
                        'phong_tro': PhongTro.objects.all(),
                        'chi_so_dich_vu': chi_so_dich_vu_list,
                        'khau_tru': khau_tru_list,
                        'form_data': data,
                        'hoa_don': hoa_don
                    })

                messages.success(request, 'Cập nhật hóa đơn thành công!')
                return redirect('hoadon:hoadon_list')

        except Exception as e:
            messages.error(request, f'Lỗi khi sửa hóa đơn: {str(e)}')
            return render(request, 'admin/hoadon/themsua_hoadon.html', {
                'phong_tro': PhongTro.objects.all(),
                'chi_so_dich_vu': chi_so_dich_vu_list,
                
                'form_data': data,
                'hoa_don': hoa_don
            })
    # Hiển thị form chỉnh sửa
    current_month = None
    if hoa_don.NGAY_LAP_HDON:
        current_month = datetime.combine(hoa_don.NGAY_LAP_HDON, datetime.min.time()).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    chi_so_dich_vu_list, dich_vu_errors = get_dich_vu_ap_dung(phong.MA_KHU_VUC, hoa_don.MA_PHONG.MA_PHONG, current_month)
    khau_tru_list = KhauTru.objects.filter(MA_HOA_DON=hoa_don)
    
    form_data = {
        'MA_PHONG': hoa_don.MA_PHONG.MA_PHONG,
        'LOAI_HOA_DON': hoa_don.LOAI_HOA_DON,
        'NGAY_LAP_HDON': hoa_don.NGAY_LAP_HDON.strftime('%Y-%m-%d') if hoa_don.NGAY_LAP_HDON else '',
        'TRANG_THAI_HDON': hoa_don.TRANG_THAI_HDON,
        'TIEN_PHONG': str(hoa_don.TIEN_PHONG),
        'TIEN_DICH_VU': str(hoa_don.TIEN_DICH_VU),
        'TIEN_COC': str(hoa_don.TIEN_COC),
        'TIEN_KHAU_TRU': str(hoa_don.TIEN_KHAU_TRU),
        'TONG_TIEN': str(hoa_don.TONG_TIEN)
    }
    context = {
        'hoa_don': hoa_don,
        'phong_tro': get_phongtro_list(),
        'chi_so_dich_vu': chi_so_dich_vu_list,
        'khau_tru': khau_tru_list,
        'form_data': form_data,
        'trang_thai_choices': ['Đã thu tiền', 'Chưa thu tiền', 'Đang nợ', 'Đã hủy'],
        'loai_hoa_don_choices': ['Hóa đơn phòng', 'Hóa đơn điện', 'Hóa đơn nước', 'Hóa đơn khác']
    }
    return render(request, 'admin/hoadon/themsua_hoadon.html', context)

@csrf_exempt
def lay_thong_tin_phong(request, ma_phong):
    try:
        # Lấy số tiền cọc
        tien_coc, errors = PhongTro.get_tien_coc(ma_phong)
        if errors:
            return JsonResponse({'success': False, 'error': errors[0]}, status=404 if 'không tồn tại' in errors[0] else 500)

        # Lấy phòng để truy xuất khu vực
        phong = PhongTro.objects.get(MA_PHONG=ma_phong)

        # Lấy hợp đồng còn hiệu lực
        hop_dong, hop_dong_errors = HopDong.get_hop_dong_hieu_luc(ma_phong)
        if hop_dong_errors:
            return JsonResponse({'success': False, 'error': hop_dong_errors[0]}, status=500)

        # Lấy danh sách dịch vụ áp dụng
        dich_vu_list, dich_vu_errors = get_dich_vu_ap_dung(phong.MA_KHU_VUC, ma_phong)
        if dich_vu_errors:
            return JsonResponse({'success': False, 'error': dich_vu_errors[0]}, status=500)

        response_data = {
            'success': True,
            'phong_tro': {
                'SO_TIEN_CAN_COC': 0
            },
            'hop_dong': hop_dong,
            'dich_vu': dich_vu_list
        }
        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Lỗi không xác định: {str(e)}'}, status=500)
def xoa_hoa_don(request, ma_hoa_don):
    if request.method == 'POST':
        success, errors = HoaDon.xoa_hoa_don(ma_hoa_don)
        if success:
            messages.success(request, 'Xóa hóa đơn thành công!')
        else:
            for error in errors:
                messages.error(request, error)
        return redirect('hoadon:hoadon_list')

    messages.error(request, 'Phương thức không hợp lệ.')
    return redirect('hoadon:hoadon_list')