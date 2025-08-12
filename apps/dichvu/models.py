from django.db import models
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Create your models here.
# Model for dichvu
class DichVu(models.Model):
    MA_DICH_VU = models.AutoField(primary_key=True)
    TEN_DICH_VU = models.CharField(max_length=200, null=True, blank=True)
    DON_VI_TINH = models.CharField(max_length=50, null=True, blank=True)
    LOAI_DICH_VU = models.CharField(max_length=50, null=True, blank=True)
    GIA_DICH_VU = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.TEN_DICH_VU or f"Dịch vụ {self.MA_DICH_VU}"
    @property
    def is_applied(self):
        return self.lichsu_dichvu.filter(NGAY_HUY_DV__isnull=True).exists()
    class Meta:
        db_table = 'dichvu'

# Model for lichsuapdungdichvu
class LichSuApDungDichVu(models.Model):
    MA_AP_DUNG_DV = models.AutoField(primary_key=True)
    MA_KHU_VUC = models.ForeignKey(
        'nhatro.KhuVuc',
        on_delete=models.CASCADE,
        db_column='MA_KHU_VUC',
        related_name='lichsu_dichvu'
    )
    MA_DICH_VU = models.ForeignKey(
        'DichVu',
        on_delete=models.CASCADE,
        db_column='MA_DICH_VU',
        related_name='lichsu_dichvu'
    )
    NGAY_AP_DUNG_DV = models.DateField(null=True, blank=True)
    NGAY_HUY_DV = models.DateField(null=True, blank=True)
    GIA_DICH_VU_AD = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    LOAI_DICH_VU_AD = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Áp dụng dịch vụ {self.MA_AP_DUNG_DV}"

    class Meta:
        db_table = 'lichsuapdungdichvu'
    @staticmethod
    def get_dich_vu_ap_dung(khu_vuc):
        try:
            return LichSuApDungDichVu.objects.filter(
                MA_KHU_VUC=khu_vuc,
                NGAY_HUY_DV__isnull=True
            ).select_related('MA_DICH_VU'), []
        except Exception as e:
            return None, [f'Lỗi khi lấy dịch vụ áp dụng: {str(e)}']
    
# Model for chisodichvu
class ChiSoDichVu(models.Model):
    MA_CHI_SO = models.AutoField(primary_key=True)
    MA_DICH_VU = models.ForeignKey(
        'DichVu',
        on_delete=models.CASCADE,
        db_column='MA_DICH_VU',
        related_name='chisodichvu'
    )
    MA_PHONG = models.ForeignKey(
        'phongtro.PhongTro',
        on_delete=models.CASCADE,
        db_column='MA_PHONG',
        related_name='chisodichvu'
    )
    MA_HOP_DONG = models.ForeignKey(
        'hopdong.HopDong',
        on_delete=models.CASCADE,
        db_column='MA_HOP_DONG',
        related_name='chisodichvu'
    )
    CHI_SO_CU = models.IntegerField(null=True, blank=True)
    CHI_SO_MOI = models.IntegerField(null=True, blank=True)
    NGAY_GHI_CS = models.DateField(null=True, blank=True)
    SO_LUONG = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return f"Chỉ số dịch vụ {self.MA_CHI_SO} - Phòng {self.MA_PHONG_id}"

    class Meta:
        db_table = 'chisodichvu'
    @staticmethod
    def get_applied_services(khu_vuc):
        return LichSuApDungDichVu.objects.filter(
            MA_KHU_VUC=khu_vuc,
        ).select_related('MA_DICH_VU')

    @staticmethod
    def validate_chi_so_data(chi_so, index):
        errors = []
        try:
            chi_so_cu = float(chi_so.get('CHI_SO_CU', 0)) if chi_so.get('CHI_SO_CU') else 0.0
            chi_so_moi = float(chi_so.get('CHI_SO_MOI', 0)) if chi_so.get('CHI_SO_MOI') else None
            so_dich_vu = float(chi_so.get('SO_DICH_VU', 0)) if chi_so.get('SO_DICH_VU') else 0.0
            thanh_tien = float(chi_so.get('THANH_TIEN', 0))

            if chi_so_moi is not None and chi_so_cu is not None and chi_so_moi < chi_so_cu:
                errors.append(f'Dịch vụ thứ {index+1}: Chỉ số mới phải lớn hơn hoặc bằng chỉ số cũ.')
            if thanh_tien < 0:
                errors.append(f'Dịch vụ thứ {index+1}: Thành tiền không được âm.')

            return {
                'CHI_SO_CU': chi_so_cu,
                'CHI_SO_MOI': chi_so_moi,
                'SO_DICH_VU': so_dich_vu,
                'THANH_TIEN': thanh_tien
            }, errors
        except (ValueError, TypeError) as e:
            errors.append(f'Lỗi dữ liệu dịch vụ thứ {index+1}: {str(e)}')
            return None, errors

    @staticmethod
    def create_chi_so_dich_vu(phong, dich_vu, chi_so_data, ngay_ghi_cs, hop_dong):
        return ChiSoDichVu(
            MA_HOP_DONG=hop_dong,
            MA_DICH_VU=dich_vu,
            MA_PHONG=phong,
            CHI_SO_CU=int(chi_so_data['CHI_SO_CU']),
            CHI_SO_MOI=int(chi_so_data['CHI_SO_MOI']),
            NGAY_GHI_CS=ngay_ghi_cs
        )
    @classmethod
    def tao_danh_sach_chi_so(cls, hop_dong, ds_dich_vu: list):
        danh_sach = []
        for item in ds_dich_vu:
            if not item.get('MA_DICH_VU'):
                continue
            chisodv = cls(
                MA_DICH_VU_id=item['MA_DICH_VU'],
                MA_HOP_DONG=hop_dong,
                CHI_SO_CU=None,  # Có thể tính nếu cần
                CHI_SO_MOI=item.get('CHI_SO_MOI') or None,
                SO_LUONG = item.get('SO_LUONG') or 0,
                NGAY_GHI_CS=hop_dong.NGAY_LAP_HD or datetime.now().date()
            )
            danh_sach.append(chisodv)
        cls.objects.bulk_create(danh_sach)
    @staticmethod
    def update_chi_so_dich_vu(chi_so_dv, chi_so_data, ngay_ghi_cs):
        chi_so_dv.CHI_SO_MOI = int(float(chi_so_data['CHI_SO_MOI']))
        chi_so_dv.NGAY_GHI_CS = ngay_ghi_cs
        return chi_so_dv
    @staticmethod
    def save_chi_so_dich_vu(phong, chi_so_dich_vu_list, ngay_ghi_cs, hop_dong):
        errors = []
        for chi_so in chi_so_dich_vu_list:
            ma_dich_vu = int(chi_so.get('MA_DICH_VU'))
            ma_chi_so = chi_so.get('MA_CHI_SO')
            dich_vu = DichVu.objects.filter(MA_DICH_VU=ma_dich_vu).first()

            # Kiểm tra MA_DICH_VU
            if not ma_dich_vu:
                errors.append(f'Dịch vụ với MA_DICH_VU={ma_dich_vu} không hợp lệ.')
                continue

            # Xác thực dữ liệu
            chi_so_data, chi_so_errors = ChiSoDichVu.validate_chi_so_data(chi_so, index=0)
            errors.extend(chi_so_errors)
            if not chi_so_data:
                continue
            

            # Kiểm tra bản ghi hiện có
            if ma_chi_so:
                chi_so_hien_co = ChiSoDichVu.objects.filter(MA_CHI_SO=ma_chi_so).first()
                if chi_so_hien_co:
                    # Cập nhật bản ghi hiện có
                    chi_so_dv = ChiSoDichVu.update_chi_so_dich_vu(chi_so_hien_co, chi_so_data, ngay_ghi_cs)
                    chi_so_dv.save()
                else:
                    errors.append(f'Bản ghi với MA_CHI_SO={ma_chi_so} không tồn tại.')
                    continue
            else:
                # Tạo bản ghi mới
                chi_so_dv = ChiSoDichVu.create_chi_so_dich_vu(phong, dich_vu, chi_so_data, ngay_ghi_cs, hop_dong)
                chi_so_dv.save()

        return errors

    @staticmethod
    def get_chi_so_moi_nhat(ma_dich_vu, ma_phong, current_month, next_month):
        try:
            return ChiSoDichVu.objects.filter(
                MA_DICH_VU=ma_dich_vu,
                MA_PHONG=ma_phong,
                NGAY_GHI_CS__gte=current_month,
                NGAY_GHI_CS__lt=next_month
            ).order_by('-NGAY_GHI_CS').first()
        except Exception:
            return None

    @staticmethod
    def get_chi_so_truoc(ma_dich_vu, ma_phong, current_month):
        try:
            return ChiSoDichVu.objects.filter(
                MA_DICH_VU=ma_dich_vu,
                MA_PHONG=ma_phong,
                NGAY_GHI_CS__lt=current_month
            ).order_by('-NGAY_GHI_CS').first()
        except Exception:
            return None

    @staticmethod
    def tinh_chi_so_dich_vu(dich_vu_ap_dung, ma_phong, current_month, next_month):
        errors = []
        try:
            chi_so = ChiSoDichVu.get_chi_so_moi_nhat(dich_vu_ap_dung.MA_DICH_VU, ma_phong, current_month, next_month)
            so_dich_vu = 0
            thanh_tien = 0
            chi_so_cu = 0
            chi_so_moi = None

            if dich_vu_ap_dung.MA_DICH_VU.LOAI_DICH_VU != 'Cố định':
                if chi_so:
                    chi_so_cu = chi_so.CHI_SO_CU or 0
                    chi_so_moi = chi_so.CHI_SO_MOI
                    so_dich_vu = (chi_so_moi - chi_so_cu) if chi_so_moi is not None else 0
                    thanh_tien = so_dich_vu * dich_vu_ap_dung.GIA_DICH_VU_AD
                else:
                    chi_so_truoc = ChiSoDichVu.get_chi_so_truoc(dich_vu_ap_dung.MA_DICH_VU, ma_phong, current_month)
                    chi_so_cu = chi_so_truoc.CHI_SO_MOI if chi_so_truoc else 0
            else:
                so_dich_vu = 1
                thanh_tien = dich_vu_ap_dung.GIA_DICH_VU_AD

            return {
                'MA_CHI_SO': chi_so.MA_CHI_SO if chi_so else None,
                'MA_DICH_VU': dich_vu_ap_dung.MA_DICH_VU.MA_DICH_VU,
                'TEN_DICH_VU': dich_vu_ap_dung.MA_DICH_VU.TEN_DICH_VU,
                'LOAI_DICH_VU': dich_vu_ap_dung.MA_DICH_VU.LOAI_DICH_VU,
                'GIA_DICH_VU': float(dich_vu_ap_dung.GIA_DICH_VU_AD),
                'CHI_SO_CU': float(chi_so_cu),
                'CHI_SO_MOI': float(chi_so_moi) if chi_so_moi is not None else None,
                'SO_DICH_VU': float(so_dich_vu),
                'THANH_TIEN': float(thanh_tien)
            }, errors
        except Exception as e:
            errors.append(f'Lỗi khi tính chi tiết dịch vụ {dich_vu_ap_dung.MA_DICH_VU.TEN_DICH_VU}: {str(e)}')
            return None, errors