from django.db import models

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
    CHI_SO_CU = models.IntegerField(null=True, blank=True)
    CHI_SO_MOI = models.IntegerField(null=True, blank=True)
    NGAY_GHI_CS = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Chỉ số dịch vụ {self.MA_CHI_SO} - Phòng {self.MA_PHONG_id}"

    class Meta:
        db_table = 'chisodichvu'