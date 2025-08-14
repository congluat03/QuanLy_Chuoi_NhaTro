from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import re
import uuid

# Model for taikhoan
class TaiKhoan(models.Model):
    MA_TAI_KHOAN = models.AutoField(primary_key=True)
    TAI_KHOAN = models.CharField(max_length=50, null=True, blank=True)
    MAT_KHAU = models.TextField(null=True, blank=True)
    TRANG_THAI_TK = models.CharField(max_length=50, null=True, blank=True)
    QUYEN_HAN = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'taikhoan'

    def set_mat_khau(self, password):
        self.MAT_KHAU = make_password(password)

    def check_mat_khau(self, password):
        return check_password(password, self.MAT_KHAU)
    @staticmethod
    def validate_tai_khoan(tai_khoan):
        if not tai_khoan or not re.match(r'^[a-zA-Z0-9]{6,20}$', tai_khoan):
            raise ValueError('Tài khoản phải từ 6-20 ký tự, không chứa ký tự đặc biệt.')
        return tai_khoan

    @staticmethod
    def validate_mat_khau(mat_khau):
        if mat_khau and not re.match(r'^(?=.*[a-zA-Z])(?=.*[0-9]).{8,}$', mat_khau):
            raise ValueError('Mật khẩu phải tối thiểu 8 ký tự, bao gồm chữ và số.')
        return mat_khau

    @classmethod
    def create_tai_khoan(cls, tai_khoan, mat_khau, quyen_han='Khách thuê'):
        cls.validate_tai_khoan(tai_khoan)
        cls.validate_mat_khau(mat_khau)
        if cls.objects.filter(TAI_KHOAN=tai_khoan).exists():
            raise ValueError('Tài khoản đã tồn tại.')
        
        # Validate quyền hạn
        valid_roles = ['Khách thuê', 'Chủ trọ', 'admin']
        if quyen_han not in valid_roles:
            quyen_han = 'Khách thuê'
            
        return cls.objects.create(
            TAI_KHOAN=tai_khoan,
            MAT_KHAU=make_password(mat_khau),
            TRANG_THAI_TK='Hoạt động',
            QUYEN_HAN=quyen_han
        )
    @classmethod
    def create_tai_khoan_mac_dinh(cls, tai_khoan=None, mat_khau=None, quyen_han='Khách thuê'):
        if tai_khoan and mat_khau:
            return cls.create_tai_khoan(tai_khoan=tai_khoan, mat_khau=mat_khau, quyen_han=quyen_han)
        else:
            unique_suffix = str(uuid.uuid4())[:8]
            default_tai_khoan = f"khachthue{unique_suffix}"
            default_mat_khau = "KhachThue@123"
            return cls.create_tai_khoan(tai_khoan=default_tai_khoan, mat_khau=default_mat_khau, quyen_han=quyen_han)
    def update_tai_khoan(self, tai_khoan=None, mat_khau=None):
        if tai_khoan and tai_khoan != self.TAI_KHOAN:
            self.validate_tai_khoan(tai_khoan)
            if TaiKhoan.objects.filter(TAI_KHOAN=tai_khoan).exclude(pk=self.pk).exists():
                raise ValueError('Tài khoản đã tồn tại.')
            self.TAI_KHOAN = tai_khoan
        if mat_khau:
            self.validate_mat_khau(mat_khau)
            self.MAT_KHAU = make_password(mat_khau)
        self.save()

# Model for nguoiquanly
class NguoiQuanLy(models.Model):
    MA_QUAN_LY = models.AutoField(primary_key=True)
    MA_TAI_KHOAN = models.ForeignKey(
        'TaiKhoan',
        on_delete=models.CASCADE,
        db_column='MA_TAI_KHOAN',
        related_name='nguoiquanly'
    )
    TEN_QUAN_LY = models.CharField(max_length=200, null=True, blank=True)
    NGAY_SINH_QL = models.DateField(null=True, blank=True)
    GIOI_TINH_QL = models.CharField(max_length=50, null=True, blank=True)
    SDT_QUAN_LY = models.CharField(max_length=15, null=True, blank=True)
    EMAIL_QL = models.EmailField(max_length=200, null=True, blank=True)
    DIA_CHI_QL = models.CharField(max_length=500, null=True, blank=True)
    ANH_QL = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.TEN_QUAN_LY or f"Quản lý {self.MA_QUAN_LY}"
    
    @classmethod
    def create_chu_tro(cls, tai_khoan_obj, ho_ten, sdt=None, email=None):
        """Tạo thông tin chủ trọ mới"""
        return cls.objects.create(
            MA_TAI_KHOAN=tai_khoan_obj,
            TEN_QUAN_LY=ho_ten,
            SDT_QUAN_LY=sdt,
            EMAIL_QL=email
        )

    class Meta:
        db_table = 'nguoiquanly'

# Model for lichsuquanly
class LichSuQuanLy(models.Model):
    MA_LICH_SU_QL = models.AutoField(primary_key=True)
    MA_KHU_VUC = models.ForeignKey(
        'nhatro.KhuVuc',
        on_delete=models.CASCADE,
        db_column='MA_KHU_VUC',
        related_name='lichsuquanly'
    )
    MA_QUAN_LY = models.ForeignKey(
        'NguoiQuanLy',
        on_delete=models.CASCADE,
        db_column='MA_QUAN_LY',
        related_name='lichsuquanly'
    )
    NGAY_BAT_DAU_QL = models.DateField(null=True, blank=True)
    NGAY_KET_THUC_QL = models.DateField(null=True, blank=True)
    LY_DO_KET_THUC = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Lịch sử quản lý {self.MA_LICH_SU_QL}"

    class Meta:
        db_table = 'lichsuquanly'