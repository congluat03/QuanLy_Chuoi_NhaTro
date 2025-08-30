# -*- coding: utf-8 -*-
"""
Views mới cho các chức năng hợp đồng
"""
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date, timedelta
import logging
import json

from .models import HopDong
from apps.phongtro.models import CocPhong

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def xac_nhan_hop_dong(request, ma_hop_dong):
    """Xác nhận hợp đồng và sinh hóa đơn bắt đầu nếu chưa có"""
    
    logger.info(f"=== BẮT ĐẦU XÁC NHẬN HỢP ĐỒNG {ma_hop_dong} ===")
    logger.info(f"Session is_authenticated: {request.session.get('is_authenticated')}")
    logger.info(f"User: {getattr(request, 'user', 'None')}")
    logger.info(f"Request method: {request.method}")
    
    # Kiểm tra authentication
    if not request.session.get('is_authenticated'):
        logger.warning(f"Authentication failed for contract {ma_hop_dong}")
        messages.error(request, 'Bạn cần đăng nhập để thực hiện thao tác này')
        return redirect('admin_hopdong:hopdong_list')
    
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        logger.info(f"Tìm thấy hợp đồng: {hop_dong.MA_HOP_DONG}, trạng thái hiện tại: {hop_dong.TRANG_THAI_HD}")
        
        # Kiểm tra trạng thái hợp đồng
        if hop_dong.TRANG_THAI_HD != 'Chờ xác nhận':
            logger.warning(f"Hợp đồng {ma_hop_dong} không ở trạng thái 'Chờ xác nhận', hiện tại: {hop_dong.TRANG_THAI_HD}")
            messages.error(request, 'Chỉ có thể xác nhận hợp đồng đang ở trạng thái "Chờ xác nhận"')
            return redirect('admin_hopdong:hopdong_list')
        
        # Kiểm tra xem đã có hóa đơn bắt đầu chưa
        da_co_hoa_don = hop_dong.get_hoa_don_bat_dau() is not None
        logger.info(f"Đã có hóa đơn bắt đầu: {da_co_hoa_don}")
        
        logger.info("Bắt đầu gọi hop_dong.xac_nhan_hop_dong()")
        hoa_don, error = hop_dong.xac_nhan_hop_dong()
        logger.info(f"Kết quả xác nhận: hoa_don={hoa_don}, error={error}")
        
        if hoa_don and error is None:
            logger.info("Xác nhận hợp đồng thành công!")
            if da_co_hoa_don:
                messages.success(
                    request, 
                    f'Đã xác nhận hợp đồng! Hóa đơn bắt đầu đã có sẵn: {hoa_don.MA_HOA_DON}'
                )
            else:
                messages.success(
                    request, 
                    f'Đã xác nhận hợp đồng và tạo hóa đơn bắt đầu! Mã hóa đơn: {hoa_don.MA_HOA_DON}'
                )
        elif error:
            logger.error(f"Lỗi xác nhận hợp đồng: {error}")
            messages.error(request, f'Lỗi: {error}')
        else:
            logger.info("Xác nhận hợp đồng thành công (không có hóa đơn)")
            messages.success(request, 'Đã xác nhận hợp đồng!')
            
    except Exception as e:
        logger.error(f"Exception trong xac_nhan_hop_dong: {e}", exc_info=True)
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
    
    logger.info(f"=== KẾT THÚC XÁC NHẬN HỢP ĐỒNG {ma_hop_dong} - REDIRECT VỀ DANH SÁCH ===")
    return redirect('admin_hopdong:hopdong_list')


@csrf_exempt
@require_POST
def gia_han_hop_dong(request, ma_hop_dong):
    """Gia hạn hợp đồng - trả về JSON response"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy dữ liệu từ form
        ngay_tra_phong_moi_str = request.POST.get('ngay_tra_phong_moi')
        thoi_han_moi = request.POST.get('thoi_han_moi')
        gia_thue_moi = request.POST.get('gia_thue_moi')
        ly_do = request.POST.get('ly_do_gia_han')
        
        # Validate dữ liệu đầu vào
        if not ngay_tra_phong_moi_str:
            return JsonResponse({
                'success': False, 
                'message': 'Vui lòng chọn ngày gia hạn'
            })
        
        if not ly_do or not ly_do.strip():
            return JsonResponse({
                'success': False, 
                'message': 'Vui lòng nhập lý do gia hạn'
            })
        
        # Validate và convert ngày
        try:
            ngay_tra_phong_moi = datetime.strptime(ngay_tra_phong_moi_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False, 
                'message': 'Ngày trả phòng mới không hợp lệ'
            })
        
        # Convert giá thuê mới (nếu có)
        if gia_thue_moi:
            try:
                gia_thue_moi = float(gia_thue_moi)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False, 
                    'message': 'Giá thuê mới không hợp lệ'
                })
        else:
            gia_thue_moi = None
        
        # Thực hiện gia hạn
        success, lich_su_or_error = hop_dong.gia_han_hop_dong(
            ngay_tra_phong_moi=ngay_tra_phong_moi,
            thoi_han_moi=thoi_han_moi,
            gia_thue_moi=gia_thue_moi,
            ly_do=ly_do.strip()
        )
        
        if success:
            lich_su = lich_su_or_error
            return JsonResponse({
                'success': True,
                'message': f'Đã gia hạn hợp đồng đến {ngay_tra_phong_moi.strftime("%d/%m/%Y")}!',
                'data': {
                    'ma_dieu_chinh': lich_su.MA_DIEU_CHINH,
                    'ngay_gia_han': ngay_tra_phong_moi.strftime('%d/%m/%Y'),
                    'ly_do': ly_do.strip()
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'Lỗi gia hạn: {lich_su_or_error}'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        })


@require_POST
def ket_thuc_hop_dong(request, ma_hop_dong):
    """Kết thúc hợp đồng và sinh hóa đơn cuối"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy ngày kết thúc thực tế (nếu có)
        ngay_ket_thuc_str = request.POST.get('ngay_ket_thuc_thuc_te')
        ngay_ket_thuc = None
        
        if ngay_ket_thuc_str:
            try:
                ngay_ket_thuc = datetime.strptime(ngay_ket_thuc_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                messages.error(request, 'Ngày kết thúc không hợp lệ')
                return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)
        
        # Thực hiện kết thúc hợp đồng
        hoa_don_cuoi, error = hop_dong.ket_thuc_hop_dong(ngay_ket_thuc)
        
        if hoa_don_cuoi:
            messages.success(
                request, 
                f'Đã kết thúc hợp đồng và sinh hóa đơn cuối! Mã hóa đơn: {hoa_don_cuoi.MA_HOA_DON}'
            )
        elif error:
            messages.error(request, f'Lỗi kết thúc hợp đồng: {error}')
        else:
            messages.success(request, 'Đã kết thúc hợp đồng!')
            
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
    
    return redirect('admin_hopdong:hopdong_list')


def handle_cancel_contract(hop_dong, data):
    """Xử lý kết thúc hợp đồng"""
    try:
        ly_do = data.get('ly_do', 'Kết thúc bởi admin')
        
        # Logic kết thúc hợp đồng
        hop_dong.TRANG_THAI_HD = 'Đã hủy'
        hop_dong.GHI_CHU_HD = f"{hop_dong.GHI_CHU_HD or ''}\n[Kết thúc {date.today()}]: {ly_do}"
        hop_dong.save()
        
        # Cập nhật trạng thái phòng về trống
        hop_dong.MA_PHONG.TRANG_THAI_P = 'Đang trống'
        hop_dong.MA_PHONG.save()
        
        # Cập nhật trạng thái cọc phòng
        CocPhong.cap_nhat_trang_thai_coc(hop_dong.MA_PHONG, 'Đã thu hồi')
        
        return JsonResponse({
            'success': True,
            'message': 'Đã kết thúc hợp đồng',
            'data': {
                'trang_thai': hop_dong.TRANG_THAI_HD
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi kết thúc hợp đồng: {str(e)}'
        })


@csrf_exempt
@require_POST
def bao_ket_thuc_som(request, ma_hop_dong):
    """Báo kết thúc sớm hợp đồng - trả về JSON response"""
    
    try:
        logger.info(f"Bắt đầu xử lý báo kết thúc hợp đồng {ma_hop_dong}")
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Log thông tin hợp đồng hiện tại
        logger.info(f"Hợp đồng {ma_hop_dong}: Trạng thái={hop_dong.TRANG_THAI_HD}")
        
        # Lấy dữ liệu từ form
        ngay_bao_ket_thuc_str = request.POST.get('ngay_bao_ket_thuc')
        ly_do = request.POST.get('ly_do_bao_ket_thuc')
        
        logger.info(f"Dữ liệu form: ngày={ngay_bao_ket_thuc_str}, lý do='{ly_do}'")
        
        # Validate dữ liệu đầu vào
        if not ngay_bao_ket_thuc_str:
            logger.warning(f"Thiếu ngày báo kết thúc cho hợp đồng {ma_hop_dong}")
            return JsonResponse({
                'success': False, 
                'message': 'Vui lòng chọn ngày báo kết thúc'
            })
        
        if not ly_do or not ly_do.strip():
            logger.warning(f"Thiếu lý do báo kết thúc cho hợp đồng {ma_hop_dong}")
            return JsonResponse({
                'success': False, 
                'message': 'Vui lòng nhập lý do báo kết thúc'
            })
        
        # Validate và convert ngày
        try:
            ngay_bao_ket_thuc = datetime.strptime(ngay_bao_ket_thuc_str, '%Y-%m-%d').date()
            logger.info(f"Ngày báo kết thúc parsed: {ngay_bao_ket_thuc}")
        except (ValueError, TypeError) as e:
            logger.error(f"Lỗi parse ngày {ngay_bao_ket_thuc_str}: {e}")
            return JsonResponse({
                'success': False, 
                'message': 'Ngày báo kết thúc không hợp lệ'
            })
        
        # Thực hiện báo kết thúc trực tiếp
        logger.info(f"Gọi hop_dong.bao_ket_thuc_som")
        success, lich_su_or_error = hop_dong.bao_ket_thuc_som(
            ngay_bao_ket_thuc=ngay_bao_ket_thuc,
            ly_do=ly_do.strip()
        )
        
        logger.info(f"Kết quả báo kết thúc: success={success}")
        
        if success:
            lich_su = lich_su_or_error
            logger.info(f"Báo kết thúc thành công hợp đồng {ma_hop_dong} - Lịch sử ID: {lich_su.MA_DIEU_CHINH}")
            return JsonResponse({
                'success': True,
                'message': f'Đã báo kết thúc hợp đồng vào ngày {ngay_bao_ket_thuc.strftime("%d/%m/%Y")}!',
                'data': {
                    'ma_dieu_chinh': lich_su.MA_DIEU_CHINH,
                    'ngay_ket_thuc': ngay_bao_ket_thuc.strftime('%d/%m/%Y'),
                    'ly_do': ly_do.strip(),
                    'trang_thai_moi': hop_dong.TRANG_THAI_HD
                }
            })
        else:
            error_message = str(lich_su_or_error)
            logger.error(f"Báo kết thúc thất bại hợp đồng {ma_hop_dong}: {error_message}")
            return JsonResponse({
                'success': False,
                'message': f'Lỗi báo kết thúc: {error_message}'
            })
            
    except Exception as e:
        logger.error(f"Exception trong bao_ket_thuc_som view: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        })

def handle_early_end_contract(hop_dong, data):
    """Xử lý báo kết thúc sớm từ workflow"""
    
    try:
        # Hỗ trợ cả hai cách gọi: workflow và direct form
        # Workflow gửi data nested trong 'data' object
        nested_data = data.get('data', {})
        ngay_bao_ket_thuc_str = nested_data.get('early_end_date') or data.get('ngay_bao_ket_thuc')
        ly_do = (nested_data.get('reason') or data.get('ly_do') or '').strip()
        
        logger.info(f"handle_early_end_contract: ngày={ngay_bao_ket_thuc_str}, lý do='{ly_do}'")
        
        if not ngay_bao_ket_thuc_str:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu ngày báo kết thúc'
            })
        
        # Convert string to date
        try:
            ngay_bao_ket_thuc = datetime.strptime(ngay_bao_ket_thuc_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Ngày báo kết thúc không hợp lệ'
            })
        
        # Thực hiện báo kết thúc trực tiếp
        success, lich_su_or_error = hop_dong.bao_ket_thuc_som(
            ngay_bao_ket_thuc=ngay_bao_ket_thuc,
            ly_do=ly_do
        )
        
        if success:
            lich_su = lich_su_or_error
            return JsonResponse({
                'success': True,
                'message': f'Đã báo kết thúc hợp đồng vào ngày {ngay_bao_ket_thuc.strftime("%d/%m/%Y")}!',
                'data': {
                    'trang_thai': hop_dong.TRANG_THAI_HD,
                    'ma_dieu_chinh': lich_su.MA_DIEU_CHINH,
                    'ngay_ket_thuc': ngay_bao_ket_thuc.strftime('%d/%m/%Y'),
                    'ly_do': ly_do
                }
            })
        else:
            error_message = str(lich_su_or_error)
            return JsonResponse({
                'success': False,
                'message': f'Lỗi báo kết thúc: {error_message}'
            })
            
    except Exception as e:
        logger.error(f"Exception trong handle_early_end_contract: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        })


def view_ket_thuc_hop_dong(request, ma_hop_dong):
    """Hiển thị trang kết thúc hợp đồng"""
    from django.shortcuts import render
    
    # Kiểm tra authentication
    if not request.session.get('is_authenticated'):
        messages.error(request, 'Bạn cần đăng nhập để thực hiện thao tác này')
        return redirect('admin_hopdong:hopdong_list')
    
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Kiểm tra quyền truy cập và trạng thái hợp đồng
        if hop_dong.TRANG_THAI_HD in ['Đã kết thúc', 'Đã hủy']:
            messages.error(request, 'Hợp đồng này đã kết thúc, không thể thực hiện thao tác.')
            return redirect('admin_hopdong:hopdong_list')
        
        context = {
            'hop_dong': hop_dong,
        }
        
        return render(request, 'admin/hopdong/ket_thuc_hop_dong.html', context)
        
    except Exception as e:
        messages.error(request, f'Lỗi hiển thị trang kết thúc: {str(e)}')
        return redirect('admin_hopdong:hopdong_list')


@require_POST  
def api_cong_no_hop_dong(request, ma_hop_dong):
    """API lấy thông tin công nợ của hợp đồng"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy danh sách hóa đơn chưa thanh toán
        hoa_don_chua_thanh_toan = hop_dong.hoadon.filter(
            TRANG_THAI_HDON='Chưa thanh toán'
        ).order_by('-NGAY_LAP_HDON')
        
        danh_sach_no = []
        tong_cong_no = 0
        
        for hd in hoa_don_chua_thanh_toan:
            so_tien_con_no = hd.TONG_TIEN or 0
            tong_cong_no += so_tien_con_no
            
            danh_sach_no.append({
                'ma_hoa_don': hd.MA_HOA_DON,
                'loai_hoa_don': hd.LOAI_HOA_DON,
                'ngay_lap': hd.NGAY_LAP_HDON.strftime('%d/%m/%Y') if hd.NGAY_LAP_HDON else '-',
                'so_tien_con_no': so_tien_con_no,
                'han_thanh_toan': hd.HAN_THANH_TOAN.strftime('%d/%m/%Y') if hd.HAN_THANH_TOAN else '-'
            })
        
        return JsonResponse({
            'success': True,
            'hoa_don_chua_thanh_toan': danh_sach_no,
            'tong_cong_no': tong_cong_no,
            'so_hoa_don_no': len(danh_sach_no)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi lấy thông tin công nợ: {str(e)}'
        })


@require_POST
def api_tinh_toan_ket_thuc(request, ma_hop_dong):
    """API tính toán hóa đơn kết thúc"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy dữ liệu từ request
        data = json.loads(request.body)
        ngay_ket_thuc_str = data.get('ngay_ket_thuc')
        dich_vu_data = data.get('dich_vu_data', [])
        
        if not ngay_ket_thuc_str:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu ngày kết thúc'
            })
        
        # Convert ngày
        ngay_ket_thuc = datetime.strptime(ngay_ket_thuc_str, '%Y-%m-%d').date()
        
        # Tính toán tiền phòng theo ngày
        ngay_bat_dau_tinh = hop_dong.NGAY_NHAN_PHONG
        if not ngay_bat_dau_tinh:
            return JsonResponse({
                'success': False,
                'message': 'Hợp đồng chưa có ngày nhận phòng'
            })
        
        # Tính số ngày ở thực tế
        so_ngay = (ngay_ket_thuc - ngay_bat_dau_tinh).days + 1
        if so_ngay <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Ngày kết thúc phải sau ngày nhận phòng'
            })
        
        # Tính tiền phòng theo ngày
        gia_thue_thang = hop_dong.GIA_THUE or 0
        tien_phong_theo_ngay = (gia_thue_thang / 30) * so_ngay
        
        # Tính tiền dịch vụ từ dữ liệu frontend
        tien_dich_vu = 0
        for dv in dich_vu_data:
            tien_dich_vu += float(dv.get('thanh_tien', 0))
        
        # Tiền cọc hoàn trả
        tien_coc_hoan_tra = hop_dong.GIA_COC_HD or 0
        
        return JsonResponse({
            'success': True,
            'tien_phong_theo_ngay': round(tien_phong_theo_ngay),
            'tu_ngay': ngay_bat_dau_tinh.strftime('%d/%m/%Y'),
            'den_ngay': ngay_ket_thuc.strftime('%d/%m/%Y'),
            'so_ngay': so_ngay,
            'tien_dich_vu': tien_dich_vu,
            'tien_coc_hoan_tra': tien_coc_hoan_tra,
            'ngay_ket_thuc': ngay_ket_thuc.strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi tính toán: {str(e)}'
        })


@csrf_exempt
@require_POST
def thuc_hien_ket_thuc_hop_dong(request, ma_hop_dong):
    """API thực hiện kết thúc hợp đồng"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy dữ liệu từ request
        data = json.loads(request.body)
        ngay_ket_thuc_str = data.get('ngay_ket_thuc')
        ly_do = data.get('ly_do', '')
        khau_tru = data.get('khau_tru', 0)
        ghi_chu_khau_tru = data.get('ghi_chu_khau_tru', '')
        
        if not ngay_ket_thuc_str:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu ngày kết thúc'
            })
        
        # Convert ngày
        ngay_ket_thuc = datetime.strptime(ngay_ket_thuc_str, '%Y-%m-%d').date()
        
        # Thực hiện kết thúc hợp đồng
        hop_dong.TRANG_THAI_HD = 'Đã kết thúc'
        hop_dong.NGAY_KET_THUC_THUC_TE = ngay_ket_thuc
        if ly_do:
            hop_dong.GHI_CHU_HD = f"{hop_dong.GHI_CHU_HD or ''}\n[Kết thúc {ngay_ket_thuc}]: {ly_do}"
        hop_dong.save()
        
        # Cập nhật trạng thái phòng
        hop_dong.MA_PHONG.TRANG_THAI_P = 'Đang trống'
        hop_dong.MA_PHONG.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Đã kết thúc hợp đồng thành công vào ngày {ngay_ket_thuc.strftime("%d/%m/%Y")}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi kết thúc hợp đồng: {str(e)}'
        })


@require_POST
def api_lay_dich_vu_hop_dong(request, ma_hop_dong):
    """API lấy danh sách dịch vụ của hợp đồng"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy danh sách dịch vụ áp dụng cho khu vực
        from apps.dichvu.models import LichSuApDungDichVu, ChiSoDichVu
        
        dich_vu_khu_vuc = LichSuApDungDichVu.objects.filter(
            MA_KHU_VUC=hop_dong.MA_PHONG.MA_KHU_VUC,
            NGAY_HUY_DV__isnull=True
        ).select_related('MA_DICH_VU')
        
        danh_sach_dich_vu = []
        
        for dv_ap_dung in dich_vu_khu_vuc:
            dich_vu = dv_ap_dung.MA_DICH_VU
            
            # Lấy chỉ số hiện tại nếu có
            chi_so_hien_tai = ChiSoDichVu.objects.filter(
                MA_HOP_DONG=hop_dong,
                MA_DICH_VU=dich_vu
            ).order_by('-NGAY_GHI_CS').first()
            
            danh_sach_dich_vu.append({
                'ma_dich_vu': dich_vu.MA_DICH_VU,
                'ten_dich_vu': dich_vu.TEN_DICH_VU,
                'don_vi_tinh': dich_vu.DON_VI_TINH,
                'loai_dich_vu': dich_vu.LOAI_DICH_VU,
                'gia_dich_vu': float(dv_ap_dung.GIA_DICH_VU_AD or dich_vu.GIA_DICH_VU or 0),
                'chi_so_cu': chi_so_hien_tai.CHI_SO_MOI if chi_so_hien_tai else 0,
                'so_luong_cu': chi_so_hien_tai.SO_LUONG if chi_so_hien_tai else 0,
            })
        
        return JsonResponse({
            'success': True,
            'dich_vu_list': danh_sach_dich_vu
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi lấy dịch vụ: {str(e)}'
        })


@csrf_exempt  
@require_POST
def huy_bao_ket_thuc(request, ma_hop_dong):
    """Hủy báo kết thúc hợp đồng - trả về JSON response"""
    
    try:
        logger.info(f"Bắt đầu xử lý hủy báo kết thúc hợp đồng {ma_hop_dong}")
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Log thông tin hợp đồng hiện tại
        logger.info(f"Hợp đồng {ma_hop_dong}: Trạng thái={hop_dong.TRANG_THAI_HD}")
        
        # Lấy lý do từ form (optional)
        ly_do = request.POST.get('ly_do_huy', '').strip() or 'Hủy báo kết thúc theo yêu cầu'
        
        logger.info(f"Lý do hủy: '{ly_do}'")
        
        # Thực hiện hủy báo kết thúc trực tiếp
        logger.info(f"Gọi hop_dong.huy_bao_ket_thuc")
        success, lich_su_or_error = hop_dong.huy_bao_ket_thuc(ly_do=ly_do)
        
        logger.info(f"Kết quả hủy báo kết thúc: success={success}")
        
        if success:
            lich_su = lich_su_or_error
            logger.info(f"Hủy báo kết thúc thành công hợp đồng {ma_hop_dong} - Lịch sử ID: {lich_su.MA_DIEU_CHINH}")
            return JsonResponse({
                'success': True,
                'message': 'Đã hủy báo kết thúc hợp đồng. Hợp đồng tiếp tục hoạt động bình thường.',
                'data': {
                    'ma_dieu_chinh': lich_su.MA_DIEU_CHINH,
                    'ngay_huy': lich_su.NGAY_DC.strftime('%d/%m/%Y'),
                    'ly_do': ly_do,
                    'trang_thai_moi': hop_dong.TRANG_THAI_HD
                }
            })
        else:
            error_message = str(lich_su_or_error)
            logger.error(f"Hủy báo kết thúc thất bại hợp đồng {ma_hop_dong}: {error_message}")
            return JsonResponse({
                'success': False,
                'message': f'Lỗi hủy báo kết thúc: {error_message}'
            })
            
    except Exception as e:
        logger.error(f"Exception trong huy_bao_ket_thuc view: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        })