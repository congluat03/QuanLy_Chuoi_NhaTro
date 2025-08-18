# EMERGENCY: Backup của KhuVuc model cũ để tránh lỗi
# Nếu cần rollback, thay thế model hiện tại bằng version này

from django.db import models

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