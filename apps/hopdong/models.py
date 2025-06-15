from django.db import models

# Create your models here.
# Model for hopdong
class HopDong(models.Model):
    MA_HOP_DONG = models.AutoField(primary_key=True)
    MA_PHONG = models.ForeignKey(
        'phongtro.PhongTro',
        on_delete=models.CASCADE,
        db_column='MA_PHONG',
        related_name='hopdong'
    )
    NGAY_LAP_HD = models.DateField(null=True, blank=True)
    THOI_HANG_HD = models.CharField(max_length=50, null=True, blank=True)
    NGAY_NHAN_PHONG = models.DateField(null=True, blank=True)
    NGAY_TRA_PHONG = models.DateField(null=True, blank=True)
    SO_THANH_VIEN = models.IntegerField(null=True, blank=True)
    GIA_THUE = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    NGAY_THU_TIEN = models.CharField(max_length=10, null=True, blank=True)
    PHUONG_THUC_THANH_TOAN = models.CharField(max_length=50, null=True, blank=True)
    TRANG_THAI_HD = models.CharField(max_length=50, null=True, blank=True)
    GHI_CHU_HD = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Hợp đồng {self.MA_HOP_DONG} - Phòng {self.MA_PHONG_id}"

    class Meta:
        db_table = 'hopdong'

# Model for lichsuhopdong
class LichSuHopDong(models.Model):
    MA_LICH_SU_HD = models.AutoField(primary_key=True)
    MA_HOP_DONG = models.ForeignKey(
        'HopDong',
        on_delete=models.CASCADE,
        db_column='MA_HOP_DONG',
        related_name='lichsuhopdong'
    )
    MA_KHACH_THUE = models.ForeignKey(
        'khachthue.KhachThue',
        on_delete=models.CASCADE,
        db_column='MA_KHACH_THUE',
        related_name='lichsuhopdong'
    )
    MOI_QUAN_HE = models.CharField(max_length=50, null=True, blank=True)
    NGAY_THAM_GIA = models.DateField(null=True, blank=True)
    NGAY_ROI_DI = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Lịch sử hợp đồng {self.MA_LICH_SU_HD}"

    class Meta:
        db_table = 'lichsuhopdong'

# Model for chukythanhtoan
class ChuKyThanhToan(models.Model):
    MA_CHU_KY = models.AutoField(primary_key=True)
    MA_HOP_DONG = models.ForeignKey(
        'HopDong',
        on_delete=models.CASCADE,
        db_column='MA_HOP_DONG',
        related_name='chukythanhtoan'
    )
    NGAY_BAT_DAU_CK = models.DateField(null=True, blank=True)
    NGAY_KET_THUC_CK = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Chu kỳ thanh toán {self.MA_CHU_KY}"

    class Meta:
        db_table = 'chukythanhtoan'