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
    """AJAX - Lấy danh sách phòng theo khu vực."""
    khu_vuc_id = request.GET.get('khu_vuc_id')
    if not khu_vuc_id:
        return JsonResponse({'error': 'Thiếu mã khu vực'}, status=400)
    
    try:
        from apps.hopdong.models import HopDong
        phong_tros = PhongTro.objects.filter(
            MA_KHU_VUC_id=khu_vuc_id,
            hopdong__TRANG_THAI_HD='Đang hoạt động'
        ).distinct().values('MA_PHONG', 'TEN_PHONG')
        
        phong_list = list(phong_tros)
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
    """AJAX - Lấy chỉ số cũ của dịch vụ."""
    ma_phong = request.GET.get('ma_phong')
    ma_dich_vu = request.GET.get('ma_dich_vu')
    
    if not ma_phong or not ma_dich_vu:
        return JsonResponse({'error': 'Thiếu thông tin phòng hoặc dịch vụ'}, status=400)
    
    try:
        # Lấy hợp đồng hiệu lực của phòng
        from apps.hopdong.models import HopDong
        from apps.phongtro.models import PhongTro
        
        phong = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
        hop_dong = HopDong.objects.filter(
            MA_PHONG=phong,
            TRANG_THAI_HD='Đang hoạt động'
        ).first()
        
        if not hop_dong:
            return JsonResponse({'chi_so_cu': 0})
        
        # Lấy chỉ số mới nhất của dịch vụ trong hợp đồng này
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
    """AJAX - Kiểm tra chỉ số đã ghi trong kỳ thanh toán hiện tại"""
    ma_phong = request.GET.get('ma_phong')
    
    if not ma_phong:
        return JsonResponse({'error': 'Thiếu thông tin phòng'}, status=400)
    
    try:
        from apps.hopdong.models import HopDong
        from apps.phongtro.models import PhongTro
        
        phong = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
        hop_dong = HopDong.objects.filter(
            MA_PHONG=phong,
            TRANG_THAI_HD='Đang hoạt động'
        ).first()
        
        if not hop_dong:
            return JsonResponse({'error': 'Không tìm thấy hợp đồng hiệu lực'}, status=404)
        
        # Lấy chỉ số có thể chỉnh sửa trong kỳ hiện tại
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
    """Lưu chỉ số dịch vụ sử dụng."""
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
        
        # Lấy thông tin phòng và hợp đồng
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

    # Lấy danh sách phòng trọ
    phong_tros = PhongTro.objects.filter(MA_PHONG__in=[5, 6]).values('MA_PHONG', 'TEN_PHONG')

    # Lấy dữ liệu chỉ số dịch vụ theo từng phòng trọ
    chi_so_dich_vus = ChiSoDichVu.objects.select_related('MA_DICH_VU').values(
        'MA_CHI_SO', 'MA_PHONG_id', 'MA_DICH_VU_id', 'CHI_SO_CU', 'CHI_SO_MOI', 'NGAY_GHI_CS',
        'MA_DICH_VU__DON_VI_TINH', 'MA_DICH_VU__GIA_DICH_VU'
    )
    # Nhóm theo MA_PHONG
    chi_so_grouped = {}
    for chi_so in chi_so_dich_vus:
        ma_phong = chi_so['MA_PHONG_id']
        if ma_phong not in chi_so_grouped:
            chi_so_grouped[ma_phong] = []
        chi_so_grouped[ma_phong].append(chi_so)

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
    """Hàm chung để chuẩn bị dữ liệu thống kê dịch vụ."""
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

    # Truy vấn phòng trọ
    phong_tros_qs = PhongTro.objects.all().distinct()
    if start_of_month and end_of_month:
        phong_tros_qs = phong_tros_qs.filter(
            chisodichvu__NGAY_GHI_CS__range=[start_of_month, end_of_month]
        ).distinct()
    
    # Áp dụng bộ lọc khu vực
    if khu_vuc_id and khu_vuc_id != 'all':
        phong_tros_qs = phong_tros_qs.filter(MA_KHU_VUC_id=khu_vuc_id)
    
    # Áp dụng bộ lọc phòng trọ
    if phong_tro_id and phong_tro_id != 'all':
        phong_tros_qs = phong_tros_qs.filter(MA_PHONG=phong_tro_id)

    phong_tros = phong_tros_qs.values('MA_PHONG', 'TEN_PHONG')
    
    # Truy vấn dịch vụ
    dich_vus_qs = DichVu.objects.order_by('MA_DICH_VU')
    
    # Áp dụng bộ lọc loại dịch vụ
    if loai_dich_vu and loai_dich_vu != 'all':
        dich_vus_qs = dich_vus_qs.filter(LOAI_DICH_VU=loai_dich_vu)
    
    dich_vus = dich_vus_qs.values('MA_DICH_VU', 'TEN_DICH_VU', 'DON_VI_TINH', 'GIA_DICH_VU')

    # Truy vấn chỉ số dịch vụ
    chi_so_dich_vus_qs = ChiSoDichVu.objects.select_related('MA_DICH_VU')
    if start_of_month and end_of_month:
        chi_so_dich_vus_qs = chi_so_dich_vus_qs.filter(
            NGAY_GHI_CS__range=[start_of_month, end_of_month]
        )
    
    # Áp dụng bộ lọc loại dịch vụ cho chỉ số dịch vụ
    if loai_dich_vu and loai_dich_vu != 'all':
        chi_so_dich_vus_qs = chi_so_dich_vus_qs.filter(MA_DICH_VU__LOAI_DICH_VU=loai_dich_vu)

    chi_so_dich_vus = chi_so_dich_vus_qs.values(
        'MA_PHONG_id', 'MA_DICH_VU_id', 'CHI_SO_CU', 'CHI_SO_MOI',
        'MA_DICH_VU__DON_VI_TINH', 'MA_DICH_VU__GIA_DICH_VU'
    )

    # Nhóm chỉ số theo phòng trọ
    chi_so_by_phong = defaultdict(list)
    for chi_so in chi_so_dich_vus:
        chi_so_by_phong[chi_so['MA_PHONG_id']].append(chi_so)

    # Tính toán tổng và chuẩn bị dữ liệu
    total_values = {dv['TEN_DICH_VU']: 0 for dv in dich_vus}
    total_chiso = {dv['TEN_DICH_VU']: 0 for dv in dich_vus if dv['DON_VI_TINH'] != 'Tháng'}
    total_so_lan_su_dung = {dv['TEN_DICH_VU']: 0 for dv in dich_vus if dv['DON_VI_TINH'] == 'Tháng'}
    
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
            chi_so_cu = chi_so_moi = chiso_difference = service_total = 0

            if dich_vu['DON_VI_TINH'] == 'Tháng':
                service_total = chi_so['MA_DICH_VU__GIA_DICH_VU'] if chi_so else dich_vu['GIA_DICH_VU'] or 0
                if chi_so:
                    total_so_lan_su_dung[dich_vu['TEN_DICH_VU']] += 1
                excel_row[f'{dich_vu["TEN_DICH_VU"]}_Sử_dụng'] = 1 if chi_so else 0
                excel_row[f'{dich_vu["TEN_DICH_VU"]}_Thành_tiền'] = service_total
            else:
                chi_so_cu = chi_so['CHI_SO_CU'] if chi_so else 0
                chi_so_moi = chi_so['CHI_SO_MOI'] if chi_so else 0
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
                'don_vi_tinh': dich_vu['DON_VI_TINH']
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
            headers.extend([f'{dich_vu["TEN_DICH_VU"]}_Sử_dụng', f'{dich_vu["TEN_DICH_VU"]}_Thành_tiền'])
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