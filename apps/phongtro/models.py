from django.db import models

# Create your models here.

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