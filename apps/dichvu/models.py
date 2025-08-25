from django.db import models
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Create your models here.
# Model for dichvu
class DichVu(models.Model):
    MA_DICH_VU = models.AutoField(primary_key=True)
    TEN_DICH_VU = models.CharField(max_length=200, null=True, blank=True)
    DON_VI_TINH = models.CharField(max_length=50, null=True, blank=True)
    LOAI_DICH_VU = models.CharField(max_length=50, null=True, blank=True)
    GIA_DICH_VU = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.TEN_DICH_VU or f"Dịch vụ {self.MA_DICH_VU}"
    @property
    def is_applied(self):
        return self.lichsu_dichvu.filter(NGAY_HUY_DV__isnull=True).exists()
    class Meta:
        db_table = 'dichvu'

# Model for lichsuapdungdichvu
class LichSuApDungDichVu(models.Model):
    MA_AP_DUNG_DV = models.AutoField(primary_key=True)
    MA_KHU_VUC = models.ForeignKey(
        'nhatro.KhuVuc',
        on_delete=models.CASCADE,
        db_column='MA_KHU_VUC',
        related_name='lichsu_dichvu'
    )
    MA_DICH_VU = models.ForeignKey(
        'DichVu',
        on_delete=models.CASCADE,
        db_column='MA_DICH_VU',
        related_name='lichsu_dichvu'
    )
    NGAY_AP_DUNG_DV = models.DateField(null=True, blank=True)
    NGAY_HUY_DV = models.DateField(null=True, blank=True)
    GIA_DICH_VU_AD = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    LOAI_DICH_VU_AD = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Áp dụng dịch vụ {self.MA_AP_DUNG_DV}"

    class Meta:
        db_table = 'lichsuapdungdichvu'
    @staticmethod
    def get_dich_vu_ap_dung(khu_vuc):
        try:
            return LichSuApDungDichVu.objects.filter(
                MA_KHU_VUC=khu_vuc,
                NGAY_HUY_DV__isnull=True
            ).select_related('MA_DICH_VU'), []
        except Exception as e:
            return None, [f'Lỗi khi lấy dịch vụ áp dụng: {str(e)}']
    
# Model for chisodichvu
class ChiSoDichVu(models.Model):
    MA_CHI_SO = models.AutoField(primary_key=True)
    MA_DICH_VU = models.ForeignKey(
        'DichVu',
        on_delete=models.CASCADE,
        db_column='MA_DICH_VU',
        related_name='chisodichvu'
    )
    MA_HOP_DONG = models.ForeignKey(
        'hopdong.HopDong',
        on_delete=models.CASCADE,
        db_column='MA_HOP_DONG',
        related_name='chisodichvu'
    )
    CHI_SO_CU = models.IntegerField(null=True, blank=True)
    CHI_SO_MOI = models.IntegerField(null=True, blank=True)
    NGAY_GHI_CS = models.DateField(null=True, blank=True)
    SO_LUONG = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return f"Chỉ số dịch vụ {self.MA_CHI_SO} - HĐ {self.MA_HOP_DONG_id}"

    class Meta:
        db_table = 'chisodichvu'
    @staticmethod
    def get_applied_services(khu_vuc):
        return LichSuApDungDichVu.objects.filter(
            MA_KHU_VUC=khu_vuc,
        ).select_related('MA_DICH_VU')

    @staticmethod
    def validate_chi_so_data(chi_so, index):
        errors = []
        try:
            chi_so_cu = float(chi_so.get('CHI_SO_CU', 0)) if chi_so.get('CHI_SO_CU') else 0.0
            chi_so_moi = float(chi_so.get('CHI_SO_MOI', 0)) if chi_so.get('CHI_SO_MOI') else None
            so_dich_vu = float(chi_so.get('SO_DICH_VU', 0)) if chi_so.get('SO_DICH_VU') else 0.0
            thanh_tien = float(chi_so.get('THANH_TIEN', 0))

            if chi_so_moi is not None and chi_so_cu is not None and chi_so_moi < chi_so_cu:
                errors.append(f'Dịch vụ thứ {index+1}: Chỉ số mới phải lớn hơn hoặc bằng chỉ số cũ.')
            if thanh_tien < 0:
                errors.append(f'Dịch vụ thứ {index+1}: Thành tiền không được âm.')

            return {
                'CHI_SO_CU': chi_so_cu,
                'CHI_SO_MOI': chi_so_moi,
                'SO_DICH_VU': so_dich_vu,
                'THANH_TIEN': thanh_tien
            }, errors
        except (ValueError, TypeError) as e:
            errors.append(f'Lỗi dữ liệu dịch vụ thứ {index+1}: {str(e)}')
            return None, errors

    @staticmethod
    def create_chi_so_dich_vu(dich_vu, chi_so_data, ngay_ghi_cs, hop_dong):
        return ChiSoDichVu(
            MA_HOP_DONG=hop_dong,
            MA_DICH_VU=dich_vu,
            CHI_SO_CU=int(chi_so_data['CHI_SO_CU']),
            CHI_SO_MOI=int(chi_so_data['CHI_SO_MOI']),
            NGAY_GHI_CS=ngay_ghi_cs
        )
    @classmethod
    def tao_danh_sach_chi_so(cls, hop_dong, ds_dich_vu: list):
        danh_sach = []
        for item in ds_dich_vu:
            if not item.get('MA_DICH_VU'):
                continue
            chisodv = cls(
                MA_DICH_VU_id=item['MA_DICH_VU'],
                MA_HOP_DONG=hop_dong,
                CHI_SO_CU=None,  # Có thể tính nếu cần
                CHI_SO_MOI=item.get('CHI_SO_MOI') or None,
                SO_LUONG = item.get('SO_LUONG') or 0,
                NGAY_GHI_CS=hop_dong.NGAY_LAP_HD or datetime.now().date()
            )
            danh_sach.append(chisodv)
        cls.objects.bulk_create(danh_sach)
    @staticmethod
    def update_chi_so_dich_vu(chi_so_dv, chi_so_data, ngay_ghi_cs):
        chi_so_dv.CHI_SO_MOI = int(float(chi_so_data['CHI_SO_MOI']))
        chi_so_dv.NGAY_GHI_CS = ngay_ghi_cs
        return chi_so_dv
    @staticmethod
    def save_chi_so_dich_vu(chi_so_dich_vu_list, ngay_ghi_cs, hop_dong):
        errors = []
        for chi_so in chi_so_dich_vu_list:
            ma_dich_vu = int(chi_so.get('MA_DICH_VU'))
            ma_chi_so = chi_so.get('MA_CHI_SO')
            dich_vu = DichVu.objects.filter(MA_DICH_VU=ma_dich_vu).first()

            # Kiểm tra MA_DICH_VU
            if not ma_dich_vu:
                errors.append(f'Dịch vụ với MA_DICH_VU={ma_dich_vu} không hợp lệ.')
                continue

            # Xác thực dữ liệu
            chi_so_data, chi_so_errors = ChiSoDichVu.validate_chi_so_data(chi_so, index=0)
            errors.extend(chi_so_errors)
            if not chi_so_data:
                continue
            

            # Kiểm tra bản ghi hiện có
            if ma_chi_so:
                chi_so_hien_co = ChiSoDichVu.objects.filter(MA_CHI_SO=ma_chi_so).first()
                if chi_so_hien_co:
                    # Cập nhật bản ghi hiện có
                    chi_so_dv = ChiSoDichVu.update_chi_so_dich_vu(chi_so_hien_co, chi_so_data, ngay_ghi_cs)
                    chi_so_dv.save()
                else:
                    errors.append(f'Bản ghi với MA_CHI_SO={ma_chi_so} không tồn tại.')
                    continue
            else:
                # Tạo bản ghi mới
                chi_so_dv = ChiSoDichVu.create_chi_so_dich_vu(dich_vu, chi_so_data, ngay_ghi_cs, hop_dong)
                chi_so_dv.save()

        return errors

    @staticmethod
    def get_chi_so_moi_nhat(ma_dich_vu, hop_dong, current_month, next_month):
        try:
            return ChiSoDichVu.objects.filter(
                MA_DICH_VU=ma_dich_vu,
                MA_HOP_DONG=hop_dong,
                NGAY_GHI_CS__gte=current_month,
                NGAY_GHI_CS__lt=next_month
            ).order_by('-NGAY_GHI_CS').first()
        except Exception:
            return None

    @staticmethod
    def get_chi_so_truoc(ma_dich_vu, hop_dong, current_month):
        try:
            return ChiSoDichVu.objects.filter(
                MA_DICH_VU=ma_dich_vu,
                MA_HOP_DONG=hop_dong,
                NGAY_GHI_CS__lt=current_month
            ).order_by('-NGAY_GHI_CS').first()
        except Exception:
            return None

    @staticmethod
    def parse_chu_ky_thanh_toan(chu_ky_str):
        """
        Parse chu kỳ thanh toán từ string thành số tháng
        VD: "1 tháng" -> 1, "3 tháng" -> 3, "6 tháng" -> 6
        """
        if not chu_ky_str:
            return 1  # Mặc định 1 tháng
            
        chu_ky_str = chu_ky_str.lower().strip()
        
        # Tách số từ chuỗi
        import re
        numbers = re.findall(r'\d+', chu_ky_str)
        if numbers:
            return int(numbers[0])
        
        # Fallback cho các trường hợp đặc biệt
        if 'quý' in chu_ky_str or 'quy' in chu_ky_str:
            return 3
        elif 'năm' in chu_ky_str or 'nam' in chu_ky_str:
            return 12
        
        return 1  # Mặc định 1 tháng

    @staticmethod
    def parse_ngay_thu_tien(ngay_thu_tien_str):
        """
        Parse ngày thu tiền từ string thành số ngày
        VD: "Ngày 1" -> 1, "Ngày 15" -> 15, "1" -> 1
        """
        if not ngay_thu_tien_str:
            return 1  # Mặc định ngày 1
            
        ngay_thu_tien_str = ngay_thu_tien_str.strip()
        
        # Tách số từ chuỗi
        import re
        numbers = re.findall(r'\d+', ngay_thu_tien_str)
        if numbers:
            day = int(numbers[0])
            # Đảm bảo ngày hợp lệ (1-31)
            return max(1, min(31, day))
        
        return 1  # Mặc định ngày 1

    @staticmethod
    def get_current_billing_period(hop_dong, current_date=None):
        """
        Tính kỳ thanh toán hiện tại dựa vào chu kỳ thanh toán của hợp đồng
        Sử dụng NGAY_NHAN_PHONG làm anchor point để đảm bảo chu kỳ chính xác
        """
        from datetime import datetime, date
        from dateutil.relativedelta import relativedelta
        
        if current_date is None:
            current_date = date.today()
        
        # Parse chu kỳ thanh toán và ngày thu tiền
        chu_ky_months = ChiSoDichVu.parse_chu_ky_thanh_toan(hop_dong.CHU_KY_THANH_TOAN)
        ngay_thu_tien = ChiSoDichVu.parse_ngay_thu_tien(hop_dong.NGAY_THU_TIEN)
        
        # Sử dụng ngày nhận phòng làm anchor point
        if hop_dong.NGAY_NHAN_PHONG:
            anchor_date = hop_dong.NGAY_NHAN_PHONG
        else:
            # Fallback nếu không có ngày nhận phòng
            anchor_date = hop_dong.NGAY_LAP_HD or current_date
        
        # Tính chu kỳ thanh toán dựa trên anchor date
        # Điều chỉnh anchor_date về ngày thu tiền trong tháng
        try:
            first_billing_date = anchor_date.replace(day=ngay_thu_tien)
        except ValueError:
            # Trường hợp ngày thu tiền > số ngày trong tháng (VD: ngày 31 trong tháng 2)
            # Lấy ngày cuối tháng
            if anchor_date.month == 12:
                next_month = anchor_date.replace(year=anchor_date.year + 1, month=1, day=1)
            else:
                next_month = anchor_date.replace(month=anchor_date.month + 1, day=1)
            first_billing_date = next_month - relativedelta(days=1)
        
        # Nếu anchor date sau ngày thu tiền trong tháng, thì chu kỳ đầu bắt đầu từ tháng sau
        if anchor_date.day > ngay_thu_tien:
            first_billing_date = first_billing_date + relativedelta(months=1)
        
        # Tìm kỳ thanh toán hiện tại
        current_period_start = first_billing_date
        
        # Lặp để tìm kỳ thanh toán hiện tại
        while current_period_start <= current_date:
            current_period_end = current_period_start + relativedelta(months=chu_ky_months)
            
            # Nếu current_date nằm trong kỳ này
            if current_period_start <= current_date < current_period_end:
                return current_period_start, current_period_end
            
            # Chuyển sang kỳ tiếp theo
            current_period_start = current_period_end
        
        # Nếu không tìm thấy (trường hợp current_date < first_billing_date)
        # Trả về kỳ đầu tiên
        final_start = first_billing_date
        final_end = first_billing_date + relativedelta(months=chu_ky_months)
        
        # Debug log
        print(f"DEBUG BILLING: Contract {hop_dong.MA_HOP_DONG}")
        print(f"DEBUG BILLING: Anchor date: {anchor_date}")
        print(f"DEBUG BILLING: First billing: {first_billing_date}")
        print(f"DEBUG BILLING: Current period: {final_start} to {final_end}")
        print(f"DEBUG BILLING: Current date: {current_date}")
        
        return final_start, final_end

    @staticmethod
    def check_existing_readings_in_period(hop_dong, start_period, end_period):
        """
        Kiểm tra xem đã có ghi chỉ số nào trong kỳ thanh toán hiện tại chưa
        """
        existing_readings = ChiSoDichVu.objects.filter(
            MA_HOP_DONG=hop_dong,
            NGAY_GHI_CS__gte=start_period,
            NGAY_GHI_CS__lt=end_period
        ).select_related('MA_DICH_VU').order_by('-NGAY_GHI_CS')
        
        return existing_readings

    @staticmethod
    def get_editable_readings(hop_dong, current_date=None):
        """
        Lấy danh sách chỉ số có thể chỉnh sửa trong kỳ thanh toán hiện tại
        """
        start_period, end_period = ChiSoDichVu.get_current_billing_period(hop_dong, current_date)
        existing_readings = ChiSoDichVu.check_existing_readings_in_period(hop_dong, start_period, end_period)
        
        # Group theo dịch vụ để lấy bản ghi mới nhất của mỗi dịch vụ
        readings_by_service = {}
        for reading in existing_readings:
            service_id = reading.MA_DICH_VU.MA_DICH_VU
            if service_id not in readings_by_service:
                readings_by_service[service_id] = reading
                
        return readings_by_service, start_period, end_period

    @staticmethod
    def tinh_chi_so_dich_vu(dich_vu_ap_dung, hop_dong, current_month, next_month):
        errors = []
        try:
            chi_so = ChiSoDichVu.get_chi_so_moi_nhat(dich_vu_ap_dung.MA_DICH_VU, hop_dong, current_month, next_month)
            so_dich_vu = 0
            thanh_tien = 0
            chi_so_cu = 0
            chi_so_moi = None

            if dich_vu_ap_dung.MA_DICH_VU.LOAI_DICH_VU not in ['Cố định', 'Co dinh']:
                if chi_so:
                    chi_so_cu = chi_so.CHI_SO_CU or 0
                    chi_so_moi = chi_so.CHI_SO_MOI
                    so_dich_vu = (chi_so_moi - chi_so_cu) if chi_so_moi is not None else 0
                    thanh_tien = so_dich_vu * dich_vu_ap_dung.GIA_DICH_VU_AD
                else:
                    chi_so_truoc = ChiSoDichVu.get_chi_so_truoc(dich_vu_ap_dung.MA_DICH_VU, hop_dong, current_month)
                    chi_so_cu = chi_so_truoc.CHI_SO_MOI if chi_so_truoc else 0
            else:
                so_dich_vu = 1
                thanh_tien = dich_vu_ap_dung.GIA_DICH_VU_AD

            return {
                'MA_CHI_SO': chi_so.MA_CHI_SO if chi_so else None,
                'MA_DICH_VU': dich_vu_ap_dung.MA_DICH_VU.MA_DICH_VU,
                'TEN_DICH_VU': dich_vu_ap_dung.MA_DICH_VU.TEN_DICH_VU,
                'LOAI_DICH_VU': dich_vu_ap_dung.MA_DICH_VU.LOAI_DICH_VU,
                'GIA_DICH_VU': float(dich_vu_ap_dung.GIA_DICH_VU_AD),
                'DON_VI_TINH': dich_vu_ap_dung.MA_DICH_VU.DON_VI_TINH,
                'CHI_SO_CU': float(chi_so_cu),
                'CHI_SO_MOI': float(chi_so_moi) if chi_so_moi is not None else None,
                'SO_DICH_VU': float(so_dich_vu),
                'THANH_TIEN': float(thanh_tien),
                'SO_LUONG': chi_so.SO_LUONG if hasattr(chi_so, 'SO_LUONG') else 0
            }, errors
        except Exception as e:
            errors.append(f'Lỗi khi tính chi tiết dịch vụ {dich_vu_ap_dung.MA_DICH_VU.TEN_DICH_VU}: {str(e)}')
            return None, errors