from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
from .models import PhongTro, CocPhong, LoaiPhong, DangTinPhong
from apps.nhatro.models import KhuVuc, NhaTro


def tim_phong(request):
    """View tìm kiếm phòng trọ - Chỉ hiển thị phòng có tin đăng"""
    # Lấy tin đăng đang hiển thị
    tin_dang_list = DangTinPhong.objects.filter(
        TRANG_THAI='DANG_HIEN_THI'
    ).select_related(
        'MA_PHONG', 
        'MA_PHONG__MA_LOAI_PHONG', 
        'MA_PHONG__MA_KHU_VUC', 
        'MA_PHONG__MA_KHU_VUC__MA_NHA_TRO'
    ).prefetch_related('hinh_anh')
    
    # Các filter parameters
    gia_min = request.GET.get('gia_min', '').strip()
    gia_max = request.GET.get('gia_max', '').strip()
    dien_tich_min = request.GET.get('dien_tich_min', '').strip()
    dien_tich_max = request.GET.get('dien_tich_max', '').strip()
    khu_vuc = request.GET.get('khu_vuc', '').strip()
    loai_phong = request.GET.get('loai_phong', '').strip()
    vi_tri = request.GET.get('vi_tri', '').strip()
    sort_by = request.GET.get('sort', '').strip()
    
    # Áp dụng filters cho tin đăng
    if gia_min:
        try:
            tin_dang_list = tin_dang_list.filter(MA_PHONG__GIA_PHONG__gte=float(gia_min))
        except ValueError:
            pass
    
    if gia_max:
        try:
            tin_dang_list = tin_dang_list.filter(MA_PHONG__GIA_PHONG__lte=float(gia_max))
        except ValueError:
            pass
    
    if dien_tich_min:
        try:
            tin_dang_list = tin_dang_list.filter(MA_PHONG__DIEN_TICH__gte=float(dien_tich_min))
        except ValueError:
            pass
    
    if dien_tich_max:
        try:
            tin_dang_list = tin_dang_list.filter(MA_PHONG__DIEN_TICH__lte=float(dien_tich_max))
        except ValueError:
            pass
    
    if khu_vuc:
        try:
            tin_dang_list = tin_dang_list.filter(MA_PHONG__MA_KHU_VUC=int(khu_vuc))
        except ValueError:
            pass
    
    if loai_phong:
        try:
            tin_dang_list = tin_dang_list.filter(MA_PHONG__MA_LOAI_PHONG=int(loai_phong))
        except ValueError:
            pass
    
    # Tìm kiếm theo vị trí (tên khu vực, tên nhà trọ, địa chỉ)
    if vi_tri:
        tin_dang_list = tin_dang_list.filter(
            Q(MA_PHONG__MA_KHU_VUC__TEN_KHU_VUC__icontains=vi_tri) |
            Q(MA_PHONG__MA_KHU_VUC__MA_NHA_TRO__TEN_NHA_TRO__icontains=vi_tri) |
            Q(MA_PHONG__MA_KHU_VUC__MA_NHA_TRO__DIA_CHI__icontains=vi_tri) |
            Q(TIEU_DE__icontains=vi_tri) |
            Q(MO_TA_TIN__icontains=vi_tri)
        )
    
    # Áp dụng sắp xếp
    if sort_by == 'price_asc':
        tin_dang_list = tin_dang_list.order_by('MA_PHONG__GIA_PHONG')
    elif sort_by == 'price_desc':
        tin_dang_list = tin_dang_list.order_by('-MA_PHONG__GIA_PHONG')
    elif sort_by == 'area_desc':
        tin_dang_list = tin_dang_list.order_by('-MA_PHONG__DIEN_TICH')
    elif sort_by == 'newest':
        tin_dang_list = tin_dang_list.order_by('-NGAY_DANG')
    else:
        # Mặc định sắp xếp theo lượt xem giảm dần và ngày đăng mới nhất
        tin_dang_list = tin_dang_list.order_by('-LUOT_XEM', '-NGAY_DANG')
    
    # Pagination
    paginator = Paginator(tin_dang_list, 12)  # 12 tin đăng mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Lấy dữ liệu cho filter dropdowns
    khu_vucs = KhuVuc.objects.all().select_related('MA_NHA_TRO')
    loai_phongs = LoaiPhong.objects.all()
    
    context = {
        'page_obj': page_obj,
        'khu_vucs': khu_vucs,
        'loai_phongs': loai_phongs,
        'filters': {
            'gia_min': gia_min,
            'gia_max': gia_max,
            'dien_tich_min': dien_tich_min,
            'dien_tich_max': dien_tich_max,
            'khu_vuc': khu_vuc,
            'loai_phong': loai_phong,
            'vi_tri': vi_tri,
            'sort': sort_by,
        },
        'total_phongs': paginator.count,
        'request': request,  # Để template có thể truy cập request.GET
    }
    
    return render(request, 'user/phongtro/tim_phong.html', context)


def chi_tiet_phong(request, ma_phong):
    """View chi tiết phòng - Hiển thị từ tin đăng"""
    # Lấy tin đăng của phòng này
    tin_dang = get_object_or_404(
        DangTinPhong.objects.select_related(
            'MA_PHONG',
            'MA_PHONG__MA_LOAI_PHONG', 
            'MA_PHONG__MA_KHU_VUC', 
            'MA_PHONG__MA_KHU_VUC__MA_NHA_TRO'
        ).prefetch_related('hinh_anh'),
        MA_PHONG=ma_phong,
        TRANG_THAI='DANG_HIEN_THI'
    )
    
    # Tăng lượt xem
    tin_dang.tang_luot_xem()
    
    context = {
        'tin_dang': tin_dang,
        'phong': tin_dang.MA_PHONG,  # Backward compatibility
    }
    
    return render(request, 'user/phongtro/chi_tiet_phong.html', context)


def dat_phong(request, ma_phong):
    """View form đặt phòng - Chỉ cần thông tin cơ bản"""
    phong = get_object_or_404(
        PhongTro.objects.select_related(
            'MA_LOAI_PHONG', 'MA_KHU_VUC', 'MA_KHU_VUC__MA_NHA_TRO'
        ),
        MA_PHONG=ma_phong,
        TRANG_THAI_P='Trống'
    )
    
    if request.method == 'POST':
        print(f"🔍 DEBUG: POST data = {dict(request.POST)}")
        try:
            # Lấy dữ liệu từ form (chỉ cần thông tin cơ bản)
            data = {
                'ma_phong': ma_phong,
                'ho_ten': request.POST.get('ho_ten', '').strip(),
                'so_dien_thoai': request.POST.get('so_dien_thoai', '').strip(),
                'email': request.POST.get('email', '').strip() or None,
                'ngay_bat_dau_thue': None,
                'so_tien_coc': None,
                'ghi_chu': request.POST.get('ghi_chu', '').strip() or None,
            }
            
            # Validate thông tin cơ bản
            if not data['ho_ten']:
                raise ValueError('Họ tên không được để trống.')
            
            if not data['so_dien_thoai']:
                raise ValueError('Số điện thoại không được để trống.')
            
            # Parse ngày bắt đầu thuê
            ngay_bat_dau_str = request.POST.get('ngay_bat_dau_thue', '').strip()
            if not ngay_bat_dau_str:
                raise ValueError('Ngày bắt đầu thuê không được để trống.')
            
            try:
                data['ngay_bat_dau_thue'] = datetime.strptime(ngay_bat_dau_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                raise ValueError('Định dạng ngày bắt đầu thuê không hợp lệ.')
            
            # Validate ngày bắt đầu thuê (cho phép từ ngày mai)
            if data['ngay_bat_dau_thue'] is None:
                raise ValueError('Ngày bắt đầu thuê không hợp lệ.')
            
            today = timezone.now().date()
            if data['ngay_bat_dau_thue'] <= today:
                raise ValueError('Ngày bắt đầu thuê phải từ ngày mai trở đi.')
            
            # Parse số tiền cọc
            so_tien_coc_str = request.POST.get('so_tien_coc', '').strip()
            if not so_tien_coc_str:
                raise ValueError('Số tiền cọc không được để trống.')
            
            try:
                data['so_tien_coc'] = float(so_tien_coc_str)
                if data['so_tien_coc'] is None or data['so_tien_coc'] <= 0:
                    raise ValueError('Số tiền cọc phải lớn hơn 0.')
            except (ValueError, TypeError):
                raise ValueError('Số tiền cọc không hợp lệ.')
            
            # Kiểm tra phòng còn trống
            phong_check = PhongTro.objects.get(MA_PHONG=ma_phong)
            if phong_check.TRANG_THAI_P != 'Trống':
                raise ValueError('Phòng đã được thuê hoặc không còn trống.')
            
            # Tạo đặt phòng online
            dat_phong = CocPhong.tao_dat_phong_online(
                phong=phong_check,
                ho_ten=data['ho_ten'],
                so_dien_thoai=data['so_dien_thoai'],
                email=data.get('email'),
                ngay_du_kien_vao=data['ngay_bat_dau_thue'],
                tien_coc=data['so_tien_coc'],
                ghi_chu=data.get('ghi_chu')
            )
            
            messages.success(
                request, 
                f'Đặt phòng thành công! Mã đặt phòng: {dat_phong.MA_COC_PHONG}. '
                'Chúng tôi sẽ liên hệ với bạn trong thời gian sớm nhất để xác nhận thông tin.'
            )
            
            return redirect('user_phongtro:xac_nhan_dat_phong', ma_dat_phong=dat_phong.MA_COC_PHONG)
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
    
    context = {
        'phong': phong,
        'today': timezone.now().date(),
    }
    
    return render(request, 'user/datphong/dat_phong.html', context)


def xac_nhan_dat_phong(request, ma_dat_phong):
    """View xác nhận đặt phòng thành công"""
    dat_phong = get_object_or_404(
        CocPhong.objects.select_related(
            'MA_PHONG', 'MA_PHONG__MA_LOAI_PHONG', 
            'MA_PHONG__MA_KHU_VUC', 'MA_PHONG__MA_KHU_VUC__MA_NHA_TRO'
        ).filter(NGUON_TAO='ONLINE'),
        MA_COC_PHONG=ma_dat_phong
    )
    
    context = {
        'dat_phong': dat_phong,
    }
    
    return render(request, 'user/datphong/xac_nhan_dat_phong.html', context)


def tra_cuu_dat_phong(request):
    """View tra cứu đơn đặt phòng"""
    dat_phong = None
    
    if request.method == 'POST':
        ma_dat_phong = request.POST.get('ma_dat_phong', '').strip()
        so_dien_thoai = request.POST.get('so_dien_thoai', '').strip()
        
        if ma_dat_phong and so_dien_thoai:
            try:
                dat_phong = CocPhong.objects.select_related(
                    'MA_PHONG', 'MA_PHONG__MA_LOAI_PHONG',
                    'MA_PHONG__MA_KHU_VUC', 'MA_PHONG__MA_KHU_VUC__MA_NHA_TRO'
                ).get(
                    MA_COC_PHONG=ma_dat_phong,
                    SO_DIEN_THOAI_TEMP=so_dien_thoai,
                    NGUON_TAO='ONLINE'
                )
            except CocPhong.DoesNotExist:
                messages.error(request, 'Không tìm thấy đơn đặt phòng với thông tin đã nhập.')
            except Exception as e:
                messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        else:
            messages.error(request, 'Vui lòng nhập đầy đủ mã đặt phòng và số điện thoại.')
    
    context = {
        'dat_phong': dat_phong,
    }
    
    return render(request, 'user/datphong/tra_cuu_dat_phong.html', context)


# API views for AJAX requests
def api_phong_autocomplete(request):
    """API tự động hoàn thành tên phòng"""
    term = request.GET.get('term', '').strip()
    phongs = []
    
    if term:
        phong_list = PhongTro.objects.filter(
            TEN_PHONG__icontains=term,
            TRANG_THAI_P='Trống'
        ).values('MA_PHONG', 'TEN_PHONG')[:10]
        
        phongs = [
            {
                'id': phong['MA_PHONG'],
                'label': phong['TEN_PHONG'],
                'value': phong['TEN_PHONG']
            }
            for phong in phong_list
        ]
    
    return JsonResponse(phongs, safe=False)


def api_location_autocomplete(request):
    """API tự động hoàn thành địa điểm"""
    term = request.GET.get('term', '').strip()
    locations = []
    
    if term and len(term) >= 2:
        # Tìm kiếm trong khu vực và nhà trọ
        khu_vucs = KhuVuc.objects.filter(
            Q(TEN_KHU_VUC__icontains=term) |
            Q(MA_NHA_TRO__TEN_NHA_TRO__icontains=term) |
            Q(MA_NHA_TRO__DIA_CHI__icontains=term)
        ).select_related('MA_NHA_TRO').distinct()[:10]
        
        for kv in khu_vucs:
            locations.append({
                'display_name': f"{kv.TEN_KHU_VUC} - {kv.MA_NHA_TRO.TEN_NHA_TRO}",
                'type': 'khu_vuc',
                'id': kv.MA_KHU_VUC,
                'address': kv.MA_NHA_TRO.DIA_CHI if kv.MA_NHA_TRO else '',
            })
        
        # Thêm các gợi ý địa điểm phổ biến nếu cần
        popular_locations = [
            'Quận 1, Thành phố Hồ Chí Minh',
            'Quận 3, Thành phố Hồ Chí Minh', 
            'Quận Bình Thạnh, Thành phố Hồ Chí Minh',
            'Quận 7, Thành phố Hồ Chí Minh',
            'Quận Phú Nhuận, Thành phố Hồ Chí Minh',
            'Quận Thủ Đức, Thành phố Hồ Chí Minh',
            'Quận Gò Vấp, Thành phố Hồ Chí Minh',
        ]
        
        # Thêm địa điểm phổ biến nếu khớp
        for loc in popular_locations:
            if term.lower() in loc.lower() and len(locations) < 10:
                locations.append({
                    'display_name': loc,
                    'type': 'popular',
                    'id': None,
                    'address': loc,
                })
    
    return JsonResponse(locations, safe=False)


def api_provinces(request):
    """API lấy danh sách tỉnh thành"""
    provinces = [
        {
            'code': 'HCM',
            'name': 'TP. Hồ Chí Minh',
            'type': 'Thành phố Trung ương'
        },
        {
            'code': 'HN', 
            'name': 'Hà Nội',
            'type': 'Thành phố Trung ương'
        },
        {
            'code': 'DN',
            'name': 'Đà Nẵng', 
            'type': 'Thành phố Trung ương'
        },
        {
            'code': 'HP',
            'name': 'Hải Phòng',
            'type': 'Thành phố Trung ương'
        },
        {
            'code': 'CT',
            'name': 'Cần Thơ',
            'type': 'Thành phố Trung ương'
        }
    ]
    return JsonResponse(provinces, safe=False)


def api_districts(request, province_code):
    """API lấy danh sách quận huyện theo tỉnh"""
    districts_data = {
        'HCM': [
            {'code': 'Q1', 'name': 'Quận 1', 'type': 'Quận'},
            {'code': 'Q3', 'name': 'Quận 3', 'type': 'Quận'},
            {'code': 'Q4', 'name': 'Quận 4', 'type': 'Quận'},
            {'code': 'Q5', 'name': 'Quận 5', 'type': 'Quận'},
            {'code': 'Q6', 'name': 'Quận 6', 'type': 'Quận'},
            {'code': 'Q7', 'name': 'Quận 7', 'type': 'Quận'},
            {'code': 'Q8', 'name': 'Quận 8', 'type': 'Quận'},
            {'code': 'Q10', 'name': 'Quận 10', 'type': 'Quận'},
            {'code': 'Q11', 'name': 'Quận 11', 'type': 'Quận'},
            {'code': 'Q12', 'name': 'Quận 12', 'type': 'Quận'},
            {'code': 'BT', 'name': 'Quận Bình Thạnh', 'type': 'Quận'},
            {'code': 'PN', 'name': 'Quận Phú Nhuận', 'type': 'Quận'},
            {'code': 'TB', 'name': 'Quận Tân Bình', 'type': 'Quận'},
            {'code': 'TD', 'name': 'Quận Thủ Đức', 'type': 'Quận'},
            {'code': 'GV', 'name': 'Quận Gò Vấp', 'type': 'Quận'}
        ],
        'HN': [
            {'code': 'HK', 'name': 'Quận Hoàn Kiếm', 'type': 'Quận'},
            {'code': 'BD', 'name': 'Quận Ba Đình', 'type': 'Quận'},
            {'code': 'CG', 'name': 'Quận Cầu Giấy', 'type': 'Quận'},
            {'code': 'DD', 'name': 'Quận Đống Đa', 'type': 'Quận'},
            {'code': 'HB', 'name': 'Quận Hai Bà Trưng', 'type': 'Quận'},
            {'code': 'TX', 'name': 'Quận Thanh Xuân', 'type': 'Quận'}
        ],
        'DN': [
            {'code': 'HC', 'name': 'Quận Hải Châu', 'type': 'Quận'},
            {'code': 'TK', 'name': 'Quận Thanh Khê', 'type': 'Quận'},
            {'code': 'SK', 'name': 'Quận Sơn Trà', 'type': 'Quận'},
            {'code': 'NV', 'name': 'Quận Ngũ Hành Sơn', 'type': 'Quận'}
        ]
    }
    
    districts = districts_data.get(province_code, [])
    return JsonResponse(districts, safe=False)


def api_wards(request, province_code, district_code):
    """API lấy danh sách phường xã theo quận huyện"""
    wards_data = {
        'HCM': {
            'Q1': [
                {'code': 'P01', 'name': 'Phường Bến Nghé', 'type': 'Phường'},
                {'code': 'P02', 'name': 'Phường Bến Thành', 'type': 'Phường'},
                {'code': 'P03', 'name': 'Phường Cầu Kho', 'type': 'Phường'},
                {'code': 'P04', 'name': 'Phường Cầu Ông Lãnh', 'type': 'Phường'},
                {'code': 'P05', 'name': 'Phường Cô Giang', 'type': 'Phường'},
                {'code': 'P06', 'name': 'Phường Đa Kao', 'type': 'Phường'},
                {'code': 'P07', 'name': 'Phường Nguyễn Cư Trinh', 'type': 'Phường'},
                {'code': 'P08', 'name': 'Phường Nguyễn Thái Bình', 'type': 'Phường'},
                {'code': 'P09', 'name': 'Phường Phạm Ngũ Lão', 'type': 'Phường'},
                {'code': 'P10', 'name': 'Phường Tân Định', 'type': 'Phường'}
            ],
            'Q3': [
                {'code': 'P01', 'name': 'Phường 1', 'type': 'Phường'},
                {'code': 'P02', 'name': 'Phường 2', 'type': 'Phường'},
                {'code': 'P03', 'name': 'Phường 3', 'type': 'Phường'},
                {'code': 'P04', 'name': 'Phường 4', 'type': 'Phường'},
                {'code': 'P05', 'name': 'Phường 5', 'type': 'Phường'},
                {'code': 'P06', 'name': 'Phường 6', 'type': 'Phường'},
                {'code': 'P07', 'name': 'Phường 7', 'type': 'Phường'},
                {'code': 'P08', 'name': 'Phường 8', 'type': 'Phường'},
                {'code': 'P09', 'name': 'Phường 9', 'type': 'Phường'},
                {'code': 'P10', 'name': 'Phường 10', 'type': 'Phường'}
            ],
            'BT': [
                {'code': 'P01', 'name': 'Phường 1', 'type': 'Phường'},
                {'code': 'P02', 'name': 'Phường 2', 'type': 'Phường'},
                {'code': 'P03', 'name': 'Phường 3', 'type': 'Phường'},
                {'code': 'P11', 'name': 'Phường 11', 'type': 'Phường'},
                {'code': 'P12', 'name': 'Phường 12', 'type': 'Phường'},
                {'code': 'P13', 'name': 'Phường 13', 'type': 'Phường'},
                {'code': 'P14', 'name': 'Phường 14', 'type': 'Phường'},
                {'code': 'P15', 'name': 'Phường 15', 'type': 'Phường'}
            ]
        },
        'HN': {
            'HK': [
                {'code': 'P01', 'name': 'Phường Chương Dương', 'type': 'Phường'},
                {'code': 'P02', 'name': 'Phường Cửa Đông', 'type': 'Phường'},
                {'code': 'P03', 'name': 'Phường Cửa Nam', 'type': 'Phường'},
                {'code': 'P04', 'name': 'Phường Hàng Bạc', 'type': 'Phường'},
                {'code': 'P05', 'name': 'Phường Hàng Bài', 'type': 'Phường'},
                {'code': 'P06', 'name': 'Phường Hàng Buồm', 'type': 'Phường'},
                {'code': 'P07', 'name': 'Phường Hàng Đào', 'type': 'Phường'},
                {'code': 'P08', 'name': 'Phường Hàng Gai', 'type': 'Phường'}
            ]
        }
    }
    
    wards = wards_data.get(province_code, {}).get(district_code, [])
    return JsonResponse(wards, safe=False)


def api_phong_info(request, ma_phong):
    """API lấy thông tin phòng"""
    try:
        phong = PhongTro.objects.select_related(
            'MA_LOAI_PHONG', 'MA_KHU_VUC', 'MA_KHU_VUC__MA_NHA_TRO'
        ).get(MA_PHONG=ma_phong, TRANG_THAI_P='Trống')
        
        data = {
            'ma_phong': phong.MA_PHONG,
            'ten_phong': phong.TEN_PHONG,
            'gia_phong': float(phong.GIA_PHONG or 0),
            'dien_tich': float(phong.DIEN_TICH or 0),
            'so_nguoi_toi_da': phong.SO_NGUOI_TOI_DA,
            'so_tien_can_coc': float(phong.SO_TIEN_CAN_COC or 0),
            'mo_ta': phong.MO_TA_P,
            'loai_phong': phong.MA_LOAI_PHONG.TEN_LOAI_PHONG if phong.MA_LOAI_PHONG else '',
            'khu_vuc': phong.MA_KHU_VUC.TEN_KHU_VUC if phong.MA_KHU_VUC else '',
            'nha_tro': phong.MA_KHU_VUC.MA_NHA_TRO.TEN_NHA_TRO if phong.MA_KHU_VUC and phong.MA_KHU_VUC.MA_NHA_TRO else '',
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except PhongTro.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Phòng không tồn tại hoặc đã được thuê.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


