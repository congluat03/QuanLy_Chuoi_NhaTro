"""
Views cho Frontend User (không phải admin)
Xử lý các request từ giao diện người dùng cuối
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
import json

from .models import HopDong, LichSuHopDong
from .services import HopDongReportService
from apps.khachthue.models import KhachThue
from apps.hoadon.models import HoaDon


@login_required
def hop_dong_user_list(request):
    """
    Danh sách hợp đồng của user hiện tại
    """
    try:
        # Lấy khách thuê từ user hiện tại
        khach_thue = KhachThue.objects.get(MA_TAI_KHOAN=request.user)
        
        # Lấy danh sách hợp đồng của khách thuê
        hop_dongs = HopDong.objects.filter(
            lichsuhopdong__MA_KHACH_THUE=khach_thue,
            lichsuhopdong__NGAY_ROI_DI__isnull=True  # Chỉ lấy hợp đồng đang tham gia
        ).select_related('MA_PHONG', 'MA_PHONG__MA_KHU_VUC').distinct()
        
        context = {
            'hop_dongs': hop_dongs,
            'khach_thue': khach_thue
        }
        
        return render(request, 'user/hopdong/danh_sach_hop_dong.html', context)
        
    except KhachThue.DoesNotExist:
        return render(request, 'user/hopdong/khong_co_hop_dong.html')


@login_required
def hop_dong_user_detail(request, ma_hop_dong):
    """
    Chi tiết hợp đồng của user
    """
    try:
        khach_thue = KhachThue.objects.get(MA_TAI_KHOAN=request.user)
        
        # Kiểm tra user có quyền xem hợp đồng này không
        hop_dong = get_object_or_404(
            HopDong,
            MA_HOP_DONG=ma_hop_dong,
            lichsuhopdong__MA_KHACH_THUE=khach_thue
        )
        
        # Lấy lịch sử hợp đồng
        lich_su = LichSuHopDong.objects.filter(
            MA_HOP_DONG=hop_dong
        ).select_related('MA_KHACH_THUE').order_by('NGAY_THAM_GIA')
        
        # Lấy hóa đơn liên quan
        hoa_dons = hop_dong.hoadon.all().order_by('-NGAY_LAP_HDON')
        
        context = {
            'hop_dong': hop_dong,
            'lich_su': lich_su,
            'hoa_dons': hoa_dons,
            'khach_thue': khach_thue
        }
        
        return render(request, 'user/hopdong/chi_tiet_hop_dong.html', context)
        
    except KhachThue.DoesNotExist:
        return render(request, 'user/errors/khong_co_quyen.html')


@require_http_methods(["GET"])
@login_required
def hop_dong_user_api(request, action):
    """
    API cho user xem thông tin hợp đồng
    """
    try:
        khach_thue = KhachThue.objects.get(MA_TAI_KHOAN=request.user)
        
        if action == 'thong_tin_hop_dong':
            ma_hop_dong = request.GET.get('ma_hop_dong')
            if not ma_hop_dong:
                return JsonResponse({
                    'success': False,
                    'message': 'Thiếu mã hợp đồng'
                }, status=400)
            
            hop_dong = get_object_or_404(
                HopDong,
                MA_HOP_DONG=ma_hop_dong,
                lichsuhopdong__MA_KHACH_THUE=khach_thue
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'ma_hop_dong': hop_dong.MA_HOP_DONG,
                    'ten_phong': hop_dong.MA_PHONG.TEN_PHONG,
                    'gia_thue': float(hop_dong.GIA_THUE or 0),
                    'ngay_nhan_phong': hop_dong.NGAY_NHAN_PHONG.isoformat() if hop_dong.NGAY_NHAN_PHONG else None,
                    'ngay_tra_phong': hop_dong.NGAY_TRA_PHONG.isoformat() if hop_dong.NGAY_TRA_PHONG else None,
                    'trang_thai': hop_dong.TRANG_THAI_HD,
                    'thoi_han': hop_dong.THOI_HAN_HD
                }
            })
        
        else:
            return JsonResponse({
                'success': False,
                'message': f'Action không được hỗ trợ: {action}'
            }, status=400)
            
    except KhachThue.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Không tìm thấy thông tin khách thuê'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi server: {str(e)}'
        }, status=500)


def xac_nhan_hop_dong_khach_hang(request, ma_hop_dong):
    """
    Trang cho khách hàng xác nhận hợp đồng
    """
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        if request.method == 'POST':
            # Xử lý xác nhận hợp đồng
            hoa_don, error = hop_dong.khach_hang_xac_nhan_hop_dong()
            
            if hoa_don:
                messages.success(request, 'Xác nhận hợp đồng thành công! Hóa đơn bắt đầu đã được tạo.')
                return redirect('user_hopdong:xac_nhan_thanh_cong', ma_hop_dong=ma_hop_dong)
            else:
                messages.error(request, f'Lỗi xác nhận hợp đồng: {error}')
        
        context = {
            'hop_dong': hop_dong,
            'hoa_don_bat_dau': hop_dong.get_hoa_don_bat_dau(),
            'da_xac_nhan': hop_dong.KHACH_DA_XAC_NHAN,
        }
        
        return render(request, 'user/hopdong/xac_nhan_hop_dong.html', context)
        
    except Exception as e:
        messages.error(request, f'Lỗi: {str(e)}')
        return render(request, 'user/hopdong/loi.html')


def xac_nhan_thanh_cong(request, ma_hop_dong):
    """
    Trang thông báo xác nhận thành công
    """
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        hoa_don_bat_dau = hop_dong.get_hoa_don_bat_dau()
        
        context = {
            'hop_dong': hop_dong,
            'hoa_don_bat_dau': hoa_don_bat_dau,
        }
        
        return render(request, 'user/hopdong/xac_nhan_thanh_cong.html', context)
        
    except Exception as e:
        messages.error(request, f'Lỗi: {str(e)}')
        return render(request, 'user/hopdong/loi.html')


def xem_hoa_don(request, ma_hoa_don):
    """
    Xem chi tiết hóa đơn
    """
    try:
        hoa_don = get_object_or_404(HoaDon, MA_HOA_DON=ma_hoa_don)
        
        context = {
            'hoa_don': hoa_don,
            'hop_dong': hoa_don.MA_HOP_DONG,
        }
        
        return render(request, 'user/hopdong/chi_tiet_hoa_don.html', context)
        
    except Exception as e:
        messages.error(request, f'Lỗi: {str(e)}')
        return render(request, 'user/hopdong/loi.html')


def xuat_hoa_don_pdf(request, ma_hoa_don):
    """
    Xuất hóa đơn ra PDF
    """
    try:
        hoa_don = get_object_or_404(HoaDon, MA_HOA_DON=ma_hoa_don)
        
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Tiêu đề
        title = Paragraph(f"HÓA ĐƠN {hoa_don.LOAI_HOA_DON.upper()}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Thông tin hóa đơn
        data = [
            ['Mã hóa đơn:', hoa_don.MA_HOA_DON],
            ['Ngày lập:', hoa_don.NGAY_LAP_HDON.strftime('%d/%m/%Y') if hoa_don.NGAY_LAP_HDON else ''],
            ['Phòng:', hoa_don.MA_PHONG.TEN_PHONG if hoa_don.MA_PHONG else ''],
            ['Tiền phòng:', f"{hoa_don.TIEN_PHONG:,.0f} VNĐ" if hoa_don.TIEN_PHONG else '0 VNĐ'],
            ['Tiền dịch vụ:', f"{hoa_don.TIEN_DICH_VU:,.0f} VNĐ" if hoa_don.TIEN_DICH_VU else '0 VNĐ'],
            ['Tiền cọc:', f"{hoa_don.TIEN_COC:,.0f} VNĐ" if hoa_don.TIEN_COC else '0 VNĐ'],
            ['Tổng tiền:', f"{hoa_don.TONG_TIEN:,.0f} VNĐ" if hoa_don.TONG_TIEN else '0 VNĐ'],
            ['Trạng thái:', hoa_don.TRANG_THAI_HDON or ''],
        ]
        
        table = Table(data)
        story.append(table)
        
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="hoa_don_{ma_hoa_don}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Lỗi xuất PDF: {str(e)}')
        return redirect('user_hopdong:xem_hoa_don', ma_hoa_don=ma_hoa_don)


def thong_tin_hop_dong(request, ma_hop_dong):
    """
    Xem thông tin chi tiết hợp đồng
    """
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy danh sách hóa đơn của hợp đồng
        hoa_dons = HoaDon.objects.filter(MA_HOP_DONG=hop_dong).order_by('-NGAY_LAP_HDON')
        
        context = {
            'hop_dong': hop_dong,
            'hoa_dons': hoa_dons,
            'hoa_don_bat_dau': hop_dong.get_hoa_don_bat_dau(),
            'hoa_don_ket_thuc': hop_dong.get_hoa_don_ket_thuc(),
        }
        
        return render(request, 'user/hopdong/thong_tin_hop_dong.html', context)
        
    except Exception as e:
        messages.error(request, f'Lỗi: {str(e)}')
        return render(request, 'user/hopdong/loi.html')
