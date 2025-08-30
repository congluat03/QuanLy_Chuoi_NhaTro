from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count, Exists, OuterRef
from .models import HopDong, LichSuHopDong, DonDieuChinh
from apps.phongtro.models import PhongTro, CocPhong
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from apps.khachthue.models import CccdCmnd, KhachThue
from apps.phongtro.models import TAISANBANGIAO
from apps.nhatro.models import KhuVuc
from apps.dichvu.models import ChiSoDichVu, LichSuApDungDichVu
from django.db import transaction
from django.utils import timezone
from datetime import date, datetime, timedelta
import json

# Import workflow services
from .services import HopDongWorkflowService, HopDongReportService
from .workflow_service import ContractLifecycleManager

def apply_filters(queryset, request):
    """Áp dụng các bộ lọc cho queryset hợp đồng"""
    
    # Lọc theo tìm kiếm
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(MA_PHONG__TEN_PHONG__icontains=search) |
            Q(lichsuhopdong__MA_KHACH_THUE__HO_TEN_KT__icontains=search) |
            Q(lichsuhopdong__MA_KHACH_THUE__SDT_KT__icontains=search)
        ).distinct()
    
    # Lọc theo trạng thái
    trang_thai = request.GET.get('trang_thai', '').strip()
    if trang_thai:
        queryset = queryset.filter(TRANG_THAI_HD=trang_thai)
    
    # Lọc theo khu vực
    khu_vuc = request.GET.get('khu_vuc', '').strip()
    if khu_vuc:
        queryset = queryset.filter(MA_PHONG__MA_KHU_VUC=khu_vuc)
    
    # Lọc theo khoảng ngày lập
    tu_ngay = request.GET.get('tu_ngay', '').strip()
    den_ngay = request.GET.get('den_ngay', '').strip()
    
    if tu_ngay:
        try:
            from datetime import datetime
            tu_ngay_obj = datetime.strptime(tu_ngay, '%Y-%m-%d').date()
            queryset = queryset.filter(NGAY_LAP_HD__gte=tu_ngay_obj)
        except ValueError:
            pass
    
    if den_ngay:
        try:
            from datetime import datetime
            den_ngay_obj = datetime.strptime(den_ngay, '%Y-%m-%d').date()
            queryset = queryset.filter(NGAY_LAP_HD__lte=den_ngay_obj)
        except ValueError:
            pass
    
    # Lọc nhanh
    quick_filters = request.GET.getlist('quick_filter')
    
    if 'sap_het_han' in quick_filters:
        today = timezone.now().date()
        sap_het_han_date = today + timedelta(days=30)
        queryset = queryset.filter(
            NGAY_TRA_PHONG__lte=sap_het_han_date,
            NGAY_TRA_PHONG__gt=today,
            TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc']
        )
    
    if 'da_gia_han' in quick_filters:
        # Chỉ lấy hợp đồng có lịch sử gia hạn
        queryset = queryset.filter(
            Exists(DonDieuChinh.objects.filter(
                MA_HOP_DONG=OuterRef('pk'),
                LOAI_DC='Gia hạn hợp đồng'
            ))
        )
    
    if 'chua_xac_nhan' in quick_filters:
        queryset = queryset.filter(TRANG_THAI_HD='Chờ xác nhận')
    
    # Sắp xếp
    sort_by = request.GET.get('sort_by', 'MA_HOP_DONG').strip()
    if sort_by in [
        'MA_HOP_DONG', '-NGAY_LAP_HD', 'NGAY_LAP_HD', 
        '-NGAY_TRA_PHONG', 'NGAY_TRA_PHONG', 
        '-GIA_THUE', 'GIA_THUE'
    ]:
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by('MA_HOP_DONG')
    
    return queryset

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

    # Build queryset with filters
    hop_dongs = HopDong.objects.select_related(
        'MA_PHONG', 'MA_PHONG__MA_KHU_VUC'
    ).prefetch_related('lichsuhopdong__MA_KHACH_THUE', 'lichsugiahan')
    
    # Apply filters
    hop_dongs = apply_filters(hop_dongs, request)
    
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

    # Fetch all rooms and areas for filter dropdowns
    phong_tros = PhongTro.objects.order_by('MA_PHONG')
    khu_vucs = KhuVuc.objects.order_by('TEN_KHU_VUC')
    
    # Get dashboard statistics
    stats = HopDongReportService.thong_ke_hop_dong_theo_trang_thai()
    contracts_expiring = HopDongReportService.danh_sach_hop_dong_sap_het_han(30)

    return render(request, 'admin/hopdong/danhsach_hopdong.html', {
        'hop_dongs': hop_dongs_page,
        'phong_tros': phong_tros,
        'khu_vucs': khu_vucs,
        'stats': stats,
        'contracts_expiring_count': contracts_expiring.count(),
        'current_page_size': page_size,
        'total_contracts': paginator.count,
    })
@require_http_methods(['GET'])
def view_chinh_sua_hop_dong(request, ma_hop_dong):
    # Lấy hợp đồng hoặc trả về 404
    hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
    
    # Kiểm tra trạng thái hợp đồng - chỉ cho phép sửa khi chờ xác nhận
    if hop_dong.TRANG_THAI_HD != 'Chờ xác nhận':
        messages.error(
            request, 
            f'Không thể chỉnh sửa hợp đồng ở trạng thái "{hop_dong.TRANG_THAI_HD}". '
            'Chỉ có thể sửa hợp đồng ở trạng thái "Chờ xác nhận".'
        )
        return redirect('hopdong:hopdong_list')
    
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

    # Lấy danh sách dịch vụ dựa vào bảng chỉ số dịch vụ của hợp đồng
    lichsu_dichvu_with_chiso = []
    if hop_dong:
        # Lấy tất cả chỉ số dịch vụ đã ghi cho hợp đồng này
        chiso_dichvu_list = ChiSoDichVu.objects.filter(
            MA_HOP_DONG=hop_dong
        ).select_related('MA_DICH_VU').order_by('MA_DICH_VU__TEN_DICH_VU', '-NGAY_GHI_CS')
        
        # Group theo dịch vụ để lấy chỉ số mới nhất của mỗi dịch vụ
        dichvu_processed = set()
        
        for chiso in chiso_dichvu_list:
            if chiso.MA_DICH_VU.MA_DICH_VU not in dichvu_processed:
                # Lấy thông tin lịch sử áp dụng dịch vụ cho khu vực
                lichsu = LichSuApDungDichVu.objects.filter(
                    MA_KHU_VUC=hop_dong.MA_PHONG.MA_KHU_VUC,
                    MA_DICH_VU=chiso.MA_DICH_VU,
                    NGAY_HUY_DV__isnull=True
                ).first()
                
                # Nếu có lịch sử áp dụng, thêm vào danh sách
                if lichsu:
                    lichsu_dichvu_with_chiso.append({
                        'lichsu': lichsu,
                        'latest_chiso': chiso
                    })
                    dichvu_processed.add(chiso.MA_DICH_VU.MA_DICH_VU)

    return render(request, 'admin/hopdong/sua_hopdong.html', {
        'hop_dong': hop_dong,
        'coc_phong': coc_phong,
        'khach_thue': khach_thue,
        'cccd_cmnd': cccd_cmnd,
        'phong_tros': phong_tros,
        'lichsu_dichvu_with_chiso': lichsu_dichvu_with_chiso,
    })
def view_them_hop_dong(request):
    # Ví dụ: lấy danh sách phòng thuộc nhà trọ có mã là 1
    phong_tros = PhongTro.lay_phong_theo_ma_nha_tro(1)
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')
    return render(request, 'admin/hopdong/themsua_hopdong.html', {
        'phong_tros': phong_tros,
        'khu_vucs': khu_vucs,
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
                        'SDT_KT': coc_phong.MA_KHACH_THUE.SDT_KT
                    }
                }
            })
        else:
            return JsonResponse({'success': False, 'message': 'Không tìm thấy cọc phòng hợp lệ'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
def lay_thong_tin_phong(request, ma_phong):
    """API lấy thông tin phòng bao gồm giá phòng và tiền cọc"""
    try:
        # Lấy thông tin phòng
        phong = PhongTro.objects.get(MA_PHONG=ma_phong)
        
        # Kiểm tra có cọc phòng không
        coc_phong = CocPhong.objects.filter(
            MA_PHONG=phong,
            TRANG_THAI_CP__in=['Đã cọc', 'Chờ xác nhận']
        ).select_related('MA_KHACH_THUE').first()
        
        response_data = {
            'success': True,
            'phong': {
                'MA_PHONG': phong.MA_PHONG,
                'TEN_PHONG': phong.TEN_PHONG,
                'GIA_PHONG': str(phong.GIA_PHONG) if phong.GIA_PHONG else '0',
                'SO_TIEN_CAN_COC': str(phong.SO_TIEN_CAN_COC) if phong.SO_TIEN_CAN_COC else '0',
                'DIEN_TICH': str(phong.DIEN_TICH) if phong.DIEN_TICH else '0',
                'SO_NGUOI_TOI_DA': phong.SO_NGUOI_TOI_DA or 1,
                'TRANG_THAI_P': phong.TRANG_THAI_P
            }
        }
        
        # Nếu có cọc phòng, thêm thông tin khách thuê
        if coc_phong:
            response_data['coc_phong'] = {
                'MA_COC_PHONG': coc_phong.MA_COC_PHONG,
                'TIEN_COC_PHONG': str(coc_phong.TIEN_COC_PHONG) if coc_phong.TIEN_COC_PHONG else '0',
                'NGAY_COC_PHONG': coc_phong.NGAY_COC_PHONG.strftime('%Y-%m-%d') if coc_phong.NGAY_COC_PHONG else '',
                'TRANG_THAI_CP': coc_phong.TRANG_THAI_CP
            }
            
            if coc_phong.MA_KHACH_THUE:
                response_data['khach_thue'] = {
                    'MA_KHACH_THUE': coc_phong.MA_KHACH_THUE.MA_KHACH_THUE,
                    'HO_TEN_KT': coc_phong.MA_KHACH_THUE.HO_TEN_KT,
                    'GIOI_TINH_KT': coc_phong.MA_KHACH_THUE.GIOI_TINH_KT,
                    'NGAY_SINH_KT': coc_phong.MA_KHACH_THUE.NGAY_SINH_KT.strftime('%Y-%m-%d') if coc_phong.MA_KHACH_THUE.NGAY_SINH_KT else '',
                    'SDT_KT': coc_phong.MA_KHACH_THUE.SDT_KT,
                    'EMAIL_KT': coc_phong.MA_KHACH_THUE.EMAIL_KT or ''
                }
        
        return JsonResponse(response_data)
        
    except PhongTro.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Không tìm thấy phòng'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Lỗi hệ thống: {str(e)}'
        })

@csrf_exempt
def tim_khach_thue_co_san(request):
    """
    API tìm kiếm khách thuê có sẵn - chỉ hiển thị khách thuê:
    1. Chưa có hợp đồng nào
    2. Hoặc có hợp đồng đã kết thúc/đã rời đi
    """
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập'})
    
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'success': False, 'message': 'Vui lòng nhập ít nhất 2 ký tự'})
    
    try:
        from apps.khachthue.models import KhachThue
        from django.db.models import Q, Exists, OuterRef
        from apps.hopdong.models import HopDong, LichSuHopDong
        
        # Tìm khách thuê theo tên hoặc SĐT
        base_queryset = KhachThue.objects.filter(
            Q(HO_TEN_KT__icontains=query) | Q(SDT_KT__icontains=query)
        )
        
        # Lọc khách thuê có hợp đồng đang hoạt động
        active_contracts_subquery = LichSuHopDong.objects.filter(
            MA_KHACH_THUE=OuterRef('pk'),
            MA_HOP_DONG__TRANG_THAI_HD__in=[
                'Đang hoạt động', 
                'Đã xác nhận',
                'Sắp kết thúc',
                'Đang báo kết thúc'
            ]
        )
        
        # Chỉ lấy khách thuê KHÔNG có hợp đồng đang hoạt động
        available_tenants = base_queryset.filter(
            ~Exists(active_contracts_subquery)
        ).distinct()[:20]  # Giới hạn 20 kết quả
        
        results = []
        for khach_thue in available_tenants:
            # Lấy thông tin hợp đồng gần nhất (nếu có)
            latest_contract = LichSuHopDong.objects.filter(
                MA_KHACH_THUE=khach_thue
            ).select_related('MA_HOP_DONG').order_by('-MA_HOP_DONG__NGAY_LAP_HD').first()
            
            contract_info = None
            if latest_contract:
                contract_info = {
                    'last_contract_end': latest_contract.MA_HOP_DONG.NGAY_TRA_PHONG.strftime('%d/%m/%Y') if latest_contract.MA_HOP_DONG.NGAY_TRA_PHONG else '',
                    'status': latest_contract.MA_HOP_DONG.TRANG_THAI_HD,
                    'room_name': latest_contract.MA_HOP_DONG.MA_PHONG.TEN_PHONG if latest_contract.MA_HOP_DONG.MA_PHONG else ''
                }
            
            results.append({
                'MA_KHACH_THUE': khach_thue.MA_KHACH_THUE,
                'HO_TEN_KT': khach_thue.HO_TEN_KT,
                'SDT_KT': khach_thue.SDT_KT,
                'EMAIL_KT': khach_thue.EMAIL_KT or '',
                'GIOI_TINH_KT': khach_thue.GIOI_TINH_KT or '',
                'NGAY_SINH_KT': khach_thue.NGAY_SINH_KT.strftime('%Y-%m-%d') if khach_thue.NGAY_SINH_KT else '',
                'TRANG_THAI_KT': khach_thue.TRANG_THAI_KT or '',
                'contract_info': contract_info,
                'is_available': True  # Tất cả kết quả đều available
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results),
            'message': f'Tìm thấy {len(results)} khách thuê có sẵn'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi tìm kiếm: {str(e)}'
        })



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

@require_http_methods(['GET', 'POST'])
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
                'THOI_DIEM_THANH_TOAN': request.POST.get('THOI_DIEM_THANH_TOAN'),
                'CHU_KY_THANH_TOAN': request.POST.get('CHU_KY_THANH_TOAN'),
                'GHI_CHU_HD': request.POST.get('GHI_CHU_HD'),
                # Dữ liệu cho Cọc phòng
                'MA_COC_PHONG': request.POST.get('MA_COC_PHONG'),
                'GIA_COC_HD': request.POST.get('GIA_COC_HD'),

                # Dữ liệu khách thuê
                'HO_TEN_KT': request.POST.get('HO_TEN_KT'),
                'SDT_KT': request.POST.get('SDT_KT'),
                'NGAY_SINH_KT': request.POST.get('NGAY_SINH_KT'),
                'GIOI_TINH_KT': request.POST.get('GIOI_TINH_KT'),
                'EMAIL_KT': request.POST.get('EMAIL_KT'),
            }
            
            # Xử lý cập nhật dịch vụ
            with transaction.atomic():
                hop_dong.cap_nhat_hop_dong(data)
                
                # Cập nhật chỉ số dịch vụ nếu có
                for key, value in request.POST.items():
                    if key.startswith('chiso_hien_tai_') and value:
                        ma_dich_vu = key.replace('chiso_hien_tai_', '')
                        
                        # Lấy chỉ số hiện tại từ DB để làm CHI_SO_CU
                        chi_so_hien_tai = ChiSoDichVu.objects.filter(
                            MA_HOP_DONG=hop_dong,
                            MA_DICH_VU_id=ma_dich_vu
                        ).order_by('-NGAY_GHI_CS').first()
                        
                        chi_so_cu = chi_so_hien_tai.CHI_SO_MOI if chi_so_hien_tai else 0
                        
                        # Tạo bản ghi mới với chỉ số hiện tại
                        ChiSoDichVu.objects.create(
                            MA_HOP_DONG=hop_dong,
                            MA_DICH_VU_id=ma_dich_vu,
                            CHI_SO_CU=chi_so_cu,
                            CHI_SO_MOI=int(value),
                            NGAY_GHI_CS=timezone.now().date()
                        )
                    
                    elif key.startswith('soluong_') and value:
                        ma_dich_vu = key.replace('soluong_', '')
                        
                        # Cập nhật số lượng cho dịch vụ cố định
                        ChiSoDichVu.objects.update_or_create(
                            MA_HOP_DONG=hop_dong,
                            MA_DICH_VU_id=ma_dich_vu,
                            defaults={
                                'SO_LUONG': int(value),
                                'NGAY_GHI_CS': timezone.now().date()
                            }
                        )
                
            messages.success(request, 'Cập nhật hợp đồng thành công!')
            return redirect('hopdong:hopdong_list')
        except ValueError as e:
            messages.error(request, f'Lỗi dữ liệu: {str(e)}')
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống: {str(e)}')
    
    # Nếu là GET request, hiển thị form
    return redirect('hopdong:view_chinh_sua_hop_dong', ma_hop_dong=ma_hop_dong)
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
    
    # Lấy lịch sử báo kết thúc
    lich_su_bao_ket_thuc = hop_dong.lichsugiahan.filter(LOAI_DC='Báo kết thúc sớm').order_by('-NGAY_TAO_DC')
    
    context = {
        'hop_dong': hop_dong,
        'khach_thue': khach_thue,  # Trả về cả object lich su hop dong
        'hoa_don_bat_dau': hoa_don_bat_dau,
        'danh_sach_hoa_don': danh_sach_hoa_don,
        'lich_su_gia_han': lich_su_gia_han,
        'so_lan_gia_han': hop_dong.da_gia_han_bao_nhieu_lan(),
        'lich_su_bao_ket_thuc': lich_su_bao_ket_thuc,
        'can_sinh_hoa_don_bat_dau': not hop_dong.get_hoa_don_bat_dau(),
    }
    
    return render(request, 'admin/hopdong/chi_tiet_hop_dong.html', context)



# ======================= WORKFLOW FUNCTIONS =======================

def get_available_workflow_actions(contract):
    """Xác định các action workflow có thể thực hiện với hợp đồng"""
    actions = []
    
    if contract.TRANG_THAI_HD == 'Chờ xác nhận':
        actions.extend([
            {'action': 'confirm', 'label': 'Xác nhận & Sinh HĐ', 'icon': 'fas fa-check-circle', 'class': 'btn-success'},
            {'action': 'edit', 'label': 'Chỉnh sửa', 'icon': 'fas fa-edit', 'class': 'btn-warning'},
            {'action': 'cancel', 'label': 'Kết thúc hợp đồng', 'icon': 'fas fa-stop-circle', 'class': 'btn-danger'}
        ])
    
    elif contract.TRANG_THAI_HD == 'Đang hoạt động':
        actions.extend([
            {'action': 'extend', 'label': 'Gia hạn', 'icon': 'fas fa-calendar-plus', 'class': 'btn-info'},
            {'action': 'early_end', 'label': 'Báo kết thúc sớm', 'icon': 'fas fa-exclamation-triangle', 'class': 'btn-warning'},
            {'action': 'view_detail', 'label': 'Chi tiết', 'icon': 'fas fa-eye', 'class': 'btn-secondary'}
        ])
    
    elif contract.TRANG_THAI_HD in ['Sắp kết thúc', 'Đang báo kết thúc']:
        actions.extend([
            {'action': 'extend', 'label': 'Gia hạn', 'icon': 'fas fa-calendar-plus', 'class': 'btn-info'},
            {'action': 'view_detail', 'label': 'Chi tiết', 'icon': 'fas fa-eye', 'class': 'btn-secondary'}
        ])
    
    else:  # Đã kết thúc
        actions.extend([
            {'action': 'view_detail', 'label': 'Chi tiết', 'icon': 'fas fa-eye', 'class': 'btn-secondary'},
            {'action': 'archive', 'label': 'Lưu trữ', 'icon': 'fas fa-archive', 'class': 'btn-outline'}
        ])
    
    return actions




@require_http_methods(['GET'])
def dashboard_statistics(request):
    """API để lấy thống kê dashboard - chỉ sử dụng MA_HOP_DONG làm key thống kê"""
    # Check authentication and permissions
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập để xem thống kê'})
    
    vai_tro = request.session.get('vai_tro')
    if vai_tro not in ['Chủ trọ', 'admin']:
        return JsonResponse({'success': False, 'message': 'Bạn không có quyền xem thống kê'})
        
    try:
        # Thống kê cơ bản theo hợp đồng
        stats = HopDongReportService.thong_ke_hop_dong_theo_trang_thai()
        
        # Hợp đồng sắp hết hạn
        contracts_expiring = HopDongReportService.danh_sach_hop_dong_sap_het_han(30)
        
        # Doanh thu tháng hiện tại từ hợp đồng
        current_month = datetime.now()
        revenue = HopDongReportService.bao_cao_doanh_thu_hop_dong(
            current_month.month, 
            current_month.year
        )
        
        # Thống kê chi tiết cho dashboard
        stats_detailed = HopDongReportService.thong_ke_chi_tiet_dashboard()
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_contracts': stats_detailed.get('tong_hop_dong', 0),
                'active_contracts': stats_detailed.get('dang_hoat_dong', 0),
                'expiring_contracts': contracts_expiring.count(),
                'pending_contracts': stats_detailed.get('cho_xac_nhan', 0)
            },
            'recent_activities': [
                {
                    'title': f'Hợp đồng #{hd.MA_HOP_DONG}',
                    'description': f'Hết hạn còn {(hd.NGAY_TRA_PHONG - date.today()).days} ngày',
                    'time': hd.NGAY_TRA_PHONG.strftime('%d/%m/%Y'),
                    'color': 'orange',
                    'icon': 'fas fa-calendar-times'
                } for hd in contracts_expiring[:3]
            ],
            'data': {
                'contract_stats': stats,
                'contracts_expiring': {
                    'count': contracts_expiring.count(),
                    'list': [
                        {
                            'ma_hop_dong': hd.MA_HOP_DONG,
                            'ma_phong': hd.MA_PHONG_id,  # Chỉ ID, không lấy tên phòng
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







# ==================== 3 VIEWS MỚI CHO CHỈNH SỬA RIÊNG BIỆT ====================

@require_http_methods(['GET', 'POST'])
def sua_thongtin_hopdong(request, ma_hop_dong):
    """Chỉnh sửa thông tin và điều khoản hợp đồng"""
    hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
    
    # Kiểm tra trạng thái hợp đồng
    if hop_dong.TRANG_THAI_HD != 'Chờ xác nhận':
        messages.error(
            request, 
            f'Không thể chỉnh sửa hợp đồng ở trạng thái "{hop_dong.TRANG_THAI_HD}". '
            'Chỉ có thể sửa hợp đồng ở trạng thái "Chờ xác nhận".'
        )
        return redirect('hopdong:hopdong_list')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Cập nhật thông tin hợp đồng
                hop_dong.NGAY_LAP_HD = request.POST.get('NGAY_LAP_HD')
                hop_dong.NGAY_NHAN_PHONG = request.POST.get('NGAY_NHAN_PHONG')
                hop_dong.NGAY_TRA_PHONG = request.POST.get('NGAY_TRA_PHONG')
                hop_dong.GIA_THUE = request.POST.get('GIA_THUE')
                hop_dong.GIA_COC_HD = request.POST.get('GIA_COC_HD')
                hop_dong.SO_THANH_VIEN = request.POST.get('SO_THANH_VIEN_TOI_DA')
                hop_dong.THOI_HAN_HD = request.POST.get('THOI_HAN_HD')
                hop_dong.NGAY_THU_TIEN = request.POST.get('NGAY_THU_TIEN')
                hop_dong.THOI_DIEM_THANH_TOAN = request.POST.get('THOI_DIEM_THANH_TOAN')
                hop_dong.CHU_KY_THANH_TOAN = request.POST.get('CHU_KY_THANH_TOAN')
                hop_dong.GHI_CHU_HD = request.POST.get('GHI_CHU_HD')
                
                hop_dong.save()
                
            messages.success(request, 'Cập nhật thông tin hợp đồng thành công!')
            return redirect('hopdong:hopdong_list')
            
        except Exception as e:
            messages.error(request, f'Lỗi cập nhật: {str(e)}')
    
    return render(request, 'admin/hopdong/sua_thongtin_hopdong.html', {
        'hop_dong': hop_dong
    })

@require_http_methods(['GET', 'POST'])  
def sua_khachthue_hopdong(request, ma_hop_dong):
    """Chỉnh sửa thông tin khách thuê"""
    hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
    
    # Kiểm tra trạng thái hợp đồng
    if hop_dong.TRANG_THAI_HD != 'Chờ xác nhận':
        messages.error(
            request, 
            f'Không thể chỉnh sửa hợp đồng ở trạng thái "{hop_dong.TRANG_THAI_HD}". '
            'Chỉ có thể sửa hợp đồng ở trạng thái "Chờ xác nhận".'
        )
        return redirect('hopdong:hopdong_list')
    
    # Lấy thông tin khách thuê hiện tại
    lich_su = LichSuHopDong.objects.filter(
        MA_HOP_DONG=hop_dong,
        MOI_QUAN_HE='Chủ hợp đồng'
    ).select_related('MA_KHACH_THUE').first()
    
    khach_thue = lich_su.MA_KHACH_THUE if lich_su else None
    cccd_cmnd = CccdCmnd.objects.filter(MA_KHACH_THUE=khach_thue).first() if khach_thue else None
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                ma_khach_thue_post = request.POST.get('MA_KHACH_THUE')
                tenant_type = request.POST.get('tenant_type', 'existing')
                
                if tenant_type == 'search' and ma_khach_thue_post and ma_khach_thue_post.isdigit():
                    # Chọn khách thuê có sẵn từ hệ thống
                    khach_thue_moi = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue_post)
                    
                    # Cập nhật lịch sử hợp đồng để trỏ đến khách thuê mới
                    if lich_su:
                        lich_su.MA_KHACH_THUE = khach_thue_moi
                        lich_su.save()
                    else:
                        LichSuHopDong.objects.create(
                            MA_HOP_DONG=hop_dong,
                            MA_KHACH_THUE=khach_thue_moi,
                            MOI_QUAN_HE='Chủ hợp đồng',
                            NGAY_THAM_GIA=timezone.now().date()
                        )
                    
                    messages.success(request, f'Đã chuyển hợp đồng sang khách thuê: {khach_thue_moi.HO_TEN_KT}')
                    
                else:
                    # Cập nhật thông tin khách thuê hiện tại (chỉ thông tin cơ bản)
                    if khach_thue:
                        khach_thue.HO_TEN_KT = request.POST.get('HO_TEN_KT')
                        khach_thue.GIOI_TINH_KT = request.POST.get('GIOI_TINH_KT')
                        khach_thue.NGAY_SINH_KT = request.POST.get('NGAY_SINH_KT') or None
                        khach_thue.SDT_KT = request.POST.get('SDT_KT')
                        khach_thue.EMAIL_KT = request.POST.get('EMAIL_KT')
                        khach_thue.save()
                        
                        messages.success(request, 'Cập nhật thông tin khách thuê thành công!')
                    else:
                        messages.error(request, 'Không tìm thấy khách thuê để cập nhật!')
                        return redirect('hopdong:hopdong_list')
                
            return redirect('hopdong:hopdong_list')
            
        except Exception as e:
            messages.error(request, f'Lỗi cập nhật: {str(e)}')
    
    return render(request, 'admin/hopdong/sua_khachthue_hopdong.html', {
        'hop_dong': hop_dong,
        'khach_thue': khach_thue,
        'cccd_cmnd': cccd_cmnd
    })

@require_http_methods(['GET'])
def tim_khach_thue_ajax(request):
    """API tìm kiếm khách thuê cho chỉnh sửa hợp đồng"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Tìm kiếm khách thuê theo tên hoặc SĐT
    khach_thue_list = KhachThue.objects.filter(
        Q(HO_TEN_KT__icontains=query) | 
        Q(SDT_KT__icontains=query)
    ).exclude(
        TRANG_THAI_KT='Đã rời đi'
    )[:10]  # Giới hạn 10 kết quả
    
    results = []
    for khach_thue in khach_thue_list:
        results.append({
            'id': khach_thue.MA_KHACH_THUE,
            'ho_ten': khach_thue.HO_TEN_KT or '',
            'sdt': khach_thue.SDT_KT or '',
            'email': khach_thue.EMAIL_KT or '',
            'gioi_tinh': khach_thue.GIOI_TINH_KT or 'Nam',
            'ngay_sinh': khach_thue.NGAY_SINH_KT.strftime('%Y-%m-%d') if khach_thue.NGAY_SINH_KT else '',
            'display_text': f"{khach_thue.HO_TEN_KT} - {khach_thue.SDT_KT}"
        })
    
    return JsonResponse({'results': results})


@require_http_methods(['GET', 'POST'])
def sua_dichvu_hopdong(request, ma_hop_dong):
    """Chỉnh sửa dịch vụ hợp đồng"""
    hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=ma_hop_dong)
    
    # Kiểm tra trạng thái hợp đồng  
    if hop_dong.TRANG_THAI_HD != 'Chờ xác nhận':
        messages.error(
            request, 
            f'Không thể chỉnh sửa hợp đồng ở trạng thái "{hop_dong.TRANG_THAI_HD}". '
            'Chỉ có thể sửa hợp đồng ở trạng thái "Chờ xác nhận".'
        )
        return redirect('hopdong:hopdong_list')
    
    # Lấy danh sách dịch vụ theo khu vực của phòng
    lichsu_dichvu_with_chiso = []
    if hop_dong and hop_dong.MA_PHONG and hop_dong.MA_PHONG.MA_KHU_VUC:
        # Lấy tất cả dịch vụ áp dụng cho khu vực
        lichsu_dichvu_list = LichSuApDungDichVu.objects.filter(
            MA_KHU_VUC=hop_dong.MA_PHONG.MA_KHU_VUC,
            NGAY_HUY_DV__isnull=True
        ).select_related('MA_DICH_VU').order_by('MA_DICH_VU__TEN_DICH_VU')
        
        # Với mỗi dịch vụ, tìm chỉ số mới nhất của hợp đồng (nếu có)
        for lichsu in lichsu_dichvu_list:
            latest_chiso = ChiSoDichVu.objects.filter(
                MA_HOP_DONG=hop_dong,
                MA_DICH_VU=lichsu.MA_DICH_VU
            ).order_by('-NGAY_GHI_CS').first()
            
            lichsu_dichvu_with_chiso.append({
                'lichsu': lichsu,
                'latest_chiso': latest_chiso,
                'co_chi_so': latest_chiso is not None
            })
    
    # Tính toán thống kê
    tong_dich_vu = len(lichsu_dichvu_with_chiso)
    theo_chi_so = len([item for item in lichsu_dichvu_with_chiso if item['lichsu'].MA_DICH_VU.LOAI_DICH_VU == 'Tính theo chỉ số'])
    co_dinh = tong_dich_vu - theo_chi_so
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Lấy danh sách dịch vụ được chọn (checked)
                selected_services = request.POST.getlist('selected_services')
                
                # Lấy tất cả dịch vụ của khu vực để biết dịch vụ nào bị bỏ chọn
                all_services = [str(item['lichsu'].MA_DICH_VU.MA_DICH_VU) for item in lichsu_dichvu_with_chiso]
                
                # Duyệt qua tất cả dịch vụ
                for item in lichsu_dichvu_with_chiso:
                    ma_dich_vu_str = str(item['lichsu'].MA_DICH_VU.MA_DICH_VU)
                    dich_vu = item['lichsu'].MA_DICH_VU
                    latest_chiso = item['latest_chiso']
                    co_chi_so_truoc = item['co_chi_so']
                    
                    # Kiểm tra dịch vụ có được chọn không
                    duoc_chon = ma_dich_vu_str in selected_services
                    
                    if duoc_chon:
                        # Dịch vụ được chọn - tạo hoặc cập nhật
                        if dich_vu.LOAI_DICH_VU == 'Tính theo chỉ số':
                            # Dịch vụ theo chỉ số
                            chi_so_moi_value = request.POST.get(f'chiso_moi_{ma_dich_vu_str}')
                            if chi_so_moi_value:
                                if co_chi_so_truoc and latest_chiso:
                                    # Cập nhật chỉ số hiện tại
                                    latest_chiso.CHI_SO_MOI = int(chi_so_moi_value)
                                    latest_chiso.NGAY_GHI_CS = timezone.now().date()
                                    latest_chiso.save()
                                else:
                                    # Tạo chỉ số mới
                                    chi_so_cu = request.POST.get(f'chiso_cu_{ma_dich_vu_str}', 0)
                                    ChiSoDichVu.objects.create(
                                        MA_HOP_DONG=hop_dong,
                                        MA_DICH_VU=dich_vu,
                                        CHI_SO_CU=int(chi_so_cu),
                                        CHI_SO_MOI=int(chi_so_moi_value),
                                        NGAY_GHI_CS=timezone.now().date()
                                    )
                        else:
                            # Dịch vụ cố định
                            so_luong_value = request.POST.get(f'soluong_{ma_dich_vu_str}')
                            if so_luong_value:
                                if co_chi_so_truoc and latest_chiso:
                                    # Cập nhật số lượng hiện tại
                                    latest_chiso.SO_LUONG = int(so_luong_value)
                                    latest_chiso.NGAY_GHI_CS = timezone.now().date()
                                    latest_chiso.save()
                                else:
                                    # Tạo bản ghi mới
                                    ChiSoDichVu.objects.create(
                                        MA_HOP_DONG=hop_dong,
                                        MA_DICH_VU=dich_vu,
                                        CHI_SO_CU=None,
                                        CHI_SO_MOI=None,
                                        SO_LUONG=int(so_luong_value),
                                        NGAY_GHI_CS=timezone.now().date()
                                    )
                
                # Xử lý các dịch vụ bị bỏ chọn (uncheck) - xóa chỉ số
                for item in lichsu_dichvu_with_chiso:
                    ma_dich_vu_str = str(item['lichsu'].MA_DICH_VU.MA_DICH_VU)
                    latest_chiso = item['latest_chiso']
                    co_chi_so_truoc = item['co_chi_so']
                    
                    # Nếu dịch vụ không được chọn và trước đó có chỉ số
                    if ma_dich_vu_str not in selected_services and co_chi_so_truoc and latest_chiso:
                        latest_chiso.delete()
                
            messages.success(request, 'Cập nhật chỉ số dịch vụ thành công!')
            return redirect('hopdong:hopdong_list')
            
        except Exception as e:
            messages.error(request, f'Lỗi cập nhật: {str(e)}')
    
    return render(request, 'admin/hopdong/sua_dichvu_hopdong.html', {
        'hop_dong': hop_dong,
        'lichsu_dichvu_with_chiso': lichsu_dichvu_with_chiso,
        'tong_dich_vu': tong_dich_vu,
        'theo_chi_so': theo_chi_so,
        'co_dinh': co_dinh
    })