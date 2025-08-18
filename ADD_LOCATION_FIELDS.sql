-- Script SQL để thêm các trường mới cho bảng khuvuc
-- Chạy script này trực tiếp trong MySQL để thêm các trường địa chỉ và tọa độ

USE quanly_nhatro;

-- Thêm các trường địa chỉ chi tiết
ALTER TABLE khuvuc 
ADD COLUMN DIA_CHI_CHI_TIET TEXT NULL COMMENT 'Địa chỉ chi tiết',
ADD COLUMN SO_NHA VARCHAR(100) NULL COMMENT 'Số nhà',
ADD COLUMN TEN_DUONG VARCHAR(200) NULL COMMENT 'Tên đường';

-- Thêm các trường tọa độ GPS
ALTER TABLE khuvuc 
ADD COLUMN KINH_DO DECIMAL(10,7) NULL COMMENT 'Kinh độ (Longitude)',
ADD COLUMN VI_DO DECIMAL(10,7) NULL COMMENT 'Vĩ độ (Latitude)';

-- Thêm các trường thông tin bổ sung
ALTER TABLE khuvuc 
ADD COLUMN MO_TA_VI_TRI TEXT NULL COMMENT 'Mô tả vị trí',
ADD COLUMN GHI_CHU_KV TEXT NULL COMMENT 'Ghi chú khu vực';

-- Cập nhật comment cho các trường hiện có
ALTER TABLE khuvuc 
MODIFY COLUMN DV_HANH_CHINH_CAP1 VARCHAR(50) NULL COMMENT 'Tỉnh/Thành phố',
MODIFY COLUMN DV_HANH_CHINH_CAP2 VARCHAR(50) NULL COMMENT 'Quận/Huyện', 
MODIFY COLUMN DV_HANH_CHINH_CAP3 VARCHAR(50) NULL COMMENT 'Phường/Xã';

-- Hiển thị cấu trúc bảng sau khi cập nhật
DESCRIBE khuvuc;