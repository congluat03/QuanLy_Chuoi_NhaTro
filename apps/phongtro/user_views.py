from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
from .models import PhongTro, CocPhong, LoaiPhong
from apps.nhatro.models import KhuVuc, NhaTro


def tim_phong(request):
    """View tìm kiếm phòng trọ"""
    # Lấy tất cả phòng (không chỉ phòng trống)
    phongs = PhongTro.objects.all().select_related(
        'MA_LOAI_PHONG', 'MA_KHU_VUC', 'MA_KHU_VUC__MA_NHA_TRO'
    )
    
    # Các filter parameters
    ten_phong = request.GET.get('ten_phong', '').strip()
    gia_min = request.GET.get('gia_min', '').strip()
    gia_max = request.GET.get('gia_max', '').strip()
    dien_tich_min = request.GET.get('dien_tich_min', '').strip()
    dien_tich_max = request.GET.get('dien_tich_max', '').strip()
    khu_vuc = request.GET.get('khu_vuc', '').strip()
    loai_phong = request.GET.get('loai_phong', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()
    
    # Áp dụng filters
    if ten_phong:
        phongs = phongs.filter(TEN_PHONG__icontains=ten_phong)
    
    if gia_min:
        try:
            phongs = phongs.filter(GIA_PHONG__gte=float(gia_min))
        except ValueError:
            pass
    
    if gia_max:
        try:
            phongs = phongs.filter(GIA_PHONG__lte=float(gia_max))
        except ValueError:
            pass
    
    if dien_tich_min:
        try:
            phongs = phongs.filter(DIEN_TICH__gte=float(dien_tich_min))
        except ValueError:
            pass
    
    if dien_tich_max:
        try:
            phongs = phongs.filter(DIEN_TICH__lte=float(dien_tich_max))
        except ValueError:
            pass
    
    if khu_vuc:
        try:
            phongs = phongs.filter(MA_KHU_VUC=int(khu_vuc))
        except ValueError:
            pass
    
    if loai_phong:
        try:
            phongs = phongs.filter(MA_LOAI_PHONG=int(loai_phong))
        except ValueError:
            pass
    
    if trang_thai:
        phongs = phongs.filter(TRANG_THAI_P=trang_thai)
    
    # Pagination
    paginator = Paginator(phongs, 12)  # 12 phòng mỗi trang
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
            'ten_phong': ten_phong,
            'gia_min': gia_min,
            'gia_max': gia_max,
            'dien_tich_min': dien_tich_min,
            'dien_tich_max': dien_tich_max,
            'khu_vuc': khu_vuc,
            'loai_phong': loai_phong,
            'trang_thai': trang_thai,
        },
        'total_phongs': paginator.count,
    }
    
    return render(request, 'user/phongtro/tim_phong.html', context)


def chi_tiet_phong(request, ma_phong):
    """View chi tiết phòng"""
    phong = get_object_or_404(
        PhongTro.objects.select_related(
            'MA_LOAI_PHONG', 'MA_KHU_VUC', 'MA_KHU_VUC__MA_NHA_TRO'
        ),
        MA_PHONG=ma_phong       
    )
    
    context = {
        'phong': phong,
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


