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


def khachthue_list(request):
    # Build queryset with optimized relations
    queryset = KhachThue.objects.select_related('MA_TAI_KHOAN').prefetch_related(
        Prefetch(
            'lichsuhopdong',
            queryset=LichSuHopDong.objects.select_related('MA_HOP_DONG__MA_PHONG').filter(
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

    # Group by room
    grouped_by_room = {}
    for khach_thue in queryset:
        for lich_su in khach_thue.lichsuhopdong.all():
            hop_dong = lich_su.MA_HOP_DONG
            if hop_dong.TRANG_THAI_HD == 'Đang hoạt động':
                room_id = hop_dong.MA_PHONG_id
                room_name = hop_dong.MA_PHONG.TEN_PHONG
                if room_id not in grouped_by_room:
                    grouped_by_room[room_id] = {
                        'room_name': room_name,
                        'tenants': []
                    }
                grouped_by_room[room_id]['tenants'].append({
                    'khach_thue': khach_thue,
                    'lich_su': lich_su,
                    'hop_dong': hop_dong
                })

    context = {
        'grouped_by_room': grouped_by_room,
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
            # Tạo tài khoản mới
            tai_khoan_obj = TaiKhoan.create_tai_khoan(tai_khoan, mat_khau)

            # Tạo khách thuê mới
            khach_thue = KhachThue.create_khach_thue(
                tai_khoan_obj, ho_ten_kt, sdt_kt, email_kt, nghe_nghiep, avatar
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

    return render(request, 'admin/khachthue/themsua_khachthue.html', {'phongtro_list': phongtro_list})
def sua_khach_thue(request, ma_khach_thue, maphong=None):
    khach_thue = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue)
    # Lấy danh sách phòng trọ có hợp đồng đang hoạt động
    phongtro_list = PhongTro.objects.filter( hopdong__TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc']).distinct()
    # Lấy hợp đồng nếu có mã phòng
    hop_dong = None
    lichsuhopdong = None
    if maphong:
        hop_dong = HopDong.objects.filter( 
            MA_PHONG=maphong, TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc']
        ).first()
        lichsuhopdong = LichSuHopDong.objects.filter(
            MA_KHACH_THUE=khach_thue,
            MA_HOP_DONG=hop_dong
        ).first()   
    hopdong = hop_dong if hop_dong else None

    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            ho_ten_kt = request.POST.get('HOTENKHACHTHUE')
            sdt_kt = request.POST.get('SODIENTHOAIKHACHTHUE')
            email_kt = request.POST.get('EMAILKHACHTHUE')
            nghe_nghiep = request.POST.get('NGHENGHIEP')
            ma_phong = request.POST.get('MA_PHONG')
            moi_quan_he = request.POST.get('MOI_QUAN_HE')
            ngay_tham_gia = request.POST.get('NGAY_THAM_GIA')
            avatar = request.FILES.get('AVATAR')
            tai_khoan = request.POST.get('TAI_KHOAN')
            mat_khau = request.POST.get('MAT_KHAU')
            ma_lich_su_hd = request.POST.get('MA_LS_HOP_DONG')

            # Cập nhật tài khoản
            khach_thue.MA_TAI_KHOAN.update_tai_khoan(tai_khoan, mat_khau)

            # Cập nhật khách thuê
            khach_thue.update_khach_thue(ho_ten_kt, sdt_kt, email_kt, nghe_nghiep, avatar)

            # Cập nhật lịch sử hợp đồng
            if ma_phong and moi_quan_he:
                hop_dong = HopDong.objects.filter(
                    MA_PHONG=ma_phong,
                    TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc'],
                ).first()              
                LichSuHopDong.create_or_update_lich_su_hop_dong(
                    khach_thue, hop_dong, moi_quan_he, ngay_tham_gia, ma_lich_su_hd
                )

            messages.success(request, 'Cập nhật thông tin khách thuê thành công.')
            return redirect('khachthue:khachthue_list')

        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'admin/khachthue/themsua_khachthue.html', {
                'khachthue': khach_thue,
                'phongtro_list': phongtro_list,
                'lichsuhopdong': lichsuhopdong,
                'hopdong': hopdong
            })
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return render(request, 'admin/khachthue/themsua_khachthue.html', {
                'khachthue': khach_thue,
                'phongtro_list': phongtro_list,
                'lichsuhopdong': lichsuhopdong,
                'hopdong': hopdong
            })

    return render(request, 'admin/khachthue/themsua_khachthue.html', {
        'khachthue': khach_thue,
        'phongtro_list': phongtro_list,
        'lichsuhopdong': lichsuhopdong,
        'hopdong': hopdong
    })
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

def view_cccd(request, ma_khach_thue=None):
    khach_thue = None
    cccd_cmnd = None

    if ma_khach_thue:
        khach_thue = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue)
        cccd_cmnd = CccdCmnd.objects.filter(MA_KHACH_THUE=khach_thue).first()

    if request.method == 'POST':
        try:
            if ma_khach_thue:
                khach_thue.update_cccd_cmnd(
                    so_cmnd_cccd=request.POST.get('CMNDORCCCD'),
                    ma_cccd = cccd_cmnd.MA_CCCD if cccd_cmnd else None,
                    ngay_cap=request.POST.get('NGAY_CAP') or None,
                    anh_mat_truoc=request.FILES.get('ANH_MAT_TRUOC'),
                    anh_mat_sau=request.FILES.get('ANH_MAT_SAU'),
                    gioi_tinh_kt=request.POST.get('GIOITINHKHACHTHUE'),
                    ngay_sinh_kt=request.POST.get('NGAYSINHKHACHTHUE')or None,
                    que_quan=request.POST.get('QUEQUAN'),
                    dia_chi_thuong_tru=request.POST.get('DIA_CHI_THUONG_TRU')
                )
                messages.success(request, 'Cập nhật thông tin CCCD/CMND thành công.')
            else:
                # Logic thêm mới khách thuê và CCCD (cần bổ sung thêm trường HO_TEN_KT, SDT_KT trong form)
                raise ValueError('Chức năng thêm mới chưa được triển khai.')
            return redirect('khachthue:khachthue_list')
        except ValueError as e:
            messages.error(request, f'Lỗi: {str(e)}')
        except Exception as e:
            messages.error(request, f'Đã xảy ra lỗi không xác định: {str(e)}')

    return render(request, 'admin/khachthue/themsua_cccd.html', {
        'khachthue': khach_thue,
        'cccd_cmnd': cccd_cmnd,
    })
