from django.db import models

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