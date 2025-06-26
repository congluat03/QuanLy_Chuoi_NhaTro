from django.db import models
from apps.phongtro.models import PhongTro
from apps.hopdong.models import HopDong
from apps.dichvu.models import ChiSoDichVu
from django.utils import timezone
from datetime import datetime
import uuid

# Create your models here.
# Model for hoadon
class HoaDon(models.Model):
    MA_HOA_DON = models.AutoField(primary_key=True)
    MA_PHONG = models.ForeignKey(
        'phongtro.PhongTro',
        on_delete=models.CASCADE,
        db_column='MA_PHONG',
        related_name='hoadon'
    )
    LOAI_HOA_DON = models.CharField(max_length=50, null=True, blank=True)
    NGAY_LAP_HDON = models.DateField(null=True, blank=True)
    TIEN_PHONG = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    TIEN_DICH_VU = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    TIEN_COC = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    TIEN_KHAU_TRU = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    TONG_TIEN = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    TRANG_THAI_HDON = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Hóa đơn {self.MA_HOA_DON} - Phòng {self.MA_PHONG_id}"

    class Meta:
        db_table = 'hoadon'
    @staticmethod
    def validate_required_fields(data):
        required_fields = ['MA_PHONG', 'LOAI_HOA_DON', 'NGAY_LAP_HDON', 
                         'TIEN_PHONG', 'TIEN_DICH_VU', 'TIEN_COC', 'TIEN_KHAU_TRU', 'TONG_TIEN']
        errors = []
        for field in required_fields:
            if not data.get(field):
                errors.append(f'Trường {field} là bắt buộc.')
        return errors

    @staticmethod
    def validate_phong_and_hop_dong(ma_phong):
        errors = []
        try:
            phong = PhongTro.objects.get(MA_PHONG=ma_phong)
            hop_dong = HopDong.objects.filter(
                MA_PHONG=phong,
                TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc', 'Đã xác nhận'],
            ).first()
            if not hop_dong:
                errors.append('Phòng chưa có hợp đồng hợp lệ.')
        except PhongTro.DoesNotExist:
            errors.append('Phòng không tồn tại.')
            phong = None
        return phong, errors

    @staticmethod
    def validate_ngay_lap(ngay_lap_hdon_str):
        errors = []
        try:
            ngay_lap_hdon = datetime.strptime(ngay_lap_hdon_str, '%Y-%m-%d').date()
            if ngay_lap_hdon > timezone.now().date():
                errors.append('Ngày lập hóa đơn không được lớn hơn ngày hiện tại.')
        except ValueError:
            errors.append('Định dạng ngày lập hóa đơn không hợp lệ.')
            ngay_lap_hdon = None
        return ngay_lap_hdon, errors

    @staticmethod
    def create_hoa_don(data, phong, ngay_lap_hdon):
        return HoaDon(
            MA_PHONG=phong,
            LOAI_HOA_DON=data['LOAI_HOA_DON'],
            NGAY_LAP_HDON=ngay_lap_hdon,
            TRANG_THAI_HDON=data['TRANG_THAI_HDON'],
            TIEN_PHONG=data['TIEN_PHONG'],
            TIEN_DICH_VU=data['TIEN_DICH_VU'],
            TIEN_COC=data['TIEN_COC'],
            TIEN_KHAU_TRU=data['TIEN_KHAU_TRU'],
            TONG_TIEN=data['TONG_TIEN']
        )

    @staticmethod
    def update_hoa_don(hoa_don, data):
        hoa_don.LOAI_HOA_DON = data['LOAI_HOA_DON']
        hoa_don.NGAY_LAP_HDON = data['NGAY_LAP_HDON']
        hoa_don.TRANG_THAI_HDON = data['TRANG_THAI_HDON']
        hoa_don.TIEN_PHONG = data['TIEN_PHONG']
        hoa_don.TIEN_DICH_VU = data['TIEN_DICH_VU']
        hoa_don.TIEN_COC = data['TIEN_COC']
        hoa_don.TIEN_KHAU_TRU = data['TIEN_KHAU_TRU']
        hoa_don.TONG_TIEN = data['TONG_TIEN']
        return hoa_don

    @staticmethod
    def save_related_data(hoa_don, phong, ngay_lap_hdon, chi_so_dich_vu_list=None, khau_tru_list=None):
        errors = []
        if chi_so_dich_vu_list:
            chi_so_errors = ChiSoDichVu.save_chi_so_dich_vu(phong, chi_so_dich_vu_list, ngay_lap_hdon)
            errors.extend(chi_so_errors)
        if khau_tru_list:
            khau_tru_errors = KhauTru.save_khau_tru(hoa_don, khau_tru_list)
            errors.extend(khau_tru_errors)
        return errors

    @staticmethod
    def validate_and_create(data, chi_so_dich_vu_list=None, khau_tru_list=None):
        errors = []
        errors.extend(HoaDon.validate_required_fields(data))
        if errors:
            return None, errors
        # phong, phong_errors = HoaDon.validate_phong_and_hop_dong(data['MA_PHONG'])
        phong = PhongTro.objects.get(MA_PHONG=data['MA_PHONG'])
        # errors.extend(phong_errors)
        if not phong:
            return None, errors
        ngay_lap_hdon = datetime.strptime(data['NGAY_LAP_HDON'], '%Y-%m-%d')
        # ngay_lap_hdon, ngay_errors = HoaDon.validate_ngay_lap(data['NGAY_LAP_HDON'])
        # errors.extend(ngay_errors)
        if not ngay_lap_hdon:
            return None, errors
        hoa_don = HoaDon.create_hoa_don(data, phong, ngay_lap_hdon)
        hoa_don.save()
        related_errors = HoaDon.save_related_data(hoa_don, phong, ngay_lap_hdon, chi_so_dich_vu_list, khau_tru_list)
        errors.extend(related_errors)
        return hoa_don, errors

    @staticmethod
    def validate_and_update(hoa_don, data, chi_so_dich_vu_list=None, khau_tru_list=None):
        errors = []
        errors.extend(HoaDon.validate_required_fields(data))

        hoa_don_save = HoaDon.update_hoa_don(hoa_don, data)
        hoa_don_save.save()

        for chi_so_dich_vu_data in chi_so_dich_vu_list:
            try:

                ma_chi_so = chi_so_dich_vu_data.get('MA_CHI_SO', '')
                chi_so_dv = ChiSoDichVu.objects.filter(MA_CHI_SO=ma_chi_so).first()
                
                chi_so_dich_vu = ChiSoDichVu.update_chi_so_dich_vu(chi_so_dv, chi_so_dich_vu_data, hoa_don_save.NGAY_LAP_HDON)
                chi_so_dich_vu.save()
            except Exception as e:
                errors.append(f"Lỗi khi lưu chỉ số dịch vụ MACHISO={chi_so_dich_vu_data.get('MA_CHI_SO', '')}: {str(e)}")

        HoaDon.update_khau_tru(hoa_don, khau_tru_list)
        return hoa_don_save, errors
    @staticmethod
    def update_khau_tru(hoa_don, khau_tru_list):
        errors = []
        existing_khau_tru = KhauTru.objects.filter(MA_HOA_DON=hoa_don).values_list('MA_KHAU_TRU', flat=True)
        for khau_tru_data in khau_tru_list:
            try:
                ma_khau_tru = khau_tru_data.get('MA_KHAU_TRU', '')
                ngay_khau_tru = khau_tru_data.get('NGAYKHAUTRU', '')
                # Cập nhật hoặc thêm mới
                if ma_khau_tru != '':
                    # Cập nhật bản ghi hiện có
                    khau_tru = KhauTru.update_khau_tru(ma_khau_tru, khau_tru_data, ngay_khau_tru)
                else:
                    # Thêm mới bản ghi
                    khau_tru = KhauTru.create_khau_tru(hoa_don, khau_tru_data, ngay_khau_tru)
                    khau_tru.save()  # MA_KHAU_TRU sẽ tự động tạo nếu là AutoField hoặc UUID
                    
            except Exception as e:
                errors.append(f"Lỗi khi lưu khấu trừ MA_KHAU_TRU={ma_khau_tru}: {str(e)}")
    @staticmethod
    def delete_hoa_don(hoa_don):
        try:
            ChiSoDichVu.objects.filter(MA_HOA_DON=hoa_don).delete()
            KhauTru.objects.filter(MA_HOA_DON=hoa_don).delete()
            hoa_don.delete()
            return True, []
        except Exception as e:
            return False, [f'Lỗi khi xóa hóa đơn: {str(e)}']


# Model for khautru
class KhauTru(models.Model):
    MA_KHAU_TRU = models.AutoField(primary_key=True)
    MA_HOA_DON = models.ForeignKey(
        'HoaDon',
        on_delete=models.CASCADE,
        db_column='MA_HOA_DON',
        related_name='khautru'
    )
    NGAYKHAUTRU = models.DateField(null=True, blank=True)
    LOAI_KHAU_TRU = models.CharField(max_length=50, null=True, blank=True)
    SO_TIEN_KT = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    LY_DO_KHAU_TRU = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Khấu trừ {self.MA_KHAU_TRU} - Hóa đơn {self.MA_HOA_DON_id}"

    class Meta:
        db_table = 'khautru'
    @staticmethod
    def validate_khau_tru_data(khau_tru, index):
        errors = []
        loai_kt = khau_tru.get('LOAI_KHAU_TRU')
        ly_do_kt = khau_tru.get('LY_DO_KHAU_TRU')

        if not loai_kt:
            errors.append(f'Khấu trừ thứ {index+1}: Thiếu loại khấu trừ.')
        if not ly_do_kt:
            errors.append(f'Khấu trừ thứ {index+1}: Thiếu lý do khấu trừ.')

        try:
            so_tien_kt = float(khau_tru.get('SO_TIEN_KT', 0))
            if so_tien_kt < 0:
                errors.append(f'Khấu trừ thứ {index+1}: Số tiền khấu trừ không được âm.')
        except (ValueError, TypeError):
            errors.append(f'Khấu trừ thứ {index+1}: Số tiền khấu trừ không hợp lệ.')
            so_tien_kt = None

        if errors:
            return None, errors

        return {
            'LOAI_KHAU_TRU': loai_kt,
            'SO_TIEN_KT': so_tien_kt,
            'LY_DO_KHAU_TRU': ly_do_kt
        }, errors

    @staticmethod
    def validate_ngay_khau_tru(ngay_khau_tru, index):
       
        errors = []
        ngay_kt = None

        if not ngay_khau_tru:
            errors.append(f'Ngày khấu trừ thứ {index + 1} không được để trống.')
            return ngay_kt, errors

        try:
            if isinstance(ngay_khau_tru, str):
                ngay_kt = datetime.strptime(ngay_khau_tru, '%Y-%m-%d')
            elif isinstance(ngay_khau_tru, datetime.date):
                ngay_kt = datetime.combine(ngay_khau_tru, datetime.min.time())
            else:
                errors.append(f'Ngày khấu trừ thứ {index + 1} có kiểu dữ liệu không hợp lệ.')
                return ngay_kt, errors

            # Nếu model KhauTru chỉ cần datetime.date, không cần thiết lập giờ/phút/giây
            # ngay_kt = ngay_kt.replace(hour=0, minute=0, second=0, microsecond=0)
            # Chuyển về datetime.date nếu model yêu cầu
            ngay_kt = ngay_kt.date()

        except ValueError:
            errors.append(f'Ngày khấu trừ thứ {index + 1} không hợp lệ (định dạng YYYY-MM-DD).')

        return ngay_kt, errors
    @staticmethod
    def create_khau_tru(hoa_don, khau_tru_data, ngay_kt):
        return KhauTru(
            MA_HOA_DON=hoa_don,
            LOAI_KHAU_TRU=khau_tru_data['LOAI_KHAU_TRU'],
            SO_TIEN_KT=khau_tru_data['SO_TIEN_KT'],
            LY_DO_KHAU_TRU=khau_tru_data['LY_DO_KHAU_TRU'],
            NGAYKHAUTRU=ngay_kt
        )
    @staticmethod
    def update_khau_tru(khau_tru_id, khau_tru_data, ngay_kt):
        try:
            khau_tru = KhauTru.objects.get(pk=khau_tru_id)
            khau_tru.LOAI_KHAU_TRU = khau_tru_data['LOAI_KHAU_TRU']
            khau_tru.SO_TIEN_KT = khau_tru_data['SO_TIEN_KT']
            khau_tru.LY_DO_KHAU_TRU = khau_tru_data['LY_DO_KHAU_TRU']
            khau_tru.NGAYKHAUTRU = ngay_kt
            khau_tru.save()
            return khau_tru
        except KhauTru.DoesNotExist:
            return None
    @staticmethod
    def save_khau_tru(hoa_don, khau_tru_list):
        errors = []
        for kt in khau_tru_list:
            # Xác thực dữ liệu khấu trừ
            khau_tru_data, data_errors = KhauTru.validate_khau_tru_data(kt, index=0)
            errors.extend(data_errors)
            if not khau_tru_data:
                continue

            # Xác thực ngày khấu trừ
            ngay_kt, ngay_errors = KhauTru.validate_ngay_khau_tru(kt.get('NGAYKHAUTRU'), index=0)
            errors.extend(ngay_errors)
            if not ngay_kt:
                continue

            # Tạo và lưu khấu trừ
            khau_tru = KhauTru.create_khau_tru(hoa_don, khau_tru_data, ngay_kt)
            khau_tru.save()
        
        return errors