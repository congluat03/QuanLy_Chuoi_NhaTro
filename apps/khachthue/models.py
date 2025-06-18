import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models, transaction

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
    ANH_KT = models.ImageField(upload_to='avatars/', null=True, blank=True)
    TRANG_THAI_KT = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.HO_TEN_KT or f"Khách thuê {self.MA_KHACH_THUE}"
    
    class Meta:
        db_table = 'khachthue'
    @staticmethod
    def validate_required_fields(ho_ten_kt, sdt_kt):
        if not ho_ten_kt or not sdt_kt:
            raise ValueError('Vui lòng điền đầy đủ các trường bắt buộc.')

    @classmethod
    def create_khach_thue(cls, tai_khoan_obj, ho_ten_kt, sdt_kt, email_kt=None, nghe_nghiep=None, avatar=None):
        cls.validate_required_fields(ho_ten_kt, sdt_kt)
        return cls.objects.create(
            MA_TAI_KHOAN=tai_khoan_obj,
            HO_TEN_KT=ho_ten_kt,
            SDT_KT=sdt_kt,
            EMAIL_KT=email_kt,
            NGHE_NGHIEP=nghe_nghiep,
            TRANG_THAI_KT='Hoạt động',
            ANH_KT=avatar
        )

    def update_khach_thue(self, ho_ten_kt=None, sdt_kt=None, ngay_sinh_kt=None, email_kt=None, nghe_nghiep=None,
                          avatar=None, gioi_tinh_kt=None, noi_sinh_kt=None):
        """Cập nhật thông tin khách thuê."""
        if ho_ten_kt and sdt_kt and ngay_sinh_kt:
            self.validate_required_fields(ho_ten_kt, sdt_kt)
        self.HO_TEN_KT = ho_ten_kt or self.HO_TEN_KT
        self.SDT_KT = sdt_kt or self.SDT_KT
        self.NGAY_SINH_KT = ngay_sinh_kt or self.NGAY_SINH_KT
        self.EMAIL_KT = email_kt if email_kt is not None else self.EMAIL_KT
        self.NGHE_NGHIEP = nghe_nghiep if nghe_nghiep is not None else self.NGHE_NGHIEP
        self.GIOI_TINH_KT = gioi_tinh_kt if gioi_tinh_kt is not None else self.GIOI_TINH_KT
        self.NOI_SINH_KT = noi_sinh_kt if noi_sinh_kt is not None else self.NOI_SINH_KT
        if avatar:
            if self.ANH_KT:
                self.ANH_KT.delete(save=False)
            self.ANH_KT = avatar
        self.save()
    def is_nguoi_dai_dien(self):
        return self.lichsuhopdong.filter(
            MOI_QUAN_HE='Chủ hợp đồng',
            MA_HOP_DONG__TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc'],
        ).exists()

    def delete_khach_thue(self):
        with transaction.atomic():
            # Kiểm tra nếu là người đại diện
            if self.is_nguoi_dai_dien():
                raise ValueError('Không thể xóa khách thuê vì đây là người đại diện.')

            # Xóa lịch sử hợp đồng
            self.lichsuhopdong.all().delete()

            # Xóa ảnh đại diện nếu có
            if self.ANH_KT:
                self.ANH_KT.delete(save=False)

            # Lưu tài khoản để xóa sau
            tai_khoan = self.MA_TAI_KHOAN

            # Xóa khách thuê
            self.delete()

            # Xóa tài khoản nếu không được sử dụng bởi khách thuê khác
            tai_khoan.delete()
    def update_cccd_cmnd(self, ma_cccd, so_cmnd_cccd, ngay_cap=None, anh_mat_truoc=None, anh_mat_sau=None,
                        gioi_tinh_kt=None, ngay_sinh_kt=None, que_quan=None, dia_chi_thuong_tru=None):
        """Cập nhật hoặc tạo mới thông tin CCCD/CMND và thông tin khách thuê."""
        if not so_cmnd_cccd or not (len(so_cmnd_cccd) in [9, 12] and so_cmnd_cccd.isdigit()):
            raise ValueError('Số CCCD/CMND phải là 9 hoặc 12 số.')

        with transaction.atomic():
            cccd_cmnd, created = CccdCmnd.objects.get_or_create(
                MA_KHACH_THUE=self,
                MA_CCCD=ma_cccd,
                defaults={
                    'SO_CMND_CCCD': so_cmnd_cccd,
                    'NGAY_CAP': ngay_cap,                   
                    'DIA_CHI_THUONG_TRU': dia_chi_thuong_tru,
                    'ANH_MAT_TRUOC': anh_mat_truoc,
                    'ANH_MAT_SAU': anh_mat_sau
                }
            )
            if not created:
                cccd_cmnd.update_cccd_cmnd(so_cmnd_cccd, ngay_cap, anh_mat_truoc, anh_mat_sau, dia_chi_thuong_tru)

            self.update_khach_thue(
                ho_ten_kt=self.HO_TEN_KT,
                sdt_kt=self.SDT_KT,
                ngay_sinh_kt=ngay_sinh_kt,
                noi_sinh_kt =que_quan,
                gioi_tinh_kt=gioi_tinh_kt
            )

# Model for cccd_cmnd
class CccdCmnd(models.Model):
    MA_CCCD = models.AutoField(primary_key=True)
    SO_CMND_CCCD = models.CharField(max_length=20)
    MA_KHACH_THUE = models.ForeignKey(
        'KhachThue',
        on_delete=models.CASCADE,
        db_column='MA_KHACH_THUE',
        related_name='cccd_cmnd'
    )
    NGAY_CAP = models.DateField(null=True, blank=True)
    ANH_MAT_TRUOC = models.ImageField(upload_to='', null=True, blank=True)
    ANH_MAT_SAU = models.ImageField(upload_to='', null=True, blank=True)
    DIA_CHI_THUONG_TRU = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"CCCD/CMND {self.SO_CMND_CCCD}"

    class Meta:
        db_table = 'cccd_cmnd'

    def validate_cccd_cmnd(self, so_cmnd_cccd):
        """Kiểm tra định dạng số CCCD/CMND (9 hoặc 12 số)."""
        if not (len(so_cmnd_cccd) in [9, 12] and so_cmnd_cccd.isdigit()):
            raise ValueError('Số CCCD/CMND phải là 9 hoặc 12 số.')

    def validate_image(self, image):
        """Kiểm tra kích thước và định dạng ảnh."""
        if image and image.size > 5 * 1024 * 1024:  # 5MB
            raise ValueError('Ảnh không được lớn hơn 5MB.')
        if image and os.path.splitext(image.name)[1].lower() not in ['.jpg', '.jpeg', '.png']:
            raise ValueError('Chỉ hỗ trợ định dạng JPG hoặc PNG.')

    def _save_image(self, image, is_front=True):
        """Lưu ảnh vào cccd_cmnd/MA_KHACH_THUE/ với tên front_MA_KHACH_THUE hoặc back_MA_KHACH_THUE."""
        if not image:
            return

        self.validate_image(image)
        base_path = os.path.join('cccd_cmnd', str(self.MA_KHACH_THUE.MA_KHACH_THUE))
        os.makedirs(os.path.join(settings.MEDIA_ROOT, base_path), exist_ok=True)
        prefix = 'front' if is_front else 'back'
        filename = f'{prefix}_{self.MA_KHACH_THUE.MA_KHACH_THUE}{os.path.splitext(image.name)[1]}'
        file_path = os.path.join(base_path, filename)
        target_field = self.ANH_MAT_TRUOC if is_front else self.ANH_MAT_SAU

        # Xóa ảnh cũ nếu tồn tại
        if target_field and target_field:
            try:
                if default_storage.exists(target_field.path):
                    default_storage.delete(target_field.path)
            except Exception:
                pass  # Bỏ qua lỗi nếu file không tồn tại hoặc không thể xóa

        # Lưu ảnh mới
        target_field.save(file_path, ContentFile(image.read()), save=False)
    def update_cccd_cmnd(self, so_cmnd_cccd, ngay_cap=None, anh_mat_truoc=None, anh_mat_sau=None,
                        dia_chi_thuong_tru=None):
        """Cập nhật hoặ tạo mới thông tin CCCD/CMND và lưu ảnh."""
        self.validate_cccd_cmnd(so_cmnd_cccd)
        self.SO_CMND_CCCD = so_cmnd_cccd
        self.NGAY_CAP = ngay_cap
        self.DIA_CHI_THUONG_TRU = dia_chi_thuong_tru if dia_chi_thuong_tru is not None else self.DIA_CHI_THUONG_TRU

        if anh_mat_truoc:
            self._save_image(anh_mat_truoc, is_front=True)
        if anh_mat_sau:
            self._save_image(anh_mat_sau, is_front=False)

        self.save()

