"""
Service layer cho workflow quản lý hợp đồng
Cung cấp các API thống nhất cho toàn bộ quy trình nghiệp vụ
"""
from django.db import transaction
from django.utils import timezone
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import logging

from .models import HopDong, LichSuHopDong
from apps.phongtro.models import PhongTro, CocPhong
from apps.khachthue.models import KhachThue

# Import từ workflow service
from .workflow_service import (
    ContractWorkflowManager,
    ContractLifecycleManager, 
    ContractValidationService
)

logger = logging.getLogger(__name__)


class HopDongWorkflowService:
    """
    Service quản lý toàn bộ workflow hợp đồng
    """
    
    @classmethod
    def lap_hop_dong_moi(cls, data):
        """
        Bước 1: Lập hợp đồng mới
        Input: data chứa thông tin hợp đồng, khách thuê, phòng
        Output: (hop_dong, success_message, errors)
        """
        try:
            with transaction.atomic():
                # 1. Tạo hợp đồng
                hop_dong = HopDong.tao_hop_dong(data)
                
                # 2. Cập nhật trạng thái phòng thành "Đã đặt cọc"
                hop_dong.MA_PHONG.TRANG_THAI_P = 'Đã đặt cọc'
                hop_dong.MA_PHONG.save()
                
                success_msg = f"Tạo hợp đồng thành công cho phòng {hop_dong.MA_PHONG.TEN_PHONG}"
                logger.info(f"Tạo hợp đồng {hop_dong.MA_HOP_DONG} thành công")
                
                return hop_dong, success_msg, []
                
        except Exception as e:
            error_msg = f"Lỗi tạo hợp đồng: {str(e)}"
            logger.error(error_msg)
            return None, None, [error_msg]
    
    @classmethod
    def xac_nhan_va_kich_hoat_hop_dong(cls, hop_dong):
        """
        Bước 2: Xác nhận và kích hoạt hợp đồng + Sinh hóa đơn bắt đầu
        Input: hop_dong object
        Output: (hoa_don_bat_dau, success_message, errors)
        """
        try:
            # Gọi method có sẵn trong model
            hoa_don, error = hop_dong.xac_nhan_hop_dong()
            
            if hoa_don:
                success_msg = f"Xác nhận hợp đồng và sinh hóa đơn bắt đầu thành công. HĐ: {hoa_don.MA_HOA_DON}"
                logger.info(f"Xác nhận hợp đồng {hop_dong.MA_HOP_DONG} thành công")
                return hoa_don, success_msg, []
            else:
                # Không có hóa đơn nhưng vẫn coi là xác nhận hợp đồng thành công
                success_msg = f"Xác nhận hợp đồng {hop_dong.MA_HOP_DONG} thành công (chưa sinh hóa đơn bắt đầu)."
                logger.info(success_msg)
                return None, success_msg, []
                
        except Exception as e:
            error_msg = f"Lỗi xác nhận hợp đồng: {str(e)}"
            logger.error(error_msg)
            return None, None, [error_msg]
    
    @classmethod
    def sinh_hoa_don_hang_thang_batch(cls, thang=None, nam=None):
        """
        Bước 3: Sinh hóa đơn hàng tháng cho tất cả hợp đồng đang hoạt động
        Input: thang, nam (mặc định là tháng hiện tại)
        Output: (danh_sach_hoa_don, success_count, errors)
        """
        if not thang or not nam:
            today = timezone.now().date()
            thang = thang or today.month
            nam = nam or today.year
        
        try:
            # Lấy tất cả hợp đồng đang hoạt động
            hop_dong_active = HopDong.objects.filter(
                TRANG_THAI_HD='Đang hoạt động'
            )
            
            danh_sach_hoa_don = []
            errors = []
            
            for hop_dong in hop_dong_active:
                try:
                    # Lazy import để tránh circular import
                    from django.apps import apps
                    HoaDon = apps.get_model('hoadon', 'HoaDon')
                    # Sinh hóa đơn hàng tháng
                    hoa_don, error = HoaDon.sinh_hoa_don_hang_thang(hop_dong, thang, nam)
                    
                    if hoa_don:
                        danh_sach_hoa_don.append(hoa_don)
                        logger.info(f"Sinh hóa đơn tháng {thang}/{nam} cho hợp đồng {hop_dong.MA_HOP_DONG}")
                    else:
                        errors.append(f"HĐ {hop_dong.MA_HOP_DONG}: {error}")
                        
                except Exception as e:
                    errors.append(f"HĐ {hop_dong.MA_HOP_DONG}: {str(e)}")
            
            success_count = len(danh_sach_hoa_don)
            success_msg = f"Sinh thành công {success_count} hóa đơn tháng {thang}/{nam}"
            
            return danh_sach_hoa_don, success_msg, errors
            
        except Exception as e:
            error_msg = f"Lỗi sinh hóa đơn batch: {str(e)}"
            logger.error(error_msg)
            return [], None, [error_msg]
    
    @classmethod
    def gia_han_hop_dong(cls, hop_dong, ngay_tra_phong_moi, thoi_han_moi=None, gia_thue_moi=None):
        """
        Bước 4: Gia hạn hợp đồng
        Input: hop_dong, ngay_tra_phong_moi, thoi_han_moi (optional), gia_thue_moi (optional)
        Output: (success, message, errors)
        """
        try:
            success, error = hop_dong.gia_han_hop_dong(
                ngay_tra_phong_moi=ngay_tra_phong_moi,
                thoi_han_moi=thoi_han_moi,
                gia_thue_moi=gia_thue_moi
            )
            
            if success:
                success_msg = f"Gia hạn hợp đồng {hop_dong.MA_HOP_DONG} đến {ngay_tra_phong_moi}"
                logger.info(success_msg)
                return True, success_msg, []
            else:
                return False, None, [error]
                
        except Exception as e:
            error_msg = f"Lỗi gia hạn hợp đồng: {str(e)}"
            logger.error(error_msg)
            return False, None, [error_msg]
    
    @classmethod
    def bao_ket_thuc_som(cls, hop_dong, ngay_bao_ket_thuc, ly_do=None):
        """
        Bước 5: Báo kết thúc sớm hợp đồng
        Input: hop_dong, ngay_bao_ket_thuc, ly_do (optional)
        Output: (success, message, errors)
        """
        try:
            success, error = hop_dong.bao_ket_thuc_som(
                ngay_bao_ket_thuc=ngay_bao_ket_thuc,
                ly_do=ly_do
            )
            
            if success:
                success_msg = f"Báo kết thúc sớm hợp đồng {hop_dong.MA_HOP_DONG} vào {ngay_bao_ket_thuc}"
                logger.info(success_msg)
                return True, success_msg, []
            else:
                return False, None, [error]
                
        except Exception as e:
            error_msg = f"Lỗi báo kết thúc sớm: {str(e)}"
            logger.error(error_msg)
            return False, None, [error_msg]
    
    @classmethod
    def ket_thuc_hop_dong(cls, hop_dong, ngay_ket_thuc_thuc_te=None):
        """
        Bước 6 & 7: Kết thúc hợp đồng + Sinh hóa đơn kết thúc
        Input: hop_dong, ngay_ket_thuc_thuc_te (optional)
        Output: (hoa_don_ket_thuc, success_message, errors)
        """
        try:
            # Gọi method có sẵn trong model
            hoa_don, error = hop_dong.ket_thuc_hop_dong(ngay_ket_thuc_thuc_te)
            
            if hoa_don or error is None:
                success_msg = f"Kết thúc hợp đồng {hop_dong.MA_HOP_DONG} thành công"
                if hoa_don:
                    success_msg += f". Sinh hóa đơn kết thúc: {hoa_don.MA_HOA_DON}"
                
                logger.info(success_msg)
                return hoa_don, success_msg, []
            else:
                return None, None, [error]
                
        except Exception as e:
            error_msg = f"Lỗi kết thúc hợp đồng: {str(e)}"
            logger.error(error_msg)
            return None, None, [error_msg]


class HopDongScheduleService:
    """
    Service xử lý các tác vụ tự động theo lịch
    """
    
    @classmethod
    def cap_nhat_trang_thai_hop_dong_hang_ngay(cls):
        """
        Chạy hàng ngày để cập nhật trạng thái hợp đồng
        - Đánh dấu hợp đồng "Sắp kết thúc" (30 ngày trước hết hạn)
        - Tự động kết thúc hợp đồng đã hết hạn
        """
        today = timezone.now().date()
        sap_ket_thuc_date = today + timedelta(days=30)
        
        results = {
            'sap_ket_thuc': 0,
            'da_het_han': 0,
            'errors': []
        }
        
        try:
            # 1. Cập nhật hợp đồng sắp kết thúc
            hop_dong_sap_ket_thuc = HopDong.objects.filter(
                TRANG_THAI_HD='Đang hoạt động',
                NGAY_TRA_PHONG__lte=sap_ket_thuc_date,
                NGAY_TRA_PHONG__gt=today
            )
            
            count = hop_dong_sap_ket_thuc.update(TRANG_THAI_HD='Sắp kết thúc')
            results['sap_ket_thuc'] = count
            
            # 2. Tự động kết thúc hợp đồng hết hạn
            hop_dong_het_han = HopDong.objects.filter(
                TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc'],
                NGAY_TRA_PHONG__lt=today
            )
            
            for hop_dong in hop_dong_het_han:
                try:
                    HopDongWorkflowService.ket_thuc_hop_dong(hop_dong, today)
                    results['da_het_han'] += 1
                except Exception as e:
                    results['errors'].append(f"HĐ {hop_dong.MA_HOP_DONG}: {str(e)}")
            
            logger.info(f"Cập nhật trạng thái hợp đồng: {results}")
            return results
            
        except Exception as e:
            error_msg = f"Lỗi cập nhật trạng thái hợp đồng: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
    
    @classmethod
    def sinh_hoa_don_hang_thang_tu_dong(cls, ngay_sinh=1):
        """
        Tự động sinh hóa đơn hàng tháng vào ngày cố định
        Input: ngay_sinh (mặc định ngày 1 hàng tháng)
        """
        today = timezone.now().date()
        
        # Chỉ chạy vào ngày được chỉ định
        if today.day != ngay_sinh:
            return {'message': f'Chưa đến ngày sinh hóa đơn (ngày {ngay_sinh})'}
        
        # Sinh hóa đơn cho tháng hiện tại
        danh_sach_hoa_don, success_msg, errors = HopDongWorkflowService.sinh_hoa_don_hang_thang_batch(
            thang=today.month,
            nam=today.year
        )
        
        result = {
            'ngay_thuc_hien': today,
            'so_hoa_don': len(danh_sach_hoa_don),
            'message': success_msg,
            'errors': errors
        }
        
        logger.info(f"Sinh hóa đơn tự động: {result}")
        return result


class HopDongReportService:
    """
    Service báo cáo và thống kê hợp đồng
    """
    
    @classmethod
    def thong_ke_hop_dong_theo_trang_thai(cls):
        """
        Thống kê số lượng hợp đồng theo trạng thái
        """
        from django.db.models import Count
        
        stats = HopDong.objects.values('TRANG_THAI_HD').annotate(
            so_luong=Count('MA_HOP_DONG')
        ).order_by('TRANG_THAI_HD')
        
        return {
            'thong_ke': list(stats),
            'tong_so': sum(item['so_luong'] for item in stats)
        }
    
    @classmethod
    def danh_sach_hop_dong_sap_het_han(cls, so_ngay=30):
        """
        Lấy danh sách hợp đồng sắp hết hạn trong N ngày tới
        Chỉ thống kê dựa trên MA_HOP_DONG, không dùng thông tin MA_PHONG
        """
        ngay_gioi_han = timezone.now().date() + timedelta(days=so_ngay)
        
        hop_dong_sap_het_han = HopDong.objects.filter(
            TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc'],
            NGAY_TRA_PHONG__lte=ngay_gioi_han
        ).order_by('NGAY_TRA_PHONG')
        
        return hop_dong_sap_het_han
    
    @classmethod
    def bao_cao_doanh_thu_hop_dong(cls, thang=None, nam=None):
        """
        Báo cáo doanh thu từ hợp đồng theo tháng
        """
        if not thang or not nam:
            today = timezone.now().date()
            thang = thang or today.month
            nam = nam or today.year
        
        # Lấy tất cả hóa đơn trong tháng
        from django.db.models import Sum
        from django.apps import apps
        HoaDon = apps.get_model('hoadon', 'HoaDon')
        
        hoa_don_thang = HoaDon.objects.filter(
            NGAY_LAP_HDON__year=nam,
            NGAY_LAP_HDON__month=thang,
            MA_HOP_DONG__isnull=False
        )
        
        tong_doanh_thu = hoa_don_thang.aggregate(
            tong_tien=Sum('TONG_TIEN')
        )['tong_tien'] or Decimal(0)
        
        return {
            'thang': thang,
            'nam': nam,
            'so_hoa_don': hoa_don_thang.count(),
            'tong_doanh_thu': tong_doanh_thu,
            'chi_tiet_theo_loai': hoa_don_thang.values('LOAI_HOA_DON').annotate(
                so_luong=Count('MA_HOA_DON'),
                tong_tien=Sum('TONG_TIEN')
            )
        }
    
    @classmethod
    def thong_ke_chi_tiet_dashboard(cls):
        """
        Thống kê chi tiết cho dashboard - hoàn toàn dựa trên MA_HOP_DONG
        Không sử dụng MA_PHONG để thống kê
        """
        from django.db.models import Count
        
        # Đếm hợp đồng theo trạng thái dựa trên MA_HOP_DONG
        tong_hop_dong = HopDong.objects.count()
        dang_hoat_dong = HopDong.objects.filter(TRANG_THAI_HD='Đang hoạt động').count()
        cho_xac_nhan = HopDong.objects.filter(
            TRANG_THAI_HD__in=['Chờ xác nhận', 'Đã xác nhận']
        ).count()
        da_ket_thuc = HopDong.objects.filter(TRANG_THAI_HD='Đã kết thúc').count()
        huy_bo = HopDong.objects.filter(TRANG_THAI_HD='Đã hủy').count()
        
        return {
            'tong_hop_dong': tong_hop_dong,
            'dang_hoat_dong': dang_hoat_dong,
            'cho_xac_nhan': cho_xac_nhan,
            'da_ket_thuc': da_ket_thuc,
            'huy_bo': huy_bo,
            # Thống kê bổ sung theo MA_HOP_DONG
            'ty_le_hoat_dong': round((dang_hoat_dong / tong_hop_dong * 100) if tong_hop_dong > 0 else 0, 2)
        }