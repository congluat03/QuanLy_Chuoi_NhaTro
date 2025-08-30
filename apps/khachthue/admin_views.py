from django.shortcuts import render, redirect
from django.db.models import Q
from .models import KhachThue, CccdCmnd
from apps.hopdong.models import LichSuHopDong
from django.db.models import Prefetch
from django.contrib import messages
from django.shortcuts import get_object_or_404
from apps.thanhvien.models import TaiKhoan
from apps.phongtro.models import PhongTro
from apps.hopdong.models import HopDong
from django.db import transaction
from apps.nhatro.models import KhuVuc


def khachthue_list(request):
    # Build queryset with optimized relations
    queryset = KhachThue.objects.select_related('MA_TAI_KHOAN').prefetch_related(
        Prefetch(
            'lichsuhopdong',
            queryset=LichSuHopDong.objects.select_related(
                'MA_HOP_DONG__MA_PHONG__MA_KHU_VUC'  # Include khu vuc
            ).filter(
                NGAY_ROI_DI__isnull=True  # Active tenants
            )
        ),
        Prefetch(
            'cccd_cmnd',
            queryset=CccdCmnd.objects.all()
        )
    )

    # Apply filters
    options = request.GET.getlist('options[]')
    if 'Da_dang_ky' in options or 'Chua_dang_ky' in options:
        # Placeholder: Implement temporary residence status filtering if field exists
        pass
    if 'Da_nop_giay_to' in options:
        queryset = queryset.filter(TRANG_THAI_KT='Đã kích hoạt')
    if 'Chua_nop_giay_to' in options:
        queryset = queryset.filter(TRANG_THAI_KT='Chưa kích hoạt')

    # Apply search
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(HO_TEN_KT__icontains=search_query) |
            Q(SDT_KT__icontains=search_query) |
            Q(EMAIL_KT__icontains=search_query)
        )
    
    # Group tenants by room for display - no pagination
    grouped_by_room = {}
    
    for khach_thue in queryset:
        for lich_su in khach_thue.lichsuhopdong.all():
            hop_dong = lich_su.MA_HOP_DONG
            if hop_dong.TRANG_THAI_HD == 'Đang hoạt động':
                room_id = hop_dong.MA_PHONG_id
                tenant_data = {
                    'khach_thue': khach_thue,
                    'lich_su': lich_su,
                    'hop_dong': hop_dong,
                    'room_id': room_id,
                    'room_name': hop_dong.MA_PHONG.TEN_PHONG,
                    'khu_vuc': hop_dong.MA_PHONG.MA_KHU_VUC
                }
                
                if room_id not in grouped_by_room:
                    grouped_by_room[room_id] = {
                        'room_name': hop_dong.MA_PHONG.TEN_PHONG,
                        'khu_vuc': hop_dong.MA_PHONG.MA_KHU_VUC,
                        'tenants': []
                    }
                grouped_by_room[room_id]['tenants'].append(tenant_data)

    # Count total tenants
    total_tenants = sum(len(room_data['tenants']) for room_data in grouped_by_room.values())
    
    # Get all khu vucs for filter dropdown
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')

    context = {
        'grouped_by_room': grouped_by_room,        # For both main table and sidebar
        'khu_vucs': khu_vucs,
        'all_tenants_count': total_tenants,
        'options': options,
        'search_query': search_query
    }
    return render(request, 'admin/khachthue/danhsach_khachthue.html', context)
def get_phongtro_list():
    return PhongTro.objects.filter(
        Q(hopdong__TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc'])  
    ).distinct()

def them_khach_thue(request):
    phongtro_list = get_phongtro_list()
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            ho_ten_kt = request.POST.get('HOTENKHACHTHUE')
            sdt_kt = request.POST.get('SODIENTHOAIKHACHTHUE')
            email_kt = request.POST.get('EMAILKHACHTHUE')
            tai_khoan = request.POST.get('TAI_KHOAN')
            mat_khau = request.POST.get('MAT_KHAU')
            nghe_nghiep = request.POST.get('NGHENGHIEP')
            ma_phong = request.POST.get('MA_PHONG')
            moi_quan_he = request.POST.get('MOI_QUAN_HE')
            ngay_tham_gia = request.POST.get('NGAY_THAM_GIA')
            avatar = request.FILES.get('AVATAR')
            
            # Debug: in ra console để kiểm tra
            print(f"Debug - Dữ liệu nhận được:")
            print(f"- ho_ten_kt: {ho_ten_kt}")
            print(f"- sdt_kt: {sdt_kt}")
            print(f"- tai_khoan: {tai_khoan}")
            print(f"- ma_phong: {ma_phong}")
            
            # Validate dữ liệu cần thiết
            if not ho_ten_kt or not sdt_kt or not tai_khoan or not mat_khau:
                messages.error(request, 'Vui lòng điền đầy đủ các trường bắt buộc.')
                return render(request, 'admin/khachthue/themsua_khachthue.html', {
                    'khu_vucs': khu_vucs, 
                    'phongtro_list': phongtro_list
                })
            
            if not ma_phong:
                messages.error(request, 'Vui lòng chọn phòng trước khi thêm khách thuê.')
                return render(request, 'admin/khachthue/themsua_khachthue.html', {
                    'khu_vucs': khu_vucs, 
                    'phongtro_list': phongtro_list
                })
            # Tạo tài khoản mới
            tai_khoan_obj = TaiKhoan.create_tai_khoan(tai_khoan, mat_khau)

            # Lấy thêm thông tin bổ sung
            ngay_sinh_kt = request.POST.get('NGAYSINHKHACHTHUE') or None
            gioi_tinh_kt = request.POST.get('GIOITINHKHACHTHUE') or None
            noi_sinh_kt = request.POST.get('NOISINHKHACHTHUE') or None
            
            # Tạo khách thuê mới
            khach_thue = KhachThue.create_khach_thue(
                tai_khoan_obj=tai_khoan_obj,
                ho_ten_kt=ho_ten_kt, 
                sdt_kt=sdt_kt, 
                email_kt=email_kt, 
                nghe_nghiep=nghe_nghiep, 
                avatar=avatar,
                ngay_sinh_kt=ngay_sinh_kt,
                gioi_tinh_kt=gioi_tinh_kt,
                noi_sinh_kt=noi_sinh_kt
            )
            # Xử lý lịch sử hợp đồng
            if ma_phong and moi_quan_he:
                hop_dong = HopDong.objects.filter(
                    MA_PHONG=ma_phong,
                    TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc']              
                ).first()
                if hop_dong:
                    LichSuHopDong.create_or_update_lich_su_hop_dong(khach_thue, hop_dong, moi_quan_he, ngay_tham_gia)

            messages.success(request, 'Thêm khách thuê thành công.')
            return redirect('khachthue:khachthue_list')

        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'admin/khachthue/themsua_khachthue.html', {'phongtro_list': phongtro_list})
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'admin/khachthue/themsua_khachthue.html', {'phongtro_list': phongtro_list})
    
    return render(request, 'admin/khachthue/themsua_khachthue.html', {'khu_vucs': khu_vucs, 'phongtro_list': phongtro_list})
def xoa_khach_thue(request, ma_khach_thue):
    khach_thue = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                khach_thue.delete_khach_thue()
                messages.success(request, 'Xóa khách thuê thành công.')
                return redirect('khachthue:khachthue_list')
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('khachthue:khachthue_list')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return redirect('khachthue:khachthue_list')
    
    messages.warning(request, 'Yêu cầu không hợp lệ.')
    return redirect('khachthue:khachthue_list')

def sua_thong_tin_khach_thue(request, ma_khach_thue):
    """Chỉnh sửa thông tin cá nhân của khách thuê - không liên quan đến hợp đồng"""
    khach_thue = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue)
    
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            ho_ten_kt = request.POST.get('HOTENKHACHTHUE')
            sdt_kt = request.POST.get('SODIENTHOAIKHACHTHUE')
            email_kt = request.POST.get('EMAILKHACHTHUE')
            nghe_nghiep = request.POST.get('NGHENGHIEP')
            ngay_sinh_kt = request.POST.get('NGAYSINHKHACHTHUE') or None
            gioi_tinh_kt = request.POST.get('GIOITINHKHACHTHUE') or None
            noi_sinh_kt = request.POST.get('NOISINHKHACHTHUE') or None
            avatar = request.FILES.get('AVATAR')
            
            # Debug: in ra console để kiểm tra
            print(f"Debug - Cập nhật thông tin khách thuê {ma_khach_thue}:")
            print(f"- ho_ten_kt: {ho_ten_kt}")
            print(f"- sdt_kt: {sdt_kt}")
            print(f"- email_kt: {email_kt}")
            
            # Validate dữ liệu cần thiết
            if not ho_ten_kt or not sdt_kt:
                messages.error(request, 'Vui lòng điền đầy đủ họ tên và số điện thoại.')
                return render(request, 'admin/khachthue/sua_khachthue.html', {'khachthue': khach_thue})
            
            # Cập nhật thông tin khách thuê
            khach_thue.update_khach_thue(
                ho_ten_kt=ho_ten_kt,
                sdt_kt=sdt_kt,
                email_kt=email_kt,
                nghe_nghiep=nghe_nghiep,
                avatar=avatar,
                ngay_sinh_kt=ngay_sinh_kt,
                gioi_tinh_kt=gioi_tinh_kt,
                noi_sinh_kt=noi_sinh_kt
            )

            messages.success(request, f'Cập nhật thông tin khách thuê "{ho_ten_kt}" thành công.')
            return redirect('khachthue:khachthue_list')

        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'admin/khachthue/sua_khachthue.html', {'khachthue': khach_thue})
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'admin/khachthue/sua_khachthue.html', {'khachthue': khach_thue})
    
    # GET request - hiển thị form
    return render(request, 'admin/khachthue/sua_khachthue.html', {'khachthue': khach_thue})

def view_cccd(request, ma_khach_thue):
    """Cập nhật thông tin CCCD/CMND - chỉ xử lý dữ liệu bảng CCCD"""
    khach_thue = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue)
    cccd_cmnd = CccdCmnd.objects.filter(MA_KHACH_THUE=khach_thue).first()

    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form - chỉ các trường thuộc bảng CCCD
            so_cmnd_cccd = request.POST.get('CMNDORCCCD')
            ngay_cap = request.POST.get('NGAY_CAP') or None
            dia_chi_thuong_tru = request.POST.get('DIA_CHI_THUONG_TRU')
            anh_mat_truoc = request.FILES.get('ANH_MAT_TRUOC')
            anh_mat_sau = request.FILES.get('ANH_MAT_SAU')
            
            # Debug: in ra console để kiểm tra
            print(f"Debug - Cập nhật CCCD cho khách thuê {ma_khach_thue}:")
            print(f"- so_cmnd_cccd: {so_cmnd_cccd}")
            print(f"- ngay_cap: {ngay_cap}")
            print(f"- dia_chi_thuong_tru: {dia_chi_thuong_tru}")
            
            # Validate dữ liệu cần thiết
            if not so_cmnd_cccd:
                messages.error(request, 'Vui lòng nhập số CCCD/CMND.')
                return render(request, 'admin/khachthue/cap_nhat_cccd.html', {
                    'khachthue': khach_thue,
                    'cccd_cmnd': cccd_cmnd,
                })
            
            # Validate số CCCD (9 hoặc 12 số)
            if not (len(so_cmnd_cccd) == 9 or len(so_cmnd_cccd) == 12) or not so_cmnd_cccd.isdigit():
                messages.error(request, 'Số CCCD/CMND phải là 9 hoặc 12 chữ số.')
                return render(request, 'admin/khachthue/cap_nhat_cccd.html', {
                    'khachthue': khach_thue,
                    'cccd_cmnd': cccd_cmnd,
                })
            
            # Cập nhật hoặc tạo mới CCCD - chỉ thông tin bảng CCCD
            if cccd_cmnd:
                # Cập nhật CCCD hiện có
                cccd_cmnd.SO_CMND_CCCD = so_cmnd_cccd
                if ngay_cap:
                    cccd_cmnd.NGAY_CAP = ngay_cap
                cccd_cmnd.DIA_CHI_THUONG_TRU = dia_chi_thuong_tru
                
                # Chỉ cập nhật ảnh nếu có upload mới
                if anh_mat_truoc:
                    cccd_cmnd.ANH_MAT_TRUOC = anh_mat_truoc
                if anh_mat_sau:
                    cccd_cmnd.ANH_MAT_SAU = anh_mat_sau
                    
                cccd_cmnd.save()
                messages.success(request, f'Cập nhật thông tin CCCD/CMND cho "{khach_thue.HO_TEN_KT}" thành công.')
            else:
                # Tạo mới CCCD
                if not anh_mat_truoc or not anh_mat_sau:
                    messages.error(request, 'Vui lòng upload ảnh mặt trước và mặt sau của CCCD/CMND.')
                    return render(request, 'admin/khachthue/cap_nhat_cccd.html', {
                        'khachthue': khach_thue,
                        'cccd_cmnd': cccd_cmnd,
                    })
                
                CccdCmnd.objects.create(
                    MA_KHACH_THUE=khach_thue,
                    SO_CMND_CCCD=so_cmnd_cccd,
                    NGAY_CAP=ngay_cap,
                    DIA_CHI_THUONG_TRU=dia_chi_thuong_tru,
                    ANH_MAT_TRUOC=anh_mat_truoc,
                    ANH_MAT_SAU=anh_mat_sau
                )
                messages.success(request, f'Thêm thông tin CCCD/CMND cho "{khach_thue.HO_TEN_KT}" thành công.')

            return redirect('khachthue:khachthue_list')
            
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'admin/khachthue/cap_nhat_cccd.html', {
                'khachthue': khach_thue,
                'cccd_cmnd': cccd_cmnd,
            })

    # GET request - hiển thị form
    return render(request, 'admin/khachthue/cap_nhat_cccd.html', {
        'khachthue': khach_thue,
        'cccd_cmnd': cccd_cmnd,
    })

def roi_di_chuyen_phong(request, ma_khach_thue):
    """Hiển thị giao diện rời đi/chuyển phòng cho khách thuê"""
    khach_thue = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue)
    
    # Lấy lịch sử hợp đồng hiện tại (chưa rời đi)
    lich_su_hop_dong = LichSuHopDong.objects.select_related(
        'MA_HOP_DONG__MA_PHONG'
    ).filter(
        MA_KHACH_THUE=khach_thue,
        NGAY_ROI_DI__isnull=True
    ).first()
    
    if not lich_su_hop_dong:
        messages.error(request, 'Khách thuê hiện không có hợp đồng đang hoạt động.')
        return redirect('khachthue:khachthue_list')
    
    # Kiểm tra khách thuê không phải chủ hợp đồng
    if lich_su_hop_dong.MOI_QUAN_HE == 'Chủ hợp đồng':
        messages.error(request, 'Chức năng này chỉ dành cho khách thuê không phải là chủ hợp đồng.')
        return redirect('khachthue:khachthue_list')
    
    # Lấy danh sách khu vực để chuyển phòng
    khu_vucs = KhuVuc.objects.all()
    
    return render(request, 'admin/khachthue/roi_di_chuyen_phong.html', {
        'khachthue': khach_thue,
        'lich_su_hop_dong': lich_su_hop_dong,
        'khu_vucs': khu_vucs,
    })

def roi_di(request, ma_khach_thue, ma_lich_su):
    """Xử lý khách thuê rời đi"""
    khach_thue = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue)
    lich_su_hop_dong = get_object_or_404(LichSuHopDong, MA_LICH_SU_HD=ma_lich_su)
    
    # Kiểm tra quyền hạn
    if lich_su_hop_dong.MA_KHACH_THUE != khach_thue:
        messages.error(request, 'Không có quyền thực hiện thao tác này.')
        return redirect('khachthue:khachthue_list')
    
    if lich_su_hop_dong.MOI_QUAN_HE == 'Chủ hợp đồng':
        messages.error(request, 'Chủ hợp đồng không thể sử dụng chức năng này.')
        return redirect('khachthue:khachthue_list')
    
    if request.method == 'POST':
        try:
            from datetime import datetime
            
            ngay_roi_di = request.POST.get('NGAY_ROI_DI')
            ly_do_roi_di = request.POST.get('LY_DO_ROI_DI')
            ghi_chu_roi_di = request.POST.get('GHI_CHU_ROI_DI')
            
            if not ngay_roi_di:
                messages.error(request, 'Vui lòng chọn ngày rời đi.')
                return redirect('khachthue:roi_di_chuyen_phong', ma_khach_thue=ma_khach_thue)
            
            # Chuyển đổi ngày
            ngay_roi_di_date = datetime.strptime(ngay_roi_di, '%Y-%m-%d').date()
            
            # Kiểm tra ngày rời đi không được trước ngày tham gia
            if ngay_roi_di_date < lich_su_hop_dong.NGAY_THAM_GIA:
                messages.error(request, 'Ngày rời đi không được trước ngày tham gia hợp đồng.')
                return redirect('khachthue:roi_di_chuyen_phong', ma_khach_thue=ma_khach_thue)
            
            with transaction.atomic():
                # Cập nhật thông tin rời đi
                lich_su_hop_dong.NGAY_ROI_DI = ngay_roi_di_date
                lich_su_hop_dong.save()
                
                messages.success(request, f'Đã cập nhật thông tin rời đi cho khách thuê {khach_thue.HO_TEN_KT}.')
                return redirect('khachthue:khachthue_list')
                
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return redirect('khachthue:roi_di_chuyen_phong', ma_khach_thue=ma_khach_thue)
    
    messages.error(request, 'Yêu cầu không hợp lệ.')
    return redirect('khachthue:khachthue_list')

def chuyen_phong(request, ma_khach_thue, ma_lich_su):
    """Xử lý khách thuê chuyển phòng"""
    khach_thue = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue)
    lich_su_hop_dong_cu = get_object_or_404(LichSuHopDong, MA_LICH_SU_HD=ma_lich_su)
    
    # Kiểm tra quyền hạn
    if lich_su_hop_dong_cu.MA_KHACH_THUE != khach_thue:
        messages.error(request, 'Không có quyền thực hiện thao tác này.')
        return redirect('khachthue:khachthue_list')
    
    if lich_su_hop_dong_cu.MOI_QUAN_HE == 'Chủ hợp đồng':
        messages.error(request, 'Chủ hợp đồng không thể sử dụng chức năng này.')
        return redirect('khachthue:khachthue_list')
    
    if request.method == 'POST':
        try:
            from datetime import datetime
            
            khu_vuc_moi = request.POST.get('KHU_VUC_MOI')
            phong_moi = request.POST.get('PHONG_MOI')
            ngay_chuyen = request.POST.get('NGAY_CHUYEN')
            moi_quan_he_moi = request.POST.get('MOI_QUAN_HE_MOI', 'Người ở cùng')
            ghi_chu_chuyen = request.POST.get('GHI_CHU_CHUYEN')
            
            if not all([khu_vuc_moi, phong_moi, ngay_chuyen]):
                messages.error(request, 'Vui lòng điền đầy đủ thông tin chuyển phòng.')
                return redirect('khachthue:roi_di_chuyen_phong', ma_khach_thue=ma_khach_thue)
            
            # Lấy phòng mới
            phong_moi_obj = get_object_or_404(PhongTro, MA_PHONG=phong_moi)
            
            # Kiểm tra phòng mới có hợp đồng đang hoạt động
            hop_dong_moi = HopDong.objects.filter(
                MA_PHONG=phong_moi_obj,
                TRANG_THAI_HD='Đang hoạt động'
            ).first()
            
            if not hop_dong_moi:
                messages.error(request, 'Phòng được chọn không có hợp đồng đang hoạt động.')
                return redirect('khachthue:roi_di_chuyen_phong', ma_khach_thue=ma_khach_thue)
            
            # Chuyển đổi ngày
            ngay_chuyen_date = datetime.strptime(ngay_chuyen, '%Y-%m-%d').date()
            
            with transaction.atomic():
                # 1. Đánh dấu rời khỏi phòng cũ
                lich_su_hop_dong_cu.NGAY_ROI_DI = ngay_chuyen_date
                lich_su_hop_dong_cu.save()
                
                # 2. Tạo lịch sử hợp đồng mới trong phòng mới
                lich_su_moi = LichSuHopDong.objects.create(
                    MA_HOP_DONG=hop_dong_moi,
                    MA_KHACH_THUE=khach_thue,
                    MOI_QUAN_HE=moi_quan_he_moi,
                    NGAY_THAM_GIA=ngay_chuyen_date,
                    NGAY_ROI_DI=None
                )
                
                messages.success(request, f'Đã chuyển khách thuê {khach_thue.HO_TEN_KT} sang phòng {phong_moi_obj.TEN_PHONG}.')
                return redirect('khachthue:khachthue_list')
                
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return redirect('khachthue:roi_di_chuyen_phong', ma_khach_thue=ma_khach_thue)
    
    messages.error(request, 'Yêu cầu không hợp lệ.')
    return redirect('khachthue:khachthue_list')

def search_khach_thue(request):
    """
    API endpoint để tìm kiếm khách thuê theo tên, SĐT hoặc CCCD
    """
    if not request.session.get('is_authenticated'):
        return JsonResponse({'success': False, 'message': 'Bạn cần đăng nhập'})
    
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'success': False, 'message': 'Vui lòng nhập ít nhất 2 ký tự'})
    
    try:
        # Tìm kiếm theo tên, SĐT hoặc CCCD
        khachthue_queryset = KhachThue.objects.select_related('cccd_cmnd').filter(
            Q(HO_TEN_KT__icontains=query) |
            Q(SDT_KT__icontains=query) |
            Q(cccd_cmnd__SO_CMND_CCCD__icontains=query)
        ).distinct()[:20]  # Giới hạn 20 kết quả
        
        results = []
        for khach_thue in khachthue_queryset:
            # Lấy thông tin CCCD nếu có
            cccd_info = None
            if hasattr(khach_thue, 'cccd_cmnd') and khach_thue.cccd_cmnd:
                cccd_info = khach_thue.cccd_cmnd.SO_CMND_CCCD
            
            results.append({
                'MA_KHACH_THUE': khach_thue.MA_KHACH_THUE,
                'HO_TEN_KT': khach_thue.HO_TEN_KT,
                'SDT_KT': khach_thue.SDT_KT,
                'GIOI_TINH_KT': khach_thue.GIOI_TINH_KT,
                'NGAY_SINH_KT': khach_thue.NGAY_SINH_KT.strftime('%Y-%m-%d') if khach_thue.NGAY_SINH_KT else None,
                'SO_CMND_CCCD': cccd_info
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        # Trả lỗi dưới dạng API
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            })
        # Hoặc hiển thị trên giao diện nếu không phải API call
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        return render(request, 'admin/khachthue/cap_nhat_cccd.html', {
            'khachthue': None,
            'cccd_cmnd': None,
        })
