-- URGENT: Sửa lỗi Unknown column 'khuvuc.DIA_CHI_CHI_TIET'
-- Chạy script này ngay lập tức trong MySQL để thêm các trường bị thiếu

USE quanly_nhatro;

-- Kiểm tra cấu trúc bảng khuvuc hiện tại
DESCRIBE khuvuc;

-- Thêm từng trường một để tránh lỗi
ALTER TABLE khuvuc ADD COLUMN IF NOT EXISTS DIA_CHI_CHI_TIET TEXT NULL COMMENT 'Địa chỉ chi tiết';

ALTER TABLE khuvuc ADD COLUMN IF NOT EXISTS SO_NHA VARCHAR(100) NULL COMMENT 'Số nhà';

ALTER TABLE khuvuc ADD COLUMN IF NOT EXISTS TEN_DUONG VARCHAR(200) NULL COMMENT 'Tên đường';

ALTER TABLE khuvuc ADD COLUMN IF NOT EXISTS KINH_DO DECIMAL(10,7) NULL COMMENT 'Kinh độ (Longitude)';

ALTER TABLE khuvuc ADD COLUMN IF NOT EXISTS VI_DO DECIMAL(10,7) NULL COMMENT 'Vĩ độ (Latitude)';

ALTER TABLE khuvuc ADD COLUMN IF NOT EXISTS MO_TA_VI_TRI TEXT NULL COMMENT 'Mô tả vị trí';

ALTER TABLE khuvuc ADD COLUMN IF NOT EXISTS GHI_CHU_KV TEXT NULL COMMENT 'Ghi chú khu vực';

-- Kiểm tra kết quả sau khi thêm
DESCRIBE khuvuc;

-- Hiển thị dữ liệu mẫu
SELECT MA_KHU_VUC, TEN_KHU_VUC, DV_HANH_CHINH_CAP1, DIA_CHI_CHI_TIET, SO_NHA, KINH_DO, VI_DO FROM khuvuc LIMIT 3;