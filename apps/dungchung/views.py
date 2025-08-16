# Views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from functools import wraps
import re
from apps.thanhvien.models import TaiKhoan
from apps.khachthue.models import KhachThue
from apps.hopdong.models import HopDong, LichSuHopDong
from apps.hoadon.models import HoaDon, KhauTru
from apps.phongtro.models import PhongTro
from apps.nhatro.models import KhuVuc
from django.db.models import Q
from datetime import datetime

def trang_chu(request):
    return render(request, 'index/trangchu/trangchu.html')

def register_view(request):
    """View đăng ký tài khoản mới với TaiKhoan"""
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        account_type = request.POST.get('account_type', 'Khách thuê')
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        
        # Validation
        errors = []
        
        # Validate full_name
        if not full_name or len(full_name) < 2:
            errors.append('Họ tên phải có ít nhất 2 ký tự.')
            
        # Validate username
        if not username or not re.match(r'^[a-zA-Z0-9]{6,20}$', username):
            errors.append('Tên đăng nhập phải từ 6-20 ký tự, chỉ bao gồm chữ cái và số.')
        elif TaiKhoan.objects.filter(TAI_KHOAN=username).exists():
            errors.append('Tên đăng nhập đã tồn tại.')
            
        # Validate email
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append('Email không hợp lệ.')
        elif KhachThue.objects.filter(EMAIL_KT=email).exists():
            errors.append('Email này đã được sử dụng.')
            
        # Validate phone
        if not phone_number or not re.match(r'^[0-9]{10,11}$', phone_number):
            errors.append('Số điện thoại phải có 10-11 chữ số.')
        elif KhachThue.objects.filter(SDT_KT=phone_number).exists():
            errors.append('Số điện thoại này đã được sử dụng.')
            
        # Validate password
        if not password1 or not re.match(r'^(?=.*[a-zA-Z])(?=.*[0-9]).{8,}$', password1):
            errors.append('Mật khẩu phải tối thiểu 8 ký tự, bao gồm chữ và số.')
        elif password1 != password2:
            errors.append('Mật khẩu xác nhận không khớp.')
            
        if not errors:
            try:
                with transaction.atomic():
                    # Tạo TaiKhoan
                    tai_khoan = TaiKhoan.create_tai_khoan(
                        tai_khoan=username,
                        mat_khau=password1,
                        quyen_han=account_type
                    )
                    
                    # Tạo thông tin chi tiết tùy theo loại tài khoản
                    if account_type == 'Khách thuê':
                        # Tạo KhachThue
                        KhachThue.create_khach_thue(
                            tai_khoan_obj=tai_khoan,
                            ho_ten_kt=full_name,
                            sdt_kt=phone_number,
                            email_kt=email
                        )
                    elif account_type == 'Chủ trọ':
                        # Tạo NguoiQuanLy (chủ trọ)
                        from apps.thanhvien.models import NguoiQuanLy
                        NguoiQuanLy.create_chu_tro(
                            tai_khoan_obj=tai_khoan,
                            ho_ten=full_name,
                            sdt=phone_number,
                            email=email
                        )
                    
                    # Đăng nhập tự động sau khi đăng ký (session-based)
                    request.session['user_id'] = tai_khoan.MA_TAI_KHOAN
                    request.session['username'] = tai_khoan.TAI_KHOAN
                    request.session['vai_tro'] = tai_khoan.QUYEN_HAN
                    request.session['is_authenticated'] = True
                    
                    messages.success(request, 'Đăng ký tài khoản thành công!')
                    return redirect('dungchung:trang_chu')
                    
            except Exception as e:
                messages.error(request, f'Đăng ký không thành công: {str(e)}')
        else:
            # Hiển thị lỗi
            for error in errors:
                messages.error(request, error)
    
    return render(request, 'auth/register.html')


def login_view(request):
    """View đăng nhập với TaiKhoan"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if username and password:
            try:
                tai_khoan = TaiKhoan.objects.get(TAI_KHOAN=username)
                if tai_khoan.check_mat_khau(password):
                    if tai_khoan.TRANG_THAI_TK != 'Hoạt động':
                        messages.error(request, 'Tài khoản đã bị khóa.')
                    else:
                        # Tạo session
                        request.session['user_id'] = tai_khoan.MA_TAI_KHOAN
                        request.session['username'] = tai_khoan.TAI_KHOAN
                        request.session['vai_tro'] = tai_khoan.QUYEN_HAN
                        request.session['is_authenticated'] = True
                        
                        messages.success(request, 'Đăng nhập thành công!')
                        
                        # Điều hướng theo loại tài khoản
                        if tai_khoan.QUYEN_HAN in ['Chủ trọ', 'admin']:
                            return redirect('admin')  # Chuyển đến trang quản trị
                        else:
                            # Khách thuê - kiểm tra next_page hoặc trang chủ
                            next_page = request.GET.get('next')
                            if next_page:
                                return redirect(next_page)
                            return redirect('dungchung:trang_chu')
                else:
                    messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
            except TaiKhoan.DoesNotExist:
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
        else:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """View đăng xuất"""
    # Xóa session
    request.session.flush()
    messages.success(request, 'Đăng xuất thành công!')
    return redirect('dungchung:trang_chu')


def custom_login_view(request):
    """View đăng nhập cũ với TaiKhoan (giữ lại để tương thích)"""
    if request.method == 'POST':
        tentai_khoan = request.POST.get('TENTAIKHOAN')
        mat_khau = request.POST.get('MATKHAU')
        
        try:
            # Lấy thông tin tài khoản từ model TaiKhoan
            user = TaiKhoan.objects.get(TAI_KHOAN=tentai_khoan)
            # Kiểm tra mật khẩu
            if user.check_mat_khau(mat_khau):
                # Kiểm tra trạng thái tài khoản
                if user.TRANG_THAI_TK:
                    # Lưu thông tin vào session
                    request.session['user_id'] = user.MA_TAI_KHOAN
                    request.session['username'] = user.TAI_KHOAN
                    request.session['vai_tro'] = user.QUYEN_HAN
                    
                    # Điều hướng dựa trên vai trò
                    if user.QUYEN_HAN == 'admin':
                        return redirect('admin')  # Chuyển hướng đến trang quản lý admin
                    else:
                        return redirect('/')  # Chuyển hướng đến trang mặc định
                else:
                    messages.error(request, 'Tài khoản đã bị khóa.')
            else:
                messages.error(request, 'Mật khẩu không đúng.')
        except TaiKhoan.DoesNotExist:
            messages.error(request, 'Tài khoản không tồn tại.')
        
        # Nếu có lỗi, render lại trang đăng nhập
        return render(request, 'auth/login.html')
    
    # Nếu không phải POST, render trang đăng nhập
    return render(request, 'auth/login.html')


def get_user_khachthue_info(request):
    """Helper function để lấy thông tin khách thuê từ session"""
    try:
        user_id = request.session.get('user_id')
        if user_id:
            tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
            khach_thue = KhachThue.objects.get(MA_TAI_KHOAN=tai_khoan)
            return {'tai_khoan': tai_khoan, 'khach_thue': khach_thue}
    except (TaiKhoan.DoesNotExist, KhachThue.DoesNotExist):
        pass
    return None


def tai_khoan_login_required(view_func):
    """Decorator để yêu cầu đăng nhập với TaiKhoan"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.session.get('is_authenticated'):
            messages.warning(request, 'Vui lòng đăng nhập để tiếp tục.')
            return redirect('dungchung:login')
        return view_func(request, *args, **kwargs)
    return wrapped_view


@tai_khoan_login_required
def user_profile_view(request):
    """View hiển thị thông tin cá nhân của người dùng"""
    user_info = get_user_khachthue_info(request)
    
    if not user_info:
        messages.error(request, 'Không tìm thấy thông tin tài khoản.')
        return redirect('dungchung:logout')
    
    context = {
        'tai_khoan': user_info['tai_khoan'],
        'khach_thue': user_info['khach_thue'],
    }
    return render(request, 'auth/profile.html', context)


@tai_khoan_login_required
def cap_nhat_profile_view(request):
    """View cập nhật thông tin cá nhân của người dùng"""
    user_info = get_user_khachthue_info(request)
    
    if not user_info:
        messages.error(request, 'Không tìm thấy thông tin tài khoản.')
        return redirect('dungchung:logout')
    
    tai_khoan = user_info['tai_khoan']
    khach_thue = user_info['khach_thue']
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Lấy dữ liệu từ form
                ho_ten_kt = request.POST.get('ho_ten_kt', '').strip()
                sdt_kt = request.POST.get('sdt_kt', '').strip()
                email_kt = request.POST.get('email_kt', '').strip()
                ngay_sinh_kt = request.POST.get('ngay_sinh_kt')
                gioi_tinh_kt = request.POST.get('gioi_tinh_kt', '').strip()
                noi_sinh_kt = request.POST.get('noi_sinh_kt', '').strip()
                nghe_nghiep = request.POST.get('nghe_nghiep', '').strip()
                avatar = request.FILES.get('avatar')
                
                # Thông tin CCCD/CMND
                so_cmnd_cccd = request.POST.get('so_cmnd_cccd', '').strip()
                ngay_cap = request.POST.get('ngay_cap')
                dia_chi_thuong_tru = request.POST.get('dia_chi_thuong_tru', '').strip()
                anh_mat_truoc = request.FILES.get('anh_mat_truoc')
                anh_mat_sau = request.FILES.get('anh_mat_sau')
                
                # Validation
                errors = []
                
                # Validate họ tên
                if ho_ten_kt and len(ho_ten_kt) < 2:
                    errors.append('Họ tên phải có ít nhất 2 ký tự.')
                
                # Validate số điện thoại
                if sdt_kt and not re.match(r'^[0-9]{10,11}$', sdt_kt):
                    errors.append('Số điện thoại phải có 10-11 chữ số.')
                
                # Validate email
                if email_kt and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email_kt):
                    errors.append('Email không hợp lệ.')
                
                # Validate CCCD/CMND
                if so_cmnd_cccd and not (len(so_cmnd_cccd) in [9, 12] and so_cmnd_cccd.isdigit()):
                    errors.append('Số CCCD/CMND phải là 9 hoặc 12 số.')
                
                if not errors:
                    # Cập nhật thông tin khách thuê
                    khach_thue.update_khach_thue(
                        ho_ten_kt=ho_ten_kt or khach_thue.HO_TEN_KT,
                        sdt_kt=sdt_kt or khach_thue.SDT_KT,
                        email_kt=email_kt if email_kt else khach_thue.EMAIL_KT,
                        ngay_sinh_kt=ngay_sinh_kt if ngay_sinh_kt else khach_thue.NGAY_SINH_KT,
                        gioi_tinh_kt=gioi_tinh_kt if gioi_tinh_kt else khach_thue.GIOI_TINH_KT,
                        noi_sinh_kt=noi_sinh_kt if noi_sinh_kt else khach_thue.NOI_SINH_KT,
                        nghe_nghiep=nghe_nghiep if nghe_nghiep else khach_thue.NGHE_NGHIEP,
                        avatar=avatar
                    )
                    
                    # Cập nhật thông tin CCCD/CMND nếu có
                    if so_cmnd_cccd:
                        khach_thue.update_cccd_cmnd(
                            ma_cccd=khach_thue.cccd_cmnd.first().MA_CCCD if khach_thue.cccd_cmnd.exists() else None,
                            so_cmnd_cccd=so_cmnd_cccd,
                            ngay_cap=ngay_cap if ngay_cap else None,
                            dia_chi_thuong_tru=dia_chi_thuong_tru,
                            anh_mat_truoc=anh_mat_truoc,
                            anh_mat_sau=anh_mat_sau,
                            gioi_tinh_kt=gioi_tinh_kt if gioi_tinh_kt else khach_thue.GIOI_TINH_KT,
                            ngay_sinh_kt=ngay_sinh_kt if ngay_sinh_kt else khach_thue.NGAY_SINH_KT,
                            que_quan=noi_sinh_kt if noi_sinh_kt else khach_thue.NOI_SINH_KT
                        )
                    
                    messages.success(request, 'Cập nhật thông tin cá nhân thành công!')
                    return redirect('dungchung:profile')
                else:
                    for error in errors:
                        messages.error(request, error)
                        
        except Exception as e:
            messages.error(request, f'Cập nhật không thành công: {str(e)}')
    
    # Lấy thông tin CCCD/CMND nếu có
    cccd_cmnd = None
    if khach_thue.cccd_cmnd.exists():
        cccd_cmnd = khach_thue.cccd_cmnd.first()
    
    context = {
        'tai_khoan': tai_khoan,
        'khach_thue': khach_thue,
        'cccd_cmnd': cccd_cmnd,
    }
    return render(request, 'auth/cap_nhat_profile.html', context)


@tai_khoan_login_required 
def user_doi_mat_khau_view(request):
    """View đổi mật khẩu cho user thường (khách thuê)"""
    user_info = get_user_khachthue_info(request)
    
    if not user_info:
        messages.error(request, 'Không tìm thấy thông tin tài khoản.')
        return redirect('dungchung:logout')
    
    tai_khoan = user_info['tai_khoan']
    khach_thue = user_info['khach_thue']
    
    if request.method == 'POST':
        mat_khau_cu = request.POST.get('mat_khau_cu', '').strip()
        mat_khau_moi = request.POST.get('mat_khau_moi', '').strip()
        xac_nhan_mat_khau = request.POST.get('xac_nhan_mat_khau', '').strip()
        
        errors = {}
        
        # Validate mật khẩu cũ
        if not mat_khau_cu:
            errors['mat_khau_cu'] = 'Vui lòng nhập mật khẩu cũ.'
        elif not tai_khoan.check_mat_khau(mat_khau_cu):
            errors['mat_khau_cu'] = 'Mật khẩu cũ không chính xác.'
        
        # Validate mật khẩu mới
        if not mat_khau_moi:
            errors['mat_khau_moi'] = 'Vui lòng nhập mật khẩu mới.'
        else:
            try:
                TaiKhoan.validate_mat_khau(mat_khau_moi)
            except ValueError as e:
                errors['mat_khau_moi'] = str(e)
        
        # Validate xác nhận mật khẩu
        if not xac_nhan_mat_khau:
            errors['xac_nhan_mat_khau'] = 'Vui lòng xác nhận mật khẩu mới.'
        elif mat_khau_moi and mat_khau_moi != xac_nhan_mat_khau:
            errors['xac_nhan_mat_khau'] = 'Mật khẩu xác nhận không khớp.'
        
        if not errors:
            try:
                # Đổi mật khẩu
                tai_khoan.set_mat_khau(mat_khau_moi)
                tai_khoan.save()
                
                messages.success(request, 'Đổi mật khẩu thành công!')
                return redirect('dungchung:profile')
            except Exception as e:
                messages.error(request, f'Đổi mật khẩu không thành công: {str(e)}')
        else:
            # Hiển thị lỗi
            for field, error in errors.items():
                messages.error(request, error)
    
    context = {
        'tai_khoan': tai_khoan,
        'khach_thue': khach_thue,
    }
    return render(request, 'auth/doi_mat_khau.html', context)


@tai_khoan_login_required 
def user_hop_dong_view(request):
    """View xem chi tiết hợp đồng của người thuê"""
    user_info = get_user_khachthue_info(request)
    
    if not user_info:
        messages.error(request, 'Không tìm thấy thông tin tài khoản.')
        return redirect('dungchung:logout')
    
    # Kiểm tra quyền khách thuê
    if user_info['tai_khoan'].QUYEN_HAN != 'Khách thuê':
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('dungchung:trang_chu')
    
    tai_khoan = user_info['tai_khoan']
    khach_thue = user_info['khach_thue']
    
    # Lấy hợp đồng hiện tại của người thuê (hợp đồng chưa kết thúc)
    try:
        lich_su_hop_dong = LichSuHopDong.objects.filter(
            MA_KHACH_THUE=khach_thue,
            NGAY_ROI_DI__isnull=True  # Chưa rời đi
        ).select_related(
            'MA_HOP_DONG',
            'MA_HOP_DONG__MA_PHONG',
            'MA_HOP_DONG__MA_PHONG__MA_KHU_VUC',
            'MA_HOP_DONG__MA_PHONG__MA_KHU_VUC__MA_NHA_TRO'
        ).first()
        
        if not lich_su_hop_dong:
            messages.info(request, 'Bạn hiện không có hợp đồng nào đang hiệu lực.')
            return render(request, 'auth/hop_dong_detail.html', {
                'tai_khoan': tai_khoan,
                'khach_thue': khach_thue,
                'hop_dong': None
            })
            
        hop_dong = lich_su_hop_dong.MA_HOP_DONG
        phong_tro = hop_dong.MA_PHONG
        
        # Lấy danh sách tất cả thành viên trong hợp đồng
        thanh_vien_hop_dong = LichSuHopDong.objects.filter(
            MA_HOP_DONG=hop_dong
        ).select_related('MA_KHACH_THUE').order_by('NGAY_THAM_GIA')
        
        context = {
            'tai_khoan': tai_khoan,
            'khach_thue': khach_thue,
            'hop_dong': hop_dong,
            'phong_tro': phong_tro,
            'lich_su_hop_dong': lich_su_hop_dong,
            'thanh_vien_hop_dong': thanh_vien_hop_dong,
        }
        
        return render(request, 'auth/hop_dong_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        return redirect('dungchung:profile')


@tai_khoan_login_required
def user_hoa_don_list_view(request):
    """View xem danh sách hóa đơn hàng tháng của người thuê"""
    user_info = get_user_khachthue_info(request)
    
    if not user_info:
        messages.error(request, 'Không tìm thấy thông tin tài khoản.')
        return redirect('dungchung:logout')
    
    # Kiểm tra quyền khách thuê
    if user_info['tai_khoan'].QUYEN_HAN != 'Khách thuê':
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('dungchung:trang_chu')
    
    tai_khoan = user_info['tai_khoan']
    khach_thue = user_info['khach_thue']
    
    # Lấy hợp đồng hiện tại của người thuê
    try:
        lich_su_hop_dong = LichSuHopDong.objects.filter(
            MA_KHACH_THUE=khach_thue,
            NGAY_ROI_DI__isnull=True
        ).select_related('MA_HOP_DONG__MA_PHONG').first()
        
        if not lich_su_hop_dong:
            messages.info(request, 'Bạn hiện không có hợp đồng nào để xem hóa đơn.')
            return render(request, 'auth/hoa_don_list.html', {
                'tai_khoan': tai_khoan,
                'khach_thue': khach_thue,
                'hoa_don_list': [],
                'phong_tro': None
            })
        
        phong_tro = lich_su_hop_dong.MA_HOP_DONG.MA_PHONG
        
        # Lọc theo năm và tháng nếu có
        year = request.GET.get('year')
        month = request.GET.get('month')
        
        # Lấy danh sách hóa đơn của phòng
        hoa_don_query = HoaDon.objects.filter(
            MA_PHONG=phong_tro
        ).order_by('-NGAY_LAP_HDON')
        
        if year:
            hoa_don_query = hoa_don_query.filter(NGAY_LAP_HDON__year=year)
        if month:
            hoa_don_query = hoa_don_query.filter(NGAY_LAP_HDON__month=month)
            
        hoa_don_list = hoa_don_query[:12]  # Giới hạn 12 hóa đơn gần nhất
        
        # Lấy danh sách năm có hóa đơn
        years = HoaDon.objects.filter(
            MA_PHONG=phong_tro
        ).dates('NGAY_LAP_HDON', 'year', order='DESC')
        
        context = {
            'tai_khoan': tai_khoan,
            'khach_thue': khach_thue,
            'hoa_don_list': hoa_don_list,
            'phong_tro': phong_tro,
            'years': years,
            'selected_year': year,
            'selected_month': month,
        }
        
        return render(request, 'auth/hoa_don_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        return redirect('dungchung:profile')


@tai_khoan_login_required
def user_hoa_don_detail_view(request, ma_hoa_don):
    """View xem chi tiết hóa đơn của người thuê"""
    user_info = get_user_khachthue_info(request)
    
    if not user_info:
        messages.error(request, 'Không tìm thấy thông tin tài khoản.')
        return redirect('dungchung:logout')
    
    # Kiểm tra quyền khách thuê
    if user_info['tai_khoan'].QUYEN_HAN != 'Khách thuê':
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('dungchung:trang_chu')
    
    tai_khoan = user_info['tai_khoan']
    khach_thue = user_info['khach_thue']
    
    try:
        # Lấy hợp đồng hiện tại của người thuê
        lich_su_hop_dong = LichSuHopDong.objects.filter(
            MA_KHACH_THUE=khach_thue,
            NGAY_ROI_DI__isnull=True
        ).select_related('MA_HOP_DONG__MA_PHONG').first()
        
        if not lich_su_hop_dong:
            messages.error(request, 'Bạn không có quyền xem hóa đơn này.')
            return redirect('dungchung:user_hoa_don_list')
        
        phong_tro = lich_su_hop_dong.MA_HOP_DONG.MA_PHONG
        
        # Lấy hóa đơn và kiểm tra quyền truy cập
        hoa_don = get_object_or_404(
            HoaDon.objects.select_related('MA_PHONG'),
            MA_HOA_DON=ma_hoa_don,
            MA_PHONG=phong_tro  # Chỉ cho phép xem hóa đơn của phòng mình
        )
        
        # Lấy danh sách khấu trừ
        khau_tru_list = KhauTru.objects.filter(
            MA_HOA_DON=hoa_don
        ).order_by('NGAYKHAUTRU')
        
        context = {
            'tai_khoan': tai_khoan,
            'khach_thue': khach_thue,
            'hoa_don': hoa_don,
            'phong_tro': phong_tro,
            'khau_tru_list': khau_tru_list,
        }
        
        return render(request, 'auth/hoa_don_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        return redirect('dungchung:user_hoa_don_list')