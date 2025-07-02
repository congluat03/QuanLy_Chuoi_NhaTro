from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import render
from .models import KhuVuc, NhaTro
from apps.dichvu.models import DichVu, LichSuApDungDichVu
from apps.thanhvien.models import NguoiQuanLy, LichSuQuanLy
from django.http import HttpResponse
from django.contrib import messages
from datetime import date
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
import json

def khuvuc_list(request):
    # Lấy danh sách dịch vụ và khu vực
    dich_vus = DichVu.objects.order_by('MA_DICH_VU')
    khu_vucs = KhuVuc.objects.order_by('MA_KHU_VUC').select_related('MA_NHA_TRO')
    
    # Check for active manager and get manager name for each khu_vuc
    for khu_vuc in khu_vucs:
        active_manager_record = LichSuQuanLy.objects.filter(
            MA_KHU_VUC=khu_vuc,
            NGAY_KET_THUC_QL__isnull=True
        ).select_related('MA_QUAN_LY').first()
        
        if active_manager_record:
            khu_vuc.has_active_manager = True
            khu_vuc.manager_name = active_manager_record.MA_QUAN_LY.TEN_QUAN_LY or f"Quản lý {active_manager_record.MA_QUAN_LY.MA_QUAN_LY}"

        else:
            khu_vuc.has_active_manager = False
            khu_vuc.manager_name = None
    
    # Phân trang: 8 mục mỗi trang
    khu_vucs_paginator = Paginator(khu_vucs, 8)
    
    # Lấy số trang riêng cho khu vực và dịch vụ
    khu_vuc_page_number = request.GET.get('khu_vuc_page')
    
    khu_vucs_page = khu_vucs_paginator.get_page(khu_vuc_page_number)
    
    context = {
        'dich_vus': dich_vus,
        'khu_vucs': khu_vucs_page,
    }
    return render(request, 'admin/khuvuc/danhsach_khuvuc.html', context)



def khuvuc_sua(request, khuVucId):
    try:
        khu_vuc = KhuVuc.objects.get(MA_KHU_VUC=khuVucId)
    except KhuVuc.DoesNotExist:
        messages.error(request, "Khu vực không tồn tại.")
        return redirect('dashboard_khuvuc')  # Thay bằng tên URL đúng trong hệ thống của bạn

    if request.method == "POST":
        ten_khu_vuc = request.POST.get("TEN_KHU_VUC")
        cap1 = request.POST.get("DV_HANH_CHINH_CAP1")
        cap2 = request.POST.get("DV_HANH_CHINH_CAP2")
        cap3 = request.POST.get("DV_HANH_CHINH_CAP3")

        khu_vuc.TEN_KHU_VUC = ten_khu_vuc
        khu_vuc.DV_HANH_CHINH_CAP1 = cap1
        khu_vuc.DV_HANH_CHINH_CAP2 = cap2
        khu_vuc.DV_HANH_CHINH_CAP3 = cap3
        khu_vuc.save()

        messages.success(request, "Cập nhật khu vực thành công.")
        return redirect("nhatro:khuvuc_list")

    return render(request, 'admin/khuvuc/themsua_khuvuc.html', {'khu_vuc': khu_vuc})

def khuvuc_them(request):
    if request.method == "POST":
        ten_khu_vuc = request.POST.get("TEN_KHU_VUC")
        cap1 = request.POST.get("DV_HANH_CHINH_CAP1")
        cap2 = request.POST.get("DV_HANH_CHINH_CAP2")
        cap3 = request.POST.get("DV_HANH_CHINH_CAP3")
        trang_thai = 'đang hoạt động' # Mặc định là 1 (hoạt động)
        # Lấy nhà trọ mặc định hoặc từ user đang đăng nhập
        nha_tro = get_object_or_404(NhaTro, pk=1)

        khu_vuc = KhuVuc.objects.create(
            MA_NHA_TRO=nha_tro,
            TEN_KHU_VUC=ten_khu_vuc,
            TRANG_THAI_KV=trang_thai,
            DV_HANH_CHINH_CAP1=cap1,
            DV_HANH_CHINH_CAP2=cap2,
            DV_HANH_CHINH_CAP3=cap3
        )

        messages.success(request, "Thêm khu vực thành công.")
        return redirect("nhatro:khuvuc_list")

    return render(request, 'admin/khuvuc/themsua_khuvuc.html', {'khu_vuc': None})

def xoa_khuvuc(request, ma_khu_vuc):
    khu_vuc = get_object_or_404(KhuVuc, MA_KHU_VUC=ma_khu_vuc)
    
    if request.method == 'POST':
        # Kiểm tra xem khu vực có phòng trọ liên quan không
        if khu_vuc.ds_phongtro.exists():
            messages.error(request, f"Khu vực '{khu_vuc.TEN_KHU_VUC}' không thể xóa vì đang có phòng trọ liên quan. Vui lòng xóa các phòng trọ trước khi xóa khu vực.")
            return redirect('nhatro:khuvuc_list')
        
        # Xóa khu vực (các dịch vụ liên quan sẽ tự động bị xóa do on_delete=models.CASCADE)
        khu_vuc_name = khu_vuc.TEN_KHU_VUC or f"Khu vực {khu_vuc.MA_KHU_VUC}"
        khu_vuc.delete()
        messages.success(request, f"Khu vực '{khu_vuc_name}' đã được xóa thành công.")
        return redirect('nhatro:khuvuc_list')
    
    # Nếu không phải POST, hiển thị trang xác nhận xóa
    context = {
        'khu_vuc': khu_vuc,
    }
    return redirect('nhatro:khuvuc_list')

def chitiet_khuvuc(request, khuVucId):
    # Tìm khu vực theo MA_KHU_VUC
    khu_vuc = get_object_or_404(
        KhuVuc.objects.prefetch_related(
            Prefetch(
                'lichsuquanly',
                queryset=LichSuQuanLy.objects.select_related('MA_QUAN_LY').order_by('-NGAY_BAT_DAU_QL')
            )
        ),
        MA_KHU_VUC=khuVucId
    )
    
    so_luong_phong_tro = khu_vuc.ds_phongtro.count()  # Số lượng phòng trọ
    dich_vu_khu_vucs = LichSuApDungDichVu.objects.filter(MA_KHU_VUC=khuVucId).select_related('MA_DICH_VU').order_by('-MA_AP_DUNG_DV')
    so_luong_dich_vu_dang_ap_dung = LichSuApDungDichVu.objects.filter(MA_KHU_VUC=khuVucId, NGAY_HUY_DV__isnull=True).count()  # Số lượng dịch vụ đang áp dụng
    quan_lys = NguoiQuanLy.objects.all()  # Lấy danh sách quản lý cho select

    context = {
        'khu_vuc': khu_vuc,
        'so_luong_phong_tro': so_luong_phong_tro,
        'dich_vu_khu_vucs': dich_vu_khu_vucs,
        'so_luong_dich_vu_dang_ap_dung': so_luong_dich_vu_dang_ap_dung,
        'quan_lys': quan_lys,
    }
    return render(request, 'admin/khuvuc/chitiet_khuvuc.html', context)





def thiet_lap_dich_vu(request, khu_vuc_id, dich_vu_id=None):
    khu_vuc = get_object_or_404(KhuVuc, MA_KHU_VUC=khu_vuc_id)
    dich_vus = DichVu.objects.all()
    lich_su_dich_vu = LichSuApDungDichVu.objects.filter(
        MA_KHU_VUC=khu_vuc,
        NGAY_HUY_DV__isnull=True
    )

    if request.method == "POST":
        action = request.POST.get("action1")
        dich_vu_id = request.POST.get("dich_vu_id")
        # return JsonResponse(dict(request.POST))
        # Kiểm tra dữ liệu đầu vào
        if not action or not dich_vu_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Thiếu thông tin hành động hoặc ID dịch vụ.'
                }, status=400)
            messages.error(request, 'Thiếu thông tin hành động hoặc ID dịch vụ.')
            return redirect("nhatro:thiet_lap_dich_vu", khu_vuc_id=khu_vuc.MA_KHU_VUC)

        try:
            dich_vu = get_object_or_404(DichVu, MA_DICH_VU=dich_vu_id)
        except:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Dịch vụ không tồn tại.'
                }, status=404)
            messages.error(request, 'Dịch vụ không tồn tại.')
            return redirect("nhatro:thiet_lap_dich_vu", khu_vuc_id=khu_vuc.MA_KHU_VUC)

        try:
            if action == "apply":
                gia_dich_vu_ad = request.POST.get("GIA_DICH_VU_AD")
                loai_dich_vu_ad = request.POST.get("LOAI_DICH_VU_AD")
                if not gia_dich_vu_ad or float(gia_dich_vu_ad) < 0:
                    raise ValueError("Giá dịch vụ không hợp lệ.")
                LichSuApDungDichVu.objects.create(
                    MA_KHU_VUC=khu_vuc,
                    MA_DICH_VU=dich_vu,
                    NGAY_AP_DUNG_DV=date.today(),
                    GIA_DICH_VU_AD=gia_dich_vu_ad,
                    LOAI_DICH_VU_AD=loai_dich_vu_ad
                )
                message = f"Áp dụng dịch vụ '{dich_vu.TEN_DICH_VU}' thành công."
            
            elif action == "update":
                lich_su_id = request.POST.get("lich_su_id")
                lich_su = get_object_or_404(LichSuApDungDichVu, MA_AP_DUNG_DV=lich_su_id)
                gia_dich_vu_ad = request.POST.get("GIA_DICH_VU_AD")
                if not gia_dich_vu_ad or float(gia_dich_vu_ad) < 0:
                    raise ValueError("Giá dịch vụ không hợp lệ.")
                lich_su.GIA_DICH_VU_AD = gia_dich_vu_ad
                lich_su.LOAI_DICH_VU_AD = request.POST.get("LOAI_DICH_VU_AD")
                lich_su.save()
                message = f"Cập nhật dịch vụ '{dich_vu.TEN_DICH_VU}' thành công."
            
            elif action == "cancel":
                lich_su_id = request.POST.get("lich_su_id")
                lich_su = get_object_or_404(LichSuApDungDichVu, MA_AP_DUNG_DV=lich_su_id)
                lich_su.NGAY_HUY_DV = date.today()
                lich_su.save()
                message = f"Hủy áp dụng dịch vụ '{dich_vu.TEN_DICH_VU}' thành công."
            
            else:
                raise ValueError("Hành động không hợp lệ.")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': message
                })
            
            messages.success(request, message)
            return redirect("nhatro:thiet_lap_dich_vu", khu_vuc_id=khu_vuc.MA_KHU_VUC)
        
        except ValueError as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
            messages.error(request, str(e))
            return redirect("nhatro:thiet_lap_dich_vu", khu_vuc_id=khu_vuc.MA_KHU_VUC)
        
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Lỗi hệ thống. Vui lòng thử lại sau.'
                }, status=500)
            messages.error(request, 'Lỗi hệ thống. Vui lòng thử lại sau.')
            return redirect("nhatro:thiet_lap_dich_vu", khu_vuc_id=khu_vuc.MA_KHU_VUC)

    context = {
        "khu_vuc": khu_vuc,
        "dich_vus": dich_vus,
        "lich_su_dich_vu": lich_su_dich_vu,
    }
    return render(request, "admin/khuvuc/thietlap_dichvu.html", context)
def thietlap_nguoiquanly(request, khuVucId=None):
    nguoi_quan_lys = NguoiQuanLy.objects.all()

    if request.method == 'POST':
        ma_quan_ly = request.POST.get('MA_QUAN_LY')
        MA_KHU_VUC = request.POST.get('MA_KHU_VUC')
        ngay_bat_dau = request.POST.get('NGAY_BAT_DAU_QL')

        try:
            nguoi_quan_ly = NguoiQuanLy.objects.get(MA_QUAN_LY=ma_quan_ly)
            khu_vuc_post = KhuVuc.objects.get(MA_KHU_VUC=MA_KHU_VUC)

            # Kết thúc người quản lý hiện tại nếu có
            active_lichsu = LichSuQuanLy.objects.filter(
                MA_KHU_VUC=khu_vuc_post,
                NGAY_KET_THUC_QL__isnull=True
            ).first()

            if active_lichsu:
                active_lichsu.NGAY_KET_THUC_QL = ngay_bat_dau
                active_lichsu.LY_DO_KET_THUC = 'Thay đổi người quản lý'
                active_lichsu.save()

            # Tạo bản ghi mới
            LichSuQuanLy.objects.create(
                MA_KHU_VUC=khu_vuc_post,
                MA_QUAN_LY=nguoi_quan_ly,
                NGAY_BAT_DAU_QL=ngay_bat_dau
            )

            messages.success(request, 'Thiết lập người quản lý thành công!')
            return redirect('nhatro:khuvuc_list')

        except NguoiQuanLy.DoesNotExist:
            messages.error(request, 'Người quản lý không tồn tại.')
        except KhuVuc.DoesNotExist:
            messages.error(request, 'Khu vực không tồn tại.')
        except Exception as e:
            messages.error(request, f'Lỗi khi thiết lập người quản lý: {str(e)}')

    # Nếu là GET
    if khuVucId is not None:
        khu_vuc = get_object_or_404(KhuVuc, MA_KHU_VUC=khuVucId)
    else:
        messages.error(request, 'Thiếu thông tin khu vực cần thiết lập.')
        return redirect('nhatro:khuvuc_list')

    context = {
        'khu_vuc': khu_vuc,
        'nguoi_quan_lys': nguoi_quan_lys,
    }
    return render(request, 'admin/khuvuc/thieplap_nguoiquanly.html', context)
def dung_quanly(request, khuVucId):
    try:
        khu_vuc = KhuVuc.objects.get(MA_KHU_VUC=khuVucId)
        active_lichsu = LichSuQuanLy.objects.filter(
            MA_KHU_VUC=khu_vuc,
            NGAY_KET_THUC_QL__isnull=True
        ).first()

        if not active_lichsu:
            messages.error(request, 'Khu vực này hiện không có người quản lý hoạt động.')
            return redirect('nhatro:danhsach_khuvuc')

        context = {
            'khu_vuc': khu_vuc,
            'nguoi_quan_ly': active_lichsu.MA_QUAN_LY,
            'action' : 'dungQuanLy'
        }

        if request.method == 'POST':
            ngay_ket_thuc = request.POST.get('NGAY_KET_THUC_QL')
            ly_do_ket_thuc = request.POST.get('LY_DO_KET_THUC')

            try:
                active_lichsu.NGAY_KET_THUC_QL = ngay_ket_thuc
                active_lichsu.LY_DO_KET_THUC = ly_do_ket_thuc
                active_lichsu.save()

                messages.success(request, 'Dừng quản lý thành công!')
                return redirect('nhatro:khuvuc_list')
            except Exception as e:
                messages.error(request, f'Lỗi khi dừng quản lý: {str(e)}')
                return render(request, 'admin/khuvuc/thieplap_nguoiquanly.html', context)

        return render(request, 'admin/khuvuc/thieplap_nguoiquanly.html', context)

    except KhuVuc.DoesNotExist:
        messages.error(request, 'Khu vực không tồn tại.')
        return redirect('nhatro:khuvuc_list')
