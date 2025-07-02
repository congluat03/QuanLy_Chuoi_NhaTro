from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import NguoiQuanLy, TaiKhoan # Assuming NguoiQuanLy is the model for managers
from django.contrib import messages
import base64
import re

def nhanvien_list(request):
    # Get filter and search parameters from request
    employee_filter = request.GET.getlist('employee_filter', [])
    search_query = request.GET.get('search', '')

    # Query all NguoiQuanLy records
    quan_lys = NguoiQuanLy.objects.all().order_by('MA_QUAN_LY')

    # Apply filters based on TRANG_THAI_TK from related TaiKhoan
    if employee_filter:
        query = Q()
        if 'active' in employee_filter:
            query |= Q(MA_TAI_KHOAN__TRANG_THAI_TK='Hoạt động')
        if 'resigned' in employee_filter:
            query |= Q(MA_TAI_KHOAN__TRANG_THAI_TK='Đã nghỉ')
        if 'probation' in employee_filter:
            query |= Q(MA_TAI_KHOAN__TRANG_THAI_TK='Thử việc')
        quan_lys = quan_lys.filter(query)

    # Apply search query
    if search_query:
        quan_lys = quan_lys.filter(
            Q(TEN_QUAN_LY__icontains=search_query) |
            Q(SDT_QUAN_LY__icontains=search_query) |
            Q(EMAIL_QL__icontains=search_query) |
            Q(DIA_CHI_QL__icontains=search_query)
        )

    # Paginate results (10 items per page)
    paginator = Paginator(quan_lys, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/quanly/danhsach_quanly.html', {
        'quan_lys': page_obj,
        'employee_filter': employee_filter,
        'search_query': search_query,
    })


def add_manager(request):
    if request.method == 'POST':
        form_data = request.POST
        form_errors = {}

        try:
            # Extract and validate form data
            ten_quan_ly = form_data.get('TEN_QUAN_LY')
            ngay_sinh_ql = form_data.get('NGAY_SINH_QL') or None
            gioi_tinh_ql = form_data.get('GIOI_TINH_QL') or None
            sdt_quan_ly = form_data.get('SDT_QUAN_LY')
            dia_chi_ql = form_data.get('DIA_CHI_QL') or None
            tai_khoan = form_data.get('TAI_KHOAN')
            mat_khau = form_data.get('MAT_KHAU')

            # Validate required fields
            if not ten_quan_ly:
                form_errors['TEN_QUAN_LY'] = 'Họ tên là bắt buộc.'
            if not ngay_sinh_ql:
                form_errors['NGAY_SINH_QL'] = 'Ngày sinh là bắt buộc.'
            if not gioi_tinh_ql:
                form_errors['GIOI_TINH_QL'] = 'Giới tính là bắt buộc.'
            if not sdt_quan_ly:
                form_errors['SDT_QUAN_LY'] = 'Số điện thoại là bắt buộc.'
            elif not re.match(r'^\d{10,11}$', sdt_quan_ly):
                form_errors['SDT_QUAN_LY'] = 'Số điện thoại phải gồm 10-11 chữ số.'
            if not tai_khoan:
                form_errors['TAI_KHOAN'] = 'Tài khoản là bắt buộc.'
            if not mat_khau:
                form_errors['MAT_KHAU'] = 'Mật khẩu là bắt buộc.'

            if form_errors:
                return render(request, 'admin/quanly/themsua_quanly.html', {
                    'form_data': form_data,
                    'form_errors': form_errors,
                })

            # Create TaiKhoan
            tk = TaiKhoan.create_tai_khoan(tai_khoan=tai_khoan, mat_khau=mat_khau)

            # Create NguoiQuanLy
            NguoiQuanLy.objects.create(
                MA_TAI_KHOAN=tk,
                TEN_QUAN_LY=ten_quan_ly,
                NGAY_SINH_QL=ngay_sinh_ql,
                GIOI_TINH_QL=gioi_tinh_ql,
                SDT_QUAN_LY=sdt_quan_ly,
                DIA_CHI_QL=dia_chi_ql,
            )

            messages.success(request, 'Thêm nhân viên thành công!')
            return redirect('thanhvien:nhanvien_list')

        except ValueError as e:
            form_errors['general'] = str(e)
            return render(request, 'admin/quanly/themsua_quanly.html', {
                'form_data': form_data,
                'form_errors': form_errors,
            })

    return render(request, 'admin/quanly/themsua_quanly.html', {
        'form_data': {},
        'form_errors': {},
    })

def edit_manager(request, ma_quan_ly):
    try:
        manager = NguoiQuanLy.objects.get(MA_QUAN_LY=ma_quan_ly)
    except NguoiQuanLy.DoesNotExist:
        messages.error(request, 'Nhân viên không tồn tại.')
        return redirect('thanhvien:nhanvien_list')

    if request.method == 'POST':
        form_data = request.POST
        form_errors = {}

        try:
            # Extract and validate form data
            ten_quan_ly = form_data.get('TEN_QUAN_LY')
            ngay_sinh_ql = form_data.get('NGAY_SINH_QL') or None
            gioi_tinh_ql = form_data.get('GIOI_TINH_QL') or None
            sdt_quan_ly = form_data.get('SDT_QUAN_LY')
            dia_chi_ql = form_data.get('DIA_CHI_QL') or None

            # Validate required fields
            if not ten_quan_ly:
                form_errors['TEN_QUAN_LY'] = 'Họ tên là bắt buộc.'
            if not ngay_sinh_ql:
                form_errors['NGAY_SINH_QL'] = 'Ngày sinh là bắt buộc.'
            if not gioi_tinh_ql:
                form_errors['GIOI_TINH_QL'] = 'Giới tính là bắt buộc.'
            if not sdt_quan_ly:
                form_errors['SDT_QUAN_LY'] = 'Số điện thoại là bắt buộc.'
            elif not re.match(r'^\d{10,11}$', sdt_quan_ly):
                form_errors['SDT_QUAN_LY'] = 'Số điện thoại phải gồm 10-11 chữ số.'

            if form_errors:
                return render(request, 'admin/quanly/themsua_quanly.html', {
                    'manager': manager,
                    'form_data': form_data,
                    'form_errors': form_errors,
                })

            # Update NguoiQuanLy
            manager.TEN_QUAN_LY = ten_quan_ly
            manager.NGAY_SINH_QL = ngay_sinh_ql
            manager.GIOI_TINH_QL = gioi_tinh_ql
            manager.SDT_QUAN_LY = sdt_quan_ly
            manager.DIA_CHI_QL = dia_chi_ql
            manager.save()

            messages.success(request, 'Cập nhật nhân viên thành công!')
            return redirect('thanhvien:nhanvien_list')

        except ValueError as e:
            form_errors['general'] = str(e)
            return render(request, 'admin/quanly/themsua_quanly.html', {
                'manager': manager,
                'form_data': form_data,
                'form_errors': form_errors,
            })

    return render(request, 'admin/quanly/themsua_quanly.html', {
        'manager': manager,
        'form_data': {},
        'form_errors': {},
    })
def delete_manager(request, ma_quan_ly):
    if request.method == 'POST':
        try:
            # Retrieve the manager
            manager = NguoiQuanLy.objects.get(MA_QUAN_LY=ma_quan_ly)
            # Store TaiKhoan for deletion
            tai_khoan = manager.MA_TAI_KHOAN
            # Delete the manager
            manager.delete()
            # Delete the associated TaiKhoan if it exists
            if tai_khoan:
                tai_khoan.delete()
            
            messages.success(request, 'Xóa nhân viên thành công!')
            return redirect('thanhvien:nhanvien_list')

        except NguoiQuanLy.DoesNotExist:
            messages.error(request, 'Nhân viên không tồn tại.')
            return redirect('thanhvien:nhanvien_list')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa nhân viên: {str(e)}')
            return redirect('thanhvien:nhanvien_list')

    # If not POST, redirect to prevent accidental deletion
    messages.error(request, 'Yêu cầu không hợp lệ.')
    return redirect('thanhvien:nhanvien_list')