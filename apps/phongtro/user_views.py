from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
from functools import wraps
from .models import PhongTro, CocPhong, LoaiPhong, DangTinPhong
from apps.nhatro.models import KhuVuc, NhaTro
from apps.khachthue.models import KhachThue
from apps.hoadon.models import HoaDon
from apps.thanhvien.models import TaiKhoan

# Custom login required decorator
def custom_login_required(view_func):
    """Custom decorator để kiểm tra đăng nhập bằng session"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.info(request, 'Vui lòng đăng nhập để đặt phòng.')
            return redirect(f'/login/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper


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
    
    # Xử lý checkbox filters từ sidebar
    gia_phong_ranges = request.GET.getlist('gia_phong')  # Có thể có nhiều giá trị
    dien_tich_ranges = request.GET.getlist('dien_tich')
    
    # Áp dụng filters cho tin đăng
    # Xử lý filter giá - ưu tiên slider, sau đó đến checkbox
    if gia_min and gia_max:
        # Nếu có slider filter thì dùng slider
        try:
            tin_dang_list = tin_dang_list.filter(
                MA_PHONG__GIA_PHONG__gte=float(gia_min),
                MA_PHONG__GIA_PHONG__lte=float(gia_max)
            )
        except ValueError:
            pass
    elif gia_phong_ranges:
        # Nếu không có slider thì dùng checkbox
        price_conditions = Q()
        for price_range in gia_phong_ranges:
            if '-' in price_range:
                try:
                    min_price, max_price = map(int, price_range.split('-'))
                    price_conditions |= Q(
                        MA_PHONG__GIA_PHONG__gte=min_price,
                        MA_PHONG__GIA_PHONG__lte=max_price
                    )
                except ValueError:
                    continue
        if price_conditions:
            tin_dang_list = tin_dang_list.filter(price_conditions)
    else:
        # Xử lý từng filter riêng lẻ nếu chỉ có một trong hai
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
    
    # Xử lý filter diện tích - ưu tiên input, sau đó đến checkbox
    if dien_tich_min and dien_tich_max:
        # Nếu có input filter thì dùng input
        try:
            tin_dang_list = tin_dang_list.filter(
                MA_PHONG__DIEN_TICH__gte=float(dien_tich_min),
                MA_PHONG__DIEN_TICH__lte=float(dien_tich_max)
            )
        except ValueError:
            pass
    elif dien_tich_ranges:
        # Nếu không có input thì dùng checkbox
        area_conditions = Q()
        for area_range in dien_tich_ranges:
            if '-' in area_range:
                try:
                    min_area, max_area = map(int, area_range.split('-'))
                    area_conditions |= Q(
                        MA_PHONG__DIEN_TICH__gte=min_area,
                        MA_PHONG__DIEN_TICH__lte=max_area
                    )
                except ValueError:
                    continue
        if area_conditions:
            tin_dang_list = tin_dang_list.filter(area_conditions)
    else:
        # Xử lý từng filter riêng lẻ
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
            'gia_phong_ranges': gia_phong_ranges,
            'dien_tich_ranges': dien_tich_ranges,
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


@custom_login_required
def dat_phong(request, ma_phong):
    """View form đặt phòng - Yêu cầu đăng nhập và lấy thông tin từ tài khoản"""
    phong = get_object_or_404(
        PhongTro.objects.select_related(
            'MA_LOAI_PHONG', 'MA_KHU_VUC', 'MA_KHU_VUC__MA_NHA_TRO'
        ),
        MA_PHONG=ma_phong,
        TRANG_THAI_P='Trống'
    )
    
    # Lấy thông tin tài khoản từ session
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
        return redirect('/login/')
    
    try:
        tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
    except TaiKhoan.DoesNotExist:
        messages.error(request, 'Tài khoản không tồn tại.')
        return redirect('/login/')
    
    # Lấy thông tin khách thuê từ tài khoản đăng nhập
    try:
        khach_thue = KhachThue.objects.get(MA_TAI_KHOAN=tai_khoan)
    except KhachThue.DoesNotExist:
        messages.error(request, 'Tài khoản chưa có thông tin khách thuê. Vui lòng cập nhật thông tin cá nhân.')
        return redirect('dungchung:profile')
    
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form - bao gồm ngày vào, ghi chú và phương thức thanh toán
            ngay_du_kien_vao_str = request.POST.get('ngay_du_kien_vao', '').strip()
            ghi_chu = request.POST.get('ghi_chu', '').strip() or None
            phuong_thuc_thanh_toan = request.POST.get('phuong_thuc_thanh_toan', '').strip()
            
            # Validate ngày dự kiến vào
            if not ngay_du_kien_vao_str:
                raise ValueError('Ngày dự kiến vào không được để trống.')
                
            # Validate phương thức thanh toán
            if not phuong_thuc_thanh_toan:
                raise ValueError('Vui lòng chọn phương thức thanh toán.')
                
            # Validate phương thức thanh toán hợp lệ
            valid_payment_methods = ['tien_mat', 'chuyen_khoan', 'online']
            if phuong_thuc_thanh_toan not in valid_payment_methods:
                raise ValueError('Phương thức thanh toán không hợp lệ.')
            
            try:
                ngay_du_kien_vao = datetime.strptime(ngay_du_kien_vao_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                raise ValueError('Định dạng ngày dự kiến vào không hợp lệ.')
            
            # Validate ngày dự kiến vào (cho phép từ ngày mai)
            today = timezone.now().date()
            if ngay_du_kien_vao <= today:
                raise ValueError('Ngày dự kiến vào phải từ ngày mai trở đi.')
            
            # Lấy số tiền cọc từ bảng phòng
            so_tien_coc = float(phong.SO_TIEN_CAN_COC or 0)
            if so_tien_coc <= 0:
                raise ValueError('Phòng này chưa thiết lập số tiền cọc. Vui lòng liên hệ quản lý.')
            
            # Kiểm tra phòng còn trống
            if phong.TRANG_THAI_P != 'Trống':
                raise ValueError('Phòng đã được thuê hoặc không còn trống.')
            
            # Tạo ghi chú chi tiết bao gồm phương thức thanh toán
            payment_method_names = {
                'tien_mat': 'Tiền mặt (Thanh toán trực tiếp)',
                'chuyen_khoan': 'Chuyển khoản ngân hàng',
                'online': 'Thẻ ATM/Visa (Thanh toán online)'
            }
            
            ghi_chu_full = f"Phương thức thanh toán: {payment_method_names.get(phuong_thuc_thanh_toan, phuong_thuc_thanh_toan)}"
            if ghi_chu:
                ghi_chu_full += f"\nGhi chú khách hàng: {ghi_chu}"
            
            # Tạo đặt phòng với thông tin từ tài khoản đăng nhập
            dat_phong = CocPhong.objects.create(
                MA_PHONG=phong,
                MA_KHACH_THUE=khach_thue,
                NGAY_DU_KIEN_VAO=ngay_du_kien_vao,
                TIEN_COC_PHONG=so_tien_coc,
                GHI_CHU_CP=ghi_chu_full,
                TRANG_THAI_CP='CHO_XAC_NHAN'
            )
            
            # Luôn tạo hóa đơn cọc phòng sau khi đặt phòng thành công
            hoa_don = HoaDon.objects.create(
                MA_HOP_DONG=None,  # Chưa có hợp đồng
                MA_COC_PHONG=dat_phong,  # Liên kết với đặt phòng
                LOAI_HOA_DON='Hóa đơn cọc phòng',
                NGAY_LAP_HDON=timezone.now().date(),
                TONG_TIEN=so_tien_coc,
                TRANG_THAI_HDON='Chưa thanh toán'
            )
            
            # Tạo chi tiết hóa đơn cho tiền cọc
            from apps.hoadon.models import CHITIETHOADON
            CHITIETHOADON.objects.create(
                MA_HOA_DON=hoa_don,
                LOAI_KHOAN='COC',
                NOI_DUNG=f'Tiền cọc phòng {phong.TEN_PHONG}',
                SO_LUONG=1,
                DON_GIA=so_tien_coc,
                THANH_TIEN=so_tien_coc,
                GHI_CHU_CTHD=f'Tiền cọc đặt phòng {phong.TEN_PHONG} - {phong.MA_KHU_VUC.TEN_KHU_VUC}'
            )
                
            success_message = (
                f'Đặt phòng thành công! Mã đặt phòng: {dat_phong.MA_COC_PHONG}. '
                f'Vui lòng thanh toán hóa đơn #{hoa_don.MA_HOA_DON} để hoàn tất đặt phòng.'
            )
            redirect_url = reverse('user_phongtro:thanh_toan_dat_phong', kwargs={'ma_dat_phong': dat_phong.MA_COC_PHONG})
            redirect_view = 'user_phongtro:thanh_toan_dat_phong'
            
            # Kiểm tra xem đây có phải AJAX request không
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                response_data = {
                    'success': True,
                    'message': success_message,
                    'redirect_url': redirect_url,
                    'ma_dat_phong': dat_phong.MA_COC_PHONG,
                    'ma_hoa_don': hoa_don.MA_HOA_DON
                }
                return JsonResponse(response_data)
            else:
                messages.success(request, success_message)
                return redirect(redirect_view, ma_dat_phong=dat_phong.MA_COC_PHONG)
            
        except ValueError as e:
            error_message = str(e)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': error_message,
                    'errors': {'general': error_message}
                })
            else:
                messages.error(request, error_message)
        except Exception as e:
            error_message = f'Có lỗi xảy ra: {str(e)}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'message': error_message,
                    'errors': {'general': error_message}
                })
            else:
                messages.error(request, error_message)
    
    context = {
        'phong': phong,
        'khach_thue': khach_thue,
        'today': timezone.now().date(),
    }
    
    return render(request, 'user/datphong/dat_phong.html', context)


def xac_nhan_dat_phong(request, ma_dat_phong):
    """View xác nhận đặt phòng thành công"""
    dat_phong = get_object_or_404(
        CocPhong.objects.select_related(
            'MA_PHONG', 'MA_PHONG__MA_LOAI_PHONG', 
            'MA_PHONG__MA_KHU_VUC', 'MA_PHONG__MA_KHU_VUC__MA_NHA_TRO'
        ),
        MA_COC_PHONG=ma_dat_phong
    )
    
    context = {
        'dat_phong': dat_phong,
    }
    
    return render(request, 'user/datphong/xac_nhan_dat_phong.html', context)


@custom_login_required  
def thanh_toan_dat_phong(request, ma_dat_phong):
    """View thanh toán đặt phòng"""
    # Lấy thông tin tài khoản từ session
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
        return redirect('/login/')
        
    try:
        tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
    except TaiKhoan.DoesNotExist:
        messages.error(request, 'Tài khoản không tồn tại.')
        return redirect('/login/')
    
    dat_phong = get_object_or_404(
        CocPhong.objects.select_related(
            'MA_PHONG', 'MA_PHONG__MA_LOAI_PHONG', 
            'MA_PHONG__MA_KHU_VUC', 'MA_PHONG__MA_KHU_VUC__MA_NHA_TRO',
            'MA_KHACH_THUE'
        ),
        MA_COC_PHONG=ma_dat_phong,
        MA_KHACH_THUE__MA_TAI_KHOAN=tai_khoan
    )
    
    # Tìm hóa đơn cọc phòng
    hoa_don = None
    try:
        hoa_don = HoaDon.objects.filter(
            MA_COC_PHONG=dat_phong,
            LOAI_HOA_DON='Hóa đơn cọc phòng',
            TRANG_THAI_HDON='Chưa thanh toán'
        ).first()
    except:
        pass
    
    # Nếu không có hóa đơn, redirect về trang xác nhận
    if not hoa_don:
        messages.info(request, 'Chưa có hóa đơn cho đơn đặt phòng này. Vui lòng chờ admin xác nhận.')
        return redirect('user_phongtro:xac_nhan_dat_phong', ma_dat_phong=dat_phong.MA_COC_PHONG)
    
    if request.method == 'POST':
        phuong_thuc_thanh_toan = request.POST.get('phuong_thuc_thanh_toan', '')
        
        if phuong_thuc_thanh_toan in ['TIEN_MAT', 'CHUYEN_KHOAN', 'THE_ATM']:
            # Cập nhật trạng thái thanh toán
            hoa_don.TRANG_THAI_HDON = 'Đã thanh toán'
            hoa_don.save()
            
            # Tự động xác nhận đặt phòng ngay sau khi thanh toán
            dat_phong.TRANG_THAI_CP = 'DA_XAC_NHAN'
            dat_phong.save()
            
            messages.success(request, 'Thanh toán thành công! Đặt phòng của bạn đã được tự động xác nhận.')
            return redirect('user_phongtro:xac_nhan_dat_phong', ma_dat_phong=dat_phong.MA_COC_PHONG)
        else:
            messages.error(request, 'Vui lòng chọn phương thức thanh toán.')
    
    context = {
        'dat_phong': dat_phong,
        'hoa_don': hoa_don,
    }
    
    return render(request, 'user/datphong/thanh_toan_dat_phong.html', context)


@custom_login_required
def phong_da_dat(request):
    """View hiển thị danh sách phòng đã đặt của người dùng"""
    # Lấy thông tin tài khoản từ session
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
        return redirect('/login/')
        
    try:
        tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
        khach_thue = KhachThue.objects.get(MA_TAI_KHOAN=tai_khoan)
    except (TaiKhoan.DoesNotExist, KhachThue.DoesNotExist):
        messages.error(request, 'Tài khoản không tồn tại hoặc chưa có thông tin khách thuê.')
        return redirect('dungchung:profile')
    
    # Lấy danh sách đặt phòng của user đăng nhập
    danh_sach_dat_phong = CocPhong.objects.filter(
        MA_KHACH_THUE=khach_thue
    ).select_related(
        'MA_PHONG', 'MA_PHONG__MA_LOAI_PHONG',
        'MA_PHONG__MA_KHU_VUC', 'MA_PHONG__MA_KHU_VUC__MA_NHA_TRO'
    ).order_by('-NGAY_COC_PHONG', '-MA_COC_PHONG')
    
    # Phân loại đặt phòng theo trạng thái
    phong_cho_xac_nhan = danh_sach_dat_phong.filter(TRANG_THAI_CP='CHO_XAC_NHAN')
    phong_da_xac_nhan = danh_sach_dat_phong.filter(TRANG_THAI_CP='DA_XAC_NHAN')
    phong_da_tu_choi = danh_sach_dat_phong.filter(TRANG_THAI_CP='DA_TU_CHOI')
    
    # Lấy thông tin hóa đơn cho từng đặt phòng
    for dat_phong in danh_sach_dat_phong:
        try:
            dat_phong.hoa_don = HoaDon.objects.filter(
                MA_COC_PHONG=dat_phong
            ).first()
        except:
            dat_phong.hoa_don = None
    
    context = {
        'danh_sach_dat_phong': danh_sach_dat_phong,
        'phong_cho_xac_nhan': phong_cho_xac_nhan,
        'phong_da_xac_nhan': phong_da_xac_nhan,
        'phong_da_tu_choi': phong_da_tu_choi,
        'khach_thue': khach_thue,
        'tong_so_dat_phong': danh_sach_dat_phong.count(),
    }
    
    return render(request, 'user/datphong/phong_da_dat.html', context)


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


