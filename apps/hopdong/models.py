from django.db import models
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.phongtro.models import PhongTro, CocPhong
from apps.khachthue.models import KhachThue
from apps.thanhvien.models import TaiKhoan
import uuid

# Import models cấu hình hóa đơn (optional - không cần thiết cho logic cơ bản)
try:
    from .invoice_config_models import (
        CauHinhHoaDon, 
        ChiTietCauHinhPhi, 
        LichSuHoaDonCauHinh,
        ThietLapHoaDonMacDinh
    )
except ImportError:
    # Nếu không có file invoice_config_models, bỏ qua
    pass

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
    THOI_DIEM_THANH_TOAN = models.CharField(max_length=20, null=True, blank=True)  # Đầu kỳ/Cuối kỳ
    TRANG_THAI_HD = models.CharField(max_length=50, null=True, blank=True)
    GHI_CHU_HD = models.TextField(null=True, blank=True)
    CHU_KY_THANH_TOAN = models.CharField(max_length=20, null=True, blank=True)
    GIA_COC_HD = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Trạng thái xác nhận của khách hàng
    KHACH_DA_XAC_NHAN = models.BooleanField(
        default=False,
        verbose_name="Khách đã xác nhận hợp đồng"
    )
    NGAY_KHACH_XAC_NHAN = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Ngày khách xác nhận"
    )
    
    def __str__(self):
        return f"Hợp đồng {self.MA_HOP_DONG} - Phòng {self.MA_PHONG_id}"

    class Meta:
        db_table = 'hopdong'
    def clean(self):
        """Validate dữ liệu hợp đồng."""
        # Kiểm tra ngày nhận phòng và ngày trả phòng
        if self.NGAY_NHAN_PHONG and self.NGAY_TRA_PHONG:
            if self.NGAY_NHAN_PHONG >= self.NGAY_TRA_PHONG:
                raise ValidationError('Ngày nhận phòng phải trước ngày trả phòng.')
        
        # Kiểm tra số thành viên
        if self.SO_THANH_VIEN is not None and self.SO_THANH_VIEN <= 0:
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
                THOI_DIEM_THANH_TOAN=data.get('THOI_DIEM_THANH_TOAN'),
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
            self.THOI_DIEM_THANH_TOAN = data.get('THOI_DIEM_THANH_TOAN')
            self.CHU_KY_THANH_TOAN = data.get('CHU_KY_THANH_TOAN')
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

    def xac_nhan_hop_dong(self):
        """Xác nhận hợp đồng và sinh hóa đơn bắt đầu nếu chưa có"""
        from apps.phongtro.models import CocPhong
        
        try:
            with transaction.atomic():
                if self.TRANG_THAI_HD != 'Chờ xác nhận':
                    raise ValueError('Chỉ có thể xác nhận hợp đồng ở trạng thái chờ xác nhận')
                
                # 1. Kiểm tra hóa đơn bắt đầu đã tồn tại chưa
                hoa_don_bat_dau = self.get_hoa_don_bat_dau()
                
                if not hoa_don_bat_dau:
                    # 2a. Chưa có hóa đơn bắt đầu -> Tạo hóa đơn bắt đầu
                    hoa_don, error = self.sinh_hoa_don_bat_dau()
                    
                    if not hoa_don:
                        raise ValueError(f'Lỗi sinh hóa đơn: {error}')
                    
                    hoa_don_bat_dau = hoa_don
                
                # 3. Cập nhật trạng thái hợp đồng
                self.TRANG_THAI_HD = 'Đang hoạt động'
                self.save()
                
                # 4. Cập nhật trạng thái phòng
                self.MA_PHONG.TRANG_THAI_P = 'Đang ở'
                self.MA_PHONG.save()
                
                # 5. Cập nhật trạng thái cọc phòng
                CocPhong.cap_nhat_trang_thai_coc(self.MA_PHONG, 'Đã sử dụng')
                
                return hoa_don_bat_dau, None
                
        except Exception as e:
            return None, str(e)

    def khach_hang_xac_nhan_hop_dong(self):
        """Khách hàng xác nhận hợp đồng và sinh hóa đơn bắt đầu nếu chưa có"""
        
        try:
            with transaction.atomic():
                if self.KHACH_DA_XAC_NHAN:
                    return None, 'Khách hàng đã xác nhận hợp đồng trước đó'
                
                # 1. Kiểm tra hóa đơn bắt đầu đã tồn tại chưa
                hoa_don_bat_dau = self.get_hoa_don_bat_dau()
                
                if not hoa_don_bat_dau:
                    # 2a. Chưa có hóa đơn bắt đầu -> Tạo hóa đơn bắt đầu
                    hoa_don, error = self.sinh_hoa_don_bat_dau()
                    if not hoa_don:
                        raise ValueError(f'Lỗi sinh hóa đơn: {error}')
                    hoa_don_bat_dau = hoa_don
                
                # 3. Cập nhật trạng thái xác nhận của khách
                self.KHACH_DA_XAC_NHAN = True
                self.NGAY_KHACH_XAC_NHAN = timezone.now()
                
                # 4. Cập nhật trạng thái hợp đồng nếu cần
                if self.TRANG_THAI_HD == 'Chờ xác nhận':
                    self.TRANG_THAI_HD = 'Đang hoạt động'
                
                self.save()
                
                return hoa_don_bat_dau, None
                
        except Exception as e:
            return None, str(e)

    def sinh_hoa_don_bat_dau(self):
        """Sinh hóa đơn bắt đầu hợp đồng"""
        try:
            # Sử dụng logic đơn giản thay vì cấu hình phức tạp
            return self._sinh_hoa_don_bat_dau_mac_dinh()
            
        except Exception as e:
            return None, str(e)
    
    def _sinh_hoa_don_bat_dau_mac_dinh(self):
        """Sinh hóa đơn bắt đầu theo cách mặc định (backward compatibility)"""
        from django.apps import apps
        
        HoaDon = apps.get_model('hoadon', 'HoaDon')
        
        # Tính toán các khoản phí
        tien_phong = self.GIA_THUE or 0
        tien_coc = self.GIA_COC_HD or 0  # Lấy từ phòng
        tien_dich_vu = 0  # Có thể tính từ dịch vụ nếu cần
        
        # Tạo hóa đơn bắt đầu
        hoa_don = HoaDon.objects.create(
            MA_HOP_DONG=self,
            LOAI_HOA_DON='Hóa đơn bắt đầu',
            NGAY_LAP_HDON=timezone.now().date(),
            TIEN_PHONG=tien_phong,
            TIEN_DICH_VU=tien_dich_vu,
            TIEN_COC=tien_coc,
            TIEN_KHAU_TRU=0,
            TONG_TIEN=tien_phong + tien_dich_vu + tien_coc,
            TRANG_THAI_HDON='Chưa thanh toán'
        )
        
        return hoa_don, None

    def sinh_hoa_don_ket_thuc(self):
        """Sinh hóa đơn kết thúc hợp đồng dựa trên cấu hình"""
        from django.apps import apps
        
        try:
            # Kiểm tra đã sinh hóa đơn kết thúc chưa
            if self.get_hoa_don_ket_thuc():
                return None, 'Đã sinh hóa đơn kết thúc trước đó'
            
            HoaDon = apps.get_model('hoadon', 'HoaDon')
            
            # Lấy cấu hình hóa đơn kết thúc
            cau_hinh = ThietLapHoaDonMacDinh.lay_cau_hinh_mac_dinh('ket_thuc', self)
            
            if cau_hinh:
                return self._sinh_hoa_don_theo_cau_hinh(cau_hinh, 'Hóa đơn kết thúc')
            else:
                # Fallback về cách cũ nếu không có cấu hình
                return self._sinh_hoa_don_ket_thuc_mac_dinh()
            
        except Exception as e:
            return None, str(e)
    
    def _sinh_hoa_don_ket_thuc_mac_dinh(self):
        """Sinh hóa đơn kết thúc theo cách mặc định (backward compatibility)"""
        from django.apps import apps
        
        HoaDon = apps.get_model('hoadon', 'HoaDon')
        
        # Tính toán các khoản phí kết thúc
        tien_hoan_coc = self.GIA_COC_HD or 0  # Tiền cọc hoàn lại
        tien_phat = 0  # Có thể có phí phạt nếu kết thúc sớm
        tien_dich_vu_cuoi = 0  # Dịch vụ tháng cuối
        
        # Tạo hóa đơn kết thúc (thường là hoàn tiền cọc)
        hoa_don = HoaDon.objects.create(
            MA_HOP_DONG=self,
            LOAI_HOA_DON='Hóa đơn kết thúc',
            NGAY_LAP_HDON=timezone.now().date(),
            TIEN_PHONG=0,
            TIEN_DICH_VU=tien_dich_vu_cuoi,
            TIEN_COC=-tien_hoan_coc,  # Số âm = hoàn lại
            TIEN_KHAU_TRU=tien_phat,
            TONG_TIEN=-tien_hoan_coc + tien_dich_vu_cuoi + tien_phat,
            TRANG_THAI_HDON='Chưa thanh toán'
        )
        
        return hoa_don, None
    
    def _sinh_hoa_don_theo_cau_hinh(self, cau_hinh, loai_hoa_don):
        """
        Sinh hóa đơn dựa trên cấu hình đã thiết lập
        """
        from django.apps import apps
        from decimal import Decimal
        
        HoaDon = apps.get_model('hoadon', 'HoaDon')
        ChiTietHoaDon = apps.get_model('hoadon', 'ChiTietHoaDon')
        
        try:
            # Tính toán các khoản phí theo cấu hình
            chi_phi_dict = {}
            tong_tien = Decimal(0)
            
            for chi_tiet_phi in cau_hinh.chi_tiet_phi.filter(CO_HIEN_THI=True).order_by('THU_TU_HIEN_THI'):
                gia_tri = chi_tiet_phi.tinh_gia_tri_phi(self)
                
                if gia_tri != 0:  # Chỉ thêm vào nếu có giá trị
                    chi_phi_dict[chi_tiet_phi.LOAI_PHI] = {
                        'ten_phi': chi_tiet_phi.TEN_PHI,
                        'gia_tri': gia_tri,
                        'don_vi': chi_tiet_phi.DON_VI
                    }
                    tong_tien += gia_tri
            
            # Mapping các loại phí vào field của HoaDon
            tien_phong = chi_phi_dict.get('tien_phong', {}).get('gia_tri', Decimal(0))
            tien_coc = chi_phi_dict.get('tien_coc', {}).get('gia_tri', Decimal(0))
            tien_dich_vu = (
                chi_phi_dict.get('phi_dich_vu', {}).get('gia_tri', Decimal(0)) +
                chi_phi_dict.get('phi_internet', {}).get('gia_tri', Decimal(0)) +
                chi_phi_dict.get('phi_nuoc', {}).get('gia_tri', Decimal(0)) +
                chi_phi_dict.get('phi_dien', {}).get('gia_tri', Decimal(0))
            )
            tien_khau_tru = (
                chi_phi_dict.get('phi_quan_ly', {}).get('gia_tri', Decimal(0)) +
                chi_phi_dict.get('phi_ve_sinh', {}).get('gia_tri', Decimal(0)) +
                chi_phi_dict.get('phi_bao_tri', {}).get('gia_tri', Decimal(0))
            )
            
            # Tạo hóa đơn - không lưu MA_PHONG cho cả hóa đơn bắt đầu và kết thúc
            hoa_don = HoaDon.objects.create(
                MA_HOP_DONG=self,
                LOAI_HOA_DON=loai_hoa_don,
                NGAY_LAP_HDON=timezone.now().date(),
                TIEN_PHONG=tien_phong,
                TIEN_DICH_VU=tien_dich_vu,
                TIEN_COC=tien_coc,
                TIEN_KHAU_TRU=tien_khau_tru,
                TONG_TIEN=tong_tien,
                TRANG_THAI_HDON='Chưa thanh toán'
            )
            
            # Lưu lịch sử cấu hình đã áp dụng
            LichSuHoaDonCauHinh.objects.create(
                MA_HOP_DONG=self,
                MA_CAU_HINH=cau_hinh,
                MA_HOA_DON=hoa_don,
                DU_LIEU_CAU_HINH={
                    'cau_hinh_id': cau_hinh.MA_CAU_HINH,
                    'ten_cau_hinh': cau_hinh.TEN_CAU_HINH,
                    'chi_phi_ap_dung': chi_phi_dict,
                    'tong_tien': float(tong_tien),
                    'ngay_ap_dung': timezone.now().isoformat()
                }
            )
            
            return hoa_don, None
            
        except Exception as e:
            return None, f"Lỗi sinh hóa đơn theo cấu hình: {str(e)}"

    def get_hoa_don_bat_dau(self):
        """Lấy hóa đơn bắt đầu hợp đồng"""
        return self.hoadon.filter(LOAI_HOA_DON='Hóa đơn bắt đầu').first()
    
    def get_hoa_don_ket_thuc(self):
        """Lấy hóa đơn kết thúc hợp đồng"""
        return self.hoadon.filter(LOAI_HOA_DON='Hóa đơn kết thúc').first()
    
    def get_lich_su_gia_han(self):
        """Lấy danh sách lịch sử gia hạn"""
        return self.lichsugiahan.all().order_by('-NGAY_GIA_HAN')
    
    def da_gia_han_bao_nhieu_lan(self):
        """Đếm số lần gia hạn"""
        return self.lichsugiahan.count()
    
    def gia_han_lan_cuoi(self):
        """Lấy thông tin gia hạn lần cuối"""
        return self.lichsugiahan.first()

    def gia_han_hop_dong(self, ngay_tra_phong_moi, thoi_han_moi=None, gia_thue_moi=None, ly_do=None):
        """Gia hạn hợp đồng"""
        
        try:
            with transaction.atomic():
                if self.TRANG_THAI_HD not in ['Đang hoạt động', 'Sắp kết thúc']:
                    raise ValueError('Chỉ có thể gia hạn hợp đồng đang hoạt động hoặc sắp kết thúc')
                
                # Kiểm tra ngày gia hạn hợp lệ
                if ngay_tra_phong_moi <= self.NGAY_TRA_PHONG:
                    raise ValueError('Ngày trả phòng mới phải sau ngày trả phòng hiện tại')
                
                # Tạo lịch sử gia hạn trước khi cập nhật
                lich_su = LichSuGiaHan.tao_lich_su_gia_han(
                    hop_dong=self,
                    ngay_tra_phong_moi=ngay_tra_phong_moi,
                    gia_thue_moi=gia_thue_moi,
                    thoi_han_moi=thoi_han_moi,
                    ly_do=ly_do
                )
                
                # Cập nhật thông tin hợp đồng
                self.NGAY_TRA_PHONG = ngay_tra_phong_moi
                
                if thoi_han_moi:
                    self.THOI_HAN_HD = thoi_han_moi
                    
                if gia_thue_moi:
                    self.GIA_THUE = gia_thue_moi
                
                # Cập nhật trạng thái về đang hoạt động
                self.TRANG_THAI_HD = 'Đang hoạt động'
                self.save()
                
                return True, lich_su
                
        except Exception as e:
            return False, str(e)

    def bao_ket_thuc_som(self, ngay_bao_ket_thuc, ly_do=None):
        """Báo kết thúc sớm hợp đồng"""
        
        try:
            with transaction.atomic():
                if self.TRANG_THAI_HD != 'Đang hoạt động':
                    raise ValueError('Chỉ có thể báo kết thúc hợp đồng đang hoạt động')
                
                # Kiểm tra ngày báo kết thúc hợp lệ
                if ngay_bao_ket_thuc <= timezone.now().date():
                    raise ValueError('Ngày báo kết thúc phải sau ngày hiện tại')
                    
                if ngay_bao_ket_thuc >= self.NGAY_TRA_PHONG:
                    raise ValueError('Ngày báo kết thúc phải trước ngày kết thúc hợp đồng')
                
                # Cập nhật trạng thái
                self.TRANG_THAI_HD = 'Đang báo kết thúc'
                
                # Cập nhật ghi chú
                if ly_do:
                    ghi_chu_moi = f"{self.GHI_CHU_HD}\n[Báo kết thúc sớm {timezone.now().date()}]: {ly_do}" if self.GHI_CHU_HD else f"[Báo kết thúc sớm {timezone.now().date()}]: {ly_do}"
                    self.GHI_CHU_HD = ghi_chu_moi
                
                self.save()
                
                return True, None
                
        except Exception as e:
            return False, str(e)

    def ket_thuc_hop_dong(self, ngay_ket_thuc_thuc_te=None):
        """Kết thúc hợp đồng và sinh hóa đơn cuối"""
        from apps.phongtro.models import CocPhong
        
        try:
            with transaction.atomic():
                if self.TRANG_THAI_HD not in ['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc']:
                    raise ValueError('Không thể kết thúc hợp đồng ở trạng thái hiện tại')
                
                # 1. Sinh hóa đơn kết thúc nếu chưa có
                if not self.get_hoa_don_ket_thuc():
                    hoa_don_ket_thuc, error = self.sinh_hoa_don_ket_thuc()
                    if not hoa_don_ket_thuc:
                        raise ValueError(f'Lỗi sinh hóa đơn kết thúc: {error}')
                
                # 2. Cập nhật trạng thái hợp đồng
                self.TRANG_THAI_HD = 'Đã kết thúc'
                
                # 3. Cập nhật ngày kết thúc thực tế nếu có
                if ngay_ket_thuc_thuc_te:
                    self.NGAY_TRA_PHONG = ngay_ket_thuc_thuc_te
                
                self.save()
                
                # 4. Cập nhật trạng thái phòng
                self.MA_PHONG.TRANG_THAI_P = 'Trống'
                self.MA_PHONG.save()
                
                # 5. Cập nhật trạng thái cọc phòng về "Chưa cọc"
                CocPhong.cap_nhat_trang_thai_coc(self.MA_PHONG, 'Chưa cọc')
                
                # 6. Cập nhật lịch sử hợp đồng - đánh dấu ngày rời đi
                for lich_su in self.lichsuhopdong.filter(NGAY_ROI_DI__isnull=True):
                    lich_su.NGAY_ROI_DI = ngay_ket_thuc_thuc_te or timezone.now().date()
                    lich_su.save()
                
                hoa_don_ket_thuc = self.get_hoa_don_ket_thuc()
                return True, hoa_don_ket_thuc
                
        except Exception as e:
            return None, str(e)

    def get_available_workflow_actions(self):
        """Lấy danh sách workflow actions có thể thực hiện dựa trên trạng thái hiện tại"""
        actions = []
        
        current_status = self.TRANG_THAI_HD or 'Chưa ký'
        
        if current_status == 'Chưa ký' or current_status == 'Chờ xác nhận':
            actions.append({
                'action': 'confirm',
                'label': 'Xác nhận Hợp đồng',
                'icon': 'fas fa-check-circle',
                'color': 'green'
            })
        
        elif current_status == 'Đang hoạt động':
            actions.extend([
                {
                    'action': 'create_invoice',
                    'label': 'Tạo Hóa đơn',
                    'icon': 'fas fa-file-invoice',
                    'color': 'blue'
                },
                {
                    'action': 'extend',
                    'label': 'Gia hạn Hợp đồng',
                    'icon': 'fas fa-calendar-plus',
                    'color': 'green'
                },
                {
                    'action': 'early_end',
                    'label': 'Báo kết thúc sớm',
                    'icon': 'fas fa-exclamation-triangle',
                    'color': 'orange'
                }
            ])
        
        elif current_status == 'Sắp hết hạn' or current_status == 'Sắp kết thúc':
            actions.extend([
                {
                    'action': 'extend',
                    'label': 'Gia hạn Hợp đồng',
                    'icon': 'fas fa-calendar-plus',
                    'color': 'green'
                },
                {
                    'action': 'end',
                    'label': 'Kết thúc Hợp đồng',
                    'icon': 'fas fa-door-open',
                    'color': 'red'
                }
            ])
        
        elif current_status == 'Đang báo kết thúc':
            actions.append({
                'action': 'end',
                'label': 'Xác nhận Kết thúc',
                'icon': 'fas fa-door-open',
                'color': 'red'
            })
        
        # Universal actions (available in most states)
        if current_status not in ['Đã kết thúc', 'Đã hủy']:
            actions.append({
                'action': 'cancel',
                'label': 'Hủy Hợp đồng',
                'icon': 'fas fa-times-circle',
                'color': 'red'
            })
        
        return actions

    def get_status_display(self):
        """Lấy thông tin hiển thị trạng thái với màu sắc"""
        status_map = {
            'Chờ xác nhận': {'text': 'Chờ xác nhận', 'color': 'bg-blue-600'},
            'Chưa ký': {'text': 'Chưa ký', 'color': 'bg-blue-600'},
            'Đang hoạt động': {'text': 'Đang hoạt động', 'color': 'bg-green-600'},
            'Sắp kết thúc': {'text': 'Sắp kết thúc', 'color': 'bg-yellow-500'},
            'Sắp hết hạn': {'text': 'Sắp hết hạn', 'color': 'bg-yellow-500'},
            'Đang báo kết thúc': {'text': 'Đang báo kết thúc', 'color': 'bg-orange-500'},
            'Đã kết thúc': {'text': 'Đã kết thúc', 'color': 'bg-red-600'},
            'Đã hủy': {'text': 'Đã hủy', 'color': 'bg-gray-600'},
        }
        
        current_status = self.TRANG_THAI_HD or 'Chưa ký'
        return status_map.get(current_status, {'text': current_status, 'color': 'bg-gray-500'})


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



# Model for lichsugiahan
class LichSuGiaHan(models.Model):
    MA_GIA_HAN = models.AutoField(primary_key=True)
    MA_HOP_DONG = models.ForeignKey(
        'HopDong',
        on_delete=models.CASCADE,
        db_column='MA_HOP_DONG',
        related_name='lichsugiahan'
    )
    NGAY_GIA_HAN = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày gia hạn"
    )
    NGAY_TRA_PHONG_MOI = models.DateField(
        verbose_name="Ngày trả phòng mới"
    )
    GIA_THUE_MOI = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Giá thuê mới"
    )
    THOI_HAN_MOI = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name="Thời hạn mới"
    )
    LY_DO_GIA_HAN = models.TextField(
        null=True, blank=True,
        verbose_name="Lý do gia hạn"
    )

    def __str__(self):
        return f"Gia hạn {self.MA_GIA_HAN} - HĐ {self.MA_HOP_DONG_id}"

    class Meta:
        db_table = 'lichsugiahan'
        ordering = ['-NGAY_GIA_HAN']

    @classmethod
    def tao_lich_su_gia_han(cls, hop_dong, ngay_tra_phong_moi, 
                           gia_thue_moi=None, thoi_han_moi=None, ly_do=None):
        """Tạo bản ghi lịch sử gia hạn"""
        return cls.objects.create(
            MA_HOP_DONG=hop_dong,
            NGAY_TRA_PHONG_MOI=ngay_tra_phong_moi,
            GIA_THUE_MOI=gia_thue_moi,
            THOI_HAN_MOI=thoi_han_moi,
            LY_DO_GIA_HAN=ly_do
        )


