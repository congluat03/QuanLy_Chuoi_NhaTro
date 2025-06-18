from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .models import PhongTro, CocPhong
from apps.nhatro.models import KhuVuc
from apps.khachthue.models import KhachThue
from apps.hopdong.models import HopDong
from django.db import transaction
from django.views.decorators.http import require_POST

def phongtro_list(request):
    # Lấy danh sách khu vực thuộc nhà trọ có MA_NHA_TRO=1
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1)
    return render(request, 'admin/phongtro/danhsach_phongtro.html', {'khu_vucs': khu_vucs})

def phong_tro_theo_khu_vuc(request, ma_khu_vuc, page_number=1):
    # Kiểm tra xem khu vực có tồn tại không
    khu_vuc = get_object_or_404(KhuVuc, MA_KHU_VUC=ma_khu_vuc)

    # Lấy tham số tìm kiếm và bộ lọc từ request
    keyword = request.GET.get('keyword', '')
    trang_thai_filters = request.GET.getlist('options[]', [])

    # Lấy danh sách phòng trọ theo mã khu vực
    phong_tros = PhongTro.objects.filter(MA_KHU_VUC=ma_khu_vuc)

    # Áp dụng bộ lọc tìm kiếm nếu có
    if keyword:
        phong_tros = phong_tros.filter(
            Q(TEN_PHONG__icontains=keyword) |
            Q(LOAI_PHONG__icontains=keyword)
        )

    # Áp dụng bộ lọc trạng thái nếu có
    if trang_thai_filters:
        phong_tros = phong_tros.filter(TRANG_THAI_P__in=trang_thai_filters)

    # Phân trang (8 mục/trang)
    paginator = Paginator(phong_tros, 8)
    phong_tros_page = paginator.get_page(page_number)

    trang_thai_options = [
        'Đang ở',
        'Đang trống',
        'Sắp kết thúc hợp đồng',
        'Đã quá hạn hợp đồng',
        'Đang cọc dự trọ',
        'Đang nợ tiền',
    ]

    context = {
        'phong_tros': phong_tros_page,
        'ma_khu_vuc': ma_khu_vuc,
        'trang_thai_options': trang_thai_options,
        'keyword': keyword,  # Truyền lại keyword để hiển thị trong input tìm kiếm
        'selected_filters': trang_thai_filters,  # Truyền lại các bộ lọc đã chọn
    }

    # Nếu là request AJAX, trả về template phần nội dung phòng trọ
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'admin/hoadon/danhsach_phongtro.html', context)

    # Nếu không phải AJAX, trả về toàn bộ trang
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
        # Lấy dữ liệu từ form
        ngay_coc_phong = request.POST.get('NGAY_COC_PHONG')
        ngay_du_kien_vao = request.POST.get('NGAY_DU_KIEN_VAO')
        tien_coc_phong = request.POST.get('TIEN_COC_PHONG')
        ghi_chu_cp = request.POST.get('GHI_CHU_CP')
        ho_ten_kt = request.POST.get('HO_TEN_KT')
        sdt_kt = request.POST.get('SDT_KT')
        email_kt = request.POST.get('EMAIL_KT')

        # Kiểm tra dữ liệu bắt buộc
        errors = []
        if not ngay_coc_phong:
            errors.append('Ngày cọc giữ chỗ là bắt buộc.')
        if not ngay_du_kien_vao:
            errors.append('Ngày vào ở là bắt buộc.')
        if not ho_ten_kt:
            errors.append('Họ tên khách thuê là bắt buộc.')
        if not sdt_kt:
            errors.append('Số điện thoại khách thuê là bắt buộc.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'admin/phongtro/coc_giu_cho.html', {
                'phong_tro': phong_tro,
                'form_data': request.POST,
            })

        try:
            # Tìm hoặc tạo khách thuê
            khach_thue, created = KhachThue.objects.get_or_create(
                HO_TEN_KT=ho_ten_kt,
                defaults={
                    'SDT_KT': sdt_kt,
                    'EMAIL_KT': email_kt,
                }
            )

            # Tạo cọc phòng
            coc_phong = CocPhong(
                MA_PHONG=phong_tro,
                MA_KHACH_THUE=khach_thue,
                NGAY_COC_PHONG=ngay_coc_phong,
                NGAY_DU_KIEN_VAO=ngay_du_kien_vao,
                TIEN_COC_PHONG=tien_coc_phong or phong_tro.GIA_PHONG,
                TRANG_THAI_CP='Pending',
                GHI_CHU_CP=ghi_chu_cp,
            )
            coc_phong.save()
            messages.success(request, 'Thêm cọc giữ chỗ thành công!')
            return redirect('phongtro_list')  # Điều hướng sau khi thành công
        except Exception as e:
            messages.error(request, f'Lỗi khi lưu dữ liệu: {str(e)}')
            return render(request, 'admin/phongtro/coc_giu_cho.html', {
                'phong_tro': phong_tro,
                'form_data': request.POST,
            })

    return render(request, 'admin/phongtro/cocphong.html', {
        'phong_tro': phong_tro,
        'form_data': {'TIEN_COC_PHONG': phong_tro.GIA_PHONG},
    })