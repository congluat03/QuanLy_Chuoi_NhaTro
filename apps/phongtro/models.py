from django.db import models
from django.core.exceptions import ValidationError
from apps.nhatro.models import KhuVuc
from datetime import date

# Create your models here.
# Hằng số trạng thái
TRANG_THAI_COC_PHONG = {
    'CHO_XAC_NHAN': 'Chờ xác nhận',
    'DA_COC': 'Đã cọc',
    'DA_SU_DUNG': 'Đã sử dụng',
    'DA_HOAN_TRA': 'Đã hoàn trả',
    'DA_THU_HOI': 'Đã thu hồi'
}
# Model for loaiphong
class LoaiPhong(models.Model):
    MA_LOAI_PHONG = models.AutoField(primary_key=True)
    TEN_LOAI_PHONG = models.CharField(max_length=200, null=True, blank=True)
    MO_TA_LP = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.TEN_LOAI_PHONG or f"Loại phòng {self.MA_LOAI_PHONG}"

    class Meta:
        db_table = 'loaiphong'

# Model for phongtro
class PhongTro(models.Model):
    MA_PHONG = models.AutoField(primary_key=True)
    MA_LOAI_PHONG = models.ForeignKey(
        'LoaiPhong',
        on_delete=models.CASCADE,
        db_column='MA_LOAI_PHONG',
        related_name='ds_phongtro'
    )
    MA_KHU_VUC = models.ForeignKey(
        'nhatro.KhuVuc',
        on_delete=models.CASCADE,
        db_column='MA_KHU_VUC',
        related_name='ds_phongtro'
    )
    TEN_PHONG = models.CharField(max_length=200, null=True, blank=True)
    TRANG_THAI_P = models.CharField(max_length=50, null=True, blank=True)
    GIA_PHONG = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    DIEN_TICH = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    SO_NGUOI_TOI_DA = models.IntegerField(null=True, blank=True)
    MO_TA_P = models.TextField(null=True, blank=True)
    SO_TIEN_CAN_COC = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.TEN_PHONG or f"Phòng {self.MA_PHONG}"

    class Meta:
        db_table = 'phongtro'
    # ===== HÀM LẤY PHÒNG THEO MÃ NHÀ TRỌ =====
    @classmethod
    def lay_phong_theo_ma_nha_tro(cls, ma_nha_tro):
        return cls.objects.filter(MA_KHU_VUC__MA_NHA_TRO=ma_nha_tro)

    # ===== HÀM LẤY PHÒNG THEO MÃ KHU VỰC =====
    @classmethod
    def lay_phong_theo_ma_khu_vuc(cls, ma_khu_vuc):
        return cls.objects.filter(MA_KHU_VUC=ma_khu_vuc)
    @staticmethod
    def get_tien_coc(ma_phong):
        try:
            phong = PhongTro.objects.get(MA_PHONG=ma_phong)
            return float(phong.SO_TIEN_CAN_COC or 0.00), []
        except PhongTro.DoesNotExist:
            return 0.00, ['Phòng không tồn tại']
        except Exception as e:
            return 0.00, [f'Lỗi khi lấy tiền cọc: {str(e)}']
    def get_hop_dong_con_hieu_luc(self):
        today = date.today()
        return self.hopdong.filter(
            NGAY_NHAN_PHONG__lte=today,
            NGAY_TRA_PHONG__gte=today
        ).order_by('-NGAY_LAP_HD').first()

# Model for cocphong
class CocPhong(models.Model):
    MA_COC_PHONG = models.AutoField(primary_key=True)
    MA_PHONG = models.ForeignKey(
        'PhongTro',
        on_delete=models.CASCADE,
        db_column='MA_PHONG',
        related_name='cocphong'
    )
    MA_KHACH_THUE = models.ForeignKey(
        'khachthue.KhachThue',
        on_delete=models.CASCADE,
        db_column='MA_KHACH_THUE',
        related_name='cocphong'
    )
    NGAY_COC_PHONG = models.DateField(null=True, blank=True)
    NGAY_DU_KIEN_VAO = models.DateField(null=True, blank=True)
    TIEN_COC_PHONG = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    TRANG_THAI_CP = models.CharField(max_length=50, null=True, blank=True)
    GHI_CHU_CP = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Cọc phòng {self.MA_COC_PHONG} - Phòng {self.MA_PHONG_id}"

    class Meta:
        db_table = 'cocphong'
    def clean(self):
        """Validate dữ liệu CocPhong."""
        if self.TIEN_COC_PHONG <= 0:
            raise ValidationError('Tiền cọc phải lớn hơn 0.')
        if self.NGAY_COC_PHONG > self.NGAY_DU_KIEN_VAO:
            raise ValidationError('Ngày cọc không được sau ngày dự kiến vào.')
    @classmethod
    def check_duplicate(cls, phong):
        """Kiểm tra xem phòng đã có cọc phòng ở trạng thái 'Đã cọc' hoặc 'Chờ xác nhận' chưa."""
        if cls.objects.filter(
            MA_PHONG=phong,
            TRANG_THAI_CP__in=[TRANG_THAI_COC_PHONG['DA_COC'], TRANG_THAI_COC_PHONG['CHO_XAC_NHAN']]
        ).exists():
            raise ValueError(f'Phòng {phong} đã có cọc phòng ở trạng thái Đã cọc hoặc Chờ xác nhận.')
    @classmethod
    def cap_nhat_trang_thai_coc(cls, phong, trang_thai):
        coc_phong = cls.objects.filter(
            MA_PHONG=phong,
            TRANG_THAI_CP__in=[TRANG_THAI_COC_PHONG['DA_COC'], TRANG_THAI_COC_PHONG['CHO_XAC_NHAN']]
        ).first()
        if coc_phong:
            coc_phong.TRANG_THAI_CP = trang_thai
            coc_phong.save()
    def cap_nhat_coc_phong(self, tien_coc_phong=None, ngay_coc_phong=None, ngay_du_kien_vao=None, ghi_chu_cp=None):
        self.TIEN_COC_PHONG = tien_coc_phong if tien_coc_phong is not None else self.TIEN_COC_PHONG
        self.NGAY_COC_PHONG = ngay_coc_phong if ngay_coc_phong is not None else self.NGAY_COC_PHONG
        self.NGAY_DU_KIEN_VAO = ngay_du_kien_vao if ngay_du_kien_vao is not None else self.NGAY_DU_KIEN_VAO
        self.GHI_CHU_CP = ghi_chu_cp if ghi_chu_cp is not None else self.GHI_CHU_CP
        self.full_clean()  # Validate dữ liệu
        self.save()

    @classmethod
    def tao_coc_phong(cls, phong, khach_thue, tien_coc_phong, ngay_coc_phong):
        cls.check_duplicate(phong)
        coc_phong = cls(
            MA_PHONG=phong,
            MA_KHACH_THUE=khach_thue,
            NGAY_COC_PHONG=ngay_coc_phong,
            NGAY_DU_KIEN_VAO=ngay_coc_phong,
            TIEN_COC_PHONG=tien_coc_phong,
            TRANG_THAI_CP='Đã lập hợp đồng'
        )
        coc_phong.full_clean()
        coc_phong.save()
        return coc_phong

class TAISAN(models.Model):
    MA_TAI_SAN = models.IntegerField(primary_key=True)
    TEN_TAI_SAN = models.CharField(max_length=100, null=True, blank=True)
    MO_TA = models.TextField(null=True, blank=True)
    DON_VI_TS = models.CharField(max_length=20, default='cái', null=True, blank=True)
    GIA_TS = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'taisan'

class TAISANPHONG(models.Model):
    MA_TAI_SAN_PHONG = models.IntegerField(primary_key=True)
    MA_PHONG = models.ForeignKey(
        'PhongTro',
        on_delete=models.CASCADE,
        db_column='MA_PHONG',
        related_name='taisanphong'
    )
    MA_TAI_SAN = models.ForeignKey(TAISAN, on_delete=models.SET_NULL, null=True, db_column='MA_TAI_SAN')
    SO_LUONG = models.IntegerField(null=True, blank=True)
    TINH_TRANG = models.CharField(max_length=50, null=True, blank=True)
    NGAY_KIEM_KE = models.DateField(null=True, blank=True)
    GHI_CHU = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'taisanphong'

class TAISANBANGIAO(models.Model):
    MA_BAN_GIAO = models.IntegerField(primary_key=True)
    MA_HOP_DONG = models.ForeignKey(
        'hopdong.HopDong',
        on_delete=models.CASCADE,
        db_column='MA_HOP_DONG',
        related_name='taisanbangiao'
    )
    MA_TAI_SAN = models.ForeignKey(TAISAN, on_delete=models.SET_NULL, null=True, db_column='MA_TAI_SAN')
    SO_LUONG = models.IntegerField(null=True, blank=True)
    TINH_TRANG_GIAO = models.CharField(max_length=100, null=True, blank=True)
    GHI_CHU = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'taisanbangiao'
    @classmethod
    def tao_danh_sach_tai_san_ban_giao(cls, hop_dong, ds_tai_san: list):
        danh_sach = []
        for item in ds_tai_san:
            if not item.get('MA_TAI_SAN'):
                continue
            ts = cls(
                MA_HOP_DONG=hop_dong,
                MA_TAI_SAN_id=item['MA_TAI_SAN'],
                SO_LUONG=item.get('SO_LUONG') or 1,
                TINH_TRANG_GIAO='Tốt',  # hoặc để None
                GHI_CHU=''
            )
            danh_sach.append(ts)
        cls.objects.bulk_create(danh_sach)

