from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from apps.thanhvien.models import TaiKhoan, NguoiQuanLy


def dashboard(request):
    # Kiểm tra authentication với session
    if not request.session.get('is_authenticated'):
        messages.warning(request, 'Vui lòng đăng nhập để truy cập trang quản trị.')
        return redirect('dungchung:login')
    
    # Kiểm tra quyền admin/chủ trọ
    vai_tro = request.session.get('vai_tro')
    if vai_tro not in ['Chủ trọ', 'admin']:
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('dungchung:trang_chu')
    
    # Lấy thông tin tài khoản và quản lý cho dashboard
    user_id = request.session.get('user_id')
    tai_khoan = None
    nguoi_quan_ly = None
    
    try:
        tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
        try:
            nguoi_quan_ly = NguoiQuanLy.objects.get(MA_TAI_KHOAN=tai_khoan)
        except NguoiQuanLy.DoesNotExist:
            nguoi_quan_ly = None
    except TaiKhoan.DoesNotExist:
        messages.error(request, 'Không tìm thấy thông tin tài khoản.')
        return redirect('dungchung:logout')
    
    context = {
        'username': request.session.get('username'),
        'vai_tro': vai_tro,
        'tai_khoan': tai_khoan,
        'nguoi_quan_ly': nguoi_quan_ly,
        # Thống kê (placeholder - có thể thêm sau)
        'total_rooms': 0,  # Sẽ tính từ database
        'total_tenants': 0,  # Sẽ tính từ database
        'monthly_revenue': 0,  # Sẽ tính từ database
        'pending_contracts': 0,  # Sẽ tính từ database
    }
    return render(request, 'admin/dashboard/dashboard.html', context)

def admin_profile(request):
    """View hiển thị thông tin cá nhân cho admin/chủ trọ"""
    # Kiểm tra authentication với session
    if not request.session.get('is_authenticated'):
        messages.warning(request, 'Vui lòng đăng nhập để truy cập.')
        return redirect('dungchung:login')
    
    # Kiểm tra quyền admin/chủ trọ
    vai_tro = request.session.get('vai_tro')
    if vai_tro not in ['Chủ trọ', 'admin']:
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return redirect('dungchung:trang_chu')
    
    # Lấy thông tin tài khoản và quản lý
    user_id = request.session.get('user_id')
    try:
        tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
        try:
            nguoi_quan_ly = NguoiQuanLy.objects.get(MA_TAI_KHOAN=tai_khoan)
        except NguoiQuanLy.DoesNotExist:
            nguoi_quan_ly = None
            
        context = {
            'tai_khoan': tai_khoan,
            'nguoi_quan_ly': nguoi_quan_ly,
            'username': request.session.get('username'),
            'vai_tro': vai_tro
        }
        return render(request, 'admin/profile/admin_profile.html', context)
        
    except TaiKhoan.DoesNotExist:
        messages.error(request, 'Không tìm thấy thông tin tài khoản.')
        return redirect('dungchung:logout')


def admin_logout(request):
    """Đăng xuất cho admin/chủ trọ"""
    if request.method == 'POST':
        # Lấy thông tin user trước khi xóa session để thông báo
        username = request.session.get('username', 'Admin')
        vai_tro = request.session.get('vai_tro', '')
        
        # Xóa toàn bộ session
        request.session.flush()
        
        # Thông báo đăng xuất thành công
        messages.success(request, f'Đăng xuất thành công! Hẹn gặp lại {username}.')
        
        # Redirect về trang login thay vì trang chủ
        return redirect('dungchung:login')
    
    # Nếu không phải POST, redirect về admin dashboard
    return redirect('admin')


def doi_mat_khau(request):
    """Đổi mật khẩu cho admin/chủ trọ"""
    # Kiểm tra session authentication
    if not request.session.get('is_authenticated'):
        messages.error(request, 'Bạn cần đăng nhập để đổi mật khẩu.')
        return redirect('dungchung:login')

    # Lấy thông tin user từ session
    user_id = request.session.get('user_id')
    vai_tro = request.session.get('vai_tro')
    
    if not user_id or vai_tro not in ['Chủ trọ', 'admin']:
        messages.error(request, 'Bạn không có quyền truy cập.')
        return redirect('dungchung:login')

    try:
        tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
        nguoi_quan_ly = None
        try:
            nguoi_quan_ly = NguoiQuanLy.objects.get(MA_TAI_KHOAN=tai_khoan)
        except NguoiQuanLy.DoesNotExist:
            pass
    except TaiKhoan.DoesNotExist:
        messages.error(request, 'Tài khoản không tồn tại.')
        return redirect('dungchung:login')

    if request.method == 'POST':
        mat_khau_cu = request.POST.get('mat_khau_cu')
        mat_khau_moi = request.POST.get('mat_khau_moi')
        xac_nhan_mat_khau = request.POST.get('xac_nhan_mat_khau')
        
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
            # Đổi mật khẩu
            tai_khoan.set_mat_khau(mat_khau_moi)
            tai_khoan.save()
            
            messages.success(request, 'Đổi mật khẩu thành công!')
            return redirect('dungchung:admin_profile')
        else:
            return render(request, 'admin/profile/doi_mat_khau.html', {
                'tai_khoan': tai_khoan,
                'nguoi_quan_ly': nguoi_quan_ly,
                'vai_tro': vai_tro,
                'form_errors': errors,
                'form_data': request.POST
            })

    return render(request, 'admin/profile/doi_mat_khau.html', {
        'tai_khoan': tai_khoan,
        'nguoi_quan_ly': nguoi_quan_ly,
        'vai_tro': vai_tro,
        'form_errors': {},
        'form_data': {}
    })


def chinh_sua_thong_tin(request):
    """Chỉnh sửa thông tin cá nhân cho admin/chủ trọ"""
    # Kiểm tra session authentication
    if not request.session.get('is_authenticated'):
        messages.error(request, 'Bạn cần đăng nhập để chỉnh sửa thông tin.')
        return redirect('dungchung:login')

    # Lấy thông tin user từ session
    user_id = request.session.get('user_id')
    vai_tro = request.session.get('vai_tro')
    
    if not user_id or vai_tro not in ['Chủ trọ', 'admin']:
        messages.error(request, 'Bạn không có quyền truy cập.')
        return redirect('dungchung:login')

    try:
        tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
        nguoi_quan_ly = None
        try:
            nguoi_quan_ly = NguoiQuanLy.objects.get(MA_TAI_KHOAN=tai_khoan)
        except NguoiQuanLy.DoesNotExist:
            # Tạo mới nếu chưa có thông tin quản lý
            nguoi_quan_ly = NguoiQuanLy.objects.create(MA_TAI_KHOAN=tai_khoan)
    except TaiKhoan.DoesNotExist:
        messages.error(request, 'Tài khoản không tồn tại.')
        return redirect('dungchung:login')

    if request.method == 'POST':
        ten_quan_ly = request.POST.get('ten_quan_ly', '').strip()
        email_ql = request.POST.get('email_ql', '').strip()
        sdt_quan_ly = request.POST.get('sdt_quan_ly', '').strip()
        dia_chi_ql = request.POST.get('dia_chi_ql', '').strip()
        gioi_tinh_ql = request.POST.get('gioi_tinh_ql', '')
        ngay_sinh_ql = request.POST.get('ngay_sinh_ql', '')
        
        errors = {}
        
        # Validate họ tên
        if not ten_quan_ly:
            errors['ten_quan_ly'] = 'Vui lòng nhập họ và tên.'
        elif len(ten_quan_ly) < 2:
            errors['ten_quan_ly'] = 'Họ tên phải có ít nhất 2 ký tự.'
        elif len(ten_quan_ly) > 200:
            errors['ten_quan_ly'] = 'Họ tên không được quá 200 ký tự.'
        
        # Validate email
        if email_ql:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email_ql):
                errors['email_ql'] = 'Email không đúng định dạng.'
            elif len(email_ql) > 200:
                errors['email_ql'] = 'Email không được quá 200 ký tự.'
        
        # Validate số điện thoại
        if sdt_quan_ly:
            import re
            phone_pattern = r'^(0[3|5|7|8|9])+([0-9]{8})$'
            if not re.match(phone_pattern, sdt_quan_ly):
                errors['sdt_quan_ly'] = 'Số điện thoại không đúng định dạng (10 số, bắt đầu 03/05/07/08/09).'
            elif len(sdt_quan_ly) > 15:
                errors['sdt_quan_ly'] = 'Số điện thoại không được quá 15 ký tự.'
        
        # Validate địa chỉ
        if dia_chi_ql and len(dia_chi_ql) > 500:
            errors['dia_chi_ql'] = 'Địa chỉ không được quá 500 ký tự.'
        
        # Validate ngày sinh
        if ngay_sinh_ql:
            try:
                from datetime import datetime, date
                ngay_sinh = datetime.strptime(ngay_sinh_ql, '%Y-%m-%d').date()
                today = date.today()
                age = today.year - ngay_sinh.year - ((today.month, today.day) < (ngay_sinh.month, ngay_sinh.day))
                if age < 16 or age > 100:
                    errors['ngay_sinh_ql'] = 'Tuổi phải từ 16 đến 100.'
            except ValueError:
                errors['ngay_sinh_ql'] = 'Ngày sinh không đúng định dạng.'
        
        if not errors:
            # Cập nhật thông tin
            nguoi_quan_ly.TEN_QUAN_LY = ten_quan_ly
            nguoi_quan_ly.EMAIL_QL = email_ql if email_ql else None
            nguoi_quan_ly.SDT_QUAN_LY = sdt_quan_ly if sdt_quan_ly else None
            nguoi_quan_ly.DIA_CHI_QL = dia_chi_ql if dia_chi_ql else None
            nguoi_quan_ly.GIOI_TINH_QL = gioi_tinh_ql if gioi_tinh_ql else None
            
            if ngay_sinh_ql:
                nguoi_quan_ly.NGAY_SINH_QL = datetime.strptime(ngay_sinh_ql, '%Y-%m-%d').date()
            
            nguoi_quan_ly.save()
            
            messages.success(request, 'Cập nhật thông tin thành công!')
            return redirect('dungchung:admin_profile')
        else:
            return render(request, 'admin/profile/chinh_sua_thong_tin.html', {
                'tai_khoan': tai_khoan,
                'nguoi_quan_ly': nguoi_quan_ly,
                'vai_tro': vai_tro,
                'form_errors': errors,
                'form_data': request.POST
            })

    return render(request, 'admin/profile/chinh_sua_thong_tin.html', {
        'tai_khoan': tai_khoan,
        'nguoi_quan_ly': nguoi_quan_ly,
        'vai_tro': vai_tro,
        'form_errors': {},
        'form_data': {}
    })


def profile(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Bạn cần đăng nhập để xem hồ sơ.')
        return redirect('dungchung:login')

    return render(request, 'admin/trangcanhan/thongtin_canhan.html', {
        'form_data': {},
        'form_errors': {},
    })