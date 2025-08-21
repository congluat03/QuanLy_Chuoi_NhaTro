from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from .models import HopDong, LichSuHopDong
from apps.phongtro.models import PhongTro, CocPhong
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from apps.khachthue.models import CccdCmnd, KhachThue
from apps.phongtro.models import TAISANBANGIAO
from apps.dichvu.models import ChiSoDichVu, LichSuApDungDichVu
from django.db import transaction
from django.utils import timezone
from datetime import date, datetime, timedelta
import json

# Import workflow services
from .services import HopDongWorkflowService, HopDongReportService
from .workflow_service import ContractLifecycleManager

class ContractWrapper:
    """Wrapper class để tránh circular references trong comparison"""
    def __init__(self, contract):
        self.original = contract
        # Copy essential attributes
        self.MA_HOP_DONG = contract.MA_HOP_DONG
        self.TRANG_THAI_HD = contract.TRANG_THAI_HD
        self.MA_PHONG = contract.MA_PHONG
        self.GIA_THUE = contract.GIA_THUE
        self.NGAY_NHAN_PHONG = contract.NGAY_NHAN_PHONG
        self.NGAY_TRA_PHONG = contract.NGAY_TRA_PHONG
        self.NGAY_LAP_HD = contract.NGAY_LAP_HD
        self.NGAY_THU_TIEN = contract.NGAY_THU_TIEN
        self.SO_THANH_VIEN = contract.SO_THANH_VIEN
        self.lichsuhopdong = contract.lichsuhopdong
        
        # Kiểm tra thực tế có hóa đơn bắt đầu không
        try:
            self._hoa_don_bat_dau = contract.get_hoa_don_bat_dau()
            self.co_hoa_don_bat_dau = self._hoa_don_bat_dau is not None
        except:
            self.co_hoa_don_bat_dau = False
            self._hoa_don_bat_dau = None
    
    def __getattr__(self, name):
        """Fallback to original contract for any missing attributes"""
        return getattr(self.original, name)
    
    def __str__(self):
        return f"ContractWrapper({self.MA_HOP_DONG})"
    
    def __repr__(self):
        return self.__str__()
    
    def __lt__(self, other):
        """Simple comparison by MA_HOP_DONG to avoid recursion"""
        if hasattr(other, 'MA_HOP_DONG'):
            return self.MA_HOP_DONG < other.MA_HOP_DONG
        return NotImplemented
    
    def __eq__(self, other):
        """Simple equality by MA_HOP_DONG"""
        if hasattr(other, 'MA_HOP_DONG'):
            return self.MA_HOP_DONG == other.MA_HOP_DONG
        return False
    
    def __le__(self, other):
        """Less than or equal"""
        if hasattr(other, 'MA_HOP_DONG'):
            return self.MA_HOP_DONG <= other.MA_HOP_DONG
        return NotImplemented
    
    def __gt__(self, other):
        """Greater than"""
        if hasattr(other, 'MA_HOP_DONG'):
            return self.MA_HOP_DONG > other.MA_HOP_DONG
        return NotImplemented
    
    def __ge__(self, other):
        """Greater than or equal"""
        if hasattr(other, 'MA_HOP_DONG'):
            return self.MA_HOP_DONG >= other.MA_HOP_DONG
        return NotImplemented
    
    def __ne__(self, other):
        """Not equal"""
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result
    
    def __hash__(self):
        """Hash for set/dict usage"""
        return hash(self.MA_HOP_DONG)


def safe_health_check(contract):
    """Simplified health check để tránh circular references"""
    warnings = []
    recommendations = []
    from django.utils import timezone
    today = timezone.now().date()
    
    # Chỉ kiểm tra ngày hết hạn (không query related objects)
    if contract.NGAY_TRA_PHONG:
        days_left = (contract.NGAY_TRA_PHONG - today).days
        
        if days_left <= 0:
            warnings.append("Hợp đồng đã hết hạn")
            recommendations.append("Cần kết thúc hợp đồng ngay lập tức")
        elif days_left <= 7:
            warnings.append(f"Hợp đồng sẽ hết hạn trong {days_left} ngày")
            recommendations.append("Cần liên hệ khách thuê để gia hạn hoặc kết thúc")
        elif days_left <= 30:
            warnings.append(f"Hợp đồng sẽ hết hạn trong {days_left} ngày")
            recommendations.append("Nên chuẩn bị thảo luận về gia hạn")
    
    # Kiểm tra trạng thái
    if contract.TRANG_THAI_HD == 'Đang báo kết thúc':
        warnings.append("Hợp đồng đang trong trạng thái báo kết thúc")
        recommendations.append("Cần xử lý thủ tục kết thúc hợp đồng")
    
    return {
        'status': 'healthy' if not warnings else 'warning',
        'warnings': warnings,
        'recommendations': recommendations,
        'days_left': (contract.NGAY_TRA_PHONG - today).days if contract.NGAY_TRA_PHONG else None
    }


def hopdong_list(request):
    # Check user authentication and permissions
    if not request.session.get('is_authenticated'):
        return redirect('auth:login')
    
    vai_tro = request.session.get('vai_tro')
    if vai_tro not in ['Chủ trọ', 'admin']:
        messages.error(request, 'Bạn không có quyền truy cập chức năng này.')
        return redirect('index:trang_chu')
    
    # Enhanced status mapping for contract status display
    status_map = {
        'Chờ xác nhận': {'text': 'Chờ xác nhận', 'color': 'bg-blue-600'},
        'Đang hoạt động': {'text': 'Đang hoạt động', 'color': 'bg-green-600'},
        'Sắp kết thúc': {'text': 'Sắp kết thúc', 'color': 'bg-yellow-500'},
        'Đang báo kết thúc': {'text': 'Đang báo kết thúc', 'color': 'bg-orange-500'},
        'Đã kết thúc': {'text': 'Đã kết thúc', 'color': 'bg-red-600'},
    }

    # Fetch contracts with related room and filter for representative tenant
    hop_dongs = HopDong.objects.select_related('MA_PHONG').prefetch_related(
        'lichsuhopdong__MA_KHACH_THUE'
    ).order_by('MA_HOP_DONG')
    
    # Enhanced contract processing with workflow status - Fix comparison recursion
    enhanced_contracts = []
    for contract in hop_dongs:
        # Create wrapper to avoid circular references in comparison
        wrapper = ContractWrapper(contract)
        
        # Add status display (safe approach)
        status_info = status_map.get(contract.TRANG_THAI_HD, {'text': 'Không xác định', 'color': 'bg-gray-600'})
        wrapper.status_display_text = status_info['text']
        wrapper.status_display_color = status_info['color']
        
        # Add workflow health check (safe approach - simplified to avoid recursion)
        wrapper.health_check = safe_health_check(contract)
        
        # Add available workflow actions (safe approach)
        try:
            wrapper.available_actions = get_available_workflow_actions(contract)
        except Exception as e:
            wrapper.available_actions = []
        
        enhanced_contracts.append(wrapper)

    # Sort contracts by MA_HOP_DONG để tránh comparison issues
    enhanced_contracts.sort(key=lambda x: x.MA_HOP_DONG)
    
    # Pagination with customizable page size
    page_size = request.GET.get('page_size', 10)
    try:
        page_size = int(page_size)
        if page_size not in [5, 10, 25, 50, 100]:
            page_size = 10
    except (ValueError, TypeError):
        page_size = 10
    
    paginator = Paginator(enhanced_contracts, page_size)
    page_number = request.GET.get('page')
    hop_dongs_page = paginator.get_page(page_number)

    # Fetch all rooms
    phong_tros = PhongTro.objects.order_by('MA_PHONG')
    
    # Get dashboard statistics
    stats = HopDongReportService.thong_ke_hop_dong_theo_trang_thai()
    contracts_expiring = HopDongReportService.danh_sach_hop_dong_sap_het_han(30)

    return render(request, 'admin/hopdong/danhsach_hopdong.html', {
        'hop_dongs': hop_dongs_page,
        'phong_tros': phong_tros,
        'stats': stats,
        'contracts_expiring_count': contracts_expiring.count(),
        'current_page_size': page_size,
        'total_contracts': paginator.count,
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


@require_POST
def xac_nhan_hop_dong(request, ma_hop_dong):
    """Xác nhận hợp đồng và sinh hóa đơn bắt đầu nếu chưa có"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Kiểm tra xem đã có hóa đơn bắt đầu chưa
        da_co_hoa_don = hop_dong.get_hoa_don_bat_dau() is not None
        
        hoa_don, error = hop_dong.xac_nhan_hop_dong()
        
        if hoa_don and error is None:
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
            messages.error(request, f'Lỗi: {error}')
        else:
            messages.success(request, 'Đã xác nhận hợp đồng!')
            
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
    
    return redirect('hopdong:hopdong_list')

def sinh_lai_hoa_don_bat_dau(request, ma_hop_dong):
    """Sinh lại hóa đơn bắt đầu (nếu cần)"""
    if request.method == 'POST':
        try:
            hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
            
            # Xóa hóa đơn cũ (nếu có)
            hoa_don_cu = hop_dong.get_hoa_don_bat_dau()
            if hoa_don_cu and hoa_don_cu.TRANG_THAI_HDON == 'Chưa thanh toán':
                hoa_don_cu.delete()
                hop_dong.DA_SINH_HOA_DON_BAT_DAU = False
                hop_dong.save()
            
            # Sinh hóa đơn mới
            from django.apps import apps
            HoaDon = apps.get_model('hoadon', 'HoaDon')
            hoa_don, error = HoaDon.sinh_hoa_don_bat_dau_hop_dong(hop_dong)
            
            if hoa_don:
                messages.success(request, f'Đã sinh lại hóa đơn bắt đầu! Mã: {hoa_don.MA_HOA_DON}')
            else:
                messages.error(request, f'Lỗi sinh hóa đơn: {error}')
                
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
    
    return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)

def chi_tiet_hop_dong(request, ma_hop_dong):
    """Chi tiết hợp đồng với thông tin hóa đơn"""
    hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
    
    # Lấy thông tin liên quan
    khach_thue = hop_dong.lichsuhopdong.filter(MOI_QUAN_HE='Chủ hợp đồng').first()
    hoa_don_bat_dau = hop_dong.get_hoa_don_bat_dau()
    
    # Lấy danh sách hóa đơn
    danh_sach_hoa_don = hop_dong.hoadon.all().order_by('-NGAY_LAP_HDON')
    
    # Lấy lịch sử gia hạn
    lich_su_gia_han = hop_dong.get_lich_su_gia_han()
    
    context = {
        'hop_dong': hop_dong,
        'khach_thue': khach_thue,  # Trả về cả object lich su hop dong
        'hoa_don_bat_dau': hoa_don_bat_dau,
        'danh_sach_hoa_don': danh_sach_hoa_don,
        'lich_su_gia_han': lich_su_gia_han,
        'so_lan_gia_han': hop_dong.da_gia_han_bao_nhieu_lan(),
        'can_sinh_hoa_don_bat_dau': not hop_dong.get_hoa_don_bat_dau(),
    }
    
    return render(request, 'admin/hopdong/chi_tiet_hop_dong.html', context)

@require_POST
def gia_han_hop_dong(request, ma_hop_dong):
    """Gia hạn hợp đồng"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy dữ liệu từ form
        ngay_tra_phong_moi_str = request.POST.get('ngay_tra_phong_moi')
        thoi_han_moi = request.POST.get('thoi_han_moi')
        gia_thue_moi = request.POST.get('gia_thue_moi')
        ly_do = request.POST.get('ly_do_gia_han')
        
        # Validate và convert ngày
        from datetime import datetime
        try:
            ngay_tra_phong_moi = datetime.strptime(ngay_tra_phong_moi_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, 'Ngày trả phòng mới không hợp lệ')
            return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)
        
        # Convert giá thuê mới (nếu có)
        if gia_thue_moi:
            try:
                gia_thue_moi = float(gia_thue_moi)
            except (ValueError, TypeError):
                messages.error(request, 'Giá thuê mới không hợp lệ')
                return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)
        else:
            gia_thue_moi = None
        
        # Thực hiện gia hạn
        success, lich_su_or_error = hop_dong.gia_han_hop_dong(
            ngay_tra_phong_moi=ngay_tra_phong_moi,
            thoi_han_moi=thoi_han_moi,
            gia_thue_moi=gia_thue_moi,
            ly_do=ly_do
        )
        
        if success:
            lich_su = lich_su_or_error
            messages.success(request, f'Đã gia hạn hợp đồng đến {ngay_tra_phong_moi}! Mã gia hạn: {lich_su.MA_GIA_HAN}')
        else:
            messages.error(request, f'Lỗi gia hạn: {lich_su_or_error}')
            
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
    
    return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)

@require_POST
def bao_ket_thuc_som(request, ma_hop_dong):
    """Báo kết thúc sớm hợp đồng"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy dữ liệu từ form
        ngay_bao_ket_thuc_str = request.POST.get('ngay_bao_ket_thuc')
        ly_do = request.POST.get('ly_do')
        
        # Validate và convert ngày
        from datetime import datetime
        try:
            ngay_bao_ket_thuc = datetime.strptime(ngay_bao_ket_thuc_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, 'Ngày báo kết thúc không hợp lệ')
            return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)
        
        # Thực hiện báo kết thúc
        success, error = hop_dong.bao_ket_thuc_som(
            ngay_bao_ket_thuc=ngay_bao_ket_thuc,
            ly_do=ly_do
        )
        
        if success:
            messages.success(request, f'Đã báo kết thúc hợp đồng vào {ngay_bao_ket_thuc}!')
        else:
            messages.error(request, f'Lỗi báo kết thúc: {error}')
            
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
    
    return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)

@require_POST
def ket_thuc_hop_dong(request, ma_hop_dong):
    """Kết thúc hợp đồng và sinh hóa đơn cuối"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy ngày kết thúc thực tế (nếu có)
        ngay_ket_thuc_str = request.POST.get('ngay_ket_thuc_thuc_te')
        ngay_ket_thuc = None
        
        if ngay_ket_thuc_str:
            from datetime import datetime
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
    
    return redirect('hopdong:hopdong_list')


# ======================= WORKFLOW FUNCTIONS =======================

def get_available_workflow_actions(contract):
    """Xác định các action workflow có thể thực hiện với hợp đồng"""
    actions = []
    
    if contract.TRANG_THAI_HD == 'Chờ xác nhận':
        actions.extend([
            {'action': 'confirm', 'label': 'Xác nhận & Sinh HĐ', 'icon': 'fas fa-check-circle', 'class': 'btn-success'},
            {'action': 'edit', 'label': 'Chỉnh sửa', 'icon': 'fas fa-edit', 'class': 'btn-warning'},
            {'action': 'cancel', 'label': 'Hủy', 'icon': 'fas fa-times', 'class': 'btn-danger'}
        ])
    
    elif contract.TRANG_THAI_HD == 'Đang hoạt động':
        actions.extend([
            {'action': 'invoice', 'label': 'Lập hóa đơn tháng', 'icon': 'fas fa-receipt', 'class': 'btn-primary'},
            {'action': 'extend', 'label': 'Gia hạn', 'icon': 'fas fa-calendar-plus', 'class': 'btn-info'},
            {'action': 'early_end', 'label': 'Báo kết thúc sớm', 'icon': 'fas fa-exclamation-triangle', 'class': 'btn-warning'},
            {'action': 'view_detail', 'label': 'Chi tiết', 'icon': 'fas fa-eye', 'class': 'btn-secondary'}
        ])
    
    elif contract.TRANG_THAI_HD in ['Sắp kết thúc', 'Đang báo kết thúc']:
        actions.extend([
            {'action': 'extend', 'label': 'Gia hạn', 'icon': 'fas fa-calendar-plus', 'class': 'btn-info'},
            {'action': 'end', 'label': 'Kết thúc', 'icon': 'fas fa-stop-circle', 'class': 'btn-danger'},
            {'action': 'view_detail', 'label': 'Chi tiết', 'icon': 'fas fa-eye', 'class': 'btn-secondary'}
        ])
    
    else:  # Đã kết thúc
        actions.extend([
            {'action': 'view_detail', 'label': 'Chi tiết', 'icon': 'fas fa-eye', 'class': 'btn-secondary'},
            {'action': 'archive', 'label': 'Lưu trữ', 'icon': 'fas fa-archive', 'class': 'btn-outline'}
        ])
    
    return actions

@csrf_exempt
@require_POST
def workflow_action(request):
    """Xử lý các action workflow từ AJAX"""
    # Check authentication and permissions
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập để thực hiện thao tác này'})
    
    vai_tro = request.session.get('vai_tro')
    if vai_tro not in ['Chủ trọ', 'admin']:
        return JsonResponse({'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này'})
        
    try:
        data = json.loads(request.body)
        action = data.get('action')
        ma_hop_dong = data.get('ma_hop_dong') or data.get('contract_id')
        
        if not action or not ma_hop_dong:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu thông tin action hoặc mã hợp đồng'
            })
        
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Xử lý từng action
        if action == 'confirm':
            return handle_confirm_contract(hop_dong, data)
        elif action == 'invoice':
            return handle_create_invoice(hop_dong, data)
        elif action == 'extend':
            return handle_extend_contract(hop_dong, data)
        elif action == 'early_end':
            return handle_early_end_contract(hop_dong, data)
        elif action == 'end':
            return handle_end_contract(hop_dong, data)
        elif action == 'cancel':
            return handle_cancel_contract(hop_dong, data)
        else:
            return JsonResponse({
                'success': False,
                'message': f'Action không được hỗ trợ: {action}'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Dữ liệu JSON không hợp lệ'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        })

def handle_confirm_contract(hop_dong, data):
    """Xử lý xác nhận hợp đồng"""
    try:
        hoa_don, success_msg, errors = HopDongWorkflowService.xac_nhan_va_kich_hoat_hop_dong(hop_dong)
        
        if hoa_don:
            # Lấy thông tin khách thuê
            lich_su = hop_dong.lichsuhopdong.filter(MOI_QUAN_HE='Chủ hợp đồng').first()
            khach_thue = lich_su.MA_KHACH_THUE if lich_su else None
            
            # Chuẩn bị dữ liệu hóa đơn chi tiết để hiển thị
            hoa_don_data = {
                'ma_hoa_don': hoa_don.MA_HOA_DON,
                'ngay_lap': hoa_don.NGAY_LAP_HDON.strftime('%d/%m/%Y') if hoa_don.NGAY_LAP_HDON else '',
                'loai_hoa_don': hoa_don.LOAI_HOA_DON,
                'trang_thai': hoa_don.TRANG_THAI_HDON,
                
                # Thông tin hợp đồng
                'ma_hop_dong': hop_dong.MA_HOP_DONG,
                'ten_phong': hop_dong.MA_PHONG.TEN_PHONG,
                'ngay_nhan_phong': hop_dong.NGAY_NHAN_PHONG.strftime('%d/%m/%Y') if hop_dong.NGAY_NHAN_PHONG else '',
                'ngay_tra_phong': hop_dong.NGAY_TRA_PHONG.strftime('%d/%m/%Y') if hop_dong.NGAY_TRA_PHONG else '',
                
                # Thông tin khách thuê
                'ten_khach_thue': khach_thue.HO_TEN_KT if khach_thue else '',
                'sdt_khach_thue': khach_thue.SDT_KT if khach_thue else '',
                'ngay_sinh': khach_thue.NGAY_SINH_KT.strftime('%d/%m/%Y') if khach_thue and khach_thue.NGAY_SINH_KT else '',
                
                # Chi tiết thanh toán
                'tien_phong': f"{float(hoa_don.TIEN_PHONG or 0):,.0f}",
                'tien_dich_vu': f"{float(hoa_don.TIEN_DICH_VU or 0):,.0f}",
                'tien_coc': f"{float(hoa_don.TIEN_COC or 0):,.0f}",
                'tien_khau_tru': f"{float(hoa_don.TIEN_KHAU_TRU or 0):,.0f}",
                'tong_tien': f"{float(hoa_don.TONG_TIEN or 0):,.0f}",
                
                # Thông tin bổ sung
                'han_thanh_toan': (hoa_don.NGAY_LAP_HDON + timedelta(days=7)).strftime('%d/%m/%Y') if hoa_don.NGAY_LAP_HDON else '',
                'ngay_tao': timezone.now().strftime('%d/%m/%Y %H:%M')
            }
            
            return JsonResponse({
                'success': True,
                'message': success_msg,
                'show_invoice': True,  # Flag để hiển thị modal hóa đơn
                'invoice_data': hoa_don_data,
                'data': {
                    'ma_hoa_don': hoa_don.MA_HOA_DON,
                    'tong_tien': float(hoa_don.TONG_TIEN),
                    'trang_thai_hop_dong': hop_dong.TRANG_THAI_HD
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'message': success_msg,
                'show_invoice': False,
                'data': {
                    'trang_thai_hop_dong': hop_dong.TRANG_THAI_HD
                }
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi xác nhận hợp đồng: {str(e)}'
        })

def handle_create_invoice(hop_dong, data):
    """Xử lý tạo hóa đơn hàng tháng"""
    try:
        thang = data.get('thang') or datetime.now().month
        nam = data.get('nam') or datetime.now().year
        
        from django.apps import apps
        HoaDon = apps.get_model('hoadon', 'HoaDon')
        hoa_don, error = HoaDon.sinh_hoa_don_hang_thang(hop_dong, thang, nam)
        
        if hoa_don:
            return JsonResponse({
                'success': True,
                'message': f'Đã sinh hóa đơn tháng {thang}/{nam}',
                'data': {
                    'ma_hoa_don': hoa_don.MA_HOA_DON,
                    'tong_tien': float(hoa_don.TONG_TIEN),
                    'ngay_lap': hoa_don.NGAY_LAP_HDON.isoformat()
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': error or 'Không thể sinh hóa đơn'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi sinh hóa đơn: {str(e)}'
        })

def handle_extend_contract(hop_dong, data):
    """Xử lý gia hạn hợp đồng"""
    try:
        ngay_tra_phong_moi_str = data.get('ngay_tra_phong_moi')
        thoi_han_moi = data.get('thoi_han_moi')
        gia_thue_moi = data.get('gia_thue_moi')
        
        if not ngay_tra_phong_moi_str:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu ngày trả phòng mới'
            })
        
        # Convert string to date
        ngay_tra_phong_moi = datetime.strptime(ngay_tra_phong_moi_str, '%Y-%m-%d').date()
        
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
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi gia hạn hợp đồng: {str(e)}'
        })

def handle_early_end_contract(hop_dong, data):
    """Xử lý báo kết thúc sớm"""
    try:
        ngay_bao_ket_thuc_str = data.get('ngay_bao_ket_thuc')
        ly_do = data.get('ly_do', '')
        
        if not ngay_bao_ket_thuc_str:
            return JsonResponse({
                'success': False,
                'message': 'Thiếu ngày báo kết thúc'
            })
        
        # Convert string to date
        ngay_bao_ket_thuc = datetime.strptime(ngay_bao_ket_thuc_str, '%Y-%m-%d').date()
        
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
                    'trang_thai': hop_dong.TRANG_THAI_HD,
                    'ghi_chu': hop_dong.GHI_CHU_HD
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Không thể báo kết thúc sớm',
                'errors': errors
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi báo kết thúc sớm: {str(e)}'
        })

def handle_end_contract(hop_dong, data):
    """Xử lý kết thúc hợp đồng"""
    try:
        ngay_ket_thuc_str = data.get('ngay_ket_thuc')
        ngay_ket_thuc = None
        
        if ngay_ket_thuc_str:
            ngay_ket_thuc = datetime.strptime(ngay_ket_thuc_str, '%Y-%m-%d').date()
        
        hoa_don, message, errors = HopDongWorkflowService.ket_thuc_hop_dong(
            hop_dong=hop_dong,
            ngay_ket_thuc_thuc_te=ngay_ket_thuc
        )
        
        if message:
            return JsonResponse({
                'success': True,
                'message': message,
                'data': {
                    'trang_thai': hop_dong.TRANG_THAI_HD,
                    'trang_thai_phong': hop_dong.MA_PHONG.TRANG_THAI_P,
                    'ma_hoa_don_ket_thuc': hoa_don.MA_HOA_DON if hoa_don else None
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Không thể kết thúc hợp đồng',
                'errors': errors
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi kết thúc hợp đồng: {str(e)}'
        })

def handle_cancel_contract(hop_dong, data):
    """Xử lý hủy hợp đồng"""
    try:
        ly_do = data.get('ly_do', 'Hủy bởi admin')
        
        # Logic hủy hợp đồng
        hop_dong.TRANG_THAI_HD = 'Đã hủy'
        hop_dong.GHI_CHU_HD = f"{hop_dong.GHI_CHU_HD or ''}\n[Hủy {date.today()}]: {ly_do}"
        hop_dong.save()
        
        # Cập nhật trạng thái phòng về trống
        hop_dong.MA_PHONG.TRANG_THAI_P = 'Trống'
        hop_dong.MA_PHONG.save()
        
        # Cập nhật trạng thái cọc phòng
        CocPhong.cap_nhat_trang_thai_coc(hop_dong.MA_PHONG, 'Đã thu hồi')
        
        return JsonResponse({
            'success': True,
            'message': 'Đã hủy hợp đồng',
            'data': {
                'trang_thai': hop_dong.TRANG_THAI_HD
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi hủy hợp đồng: {str(e)}'
        })

@require_http_methods(['GET'])
def dashboard_statistics(request):
    """API để lấy thống kê dashboard"""
    # Check authentication and permissions
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập để xem thống kê'})
    
    vai_tro = request.session.get('vai_tro')
    if vai_tro not in ['Chủ trọ', 'admin']:
        return JsonResponse({'success': False, 'message': 'Bạn không có quyền xem thống kê'})
        
    try:
        # Thống kê cơ bản
        stats = HopDongReportService.thong_ke_hop_dong_theo_trang_thai()
        
        # Hợp đồng sắp hết hạn
        contracts_expiring = HopDongReportService.danh_sach_hop_dong_sap_het_han(30)
        
        # Doanh thu tháng hiện tại
        current_month = datetime.now()
        revenue = HopDongReportService.bao_cao_doanh_thu_hop_dong(
            current_month.month, 
            current_month.year
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'contract_stats': stats,
                'contracts_expiring': {
                    'count': contracts_expiring.count(),
                    'list': [
                        {
                            'ma_hop_dong': hd.MA_HOP_DONG,
                            'ten_phong': hd.MA_PHONG.TEN_PHONG,
                            'ngay_het_han': hd.NGAY_TRA_PHONG.isoformat(),
                            'days_left': (hd.NGAY_TRA_PHONG - date.today()).days
                        } for hd in contracts_expiring[:5]  # Top 5
                    ]
                },
                'revenue': revenue
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi lấy thống kê: {str(e)}'
        })

@require_POST
def sinh_hoa_don_hang_thang(request, ma_hop_dong):
    """Sinh hóa đơn hàng tháng"""
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy tháng và năm từ form
        thang = int(request.POST.get('thang'))
        nam = int(request.POST.get('nam'))
        
        # Validate tháng và năm
        if not (1 <= thang <= 12):
            messages.error(request, 'Tháng không hợp lệ (1-12)')
            return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)
        
        if not (2020 <= nam <= 2030):  # Có thể điều chỉnh phạm vi năm
            messages.error(request, 'Năm không hợp lệ')
            return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)
        
        # Sinh hóa đơn hàng tháng
        from django.apps import apps
        HoaDon = apps.get_model('hoadon', 'HoaDon')
        hoa_don, error = HoaDon.sinh_hoa_don_hang_thang(hop_dong, thang, nam)
        
        if hoa_don:
            messages.success(
                request, 
                f'Đã sinh hóa đơn tháng {thang}/{nam}! Mã hóa đơn: {hoa_don.MA_HOA_DON}'
            )
        else:
            messages.error(request, f'Lỗi sinh hóa đơn: {error}')
            
    except ValueError as e:
        messages.error(request, f'Dữ liệu không hợp lệ: {str(e)}')
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
    
    return redirect('hopdong:chi_tiet_hop_dong', ma_hop_dong=ma_hop_dong)









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


@require_http_methods(['GET'])
def export_invoice_pdf(request, ma_hoa_don):
    """
    Xuất hóa đơn ra file PDF
    """
    try:
        from django.apps import apps
        HoaDon = apps.get_model('hoadon', 'HoaDon')
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        import io
        
        # Lấy hóa đơn
        hoa_don = get_object_or_404(HoaDon, MA_HOA_DON=ma_hoa_don)
        
        # Lấy thông tin hợp đồng và khách thuê
        hop_dong = hoa_don.MA_HOP_DONG
        if hop_dong:
            lich_su = hop_dong.lichsuhopdong.filter(MOI_QUAN_HE='Chủ hợp đồng').first()
            khach_thue = lich_su.MA_KHACH_THUE if lich_su else None
        else:
            khach_thue = None
        
        # Chuẩn bị context cho template
        context = {
            'hoa_don': hoa_don,
            'hop_dong': hop_dong,
            'khach_thue': khach_thue,
            'company_name': 'CÔNG TY CHO THUÊ PHÒNG TRỌ',
            'company_address': 'Địa chỉ công ty',
            'company_phone': 'Số điện thoại công ty',
        }
        
        # Render HTML template
        html_content = render_to_string('admin/hopdong/invoice_pdf_template.html', context)
        
        # Kiểm tra xem có thư viện tạo PDF không
        try:
            from weasyprint import HTML
            
            # Tạo PDF bằng WeasyPrint
            pdf_file = HTML(string=html_content).write_pdf()
            
            # Trả về response PDF
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="hoadon_{ma_hoa_don}.pdf"'
            return response
            
        except ImportError:
            # Fallback: trả về HTML để browser print
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'inline; filename="hoadon_{ma_hoa_don}.html"'
            return response
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi xuất PDF: {str(e)}'
        }, status=500)

@require_http_methods(['POST'])
def send_invoice_email(request, ma_hoa_don):
    """
    Gửi hóa đơn qua email cho khách thuê
    """
    try:
        from django.apps import apps
        HoaDon = apps.get_model('hoadon', 'HoaDon')
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string
        from django.conf import settings
        import json
        
        # Parse request data
        data = json.loads(request.body) if request.body else {}
        recipient_email = data.get('email')
        
        # Lấy hóa đơn
        hoa_don = get_object_or_404(HoaDon, MA_HOA_DON=ma_hoa_don)
        
        # Lấy thông tin hợp đồng và khách thuê
        hop_dong = hoa_don.MA_HOP_DONG
        if hop_dong:
            lich_su = hop_dong.lichsuhopdong.filter(MOI_QUAN_HE='Chủ hợp đồng').first()
            khach_thue = lich_su.MA_KHACH_THUE if lich_su else None
        else:
            khach_thue = None
        
        # Lấy email từ thông tin khách thuê nếu không có trong request
        if not recipient_email and khach_thue:
            # Giả sử có trường email trong model KhachThue
            recipient_email = getattr(khach_thue, 'EMAIL_KT', None)
        
        if not recipient_email:
            return JsonResponse({
                'success': False,
                'message': 'Không tìm thấy email của khách thuê'
            })
        
        # Chuẩn bị nội dung email
        subject = f'Hóa đơn #{ma_hoa_don} - {hoa_don.LOAI_HOA_DON}'
        
        context = {
            'hoa_don': hoa_don,
            'hop_dong': hop_dong,
            'khach_thue': khach_thue,
            'company_name': 'CÔNG TY CHO THUÊ PHÒNG TRỌ',
        }
        
        # Render email template
        html_message = render_to_string('admin/hopdong/invoice_email_template.html', context)
        text_message = f"""
        Kính gửi {khach_thue.HO_TEN_KT if khach_thue else 'Quý khách'},

        Chúng tôi gửi đến Quý khách hóa đơn #{ma_hoa_don} với các thông tin sau:
        - Loại hóa đơn: {hoa_don.LOAI_HOA_DON}
        - Ngày lập: {hoa_don.NGAY_LAP_HDON.strftime('%d/%m/%Y') if hoa_don.NGAY_LAP_HDON else ''}
        - Tổng tiền: {hoa_don.TONG_TIEN:,.0f} VNĐ
        - Trạng thái: {hoa_don.TRANG_THAI_HDON}

        Vui lòng thanh toán đúng hạn theo quy định.

        Trân trọng,
        CÔNG TY CHO THUÊ PHÒNG TRỌ
        """
        
        # Tạo và gửi email
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            to=[recipient_email],
        )
        
        # Attach HTML version
        email.attach_alternative(html_message, "text/html")
        
        # Gửi email
        email.send(fail_silently=False)
        
        return JsonResponse({
            'success': True,
            'message': f'Đã gửi hóa đơn qua email: {recipient_email}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi gửi email: {str(e)}'
        }, status=500)


@require_http_methods(['GET', 'POST'])
def thiet_lap_hoa_don_bat_dau_hop_dong(request, ma_hop_dong):
    """
    Thiết lập và tạo hóa đơn bắt đầu cho hợp đồng chờ xác nhận
    """
    from decimal import Decimal
    from django.apps import apps
    
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Kiểm tra trạng thái hợp đồng
        if hop_dong.TRANG_THAI_HD != 'Chờ xác nhận':
            return JsonResponse({
                'success': False,
                'message': 'Chỉ có thể tạo hóa đơn bắt đầu cho hợp đồng đang chờ xác nhận'
            })
        
        # Kiểm tra đã có hóa đơn bắt đầu chưa
        if hop_dong.get_hoa_don_bat_dau():
            return JsonResponse({
                'success': False,
                'message': 'Hợp đồng này đã có hóa đơn bắt đầu'
            })
        
        if request.method == 'GET':
            # Lấy thông tin khách thuê
            lich_su = hop_dong.lichsuhopdong.filter(MOI_QUAN_HE='Chủ hợp đồng').first()
            khach_thue = lich_su.MA_KHACH_THUE if lich_su else None
            
            # Tạo preview đơn giản
            tien_phong = hop_dong.GIA_THUE or Decimal(0)
            tien_coc = hop_dong.GIA_COC_HD or Decimal(0)
            tien_dich_vu = Decimal(0)  # Sẽ tính dựa vào dịch vụ phòng

            tong_tien = tien_phong + tien_coc + tien_dich_vu
            
            # Tạo dữ liệu đơn giản cho preview
            hoa_don_preview = {
                'tien_phong': tien_phong,
                'tien_coc': tien_coc, 
                'tien_dich_vu': tien_dich_vu,
                'tien_khau_tru': Decimal(0),
                'tong_tien': tong_tien
            }
            
            return JsonResponse({
                'success': True,
                'html': render(request, 'admin/hopdong/modal_tao_hoa_don_bat_dau.html', {
                    'hop_dong': hop_dong,
                    'khach_thue': khach_thue,
                    'hoa_don_preview': hoa_don_preview
                }).content.decode('utf-8')
            })
        
        elif request.method == 'POST':
            # Tạo hóa đơn bắt đầu trực tiếp
            HoaDon = apps.get_model('hoadon', 'HoaDon')
            
            try:
                with transaction.atomic():
                    # Tính toán các khoản phí
                    tien_phong = hop_dong.GIA_THUE or Decimal(0)
                    tien_coc = hop_dong.GIA_COC_HD or Decimal(0)
                    tien_dich_vu = Decimal(0)  # Có thể tính từ dịch vụ sau
                    tien_khau_tru = Decimal(0)
                    
                    tong_tien = tien_phong + tien_coc + tien_dich_vu - tien_khau_tru
                    # Tạo hóa đơn
                    hoa_don = HoaDon.objects.create(
                        MA_HOP_DONG=hop_dong,
                        LOAI_HOA_DON='Hóa đơn bắt đầu',
                        NGAY_LAP_HDON=timezone.now().date(),
                        TIEN_PHONG=tien_phong,
                        TIEN_DICH_VU=tien_dich_vu,
                        TIEN_COC=tien_coc,
                        TIEN_KHAU_TRU=tien_khau_tru,
                        TONG_TIEN=tong_tien,
                        TRANG_THAI_HDON='Chưa thanh toán'
                    )
                    
                    # Lấy thông tin khách thuê để trả về
                    lich_su = hop_dong.lichsuhopdong.filter(MOI_QUAN_HE='Chủ hợp đồng').first()
                    khach_thue = lich_su.MA_KHACH_THUE if lich_su else None
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Đã tạo hóa đơn bắt đầu thành công! Mã hóa đơn: {hoa_don.MA_HOA_DON}',
                        'show_invoice': True,
                        'invoice_data': {
                            'ma_hoa_don': hoa_don.MA_HOA_DON,
                            'ngay_lap': hoa_don.NGAY_LAP_HDON.strftime('%d/%m/%Y'),
                            'loai_hoa_don': hoa_don.LOAI_HOA_DON,
                            'trang_thai': hoa_don.TRANG_THAI_HDON,
                            'ma_hop_dong': hop_dong.MA_HOP_DONG,
                            'ten_phong': hop_dong.MA_PHONG.TEN_PHONG,
                            'ten_khach_thue': khach_thue.HO_TEN_KT if khach_thue else '',
                            'tien_phong': f"{float(tien_phong):,.0f}",
                            'tien_dich_vu': f"{float(tien_dich_vu):,.0f}",
                            'tien_coc': f"{float(tien_coc):,.0f}",
                            'tien_khau_tru': f"{float(tien_khau_tru):,.0f}",
                            'tong_tien': f"{float(tong_tien):,.0f}",
                            'can_delete': True  # Vì là hóa đơn mới tạo
                        }
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Lỗi tạo hóa đơn: {str(e)}'
                })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        })


@require_http_methods(['POST'])
def xoa_hoa_don_bat_dau(request, ma_hop_dong):
    """
    Xóa hóa đơn bắt đầu của hợp đồng (chỉ khi chưa thanh toán)
    """
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy hóa đơn bắt đầu
        hoa_don_bat_dau = hop_dong.get_hoa_don_bat_dau()
        
        if not hoa_don_bat_dau:
            return JsonResponse({
                'success': False,
                'message': 'Không tìm thấy hóa đơn bắt đầu để xóa'
            })
        
        # Chỉ cho phép xóa hóa đơn chưa thanh toán
        if hoa_don_bat_dau.TRANG_THAI_HDON == 'Đã thanh toán':
            return JsonResponse({
                'success': False,
                'message': 'Không thể xóa hóa đơn đã thanh toán'
            })
        
        # Xóa hóa đơn
        with transaction.atomic():
            ma_hoa_don = hoa_don_bat_dau.MA_HOA_DON
            hoa_don_bat_dau.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Đã xóa hóa đơn bắt đầu {ma_hoa_don} thành công'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        })


@require_http_methods(['GET'])
def xem_hoa_don_bat_dau(request, ma_hop_dong):
    """
    Xem hóa đơn bắt đầu hiện tại của hợp đồng
    """
    try:
        hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
        
        # Lấy hóa đơn bắt đầu
        hoa_don = hop_dong.get_hoa_don_bat_dau()
        
        if not hoa_don:
            return JsonResponse({
                'success': False,
                'message': 'Hợp đồng này chưa có hóa đơn bắt đầu'
            })
        
        # Lấy thông tin khách thuê
        lich_su = hop_dong.lichsuhopdong.filter(MOI_QUAN_HE='Chủ hợp đồng').first()
        khach_thue = lich_su.MA_KHACH_THUE if lich_su else None
        
        return JsonResponse({
            'success': True,
            'data': {
                'ma_hoa_don': hoa_don.MA_HOA_DON,
                'ma_hop_dong': ma_hop_dong,
                'ten_phong': hop_dong.MA_PHONG.TEN_PHONG,
                'ten_khach_thue': khach_thue.HO_TEN_KT if khach_thue else '',
                'ngay_lap': hoa_don.NGAY_LAP_HDON.strftime('%d/%m/%Y') if hoa_don.NGAY_LAP_HDON else '',
                'loai_hoa_don': hoa_don.LOAI_HOA_DON,
                'trang_thai': hoa_don.TRANG_THAI_HDON,
                'tien_phong': f"{float(hoa_don.TIEN_PHONG or 0):,.0f}",
                'tien_dich_vu': f"{float(hoa_don.TIEN_DICH_VU or 0):,.0f}",
                'tien_coc': f"{float(hoa_don.TIEN_COC or 0):,.0f}",
                'tien_khau_tru': f"{float(hoa_don.TIEN_KHAU_TRU or 0):,.0f}",
                'tong_tien': f"{float(hoa_don.TONG_TIEN or 0):,.0f}",
                'can_delete': hoa_don.TRANG_THAI_HDON != 'Đã thanh toán'
            }
        })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        })