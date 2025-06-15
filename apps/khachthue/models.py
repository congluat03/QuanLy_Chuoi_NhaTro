from django.db import models

# Create your models here.
# Model for khachthue
class KhachThue(models.Model):
    MA_KHACH_THUE = models.AutoField(primary_key=True)
    MA_TAI_KHOAN = models.ForeignKey(
        'thanhvien.TaiKhoan',
        on_delete=models.CASCADE,
        db_column='MA_TAI_KHOAN',
        related_name='khachthue'
    )
    HO_TEN_KT = models.CharField(max_length=200, null=True, blank=True)
    GIOI_TINH_KT = models.CharField(max_length=20, null=True, blank=True)
    NGAY_SINH_KT = models.DateField(null=True, blank=True)
    NOI_SINH_KT = models.CharField(max_length=50, null=True, blank=True)
    SDT_KT = models.CharField(max_length=15, null=True, blank=True)
    EMAIL_KT = models.EmailField(max_length=100, null=True, blank=True)
    NGHE_NGHIEP = models.CharField(max_length=200, null=True, blank=True)
    ANH_KT = models.TextField(null=True, blank=True)
    TRANG_THAI_KT = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.HO_TEN_KT or f"Khách thuê {self.MA_KHACH_THUE}"

    class Meta:
        db_table = 'khachthue'

# Model for cccd_cmnd
class CccdCmnd(models.Model):
    SO_CMND_CCCD = models.CharField(max_length=20, primary_key=True)
    MA_KHACH_THUE = models.ForeignKey(
        'KhachThue',
        on_delete=models.CASCADE,
        db_column='MA_KHACH_THUE',
        related_name='cccd_cmnd'
    )
    NGAY_CAP = models.DateField(null=True, blank=True)
    ANH_MAT_TRUOC = models.TextField(null=True, blank=True)
    ANH_MAT_SAU = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"CCCD/CMND {self.SO_CMND_CCCD}"

    class Meta:
        db_table = 'cccd_cmnd'