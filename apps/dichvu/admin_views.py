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