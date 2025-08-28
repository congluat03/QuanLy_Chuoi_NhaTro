from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import NguoiQuanLy, TaiKhoan, LichSuQuanLy # Assuming NguoiQuanLy is the model for managers
from apps.nhatro.models import KhuVuc
from django.contrib import messages
from django.db import transaction
import base64
import re
from datetime import date

def nhanvien_list(request):
    # Get filter and search parameters from request
    employee_filter = request.GET.getlist('employee_filter', [])
    search_query = request.GET.get('search', '')

    # Query all NguoiQuanLy records with prefetch for better performance
    quan_lys = NguoiQuanLy.objects.select_related('MA_TAI_KHOAN').prefetch_related(
        'lichsuquanly__MA_KHU_VUC'
    ).all().order_by('MA_QUAN_LY')

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

    # Thêm thông tin khu vực hiện tại cho mỗi quản lý
    for quan_ly in quan_lys:
        quan_ly.current_khu_vuc = quan_ly.lichsuquanly.filter(
            NGAY_KET_THUC_QL__isnull=True
        ).first()

    # Lấy danh sách tất cả khu vực để hiển thị bên trái
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')
    
    # Nhóm quản lý theo khu vực
    quan_ly_by_khu_vuc = {}
    quan_ly_no_area = []
    
    for quan_ly in quan_lys:
        if quan_ly.current_khu_vuc:
            khu_vuc_id = quan_ly.current_khu_vuc.MA_KHU_VUC.MA_KHU_VUC
            if khu_vuc_id not in quan_ly_by_khu_vuc:
                quan_ly_by_khu_vuc[khu_vuc_id] = {
                    'khu_vuc': quan_ly.current_khu_vuc.MA_KHU_VUC,
                    'quan_lys': []
                }
            quan_ly_by_khu_vuc[khu_vuc_id]['quan_lys'].append(quan_ly)
        else:
            quan_ly_no_area.append(quan_ly)

    # Paginate results (10 items per page)
    paginator = Paginator(quan_lys, 50)  # Tăng lên để hiển thị nhiều hơn
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/quanly/danhsach_quanly.html', {
        'quan_lys': page_obj,
        'khu_vucs': khu_vucs,
        'quan_ly_by_khu_vuc': quan_ly_by_khu_vuc,
        'quan_ly_no_area': quan_ly_no_area,
        'employee_filter': employee_filter,
        'search_query': search_query,
    })


def add_manager(request):
    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')
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
            ma_khu_vuc = form_data.get('MA_KHU_VUC')
            vi_tri_cong_viec = form_data.get('VI_TRI_CONG_VIEC')
            ngay_bat_dau = form_data.get('NGAY_BAT_DAU')

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
            if not ma_khu_vuc:
                form_errors['MA_KHU_VUC'] = 'Vui lòng chọn khu vực quản lý.'
            if not vi_tri_cong_viec:
                form_errors['VI_TRI_CONG_VIEC'] = 'Vị trí công việc là bắt buộc.'
            if not ngay_bat_dau:
                form_errors['NGAY_BAT_DAU'] = 'Ngày bắt đầu là bắt buộc.'

            # Validate khu vuc exists
            khu_vuc = None
            if ma_khu_vuc:
                try:
                    khu_vuc = KhuVuc.objects.get(MA_KHU_VUC=ma_khu_vuc)
                except KhuVuc.DoesNotExist:
                    form_errors['MA_KHU_VUC'] = 'Khu vực không tồn tại.'

            if form_errors:
                return render(request, 'admin/quanly/themsua_quanly.html', {
                    'form_data': form_data,
                    'form_errors': form_errors,
                    'khu_vucs': khu_vucs,
                })

            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Create TaiKhoan
                tk = TaiKhoan.create_tai_khoan(
                    tai_khoan=tai_khoan, 
                    mat_khau=mat_khau, 
                    quyen_han='Chủ trọ'
                )

                # Create NguoiQuanLy
                quan_ly = NguoiQuanLy.objects.create(
                    MA_TAI_KHOAN=tk,
                    TEN_QUAN_LY=ten_quan_ly,
                    NGAY_SINH_QL=ngay_sinh_ql,
                    GIOI_TINH_QL=gioi_tinh_ql,
                    SDT_QUAN_LY=sdt_quan_ly,
                    DIA_CHI_QL=dia_chi_ql,
                )

                # Create LichSuQuanLy - Thiết lập quản lý khu vực
                LichSuQuanLy.objects.create(
                    MA_KHU_VUC=khu_vuc,
                    MA_QUAN_LY=quan_ly,
                    NGAY_BAT_DAU_QL=ngay_bat_dau,
                    NGAY_KET_THUC_QL=None,  # Không có ngày kết thúc = đang quản lý
                    VI_TRI_CONG_VIEC=vi_tri_cong_viec,
                    LY_DO_KET_THUC=None
                )

            messages.success(request, f'Thêm nhân viên thành công! Đã thiết lập quản lý khu vực {khu_vuc.TEN_KHU_VUC}.')
            return redirect('thanhvien:nhanvien_list')

        except ValueError as e:
            form_errors['general'] = str(e)
            return render(request, 'admin/quanly/themsua_quanly.html', {
                'form_data': form_data,
                'form_errors': form_errors,
                'khu_vucs': khu_vucs,
            })
        except Exception as e:
            form_errors['general'] = f'Có lỗi xảy ra: {str(e)}'
            return render(request, 'admin/quanly/themsua_quanly.html', {
                'form_data': form_data,
                'form_errors': form_errors,
                'khu_vucs': khu_vucs,
            })

    return render(request, 'admin/quanly/themsua_quanly.html', {
        'form_data': {},
        'form_errors': {},
        'khu_vucs': khu_vucs,
    })

def edit_manager(request, ma_quan_ly):
    try:
        manager = NguoiQuanLy.objects.get(MA_QUAN_LY=ma_quan_ly)
    except NguoiQuanLy.DoesNotExist:
        messages.error(request, 'Nhân viên không tồn tại.')
        return redirect('thanhvien:nhanvien_list')

    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')
    
    # Lấy khu vực hiện tại mà quản lý đang phụ trách
    current_lich_su = LichSuQuanLy.objects.filter(
        MA_QUAN_LY=manager,
        NGAY_KET_THUC_QL__isnull=True
    ).first()
    
    if request.method == 'POST':
        form_data = request.POST
        form_errors = {}

        try:
            # Extract and validate form data - chỉ thông tin cá nhân
            ten_quan_ly = form_data.get('TEN_QUAN_LY')
            ngay_sinh_ql = form_data.get('NGAY_SINH_QL') or None
            gioi_tinh_ql = form_data.get('GIOI_TINH_QL') or None
            sdt_quan_ly = form_data.get('SDT_QUAN_LY')
            dia_chi_ql = form_data.get('DIA_CHI_QL') or None

            # Validate required fields - chỉ thông tin cá nhân
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
                    'khu_vucs': khu_vucs,
                    'current_lich_su': current_lich_su,
                })

            # Chỉ cập nhật thông tin cá nhân của nhân viên
            manager.TEN_QUAN_LY = ten_quan_ly
            manager.NGAY_SINH_QL = ngay_sinh_ql
            manager.GIOI_TINH_QL = gioi_tinh_ql
            manager.SDT_QUAN_LY = sdt_quan_ly
            manager.DIA_CHI_QL = dia_chi_ql
            manager.save()

            messages.success(request, 'Cập nhật thông tin cá nhân nhân viên thành công!')
            return redirect('thanhvien:nhanvien_list')

        except ValueError as e:
            form_errors['general'] = str(e)
            return render(request, 'admin/quanly/themsua_quanly.html', {
                'manager': manager,
                'form_data': form_data,
                'form_errors': form_errors,
                'khu_vucs': khu_vucs,
                'current_lich_su': current_lich_su,
            })
        except Exception as e:
            form_errors['general'] = f'Có lỗi xảy ra: {str(e)}'
            return render(request, 'admin/quanly/themsua_quanly.html', {
                'manager': manager,
                'form_data': form_data,
                'form_errors': form_errors,
                'khu_vucs': khu_vucs,
                'current_lich_su': current_lich_su,
            })

    return render(request, 'admin/quanly/themsua_quanly.html', {
        'manager': manager,
        'form_data': {},
        'form_errors': {},
        'khu_vucs': khu_vucs,
        'current_lich_su': current_lich_su,
    })
def delete_manager(request, ma_quan_ly):
    """Xóa nhân viên và tất cả dữ liệu liên quan"""
    if request.method == 'POST':
        try:
            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Retrieve the manager with related data
                try:
                    manager = NguoiQuanLy.objects.select_related('MA_TAI_KHOAN').get(MA_QUAN_LY=ma_quan_ly)
                except NguoiQuanLy.DoesNotExist:
                    messages.error(request, 'Nhân viên không tồn tại.')
                    return redirect('thanhvien:nhanvien_list')
                
                # Store manager name and TaiKhoan for better feedback
                ten_quan_ly = manager.TEN_QUAN_LY or f"Nhân viên ID {ma_quan_ly}"
                tai_khoan = manager.MA_TAI_KHOAN
                
                # Kết thúc tất cả lịch sử quản lý đang hoạt động (bulk update for performance)
                active_lich_su_count = LichSuQuanLy.objects.filter(
                    MA_QUAN_LY=manager,
                    NGAY_KET_THUC_QL__isnull=True
                ).update(
                    NGAY_KET_THUC_QL=date.today(),
                    LY_DO_KET_THUC='Nhân viên đã được xóa khỏi hệ thống'
                )
                
                # Kiểm tra xem có dữ liệu liên quan nào khác cần xử lý không
                # (Ví dụ: hợp đồng, hóa đơn do nhân viên tạo - tùy thuộc vào thiết kế database)
                
                # Delete the manager (cascade sẽ xóa các dữ liệu liên quan)
                manager.delete()
                
                # Delete the associated TaiKhoan if it exists and not referenced elsewhere
                if tai_khoan:
                    try:
                        tai_khoan.delete()
                    except Exception as e:
                        # Nếu TaiKhoan đang được sử dụng ở nơi khác, chỉ deactivate
                        tai_khoan.TRANG_THAI_TK = 'Đã khóa'
                        tai_khoan.save()
                        print(f"Warning: Could not delete TaiKhoan {tai_khoan.MA_TAI_KHOAN}, deactivated instead: {e}")
            
            # Thông báo thành công với thông tin chi tiết
            success_message = f'Xóa nhân viên "{ten_quan_ly}" thành công!'
            if active_lich_su_count > 0:
                success_message += f' Đã kết thúc {active_lich_su_count} lịch sử quản lý.'
            
            messages.success(request, success_message)
            return redirect('thanhvien:nhanvien_list')

        except Exception as e:
            # Log detailed error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error deleting manager {ma_quan_ly}: {str(e)}', exc_info=True)
            
            # User-friendly error message
            messages.error(request, f'Lỗi khi xóa nhân viên: {str(e)}. Vui lòng liên hệ quản trị viên nếu lỗi tiếp tục xảy ra.')
            return redirect('thanhvien:nhanvien_list')

    # If not POST, redirect to prevent accidental deletion
    messages.error(request, 'Yêu cầu không hợp lệ. Chỉ chấp nhận phương thức POST.')
    return redirect('thanhvien:nhanvien_list')

def transfer_manager_area(request, ma_quan_ly):
    """Chuyển nhân viên sang khu vực quản lý khác"""
    try:
        manager = NguoiQuanLy.objects.get(MA_QUAN_LY=ma_quan_ly)
    except NguoiQuanLy.DoesNotExist:
        messages.error(request, 'Nhân viên không tồn tại.')
        return redirect('thanhvien:nhanvien_list')

    khu_vucs = KhuVuc.objects.filter(MA_NHA_TRO=1).order_by('MA_KHU_VUC')
    
    # Lấy khu vực hiện tại mà quản lý đang phụ trách
    current_lich_su = LichSuQuanLy.objects.filter(
        MA_QUAN_LY=manager,
        NGAY_KET_THUC_QL__isnull=True
    ).first()
    
    if request.method == 'POST':
        form_data = request.POST
        form_errors = {}

        try:
            ma_khu_vuc_moi = form_data.get('MA_KHU_VUC_MOI')
            vi_tri_cong_viec_moi = form_data.get('VI_TRI_CONG_VIEC_MOI')
            ngay_bat_dau_moi = form_data.get('NGAY_BAT_DAU_MOI')
            ly_do_chuyen = form_data.get('LY_DO_CHUYEN', '').strip()

            # Validate required fields
            if not ma_khu_vuc_moi:
                form_errors['MA_KHU_VUC_MOI'] = 'Vui lòng chọn khu vực mới.'
            if not vi_tri_cong_viec_moi:
                form_errors['VI_TRI_CONG_VIEC_MOI'] = 'Vị trí công việc là bắt buộc.'
            if not ngay_bat_dau_moi:
                form_errors['NGAY_BAT_DAU_MOI'] = 'Ngày bắt đầu là bắt buộc.'
            if not ly_do_chuyen:
                form_errors['LY_DO_CHUYEN'] = 'Lý do chuyển khu vực là bắt buộc.'

            # Validate khu vuc moi exists
            khu_vuc_moi = None
            if ma_khu_vuc_moi:
                try:
                    khu_vuc_moi = KhuVuc.objects.get(MA_KHU_VUC=ma_khu_vuc_moi)
                    # Kiểm tra không chuyển về cùng khu vực
                    if current_lich_su and current_lich_su.MA_KHU_VUC.MA_KHU_VUC == int(ma_khu_vuc_moi):
                        form_errors['MA_KHU_VUC_MOI'] = 'Không thể chuyển về cùng khu vực hiện tại.'
                except KhuVuc.DoesNotExist:
                    form_errors['MA_KHU_VUC_MOI'] = 'Khu vực không tồn tại.'

            # Validate ngay bat dau
            from datetime import datetime
            if ngay_bat_dau_moi:
                try:
                    ngay_bat_dau_obj = datetime.strptime(ngay_bat_dau_moi, '%Y-%m-%d').date()
                    if current_lich_su and ngay_bat_dau_obj <= current_lich_su.NGAY_BAT_DAU_QL:
                        form_errors['NGAY_BAT_DAU_MOI'] = 'Ngày bắt đầu mới phải sau ngày bắt đầu khu vực hiện tại.'
                except ValueError:
                    form_errors['NGAY_BAT_DAU_MOI'] = 'Định dạng ngày không hợp lệ.'

            if form_errors:
                return render(request, 'admin/quanly/chuyen_khu_vuc.html', {
                    'manager': manager,
                    'current_lich_su': current_lich_su,
                    'khu_vucs': khu_vucs,
                    'form_data': form_data,
                    'form_errors': form_errors,
                })

            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Kết thúc lịch sử quản lý cũ nếu có
                if current_lich_su:
                    # Tính ngày kết thúc = ngày bắt đầu mới - 1 ngày
                    from datetime import timedelta
                    ngay_ket_thuc = ngay_bat_dau_obj - timedelta(days=1)
                    
                    current_lich_su.NGAY_KET_THUC_QL = ngay_ket_thuc
                    current_lich_su.LY_DO_KET_THUC = f'Chuyển sang khu vực {khu_vuc_moi.TEN_KHU_VUC}. Lý do: {ly_do_chuyen}'
                    current_lich_su.save()
                
                # Tạo lịch sử quản lý mới
                lich_su_moi = LichSuQuanLy.objects.create(
                    MA_KHU_VUC=khu_vuc_moi,
                    MA_QUAN_LY=manager,
                    NGAY_BAT_DAU_QL=ngay_bat_dau_moi,
                    NGAY_KET_THUC_QL=None,
                    VI_TRI_CONG_VIEC=vi_tri_cong_viec_moi,
                    LY_DO_KET_THUC=None
                )

            # Thông báo thành công
            if current_lich_su:
                success_message = f'Chuyển nhân viên {manager.TEN_QUAN_LY} từ khu vực {current_lich_su.MA_KHU_VUC.TEN_KHU_VUC} sang khu vực {khu_vuc_moi.TEN_KHU_VUC} thành công!'
            else:
                success_message = f'Phân công nhân viên {manager.TEN_QUAN_LY} vào khu vực {khu_vuc_moi.TEN_KHU_VUC} thành công!'
                
            messages.success(request, success_message)
            return redirect('thanhvien:nhanvien_list')

        except ValueError as e:
            form_errors['general'] = str(e)
            return render(request, 'admin/quanly/chuyen_khu_vuc.html', {
                'manager': manager,
                'current_lich_su': current_lich_su,
                'khu_vucs': khu_vucs,
                'form_data': form_data,
                'form_errors': form_errors,
            })
        except Exception as e:
            form_errors['general'] = f'Có lỗi xảy ra: {str(e)}'
            return render(request, 'admin/quanly/chuyen_khu_vuc.html', {
                'manager': manager,
                'current_lich_su': current_lich_su,
                'khu_vucs': khu_vucs,
                'form_data': form_data,
                'form_errors': form_errors,
            })

    return render(request, 'admin/quanly/chuyen_khu_vuc.html', {
        'manager': manager,
        'current_lich_su': current_lich_su,
        'khu_vucs': khu_vucs,
        'form_data': {},
        'form_errors': {},
    })