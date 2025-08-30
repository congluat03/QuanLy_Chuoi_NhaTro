from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal
from apps.thanhvien.models import TaiKhoan, NguoiQuanLy
from apps.nhatro.models import NhaTro, KhuVuc
from apps.phongtro.models import PhongTro, LoaiPhong
from apps.hopdong.models import HopDong, LichSuHopDong
from apps.khachthue.models import KhachThue
from apps.hoadon.models import HoaDon, CHITIETHOADON, PHIEUTHU
from apps.dichvu.models import DichVu


def dashboard(request):
    # Tính toán thống kê tổng quan
    stats = calculate_dashboard_stats()
    
    return render(request, 'admin/dashboard/dashboard.html', {
        'stats': stats
    })

def calculate_dashboard_stats():
    """Tính toán tất cả thống kê cho dashboard"""
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year
    last_month = (today.replace(day=1) - timedelta(days=1)).month
    last_month_year = (today.replace(day=1) - timedelta(days=1)).year
    
    # Thống kê tổng quan
    tong_so_phong = PhongTro.objects.count()
    
    # Đếm phòng đang ở từ HopDong
    phong_dang_o = PhongTro.objects.filter(
        hopdong__in=HopDong.objects.filter(
            TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc', 'Đang báo kết thúc']
        )
    ).distinct().count()
    
    phong_trong = tong_so_phong - phong_dang_o
    ty_le_cong_suat = round((phong_dang_o / tong_so_phong * 100) if tong_so_phong > 0 else 0, 1)
    
    # Doanh thu tháng hiện tại
    doanh_thu_thang = PHIEUTHU.objects.filter(
        NGAY_THU__month=current_month,
        NGAY_THU__year=current_year
    ).aggregate(total=Sum('SO_TIEN'))['total'] or 0
    
    # Doanh thu tháng trước
    doanh_thu_thang_truoc = PHIEUTHU.objects.filter(
        NGAY_THU__month=last_month,
        NGAY_THU__year=last_month_year
    ).aggregate(total=Sum('SO_TIEN'))['total'] or 0
    
    # Tính % thay đổi doanh thu
    tang_giam_doanh_thu = 0
    if doanh_thu_thang_truoc > 0:
        tang_giam_doanh_thu = round(
            ((doanh_thu_thang - doanh_thu_thang_truoc) / doanh_thu_thang_truoc) * 100, 1
        )
    
    # Tính công nợ
    tong_cong_no = 0
    so_khach_no = 0
    
    # Lấy tất cả hợp đồng đang hoạt động
    hop_dong_hoat_dong = HopDong.objects.filter(
        TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc', 'Đang báo kết thúc']
    )
    
    for hop_dong in hop_dong_hoat_dong:
        # Tính tổng hóa đơn chưa thanh toán
        tong_hoa_don = HoaDon.objects.filter(
            MA_HOP_DONG=hop_dong
        ).aggregate(total=Sum('TONG_TIEN'))['total'] or 0
        
        # Tính tổng đã thanh toán
        tong_da_thanh_toan = PHIEUTHU.objects.filter(
            MA_HOA_DON__MA_HOP_DONG=hop_dong
        ).aggregate(total=Sum('SO_TIEN'))['total'] or 0
        
        # Tính nợ
        no_cua_hop_dong = tong_hoa_don - tong_da_thanh_toan
        if no_cua_hop_dong > 0:
            tong_cong_no += no_cua_hop_dong
            so_khach_no += 1
    
    # Thống kê theo khu vực
    khu_vuc_stats = []
    for khu_vuc in KhuVuc.objects.all():
        kv_stat = calculate_area_stats(khu_vuc, current_month, current_year, last_month, last_month_year)
        khu_vuc_stats.append(kv_stat)
    
    # Doanh thu 6 tháng gần đây
    doanh_thu_6_thang = []
    for i in range(5, -1, -1):
        target_date = today - timedelta(days=30 * i)
        month = target_date.month
        year = target_date.year
        
        doanh_thu = PHIEUTHU.objects.filter(
            NGAY_THU__month=month,
            NGAY_THU__year=year
        ).aggregate(total=Sum('SO_TIEN'))['total'] or 0
        
        doanh_thu_6_thang.append({
            'thang': month,
            'nam': year,
            'doanh_thu': doanh_thu,
            'ty_le': min(100, (doanh_thu / max(doanh_thu_thang, 1)) * 100) if doanh_thu_thang > 0 else 0
        })
    
    # Hợp đồng sắp hết hạn (trong 30 ngày)
    hop_dong_sap_het_han = HopDong.objects.filter(
        TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc'],
        NGAY_TRA_PHONG__lte=today + timedelta(days=30),
        NGAY_TRA_PHONG__gte=today
    ).select_related('MA_PHONG').prefetch_related('lichsuhopdong__MA_KHACH_THUE')[:10]
    
    hop_dong_list = []
    for hd in hop_dong_sap_het_han:
        chu_hop_dong = hd.lichsuhopdong.filter(MOI_QUAN_HE='Chủ hợp đồng').first()
        hop_dong_list.append({
            'phong_ten': hd.MA_PHONG.TEN_PHONG,
            'khach_thue_ten': chu_hop_dong.MA_KHACH_THUE.HO_TEN_KT if chu_hop_dong else 'Chưa có chủ hợp đồng',
            'con_lai_ngay': (hd.NGAY_TRA_PHONG - today).days
        })
    
    # Top khách nợ nhiều nhất
    top_khach_no = []
    for hop_dong in hop_dong_hoat_dong[:10]:
        tong_hoa_don = HoaDon.objects.filter(
            MA_HOP_DONG=hop_dong
        ).aggregate(total=Sum('TONG_TIEN'))['total'] or 0
        
        tong_da_thanh_toan = PHIEUTHU.objects.filter(
            MA_HOA_DON__MA_HOP_DONG=hop_dong
        ).aggregate(total=Sum('SO_TIEN'))['total'] or 0
        
        no = tong_hoa_don - tong_da_thanh_toan
        if no > 0:
            chu_hop_dong = hop_dong.lichsuhopdong.filter(MOI_QUAN_HE='Chủ hợp đồng').first()
            if chu_hop_dong:
                top_khach_no.append({
                    'ho_ten': chu_hop_dong.MA_KHACH_THUE.HO_TEN_KT,
                    'phong_ten': hop_dong.MA_PHONG.TEN_PHONG,
                    'so_tien_no': no
                })
    
    # Sắp xếp theo số tiền nợ giảm dần
    top_khach_no = sorted(top_khach_no, key=lambda x: x['so_tien_no'], reverse=True)[:5]
    
    # Thống kê hiệu suất
    doanh_thu_tb_phong = doanh_thu_thang / max(phong_dang_o, 1) if phong_dang_o > 0 else 0
    
    # Thời gian thuê trung bình (tính từ hợp đồng đã kết thúc)
    hop_dong_da_ket_thuc = HopDong.objects.filter(
        TRANG_THAI_HD='Đã kết thúc'
    )
    
    tong_thoi_gian = 0
    so_hop_dong = 0
    for hd in hop_dong_da_ket_thuc:
        if hd.NGAY_NHAN_PHONG and hd.NGAY_TRA_PHONG:
            thoi_gian = (hd.NGAY_TRA_PHONG - hd.NGAY_NHAN_PHONG).days / 30
            tong_thoi_gian += thoi_gian
            so_hop_dong += 1
    
    thoi_gian_thue_tb = round(tong_thoi_gian / max(so_hop_dong, 1), 1) if so_hop_dong > 0 else 0
    
    # Tỷ lệ gia hạn (số hợp đồng có lịch sử gia hạn / tổng hợp đồng)
    hop_dong_gia_han = HopDong.objects.filter(lichsugiahan__LOAI_DC='Gia hạn hợp đồng').distinct().count()
    tong_hop_dong = HopDong.objects.count()
    ty_le_gia_han = round((hop_dong_gia_han / max(tong_hop_dong, 1)) * 100, 1)
    
    # Xu hướng tháng này
    hop_dong_moi_thang = HopDong.objects.filter(
        NGAY_LAP_HD__month=current_month,
        NGAY_LAP_HD__year=current_year
    ).count()
    
    hop_dong_ket_thuc_thang = HopDong.objects.filter(
        NGAY_TRA_PHONG__month=current_month,
        NGAY_TRA_PHONG__year=current_year,
        TRANG_THAI_HD='Đã kết thúc'
    ).count()
    
    khach_thue_moi_thang = 0  # Tạm thời set 0 vì model chưa có trường NGAY_TAO
    
    phieu_thu_thang = PHIEUTHU.objects.filter(
        NGAY_THU__month=current_month,
        NGAY_THU__year=current_year
    ).count()
    
    # Cảnh báo hệ thống
    phong_qua_han = HopDong.objects.filter(
        TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc'],
        NGAY_TRA_PHONG__lt=today
    ).count()
    
    hoa_don_qua_han = HoaDon.objects.filter(
        TRANG_THAI_HDON='Chưa thanh toán',
        NGAY_LAP_HDON__lt=today - timedelta(days=7)  # Quá hạn 7 ngày
    ).count()
    
    # Khu vực công suất thấp (<60%)
    phong_cong_suat_thap = 0
    for kv in KhuVuc.objects.all():
        phong_kv = PhongTro.objects.filter(MA_KHU_VUC=kv).count()
        phong_o_kv = PhongTro.objects.filter(
            MA_KHU_VUC=kv,
            hopdong__in=HopDong.objects.filter(
                TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc', 'Đang báo kết thúc']
            )
        ).distinct().count()
        
        cong_suat_kv = (phong_o_kv / max(phong_kv, 1)) * 100
        if cong_suat_kv < 60:
            phong_cong_suat_thap += 1
    
    # Quick stats
    tong_khach_thue = KhachThue.objects.count()
    tong_hop_dong_hoat_dong = HopDong.objects.filter(
        TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc', 'Đang báo kết thúc']
    ).count()
    
    tong_hoa_don_thang = HoaDon.objects.filter(
        NGAY_LAP_HDON__month=current_month,
        NGAY_LAP_HDON__year=current_year
    ).count()
    
    phong_bao_tri = PhongTro.objects.filter(TRANG_THAI_P='Bảo trì').count()
    
    # Thống kê phòng tăng trong tháng (giả định)
    tang_phong_thang_nay = 0  # Tạm thời set 0 vì model chưa có trường NGAY_TAO_PHONG
    
    # Thời gian phòng trống trung bình (giả định)
    thoi_gian_trong_tb = 7  # Tạm thời hard-code, có thể tính toán chi tiết hơn
    
    return {
        # Thống kê chính
        'tong_so_phong': tong_so_phong,
        'phong_dang_o': phong_dang_o,
        'ty_le_cong_suat': ty_le_cong_suat,
        'doanh_thu_thang': doanh_thu_thang,
        'tang_giam_doanh_thu': tang_giam_doanh_thu,
        'tong_cong_no': tong_cong_no,
        'so_khach_no': so_khach_no,
        'tang_phong_thang_nay': tang_phong_thang_nay,
        
        # Thống kê theo khu vực
        'khu_vuc_stats': khu_vuc_stats,
        
        # Tổng toàn hệ thống
        'tong_tat_ca_phong': tong_so_phong,
        'tong_phong_dang_o': phong_dang_o,
        'tong_phong_trong': phong_trong,
        'tong_doanh_thu_thang': doanh_thu_thang,
        'tong_cong_no_he_thong': tong_cong_no,
        
        # Biểu đồ doanh thu
        'doanh_thu_6_thang': doanh_thu_6_thang,
        
        # Danh sách cảnh báo
        'hop_dong_sap_het_han': hop_dong_list,
        'top_khach_no': top_khach_no,
        
        # Hiệu suất kinh doanh
        'doanh_thu_tb_phong': doanh_thu_tb_phong,
        'thoi_gian_thue_tb': thoi_gian_thue_tb,
        'ty_le_gia_han': ty_le_gia_han,
        'thoi_gian_trong_tb': thoi_gian_trong_tb,
        
        # Xu hướng tháng này
        'hop_dong_moi_thang': hop_dong_moi_thang,
        'hop_dong_ket_thuc_thang': hop_dong_ket_thuc_thang,
        'khach_thue_moi_thang': khach_thue_moi_thang,
        'phieu_thu_thang': phieu_thu_thang,
        
        # Cảnh báo
        'canh_bao': {
            'phong_qua_han': phong_qua_han,
            'hoa_don_qua_han': hoa_don_qua_han,
            'phong_cong_suat_thap': phong_cong_suat_thap
        },
        
        # Quick stats
        'tong_khach_thue': tong_khach_thue,
        'tong_hop_dong_hoat_dong': tong_hop_dong_hoat_dong,
        'tong_hoa_don_thang': tong_hoa_don_thang,
        'tong_phieu_thu_thang': phieu_thu_thang,
        'phong_bao_tri': phong_bao_tri,
        'diem_danh_gia_tb': 4.2  # Tạm thời hard-code
    }

def calculate_area_stats(khu_vuc, current_month, current_year, last_month, last_month_year):
    """Tính thống kê cho một khu vực cụ thể"""
    # Thống kê phòng trong khu vực
    tong_phong = PhongTro.objects.filter(MA_KHU_VUC=khu_vuc).count()
    
    phong_dang_o = PhongTro.objects.filter(
        MA_KHU_VUC=khu_vuc,
        hopdong__in=HopDong.objects.filter(
            TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc', 'Đang báo kết thúc']
        )
    ).distinct().count()
    
    phong_trong = tong_phong - phong_dang_o
    ty_le_thue = round((phong_dang_o / max(tong_phong, 1)) * 100, 1) if tong_phong > 0 else 0
    
    # Doanh thu khu vực tháng này
    doanh_thu_thang = PHIEUTHU.objects.filter(
        MA_HOA_DON__MA_HOP_DONG__MA_PHONG__MA_KHU_VUC=khu_vuc,
        NGAY_THU__month=current_month,
        NGAY_THU__year=current_year
    ).aggregate(total=Sum('SO_TIEN'))['total'] or 0
    
    # Doanh thu tháng trước
    doanh_thu_thang_truoc = PHIEUTHU.objects.filter(
        MA_HOA_DON__MA_HOP_DONG__MA_PHONG__MA_KHU_VUC=khu_vuc,
        NGAY_THU__month=last_month,
        NGAY_THU__year=last_month_year
    ).aggregate(total=Sum('SO_TIEN'))['total'] or 0
    
    # Tính % thay đổi
    tang_giam_doanh_thu = 0
    if doanh_thu_thang_truoc > 0:
        tang_giam_doanh_thu = round(
            ((doanh_thu_thang - doanh_thu_thang_truoc) / doanh_thu_thang_truoc) * 100, 1
        )
    
    # Công nợ khu vực
    cong_no = 0
    so_khach_no = 0
    
    hop_dong_kv = HopDong.objects.filter(
        MA_PHONG__MA_KHU_VUC=khu_vuc,
        TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc', 'Đang báo kết thúc']
    )
    
    for hop_dong in hop_dong_kv:
        tong_hoa_don = HoaDon.objects.filter(
            MA_HOP_DONG=hop_dong
        ).aggregate(total=Sum('TONG_TIEN'))['total'] or 0
        
        tong_da_thanh_toan = PHIEUTHU.objects.filter(
            MA_HOA_DON__MA_HOP_DONG=hop_dong
        ).aggregate(total=Sum('SO_TIEN'))['total'] or 0
        
        no_hop_dong = tong_hoa_don - tong_da_thanh_toan
        if no_hop_dong > 0:
            cong_no += no_hop_dong
            so_khach_no += 1
    
    # Hợp đồng sắp hết hạn trong khu vực
    hop_dong_sap_het_han = HopDong.objects.filter(
        MA_PHONG__MA_KHU_VUC=khu_vuc,
        TRANG_THAI_HD__in=['Đang hoạt động', 'Sắp kết thúc'],
        NGAY_TRA_PHONG__lte=timezone.now().date() + timedelta(days=30),
        NGAY_TRA_PHONG__gte=timezone.now().date()
    ).count()
    
    # Số quản lý trong khu vực (giả định mỗi khu vực có 1 quản lý)
    so_quan_ly = 1  # Tạm thời set 1 vì chưa có quan hệ quản lý-khu vực
    
    return {
        'ma_khu_vuc': khu_vuc.MA_KHU_VUC,
        'ten_khu_vuc': khu_vuc.TEN_KHU_VUC,
        'dia_chi': khu_vuc.dia_chi_day_du,
        'so_quan_ly': so_quan_ly,
        'tong_phong': tong_phong,
        'phong_dang_o': phong_dang_o,
        'phong_trong': phong_trong,
        'ty_le_thue': ty_le_thue,
        'doanh_thu_thang': doanh_thu_thang,
        'tang_giam_doanh_thu': tang_giam_doanh_thu,
        'cong_no': cong_no,
        'so_khach_no': so_khach_no,
        'hop_dong_sap_het_han': hop_dong_sap_het_han
    }

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