from django.shortcuts import render, redirect
from django.db.models import Q
from .models import KhachThue, CccdCmnd
from apps.hopdong.models import LichSuHopDong
from django.db.models import Prefetch
from django.contrib import messages
from django.shortcuts import get_object_or_404
from apps.thanhvien.models import TaiKhoan
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
def view_them_khach_thue(request):
    if request.method == 'POST':
        # Create new KhachThue
        ma_tai_khoan_id = request.POST.get('MA_TAI_KHOAN')  # Assuming a field to select or input MA_TAI_KHOAN
        try:
            ma_tai_khoan = TaiKhoan.objects.get(pk=ma_tai_khoan_id)
        except TaiKhoan.DoesNotExist:
            messages.error(request, 'Tài khoản không tồn tại!')
            return render(request, 'admin/khachthue/themsua_khachthue.html', {'khachthue': None, 'cccd_cmnd': None})

        khachthue = KhachThue(
            MA_TAI_KHOAN=ma_tai_khoan,
            HO_TEN_KT=request.POST.get('HOTENKHACHTHUE'),
            SDT_KT=request.POST.get('SODIENTHOAIKHACHTHUE'),
            NGAY_SINH_KT=request.POST.get('NGAYSINHKHACHTHUE'),
            NOI_SINH_KT=request.POST.get('NOISINH'),
            GIOI_TINH_KT=request.POST.get('GIOITINHKHACHTHUE'),
            EMAIL_KT=request.POST.get('EMAILKHACHTHUE'),
            NGHE_NGHIEP=request.POST.get('NGHENGHIEP')
        )
        khachthue.save()

        # Create CccdCmnd if provided
        so_cmnd_cccd = request.POST.get('CMNDORCCCD')
        noi_cap = request.POST.get('NOICAP')
        if so_cmnd_cccd:
            CccdCmnd.objects.create(
                SO_CMND_CCCD=so_cmnd_cccd,
                MA_KHACH_THUE=khachthue,
                NOI_CAP=noi_cap
            )
        messages.success(request, 'Thêm khách thuê thành công!')
        return redirect('sua_khach_thue', ma_khach_thue=khachthue.MA_KHACH_THUE)

    context = {
        'khachthue': None,
        'cccd_cmnd': None
    }
    return render(request, 'admin/khachthue/themsua_khachthue.html', context)
def view_sua_thong_tin(request, ma_khach_thue):
    khachthue = get_object_or_404(KhachThue, MA_KHACH_THUE=ma_khach_thue)
    cccd_cmnd = khachthue.cccd_cmnd.first() if khachthue.cccd_cmnd.exists() else None

    if request.method == 'POST':
        # Update KhachThue
        khachthue.HO_TEN_KT = request.POST.get('HOTENKHACHTHUE')
        khachthue.SDT_KT = request.POST.get('SODIENTHOAIKHACHTHUE')
        khachthue.NGAY_SINH_KT = request.POST.get('NGAYSINHKHACHTHUE')
        khachthue.NOI_SINH_KT = request.POST.get('NOISINH')
        khachthue.GIOI_TINH_KT = request.POST.get('GIOITINHKHACHTHUE')
        khachthue.EMAIL_KT = request.POST.get('EMAILKHACHTHUE')
        khachthue.NGHE_NGHIEP = request.POST.get('NGHENGHIEP')
        khachthue.save()

        # Update or create CccdCmnd
        so_cmnd_cccd = request.POST.get('CMNDORCCCD')
        noi_cap = request.POST.get('NOICAP')
        if so_cmnd_cccd:
            if cccd_cmnd:
                cccd_cmnd.SO_CMND_CCCD = so_cmnd_cccd
                cccd_cmnd.NOI_CAP = noi_cap
                cccd_cmnd.save()
            else:
                CccdCmnd.objects.create(
                    SO_CMND_CCCD=so_cmnd_cccd,
                    MA_KHACH_THUE=khachthue,
                    NOI_CAP=noi_cap
                )
        messages.success(request, 'Thông tin đã được cập nhật thành công!')
        return redirect('sua_khach_thue', ma_khach_thue=ma_khach_thue)

    context = {
        'khachthue': khachthue,
        'cccd_cmnd': cccd_cmnd
    }
    return render(request, 'admin/khachthue/themsua_khachthue.html', context)