from django.db import models
from django.core.exceptions import ValidationError
from apps.nhatro.models import KhuVuc
from datetime import date, datetime
from django.utils import timezone
import os
from django.conf import settings

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

# Model for cocphong - Hỗ trợ cả admin tạo và guest booking online
class CocPhong(models.Model):
    MA_COC_PHONG = models.AutoField(primary_key=True)
    MA_PHONG = models.ForeignKey(
        'PhongTro',
        on_delete=models.CASCADE,
        db_column='MA_PHONG',
        related_name='cocphong'
    )
    
    # Khách thuê (null khi là guest booking chưa xác nhận)
    MA_KHACH_THUE = models.ForeignKey(
        'khachthue.KhachThue',
        on_delete=models.CASCADE,
        db_column='MA_KHACH_THUE',
        related_name='cocphong',
        null=True, blank=True
    )
    
    # Thông tin tạm thời cho guest booking (khi MA_KHACH_THUE = null)
    HO_TEN_TEMP = models.CharField(
        max_length=200, 
        null=True, blank=True,
        verbose_name="Họ tên (tạm thời)"
    )
    SO_DIEN_THOAI_TEMP = models.CharField(
        max_length=15, 
        null=True, blank=True,
        verbose_name="Số điện thoại (tạm thời)"
    )
    EMAIL_TEMP = models.EmailField(
        max_length=100, 
        null=True, blank=True,
        verbose_name="Email (tạm thời)"
    )
    
    # Thông tin cọc phòng
    NGAY_COC_PHONG = models.DateField(null=True, blank=True)
    NGAY_DU_KIEN_VAO = models.DateField(null=True, blank=True)
    TIEN_COC_PHONG = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Trạng thái và nguồn tạo
    TRANG_THAI_CP = models.CharField(
        max_length=50, 
        choices=[
            ('CHO_XAC_NHAN', 'Chờ xác nhận'),
            ('DA_XAC_NHAN', 'Đã xác nhận'),
            ('DA_COC', 'Đã cọc'),
            ('DA_SU_DUNG', 'Đã sử dụng'),
            ('DA_HOAN_TRA', 'Đã hoàn trả'),
            ('DA_THU_HOI', 'Đã thu hồi'),
            ('DA_TU_CHOI', 'Đã từ chối'),
            ('DA_HUY', 'Đã hủy')
        ],
        default='CHO_XAC_NHAN',
        null=True, blank=True
    )
    
    NGUON_TAO = models.CharField(
        max_length=20,
        choices=[
            ('ADMIN', 'Admin tạo'),
            ('ONLINE', 'Đặt phòng online')
        ],
        default='ADMIN',
        verbose_name="Nguồn tạo"
    )
    
    GHI_CHU_CP = models.TextField(null=True, blank=True)
    LY_DO_TU_CHOI = models.TextField(null=True, blank=True, verbose_name="Lý do từ chối")
    NGAY_TAO = models.DateField(auto_now_add=True, null=True, blank=True, verbose_name="Ngày tạo")

    def __str__(self):
        if self.MA_KHACH_THUE:
            return f"Cọc phòng {self.MA_COC_PHONG} - {self.MA_KHACH_THUE.HO_TEN_KT} - Phòng {self.MA_PHONG.TEN_PHONG}"
        return f"Đặt phòng {self.MA_COC_PHONG} - {self.HO_TEN_TEMP} - Phòng {self.MA_PHONG.TEN_PHONG}"

    class Meta:
        db_table = 'cocphong'
        ordering = ['-NGAY_TAO']
        verbose_name = "Cọc phòng / Đặt phòng"
        verbose_name_plural = "Cọc phòng / Đặt phòng"
    def clean(self):
        """Validate dữ liệu CocPhong."""
        if self.TIEN_COC_PHONG and self.TIEN_COC_PHONG <= 0:
            raise ValidationError('Tiền cọc phải lớn hơn 0.')
        
        # Kiểm tra null trước khi so sánh ngày
        if self.NGAY_COC_PHONG and self.NGAY_DU_KIEN_VAO:
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
        # Validate inputs trước khi cập nhật
        if tien_coc_phong is not None and tien_coc_phong <= 0:
            raise ValueError('Tiền cọc phải lớn hơn 0.')
        
        self.TIEN_COC_PHONG = tien_coc_phong if tien_coc_phong is not None else self.TIEN_COC_PHONG
        self.NGAY_COC_PHONG = ngay_coc_phong if ngay_coc_phong is not None else self.NGAY_COC_PHONG
        self.NGAY_DU_KIEN_VAO = ngay_du_kien_vao if ngay_du_kien_vao is not None else self.NGAY_DU_KIEN_VAO
        self.GHI_CHU_CP = ghi_chu_cp if ghi_chu_cp is not None else self.GHI_CHU_CP
        self.full_clean()  # Validate dữ liệu
        self.save()

    @classmethod
    def tao_coc_phong(cls, phong, khach_thue, tien_coc_phong, ngay_coc_phong):
        """Tạo cọc phòng từ admin (có khách thuê)"""
        cls.check_duplicate(phong)
        coc_phong = cls(
            MA_PHONG=phong,
            MA_KHACH_THUE=khach_thue,
            NGAY_COC_PHONG=ngay_coc_phong,
            NGAY_DU_KIEN_VAO=ngay_coc_phong,
            TIEN_COC_PHONG=tien_coc_phong,
            TRANG_THAI_CP='DA_COC',
            NGUON_TAO='ADMIN'
        )
        coc_phong.full_clean()
        coc_phong.save()
        return coc_phong

    @classmethod
    def tao_dat_phong_online(cls, phong, ho_ten, so_dien_thoai, email, ngay_du_kien_vao, tien_coc, ghi_chu=None):
        """Tạo đặt phòng online (chưa có khách thuê)"""
        # Validate input trước khi tạo
        if not ngay_du_kien_vao:
            raise ValueError('Ngày dự kiến vào không được để trống.')
        if not tien_coc or tien_coc <= 0:
            raise ValueError('Tiền cọc phải lớn hơn 0.')
        
        cls.check_duplicate(phong)
        dat_phong = cls(
            MA_PHONG=phong,
            MA_KHACH_THUE=None,  # Chưa có khách thuê
            HO_TEN_TEMP=ho_ten,
            SO_DIEN_THOAI_TEMP=so_dien_thoai,
            EMAIL_TEMP=email,
            NGAY_DU_KIEN_VAO=ngay_du_kien_vao,
            TIEN_COC_PHONG=tien_coc,
            TRANG_THAI_CP='CHO_XAC_NHAN',
            NGUON_TAO='ONLINE',
            GHI_CHU_CP=ghi_chu
            # NGAY_TAO sẽ tự động được set bởi auto_now_add=True
        )
        dat_phong.full_clean()
        dat_phong.save()
        return dat_phong

    def xac_nhan_dat_phong_online(self):
        """Admin xác nhận đặt phòng online"""
        if self.NGUON_TAO != 'ONLINE':
            raise ValueError('Chỉ có thể xác nhận đặt phòng online.')
        if self.TRANG_THAI_CP != 'CHO_XAC_NHAN':
            raise ValueError('Chỉ có thể xác nhận đặt phòng ở trạng thái Chờ xác nhận.')
        
        self.TRANG_THAI_CP = 'DA_XAC_NHAN'
        self.save()
        return self

    def tu_choi_dat_phong_online(self, ly_do):
        """Admin từ chối đặt phòng online"""
        if self.NGUON_TAO != 'ONLINE':
            raise ValueError('Chỉ có thể từ chối đặt phòng online.')
        if self.TRANG_THAI_CP != 'CHO_XAC_NHAN':
            raise ValueError('Chỉ có thể từ chối đặt phòng ở trạng thái Chờ xác nhận.')
        
        self.TRANG_THAI_CP = 'DA_TU_CHOI'
        self.LY_DO_TU_CHOI = ly_do
        self.save()
        return self

    def chuyen_thanh_coc_phong(self, khach_thue):
        """Chuyển đặt phòng online thành cọc phòng (sau khi tạo khách thuê)"""
        if self.NGUON_TAO != 'ONLINE':
            raise ValueError('Chỉ có thể chuyển đặt phòng online.')
        if self.TRANG_THAI_CP != 'DA_XAC_NHAN':
            raise ValueError('Chỉ có thể chuyển đặt phòng đã được xác nhận.')
        
        self.MA_KHACH_THUE = khach_thue
        # Kiểm tra null trước khi gán
        if self.NGAY_DU_KIEN_VAO:
            self.NGAY_COC_PHONG = self.NGAY_DU_KIEN_VAO
        else:
            from datetime import date
            self.NGAY_COC_PHONG = date.today()
        self.TRANG_THAI_CP = 'DA_COC'
        # Xóa thông tin tạm thời
        self.HO_TEN_TEMP = None
        self.SO_DIEN_THOAI_TEMP = None
        self.EMAIL_TEMP = None
        self.save()
        return self

    @property
    def ten_khach_thue(self):
        """Trả về tên khách thuê"""
        if self.MA_KHACH_THUE:
            return self.MA_KHACH_THUE.HO_TEN_KT
        return self.HO_TEN_TEMP

    @property
    def sdt_khach_thue(self):
        """Trả về SĐT khách thuê"""
        if self.MA_KHACH_THUE:
            return self.MA_KHACH_THUE.SDT_KT
        return self.SO_DIEN_THOAI_TEMP

    @property
    def email_khach_thue(self):
        """Trả về email khách thuê"""
        if self.MA_KHACH_THUE:
            return self.MA_KHACH_THUE.EMAIL_KT
        return self.EMAIL_TEMP
    
    @property 
    def ngay_tao_display(self):
        """Hiển thị ngày tạo an toàn"""
        if self.NGAY_TAO:
            return self.NGAY_TAO
        else:
            # Fallback cho dữ liệu cũ - trả về date
            from datetime import date
            return date.today()

class TAISAN(models.Model):
    MA_TAI_SAN = models.IntegerField(primary_key=True)
    TEN_TAI_SAN = models.CharField(max_length=100, null=True, blank=True)
    MO_TA = models.TextField(null=True, blank=True)
    DON_VI_TS = models.CharField(max_length=20, default='cái', null=True, blank=True)
    GIA_TS = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'taisan'
    
    @classmethod
    def tao_tai_san_tu_ten(cls, ten_tai_san):
        """Tạo hoặc lấy tài sản từ tên"""
        tai_san, created = cls.objects.get_or_create(
            TEN_TAI_SAN=ten_tai_san,
            defaults={
                'DON_VI_TS': 'cái',
                'GIA_TS': 0.00
            }
        )
        return tai_san

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
        # Lưu từng đối tượng riêng lẻ để tránh lỗi bulk_create với foreign key
        for tai_san_ban_giao in danh_sach:
            tai_san_ban_giao.save()

    @classmethod
    def tao_tai_san_tu_form(cls, hop_dong, danh_sach_tai_san_co_ban, danh_sach_tai_san_tuy_chinh):
        """Tạo tài sản bàn giao từ form data"""
        danh_sach_ban_giao = []
        
        # Xử lý tài sản cơ bản
        for tai_san_data in danh_sach_tai_san_co_ban:
            if tai_san_data.get('selected'):
                # Tạo hoặc lấy tài sản và đảm bảo nó đã được lưu
                tai_san = TAISAN.tao_tai_san_tu_ten(tai_san_data['name'])
                
                # Tạo bản ghi bàn giao sử dụng ID thay vì đối tượng
                ban_giao = cls(
                    MA_HOP_DONG=hop_dong,
                    MA_TAI_SAN_id=tai_san.MA_TAI_SAN,  # Sử dụng ID thay vì đối tượng
                    SO_LUONG=1,
                    TINH_TRANG_GIAO=tai_san_data.get('condition', 'Tốt'),
                    GHI_CHU=f"Tài sản cơ bản: {tai_san_data['name']}"
                )
                danh_sach_ban_giao.append(ban_giao)
        
        # Xử lý tài sản tùy chỉnh
        for tai_san_data in danh_sach_tai_san_tuy_chinh:
            ten_tai_san = tai_san_data.get('name', '').strip()
            if ten_tai_san:
                # Tạo hoặc lấy tài sản và đảm bảo nó đã được lưu
                tai_san = TAISAN.tao_tai_san_tu_ten(ten_tai_san)
                
                # Tạo bản ghi bàn giao sử dụng ID thay vì đối tượng
                ban_giao = cls(
                    MA_HOP_DONG=hop_dong,
                    MA_TAI_SAN_id=tai_san.MA_TAI_SAN,  # Sử dụng ID thay vì đối tượng
                    SO_LUONG=1,
                    TINH_TRANG_GIAO=tai_san_data.get('condition', 'Tốt'),
                    GHI_CHU=f"Tài sản tùy chỉnh: {ten_tai_san}"
                )
                danh_sach_ban_giao.append(ban_giao)
        
        # Lưu từng đối tượng riêng lẻ để tránh lỗi bulk_create với foreign key
        danh_sach_da_luu = []
        for ban_giao in danh_sach_ban_giao:
            ban_giao.save()
            danh_sach_da_luu.append(ban_giao)
        
        return danh_sach_da_luu


# Model for tin đăng phòng - Đăng phòng có sẵn lên giao diện tìm phòng
class DangTinPhong(models.Model):
    MA_TIN_DANG = models.AutoField(primary_key=True)
    MA_PHONG = models.OneToOneField(
        'PhongTro',
        on_delete=models.CASCADE,
        db_column='MA_PHONG',
        related_name='tin_dang'
    )
    
    # Thông tin tin đăng
    TIEU_DE = models.CharField(max_length=200, verbose_name="Tiêu đề tin đăng")
    MO_TA_TIN = models.TextField(null=True, blank=True, verbose_name="Mô tả tin đăng")
    NGAY_HET_HANG_TIN = models.DateField(null=True, blank=True, verbose_name="Ngày hết hạn tin")
    
    # Thông tin liên hệ
    SDT_LIEN_HE = models.CharField(max_length=15, verbose_name="Số điện thoại liên hệ")
    EMAIL_LIEN_HE = models.EmailField(max_length=100, null=True, blank=True, verbose_name="Email liên hệ")
    
    # Trạng thái tin đăng
    TRANG_THAI = models.CharField(
        max_length=20,
        choices=[
            ('DANG_HIEN_THI', 'Đang hiển thị'),
            ('DA_AN', 'Đã ẩn'),
        ],
        default='DANG_HIEN_THI',
        verbose_name="Trạng thái"
    )
    
    NGAY_DANG = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng")
    NGAY_CAP_NHAT = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    
    # Thống kê
    LUOT_XEM = models.IntegerField(default=0, verbose_name="Lượt xem")
    LUOT_LIEN_HE = models.IntegerField(default=0, verbose_name="Lượt liên hệ")
    
    def __str__(self):
        return f"Tin đăng - {self.MA_PHONG.TEN_PHONG}"
    
    class Meta:
        db_table = 'dangtinphong'
        ordering = ['-NGAY_CAP_NHAT']
        verbose_name = "Tin đăng phòng"
        verbose_name_plural = "Tin đăng phòng"
    
    @property
    def hinh_anh_dai_dien(self):
        """Lấy hình ảnh đại diện (hình đầu tiên)."""
        return self.hinh_anh.first()
    
    def tang_luot_xem(self):
        """Tăng lượt xem tin đăng."""
        self.LUOT_XEM += 1
        self.save(update_fields=['LUOT_XEM'])
    
    def tang_luot_lien_he(self):
        """Tăng lượt liên hệ tin đăng."""
        self.LUOT_LIEN_HE += 1
        self.save(update_fields=['LUOT_LIEN_HE'])
    
    def set_default_expiry_date(self, days=30):
        """Đặt ngày hết hạn mặc định (30 ngày từ ngày đăng)."""
        from datetime import timedelta
        if not self.NGAY_HET_HANG_TIN:
            self.NGAY_HET_HANG_TIN = (self.NGAY_DANG.date() if self.NGAY_DANG else date.today()) + timedelta(days=days)
    
    @property
    def is_expired(self):
        """Kiểm tra tin đăng đã hết hạn chưa."""
        from datetime import date
        if self.NGAY_HET_HANG_TIN:
            return date.today() > self.NGAY_HET_HANG_TIN
        return False
    
    @property
    def days_until_expiry(self):
        """Số ngày còn lại đến hết hạn."""
        from datetime import date
        if self.NGAY_HET_HANG_TIN:
            delta = self.NGAY_HET_HANG_TIN - date.today()
            return delta.days if delta.days >= 0 else 0
        return None
    
    def clean(self):
        """Validation cho model."""
        from datetime import date
        super().clean()
        
        if self.NGAY_HET_HANG_TIN and self.NGAY_HET_HANG_TIN <= date.today():
            raise ValidationError('Ngày hết hạn tin phải sau ngày hiện tại.')
        
        if not self.TIEU_DE or len(self.TIEU_DE.strip()) < 10:
            raise ValidationError('Tiêu đề tin đăng phải có ít nhất 10 ký tự.')
    
    def save(self, *args, **kwargs):
        """Override save để tự động đặt ngày hết hạn."""
        if not self.NGAY_HET_HANG_TIN:
            self.set_default_expiry_date()
        super().save(*args, **kwargs)


def hinh_anh_tin_dang_path(instance, filename):
    """Đường dẫn lưu hình ảnh tin đăng."""
    ext = filename.split('.')[-1]
    filename = f"tin_{instance.MA_TIN_DANG.MA_TIN_DANG}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('tin_dang', str(instance.MA_TIN_DANG.MA_TIN_DANG), filename)


# Model for hình ảnh tin đăng  
class HinhAnhTinDang(models.Model):
    MA_HINH_ANH = models.AutoField(primary_key=True)
    MA_TIN_DANG = models.ForeignKey(
        'DangTinPhong',
        on_delete=models.CASCADE,
        db_column='MA_TIN_DANG',
        related_name='hinh_anh'
    )
    
    HINH_ANH = models.ImageField(
        upload_to=hinh_anh_tin_dang_path,
        verbose_name="Hình ảnh"
    )
    THU_TU = models.PositiveIntegerField(default=1, verbose_name="Thứ tự hiển thị")
    MO_TA = models.CharField(max_length=200, null=True, blank=True, verbose_name="Mô tả hình ảnh")
    
    NGAY_TAO = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    
    def __str__(self):
        return f"Hình ảnh {self.THU_TU} - {self.MA_TIN_DANG}"
    
    class Meta:
        db_table = 'hinhanhtindang'
        ordering = ['THU_TU']
        verbose_name = "Hình ảnh tin đăng"
        verbose_name_plural = "Hình ảnh tin đăng"

