from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .models import PhongTro, CocPhong, TAISANPHONG, TAISAN, DangTinPhong, HinhAnhTinDang
from apps.nhatro.models import KhuVuc
from apps.khachthue.models import KhachThue
from apps.hopdong.models import HopDong
from apps.thanhvien.models import TaiKhoan
from apps.dichvu.models import LichSuApDungDichVu, ChiSoDichVu
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST
from datetime import date
from django.db.models import Q
from apps.hopdong.services import HopDongWorkflowService
import json
from decimal import Decimal



def phongtro_list(request):
    # Check user authentication and permissions
    if not request.session.get('is_authenticated'):
        return redirect('auth:login')
    
    vai_tro = request.session.get('vai_tro')
    if vai_tro not in ['Chủ trọ', 'admin']:
        messages.error(request, 'Bạn không có quyền truy cập chức năng này.')
        return redirect('index:trang_chu')
    
    # Lấy ma_khu_vuc và page_number từ query string (?ma_khu_vuc=...&page_number=...)
    ma_khu_vuc = request.GET.get('ma_khu_vuc')
    page_number = request.GET.get('page_number', 1)

    # Lấy danh sách khu vực nhà trọ có MA_NHA_TRO = 1
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1)
    
    # Nếu không có mã khu vực, chọn khu vực đầu tiên
    if not ma_khu_vuc and khu_vucs.exists():
        ma_khu_vuc = khu_vucs.first().MA_KHU_VUC
    
    # Chuyển đổi ma_khu_vuc thành integer để so sánh
    try:
        ma_khu_vuc = int(ma_khu_vuc) if ma_khu_vuc else None
    except (ValueError, TypeError):
        ma_khu_vuc = khu_vucs.first().MA_KHU_VUC if khu_vucs.exists() else None

    # Lấy tham số tìm kiếm và bộ lọc từ request
    keyword = request.GET.get('keyword', '') or request.GET.get('ten_phong', '')
    trang_thai_phong = request.GET.get('trang_thai_phong', '')
    
    # QUAN TRỌNG: Luôn lọc theo khu vực đã chọn, không cho phép lọc sang khu vực khác
    phong_tros = PhongTro.objects.filter(MA_KHU_VUC=ma_khu_vuc)\
        .select_related('MA_LOAI_PHONG', 'MA_KHU_VUC')\
        .prefetch_related('cocphong', 'hopdong')

    # Áp dụng bộ lọc từ khóa nếu có
    if keyword:
        phong_tros = phong_tros.filter(
            Q(TEN_PHONG__icontains=keyword) |
            Q(MA_LOAI_PHONG__TEN_LOAI_PHONG__icontains=keyword)
        )

    # Áp dụng bộ lọc trạng thái phòng đơn giản
    if trang_thai_phong:
        if trang_thai_phong == 'Đang trống':
            phong_tros = phong_tros.filter(TRANG_THAI_P='Đang trống')
        elif trang_thai_phong == 'Đang ở':
            phong_tros = phong_tros.filter(TRANG_THAI_P='Đang ở')

    # Phân trang (8 mục/trang)
    paginator = Paginator(phong_tros, 8)
    phong_tros_page = paginator.get_page(page_number)

    # Danh sách trạng thái đơn giản
    trang_thai_phong_choices = ['Đang trống', 'Đang ở']

    # Lấy thông tin khu vực hiện tại
    khu_vuc_hien_tai = khu_vucs.filter(MA_KHU_VUC=ma_khu_vuc).first() if ma_khu_vuc else None
    
    context = {
        'phong_tros': phong_tros_page,
        'ma_khu_vuc': ma_khu_vuc,
        'khu_vuc_hien_tai': khu_vuc_hien_tai,
        'trang_thai_phong_choices': trang_thai_phong_choices,
        'keyword': keyword,
        'trang_thai_phong': trang_thai_phong,
        'khu_vucs': khu_vucs,
    }
    
    # Thêm thông tin workflow và cập nhật trạng thái phòng
    for phong in phong_tros_page:
        # Lấy hợp đồng hiện tại của phòng (chỉ những trạng thái yêu cầu)
        hop_dong = phong.hopdong.filter(TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc', 'Đang báo kết thúc']).first()
        phong.current_contract = hop_dong
        
        # Cập nhật trạng thái phòng dựa trên hợp đồng
        if hop_dong:
            # Chỉ có 3 trạng thái hợp đồng được xem xét
            phong.trang_thai_hien_thi = 'Đang ở'
        else:
            # Kiểm tra có cọc phòng không
            coc_phong = phong.cocphong.filter(TRANG_THAI_CP__in=['Đã cọc', 'Chờ xác nhận']).first()
            if coc_phong:
                phong.trang_thai_hien_thi = 'Đang cọc'
            else:
                phong.trang_thai_hien_thi = phong.TRANG_THAI_P or 'Đang trống'
        
        # Thêm thông tin các actions có thể thực hiện
        if hop_dong:
            phong.workflow_actions = hop_dong.get_available_workflow_actions()
        else:
            phong.workflow_actions = []
            
        # Lấy thông tin người đại diện và đếm số người thực tế đang ở
        if hop_dong:
            from apps.hopdong.models import LichSuHopDong
            
            # Lấy người đại diện (Chủ hợp đồng)
            chu_hop_dong = LichSuHopDong.objects.filter(
                MA_HOP_DONG=hop_dong,
                MOI_QUAN_HE='Chủ hợp đồng',
                NGAY_ROI_DI__isnull=True
            ).select_related('MA_KHACH_THUE').first()
            
            if chu_hop_dong:
                phong.nguoi_dai_dien = chu_hop_dong.MA_KHACH_THUE
            else:
                phong.nguoi_dai_dien = None
            
            # Đếm số người từ lịch sử hợp đồng (những người chưa rời đi)
            so_nguoi_dang_o = LichSuHopDong.objects.filter(
                MA_HOP_DONG=hop_dong,
                NGAY_ROI_DI__isnull=True  # Chưa rời đi
            ).count()
            phong.so_nguoi_dang_o = so_nguoi_dang_o
            
            # Tính toán tình trạng thanh toán
            from apps.hoadon.models import HoaDon, PHIEUTHU
            
            # Lấy tất cả hóa đơn của hợp đồng
            hoa_dons = hop_dong.hoadon.all()
            tong_so_tien_can_thu = Decimal('0')
            tong_so_tien_da_thu = Decimal('0')
            
            for hoa_don in hoa_dons:
                # Tổng tiền hóa đơn
                tong_so_tien_can_thu += hoa_don.TONG_TIEN or Decimal('0')
                
                # Tổng tiền đã thu từ phiếu thu
                phieu_thus = PHIEUTHU.objects.filter(MA_HOA_DON=hoa_don)
                for phieu_thu in phieu_thus:
                    tong_so_tien_da_thu += phieu_thu.SO_TIEN or Decimal('0')
            
            # Tính số tiền còn nợ
            so_tien_con_no = tong_so_tien_can_thu - tong_so_tien_da_thu
            
            phong.tong_so_tien_can_thu = tong_so_tien_can_thu
            phong.tong_so_tien_da_thu = tong_so_tien_da_thu
            phong.so_tien_con_no = so_tien_con_no
            phong.co_hoa_don_chua_thanh_toan = so_tien_con_no > 0
            
            # Kiểm tra hợp đồng sắp hết hạn (còn 30 ngày)
            from datetime import date, timedelta
            if hop_dong.NGAY_TRA_PHONG:
                ngay_het_han = hop_dong.NGAY_TRA_PHONG
                ngay_canh_bao = date.today() + timedelta(days=30)
                phong.sap_het_han = ngay_het_han <= ngay_canh_bao
            else:
                phong.sap_het_han = False
        else:
            phong.nguoi_dai_dien = None
            phong.so_nguoi_dang_o = 0
            phong.tong_so_tien_can_thu = Decimal('0')
            phong.tong_so_tien_da_thu = Decimal('0')
            phong.so_tien_con_no = Decimal('0')
            phong.co_hoa_don_chua_thanh_toan = False
            phong.sap_het_han = False

    return render(request, 'admin/phongtro/phongtro.html', context)


def room_workflow_action(request):
    """
    Xử lý các thao tác workflow cho phòng trọ qua AJAX
    """
    # Check authentication and permissions
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập để thực hiện thao tác này'})
    
    vai_tro = request.session.get('vai_tro')
    if vai_tro not in ['Chủ trọ', 'admin']:
        return JsonResponse({'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            room_id = data.get('room_id')
            contract_id = data.get('contract_id')
            additional_data = data.get('data', {})
            
            if not room_id:
                return JsonResponse({'success': False, 'message': 'ID phòng không hợp lệ'})
            
            # Lấy phòng trọ
            phong = get_object_or_404(PhongTro, MA_PHONG=room_id)
            
            # Nếu có contract_id, lấy hợp đồng cụ thể
            if contract_id:
                hop_dong = get_object_or_404(HopDong, MA_HOP_DONG=contract_id)
            else:
                # Tìm hợp đồng hiện tại của phòng
                hop_dong = phong.hopdong.filter(
                    TRANG_THAI_HD__in=['Hoạt động', 'Chưa ký', 'Sắp hết hạn']
                ).first()
                
                if not hop_dong:
                    return JsonResponse({'success': False, 'message': 'Không tìm thấy hợp đồng hiện tại'})
            
            # Xử lý từng loại action
            if action == 'create_contract':
                # Tạo hợp đồng mới cho phòng trống
                if phong.TRANG_THAI_P != 'Đang trống':
                    return JsonResponse({'success': False, 'message': 'Phòng không ở trạng thái trống'})
                
                # Redirect đến trang tạo hợp đồng với MA_PHONG
                return JsonResponse({
                    'success': True, 
                    'redirect': f'/admin/hopdong/viewthem/?ma_phong={room_id}',
                    'message': 'Chuyển đến trang tạo hợp đồng'
                })
            
            elif action == 'confirm':
                result, message, errors = HopDongWorkflowService.xac_nhan_va_kich_hoat_hop_dong(hop_dong)
                if result:
                    return JsonResponse({'success': True, 'message': message})
                else:
                    return JsonResponse({'success': False, 'message': message, 'errors': errors})
            
            elif action == 'create_invoice':
                result, message, errors = HopDongWorkflowService.tao_hoa_don_cho_hop_dong(hop_dong)
                if result:
                    return JsonResponse({'success': True, 'message': message})
                else:
                    return JsonResponse({'success': False, 'message': message, 'errors': errors})
            
            elif action == 'extend':
                new_end_date = additional_data.get('new_end_date')
                reason = additional_data.get('reason', '')
                
                if not new_end_date:
                    return JsonResponse({'success': False, 'message': 'Ngày kết thúc mới không hợp lệ'})
                
                result, message, errors = HopDongWorkflowService.gia_han_hop_dong(
                    hop_dong, new_end_date, reason
                )
                if result:
                    return JsonResponse({'success': True, 'message': message})
                else:
                    return JsonResponse({'success': False, 'message': message, 'errors': errors})
            
            elif action == 'early_end':
                early_end_date = additional_data.get('early_end_date')
                reason = additional_data.get('reason', '')
                
                if not early_end_date or not reason:
                    return JsonResponse({'success': False, 'message': 'Thiếu thông tin ngày và lý do'})
                
                result, message, errors = HopDongWorkflowService.bao_ket_thuc_som(
                    hop_dong, early_end_date, reason
                )
                if result:
                    return JsonResponse({'success': True, 'message': message})
                else:
                    return JsonResponse({'success': False, 'message': message, 'errors': errors})
            
            elif action == 'end':
                result, message, errors = HopDongWorkflowService.ket_thuc_hop_dong(hop_dong)
                if result:
                    return JsonResponse({'success': True, 'message': message})
                else:
                    return JsonResponse({'success': False, 'message': message, 'errors': errors})
            
            elif action == 'cancel':
                reason = additional_data.get('reason', 'Hủy từ giao diện quản lý')
                result, message, errors = HopDongWorkflowService.huy_hop_dong(hop_dong, reason)
                if result:
                    return JsonResponse({'success': True, 'message': message})
                else:
                    return JsonResponse({'success': False, 'message': message, 'errors': errors})
            
            else:
                return JsonResponse({'success': False, 'message': 'Thao tác không được hỗ trợ'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Dữ liệu JSON không hợp lệ'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Chỉ hỗ trợ POST request'})




def view_themsua_phongtro(request, ma_khu_vuc, loai='single', ma_phong_tro=None):
    # 1. Tìm khu vực
    khu_vuc = KhuVuc.objects.filter(MA_KHU_VUC=ma_khu_vuc).first()
    if not khu_vuc:
        messages.error(request, "Khu vực không tồn tại.")
        return redirect('dashboard')  # Đảm bảo bạn có route tên 'dashboard'

    # 2. Kiểm tra loại yêu cầu
    valid_loai = ['single', 'multiple', 'edit']
    if loai not in valid_loai:
        messages.error(request, "Loại yêu cầu không hợp lệ.")
        return redirect('dashboard')

    # 3. Nếu là 'edit', kiểm tra MA_PHONG
    phong_tro = None
    if loai == 'edit':
        if not ma_phong_tro:
            messages.error(request, "Mã phòng trọ không được cung cấp.")
            return redirect('dashboard')

        phong_tro = PhongTro.objects.filter(MA_PHONG=ma_phong_tro).first()
        if not phong_tro:
            messages.error(request, "Phòng trọ không tồn tại.")
            return redirect('dashboard')

    # 4. Trả về template
    context = {
        'khu_vuc': khu_vuc,
        'loai': loai,
        'phong_tro': phong_tro
    }
    return render(request, 'admin/phongtro/themsua_phongtro.html', context)

def sua_phongtro(request, ma_phong_tro):
    phong_tro = get_object_or_404(PhongTro, MA_PHONG=ma_phong_tro)
    if request.method == 'POST':
        data = request.POST
        phong_tro.TEN_PHONG = data.get('TEN_PHONG')
        phong_tro.MA_LOAI_PHONG_id = data.get('MA_LOAI_PHONG')
        phong_tro.GIA_PHONG = data.get('GIA_PHONG')
        phong_tro.SO_NGUOI_TOI_DA = data.get('SO_NGUOI_TOI_DA')
        phong_tro.SO_TIEN_CAN_COC=data.get('SOTIENCANCOC')
        phong_tro.DIEN_TICH=data.get('DIEN_TICH', '')
        phong_tro.MO_TA_P = data.get('MO_TA_P', '')
        phong_tro.save()
        messages.success(request, 'Cập nhật phòng trọ thành công.')
        return redirect(request.META.get('HTTP_REFERER', 'phongtro:danh_sach_phongtro'))
    return redirect('phongtro:phongtro_list')

def them_phongtro(request):
    if request.method == 'POST':
        data = request.POST
        loai = data.get('loai')

        if loai == 'multiple':
            so_phong_bat_dau = data.get('SOPHONGBATDAU')
            so_phong_ket_thuc = data.get('SOPHONGKETTHUC')

            if not so_phong_bat_dau or not so_phong_ket_thuc:
                messages.error(request, 'Vui lòng nhập số phòng bắt đầu và kết thúc.')
                return redirect(request.META.get('HTTP_REFERER', 'phongtro:them_phongtro'))

            so_phong_bat_dau = int(so_phong_bat_dau)
            so_phong_ket_thuc = int(so_phong_ket_thuc)

            if so_phong_bat_dau > so_phong_ket_thuc:
                messages.error(request, 'Số phòng bắt đầu phải nhỏ hơn hoặc bằng số phòng kết thúc.')
                return redirect(request.META.get('HTTP_REFERER', 'phongtro:them_phongtro'))

            for i in range(so_phong_bat_dau, so_phong_ket_thuc + 1):
                PhongTro.objects.create(
                    MA_LOAI_PHONG_id=data.get('MA_LOAI_PHONG'),
                    MA_KHU_VUC_id=data.get('MA_KHU_VUC'),
                    TEN_PHONG=f"{data.get('TEN_PHONG')} {i}",
                    GIA_PHONG=data.get('GIA_PHONG'),
                    SO_NGUOI_TOI_DA=data.get('SO_NGUOI_TOI_DA'),
                    SO_TIEN_CAN_COC=data.get('SOTIENCANCOC'),
                    TRANG_THAI_P = 'Trống',  # Mặc định trạng thái là 'Trống'
                    DIEN_TICH=data.get('DIEN_TICH', ''),
                    MO_TA_P = data.get('MO_TA_P', ''),
                )

            messages.success(request, 'Thêm nhiều phòng trọ thành công.')
            return redirect('phongtro:phongtro_list')

        elif loai == 'single':
            PhongTro.objects.create(
                MA_LOAI_PHONG_id=data.get('MA_LOAI_PHONG'),
                MA_KHU_VUC_id=data.get('MA_KHU_VUC'),
                TEN_PHONG=data.get('TEN_PHONG'),
                GIA_PHONG=data.get('GIA_PHONG'),
                SO_NGUOI_TOI_DA=data.get('SO_NGUOI_TOI_DA'),
                SO_TIEN_CAN_COC=data.get('SOTIENCANCOC'),
                TRANG_THAI_P='Đang trống',  # Mặc định trạng thái là 'Đang trống'
                DIEN_TICH=data.get('DIEN_TICH', ''),
                MO_TA_P=data.get('MO_TA_P', ''),
            )
            messages.success(request, 'Thêm phòng trọ thành công.')
            return redirect('phongtro:phongtro_list')

        else:
            messages.error(request, 'Loại hành động không hợp lệ.')
            return redirect(request.META.get('HTTP_REFERER', 'phongtro:them_phongtro'))

    return redirect('phongtro:phongtro_list')

@require_POST
def xoa_phong_tro(request, ma_phong_tro):
    phong_tro = get_object_or_404(PhongTro, MA_PHONG=ma_phong_tro)

    # Kiểm tra phòng có hợp đồng hiệu lực không
    hop_dong_hieu_luc = HopDong.objects.filter(
        MA_PHONG=phong_tro,
        TRANG_THAI_HD__in=['Hiệu lực', 'Đang thực hiện']
    ).exists()

    # Nếu có hợp đồng và không có xác nhận xóa từ phía người dùng
    if hop_dong_hieu_luc and not request.POST.get('confirm_delete'):
        messages.error(request, f"Phòng '{phong_tro.TEN_PHONG}' đang có hợp đồng hiệu lực. Không thể xóa.")
        return redirect('phongtro:phongtro_list')  # Đổi lại route phù hợp

    try:
        with transaction.atomic():
            phong_tro.delete()
            messages.success(request, f"Phòng '{phong_tro.TEN_PHONG}' đã được xóa thành công.")
    except Exception as e:
        messages.error(request, f"Lỗi khi xóa phòng trọ: {str(e)}")

    return redirect('phongtro:phongtro_list')  # Đổi lại route phù hợp

def view_coc_giu_cho(request, ma_phong):
    phong_tro = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Lấy dữ liệu từ form
                ngay_coc_phong = request.POST.get('NGAY_COC_PHONG')
                ngay_du_kien_vao = request.POST.get('NGAY_DU_KIEN_VAO')
                tien_coc_phong = request.POST.get('TIEN_COC_PHONG')
                ho_ten_kt = request.POST.get('HO_TEN_KT')
                sdt_kt = request.POST.get('SDT_KT')
                email_kt = request.POST.get('EMAIL_KT') or None
                ghi_chu_cp = request.POST.get('GHI_CHU_CP') or None
                
                # Kiểm tra các trường bắt buộc
                if not all([ngay_coc_phong, ngay_du_kien_vao, ho_ten_kt, sdt_kt]):
                    raise ValueError('Vui lòng điền đầy đủ các trường bắt buộc.')
                
                # Tạo tài khoản mặc định
                tai_khoan = TaiKhoan.create_tai_khoan_mac_dinh()
                
                # Tạo khách thuê
                khach_thue = KhachThue.create_khach_thue(
                    tai_khoan_obj=tai_khoan,
                    ho_ten_kt=ho_ten_kt,
                    sdt_kt=sdt_kt,
                    email_kt=email_kt
                )
                # return JsonResponse(dict(request.POST))
                # Tạo cọc phòng
                coc_phong = CocPhong.tao_coc_phong(
                    phong=phong_tro,
                    khach_thue=khach_thue,
                    tien_coc_phong=float(tien_coc_phong),
                    ngay_coc_phong=ngay_coc_phong
                )
                
                # Cập nhật thêm thông tin cọc phòng
                coc_phong.cap_nhat_coc_phong(
                    ngay_du_kien_vao=ngay_du_kien_vao,
                    ghi_chu_cp=ghi_chu_cp
                )
                
                messages.success(request, 'Thêm cọc phòng thành công!')
                return redirect('phongtro:phongtro_list') # Điều hướng đến trang danh sách phòng trọ
                
        except (ValueError, ValidationError) as e:
            messages.error(request, str(e))
            form_data = request.POST
            # return JsonResponse(str(e), safe=False)
            # return JsonResponse(dict(request.POST))
            return render(request, 'admin/phongtro/cocphong.html', {
                'phong_tro': phong_tro,
                'form_data': form_data
            })
    return render(request, 'admin/phongtro/cocphong.html', {
        'phong_tro': phong_tro,
        'form_data': {'TIEN_COC_PHONG': phong_tro.GIA_PHONG},
    })
def view_lap_hop_dong(request, ma_phong):
    """View hiển thị trang lập hợp đồng cho phòng trọ"""
    phong_tro = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Xử lý tạo hợp đồng mới
                # Xử lý số thành viên an toàn
                so_thanh_vien = request.POST.get('SO_THANH_VIEN_TOI_DA')
                if so_thanh_vien:
                    try:
                        so_thanh_vien = int(so_thanh_vien)
                    except (ValueError, TypeError):
                        so_thanh_vien = 1  # Giá trị mặc định
                else:
                    so_thanh_vien = 1
                
                # Xử lý giá cọc an toàn
                gia_coc = request.POST.get('GIA_COC_HD')
                if gia_coc:
                    try:
                        gia_coc = float(gia_coc)
                    except (ValueError, TypeError):
                        gia_coc = 0.00
                else:
                    gia_coc = 0.00
                
                hop_dong_data = {
                    'MA_PHONG': ma_phong,
                    'MA_KHACH_THUE': request.POST.get('MA_KHACH_THUE'),
                    'HO_TEN_KT': request.POST.get('HO_TEN_KT'),
                    'SDT_KT': request.POST.get('SDT_KT'),
                    'NGAY_SINH_KT': request.POST.get('NGAY_SINH_KT'),
                    'GIOI_TINH_KT': request.POST.get('GIOI_TINH_KT'),
                    'TAI_KHOAN': request.POST.get('TAI_KHOAN'),
                    'MAT_KHAU': request.POST.get('MAT_KHAU'),
                    'NGAY_LAP_HD': request.POST.get('NGAY_LAP_HD'),
                    'THOI_HAN_HD': request.POST.get('THOI_HAN_HD'),
                    'NGAY_NHAN_PHONG': request.POST.get('NGAY_NHAN_PHONG'),
                    'NGAY_TRA_PHONG': request.POST.get('NGAY_TRA_PHONG'),
                    'SO_THANH_VIEN_TOI_DA': so_thanh_vien,
                    'GIA_THUE': request.POST.get('GIA_THUE') or phong_tro.GIA_PHONG,
                    'NGAY_THU_TIEN': request.POST.get('NGAY_THU_TIEN'),
                    'THOI_DIEM_THANH_TOAN': request.POST.get('THOI_DIEM_THANH_TOAN'),
                    'CHU_KY_THANH_TOAN': request.POST.get('CHU_KY_THANH_TOAN'),
                    'GHI_CHU_HD': request.POST.get('GHI_CHU_HD'),
                    'GIA_COC_HD': gia_coc,
                }
                
                
                # Tạo hợp đồng
                hop_dong = HopDong.tao_hop_dong(hop_dong_data)
                
                # Xử lý tài sản bàn giao từ form mới
                ds_tai_san_ban_giao = []
                
                # Lấy tài sản từ checkbox trong form
                tai_san_keys = [key for key in request.POST.keys() if key.startswith('taisan[') and key.endswith('][MA_TAI_SAN]')]
                
                for key in tai_san_keys:
                    ma_tai_san = request.POST.get(key)
                    # Lấy index từ key để lấy số lượng tương ứng
                    index = key.split('[')[1].split(']')[0]
                    so_luong_key = f'taisan[{index}][so_luong]'
                    so_luong = request.POST.get(so_luong_key, 1)
                    
                    if ma_tai_san:
                        ds_tai_san_ban_giao.append({
                            'MA_TAI_SAN': ma_tai_san,
                            'SO_LUONG': so_luong
                        })
                
                # Xử lý tài sản tùy chỉnh
                i = 0
                while request.POST.get(f'custom_asset_name_{i}'):
                    ten_tai_san = request.POST.get(f'custom_asset_name_{i}')
                    tinh_trang = request.POST.get(f'custom_asset_condition_{i}', 'Tốt')
                    
                    if ten_tai_san:
                        # Tạo hoặc lấy tài sản
                        from .models import TAISAN
                        tai_san = TAISAN.tao_tai_san_tu_ten(ten_tai_san)
                        
                        ds_tai_san_ban_giao.append({
                            'MA_TAI_SAN': tai_san.MA_TAI_SAN,
                            'SO_LUONG': 1,
                            'TINH_TRANG': tinh_trang
                        })
                    i += 1
                
                # Tạo tài sản bàn giao
                if ds_tai_san_ban_giao:
                    from .models import TAISANBANGIAO
                    TAISANBANGIAO.tao_danh_sach_tai_san_ban_giao(hop_dong, ds_tai_san_ban_giao)
                
                # Xử lý dịch vụ (nếu có)
                ds_dich_vu = []
                dichvu_keys = [key for key in request.POST.keys() if key.startswith('dichvu_')]
                for key in dichvu_keys:
                    ma_dv = key.split('_')[1]
                    if request.POST.get(key):  # Nếu checkbox được check
                        dich_vu_data = {'MA_DICH_VU': ma_dv}
                        
                        # Kiểm tra loại dịch vụ để lấy đúng dữ liệu
                        chiso_moi = request.POST.get(f'chiso_moi_{ma_dv}')
                        so_luong = request.POST.get(f'soluong_{ma_dv}')
                        
                        if chiso_moi:  # Dịch vụ tính theo chỉ số
                            dich_vu_data['CHI_SO_MOI'] = chiso_moi
                            dich_vu_data['SO_LUONG'] = 0  # Không cần số lượng cho dịch vụ chỉ số
                        elif so_luong:  # Dịch vụ cố định
                            dich_vu_data['SO_LUONG'] = so_luong
                            dich_vu_data['CHI_SO_MOI'] = None
                        else:
                            dich_vu_data['SO_LUONG'] = 1  # Mặc định
                            dich_vu_data['CHI_SO_MOI'] = None
                            
                        ds_dich_vu.append(dich_vu_data)
                
                if ds_dich_vu:
                    ChiSoDichVu.tao_danh_sach_chi_so(hop_dong, ds_dich_vu)
                
                messages.success(request, f'Tạo hợp đồng thành công! Mã hợp đồng: {hop_dong.MA_HOP_DONG}')
                return redirect('phongtro:phongtro_list')
                
        except Exception as e:
            messages.error(request, f'Lỗi khi tạo hợp đồng: {str(e)}')
            return redirect('phongtro:lap_hop_dong', ma_phong=ma_phong)
    
     # Ví dụ: lấy danh sách phòng thuộc nhà trọ có mã là 1
    phong_tros = PhongTro.lay_phong_theo_ma_nha_tro(1)
    phong_tro = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
    
    # Lấy tài sản phòng
    taisanphong_list = TAISANPHONG.objects.filter(MA_PHONG=ma_phong).select_related('MA_TAI_SAN')

    # Sử dụng helper function chung từ dichvu app để lấy dịch vụ với chỉ số
    from apps.dichvu.admin_views import get_dichvu_with_chiso_for_phong
    lichsu_dichvu_with_chiso = get_dichvu_with_chiso_for_phong(phong_tro)
    coc_phong = CocPhong.objects.filter(
            MA_PHONG_id=ma_phong,
            TRANG_THAI_CP__in=['Đã cọc', 'Chờ xác nhận']  # Điều chỉnh trạng thái theo yêu cầu
        ).select_related('MA_KHACH_THUE').first()

    # return JsonResponse(dict(lichsu_dichvu))


    # Lấy danh sách khu vực để hiển thị dropdown
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1)
    
    return render(request, 'admin/hopdong/themsua_hopdong.html', {
        'phong_tros': phong_tros,
        'phong_tro': phong_tro,
        'lichsu_dichvu_with_chiso': lichsu_dichvu_with_chiso,
        'taisanphong_list': taisanphong_list,
        'coc_phong': coc_phong,
        'khu_vucs': khu_vucs,
        })








def ghi_so_dich_vu(request, ma_phong_tro):
    phong_tro = get_object_or_404(PhongTro, MA_PHONG=ma_phong_tro)
    lichsu_dichvu = LichSuApDungDichVu.objects.filter(
            MA_KHU_VUC=phong_tro.MA_KHU_VUC,
            NGAY_HUY_DV__isnull=True
        ).select_related('MA_DICH_VU')
    taisanphong_list = TAISANPHONG.objects.filter(MA_PHONG=ma_phong_tro).select_related('MA_TAI_SAN')

    # Tạo danh sách dịch vụ với chỉ số mới nhất
    lichsu_dichvu_with_chiso = []
    for lichsu in lichsu_dichvu:
        latest_chiso = ChiSoDichVu.objects.filter(
            MA_DICH_VU=lichsu.MA_DICH_VU,
            MA_PHONG=phong_tro
        ).order_by('-NGAY_GHI_CS').first()
        lichsu_dichvu_with_chiso.append({
            'lichsu': lichsu,
            'latest_chiso': latest_chiso
        })
    context = {    
        'phong_tro': phong_tro,
        'lichsu_dichvu_with_chiso': lichsu_dichvu_with_chiso,
        'taisanphong_list': taisanphong_list,
    }
    
    return render(request, 'admin/phongtro/ghiso_dichvu.html', context)


# ==================== QUẢN LÝ TIN ĐĂNG PHÒNG ====================

def dang_tin_list(request):
    """Danh sách tin đăng phòng"""
    # Lấy tham số tìm kiếm và bộ lọc
    keyword = request.GET.get('keyword', '')
    trang_thai = request.GET.get('trang_thai', '')
    ma_khu_vuc = request.GET.get('ma_khu_vuc', '')
    
    # Lấy danh sách tin đăng
    tin_dang_list = DangTinPhong.objects.select_related(
        'MA_PHONG', 
        'MA_PHONG__MA_KHU_VUC',
        'MA_PHONG__MA_LOAI_PHONG'
    ).prefetch_related('hinh_anh')
    
    # Áp dụng bộ lọc
    if keyword:
        tin_dang_list = tin_dang_list.filter(
            Q(MA_PHONG__TEN_PHONG__icontains=keyword) |
            Q(MA_PHONG__MA_KHU_VUC__TEN_KHU_VUC__icontains=keyword)
        )
    
    if trang_thai:
        tin_dang_list = tin_dang_list.filter(TRANG_THAI=trang_thai)
    
    if ma_khu_vuc:
        tin_dang_list = tin_dang_list.filter(MA_PHONG__MA_KHU_VUC=ma_khu_vuc)
    
    # Phân trang
    paginator = Paginator(tin_dang_list, 12)
    page_number = request.GET.get('page', 1)
    tin_dang_page = paginator.get_page(page_number)
    
    # Lấy danh sách khu vực cho filter
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1)
    
    context = {
        'tin_dang_list': tin_dang_page,
        'khu_vucs': khu_vucs,
        'keyword': keyword,
        'trang_thai': trang_thai,
        'ma_khu_vuc': ma_khu_vuc,
        'trang_thai_choices': DangTinPhong._meta.get_field('TRANG_THAI').choices,
    }
    
    return render(request, 'admin/dangtin/dang_tin_list.html', context)


def dang_tin_create(request):
    """Tạo tin đăng mới"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Lấy dữ liệu từ form
                ma_phong = request.POST.get('ma_phong')
                tieu_de = request.POST.get('tieu_de')
                mo_ta_tin = request.POST.get('mo_ta_tin')
                ngay_het_hang_tin = request.POST.get('ngay_het_hang_tin')
                sdt_lien_he = request.POST.get('sdt_lien_he')
                email_lien_he = request.POST.get('email_lien_he')
                
                # Validation
                if not ma_phong:
                    messages.error(request, 'Vui lòng chọn phòng.')
                    return redirect('admin_phongtro:dang_tin_create')
                
                if not tieu_de or len(tieu_de.strip()) < 10:
                    messages.error(request, 'Tiêu đề tin đăng phải có ít nhất 10 ký tự.')
                    return redirect('admin_phongtro:dang_tin_create')
                
                if not sdt_lien_he:
                    messages.error(request, 'Vui lòng nhập số điện thoại liên hệ.')
                    return redirect('admin_phongtro:dang_tin_create')
                
                # Validation ngày hết hạn
                if ngay_het_hang_tin:
                    from datetime import datetime, date
                    try:
                        ngay_het_hang = datetime.strptime(ngay_het_hang_tin, '%Y-%m-%d').date()
                        if ngay_het_hang <= date.today():
                            messages.error(request, 'Ngày hết hạn tin phải sau ngày hiện tại.')
                            return redirect('admin_phongtro:dang_tin_create')
                    except ValueError:
                        messages.error(request, 'Định dạng ngày hết hạn không hợp lệ.')
                        return redirect('admin_phongtro:dang_tin_create')
                
                # Kiểm tra phòng có tồn tại và chưa có tin đăng
                phong = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
                if hasattr(phong, 'tin_dang'):
                    messages.error(request, f'Phòng {phong.TEN_PHONG} đã có tin đăng.')
                    return redirect('admin_phongtro:dang_tin_create')
                
                # Tạo tin đăng
                tin_dang_data = {
                    'MA_PHONG': phong,
                    'TIEU_DE': tieu_de.strip(),
                    'SDT_LIEN_HE': sdt_lien_he,
                    'EMAIL_LIEN_HE': email_lien_he,
                    'TRANG_THAI': 'DANG_HIEN_THI'
                }
                
                # Thêm mô tả nếu có
                if mo_ta_tin:
                    tin_dang_data['MO_TA_TIN'] = mo_ta_tin.strip()
                
                # Thêm ngày hết hạn nếu có
                if ngay_het_hang_tin:
                    tin_dang_data['NGAY_HET_HANG_TIN'] = ngay_het_hang
                
                tin_dang = DangTinPhong.objects.create(**tin_dang_data)
                
                # Xử lý upload hình ảnh
                hinh_anhs = request.FILES.getlist('hinh_anh')
                if not hinh_anhs:
                    tin_dang.delete()
                    messages.error(request, 'Phải có ít nhất 1 hình ảnh để đăng tin.')
                    return redirect('admin_phongtro:dang_tin_create')
                
                # Lưu hình ảnh
                for index, hinh_anh in enumerate(hinh_anhs):
                    HinhAnhTinDang.objects.create(
                        MA_TIN_DANG=tin_dang,
                        HINH_ANH=hinh_anh,
                        THU_TU=index + 1,
                        MO_TA=f'Hình ảnh {index + 1}'
                    )
                
                messages.success(request, f'Đã tạo tin đăng cho phòng {phong.TEN_PHONG}.')
                return redirect('admin_phongtro:dang_tin_list')
                
        except Exception as e:
            messages.error(request, f'Lỗi khi tạo tin đăng: {str(e)}')
    
    # Lấy danh sách phòng chưa có tin đăng và trạng thái "Trống"
    phong_chua_dang = PhongTro.objects.filter(
        tin_dang__isnull=True,
        TRANG_THAI_P='Trống'
    ).select_related('MA_KHU_VUC', 'MA_LOAI_PHONG')
    
    # Lấy danh sách khu vực cho filter
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('TEN_KHU_VUC')
    
    context = {
        'phong_chua_dang': phong_chua_dang,
        'khu_vucs': khu_vucs,
    }
    
    return render(request, 'admin/dangtin/dang_tin_create.html', context)


def dang_tin_edit(request, ma_tin_dang):
    """Chỉnh sửa tin đăng"""
    tin_dang = get_object_or_404(DangTinPhong, MA_TIN_DANG=ma_tin_dang)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Cập nhật thông tin tin đăng
                tieu_de = request.POST.get('tieu_de', '').strip()
                if tieu_de and len(tieu_de) >= 10:
                    tin_dang.TIEU_DE = tieu_de
                
                mo_ta_tin = request.POST.get('mo_ta_tin', '').strip()
                tin_dang.MO_TA_TIN = mo_ta_tin if mo_ta_tin else None
                
                ngay_het_hang_tin = request.POST.get('ngay_het_hang_tin')
                if ngay_het_hang_tin:
                    from datetime import datetime, date
                    try:
                        ngay_het_hang = datetime.strptime(ngay_het_hang_tin, '%Y-%m-%d').date()
                        if ngay_het_hang > date.today():
                            tin_dang.NGAY_HET_HANG_TIN = ngay_het_hang
                    except ValueError:
                        pass  # Giữ nguyên giá trị cũ nếu format không hợp lệ
                
                tin_dang.SDT_LIEN_HE = request.POST.get('sdt_lien_he', tin_dang.SDT_LIEN_HE)
                tin_dang.EMAIL_LIEN_HE = request.POST.get('email_lien_he', tin_dang.EMAIL_LIEN_HE)
                tin_dang.TRANG_THAI = request.POST.get('trang_thai', tin_dang.TRANG_THAI)
                tin_dang.save()
                
                # Xử lý hình ảnh mới nếu có
                hinh_anhs = request.FILES.getlist('hinh_anh')
                if hinh_anhs:
                    # Xóa hình ảnh cũ
                    tin_dang.hinh_anh.all().delete()
                    
                    # Lưu hình ảnh mới
                    for index, hinh_anh in enumerate(hinh_anhs):
                        HinhAnhTinDang.objects.create(
                            MA_TIN_DANG=tin_dang,
                            HINH_ANH=hinh_anh,
                            THU_TU=index + 1,
                            MO_TA=f'Hình ảnh {index + 1}'
                        )
                
                messages.success(request, 'Đã cập nhật tin đăng.')
                return redirect('admin_phongtro:dang_tin_list')
                
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật tin đăng: {str(e)}')
    
    context = {
        'tin_dang': tin_dang,
        'trang_thai_choices': DangTinPhong._meta.get_field('TRANG_THAI').choices,
    }
    
    return render(request, 'admin/dangtin/dang_tin_edit.html', context)


@require_POST
def dang_tin_delete(request, ma_tin_dang):
    """Xóa tin đăng"""
    try:
        tin_dang = get_object_or_404(DangTinPhong, MA_TIN_DANG=ma_tin_dang)
        ten_phong = tin_dang.MA_PHONG.TEN_PHONG
        tin_dang.delete()
        messages.success(request, f'Đã xóa tin đăng phòng {ten_phong}.')
    except Exception as e:
        messages.error(request, f'Lỗi khi xóa tin đăng: {str(e)}')
    
    return redirect('admin_phongtro:dang_tin_list')


@require_POST
def dang_tin_toggle_status(request, ma_tin_dang):
    """Chuyển đổi trạng thái tin đăng (hiển thị/ẩn)"""
    try:
        tin_dang = get_object_or_404(DangTinPhong, MA_TIN_DANG=ma_tin_dang)
        
        if tin_dang.TRANG_THAI == 'DANG_HIEN_THI':
            tin_dang.TRANG_THAI = 'DA_AN'
            action = 'ẩn'
        else:
            tin_dang.TRANG_THAI = 'DANG_HIEN_THI'
            action = 'hiển thị'
        
        tin_dang.save()
        messages.success(request, f'Đã {action} tin đăng.')
        
    except Exception as e:
        messages.error(request, f'Lỗi khi thay đổi trạng thái: {str(e)}')
    
    return redirect('admin_phongtro:dang_tin_list')


def dang_tin_detail(request, ma_tin_dang):
    """Chi tiết tin đăng"""
    tin_dang = get_object_or_404(
        DangTinPhong.objects.select_related(
            'MA_PHONG',
            'MA_PHONG__MA_KHU_VUC',
            'MA_PHONG__MA_LOAI_PHONG'
        ).prefetch_related('hinh_anh'),
        MA_TIN_DANG=ma_tin_dang
    )
    
    context = {
        'tin_dang': tin_dang,
    }
    
    return render(request, 'admin/dangtin/dang_tin_detail.html', context)


def lay_phong_kha_dung(request):
    """
    AJAX view để lấy danh sách phòng khả dụng theo khu vực
    """
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập'})
    
    khu_vuc_id = request.GET.get('khu_vuc_id')
    if not khu_vuc_id:
        return JsonResponse({'success': False, 'message': 'Thiếu mã khu vực'})
    
    try:
        # Lấy phòng chưa có hợp đồng hoạt động hoặc đang trống
        phong_tros = PhongTro.objects.filter(
            MA_KHU_VUC=khu_vuc_id
        ).exclude(
            # Loại bỏ phòng có hợp đồng đang hoạt động
            hopdong__TRANG_THAI_HD__in=['Đang hoạt động', 'Chờ xác nhận', 'Đã xác nhận']
        ).select_related('MA_LOAI_PHONG', 'MA_KHU_VUC')
        
        # Serialize data
        phong_data = []
        for phong in phong_tros:
            phong_data.append({
                'MA_PHONG': phong.MA_PHONG,
                'TEN_PHONG': phong.TEN_PHONG,
                'TRANG_THAI_P': phong.TRANG_THAI_P,
                'GIA_PHONG': float(phong.GIA_PHONG) if phong.GIA_PHONG else 0,
                'SO_NGUOI_TOI_DA': phong.SO_NGUOI_TOI_DA,
                'SO_TIEN_CAN_COC': float(phong.SO_TIEN_CAN_COC) if phong.SO_TIEN_CAN_COC else 0,
            })
        
        return JsonResponse({
            'success': True,
            'phong_tros': phong_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })


def lay_thong_tin_phong(request):
    """
    AJAX view để lấy thông tin chi tiết phòng
    """
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập'})
    
    ma_phong = request.GET.get('ma_phong')
    if not ma_phong:
        return JsonResponse({'success': False, 'message': 'Thiếu mã phòng'})
    
    try:
        phong = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
        
        phong_info = {
            'MA_PHONG': phong.MA_PHONG,
            'TEN_PHONG': phong.TEN_PHONG,
            'GIA_PHONG': float(phong.GIA_PHONG) if phong.GIA_PHONG else 0,
            'SO_NGUOI_TOI_DA': phong.SO_NGUOI_TOI_DA or 1,
            'SO_TIEN_CAN_COC': float(phong.SO_TIEN_CAN_COC) if phong.SO_TIEN_CAN_COC else 0,
            'DIEN_TICH': float(phong.DIEN_TICH) if phong.DIEN_TICH else 0,
            'MO_TA_P': phong.MO_TA_P or '',
            'TRANG_THAI_P': phong.TRANG_THAI_P,
        }
        
        return JsonResponse({
            'success': True,
            'phong_info': phong_info
        })
        
    except PhongTro.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Phòng không tồn tại'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })