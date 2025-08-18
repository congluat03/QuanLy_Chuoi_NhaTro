# 📍 HƯỚNG DẪN CẬP NHẬT TÍNH NĂNG BẢN ĐỒ KHU VỰC

## 🎯 Mục đích
Thêm các trường địa chỉ chi tiết và tọa độ GPS vào model KhuVuc để hiển thị vị trí trên bản đồ Google Maps.

## 🔧 Các trường đã thêm vào model KhuVuc

### 1. **Địa chỉ chi tiết**
- `DIA_CHI_CHI_TIET` (TEXT) - Địa chỉ chi tiết
- `SO_NHA` (VARCHAR 100) - Số nhà
- `TEN_DUONG` (VARCHAR 200) - Tên đường

### 2. **Tọa độ GPS**
- `KINH_DO` (DECIMAL 10,7) - Kinh độ (Longitude)
- `VI_DO` (DECIMAL 10,7) - Vĩ độ (Latitude)

### 3. **Thông tin bổ sung**
- `MO_TA_VI_TRI` (TEXT) - Mô tả vị trí
- `GHI_CHU_KV` (TEXT) - Ghi chú khu vực

## 📋 Cách cập nhật database

### Option 1: Chạy script SQL trực tiếp
```bash
# Vào MySQL và chạy file SQL
mysql -u root -p quanly_nhatro < ADD_LOCATION_FIELDS.sql
```

### Option 2: Copy từng lệnh vào MySQL
```sql
USE quanly_nhatro;

ALTER TABLE khuvuc 
ADD COLUMN DIA_CHI_CHI_TIET TEXT NULL COMMENT 'Địa chỉ chi tiết',
ADD COLUMN SO_NHA VARCHAR(100) NULL COMMENT 'Số nhà',
ADD COLUMN TEN_DUONG VARCHAR(200) NULL COMMENT 'Tên đường',
ADD COLUMN KINH_DO DECIMAL(10,7) NULL COMMENT 'Kinh độ (Longitude)',
ADD COLUMN VI_DO DECIMAL(10,7) NULL COMMENT 'Vĩ độ (Latitude)',
ADD COLUMN MO_TA_VI_TRI TEXT NULL COMMENT 'Mô tả vị trí',
ADD COLUMN GHI_CHU_KV TEXT NULL COMMENT 'Ghi chú khu vực';
```

## ✨ Tính năng mới

### 1. **Form thêm/sửa khu vực**
- ✅ Nhập địa chỉ chi tiết (số nhà, tên đường)
- ✅ Nhập tọa độ GPS với hướng dẫn từ Google Maps
- ✅ Mô tả vị trí và ghi chú

### 2. **Trang chi tiết khu vực**
- ✅ Hiển thị bản đồ Google Maps tương tác
- ✅ 3 chế độ hiển thị:
  - 🔴 **Tọa độ chính xác**: Marker đỏ
  - 🟡 **Địa chỉ ước tính**: Marker vàng (geocoding)
  - ⚪ **Chưa có thông tin**: Gợi ý cập nhật

### 3. **Tính năng bản đồ**
- ✅ Marker với thông tin chi tiết
- ✅ Nút mở Google Maps
- ✅ Copy tọa độ clipboard
- ✅ Responsive design

## 🔍 Cách lấy tọa độ từ Google Maps

1. Mở https://maps.google.com
2. Tìm kiếm địa chỉ hoặc click chuột phải vào vị trí
3. Chọn "What's here?" hoặc xem tọa độ hiển thị
4. Copy số đầu tiên (Vĩ độ) và số thứ hai (Kinh độ)

## 📁 Files đã cập nhật

### Models
- `apps/nhatro/models.py` - Thêm trường và methods mới

### Views  
- `apps/nhatro/admin_views.py` - Xử lý form thêm/sửa

### Templates
- `templates/admin/khuvuc/themsua_khuvuc.html` - Form mới
- `templates/admin/khuvuc/chitiet_khuvuc.html` - Tích hợp bản đồ

## ⚠️ Lưu ý quan trọng

1. **Google Maps API**: Template sử dụng API key demo, nên thay thế bằng key thật
2. **Responsive**: Bản đồ tự động điều chỉnh kích thước
3. **Fallback**: Có xử lý khi không load được bản đồ
4. **Performance**: Chỉ load Maps API khi cần thiết

## 🚀 Kết quả

- ✅ Admin có thể nhập địa chỉ và tọa độ chi tiết
- ✅ Hiển thị vị trí khu vực trên bản đồ
- ✅ Liên kết trực tiếp đến Google Maps
- ✅ UI/UX hiện đại và dễ sử dụng
- ✅ Tương thích mobile

Sau khi cập nhật database, tất cả tính năng sẽ hoạt động ngay lập tức!