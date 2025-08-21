"""
Dedicated Workflow Service cho Hợp đồng
Tách riêng từ services.py để dễ quản lý
"""
from django.db import transaction
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging

from .models import HopDong, LichSuHopDong
from apps.hoadon.models import HoaDon
from apps.phongtro.models import PhongTro, CocPhong

logger = logging.getLogger(__name__)


class ContractWorkflowManager:
    """
    Manager chuyên xử lý workflow hợp đồng
    Đảm bảo tuân thủ đúng quy trình nghiệp vụ
    """
    
    @classmethod
    def execute_full_workflow(cls, contract_data, auto_confirm=False):
        """
        Thực thi toàn bộ workflow từ tạo hợp đồng đến kích hoạt
        
        Args:
            contract_data: Dict chứa thông tin hợp đồng
            auto_confirm: Bool - tự động xác nhận hợp đồng
            
        Returns:
            Dict với keys: hop_dong, hoa_don_bat_dau, success, errors
        """
        result = {
            'hop_dong': None,
            'hoa_don_bat_dau': None,
            'success': False,
            'errors': [],
            'workflow_steps': []
        }
        
        try:
            with transaction.atomic():
                # Bước 1: Tạo hợp đồng
                step_1 = cls._step_1_create_contract(contract_data)
                result['workflow_steps'].append(step_1)
                
                if not step_1['success']:
                    result['errors'].extend(step_1['errors'])
                    return result
                
                result['hop_dong'] = step_1['hop_dong']
                
                # Bước 2: Xác nhận tự động (nếu được yêu cầu)
                if auto_confirm:
                    step_2 = cls._step_2_confirm_contract(step_1['hop_dong'])
                    result['workflow_steps'].append(step_2)
                    
                    if step_2['success']:
                        result['hoa_don_bat_dau'] = step_2['hoa_don']
                    else:
                        result['errors'].extend(step_2['errors'])
                        return result
                
                result['success'] = True
                return result
                
        except Exception as e:
            error_msg = f"Lỗi workflow hợp đồng: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
    @classmethod  
    def _step_1_create_contract(cls, data):
        """Bước 1: Tạo hợp đồng"""
        try:
            hop_dong = HopDong.tao_hop_dong(data)
            
            # Cập nhật trạng thái phòng
            hop_dong.MA_PHONG.TRANG_THAI_P = 'Đã đặt cọc'
            hop_dong.MA_PHONG.save()
            
            return {
                'step': 1,
                'name': 'Tạo hợp đồng',
                'success': True,
                'hop_dong': hop_dong,
                'message': f"Tạo hợp đồng {hop_dong.MA_HOP_DONG} thành công",
                'errors': []
            }
            
        except Exception as e:
            return {
                'step': 1,
                'name': 'Tạo hợp đồng', 
                'success': False,
                'hop_dong': None,
                'message': None,
                'errors': [f"Lỗi tạo hợp đồng: {str(e)}"]
            }
    
    @classmethod
    def _step_2_confirm_contract(cls, hop_dong):
        """Bước 2: Xác nhận hợp đồng + Sinh hóa đơn bắt đầu"""
        try:
            hoa_don, error = hop_dong.xac_nhan_hop_dong()
            
            if hoa_don:
                return {
                    'step': 2,
                    'name': 'Xác nhận hợp đồng + Sinh hóa đơn bắt đầu',
                    'success': True,
                    'hoa_don': hoa_don,
                    'message': f"Xác nhận hợp đồng và sinh hóa đơn {hoa_don.MA_HOA_DON} thành công",
                    'errors': []
                }
            else:
                return {
                    'step': 2,
                    'name': 'Xác nhận hợp đồng + Sinh hóa đơn bắt đầu',
                    'success': False,
                    'hoa_don': None,
                    'message': None,
                    'errors': [error or "Lỗi không xác định"]
                }
                
        except Exception as e:
            return {
                'step': 2,
                'name': 'Xác nhận hợp đồng + Sinh hóa đơn bắt đầu',
                'success': False,
                'hoa_don': None,
                'message': None,
                'errors': [f"Lỗi xác nhận hợp đồng: {str(e)}"]
            }


class ContractLifecycleManager:
    """
    Manager quản lý vòng đời hợp đồng
    """
    
    @classmethod
    def check_contract_health(cls, hop_dong):
        """
        Kiểm tra sức khỏe hợp đồng
        Trả về các cảnh báo và khuyến nghị
        """
        warnings = []
        recommendations = []
        today = timezone.now().date()
        
        # Kiểm tra ngày hết hạn
        if hop_dong.NGAY_TRA_PHONG:
            days_left = (hop_dong.NGAY_TRA_PHONG - today).days
            
            if days_left <= 0:
                warnings.append("Hợp đồng đã hết hạn")
                recommendations.append("Cần kết thúc hợp đồng ngay lập tức")
            elif days_left <= 7:
                warnings.append(f"Hợp đồng sẽ hết hạn trong {days_left} ngày")
                recommendations.append("Cần liên hệ khách thuê để gia hạn hoặc kết thúc")
            elif days_left <= 30:
                warnings.append(f"Hợp đồng sẽ hết hạn trong {days_left} ngày")
                recommendations.append("Nên chuẩn bị thảo luận về gia hạn")
        
        # Kiểm tra thanh toán
        hoa_don_chua_thanh_toan = hop_dong.hoadon.filter(
            TRANG_THAI_HDON='Chưa thanh toán'
        ).count()
        
        if hoa_don_chua_thanh_toan > 0:
            warnings.append(f"Có {hoa_don_chua_thanh_toan} hóa đơn chưa thanh toán")
            recommendations.append("Cần nhắc nhở khách thuê thanh toán")
        
        # Kiểm tra trạng thái
        if hop_dong.TRANG_THAI_HD == 'Đang báo kết thúc':
            warnings.append("Hợp đồng đang trong trạng thái báo kết thúc")
            recommendations.append("Cần xử lý thủ tục kết thúc hợp đồng")
        
        return {
            'status': 'healthy' if not warnings else 'warning',
            'warnings': warnings,
            'recommendations': recommendations,
            'days_left': (hop_dong.NGAY_TRA_PHONG - today).days if hop_dong.NGAY_TRA_PHONG else None
        }
    
    @classmethod
    def prepare_contract_renewal(cls, hop_dong, extension_months=12):
        """
        Chuẩn bị dữ liệu cho việc gia hạn hợp đồng
        """
        from dateutil.relativedelta import relativedelta
        
        current_end_date = hop_dong.NGAY_TRA_PHONG
        if not current_end_date:
            return None, ["Hợp đồng không có ngày kết thúc"]
        
        new_end_date = current_end_date + relativedelta(months=extension_months)
        
        # Tính toán các thông tin gia hạn
        renewal_data = {
            'ma_hop_dong': hop_dong.MA_HOP_DONG,
            'ngay_tra_phong_cu': current_end_date,
            'ngay_tra_phong_moi': new_end_date,
            'thoi_han_gia_han': f"{extension_months} tháng",
            'gia_thue_hien_tai': hop_dong.GIA_THUE,
            'gia_thue_de_xuat': hop_dong.GIA_THUE,  # Có thể điều chỉnh
            'ly_do_gia_han': f"Gia hạn {extension_months} tháng theo yêu cầu"
        }
        
        return renewal_data, []
    
    @classmethod
    def calculate_early_termination_cost(cls, hop_dong, termination_date):
        """
        Tính toán chi phí khi kết thúc sớm hợp đồng
        """
        if not hop_dong.NGAY_TRA_PHONG:
            return None, ["Hợp đồng không có ngày kết thúc"]
        
        days_early = (hop_dong.NGAY_TRA_PHONG - termination_date).days
        
        if days_early <= 0:
            return {
                'penalty_fee': 0,
                'reason': 'Kết thúc đúng hạn hoặc muộn'
            }, []
        
        # Tính phí phạt (ví dụ: 1 tháng tiền phòng nếu kết thúc sớm > 30 ngày)
        monthly_rent = hop_dong.GIA_THUE or Decimal(0)
        
        if days_early > 30:
            penalty_fee = monthly_rent
        elif days_early > 15:
            penalty_fee = monthly_rent * Decimal(0.5)
        else:
            penalty_fee = Decimal(0)
        
        return {
            'days_early': days_early,
            'penalty_fee': penalty_fee,
            'monthly_rent': monthly_rent,
            'reason': f'Kết thúc sớm {days_early} ngày'
        }, []


class ContractValidationService:
    """
    Service validation cho hợp đồng
    """
    
    @classmethod
    def validate_contract_data(cls, data):
        """
        Validate dữ liệu hợp đồng trước khi tạo
        """
        errors = []
        warnings = []
        
        # Required fields
        required_fields = [
            'MA_PHONG', 'NGAY_LAP_HD', 'NGAY_NHAN_PHONG', 
            'NGAY_TRA_PHONG', 'GIA_THUE', 'MA_KHACH_THUE'
        ]
        
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Trường {field} là bắt buộc")
        
        # Date validations
        if data.get('NGAY_NHAN_PHONG') and data.get('NGAY_TRA_PHONG'):
            if data['NGAY_NHAN_PHONG'] >= data['NGAY_TRA_PHONG']:
                errors.append("Ngày nhận phòng phải trước ngày trả phòng")
        
        # Business logic validations
        if data.get('MA_PHONG'):
            try:
                phong = PhongTro.objects.get(MA_PHONG=data['MA_PHONG'])
                
                # Kiểm tra phòng đã có hợp đồng active
                active_contracts = HopDong.objects.filter(
                    MA_PHONG=phong,
                    TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc', 'Chờ xác nhận']
                )
                
                if active_contracts.exists():
                    errors.append(f"Phòng {phong.TEN_PHONG} đã có hợp đồng đang hoạt động")
                
                # Kiểm tra giá thuê
                if data.get('GIA_THUE'):
                    if data['GIA_THUE'] <= 0:
                        errors.append("Giá thuê phải lớn hơn 0")
                    elif phong.GIA_PHONG and abs(data['GIA_THUE'] - phong.GIA_PHONG) > phong.GIA_PHONG * 0.2:
                        warnings.append(f"Giá thuê chênh lệch > 20% so với giá phòng gốc ({phong.GIA_PHONG})")
                        
            except PhongTro.DoesNotExist:
                errors.append("Phòng không tồn tại")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }