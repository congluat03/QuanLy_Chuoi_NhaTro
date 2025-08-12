from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from .models import HopDong, LichSuHopDong
from apps.phongtro.models import PhongTro, CocPhong
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from apps.khachthue.models import CccdCmnd, KhachThue
from apps.phongtro.models import TAISANBANGIAO
from apps.dichvu.models import ChiSoDichVu, LichSuApDungDichVu


def hopdong_list(request):
    # Status mapping for contract status display
    status_map = {
        '1': {'text': 'Trong thời hạn', 'color': 'bg-green-600'},
        '2': {'text': 'Đang báo kết thúc', 'color': 'bg-yellow-500'},
        '3': {'text': 'Sắp kết thúc', 'color': 'bg-orange-500'},
        '0': {'text': 'Đã kết thúc', 'color': 'bg-red-600'},
    }

    # Fetch contracts with related room and filter for representative tenant
    hop_dongs = HopDong.objects.select_related('MA_PHONG').prefetch_related('lichsuhopdong__MA_KHACH_THUE').order_by('MA_HOP_DONG')
    
    # Add status display to each contract
    for contract in hop_dongs:
        contract.get_status_display = lambda: status_map.get(contract.TRANG_THAI_HD, {'text': 'Không xác định', 'color': 'bg-gray-600'})

    # Pagination
    paginator = Paginator(hop_dongs, 10)
    page_number = request.GET.get('page')
    hop_dongs_page = paginator.get_page(page_number)

    # Fetch all rooms
    phong_tros = PhongTro.objects.order_by('MA_PHONG')

    return render(request, 'admin/hopdong/danhsach_hopdong.html', {
        'hop_dongs': hop_dongs_page,
        'phong_tros': phong_tros,
    })
@require_http_methods(['GET'])
def view_chinh_sua_hop_dong(request, ma_hop_dong):
    # Lấy hợp đồng hoặc trả về 404
    hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
    
    # Lấy bản ghi cọc phòng mới nhất cho phòng
    coc_phong = CocPhong.objects.filter(
                MA_PHONG=hop_dong.MA_PHONG,
                TRANG_THAI_CP__in=['Đã cọc', 'Chờ xác nhận']
            ).select_related('MA_KHACH_THUE').first()
    # Lấy thông tin khách thuê từ lịch sử hợp đồng (người đại diện)
    lich_su = LichSuHopDong.objects.filter(
        MA_HOP_DONG=hop_dong,
        MOI_QUAN_HE='Chủ hợp đồng'
    ).select_related('MA_KHACH_THUE').first()
    
    khach_thue = lich_su.MA_KHACH_THUE if lich_su else None
    
    # Lấy thông tin CCCD/CMND của khách thuê
    cccd_cmnd = CccdCmnd.objects.filter(MA_KHACH_THUE=khach_thue).first() if khach_thue else None
    
    # Lấy danh sách phòng trọ
    phong_tros = PhongTro.objects.all().only('MA_PHONG', 'TEN_PHONG')

    return render(request, 'admin/hopdong/themsua_hopdong.html', {
        'hop_dong': hop_dong,
        'coc_phong': coc_phong,
        'khach_thue': khach_thue,
        'cccd_cmnd': cccd_cmnd,
        'phong_tros': phong_tros,
    })
def view_them_hop_dong(request):
    # Ví dụ: lấy danh sách phòng thuộc nhà trọ có mã là 1
    phong_tros = PhongTro.lay_phong_theo_ma_nha_tro(1)
    return render(request, 'admin/hopdong/themsua_hopdong.html', {
        'phong_tros': phong_tros,
    })
@csrf_exempt
def kiem_tra_coc_phong(request, ma_phong):
    try:
        # Tìm bản ghi cọc phòng với MA_PHONG và trạng thái không phải "Đã hoàn trả" hoặc "Đã thu hồi"
        coc_phong = CocPhong.objects.filter(
            MA_PHONG_id=ma_phong,
            TRANG_THAI_CP__in=['Đã cọc', 'Chờ xác nhận']  # Điều chỉnh trạng thái theo yêu cầu
        ).select_related('MA_KHACH_THUE').first()

        if coc_phong:
            # Trả về thông tin cọc phòng và khách thuê
            return JsonResponse({
                'success': True,
                'coc_phong': {
                    'TIEN_COC_PHONG': str(coc_phong.TIEN_COC_PHONG),
                    'TIEN_PHONG': str(coc_phong.MA_PHONG.GIA_PHONG),
                    'MA_KHACH_THUE': {
                        'MA_KHACH_THUE': coc_phong.MA_KHACH_THUE.MA_KHACH_THUE,
                        'HO_TEN_KT': coc_phong.MA_KHACH_THUE.HO_TEN_KT,
                        'GIOI_TINH_KT': coc_phong.MA_KHACH_THUE.GIOI_TINH_KT,
                        'NGAY_SINH_KT': coc_phong.MA_KHACH_THUE.NGAY_SINH_KT.strftime('%Y-%m-%d') if coc_phong.MA_KHACH_THUE.NGAY_SINH_KT else '',
                        'SDT_KT': coc_phong.MA_KHACH_THUE.SDT_KT,
                        'SO_CMND_CCCD': coc_phong.MA_KHACH_THUE.cccd_cmnd.first().SO_CMND_CCCD if coc_phong.MA_KHACH_THUE.cccd_cmnd.exists() else ''
                    }
                }
            })
        else:
            return JsonResponse({'success': False, 'message': 'Không tìm thấy cọc phòng hợp lệ'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})



@require_http_methods('POST')
def them_hop_dong(request):
    messages.success(request, 'Thêm hợp đồng thành công!')
    if request.method == 'POST':
        try:
            messages.success(request, 'Thêm hợp đồng thành công!')
            data = {
                'MA_PHONG': request.POST.get('MA_PHONG'),
                'MA_KHACH_THUE': request.POST.get('MA_KHACH_THUE'),
                'NGAY_LAP_HD': request.POST.get('NGAY_LAP_HD'),
                'THOI_HAN_HD': request.POST.get('THOI_HAN_HD'),
                'NGAY_NHAN_PHONG': request.POST.get('NGAY_NHAN_PHONG'),
                'NGAY_TRA_PHONG': request.POST.get('NGAY_TRA_PHONG'),
                'SO_THANH_VIEN_TOI_DA': request.POST.get('SO_THANH_VIEN_TOI_DA'),
                'GIA_THUE': request.POST.get('GIA_THUE'),
                'NGAY_THU_TIEN': request.POST.get('NGAY_THU_TIEN'),
                'CHU_KY_THANH_TOAN': request.POST.get('KY_THANH_TOAN'),
                'THOI_DIEM_THANH_TOAN': request.POST.get('THOI_DIEM_THANH_TOAN'),
                'GHI_CHU_HD': request.POST.get('GHI_CHU_HD'),
                'TIEN_COC_PHONG': request.POST.get('TIEN_COC_PHONG'),
                'HO_TEN_KT': request.POST.get('HO_TEN_KT'),
                'GIOI_TINH_KT': request.POST.get('GIOI_TINH_KT'),
                'NGAY_SINH_KT': request.POST.get('NGAY_SINH_KT'),
                'SDT_KT': request.POST.get('SDT_KT'),
                'SO_CMND_CCCD': request.POST.get('SO_CMND_CCCD'), 
                'GIA_COC_HD' : request.POST.get('GIA_COC_HD', 0.00),
            }
            dich_vu_su_dung = []
            index = 1
            while f'dichvu[{index}][MA_DICH_VU]' in request.POST:
                dich_vu = {
                    'MA_DICH_VU': request.POST.get(f'dichvu[{index}][MA_DICH_VU]', ''),
                    'CHI_SO_MOI': request.POST.get(f'dichvu[{index}][CHI_SO_MOI]', ''),
                    'SO_LUONG': request.POST.get(f'dichvu[{index}][SO_LUONG]', ''),
                }
                dich_vu_su_dung.append(dich_vu)
                index += 1
            taisan_list = []
            index = 1
            while f'taisan[{index}][MA_TAI_SAN]' in request.POST:
                ts = {
                    'MA_TAI_SAN': request.POST.get(f'taisan[{index}][MA_TAI_SAN]', ''),
                    'SO_LUONG': request.POST.get(f'taisan[{index}][so_luong]', ''),
                }
                taisan_list.append(ts)
                index += 1
            # return JsonResponse({'chi_so_dich_vu': dich_vu_su_dung})
            # return JsonResponse(dict(request.POST))
            hopdong_obj = HopDong.tao_hop_dong(data)
            ChiSoDichVu.tao_danh_sach_chi_so(hop_dong=hopdong_obj, ds_dich_vu=dich_vu_su_dung)
            TAISANBANGIAO.tao_danh_sach_tai_san_ban_giao(hop_dong=hopdong_obj, ds_tai_san=taisan_list)

            messages.success(request, 'Thêm hợp đồng thành công!')
            return redirect('hopdong:hopdong_list')
        except ValueError as e:
            messages.error(request, f'Lỗi dữ liệu: {str(e)}')
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống: {str(e)}')

    phong_tros = PhongTro.objects.all().only('MA_PHONG', 'TEN_PHONG')  # Tối ưu truy vấn
    return render(request, 'admin/hopdong/themsua_hopdong.html', {'phong_tros': phong_tros})

@require_http_methods('POST')
def chinh_sua_hop_dong(request, ma_hop_dong):
    hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
    
    if request.method == 'POST':
        try:
            data = {
                'MA_PHONG': request.POST.get('MA_PHONG'),
                'MA_KHACH_THUE': request.POST.get('MA_KHACH_THUE'),
                'NGAY_LAP_HD': request.POST.get('NGAY_LAP_HD'),
                'THOI_HAN_HD': request.POST.get('THOI_HAN_HD'),
                'NGAY_NHAN_PHONG': request.POST.get('NGAY_NHAN_PHONG'),
                'NGAY_TRA_PHONG': request.POST.get('NGAY_TRA_PHONG'),
                'SO_THANH_VIEN_TOI_DA': request.POST.get('SO_THANH_VIEN_TOI_DA'),
                'GIA_THUE': request.POST.get('GIA_THUE'),
                'NGAY_THU_TIEN': request.POST.get('NGAY_THU_TIEN'),
                'PHUONG_THUC_THANH_TOAN': request.POST.get('PHUONG_THUC_THANH_TOAN'),
                'THOI_DIEM_THANH_TOAN': request.POST.get('THOI_DIEM_THANH_TOAN'),
                'GHI_CHU_HD': request.POST.get('GHI_CHU_HD'),
                # Dữ liệu cho Cọc phòng
                'MA_COC_PHONG': request.POST.get('MA_COC_PHONG'),
                'TIEN_COC_PHONG': request.POST.get('TIEN_COC_PHONG'),
                'GHI_CHU_CP': request.POST.get('GHI_CHU_CP'),

                # Dữ liệu khách thuê
                'HO_TEN_KT': request.POST.get('HO_TEN_KT'),
                'SDT_KT': request.POST.get('SDT_KT'),
                'NGAY_SINH_KT': request.POST.get('NGAY_SINH_KT'),
                'GIOI_TINH_KT': request.POST.get('GIOI_TINH_KT'),
                'SO_CMND_CCCD': request.POST.get('SO_CMND_CCCD'),
            }
            
            hop_dong.cap_nhat_hop_dong(data)
            messages.success(request, 'Cập nhật hợp đồng thành công!')
            return redirect('hopdong:hopdong_list')
        except ValueError as e:
            messages.error(request, f'Lỗi dữ liệu: {str(e)}')
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống: {str(e)}')

    phong_tros = PhongTro.objects.all().only('MA_PHONG', 'TEN_PHONG')
    coc_phong = CocPhong.objects.filter(MA_PHONG=hop_dong.MA_PHONG).select_related('MA_KHACH_THUE').first()
    return render(request, 'admin/hopdong/themsua_hopdong.html', {
        'hop_dong': hop_dong,
        'phong_tros': phong_tros,
        'coc_phong': coc_phong
    })
@require_http_methods('POST')
def xoa_hop_dong(request, ma_hop_dong):
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        hop_dong.delete_hop_dong()
        messages.success(request, f'Xóa hợp đồng {ma_hop_dong} và lịch sử hợp đồng liên quan thành công!')
        return redirect('hopdong:hopdong_list')
    except HopDong.DoesNotExist:
        messages.error(request, 'Hợp đồng không tồn tại.')
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
    return redirect('hopdong:hopdong_list')









def view_contract(request, hopdong_id):
    hopdong = get_object_or_404(HopDong, MA_HOP_DONG=hopdong_id)
    khachthue = KhachThue.objects.filter(lichsuhopdong__MA_HOP_DONG=hopdong).first()
    cccdcmnd = CccdCmnd.objects.filter(MA_KHACH_THUE=khachthue).first() if khachthue else None
    taisanbangiao = TAISANBANGIAO.objects.filter(MA_HOP_DONG=hopdong)
    
    # Lấy danh sách MA_DICH_VU duy nhất từ ChiSoDichVu và bản ghi đầu tiên
    chisodichvu_ids = ChiSoDichVu.objects.filter(MA_HOP_DONG=hopdong).values('MA_DICH_VU').distinct()
    chisodichvu = []
    for item in chisodichvu_ids:
        first_chisodichvu = ChiSoDichVu.objects.filter(
            MA_HOP_DONG=hopdong, 
            MA_DICH_VU=item['MA_DICH_VU']
        ).order_by('NGAY_GHI_CS').first()  # Lấy bản ghi đầu tiên theo NGAY_GHI_CS
        if first_chisodichvu:
            chisodichvu.append(first_chisodichvu)

    # Lấy danh sách dịch vụ từ LichSuApDungDichVu theo khu vực của phòng trọ
    phongtro = PhongTro.objects.get(MA_PHONG=hopdong.MA_PHONG_id)
    lichsu_dichvu, _ = LichSuApDungDichVu.get_dich_vu_ap_dung(phongtro.MA_KHU_VUC)

    # Tạo danh sách dịch vụ hợp nhất (loại bỏ trùng lặp MA_DICH_VU)
    dichvu_set = set()
    dichvu_list = []
    
    # Thêm dịch vụ từ ChiSoDichVu
    for csdv in chisodichvu:
        if csdv.MA_DICH_VU_id not in dichvu_set:
            dichvu_set.add(csdv.MA_DICH_VU_id)
            dichvu_list.append({
                'dichvu': csdv.MA_DICH_VU,
                'chi_so_cu': csdv.CHI_SO_CU,
                'chi_so_moi': csdv.CHI_SO_MOI,
                'ngay_ghi_cs': csdv.NGAY_GHI_CS,
                'gia': csdv.MA_DICH_VU.GIA_DICH_VU,
                'don_vi': csdv.MA_DICH_VU.DON_VI_TINH,
                'nguon': 'ChiSoDichVu'
            })

    # Thêm dịch vụ từ LichSuApDungDichVu
    for lsdv in lichsu_dichvu:
        if lsdv.MA_DICH_VU_id not in dichvu_set:
            dichvu_set.add(lsdv.MA_DICH_VU_id)
            dichvu_list.append({
                'dichvu': lsdv.MA_DICH_VU,
                'chi_so_cu': None,
                'chi_so_moi': None,
                'ngay_ghi_cs': lsdv.NGAY_AP_DUNG_DV,
                'gia': lsdv.GIA_DICH_VU_AD or lsdv.MA_DICH_VU.GIA_DICH_VU,
                'don_vi': lsdv.MA_DICH_VU.DON_VI_TINH,
                'nguon': 'LichSuApDungDichVu'
            })

    context = {
        'hopdong': hopdong,
        'khachthue': khachthue,
        'cccdcmnd': cccdcmnd,
        'taisanbangiao': taisanbangiao,
        'dichvu_list': dichvu_list,  # Danh sách dịch vụ hợp nhất
        'ten_chu_nha': 'Tên chủ nhà',  # Thay bằng dữ liệu thực tế
        'dia_chi_phong_tro': f"{phongtro.MA_KHU_VUC.DV_HANH_CHINH_CAP3}, {phongtro.MA_KHU_VUC.DV_HANH_CHINH_CAP2}, {phongtro.MA_KHU_VUC.DV_HANH_CHINH_CAP1}",
        'dia_chi_chu_nha': 'Địa chỉ chủ nhà',  # Thay bằng dữ liệu thực tế
        'so_cmnd_chu_nha': 'Số CMND/CCCD chủ nhà',  # Thay bằng dữ liệu thực tế
        'sdt_chu_nha': 'Số điện thoại chủ nhà',  # Thay bằng dữ liệu thực tế
        'dia_phuong': f"{phongtro.MA_KHU_VUC.DV_HANH_CHINH_CAP1}",  # Lấy từ KhuVuc
    }
    return render(request, 'admin/hopdong/vanban_hopdong.html', context)