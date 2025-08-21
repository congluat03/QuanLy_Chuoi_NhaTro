from django.db import models
from apps.phongtro.models import PhongTro
from apps.hopdong.models import HopDong
from apps.dichvu.models import ChiSoDichVu
from django.utils import timezone
from datetime import datetime
import uuid
from django.db import transaction
from decimal import Decimal

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
    MA_HOP_DONG = models.ForeignKey(
        'hopdong.HopDong',
        on_delete=models.CASCADE,
        db_column='MA_HOP_DONG',
        related_name='hoadon',
        null=True, blank=True
    )
    LOAI_HOA_DON = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        choices=[
            ('Hóa đơn bắt đầu', 'Hóa đơn bắt đầu hợp đồng'),
            ('Hóa đơn hàng tháng', 'Hóa đơn hàng tháng'),
            ('Hóa đơn kết thúc', 'Hóa đơn kết thúc hợp đồng'),
            ('Hóa đơn khác', 'Hóa đơn khác'),
        ]
    )
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
    @staticmethod
    def validate_required_fields(data):
        required_fields = ['MA_PHONG', 'LOAI_HOA_DON', 'NGAY_LAP_HDON', 
                         'TIEN_PHONG', 'TIEN_DICH_VU', 'TIEN_COC', 'TIEN_KHAU_TRU', 'TONG_TIEN']
        errors = []
        for field in required_fields:
            if not data.get(field):
                errors.append(f'Trường {field} là bắt buộc.')
        return errors

    @staticmethod
    def validate_phong_and_hop_dong(ma_phong):
        errors = []
        try:
            phong = PhongTro.objects.get(MA_PHONG=ma_phong)
            hop_dong = HopDong.objects.filter(
                MA_PHONG=phong,
                TRANG_THAI_HD__in=['Đang hoạt động', 'Đang báo kết thúc', 'Sắp kết thúc', 'Đã xác nhận'],
            ).first()
            if not hop_dong:
                errors.append('Phòng chưa có hợp đồng hợp lệ.')
        except PhongTro.DoesNotExist:
            errors.append('Phòng không tồn tại.')
            phong = None
        return phong, errors

    @staticmethod
    def validate_ngay_lap(ngay_lap_hdon_str):
        errors = []
        try:
            ngay_lap_hdon = datetime.strptime(ngay_lap_hdon_str, '%Y-%m-%d').date()
            if ngay_lap_hdon > timezone.now().date():
                errors.append('Ngày lập hóa đơn không được lớn hơn ngày hiện tại.')
        except ValueError:
            errors.append('Định dạng ngày lập hóa đơn không hợp lệ.')
            ngay_lap_hdon = None
        return ngay_lap_hdon, errors

    @staticmethod
    def create_hoa_don(data, phong, ngay_lap_hdon):
        return HoaDon(
            MA_PHONG=phong,
            LOAI_HOA_DON=data['LOAI_HOA_DON'],
            NGAY_LAP_HDON=ngay_lap_hdon,
            TRANG_THAI_HDON=data['TRANG_THAI_HDON'],
            TIEN_PHONG=data['TIEN_PHONG'],
            TIEN_DICH_VU=data['TIEN_DICH_VU'],
            TIEN_COC=data['TIEN_COC'],
            TIEN_KHAU_TRU=data['TIEN_KHAU_TRU'],
            TONG_TIEN=data['TONG_TIEN']
        )

    @staticmethod
    def update_hoa_don(hoa_don, data):
        hoa_don.LOAI_HOA_DON = data['LOAI_HOA_DON']
        hoa_don.NGAY_LAP_HDON = data['NGAY_LAP_HDON']
        hoa_don.TRANG_THAI_HDON = data['TRANG_THAI_HDON']
        hoa_don.TIEN_PHONG = data['TIEN_PHONG']
        hoa_don.TIEN_DICH_VU = data['TIEN_DICH_VU']
        hoa_don.TIEN_COC = data['TIEN_COC']
        hoa_don.TIEN_KHAU_TRU = data['TIEN_KHAU_TRU']
        hoa_don.TONG_TIEN = data['TONG_TIEN']
        return hoa_don

    @staticmethod
    def save_related_data(hoa_don, phong, hop_dong, ngay_lap_hdon, chi_so_dich_vu_list=None, khau_tru_list=None):
        errors = []
        if chi_so_dich_vu_list:
            chi_so_errors = ChiSoDichVu.save_chi_so_dich_vu(phong, chi_so_dich_vu_list, ngay_lap_hdon, hop_dong)
            errors.extend(chi_so_errors)
        if khau_tru_list:
            khau_tru_errors = KhauTru.save_khau_tru(hoa_don, khau_tru_list)
            errors.extend(khau_tru_errors)
        return errors

    @staticmethod
    def validate_and_create(data, chi_so_dich_vu_list=None, khau_tru_list=None):
        errors = []
        errors.extend(HoaDon.validate_required_fields(data))
        if errors:
            return None, errors
        phong = PhongTro.objects.get(MA_PHONG=data['MA_PHONG'])
        hop_dong = HopDong.objects.get(MA_HOP_DONG=data['MA_HOP_DONG'])
        if not phong:
            return None, errors
        ngay_lap_hdon = datetime.strptime(data['NGAY_LAP_HDON'], '%Y-%m-%d')
   
        if not ngay_lap_hdon:
            return None, errors
        hoa_don = HoaDon.create_hoa_don(data, phong, ngay_lap_hdon)
        hoa_don.save()
        related_errors = HoaDon.save_related_data(hoa_don, phong, hop_dong, ngay_lap_hdon, chi_so_dich_vu_list, khau_tru_list)
        errors.extend(related_errors)
        return hoa_don, errors

    @staticmethod
    def validate_and_update(hoa_don, data, chi_so_dich_vu_list=None, khau_tru_list=None):
        errors = []
        errors.extend(HoaDon.validate_required_fields(data))

        hoa_don_save = HoaDon.update_hoa_don(hoa_don, data)
        hoa_don_save.save()

        for chi_so_dich_vu_data in chi_so_dich_vu_list:
            try:

                ma_chi_so = chi_so_dich_vu_data.get('MA_CHI_SO', '')
                chi_so_dv = ChiSoDichVu.objects.filter(MA_CHI_SO=ma_chi_so).first()
                
                chi_so_dich_vu = ChiSoDichVu.update_chi_so_dich_vu(chi_so_dv, chi_so_dich_vu_data, hoa_don_save.NGAY_LAP_HDON)
                chi_so_dich_vu.save()
            except Exception as e:
                errors.append(f"Lỗi khi lưu chỉ số dịch vụ MACHISO={chi_so_dich_vu_data.get('MA_CHI_SO', '')}: {str(e)}")

        HoaDon.update_khau_tru(hoa_don, khau_tru_list)
        return hoa_don_save, errors
    @staticmethod
    def update_khau_tru(hoa_don, khau_tru_list):
        errors = []
        existing_khau_tru = KhauTru.objects.filter(MA_HOA_DON=hoa_don).values_list('MA_KHAU_TRU', flat=True)
        for khau_tru_data in khau_tru_list:
            try:
                ma_khau_tru = khau_tru_data.get('MA_KHAU_TRU', '')
                ngay_khau_tru = khau_tru_data.get('NGAYKHAUTRU', '')
                # Cập nhật hoặc thêm mới
                if ma_khau_tru != '':
                    # Cập nhật bản ghi hiện có
                    khau_tru = KhauTru.update_khau_tru(ma_khau_tru, khau_tru_data, ngay_khau_tru)
                else:
                    # Thêm mới bản ghi
                    khau_tru = KhauTru.create_khau_tru(hoa_don, khau_tru_data, ngay_khau_tru)
                    khau_tru.save()  # MA_KHAU_TRU sẽ tự động tạo nếu là AutoField hoặc UUID
                    
            except Exception as e:
                errors.append(f"Lỗi khi lưu khấu trừ MA_KHAU_TRU={ma_khau_tru}: {str(e)}")
    @staticmethod
    def delete_hoa_don(hoa_don):
        try:
            ChiSoDichVu.objects.filter(MA_HOA_DON=hoa_don).delete()
            KhauTru.objects.filter(MA_HOA_DON=hoa_don).delete()
            hoa_don.delete()
            return True, []
        except Exception as e:
            return False, [f'Lỗi khi xóa hóa đơn: {str(e)}']

    @classmethod
    def sinh_hoa_don_bat_dau_hop_dong(cls, hop_dong):
        """
        Sinh hóa đơn bắt đầu hợp đồng
        Bao gồm: Tiền phòng tháng đầu + Tiền dịch vụ + Tiền cọc
        """
        try:
            with transaction.atomic():
                # 1. Kiểm tra đã có hóa đơn bắt đầu chưa
                if cls.objects.filter(
                    MA_HOP_DONG=hop_dong,
                    LOAI_HOA_DON='Bắt đầu hợp đồng'
                ).exists():
                    raise ValueError('Hợp đồng đã có hóa đơn bắt đầu')
                
                # 2. Tính tiền phòng (theo hợp đồng)
                tien_phong = Decimal(hop_dong.GIA_THUE or 0)
                
                # 3. Tính tiền dịch vụ tháng đầu
                tien_dich_vu = cls._tinh_tien_dich_vu_thang_dau(hop_dong)
                
                # 4. Tiền cọc (nếu có)
                tien_coc = Decimal(hop_dong.GIA_COC_HD or 0)
                
                # 5. Tổng tiền
                tong_tien = tien_phong + tien_dich_vu + tien_coc
                
                # 6. Tạo hóa đơn
                hoa_don = cls.objects.create(
                    MA_PHONG=hop_dong.MA_PHONG,
                    MA_HOP_DONG=hop_dong,
                    LOAI_HOA_DON='Bắt đầu hợp đồng',
                    NGAY_LAP_HDON=hop_dong.NGAY_NHAN_PHONG or timezone.now().date(),
                    TIEN_PHONG=tien_phong,
                    TIEN_DICH_VU=tien_dich_vu,
                    TIEN_COC=tien_coc,
                    TIEN_KHAU_TRU=Decimal(0),
                    TONG_TIEN=tong_tien,
                    TRANG_THAI_HDON='Chưa thanh toán'
                )
                
                # 7. Tạo chi tiết hóa đơn
                cls._tao_chi_tiet_hoa_don_bat_dau(hoa_don, hop_dong)
                
                return hoa_don, None
                
        except Exception as e:
            return None, str(e)

    @classmethod  
    def _tinh_tien_dich_vu_thang_dau(cls, hop_dong):
        """Tính tiền dịch vụ tháng đầu của hợp đồng"""
        from apps.dichvu.models import ChiSoDichVu, LichSuApDungDichVu
        
        try:
            tong_tien_dv = Decimal(0)
            
            # Lấy danh sách dịch vụ áp dụng cho khu vực
            dich_vu_ap_dung = LichSuApDungDichVu.objects.filter(
                MA_KHU_VUC=hop_dong.MA_PHONG.MA_KHU_VUC,
                NGAY_HUY_DV__isnull=True
            ).select_related('MA_DICH_VU')
            
            for dv_ap_dung in dich_vu_ap_dung:
                dich_vu = dv_ap_dung.MA_DICH_VU
                gia_ap_dung = dv_ap_dung.GIA_DICH_VU_AD or dich_vu.GIA_DICH_VU or Decimal(0)
                
                if dich_vu.LOAI_DICH_VU == 'Cố định':
                    # Dịch vụ cố định: wifi, rác, bảo vệ...
                    tong_tien_dv += gia_ap_dung
                    
                else:
                    # Dịch vụ theo chỉ số: điện, nước
                    # Lấy chỉ số đầu từ ChiSoDichVu (nếu có)
                    chi_so_dv = ChiSoDichVu.objects.filter(
                        MA_HOP_DONG=hop_dong,
                        MA_DICH_VU=dich_vu
                    ).first()
                    
                    if chi_so_dv and chi_so_dv.CHI_SO_MOI:
                        # Có chỉ số ban đầu
                        so_luong = chi_so_dv.CHI_SO_MOI - (chi_so_dv.CHI_SO_CU or 0)
                        tong_tien_dv += gia_ap_dung * Decimal(so_luong)
                    else:
                        # Chưa có chỉ số, tạm tính = 0 (sẽ cập nhật sau)
                        tong_tien_dv += Decimal(0)
            
            return tong_tien_dv
            
        except Exception as e:
            print(f"Lỗi tính tiền dịch vụ: {e}")
            return Decimal(0)

    @classmethod
    def _tao_chi_tiet_hoa_don_bat_dau(cls, hoa_don, hop_dong):
        """Tạo chi tiết hóa đơn bắt đầu"""
        # 1. Chi tiết tiền phòng
        if hoa_don.TIEN_PHONG > 0:
            CHITIETHOADON.objects.create(
                MA_HOA_DON=hoa_don,
                LOAI_KHOAN='PHONG',
                NOI_DUNG=f'Tiền phòng tháng đầu - {hoa_don.MA_PHONG.TEN_PHONG}',
                SO_LUONG=1,
                DON_GIA=hoa_don.TIEN_PHONG,
                THANH_TIEN=hoa_don.TIEN_PHONG,
                GHI_CHU_CTHD=f'Từ {hop_dong.NGAY_NHAN_PHONG} đến {hop_dong.NGAY_TRA_PHONG}'
            )
        
        # 2. Chi tiết tiền cọc
        if hoa_don.TIEN_COC > 0:
            CHITIETHOADON.objects.create(
                MA_HOA_DON=hoa_don,
                LOAI_KHOAN='COC',
                NOI_DUNG='Tiền cọc hợp đồng',
                SO_LUONG=1,
                DON_GIA=hoa_don.TIEN_COC,
                THANH_TIEN=hoa_don.TIEN_COC,
                GHI_CHU_CTHD='Tiền cọc sẽ hoàn trả khi kết thúc hợp đồng'
            )
        
        # 3. Chi tiết dịch vụ (nếu có)
        if hoa_don.TIEN_DICH_VU > 0:
            CHITIETHOADON.objects.create(
                MA_HOA_DON=hoa_don,
                LOAI_KHOAN='DICH_VU',
                NOI_DUNG='Dịch vụ tháng đầu',
                SO_LUONG=1,
                DON_GIA=hoa_don.TIEN_DICH_VU,
                THANH_TIEN=hoa_don.TIEN_DICH_VU,
                GHI_CHU_CTHD='Chi tiết dịch vụ xem phụ lục'
            )

    @classmethod
    def sinh_hoa_don_ket_thuc_hop_dong(cls, hop_dong, ngay_ket_thuc):
        """
        Sinh hóa đơn kết thúc hợp đồng
        Bao gồm: Tiền phòng (nếu có), Tiền dịch vụ cuối, Hoàn trả cọc
        """
        try:
            with transaction.atomic():
                # 1. Kiểm tra đã có hóa đơn kết thúc chưa
                if cls.objects.filter(
                    MA_HOP_DONG=hop_dong,
                    LOAI_HOA_DON='Kết thúc hợp đồng'
                ).exists():
                    raise ValueError('Hợp đồng đã có hóa đơn kết thúc')
                
                # 2. Tính tiền phòng (nếu chưa đủ tháng)
                tien_phong = cls._tinh_tien_phong_cuoi_ky(hop_dong, ngay_ket_thuc)
                
                # 3. Tính tiền dịch vụ cuối kỳ
                tien_dich_vu = cls._tinh_tien_dich_vu_cuoi_ky(hop_dong, ngay_ket_thuc)
                
                # 4. Tiền hoàn cọc (âm = hoàn trả)
                tien_hoan_coc = -Decimal(hop_dong.GIA_COC_HD or 0)
                
                # 5. Tổng tiền (có thể âm nếu hoàn cọc nhiều hơn phí)
                tong_tien = tien_phong + tien_dich_vu + tien_hoan_coc
                
                # 6. Tạo hóa đơn
                hoa_don = cls.objects.create(
                    MA_PHONG=hop_dong.MA_PHONG,
                    MA_HOP_DONG=hop_dong,
                    LOAI_HOA_DON='Kết thúc hợp đồng',
                    NGAY_LAP_HDON=ngay_ket_thuc,
                    TIEN_PHONG=tien_phong,
                    TIEN_DICH_VU=tien_dich_vu,
                    TIEN_COC=tien_hoan_coc,
                    TIEN_KHAU_TRU=Decimal(0),
                    TONG_TIEN=tong_tien,
                    TRANG_THAI_HDON='Chưa thanh toán' if tong_tien > 0 else 'Chờ hoàn trả'
                )
                
                # 7. Tạo chi tiết hóa đơn
                cls._tao_chi_tiet_hoa_don_ket_thuc(hoa_don, hop_dong, ngay_ket_thuc)
                
                return hoa_don, None
                
        except Exception as e:
            return None, str(e)

    @classmethod  
    def _tinh_tien_phong_cuoi_ky(cls, hop_dong, ngay_ket_thuc):
        """Tính tiền phòng cuối kỳ (nếu kết thúc giữa tháng)"""
        from datetime import datetime
        from calendar import monthrange
        
        try:
            # Lấy ngày thu tiền gần nhất
            ngay_thu_tien = int(hop_dong.NGAY_THU_TIEN or 1)
            
            # Tính chu kỳ thanh toán cuối
            if ngay_ket_thuc.day <= ngay_thu_tien:
                # Kết thúc trước ngày thu tiền = không tính tiền tháng này
                return Decimal(0)
            else:
                # Kết thúc sau ngày thu tiền = tính tiền theo tỷ lệ
                ngay_dau_thang = ngay_ket_thuc.replace(day=ngay_thu_tien)
                so_ngay_thang = monthrange(ngay_ket_thuc.year, ngay_ket_thuc.month)[1]
                so_ngay_su_dung = (ngay_ket_thuc - ngay_dau_thang).days + 1
                
                ty_le = so_ngay_su_dung / so_ngay_thang
                return Decimal(hop_dong.GIA_THUE or 0) * Decimal(ty_le)
                
        except Exception as e:
            print(f"Lỗi tính tiền phòng cuối kỳ: {e}")
            return Decimal(0)

    @classmethod
    def _tinh_tien_dich_vu_cuoi_ky(cls, hop_dong, ngay_ket_thuc):
        """Tính tiền dịch vụ cuối kỳ"""
        from apps.dichvu.models import ChiSoDichVu, LichSuApDungDichVu
        
        try:
            tong_tien_dv = Decimal(0)
            
            # Lấy danh sách dịch vụ áp dụng cho khu vực
            dich_vu_ap_dung = LichSuApDungDichVu.objects.filter(
                MA_KHU_VUC=hop_dong.MA_PHONG.MA_KHU_VUC,
                NGAY_HUY_DV__isnull=True
            ).select_related('MA_DICH_VU')
            
            for dv_ap_dung in dich_vu_ap_dung:
                dich_vu = dv_ap_dung.MA_DICH_VU
                gia_ap_dung = dv_ap_dung.GIA_DICH_VU_AD or dich_vu.GIA_DICH_VU or Decimal(0)
                
                if dich_vu.LOAI_DICH_VU == 'Cố định':
                    # Dịch vụ cố định: tính theo tỷ lệ ngày
                    from calendar import monthrange
                    so_ngay_thang = monthrange(ngay_ket_thuc.year, ngay_ket_thuc.month)[1]
                    ty_le = ngay_ket_thuc.day / so_ngay_thang
                    tong_tien_dv += gia_ap_dung * Decimal(ty_le)
                    
                else:
                    # Dịch vụ theo chỉ số: lấy chỉ số cuối cùng
                    chi_so_cuoi = ChiSoDichVu.objects.filter(
                        MA_HOP_DONG=hop_dong,
                        MA_DICH_VU=dich_vu
                    ).order_by('-NGAY_GHI_CS').first()
                    
                    if chi_so_cuoi and chi_so_cuoi.CHI_SO_MOI:
                        # Có chỉ số cuối
                        so_luong = chi_so_cuoi.CHI_SO_MOI - (chi_so_cuoi.CHI_SO_CU or 0)
                        tong_tien_dv += gia_ap_dung * Decimal(so_luong)
            
            return tong_tien_dv
            
        except Exception as e:
            print(f"Lỗi tính tiền dịch vụ cuối kỳ: {e}")
            return Decimal(0)

    @classmethod
    def _tao_chi_tiet_hoa_don_ket_thuc(cls, hoa_don, hop_dong, ngay_ket_thuc):
        """Tạo chi tiết hóa đơn kết thúc"""
        # 1. Chi tiết tiền phòng (nếu có)
        if hoa_don.TIEN_PHONG > 0:
            CHITIETHOADON.objects.create(
                MA_HOA_DON=hoa_don,
                LOAI_KHOAN='PHONG',
                NOI_DUNG=f'Tiền phòng cuối kỳ - {hoa_don.MA_PHONG.TEN_PHONG}',
                SO_LUONG=1,
                DON_GIA=hoa_don.TIEN_PHONG,
                THANH_TIEN=hoa_don.TIEN_PHONG,
                GHI_CHU_CTHD=f'Tính từ ngày thu tiền đến {ngay_ket_thuc}'
            )
        
        # 2. Chi tiết hoàn cọc
        if hoa_don.TIEN_COC < 0:
            CHITIETHOADON.objects.create(
                MA_HOA_DON=hoa_don,
                LOAI_KHOAN='HOAN_COC',
                NOI_DUNG='Hoàn trả tiền cọc hợp đồng',
                SO_LUONG=1,
                DON_GIA=hoa_don.TIEN_COC,
                THANH_TIEN=hoa_don.TIEN_COC,
                GHI_CHU_CTHD='Hoàn trả tiền cọc khi kết thúc hợp đồng'
            )
        
        # 3. Chi tiết dịch vụ cuối kỳ (nếu có)
        if hoa_don.TIEN_DICH_VU > 0:
            CHITIETHOADON.objects.create(
                MA_HOA_DON=hoa_don,
                LOAI_KHOAN='DICH_VU',
                NOI_DUNG='Dịch vụ cuối kỳ',
                SO_LUONG=1,
                DON_GIA=hoa_don.TIEN_DICH_VU,
                THANH_TIEN=hoa_don.TIEN_DICH_VU,
                GHI_CHU_CTHD='Chi tiết dịch vụ cuối kỳ xem phụ lục'
            )

    @classmethod
    def sinh_hoa_don_hang_thang(cls, hop_dong, thang, nam):
        """
        Sinh hóa đơn hàng tháng
        Bao gồm: Tiền phòng + Tiền dịch vụ
        """
        try:
            with transaction.atomic():
                # 1. Kiểm tra đã có hóa đơn tháng này chưa
                if cls.objects.filter(
                    MA_HOP_DONG=hop_dong,
                    LOAI_HOA_DON='Hàng tháng',
                    NGAY_LAP_HDON__year=nam,
                    NGAY_LAP_HDON__month=thang
                ).exists():
                    raise ValueError(f'Đã có hóa đơn tháng {thang}/{nam}')
                
                # 2. Tính tiền phòng
                tien_phong = Decimal(hop_dong.GIA_THUE or 0)
                
                # 3. Tính tiền dịch vụ tháng
                tien_dich_vu = cls._tinh_tien_dich_vu_thang(hop_dong, thang, nam)
                
                # 4. Tổng tiền
                tong_tien = tien_phong + tien_dich_vu
                
                # 5. Ngày lập hóa đơn (ngày thu tiền)
                from datetime import date
                ngay_thu = int(hop_dong.NGAY_THU_TIEN or 1)
                ngay_lap = date(nam, thang, min(ngay_thu, 28))  # Tránh lỗi ngày 31
                
                # 6. Tạo hóa đơn
                hoa_don = cls.objects.create(
                    MA_PHONG=hop_dong.MA_PHONG,
                    MA_HOP_DONG=hop_dong,
                    LOAI_HOA_DON='Hàng tháng',
                    NGAY_LAP_HDON=ngay_lap,
                    TIEN_PHONG=tien_phong,
                    TIEN_DICH_VU=tien_dich_vu,
                    TIEN_COC=Decimal(0),
                    TIEN_KHAU_TRU=Decimal(0),
                    TONG_TIEN=tong_tien,
                    TRANG_THAI_HDON='Chưa thanh toán'
                )
                
                # 7. Tạo chi tiết hóa đơn
                cls._tao_chi_tiet_hoa_don_hang_thang(hoa_don, hop_dong, thang, nam)
                
                return hoa_don, None
                
        except Exception as e:
            return None, str(e)

    @classmethod
    def _tinh_tien_dich_vu_thang(cls, hop_dong, thang, nam):
        """Tính tiền dịch vụ của tháng cụ thể"""
        from apps.dichvu.models import ChiSoDichVu, LichSuApDungDichVu
        
        try:
            tong_tien_dv = Decimal(0)
            
            # Lấy danh sách dịch vụ áp dụng cho khu vực
            dich_vu_ap_dung = LichSuApDungDichVu.objects.filter(
                MA_KHU_VUC=hop_dong.MA_PHONG.MA_KHU_VUC,
                NGAY_HUY_DV__isnull=True
            ).select_related('MA_DICH_VU')
            
            for dv_ap_dung in dich_vu_ap_dung:
                dich_vu = dv_ap_dung.MA_DICH_VU
                gia_ap_dung = dv_ap_dung.GIA_DICH_VU_AD or dich_vu.GIA_DICH_VU or Decimal(0)
                
                if dich_vu.LOAI_DICH_VU == 'Cố định':
                    # Dịch vụ cố định: wifi, rác, bảo vệ...
                    tong_tien_dv += gia_ap_dung
                    
                else:
                    # Dịch vụ theo chỉ số: lấy chỉ số của tháng
                    chi_so_thang = ChiSoDichVu.objects.filter(
                        MA_HOP_DONG=hop_dong,
                        MA_DICH_VU=dich_vu,
                        NGAY_GHI_CS__year=nam,
                        NGAY_GHI_CS__month=thang
                    ).first()
                    
                    if chi_so_thang and chi_so_thang.CHI_SO_MOI:
                        so_luong = chi_so_thang.CHI_SO_MOI - (chi_so_thang.CHI_SO_CU or 0)
                        tong_tien_dv += gia_ap_dung * Decimal(so_luong)
            
            return tong_tien_dv
            
        except Exception as e:
            print(f"Lỗi tính tiền dịch vụ tháng {thang}/{nam}: {e}")
            return Decimal(0)

    @classmethod
    def _tao_chi_tiet_hoa_don_hang_thang(cls, hoa_don, hop_dong, thang, nam):
        """Tạo chi tiết hóa đơn hàng tháng"""
        # 1. Chi tiết tiền phòng
        if hoa_don.TIEN_PHONG > 0:
            CHITIETHOADON.objects.create(
                MA_HOA_DON=hoa_don,
                LOAI_KHOAN='PHONG',
                NOI_DUNG=f'Tiền phòng tháng {thang}/{nam} - {hoa_don.MA_PHONG.TEN_PHONG}',
                SO_LUONG=1,
                DON_GIA=hoa_don.TIEN_PHONG,
                THANH_TIEN=hoa_don.TIEN_PHONG,
                GHI_CHU_CTHD=f'Tiền phòng tháng {thang}/{nam}'
            )
        
        # 2. Chi tiết dịch vụ
        if hoa_don.TIEN_DICH_VU > 0:
            CHITIETHOADON.objects.create(
                MA_HOA_DON=hoa_don,
                LOAI_KHOAN='DICH_VU',
                NOI_DUNG=f'Dịch vụ tháng {thang}/{nam}',
                SO_LUONG=1,
                DON_GIA=hoa_don.TIEN_DICH_VU,
                THANH_TIEN=hoa_don.TIEN_DICH_VU,
                GHI_CHU_CTHD=f'Chi tiết dịch vụ tháng {thang}/{nam} xem phụ lục'
            )


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
    @staticmethod
    def validate_khau_tru_data(khau_tru, index):
        errors = []
        loai_kt = khau_tru.get('LOAI_KHAU_TRU')
        ly_do_kt = khau_tru.get('LY_DO_KHAU_TRU')

        if not loai_kt:
            errors.append(f'Khấu trừ thứ {index+1}: Thiếu loại khấu trừ.')
        if not ly_do_kt:
            errors.append(f'Khấu trừ thứ {index+1}: Thiếu lý do khấu trừ.')

        try:
            so_tien_kt = float(khau_tru.get('SO_TIEN_KT', 0))
            if so_tien_kt < 0:
                errors.append(f'Khấu trừ thứ {index+1}: Số tiền khấu trừ không được âm.')
        except (ValueError, TypeError):
            errors.append(f'Khấu trừ thứ {index+1}: Số tiền khấu trừ không hợp lệ.')
            so_tien_kt = None

        if errors:
            return None, errors

        return {
            'LOAI_KHAU_TRU': loai_kt,
            'SO_TIEN_KT': so_tien_kt,
            'LY_DO_KHAU_TRU': ly_do_kt
        }, errors

    @staticmethod
    def validate_ngay_khau_tru(ngay_khau_tru, index):
       
        errors = []
        ngay_kt = None

        if not ngay_khau_tru:
            errors.append(f'Ngày khấu trừ thứ {index + 1} không được để trống.')
            return ngay_kt, errors

        try:
            if isinstance(ngay_khau_tru, str):
                ngay_kt = datetime.strptime(ngay_khau_tru, '%Y-%m-%d')
            elif isinstance(ngay_khau_tru, datetime.date):
                ngay_kt = datetime.combine(ngay_khau_tru, datetime.min.time())
            else:
                errors.append(f'Ngày khấu trừ thứ {index + 1} có kiểu dữ liệu không hợp lệ.')
                return ngay_kt, errors

            # Nếu model KhauTru chỉ cần datetime.date, không cần thiết lập giờ/phút/giây
            # ngay_kt = ngay_kt.replace(hour=0, minute=0, second=0, microsecond=0)
            # Chuyển về datetime.date nếu model yêu cầu
            ngay_kt = ngay_kt.date()

        except ValueError:
            errors.append(f'Ngày khấu trừ thứ {index + 1} không hợp lệ (định dạng YYYY-MM-DD).')

        return ngay_kt, errors
    @staticmethod
    def create_khau_tru(hoa_don, khau_tru_data, ngay_kt):
        return KhauTru(
            MA_HOA_DON=hoa_don,
            LOAI_KHAU_TRU=khau_tru_data['LOAI_KHAU_TRU'],
            SO_TIEN_KT=khau_tru_data['SO_TIEN_KT'],
            LY_DO_KHAU_TRU=khau_tru_data['LY_DO_KHAU_TRU'],
            NGAYKHAUTRU=ngay_kt
        )
    @staticmethod
    def update_khau_tru(khau_tru_id, khau_tru_data, ngay_kt):
        try:
            khau_tru = KhauTru.objects.get(pk=khau_tru_id)
            khau_tru.LOAI_KHAU_TRU = khau_tru_data['LOAI_KHAU_TRU']
            khau_tru.SO_TIEN_KT = khau_tru_data['SO_TIEN_KT']
            khau_tru.LY_DO_KHAU_TRU = khau_tru_data['LY_DO_KHAU_TRU']
            khau_tru.NGAYKHAUTRU = ngay_kt
            khau_tru.save()
            return khau_tru
        except KhauTru.DoesNotExist:
            return None
    @staticmethod
    def save_khau_tru(hoa_don, khau_tru_list):
        errors = []
        for kt in khau_tru_list:
            # Xác thực dữ liệu khấu trừ
            khau_tru_data, data_errors = KhauTru.validate_khau_tru_data(kt, index=0)
            errors.extend(data_errors)
            if not khau_tru_data:
                continue

            # Xác thực ngày khấu trừ
            ngay_kt, ngay_errors = KhauTru.validate_ngay_khau_tru(kt.get('NGAYKHAUTRU'), index=0)
            errors.extend(ngay_errors)
            if not ngay_kt:
                continue

            # Tạo và lưu khấu trừ
            khau_tru = KhauTru.create_khau_tru(hoa_don, khau_tru_data, ngay_kt)
            khau_tru.save()
        
        return errors
class PHIEUTHU(models.Model):
    MA_PHIEU_THU = models.IntegerField(primary_key=True)
    MA_HOA_DON = models.ForeignKey(
        'HoaDon',
        on_delete=models.CASCADE,
        db_column='MA_HOA_DON',
        related_name='phieuthu'
    )
    MA_KHACH = models.ForeignKey(
        'khachthue.KhachThue',
        on_delete=models.CASCADE,
        db_column='MA_KHACH_THUE',
        related_name='phieuthu'
    )
    NGAY_THU = models.DateField()
    SO_TIEN = models.DecimalField(max_digits=12, decimal_places=2)
    HINH_THUC = models.CharField(max_length=50, null=True, blank=True)
    GHI_CHU = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'phieu_thu'

class CHITIETHOADON(models.Model):
    MA_CHI_TIET = models.IntegerField(primary_key=True)
    MA_HOA_DON = models.ForeignKey(
        'HoaDon',
        on_delete=models.CASCADE,
        db_column='MA_HOA_DON',
        related_name='chitiethoadon'
    )
    LOAI_KHOAN = models.CharField(
        max_length=10,
        choices=[
            ('PHONG', 'PHONG'),
            ('DICH_VU', 'DICH_VU'),
            ('KHAU_TRU', 'KHAU_TRU'),
            ('COC', 'COC'),
            ('HOAN_COC', 'HOAN_COC')
        ],
        null=True, blank=True
    )
    NOI_DUNG = models.CharField(max_length=200, null=True, blank=True)
    SO_LUONG = models.IntegerField(null=True, blank=True)
    DON_GIA = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    THANH_TIEN = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    GHI_CHU_CTHD = models.TextField()

    class Meta:
        db_table = 'chitiethoadon'
