from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .models import PhongTro, CocPhong, TAISANPHONG, TAISAN
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



def phongtro_list(request):
    # Lấy ma_khu_vuc và page_number từ query string (?ma_khu_vuc=...&page_number=...)
    ma_khu_vuc = request.GET.get('ma_khu_vuc')
    page_number = request.GET.get('page_number', 1)

    # Nếu không có mã khu vực → trả về danh sách khu vực nhà trọ có MA_NHA_TRO = 1
    # Kiểm tra khu vực có tồn tại không
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1)
    

    # Lấy tham số tìm kiếm và bộ lọc từ request
    keyword = request.GET.get('keyword', '')
    trang_thai_filters = request.GET.getlist('options[]', [])
    if not ma_khu_vuc and khu_vucs.exists():
        ma_khu_vuc = khu_vucs.first().MA_KHU_VUC
        # Lấy danh sách phòng trọ theo mã khu vực
    phong_tros = PhongTro.objects.filter(MA_KHU_VUC=ma_khu_vuc)\
        .select_related('MA_LOAI_PHONG')\
        .prefetch_related('cocphong', 'hopdong')

    # Áp dụng bộ lọc từ khóa nếu có
    if keyword:
        phong_tros = phong_tros.filter(
            Q(TEN_PHONG__icontains=keyword) |
            Q(MA_LOAI_PHONG__TEN_LOAI_PHONG__icontains=keyword)
        )

    # Áp dụng bộ lọc trạng thái nếu có
    if trang_thai_filters:
        phong_tros = phong_tros.filter(TRANG_THAI_P__in=trang_thai_filters)

    # Phân trang (8 mục/trang)
    paginator = Paginator(phong_tros, 8)
    phong_tros_page = paginator.get_page(page_number)

    # Danh sách trạng thái
    trang_thai_phong_choices = ['Đang ở', 'Đang trống', 'Đang cọc dự trọ']
    trang_thai_hd_choices = ['Sắp kết thúc hợp đồng', 'Đã quá hạn hợp đồng', 'Đang nợ tiền']

    context = {
        'phong_tros': phong_tros_page,
        'ma_khu_vuc': ma_khu_vuc,
        'trang_thai_phong_choices': trang_thai_phong_choices,
        'trang_thai_hd_choices': trang_thai_hd_choices,
        'keyword': keyword,
        'selected_filters': trang_thai_filters,
        'khu_vucs': khu_vucs,
    }
    
    return render(request, 'admin/phongtro/phongtro.html', context)    




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
                    TRANG_THAI_P = 'Đang trống',  # Mặc định trạng thái là 'Đang trống'
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
    # Ví dụ: lấy danh sách phòng thuộc nhà trọ có mã là 1
    phong_tros = PhongTro.lay_phong_theo_ma_nha_tro(1)
    phong_tro = get_object_or_404(PhongTro, MA_PHONG=ma_phong)
    
     # Get all applied services for the room
    # Lấy danh sách dịch vụ áp dụng cho khu vực của phòng
    lichsu_dichvu = LichSuApDungDichVu.objects.filter(
        MA_KHU_VUC=phong_tro.MA_KHU_VUC,
        NGAY_HUY_DV__isnull=True
    ).select_related('MA_DICH_VU')
    taisanphong_list = TAISANPHONG.objects.filter(MA_PHONG__MA_PHONG=ma_phong).select_related('MA_TAI_SAN')

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
    coc_phong = CocPhong.objects.filter(
            MA_PHONG_id=ma_phong,
            TRANG_THAI_CP__in=['Đã cọc', 'Chờ xác nhận']  # Điều chỉnh trạng thái theo yêu cầu
        ).select_related('MA_KHACH_THUE').first()

    # return JsonResponse(dict(lichsu_dichvu))


    return render(request, 'admin/hopdong/themsua_hopdong.html', {
        'phong_tros': phong_tros,
        'phong_tro': phong_tro,
        'lichsu_dichvu_with_chiso': lichsu_dichvu_with_chiso,
        'taisanphong_list': taisanphong_list,
        'coc_phong': coc_phong,
        })








def ghi_so_dich_vu(request, ma_phong_tro):
    phong_tro = get_object_or_404(PhongTro, MA_PHONG=ma_phong_tro)
    lichsu_dichvu = LichSuApDungDichVu.objects.filter(
            MA_KHU_VUC=phong_tro.MA_KHU_VUC,
            NGAY_HUY_DV__isnull=True
        ).select_related('MA_DICH_VU')
    taisanphong_list = TAISANPHONG.objects.filter(MA_PHONG__MA_PHONG=ma_phong_tro).select_related('MA_TAI_SAN')

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