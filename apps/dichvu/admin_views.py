from django.shortcuts import render, redirect
from django.contrib import messages
from apps.dichvu.models import DichVu, ChiSoDichVu, LichSuApDungDichVu
from apps.nhatro.models import KhuVuc
from apps.phongtro.models import PhongTro
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openpyxl import Workbook
from django.http import HttpResponse
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from io import BytesIO
from collections import defaultdict
from django.core.paginator import Paginator
from django.db import transaction
from datetime import date
from django.http import JsonResponse

def ghi_so_dich_vu(request):
    """Hiển thị form ghi số dịch vụ sử dụng."""
    if request.method == 'GET':
        khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')
        context = {
            'khu_vucs': khu_vucs,
        }
        return render(request, 'admin/dichvu/ghi_so_dichvu.html', context)
    
    if request.method == 'POST':
        return luu_chi_so_dich_vu(request)

def lay_phong_theo_khu_vuc(request):
    """AJAX - Lấy danh sách phòng theo khu vực - Hybrid approach: qua hợp đồng nhưng group theo phòng."""
    khu_vuc_id = request.GET.get('khu_vuc_id')
    if not khu_vuc_id:
        return JsonResponse({'error': 'Thiếu mã khu vực'}, status=400)
    
    try:
        from apps.hopdong.models import HopDong
        
        # HYBRID APPROACH: Lấy phòng từ hợp đồng có hiệu lực và group theo MA_PHONG
        hop_dong_qs = HopDong.objects.filter(
            MA_PHONG__MA_KHU_VUC_id=khu_vuc_id,
            TRANG_THAI_HD='Đang hoạt động'
        ).select_related('MA_PHONG')
        
        # Group theo MA_PHONG để tránh trùng lặp
        phong_dict = {}
        for hop_dong in hop_dong_qs.values('MA_PHONG_id', 'MA_PHONG__TEN_PHONG'):
            ma_phong = hop_dong['MA_PHONG_id']
            if ma_phong not in phong_dict:
                phong_dict[ma_phong] = {
                    'MA_PHONG': ma_phong,
                    'TEN_PHONG': hop_dong['MA_PHONG__TEN_PHONG']
                }
        
        phong_list = list(phong_dict.values())
        return JsonResponse({'phong_tros': phong_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def lay_dich_vu_theo_khu_vuc(request):
    """AJAX - Lấy danh sách dịch vụ đang áp dụng theo khu vực."""
    khu_vuc_id = request.GET.get('khu_vuc_id')
    if not khu_vuc_id:
        return JsonResponse({'error': 'Thiếu mã khu vực'}, status=400)
    
    try:
        dich_vus = LichSuApDungDichVu.objects.filter(
            MA_KHU_VUC_id=khu_vuc_id,
            NGAY_HUY_DV__isnull=True
        ).select_related('MA_DICH_VU').values(
            'MA_DICH_VU__MA_DICH_VU',
            'MA_DICH_VU__TEN_DICH_VU',
            'MA_DICH_VU__DON_VI_TINH',
            'MA_DICH_VU__LOAI_DICH_VU',
            'GIA_DICH_VU_AD'
        )
        
        dich_vu_list = list(dich_vus)
        return JsonResponse({'dich_vus': dich_vu_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def lay_chi_so_cu(request):
    """AJAX - Lấy chỉ số cũ của dịch vụ - Hybrid approach: sử dụng hợp đồng để lấy chỉ số."""
    ma_phong = request.GET.get('ma_phong')
    ma_dich_vu = request.GET.get('ma_dich_vu')
    
    if not ma_phong or not ma_dich_vu:
        return JsonResponse({'error': 'Thiếu thông tin phòng hoặc dịch vụ'}, status=400)
    
    try:
        # HYBRID APPROACH: Lấy hợp đồng hiệu lực của phòng
        from apps.hopdong.models import HopDong
        from apps.phongtro.models import PhongTro
        
        phong = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
        hop_dong = HopDong.objects.filter(
            MA_PHONG=phong,
            TRANG_THAI_HD='Đang hoạt động'
        ).first()
        
        if not hop_dong:
            return JsonResponse({'chi_so_cu': 0})
        
        # Sử dụng MA_HOP_DONG để lấy chỉ số mới nhất của dịch vụ
        chi_so_moi_nhat = ChiSoDichVu.objects.filter(
            MA_HOP_DONG=hop_dong,
            MA_DICH_VU_id=ma_dich_vu
        ).order_by('-NGAY_GHI_CS').first()
        
        chi_so_cu = 0
        if chi_so_moi_nhat and chi_so_moi_nhat.CHI_SO_MOI is not None:
            chi_so_cu = chi_so_moi_nhat.CHI_SO_MOI
            
        return JsonResponse({'chi_so_cu': chi_so_cu})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def kiem_tra_chi_so_da_ghi(request):
    """AJAX - Kiểm tra chỉ số đã ghi trong kỳ thanh toán hiện tại - Hybrid approach: sử dụng hợp đồng"""
    ma_phong = request.GET.get('ma_phong')
    
    if not ma_phong:
        return JsonResponse({'error': 'Thiếu thông tin phòng'}, status=400)
    
    try:
        from apps.hopdong.models import HopDong
        from apps.phongtro.models import PhongTro
        
        phong = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
        
        # HYBRID APPROACH: Lấy hợp đồng hiệu lực của phòng
        hop_dong = HopDong.objects.filter(
            MA_PHONG=phong,
            TRANG_THAI_HD='Đang hoạt động'
        ).first()
        
        if not hop_dong:
            return JsonResponse({'error': 'Không tìm thấy hợp đồng hiệu lực'}, status=404)
        
        # Sử dụng MA_HOP_DONG để lấy chỉ số có thể chỉnh sửa trong kỳ hiện tại
        readings_by_service, start_period, end_period = ChiSoDichVu.get_editable_readings(hop_dong)
        
        
        # Chuẩn bị dữ liệu trả về
        editable_readings = {}
        for service_id, reading in readings_by_service.items():
            editable_readings[str(service_id)] = {
                'MA_CHI_SO': reading.MA_CHI_SO,
                'CHI_SO_CU': reading.CHI_SO_CU,
                'CHI_SO_MOI': reading.CHI_SO_MOI,
                'SO_LUONG': reading.SO_LUONG,
                'NGAY_GHI_CS': reading.NGAY_GHI_CS.strftime('%Y-%m-%d') if reading.NGAY_GHI_CS else None,
                'TEN_DICH_VU': reading.MA_DICH_VU.TEN_DICH_VU,
                'LOAI_DICH_VU': reading.MA_DICH_VU.LOAI_DICH_VU
            }
        
        return JsonResponse({
            'has_readings': len(editable_readings) > 0,
            'readings': editable_readings,
            'billing_period': {
                'start': start_period.strftime('%Y-%m-%d'),
                'end': end_period.strftime('%Y-%m-%d'),
                'chu_ky': hop_dong.CHU_KY_THANH_TOAN,
                'ngay_thu_tien': hop_dong.NGAY_THU_TIEN
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def luu_chi_so_dich_vu(request):
    """Lưu chỉ số dịch vụ sử dụng - Hybrid approach: sử dụng hợp đồng để lưu chỉ số."""
    try:
        from datetime import datetime
        
        ma_phong = request.POST.get('ma_phong')
        ngay_ghi_cs_str = request.POST.get('ngay_ghi_cs')
        chi_so_data = []
        
        # Parse ngày ghi chỉ số
        if ngay_ghi_cs_str:
            try:
                ngay_ghi_cs = datetime.strptime(ngay_ghi_cs_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Định dạng ngày ghi chỉ số không hợp lệ.')
                return redirect('dichvu:ghi_so_dich_vu')
        else:
            messages.error(request, 'Vui lòng chọn ngày ghi chỉ số.')
            return redirect('dichvu:ghi_so_dich_vu')
        
        # HYBRID APPROACH: Lấy thông tin phòng và hợp đồng hiệu lực
        phong = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
        from apps.hopdong.models import HopDong
        hop_dong = HopDong.objects.filter(
            MA_PHONG=phong,
            TRANG_THAI_HD='Đang hoạt động'
        ).first()
        
        if not hop_dong:
            messages.error(request, 'Không tìm thấy hợp đồng hiệu lực cho phòng này.')
            return redirect('dichvu:ghi_so_dich_vu')
        
        # Lấy dữ liệu chỉ số từ form - chỉ số theo thực tế
        for key, value in request.POST.items():
            if key.startswith('chi_so_moi_'):
                ma_dich_vu = key.split('_')[-1]
                chi_so_cu = request.POST.get(f'chi_so_cu_{ma_dich_vu}', 0)
                chi_so_moi = value
                
                if chi_so_moi:
                    chi_so_data.append({
                        'MA_DICH_VU': ma_dich_vu,
                        'CHI_SO_CU': chi_so_cu,
                        'CHI_SO_MOI': chi_so_moi,
                        'LOAI': 'chi_so'
                    })
            elif key.startswith('so_luong_'):
                ma_dich_vu = key.split('_')[-1]
                so_luong = value
                
                if so_luong and int(so_luong) > 0:
                    chi_so_data.append({
                        'MA_DICH_VU': ma_dich_vu,
                        'SO_LUONG': so_luong,
                        'LOAI': 'co_dinh'
                    })
        
        # Tự động thêm tất cả dịch vụ cố định của khu vực với số lượng mặc định
        from .models import LichSuApDungDichVu
        dich_vu_co_dinh = LichSuApDungDichVu.objects.filter(
            MA_KHU_VUC=phong.MA_KHU_VUC,
            MA_DICH_VU__LOAI_DICH_VU__in=['Cố định', 'Co dinh'],  # Xử lý cả 2 trường hợp
            NGAY_HUY_DV__isnull=True
        )
        
        # Lấy danh sách dịch vụ đã được nhập (cả chỉ số và cố định)
        ma_dv_da_nhap = [item['MA_DICH_VU'] for item in chi_so_data]
        
        # Chỉ thêm dịch vụ cố định chưa được nhập
        for dv_co_dinh in dich_vu_co_dinh:
            ma_dv_str = str(dv_co_dinh.MA_DICH_VU.MA_DICH_VU)
            if ma_dv_str not in ma_dv_da_nhap:
                chi_so_data.append({
                    'MA_DICH_VU': ma_dv_str,
                    'SO_LUONG': '1',  # Mặc định số lượng = 1
                    'LOAI': 'co_dinh'
                })
        
        # Validation
        if not chi_so_data:
            messages.error(request, 'Không có dịch vụ nào để ghi chỉ số.')
            return redirect('dichvu:ghi_so_dich_vu')
        
        # Debug: In ra dữ liệu sẽ được lưu
        print(f"DEBUG: Ngày ghi chỉ số: {ngay_ghi_cs} (type: {type(ngay_ghi_cs)})")
        print(f"DEBUG: Sẽ lưu {len(chi_so_data)} bản ghi chỉ số dịch vụ:")
        for item in chi_so_data:
            dich_vu_temp = DichVu.objects.get(MA_DICH_VU=item['MA_DICH_VU'])
            print(f"  - {dich_vu_temp.TEN_DICH_VU} ({dich_vu_temp.LOAI_DICH_VU}) - Loại: {item['LOAI']}")

        # Lưu chỉ số dịch vụ
        saved_count = 0
        with transaction.atomic():
            for chi_so in chi_so_data:
                dich_vu = get_object_or_404(DichVu, MA_DICH_VU=chi_so['MA_DICH_VU'])
                
                # Kiểm tra trùng lặp - chỉ lưu nếu chưa có bản ghi trong ngày
                existing = ChiSoDichVu.objects.filter(
                    MA_DICH_VU=dich_vu,
                    MA_HOP_DONG=hop_dong,
                    NGAY_GHI_CS=ngay_ghi_cs
                ).exists()
                
                if existing:
                    print(f"DEBUG: Bỏ qua {dich_vu.TEN_DICH_VU} - đã có bản ghi trong ngày")
                    continue
                
                if chi_so['LOAI'] == 'chi_so':
                    # Dịch vụ theo chỉ số (điện, nước)
                    chi_so_cu = float(chi_so['CHI_SO_CU'] or 0)
                    chi_so_moi = float(chi_so['CHI_SO_MOI'])
                    
                    if chi_so_moi < chi_so_cu:
                        messages.error(request, f'Chỉ số mới của {dich_vu.TEN_DICH_VU} phải lớn hơn hoặc bằng chỉ số cũ.')
                        return redirect('dichvu:ghi_so_dich_vu')
                    
                    # Tạo bản ghi chỉ số
                    new_reading = ChiSoDichVu.objects.create(
                        MA_DICH_VU=dich_vu,
                        MA_HOP_DONG=hop_dong,
                        CHI_SO_CU=int(chi_so_cu),
                        CHI_SO_MOI=int(chi_so_moi),
                        NGAY_GHI_CS=ngay_ghi_cs,
                        SO_LUONG=int(chi_so_moi - chi_so_cu)
                    )
                    saved_count += 1
                    print(f"DEBUG: Lưu dịch vụ theo chỉ số - {dich_vu.TEN_DICH_VU}, Ngày: {ngay_ghi_cs}, MA_CHI_SO: {new_reading.MA_CHI_SO}")
                else:
                    # Dịch vụ cố định (wifi, rác, bảo vệ...)
                    so_luong = int(chi_so['SO_LUONG'] or 1)
                    new_reading = ChiSoDichVu.objects.create(
                        MA_DICH_VU=dich_vu,
                        MA_HOP_DONG=hop_dong,
                        CHI_SO_CU=0,
                        CHI_SO_MOI=0,
                        NGAY_GHI_CS=ngay_ghi_cs,
                        SO_LUONG=so_luong
                    )
                    saved_count += 1
                    print(f"DEBUG: Lưu dịch vụ cố định - {dich_vu.TEN_DICH_VU}, Ngày: {ngay_ghi_cs}, MA_CHI_SO: {new_reading.MA_CHI_SO}")
        
        print(f"DEBUG: Đã lưu thành công {saved_count}/{len(chi_so_data)} bản ghi")
        
        messages.success(request, 'Ghi số dịch vụ sử dụng thành công!')
        
        # Redirect với thông tin phòng để reload lại
        return redirect(f"{request.path}?room={ma_phong}&area={phong.MA_KHU_VUC_id}")
        
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        return redirect('dichvu:ghi_so_dich_vu')

def cap_nhat_chi_so_dich_vu(request):
   
    
    """API - Cập nhật chỉ số dịch vụ đã ghi"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Chỉ hỗ trợ POST method'}, status=405)
    
    try:
        from datetime import datetime
        import json
        
        print(f"DEBUG UPDATE: Request method: {request.method}")
        print(f"DEBUG UPDATE: Request body: {request.body}")
        
        data = json.loads(request.body)
        ma_chi_so = data.get('ma_chi_so')
        chi_so_moi = data.get('chi_so_moi')
        so_luong = data.get('so_luong')
        ngay_ghi_cs_str = data.get('ngay_ghi_cs')
        
        print(f"DEBUG UPDATE: Parsed data - ma_chi_so: {ma_chi_so}, chi_so_moi: {chi_so_moi}, so_luong: {so_luong}")
        
        # return JsonResponse({
        #     'success': True,
        #     'message': chi_so_moi,        
        # })

        if not ma_chi_so:
            return JsonResponse({'error': 'Thiếu mã chỉ số'}, status=400)
        
        # Parse ngày
        if ngay_ghi_cs_str:
            try:
                ngay_ghi_cs = datetime.strptime(ngay_ghi_cs_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Định dạng ngày không hợp lệ'}, status=400)
        else:
            ngay_ghi_cs = None
        
        # Lấy bản ghi chỉ số
        chi_so_obj = get_object_or_404(ChiSoDichVu, MA_CHI_SO=ma_chi_so)
        
        # Kiểm tra xem có được phép chỉnh sửa không (trong kỳ thanh toán hiện tại)
        hop_dong = chi_so_obj.MA_HOP_DONG
        start_period, end_period = ChiSoDichVu.get_current_billing_period(hop_dong)
        
        if not (start_period <= chi_so_obj.NGAY_GHI_CS < end_period):
            return JsonResponse({'error': 'Chỉ có thể chỉnh sửa chỉ số trong kỳ thanh toán hiện tại'}, status=403)
        
        # Cập nhật thông tin
        with transaction.atomic():
            if chi_so_obj.MA_DICH_VU.LOAI_DICH_VU not in ['Cố định', 'Co dinh']:
                # Dịch vụ theo chỉ số
                if chi_so_moi is not None:
                    chi_so_cu = chi_so_obj.CHI_SO_CU or 0
                    if float(chi_so_moi) < chi_so_cu:
                        return JsonResponse({'error': 'Chỉ số mới phải lớn hơn hoặc bằng chỉ số cũ'}, status=400)
                    
                    chi_so_obj.CHI_SO_MOI = int(float(chi_so_moi))
                    chi_so_obj.SO_LUONG = int(float(chi_so_moi)) - chi_so_cu
            else:
                # Dịch vụ cố định
                if so_luong is not None:
                    chi_so_obj.SO_LUONG = int(float(so_luong))
            
            if ngay_ghi_cs:
                chi_so_obj.NGAY_GHI_CS = ngay_ghi_cs
                
            chi_so_obj.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã cập nhật chỉ số thành công',
            'data': {
                'MA_CHI_SO': chi_so_obj.MA_CHI_SO,
                'CHI_SO_CU': chi_so_obj.CHI_SO_CU,
                'CHI_SO_MOI': chi_so_obj.CHI_SO_MOI,
                'SO_LUONG': chi_so_obj.SO_LUONG,
                'NGAY_GHI_CS': chi_so_obj.NGAY_GHI_CS.strftime('%Y-%m-%d') if chi_so_obj.NGAY_GHI_CS else None
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def xoa_chi_so_dich_vu(request):
    """API - Xóa chỉ số dịch vụ đã ghi"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Chỉ hỗ trợ DELETE method'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        ma_chi_so = data.get('ma_chi_so')
        
        if not ma_chi_so:
            return JsonResponse({'error': 'Thiếu mã chỉ số'}, status=400)
        
        # Lấy bản ghi chỉ số
        chi_so_obj = get_object_or_404(ChiSoDichVu, MA_CHI_SO=ma_chi_so)
        
        # Kiểm tra xem có được phép xóa không (trong kỳ thanh toán hiện tại)
        hop_dong = chi_so_obj.MA_HOP_DONG
        start_period, end_period = ChiSoDichVu.get_current_billing_period(hop_dong)
        
        if not (start_period <= chi_so_obj.NGAY_GHI_CS < end_period):
            return JsonResponse({'error': 'Chỉ có thể xóa chỉ số trong kỳ thanh toán hiện tại'}, status=403)
        
        # Lưu thông tin để trả về
        ten_dich_vu = chi_so_obj.MA_DICH_VU.TEN_DICH_VU
        
        # Xóa bản ghi
        chi_so_obj.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Đã xóa chỉ số dịch vụ {ten_dich_vu} thành công'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def dichvu_list(request):
    # Lấy toàn bộ danh sách dịch vụ (không phân trang)
    dich_vus = DichVu.objects.order_by('MA_DICH_VU')

    # Lấy toàn bộ danh sách khu vực (không phân trang)
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')

    # HYBRID APPROACH: Lấy danh sách phòng từ hợp đồng nhưng group theo MA_PHONG
    from apps.hopdong.models import HopDong
    
    # Lấy phòng từ hợp đồng có chỉ số dịch vụ
    hop_dong_with_services = HopDong.objects.filter(
        chisodichvu__isnull=False
    ).select_related('MA_PHONG').distinct()
    
    # Group theo MA_PHONG để tránh trùng lặp
    phong_dict = {}
    for hop_dong in hop_dong_with_services.values('MA_PHONG_id', 'MA_PHONG__TEN_PHONG'):
        ma_phong = hop_dong['MA_PHONG_id']
        if ma_phong not in phong_dict:
            phong_dict[ma_phong] = {
                'MA_PHONG': ma_phong,
                'TEN_PHONG': hop_dong['MA_PHONG__TEN_PHONG']
            }
    
    phong_tros = list(phong_dict.values())

    # HYBRID APPROACH: Lấy dữ liệu chỉ số dịch vụ qua hợp đồng nhưng group theo MA_PHONG
    chi_so_dich_vus_qs = ChiSoDichVu.objects.select_related('MA_DICH_VU', 'MA_HOP_DONG', 'MA_HOP_DONG__MA_PHONG')
    
    chi_so_dich_vus = []
    for chi_so in chi_so_dich_vus_qs:
        chi_so_dich_vus.append({
            'MA_CHI_SO': chi_so.MA_CHI_SO,
            'MA_HOP_DONG_id': chi_so.MA_HOP_DONG_id,
            'MA_HOP_DONG__MA_PHONG_id': chi_so.MA_HOP_DONG.MA_PHONG.MA_PHONG if chi_so.MA_HOP_DONG and chi_so.MA_HOP_DONG.MA_PHONG else None,
            'MA_DICH_VU_id': chi_so.MA_DICH_VU_id,
            'CHI_SO_CU': chi_so.CHI_SO_CU,
            'CHI_SO_MOI': chi_so.CHI_SO_MOI,
            'SO_LUONG': chi_so.SO_LUONG,
            'NGAY_GHI_CS': chi_so.NGAY_GHI_CS,
            'MA_DICH_VU__DON_VI_TINH': chi_so.MA_DICH_VU.DON_VI_TINH if chi_so.MA_DICH_VU else None,
            'MA_DICH_VU__GIA_DICH_VU': chi_so.MA_DICH_VU.GIA_DICH_VU if chi_so.MA_DICH_VU else None,
            'MA_DICH_VU__LOAI_DICH_VU': chi_so.MA_DICH_VU.LOAI_DICH_VU if chi_so.MA_DICH_VU else None,
        })
    
    # Nhóm theo MA_PHONG (extracted từ hợp đồng)
    chi_so_grouped = {}
    for chi_so in chi_so_dich_vus:
        ma_phong_from_contract = chi_so['MA_HOP_DONG__MA_PHONG_id']
        if ma_phong_from_contract not in chi_so_grouped:
            chi_so_grouped[ma_phong_from_contract] = []
        chi_so_grouped[ma_phong_from_contract].append(chi_so)

    # Xử lý thông báo
    success_message = request.session.pop('success', None)
    error_message = request.session.pop('error', None)
    if success_message:
        messages.success(request, success_message)
    if error_message:
        messages.error(request, error_message)

    context = {
        'dich_vus': dich_vus,
        'khu_vucs': khu_vucs,
        'phong_tros': phong_tros,
        'chi_so_dich_vus': chi_so_grouped,
    }
    return render(request, 'admin/dichvu/dansach_dichvu.html', context)

def _prepare_thong_ke_data(request):
    """Hàm chung để chuẩn bị dữ liệu thống kê dịch vụ - Hybrid approach: sử dụng MA_HOP_DONG internally nhưng group theo MA_PHONG."""
    khu_vuc_id = request.GET.get('khuVuc')
    thang = request.GET.get('thang')
    phong_tro_id = request.GET.get('phongTro')
    loai_dich_vu = request.GET.get('loaiDichVu')

    # Xử lý ngày tháng
    start_of_month = None
    end_of_month = None
    if thang == 'all':
        # Nếu chọn tất cả khoảng thời gian, không giới hạn NGAY_GHI_CS
        pass
    else:
        try:
            start_of_month = datetime.strptime(thang, '%Y-%m').replace(day=1)
            end_of_month = start_of_month + relativedelta(months=1) - relativedelta(days=1)
        except (ValueError, TypeError):
            start_of_month = datetime.now().replace(day=1)
            end_of_month = start_of_month + relativedelta(months=1) - relativedelta(days=1)

    # HYBRID APPROACH: Truy vấn hợp đồng thay vì phòng trực tiếp
    from apps.hopdong.models import HopDong
    hop_dong_qs = HopDong.objects.select_related('MA_PHONG', 'MA_PHONG__MA_KHU_VUC').distinct()
    
    # Lọc theo thời gian thông qua chỉ số dịch vụ của hợp đồng
    if start_of_month and end_of_month:
        hop_dong_qs = hop_dong_qs.filter(
            chisodichvu__NGAY_GHI_CS__range=[start_of_month, end_of_month]
        ).distinct()
    
    # Áp dụng bộ lọc khu vực thông qua phòng
    if khu_vuc_id and khu_vuc_id != 'all':
        hop_dong_qs = hop_dong_qs.filter(MA_PHONG__MA_KHU_VUC_id=khu_vuc_id)
    
    # Áp dụng bộ lọc phòng trọ
    if phong_tro_id and phong_tro_id != 'all':
        hop_dong_qs = hop_dong_qs.filter(MA_PHONG_id=phong_tro_id)

    # Lấy danh sách phòng từ các hợp đồng và group theo MA_PHONG
    phong_dict = {}
    for hop_dong in hop_dong_qs.values('MA_PHONG_id', 'MA_PHONG__TEN_PHONG'):
        ma_phong = hop_dong['MA_PHONG_id']
        if ma_phong not in phong_dict:
            phong_dict[ma_phong] = {
                'MA_PHONG': ma_phong,
                'TEN_PHONG': hop_dong['MA_PHONG__TEN_PHONG']
            }
    
    phong_tros = list(phong_dict.values())
    
    # Truy vấn dịch vụ
    dich_vus_qs = DichVu.objects.order_by('MA_DICH_VU')
    
    # Áp dụng bộ lọc loại dịch vụ
    if loai_dich_vu and loai_dich_vu != 'all':
        dich_vus_qs = dich_vus_qs.filter(LOAI_DICH_VU=loai_dich_vu)
    
    dich_vus = dich_vus_qs.values('MA_DICH_VU', 'TEN_DICH_VU', 'DON_VI_TINH', 'GIA_DICH_VU', 'LOAI_DICH_VU')

    # HYBRID APPROACH: Truy vấn chỉ số dịch vụ qua MA_HOP_DONG
    chi_so_dich_vus_qs = ChiSoDichVu.objects.select_related('MA_DICH_VU', 'MA_HOP_DONG', 'MA_HOP_DONG__MA_PHONG')
    
    if start_of_month and end_of_month:
        chi_so_dich_vus_qs = chi_so_dich_vus_qs.filter(
            NGAY_GHI_CS__range=[start_of_month, end_of_month]
        )
    
    # Áp dụng bộ lọc khu vực thông qua hợp đồng -> phòng
    if khu_vuc_id and khu_vuc_id != 'all':
        chi_so_dich_vus_qs = chi_so_dich_vus_qs.filter(MA_HOP_DONG__MA_PHONG__MA_KHU_VUC_id=khu_vuc_id)
    
    # Áp dụng bộ lọc phòng trọ
    if phong_tro_id and phong_tro_id != 'all':
        chi_so_dich_vus_qs = chi_so_dich_vus_qs.filter(MA_HOP_DONG__MA_PHONG_id=phong_tro_id)
    
    # Áp dụng bộ lọc loại dịch vụ cho chỉ số dịch vụ
    if loai_dich_vu and loai_dich_vu != 'all':
        chi_so_dich_vus_qs = chi_so_dich_vus_qs.filter(MA_DICH_VU__LOAI_DICH_VU=loai_dich_vu)

    # Lấy dữ liệu chỉ số với thông tin hợp đồng và group theo MA_PHONG từ hợp đồng
    chi_so_dich_vus = []
    for chi_so in chi_so_dich_vus_qs.select_related('MA_HOP_DONG__MA_PHONG', 'MA_DICH_VU'):
        chi_so_dich_vus.append({
            'MA_HOP_DONG_id': chi_so.MA_HOP_DONG_id,
            'MA_HOP_DONG__MA_PHONG_id': chi_so.MA_HOP_DONG.MA_PHONG.MA_PHONG if chi_so.MA_HOP_DONG and chi_so.MA_HOP_DONG.MA_PHONG else None,
            'MA_DICH_VU_id': chi_so.MA_DICH_VU_id,
            'CHI_SO_CU': chi_so.CHI_SO_CU,
            'CHI_SO_MOI': chi_so.CHI_SO_MOI,
            'SO_LUONG': chi_so.SO_LUONG,
            'MA_DICH_VU__DON_VI_TINH': chi_so.MA_DICH_VU.DON_VI_TINH if chi_so.MA_DICH_VU else None,
            'MA_DICH_VU__GIA_DICH_VU': chi_so.MA_DICH_VU.GIA_DICH_VU if chi_so.MA_DICH_VU else None,
            'MA_DICH_VU__LOAI_DICH_VU': chi_so.MA_DICH_VU.LOAI_DICH_VU if chi_so.MA_DICH_VU else None,
        })

    # Nhóm chỉ số theo phòng trọ (extracted từ hợp đồng)
    chi_so_by_phong = defaultdict(list)
    for chi_so in chi_so_dich_vus:
        # Group theo MA_PHONG được lấy từ hợp đồng
        ma_phong_from_contract = chi_so['MA_HOP_DONG__MA_PHONG_id']
        chi_so_by_phong[ma_phong_from_contract].append(chi_so)

    # Tính toán tổng và chuẩn bị dữ liệu
    total_values = {dv['TEN_DICH_VU']: 0 for dv in dich_vus}
    # Phân biệt dịch vụ cố định và dịch vụ theo chỉ số cho tổng kết
    total_chiso = {dv['TEN_DICH_VU']: 0 for dv in dich_vus 
                   if not (dv['DON_VI_TINH'] == 'Tháng' or dv['LOAI_DICH_VU'] in ['Cố định', 'Co dinh', 'thang'])}
    total_so_lan_su_dung = {dv['TEN_DICH_VU']: 0 for dv in dich_vus 
                            if dv['DON_VI_TINH'] == 'Tháng' or dv['LOAI_DICH_VU'] in ['Cố định', 'Co dinh', 'thang']}
    
    phong_data = []
    excel_data = []

    for phong in phong_tros:
        ma_phong = phong['MA_PHONG']
        chi_so_data = []
        excel_row = {'Tên phòng': phong['TEN_PHONG'] or f"Phòng {ma_phong}"}

        for dich_vu in dich_vus:
            chi_so = next(
                (cs for cs in chi_so_by_phong[ma_phong] if cs['MA_DICH_VU_id'] == dich_vu['MA_DICH_VU']),
                None
            )
            chi_so_cu = chi_so_moi = chiso_difference = service_total = so_luong_su_dung = 0

            # Kiểm tra nếu là dịch vụ cố định (theo tháng, cố định, hoặc các loại tương tự)
            is_fixed_service = (
                dich_vu['DON_VI_TINH'] == 'Tháng' or 
                (chi_so and chi_so.get('MA_DICH_VU__DON_VI_TINH') == 'Tháng') or
                (chi_so and chi_so.get('MA_DICH_VU__LOAI_DICH_VU') in ['Cố định', 'Co dinh', 'thang'])
            )
            
            if is_fixed_service:
                # Dịch vụ cố định: Sử dụng SO_LUONG từ ChiSoDichVu
                if chi_so:
                    # Lấy SO_LUONG từ bảng ChiSoDichVu thay vì mặc định = 1
                    so_luong_su_dung = chi_so.get('SO_LUONG', 0) or 0
                    service_total = so_luong_su_dung * (chi_so['MA_DICH_VU__GIA_DICH_VU'] or dich_vu['GIA_DICH_VU'] or 0)
                    total_so_lan_su_dung[dich_vu['TEN_DICH_VU']] += so_luong_su_dung
                else:
                    so_luong_su_dung = 0
                    service_total = 0
                
                excel_row[f'{dich_vu["TEN_DICH_VU"]}_Số_lượng_sử_dụng'] = so_luong_su_dung
                excel_row[f'{dich_vu["TEN_DICH_VU"]}_Thành_tiền'] = service_total
            else:
                # Dịch vụ theo chỉ số: Giữ nguyên logic cũ
                chi_so_cu = (chi_so['CHI_SO_CU'] if chi_so else 0) or 0
                chi_so_moi = (chi_so['CHI_SO_MOI'] if chi_so else 0) or 0
                chiso_difference = max(chi_so_moi - chi_so_cu, 0)

                service_total = chiso_difference * (chi_so['MA_DICH_VU__GIA_DICH_VU'] if chi_so else dich_vu['GIA_DICH_VU'] or 0)
                if chi_so:
                    total_chiso[dich_vu['TEN_DICH_VU']] += chiso_difference
                excel_row[f'{dich_vu["TEN_DICH_VU"]}_Số_cũ'] = chi_so_cu
                excel_row[f'{dich_vu["TEN_DICH_VU"]}_Số_mới'] = chi_so_moi
                excel_row[f'{dich_vu["TEN_DICH_VU"]}_Thành_tiền'] = service_total

            total_values[dich_vu['TEN_DICH_VU']] += service_total

            chi_so_data.append({
                'chi_so_cu': chi_so_cu,
                'chi_so_moi': chi_so_moi,
                'chiso_difference': chiso_difference,
                'service_total': service_total,
                'don_vi_tinh': dich_vu['DON_VI_TINH'],
                'so_luong_su_dung': so_luong_su_dung,  # Thêm thông tin số lượng sử dụng
                'is_fixed_service': is_fixed_service   # Thêm flag để phân biệt dịch vụ cố định
            })

        phong_data.append({'phong': phong, 'chi_so_data': chi_so_data})
        excel_data.append(excel_row)

    return {
        'phong_data': phong_data,
        'excel_data': excel_data,
        'dich_vus': dich_vus,
        'total_values': total_values,
        'total_chiso': total_chiso,
        'total_so_lan_su_dung': total_so_lan_su_dung,
        'start_of_month': start_of_month,
        'end_of_month': end_of_month
    }
def thong_ke_dich_vu(request):
    """Hiển thị bảng thống kê dịch vụ trên giao diện."""
    try:
        data = _prepare_thong_ke_data(request)
        # return JsonResponse(dict(request.GET))
        context = {
            'phong_tros': data['phong_data'],
            'dich_vus': data['dich_vus'],
            'total_values': data['total_values'],
            'total_chiso': data['total_chiso'],
            'total_so_lan_su_dung': data['total_so_lan_su_dung']
        }
        return render(request, 'admin/dichvu/bang_thongke.html', context)
    except Exception as e:
        import traceback
        print(f"Error in thong_ke_dich_vu: {e}")
        print(traceback.format_exc())
        from django.http import JsonResponse
        return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()}, status=500)


def export_thong_ke_dich_vu(request):
    """Xuất thống kê dịch vụ ra file Excel."""
    data = _prepare_thong_ke_data(request)
    dich_vus = data['dich_vus']
    excel_data = data['excel_data']

    # Tạo DataFrame
    df = pd.DataFrame(excel_data)

    # Tạo workbook và worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Thống kê dịch vụ"

    # Tạo tiêu đề
    headers = ['Tên phòng']
    for dich_vu in dich_vus:
        if dich_vu['DON_VI_TINH'] == 'Tháng':
            headers.extend([f'{dich_vu["TEN_DICH_VU"]}_Số_lượng_sử_dụng', f'{dich_vu["TEN_DICH_VU"]}_Thành_tiền'])
        else:
            headers.extend([f'{dich_vu["TEN_DICH_VU"]}_Số_cũ', f'{dich_vu["TEN_DICH_VU"]}_Số_mới', f'{dich_vu["TEN_DICH_VU"]}_Thành_tiền'])
    ws.append(headers)

    # Ghi dữ liệu
    for row in dataframe_to_rows(df, index=False, header=False):
        ws.append(row)

    # Xuất file Excel
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        content=output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=thongke_dichvu.xlsx'
    return response

def view_sua_dich_vu(request, ma_dich_vu):
    """Hiển thị form sửa dịch vụ."""
    # Tìm dịch vụ theo MA_DICH_VU
    try:
        dich_vu = DichVu.objects.get(MA_DICH_VU=ma_dich_vu)
    except DichVu.DoesNotExist:
        return render(request, 'admin/dichvu/them_sua_dich_vu.html', {'error': 'Dịch vụ không tồn tại'})

    # Lấy danh sách khu vực có MA_NHA_TRO = 1, phân trang
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')

    # Lấy danh sách khu vực áp dụng dịch vụ
    khu_vuc_ap_dung = KhuVuc.objects.filter(
        lichsu_dichvu__MA_DICH_VU=ma_dich_vu,
        lichsu_dichvu__NGAY_HUY_DV__isnull=True
    ).prefetch_related('lichsu_dichvu').values(
        'MA_KHU_VUC', 'TEN_KHU_VUC', 'lichsu_dichvu__MA_AP_DUNG_DV'
    )

    context = {
        'dich_vu': dich_vu,
        'khu_vucs': khu_vucs,
        'khu_vuc_ap_dung': list(khu_vuc_ap_dung)
    }
    return render(request, 'admin/dichvu/themsua_dichvu.html', context)

def view_them_moi_dich_vu(request):
    """Hiển thị form thêm mới dịch vụ."""
    # Lấy danh sách khu vực có MA_NHA_TRO = 1, phân trang
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')
    context = {
        'khu_vucs': khu_vucs
    }
    return render(request, 'admin/dichvu/themsua_dichvu.html', context)
def validate_dich_vu_data(data, rooms):
    """Validate input data for DichVu and return errors if any."""
    errors = {}
    ten_dich_vu = data.get('TENDICHVU')
    don_vi_tinh = data.get('DONVITINH')
    gia_dich_vu = data.get('GIADICHVU')

    if not ten_dich_vu or len(ten_dich_vu.strip()) > 200:
        errors['TENDICHVU'] = "Tên dịch vụ là bắt buộc và không được vượt quá 200 ký tự."
    if not don_vi_tinh or len(don_vi_tinh) > 50:
        errors['DONVITINH'] = "Đơn vị tính là bắt buộc và không được vượt quá 50 ký tự."
    if not gia_dich_vu:
        errors['GIADICHVU'] = "Giá dịch vụ là bắt buộc."
    else:
        try:
            gia_dich_vu = float(gia_dich_vu)
            if gia_dich_vu < 0:
                errors['GIADICHVU'] = "Giá dịch vụ phải lớn hơn hoặc bằng 0."
        except ValueError:
            errors['GIADICHVU'] = "Giá dịch vụ phải là một số hợp lệ."
    if rooms:
        invalid_rooms = [room for room in rooms if not KhuVuc.objects.filter(MA_KHU_VUC=room).exists()]
        if invalid_rooms:
            errors['rooms'] = f"Các khu vực sau không tồn tại: {', '.join(invalid_rooms)}."
    else:
        errors['rooms'] = "Vui lòng chọn ít nhất một khu vực áp dụng."

    return errors, gia_dich_vu if not errors.get('GIADICHVU') else None

def them_dich_vu(request):
    if request.method == 'POST':
        dong_ho_dien_nuoc = request.POST.get('dong_ho_dien_nuoc', '0') == '1'
        rooms = request.POST.getlist('rooms[]')
        errors, gia_dich_vu = validate_dich_vu_data(request.POST, rooms)

        if errors:
            messages.error(request, "Vui lòng kiểm tra các lỗi sau.")
            return redirect('dichvu:dichvu_list')

        with transaction.atomic():
            dich_vu = DichVu.objects.create(
                TEN_DICH_VU=request.POST['TENDICHVU'].strip(),
                DON_VI_TINH=request.POST['DONVITINH'],
                GIA_DICH_VU=gia_dich_vu,
                LOAI_DICH_VU='chi_so' if dong_ho_dien_nuoc else 'thang'
            )

            lich_su_records = [
                LichSuApDungDichVu(
                    MA_KHU_VUC_id=ma_khu_vuc,
                    MA_DICH_VU=dich_vu,
                    NGAY_AP_DUNG_DV=date.today(),
                    GIA_DICH_VU_AD=gia_dich_vu,
                    LOAI_DICH_VU_AD='chi_so' if dong_ho_dien_nuoc else 'thang'
                ) for ma_khu_vuc in rooms
            ]
            LichSuApDungDichVu.objects.bulk_create(lich_su_records)

        messages.success(request, 'Dịch vụ mới đã được thêm thành công.')
        return redirect('dichvu:dichvu_list')

    return redirect('dichvu:dichvu_list')

def sua_dich_vu(request, ma_dich_vu):
    dich_vu = get_object_or_404(DichVu, MA_DICH_VU=ma_dich_vu)

    if request.method == 'GET':
        return redirect('dichvu:dichvu_list')

    # Handle POST or PUT
    if request.method == 'POST' or request.POST.get('_method') == 'PUT':
        dong_ho_dien_nuoc = request.POST.get('dong_ho_dien_nuoc', '0') == '1'
        rooms = request.POST.getlist('rooms[]')
        errors, gia_dich_vu = validate_dich_vu_data(request.POST, rooms)

        if errors:
            messages.error(request, "Vui lòng kiểm tra các lỗi sau.")
            return redirect('dichvu:dichvu_list')

        with transaction.atomic():
            # Update DichVu
            dich_vu.TEN_DICH_VU = request.POST['TENDICHVU'].strip()
            dich_vu.DON_VI_TINH = request.POST['DONVITINH']
            dich_vu.GIA_DICH_VU = gia_dich_vu
            dich_vu.LOAI_DICH_VU = 'chi_so' if dong_ho_dien_nuoc else 'thang'
            dich_vu.save()

            # Get current active service applications
            current_ap_dungs = LichSuApDungDichVu.objects.filter(
                MA_DICH_VU=dich_vu,
                NGAY_HUY_DV__isnull=True
            )
            current_khu_vuc_ids = set(ap_dung.MA_KHU_VUC_id for ap_dung in current_ap_dungs)
            selected_khu_vuc_ids = set(int(room) for room in rooms)

            # Update or create new applications
            new_records = []
            for ma_khu_vuc in selected_khu_vuc_ids:
                if ma_khu_vuc in current_khu_vuc_ids:
                    ap_dung = current_ap_dungs.get(MA_KHU_VUC_id=ma_khu_vuc)
                    ap_dung.GIA_DICH_VU_AD = gia_dich_vu
                    ap_dung.LOAI_DICH_VU_AD = 'chi_so' if dong_ho_dien_nuoc else 'thang'
                    ap_dung.save()
                else:
                    new_records.append(LichSuApDungDichVu(
                        MA_KHU_VUC_id=ma_khu_vuc,
                        MA_DICH_VU=dich_vu,
                        NGAY_AP_DUNG_DV=date.today(),
                        GIA_DICH_VU_AD=gia_dich_vu,
                        LOAI_DICH_VU_AD='chi_so' if dong_ho_dien_nuoc else 'thang'
                    ))
            if new_records:
                LichSuApDungDichVu.objects.bulk_create(new_records)

            # Deactivate unselected areas
            for ap_dung in current_ap_dungs:
                if ap_dung.MA_KHU_VUC_id not in selected_khu_vuc_ids:
                    ap_dung.NGAY_HUY_DV = date.today()
                    ap_dung.save()

        messages.success(request, 'Cập nhật dịch vụ thành công!')
        return redirect('dichvu:dichvu_list')

    return redirect('dichvu:dichvu_list')

@require_POST
def xoa_dich_vu(request, ma_dich_vu):
    dich_vu = get_object_or_404(DichVu, MA_DICH_VU=ma_dich_vu)
    
    # Check if the service is currently applied to any area
    is_applied = LichSuApDungDichVu.objects.filter(
        MA_DICH_VU=dich_vu,
        NGAY_HUY_DV__isnull=True
    ).exists()

    # If service is applied, rely on frontend confirmation
    if is_applied and not request.POST.get('confirm_delete'):
        # This case is handled by the form's onsubmit confirmation
        pass

    with transaction.atomic():
        # Delete all related LichSuApDungDichVu records
        LichSuApDungDichVu.objects.filter(MA_DICH_VU=dich_vu).delete()
        # Delete the service
        dich_vu.delete()

    messages.success(request, f"Dịch vụ '{dich_vu.TEN_DICH_VU}' và các áp dụng liên quan đã được xóa thành công.")
    return redirect('dichvu:dichvu_list')


def get_dichvu_with_chiso_for_phong(phong):
    """
    Helper function để lấy danh sách dịch vụ với chỉ số cho một phòng
    Sử dụng cùng logic như view_lap_hop_dong để đảm bảo tính nhất quán
    """
    from apps.hopdong.models import HopDong
    
    # Lấy danh sách dịch vụ áp dụng cho khu vực của phòng
    lichsu_dichvu = LichSuApDungDichVu.objects.filter(
        MA_KHU_VUC=phong.MA_KHU_VUC,
        NGAY_HUY_DV__isnull=True
    ).select_related('MA_DICH_VU')

    # Tạo danh sách dịch vụ với chỉ số từ hợp đồng cuối cùng
    result = []
    
    for lichsu in lichsu_dichvu:
        # Lấy hợp đồng cuối cùng của phòng
        latest_contract = HopDong.objects.filter(
            MA_PHONG=phong,
            TRANG_THAI_HD__in=['Đã kết thúc', 'Hủy']
        ).order_by('-NGAY_TRA_PHONG').first()
        
        chi_so_cu = 0
        so_luong_cu = 1
        
        if latest_contract:
            # Lấy chỉ số từ hợp đồng cuối cùng - sử dụng relationship qua MA_HOP_DONG
            latest_chiso = ChiSoDichVu.objects.filter(
                MA_HOP_DONG__MA_PHONG=phong,
                MA_DICH_VU=lichsu.MA_DICH_VU,
                MA_HOP_DONG=latest_contract
            ).order_by('-NGAY_GHI_CS').first()
            
            if latest_chiso:
                chi_so_cu = latest_chiso.CHI_SO_MOI
                so_luong_cu = latest_chiso.SO_LUONG
        else:
            # Nếu không có hợp đồng cũ, lấy chỉ số mới nhất từ tất cả hợp đồng của phòng
            latest_chiso = ChiSoDichVu.objects.filter(
                MA_DICH_VU=lichsu.MA_DICH_VU,
                MA_HOP_DONG__MA_PHONG=phong
            ).order_by('-NGAY_GHI_CS').first()
            
            if latest_chiso:
                chi_so_cu = latest_chiso.CHI_SO_MOI
                so_luong_cu = latest_chiso.SO_LUONG

        # Tạo object giống latest_chiso để template hoạt động
        chiso_obj = type('ChiSo', (), {
            'CHI_SO_CU': chi_so_cu,
            'CHI_SO_MOI': chi_so_cu,  # Mặc định bằng cũ
            'SO_LUONG': so_luong_cu
        })()
        
        result.append({
            'lichsu': lichsu,
            'latest_chiso': chiso_obj
        })
    
    return result


def lay_dich_vu_theo_phong(request):
    """
    AJAX view để lấy danh sách dịch vụ theo phòng
    """
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập'})
    
    ma_phong = request.GET.get('ma_phong')
    if not ma_phong:
        return JsonResponse({'success': False, 'message': 'Thiếu mã phòng'})
    
    try:
        from apps.phongtro.models import PhongTro
        
        phong = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
        
        # Sử dụng helper function chung
        lichsu_dichvu_with_chiso = get_dichvu_with_chiso_for_phong(phong)
        
        # Serialize data cho AJAX response
        dich_vu_data = []
        for item in lichsu_dichvu_with_chiso:
            lichsu = item['lichsu']
            chiso = item['latest_chiso']
            
            dich_vu_data.append({
                'MA_DICH_VU': lichsu.MA_DICH_VU.MA_DICH_VU,
                'TEN_DICH_VU': lichsu.MA_DICH_VU.TEN_DICH_VU,
                'DON_VI_TINH': lichsu.MA_DICH_VU.DON_VI_TINH,
                'LOAI_DICH_VU': lichsu.MA_DICH_VU.LOAI_DICH_VU,
                'GIA_DICH_VU_AD': float(lichsu.GIA_DICH_VU_AD) if lichsu.GIA_DICH_VU_AD else 0,
                'CHI_SO_CU': chiso.CHI_SO_CU,
                'CHI_SO_MOI': chiso.CHI_SO_MOI,
                'SO_LUONG': chiso.SO_LUONG,
            })
        
        return JsonResponse({
            'success': True,
            'dich_vus': dich_vu_data,
            'message': f'Tìm thấy {len(dich_vu_data)} dịch vụ'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })