from datetime import datetime, date
from django.db.models import Q, Sum
from django.utils import timezone
from apps.thanhvien.models import TaiKhoan
from apps.khachthue.models import KhachThue
from apps.hopdong.models import HopDong, LichSuHopDong
from apps.hoadon.models import HoaDon
from apps.phongtro.models import PhongTro


class PersonalDataService:
    """
    Service để truy vấn thông tin cá nhân của khách thuê
    """
    
    def __init__(self, user_session=None):
        """
        Khởi tạo với session của user hoặc user_id
        """
        self.user_session = user_session
        self.khach_thue = None
        self.tai_khoan = None
        
        if user_session and user_session.get('is_authenticated'):
            user_id = user_session.get('user_id')
            vai_tro = user_session.get('vai_tro')
            
            if user_id and vai_tro == 'Khách thuê':
                try:
                    self.tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
                    self.khach_thue = KhachThue.objects.get(MA_TAI_KHOAN=self.tai_khoan)
                except (TaiKhoan.DoesNotExist, KhachThue.DoesNotExist):
                    pass
    
    def is_authenticated(self):
        """Kiểm tra người dùng đã đăng nhập chưa"""
        return self.khach_thue is not None
    
    def get_user_info(self):
        """Lấy thông tin cơ bản của người dùng"""
        if not self.is_authenticated():
            return None
        
        return {
            'ho_ten': self.khach_thue.HO_TEN_KT,
            'email': self.khach_thue.EMAIL_KT,
            'sdt': self.khach_thue.SDT_KT,
            'dia_chi': self.khach_thue.DIA_CHI_KT,
            'cccd': self.khach_thue.CCCD_KT,
            'ngay_sinh': self.khach_thue.NGAY_SINH_KT,
            'username': self.tai_khoan.TAI_KHOAN,
        }
    
    def get_active_contracts(self):
        """Lấy danh sách hợp đồng đang hiệu lực"""
        if not self.is_authenticated():
            return []
        
        try:
            contracts = HopDong.objects.filter(
                MA_KHACH_THUE=self.khach_thue,
                TRANG_THAI_HD='Đang hiệu lực'
            ).select_related(
                'MA_PHONG',
                'MA_PHONG__MA_KHU_VUC',
                'MA_PHONG__MA_KHU_VUC__MA_NHA_TRO'
            )
            
            result = []
            for contract in contracts:
                result.append({
                    'ma_hop_dong': contract.MA_HOP_DONG,
                    'ten_phong': contract.MA_PHONG.TEN_PHONG if contract.MA_PHONG else 'N/A',
                    'khu_vuc': contract.MA_PHONG.MA_KHU_VUC.TEN_KHU_VUC if contract.MA_PHONG and contract.MA_PHONG.MA_KHU_VUC else 'N/A',
                    'nha_tro': contract.MA_PHONG.MA_KHU_VUC.MA_NHA_TRO.TEN_NHA_TRO if contract.MA_PHONG and contract.MA_PHONG.MA_KHU_VUC and contract.MA_PHONG.MA_KHU_VUC.MA_NHA_TRO else 'N/A',
                    'ngay_bat_dau': contract.NGAY_BAT_DAU_HD,
                    'ngay_ket_thuc': contract.NGAY_KET_THUC_HD,
                    'gia_thue': contract.GIA_THUE_HD,
                    'gia_dien': contract.GIA_DIEN,
                    'gia_nuoc': contract.GIA_NUOC,
                    'tien_coc': contract.TIEN_COC,
                    'trang_thai': contract.TRANG_THAI_HD,
                    'so_ngay_con_lai': self._calculate_days_remaining(contract.NGAY_KET_THUC_HD)
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting active contracts: {e}")
            return []
    
    def get_contract_expiry_info(self):
        """Lấy thông tin hết hạn hợp đồng"""
        contracts = self.get_active_contracts()
        
        if not contracts:
            return "Bạn hiện không có hợp đồng nào đang hiệu lực."
        
        expiry_info = []
        for contract in contracts:
            days_left = contract['so_ngay_con_lai']
            expiry_info.append({
                'phong': contract['ten_phong'],
                'ngay_het_han': contract['ngay_ket_thuc'],
                'so_ngay_con_lai': days_left,
                'trang_thai_canh_bao': 'Sắp hết hạn' if days_left <= 30 else 'Bình thường'
            })
        
        return expiry_info
    
    def get_unpaid_invoices(self):
        """Lấy danh sách hóa đơn chưa thanh toán"""
        if not self.is_authenticated():
            return []
        
        try:
            # Lấy các hợp đồng của khách thuê
            hop_dong_ids = HopDong.objects.filter(
                MA_KHACH_THUE=self.khach_thue
            ).values_list('MA_HOP_DONG', flat=True)
            
            if not hop_dong_ids:
                return []
            
            # Lấy hóa đơn chưa thanh toán
            unpaid_invoices = HoaDon.objects.filter(
                MA_HOP_DONG__in=hop_dong_ids,
                TRANG_THAI_HD='Chưa thanh toán'
            ).select_related(
                'MA_HOP_DONG',
                'MA_HOP_DONG__MA_PHONG'
            ).order_by('-THANG_HOA_DON', '-NAM_HOA_DON')
            
            result = []
            for invoice in unpaid_invoives:
                result.append({
                    'ma_hoa_don': invoice.MA_HOA_DON,
                    'thang': invoice.THANG_HOA_DON,
                    'nam': invoice.NAM_HOA_DON,
                    'ten_phong': invoice.MA_HOP_DONG.MA_PHONG.TEN_PHONG if invoice.MA_HOP_DONG and invoice.MA_HOP_DONG.MA_PHONG else 'N/A',
                    'tong_tien': invoice.TONG_TIEN_HD,
                    'han_thanh_toan': invoice.HAN_THANH_TOAN,
                    'trang_thai': invoice.TRANG_THAI_HD,
                    'qua_han': self._is_overdue(invoice.HAN_THANH_TOAN),
                    'so_ngay_qua_han': self._calculate_overdue_days(invoice.HAN_THANH_TOAN)
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting unpaid invoices: {e}")
            return []
    
    def get_payment_status_current_month(self):
        """Kiểm tra trạng thái thanh toán tháng hiện tại"""
        current_date = timezone.now()
        current_month = current_date.month
        current_year = current_date.year
        
        if not self.is_authenticated():
            return "Bạn cần đăng nhập để xem thông tin thanh toán."
        
        try:
            # Lấy các hợp đồng đang hiệu lực
            hop_dong_ids = HopDong.objects.filter(
                MA_KHACH_THUE=self.khach_thue,
                TRANG_THAI_HD='Đang hiệu lực'
            ).values_list('MA_HOP_DONG', flat=True)
            
            if not hop_dong_ids:
                return "Bạn hiện không có hợp đồng nào đang hiệu lực."
            
            # Kiểm tra hóa đơn tháng hiện tại
            current_month_invoices = HoaDon.objects.filter(
                MA_HOP_DONG__in=hop_dong_ids,
                THANG_HOA_DON=current_month,
                NAM_HOA_DON=current_year
            ).select_related('MA_HOP_DONG__MA_PHONG')
            
            if not current_month_invoices.exists():
                return f"Chưa có hóa đơn nào được tạo cho tháng {current_month}/{current_year}."
            
            payment_status = []
            for invoice in current_month_invoices:
                room_name = invoice.MA_HOP_DONG.MA_PHONG.TEN_PHONG if invoice.MA_HOP_DONG.MA_PHONG else 'N/A'
                status = "✅ Đã thanh toán" if invoice.TRANG_THAI_HD == 'Đã thanh toán' else "❌ Chưa thanh toán"
                
                payment_status.append({
                    'phong': room_name,
                    'trang_thai': status,
                    'so_tien': invoice.TONG_TIEN_HD,
                    'han_thanh_toan': invoice.HAN_THANH_TOAN
                })
            
            return payment_status
            
        except Exception as e:
            print(f"Error getting current month payment status: {e}")
            return "Có lỗi xảy ra khi kiểm tra thông tin thanh toán."
    
    def get_recent_payments(self, limit=5):
        """Lấy lịch sử thanh toán gần đây"""
        if not self.is_authenticated():
            return []
        
        try:
            hop_dong_ids = HopDong.objects.filter(
                MA_KHACH_THUE=self.khach_thue
            ).values_list('MA_HOP_DONG', flat=True)
            
            if not hop_dong_ids:
                return []
            
            paid_invoices = HoaDon.objects.filter(
                MA_HOP_DONG__in=hop_dong_ids,
                TRANG_THAI_HD='Đã thanh toán'
            ).select_related(
                'MA_HOP_DONG__MA_PHONG'
            ).order_by('-NAM_HOA_DON', '-THANG_HOA_DON')[:limit]
            
            result = []
            for invoice in paid_invoices:
                result.append({
                    'ma_hoa_don': invoice.MA_HOA_DON,
                    'thang': invoice.THANG_HOA_DON,
                    'nam': invoice.NAM_HOA_DON,
                    'ten_phong': invoice.MA_HOP_DONG.MA_PHONG.TEN_PHONG if invoice.MA_HOP_DONG.MA_PHONG else 'N/A',
                    'so_tien': invoice.TONG_TIEN_HD,
                    'ngay_thanh_toan': invoice.NGAY_THANH_TOAN
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting recent payments: {e}")
            return []
    
    def _calculate_days_remaining(self, end_date):
        """Tính số ngày còn lại đến hết hạn"""
        if not end_date:
            return None
        
        today = date.today()
        if isinstance(end_date, str):
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except:
                return None
        
        if end_date < today:
            return 0  # Đã hết hạn
        
        return (end_date - today).days
    
    def _is_overdue(self, due_date):
        """Kiểm tra có quá hạn không"""
        if not due_date:
            return False
        
        today = date.today()
        if isinstance(due_date, str):
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except:
                return False
        
        return due_date < today
    
    def _calculate_overdue_days(self, due_date):
        """Tính số ngày quá hạn"""
        if not self._is_overdue(due_date):
            return 0
        
        today = date.today()
        if isinstance(due_date, str):
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except:
                return 0
        
        return (today - due_date).days
    
    def search_contracts_by_keyword(self, keyword):
        """Tìm kiếm hợp đồng theo từ khóa"""
        if not self.is_authenticated():
            return []
        
        contracts = self.get_active_contracts()
        return [
            contract for contract in contracts
            if keyword.lower() in contract['ten_phong'].lower() or
               keyword.lower() in contract['khu_vuc'].lower() or
               keyword.lower() in contract['nha_tro'].lower()
        ]