from django.db import models

# Create your models here.
# Model for nhatro
class NhaTro(models.Model):
    MA_NHA_TRO = models.AutoField(primary_key=True)
    MA_QUAN_LY = models.ForeignKey(
        'thanhvien.NguoiQuanLy',
        on_delete=models.CASCADE,
        db_column='MA_QUAN_LY',
        related_name='ds_nhatro'
    )
    TEN_NHA_TRO = models.CharField(max_length=200, null=True, blank=True)
    VUNG_MIEN = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.TEN_NHA_TRO or f"Nhà trọ {self.MA_NHA_TRO}"

    class Meta:
        db_table = 'nhatro'

# Model for khuvuc
class KhuVuc(models.Model):
    MA_KHU_VUC = models.AutoField(primary_key=True)
    MA_NHA_TRO = models.ForeignKey(
        'NhaTro',
        on_delete=models.CASCADE,
        db_column='MA_NHA_TRO',
        related_name='ds_khuvuc'
    )
    TEN_KHU_VUC = models.CharField(max_length=200, null=True, blank=True)
    TRANG_THAI_KV = models.CharField(max_length=50, null=True, blank=True)
    DV_HANH_CHINH_CAP1 = models.CharField(max_length=50, null=True, blank=True, verbose_name="Tỉnh/Thành phố")
    DV_HANH_CHINH_CAP2 = models.CharField(max_length=50, null=True, blank=True, verbose_name="Quận/Huyện")
    DV_HANH_CHINH_CAP3 = models.CharField(max_length=50, null=True, blank=True, verbose_name="Phường/Xã")
    
    # Thông tin địa chỉ chi tiết
    DIA_CHI_CHI_TIET = models.TextField(null=True, blank=True, verbose_name="Địa chỉ chi tiết")
    SO_NHA = models.CharField(max_length=100, null=True, blank=True, verbose_name="Số nhà")
    TEN_DUONG = models.CharField(max_length=200, null=True, blank=True, verbose_name="Tên đường")
    
    # Tọa độ GPS để hiển thị trên bản đồ
    KINH_DO = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Kinh độ (Longitude)")
    VI_DO = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Vĩ độ (Latitude)")
    
    # Điểm tọa độ kết hợp để dễ xử lý (format: "lat,lng")
    DIEM_TOA_DO = models.CharField(max_length=50, null=True, blank=True, verbose_name="Điểm tọa độ")
    
    # Thông tin bổ sung
    MO_TA_VI_TRI = models.TextField(null=True, blank=True, verbose_name="Mô tả vị trí")
    GHI_CHU_KV = models.TextField(null=True, blank=True, verbose_name="Ghi chú khu vực")

    def __str__(self):
        return self.TEN_KHU_VUC or f"Khu vực {self.MA_KHU_VUC}"

    class Meta:
        db_table = 'khuvuc'
        
    @property
    def dia_chi_day_du(self):
        """Trả về địa chỉ đầy đủ của khu vực."""
        parts = []
        if self.SO_NHA:
            parts.append(self.SO_NHA)
        if self.TEN_DUONG:
            parts.append(self.TEN_DUONG)
        if self.DV_HANH_CHINH_CAP3:
            parts.append(self.DV_HANH_CHINH_CAP3)
        if self.DV_HANH_CHINH_CAP2:
            parts.append(self.DV_HANH_CHINH_CAP2)
        if self.DV_HANH_CHINH_CAP1:
            parts.append(self.DV_HANH_CHINH_CAP1)
        return ", ".join(parts)
    
    @property
    def has_coordinates(self):
        """Kiểm tra xem khu vực có tọa độ hay không."""
        return self.KINH_DO is not None and self.VI_DO is not None
    
    def get_google_maps_url(self):
        """Trả về URL Google Maps dựa trên tọa độ hoặc địa chỉ."""
        if self.has_coordinates:
            return f"https://www.google.com/maps?q={self.VI_DO},{self.KINH_DO}"
        elif self.dia_chi_day_du:
            import urllib.parse
            address = urllib.parse.quote(self.dia_chi_day_du)
            return f"https://www.google.com/maps/search/{address}"
        return None
    
    def save(self, *args, **kwargs):
        """Override save để tự động cập nhật DIEM_TOA_DO khi lưu."""
        # Tự động tạo DIEM_TOA_DO từ VI_DO và KINH_DO
        if self.VI_DO is not None and self.KINH_DO is not None:
            self.DIEM_TOA_DO = f"{self.VI_DO},{self.KINH_DO}"
        else:
            self.DIEM_TOA_DO = None
        super().save(*args, **kwargs)
    
    def set_coordinates_from_string(self, coordinates_string):
        """Thiết lập tọa độ từ string format 'lat,lng'."""
        if coordinates_string and ',' in coordinates_string:
            try:
                parts = coordinates_string.split(',')
                if len(parts) == 2:
                    self.VI_DO = float(parts[0].strip())
                    self.KINH_DO = float(parts[1].strip())
                    self.DIEM_TOA_DO = coordinates_string.strip()
            except (ValueError, IndexError):
                pass
    
    @property
    def coordinates_string(self):
        """Trả về tọa độ dưới dạng string 'lat,lng'."""
        if self.DIEM_TOA_DO:
            return self.DIEM_TOA_DO
        elif self.has_coordinates:
            return f"{self.VI_DO},{self.KINH_DO}"
        return None
    
    @property
    def coordinates_dict(self):
        """Trả về tọa độ dưới dạng dict {lat: ..., lng: ...}."""
        if self.has_coordinates:
            return {
                'lat': float(self.VI_DO),
                'lng': float(self.KINH_DO)
            }
        return None