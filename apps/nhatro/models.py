from django.db import models

# Create your models here.
# Model for nhatro
class NhaTro(models.Model):
    MA_NHA_TRO = models.AutoField(primary_key=True)
    MA_QUAN_LY = models.ForeignKey(
        'thanhvien.NguoiQuanLy',
        on_delete=models.CASCADE,
        db_column='MA_QUAN_LY',
        related_name='ds_nhatro'
    )
    TEN_NHA_TRO = models.CharField(max_length=200, null=True, blank=True)
    VUNG_MIEN = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.TEN_NHA_TRO or f"Nhà trọ {self.MA_NHA_TRO}"

    class Meta:
        db_table = 'nhatro'

# Model for khuvuc
class KhuVuc(models.Model):
    MA_KHU_VUC = models.AutoField(primary_key=True)
    MA_NHA_TRO = models.ForeignKey(
        'NhaTro',
        on_delete=models.CASCADE,
        db_column='MA_NHA_TRO',
        related_name='ds_khuvuc'
    )
    TEN_KHU_VUC = models.CharField(max_length=200, null=True, blank=True)
    TRANG_THAI_KV = models.CharField(max_length=50, null=True, blank=True)
    DV_HANH_CHINH_CAP1 = models.CharField(max_length=50, null=True, blank=True)
    DV_HANH_CHINH_CAP2 = models.CharField(max_length=50, null=True, blank=True)
    DV_HANH_CHINH_CAP3 = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.TEN_KHU_VUC or f"Khu vực {self.MA_KHU_VUC}"

    class Meta:
        db_table = 'khuvuc'