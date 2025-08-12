from django.db import models
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.phongtro.models import PhongTro, CocPhong
from apps.khachthue.models import KhachThue
from apps.thanhvien.models import TaiKhoan
import uuid

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
    THOI_HAN_HD = models.CharField(max_length=50, null=True, blank=True)
    NGAY_NHAN_PHONG = models.DateField(null=True, blank=True)
    NGAY_TRA_PHONG = models.DateField(null=True, blank=True)
    SO_THANH_VIEN = models.IntegerField(null=True, blank=True)
    GIA_THUE = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    NGAY_THU_TIEN = models.CharField(max_length=10, null=True, blank=True)
    PHUONG_THUC_THANH_TOAN = models.CharField(max_length=50, null=True, blank=True)
    TRANG_THAI_HD = models.CharField(max_length=50, null=True, blank=True)
    GHI_CHU_HD = models.TextField(null=True, blank=True)
    CHU_KY_THANH_TOAN = models.CharField(max_length=20, null=True, blank=True)
    GIA_COC_HD = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"Hợp đồng {self.MA_HOP_DONG} - Phòng {self.MA_PHONG_id}"

    class Meta:
        db_table = 'hopdong'
    def clean(self):
        """Validate dữ liệu hợp đồng."""
        if self.NGAY_NHAN_PHONG >= self.NGAY_TRA_PHONG:
            raise ValidationError('Ngày nhận phòng phải trước ngày trả phòng.')
        if self.SO_THANH_VIEN <= 0:
            raise ValidationError('Số thành viên phải lớn hơn 0.')
    def get_hop_dong_hieu_luc(ma_phong):
        try:
            hop_dong = HopDong.objects.filter(
                MA_PHONG=ma_phong,
                TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc', 'Đã xác nhận']
            ).first()
            if hop_dong:
                return {'GIA_THUE': float(hop_dong.GIA_THUE or 0.00)}, []
            return None, []
        except Exception as e:
            return None, [f'Lỗi khi lấy hợp đồng: {str(e)}']
    @classmethod
    def tao_hop_dong(cls, data):
        with transaction.atomic():
            phong = PhongTro.objects.get(MA_PHONG = data.get('MA_PHONG')) 
            khach_thue = cls._xu_ly_khach_thue(data)
            # Tạo hợp đồng
            hop_dong = cls(
                MA_PHONG=phong,
                NGAY_LAP_HD=data.get('NGAY_LAP_HD'),
                THOI_HAN_HD=data.get('THOI_HAN_HD'),
                NGAY_NHAN_PHONG=data.get('NGAY_NHAN_PHONG'),
                NGAY_TRA_PHONG=data.get('NGAY_TRA_PHONG'),
                SO_THANH_VIEN=data.get('SO_THANH_VIEN_TOI_DA'),
                GIA_THUE=data.get('GIA_THUE'),
                NGAY_THU_TIEN=data.get('NGAY_THU_TIEN'),
                PHUONG_THUC_THANH_TOAN=data.get('THOI_DIEM_THANH_TOAN'),
                TRANG_THAI_HD= 'Chờ xác nhận',
                GHI_CHU_HD=data.get('GHI_CHU_HD'),
                CHU_KY_THANH_TOAN=data.get('CHU_KY_THANH_TOAN'),
                GIA_COC_HD=data.get('GIA_COC_HD', 0.00)
            )
            hop_dong.full_clean()  # Validate trước khi lưu
            hop_dong.save()

            # Tạo LichSuHopDong
            LichSuHopDong.tao_lich_su(
                hop_dong=hop_dong,
                khach_thue=khach_thue,
                moi_quan_he='Chủ hợp đồng',
                ngay_tham_gia=data.get('NGAY_NHAN_PHONG')
            )

            return hop_dong
    @classmethod
    def _xu_ly_khach_thue(cls, data):
        with transaction.atomic():         
            khach_thue = KhachThue.kiem_tra_khach_thue(data.get('MA_KHACH_THUE'))
            if khach_thue:
                # Cập nhật thông tin khách thu            
                khach_thue.update_khach_thue(
                    ho_ten_kt=data.get('HO_TEN_KT'),
                    sdt_kt=data.get('SDT_KT'),
                    ngay_sinh_kt=data.get('NGAY_SINH_KT'),
                    gioi_tinh_kt=data.get('GIOI_TINH_KT'),               
                )    
                return khach_thue
            # Nếu chưa có cọc phòng, tạo tài khoản mặc định
            try:
                tai_khoan = TaiKhoan.create_tai_khoan_mac_dinh(
                    tai_khoan=data.get('TAI_KHOAN'),
                    mat_khau=data.get('MAT_KHAU')
                )
                khach_thue = KhachThue.create_khach_thue(
                    tai_khoan_obj=tai_khoan,
                    ho_ten_kt=data.get('HO_TEN_KT'),
                    sdt_kt=data.get('SDT_KT'),
                    ngay_sinh_kt=data.get('NGAY_SINH_KT'),
                    gioi_tinh_kt=data.get('GIOI_TINH_KT'),
                )
            except ValueError as e:
                raise ValueError(f"Lỗi khi tạo tài khoản hoặc khách thuê: {str(e)}")
            # Tạo khách thuê
                
            return khach_thue
        
    def cap_nhat_hop_dong(self, data):
        with transaction.atomic():
            phong = PhongTro.objects.get(MA_PHONG = data.get('MA_PHONG')) 
            khach_thue = self._get_khach_thue(data.get('MA_KHACH_THUE'))
            coc_phong = CocPhong.objects.get(MA_COC_PHONG=data.get('MA_COC_PHONG'))
            # Cập nhật hợp đồng
            self.MA_PHONG = phong
            self.NGAY_LAP_HD = data.get('NGAY_LAP_HD')
            self.THOI_HAN_HD = data.get('THOI_HAN_HD')
            self.NGAY_NHAN_PHONG = data.get('NGAY_NHAN_PHONG')
            self.NGAY_TRA_PHONG = data.get('NGAY_TRA_PHONG')
            self.SO_THANH_VIEN = data.get('SO_THANH_VIEN_TOI_DA')
            self.GIA_THUE = data.get('GIA_THUE')
            self.NGAY_THU_TIEN = data.get('NGAY_THU_TIEN')
            self.PHUONG_THUC_THANH_TOAN = data.get('PHUONG_THUC_THANH_TOAN')
            self.CHU_KY_THANH_TOAN = data.get('THOI_DIEM_THANH_TOAN')
            self.GHI_CHU_HD = data.get('GHI_CHU_HD')
            self.full_clean()  # Validate trước khi lưu
            self.save()
            # Cập nhật thông tin cọc phòng
            coc_phong.cap_nhat_coc_phong(
                tien_coc_phong=data.get('TIEN_COC_PHONG'),
                ngay_coc_phong=data.get('NGAY_NHAN_PHONG'),
                ngay_du_kien_vao=data.get('NGAY_NHAN_PHONG')    
            )
            khach_thue.update_khach_thue(
                ho_ten_kt=data.get('HO_TEN_KT'),
                sdt_kt=data.get('SDT_KT'),
                ngay_sinh_kt=data.get('NGAY_SINH_KT'),
                gioi_tinh_kt=data.get('GIOI_TINH_KT')             
            )

            # Cập nhật LichSuHopDong
            self._xu_ly_lich_su_hop_dong(khach_thue, data.get('NGAY_NHAN_PHONG'))


    def _get_khach_thue(self, ma_khach_thue):
        """Lấy bản ghi KhachThue, ném lỗi nếu không tồn tại."""
        try:
            return KhachThue.objects.get(MA_KHACH_THUE=ma_khach_thue)
        except KhachThue.DoesNotExist:
            raise ValidationError(f'Khách thuê {ma_khach_thue} không tồn tại.')

    def _xu_ly_lich_su_hop_dong(self, khach_thue, ngay_tham_gia):
        """Xử lý LichSuHopDong khi cập nhật hợp đồng."""
        lich_su = self.lichsuhopdong.filter(NGAY_ROI_DI__isnull=True).first()
        if lich_su and lich_su.MA_KHACH_THUE.MA_KHACH_THUE != khach_thue.MA_KHACH_THUE:
            lich_su.cap_nhat_ngay_roi_di()
            LichSuHopDong.tao_lich_su(
                hop_dong=self,
                khach_thue=khach_thue,
                moi_quan_he='Chủ hợp đồng',
                ngay_tham_gia=ngay_tham_gia
            )
        elif not lich_su:
            LichSuHopDong.tao_lich_su(
                hop_dong=self,
                khach_thue=khach_thue,
                moi_quan_he='Chủ hợp đồng',
                ngay_tham_gia=ngay_tham_gia
            )
    def delete_hop_dong(self):
        """Xóa hợp đồng và cập nhật trạng thái CocPhong."""
        with transaction.atomic():
            coc_phong = CocPhong.objects.filter(MA_PHONG=self.MA_PHONG).first()
            if coc_phong:
                coc_phong.TRANG_THAI_CP = 'Đã cọc'
                coc_phong.save()
            self.delete()

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
    @classmethod
    def create_or_update_lich_su_hop_dong(cls, khach_thue, hop_dong, moi_quan_he, ngay_tham_gia=None, ma_lich_su_hd=None):
        if not hop_dong or not moi_quan_he:
            raise ValueError('Phòng trọ và mối quan hệ là bắt buộc.')
        ngay_tham_gia = ngay_tham_gia or datetime.now().date()
        if ma_lich_su_hd:
            lich_su = cls.objects.filter(MA_LICH_SU_HD=ma_lich_su_hd).first()
            if lich_su:
                lich_su.MA_HOP_DONG = hop_dong
                lich_su.MOI_QUAN_HE = moi_quan_he
                lich_su.NGAY_THAM_GIA = ngay_tham_gia
                lich_su.save()
                return lich_su
        return cls.objects.create(
            MA_HOP_DONG=hop_dong,
            MA_KHACH_THUE=khach_thue,
            MOI_QUAN_HE=moi_quan_he,
            NGAY_THAM_GIA=ngay_tham_gia
        )
    @classmethod
    def tao_lich_su(cls, hop_dong, khach_thue, moi_quan_he, ngay_tham_gia):
        lich_su = cls(
            MA_HOP_DONG=hop_dong,
            MA_KHACH_THUE=khach_thue,
            MOI_QUAN_HE=moi_quan_he,
            NGAY_THAM_GIA=ngay_tham_gia
        )
        lich_su.save()
        return lich_su

    def cap_nhat_ngay_roi_di(self):
        """Cập nhật ngày rời đi cho bản ghi lịch sử."""
        self.NGAY_ROI_DI = datetime.now().date()
        self.save()
    

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