"""
API Views cho Workflow Quản lý Hợp đồng
Cung cấp REST API cho các chức năng quản lý hợp đồng
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json
import logging

from .models import HopDong
from .services import HopDongWorkflowService, HopDongScheduleService, HopDongReportService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class HopDongWorkflowAPI(View):
    """
    API xử lý workflow hợp đồng
    """
    
    def post(self, request, action):
        """
        Xử lý các action của workflow hợp đồng
        """
        try:
            data = json.loads(request.body)
            
            if action == 'lap_hop_dong_moi':
                return self._lap_hop_dong_moi(data)
            elif action == 'xac_nhan_hop_dong':
                return self._xac_nhan_hop_dong(data)
            elif action == 'sinh_hoa_don_hang_thang':
                return self._sinh_hoa_don_hang_thang(data)
            elif action == 'gia_han_hop_dong':
                return self._gia_han_hop_dong(data)
            elif action == 'bao_ket_thuc_som':
                return self._bao_ket_thuc_som(data)
            elif action == 'ket_thuc_hop_dong':
                return self._ket_thuc_hop_dong(data)
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Action không được hỗ trợ: {action}'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Dữ liệu JSON không hợp lệ'
            }, status=400)
        except Exception as e:
            logger.error(f'Lỗi API workflow {action}: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': f'Lỗi server: {str(e)}'
            }, status=500)
    
    def _lap_hop_dong_moi(self, data):
        """Lập hợp đồng mới"""
        hop_dong, success_msg, errors = HopDongWorkflowService.lap_hop_dong_moi(data)
        
        if hop_dong:
            return JsonResponse({
                'success': True,
                'message': success_msg,
                'data': {
                    'ma_hop_dong': hop_dong.MA_HOP_DONG,
                    'trang_thai': hop_dong.TRANG_THAI_HD,
                    'ma_phong': hop_dong.MA_PHONG.MA_PHONG,
                    'ten_phong': hop_dong.MA_PHONG.TEN_PHONG
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Không thể tạo hợp đồng',
                'errors': errors
            }, status=400)
    
    def _xac_nhan_hop_dong(self, data):
        """Xác nhận hợp đồng và sinh hóa đơn bắt đầu"""
        ma_hop_dong = data.get('ma_hop_dong')
        if not ma_hop_dong:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu mã hợp đồng'
            }, status=400)
        
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        hoa_don, success_msg, errors = HopDongWorkflowService.xac_nhan_va_kich_hoat_hop_dong(hop_dong)
        
        if hoa_don:
            return JsonResponse({
                'success': True,
                'message': success_msg,
                'data': {
                    'ma_hop_dong': hop_dong.MA_HOP_DONG,
                    'trang_thai_hd': hop_dong.TRANG_THAI_HD,
                    'ma_hoa_don': hoa_don.MA_HOA_DON,
                    'tong_tien': float(hoa_don.TONG_TIEN),
                    'ngay_lap': hoa_don.NGAY_LAP_HDON.isoformat()
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Không thể xác nhận hợp đồng',
                'errors': errors
            }, status=400)
    
    def _sinh_hoa_don_hang_thang(self, data):
        """Sinh hóa đơn hàng tháng batch"""
        thang = data.get('thang')
        nam = data.get('nam')
        
        danh_sach_hoa_don, success_msg, errors = HopDongWorkflowService.sinh_hoa_don_hang_thang_batch(
            thang=thang, 
            nam=nam
        )
        
        return JsonResponse({
            'success': len(danh_sach_hoa_don) > 0,
            'message': success_msg,
            'data': {
                'so_hoa_don_tao': len(danh_sach_hoa_don),
                'tong_tien': sum(float(hd.TONG_TIEN) for hd in danh_sach_hoa_don),
                'danh_sach_hoa_don': [
                    {
                        'ma_hoa_don': hd.MA_HOA_DON,
                        'ma_hop_dong': hd.MA_HOP_DONG.MA_HOP_DONG,
                        'ten_phong': hd.MA_PHONG.TEN_PHONG,
                        'tong_tien': float(hd.TONG_TIEN),
                        'ngay_lap': hd.NGAY_LAP_HDON.isoformat()
                    } for hd in danh_sach_hoa_don
                ]
            },
            'errors': errors
        })
    
    def _gia_han_hop_dong(self, data):
        """Gia hạn hợp đồng"""
        ma_hop_dong = data.get('ma_hop_dong')
        ngay_tra_phong_moi = data.get('ngay_tra_phong_moi')
        thoi_han_moi = data.get('thoi_han_moi')
        gia_thue_moi = data.get('gia_thue_moi')
        
        if not ma_hop_dong or not ngay_tra_phong_moi:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu mã hợp đồng hoặc ngày trả phòng mới'
            }, status=400)
        
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Convert string date to date object
        from datetime import datetime
        ngay_tra_phong_moi = datetime.strptime(ngay_tra_phong_moi, '%Y-%m-%d').date()
        
        success, message, errors = HopDongWorkflowService.gia_han_hop_dong(
            hop_dong=hop_dong,
            ngay_tra_phong_moi=ngay_tra_phong_moi,
            thoi_han_moi=thoi_han_moi,
            gia_thue_moi=gia_thue_moi
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message,
                'data': {
                    'ma_hop_dong': hop_dong.MA_HOP_DONG,
                    'ngay_tra_phong_moi': hop_dong.NGAY_TRA_PHONG.isoformat(),
                    'thoi_han_hd': hop_dong.THOI_HAN_HD,
                    'gia_thue': float(hop_dong.GIA_THUE or 0)
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Không thể gia hạn hợp đồng',
                'errors': errors
            }, status=400)
    
    def _bao_ket_thuc_som(self, data):
        """Báo kết thúc sớm hợp đồng"""
        ma_hop_dong = data.get('ma_hop_dong')
        ngay_bao_ket_thuc = data.get('ngay_bao_ket_thuc')
        ly_do = data.get('ly_do')
        
        if not ma_hop_dong or not ngay_bao_ket_thuc:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu mã hợp đồng hoặc ngày báo kết thúc'
            }, status=400)
        
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Convert string date to date object
        from datetime import datetime
        ngay_bao_ket_thuc = datetime.strptime(ngay_bao_ket_thuc, '%Y-%m-%d').date()
        
        success, message, errors = HopDongWorkflowService.bao_ket_thuc_som(
            hop_dong=hop_dong,
            ngay_bao_ket_thuc=ngay_bao_ket_thuc,
            ly_do=ly_do
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message,
                'data': {
                    'ma_hop_dong': hop_dong.MA_HOP_DONG,
                    'trang_thai': hop_dong.TRANG_THAI_HD,
                    'ghi_chu': hop_dong.GHI_CHU_HD
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Không thể báo kết thúc sớm',
                'errors': errors
            }, status=400)
    
    def _ket_thuc_hop_dong(self, data):
        """Kết thúc hợp đồng và sinh hóa đơn kết thúc"""
        ma_hop_dong = data.get('ma_hop_dong')
        ngay_ket_thuc = data.get('ngay_ket_thuc')
        
        if not ma_hop_dong:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu mã hợp đồng'
            }, status=400)
        
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Convert string date to date object if provided
        if ngay_ket_thuc:
            from datetime import datetime
            ngay_ket_thuc = datetime.strptime(ngay_ket_thuc, '%Y-%m-%d').date()
        
        hoa_don, message, errors = HopDongWorkflowService.ket_thuc_hop_dong(
            hop_dong=hop_dong,
            ngay_ket_thuc_thuc_te=ngay_ket_thuc
        )
        
        if message:
            return JsonResponse({
                'success': True,
                'message': message,
                'data': {
                    'ma_hop_dong': hop_dong.MA_HOP_DONG,
                    'trang_thai': hop_dong.TRANG_THAI_HD,
                    'trang_thai_phong': hop_dong.MA_PHONG.TRANG_THAI_P,
                    'ma_hoa_don_ket_thuc': hoa_don.MA_HOA_DON if hoa_don else None,
                    'tong_tien_ket_thuc': float(hoa_don.TONG_TIEN) if hoa_don else 0
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Không thể kết thúc hợp đồng',
                'errors': errors
            }, status=400)


@require_http_methods(["GET"])
def hop_dong_reports_api(request, report_type):
    """
    API báo cáo và thống kê hợp đồng
    """
    try:
        if report_type == 'thong_ke_trang_thai':
            data = HopDongReportService.thong_ke_hop_dong_theo_trang_thai()
        
        elif report_type == 'sap_het_han':
            so_ngay = int(request.GET.get('so_ngay', 30))
            hop_dong_list = HopDongReportService.danh_sach_hop_dong_sap_het_han(so_ngay)
            data = {
                'so_ngay': so_ngay,
                'so_luong': hop_dong_list.count(),
                'danh_sach': [
                    {
                        'ma_hop_dong': hd.MA_HOP_DONG,
                        'ten_phong': hd.MA_PHONG.TEN_PHONG,
                        'ten_khu_vuc': hd.MA_PHONG.MA_KHU_VUC.TEN_KHU_VUC,
                        'ngay_tra_phong': hd.NGAY_TRA_PHONG.isoformat(),
                        'trang_thai': hd.TRANG_THAI_HD,
                        'gia_thue': float(hd.GIA_THUE or 0)
                    } for hd in hop_dong_list
                ]
            }
        
        elif report_type == 'doanh_thu':
            thang = request.GET.get('thang')
            nam = request.GET.get('nam')
            if thang:
                thang = int(thang)
            if nam:
                nam = int(nam)
            data = HopDongReportService.bao_cao_doanh_thu_hop_dong(thang, nam)
        
        else:
            return JsonResponse({
                'success': False,
                'message': f'Loại báo cáo không được hỗ trợ: {report_type}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f'Lỗi API báo cáo {report_type}: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': f'Lỗi server: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt  
def hop_dong_schedule_api(request, action):
    """
    API xử lý các tác vụ tự động
    """
    try:
        if action == 'cap_nhat_trang_thai':
            results = HopDongScheduleService.cap_nhat_trang_thai_hop_dong_hang_ngay()
            return JsonResponse({
                'success': True,
                'message': 'Cập nhật trạng thái hợp đồng thành công',
                'data': results
            })
        
        elif action == 'sinh_hoa_don_tu_dong':
            data = json.loads(request.body) if request.body else {}
            ngay_sinh = data.get('ngay_sinh', 1)
            results = HopDongScheduleService.sinh_hoa_don_hang_thang_tu_dong(ngay_sinh)
            return JsonResponse({
                'success': True,
                'message': 'Sinh hóa đơn tự động thành công',
                'data': results
            })
        
        else:
            return JsonResponse({
                'success': False,
                'message': f'Action không được hỗ trợ: {action}'
            }, status=400)
        
    except Exception as e:
        logger.error(f'Lỗi API schedule {action}: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': f'Lỗi server: {str(e)}'
        }, status=500)