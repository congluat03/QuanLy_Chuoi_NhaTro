

-- Tạo bảng dangtinphong
CREATE TABLE IF NOT EXISTS `dangtinphong` (
    `MA_TIN_DANG` int(11) NOT NULL AUTO_INCREMENT,
    `MA_PHONG` int(11) NOT NULL,
    `SDT_LIEN_HE` varchar(15) NOT NULL COMMENT 'Số điện thoại liên hệ',
    `EMAIL_LIEN_HE` varchar(100) DEFAULT NULL COMMENT 'Email liên hệ',
    `TRANG_THAI` varchar(20) NOT NULL DEFAULT 'DANG_HIEN_THI' COMMENT 'Trạng thái tin đăng',
    `NGAY_DANG` datetime(6) NOT NULL COMMENT 'Ngày đăng tin',
    `NGAY_CAP_NHAT` datetime(6) NOT NULL COMMENT 'Ngày cập nhật',
    `LUOT_XEM` int(11) NOT NULL DEFAULT 0 COMMENT 'Số lượt xem',
    `LUOT_LIEN_HE` int(11) NOT NULL DEFAULT 0 COMMENT 'Số lượt liên hệ',
    PRIMARY KEY (`MA_TIN_DANG`),
    UNIQUE KEY `MA_PHONG` (`MA_PHONG`),
    CONSTRAINT `dangtinphong_MA_PHONG_fk` FOREIGN KEY (`MA_PHONG`) REFERENCES `phongtro` (`MA_PHONG`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng quản lý tin đăng phòng';

-- Tạo bảng hinhanhtindang  
CREATE TABLE IF NOT EXISTS `hinhanhtindang` (
    `MA_HINH_ANH` int(11) NOT NULL AUTO_INCREMENT,
    `MA_TIN_DANG` int(11) NOT NULL,
    `HINH_ANH` varchar(100) NOT NULL COMMENT 'Đường dẫn file hình ảnh',
    `THU_TU` int(10) unsigned NOT NULL DEFAULT 1 COMMENT 'Thứ tự hiển thị',
    `MO_TA` varchar(200) DEFAULT NULL COMMENT 'Mô tả hình ảnh',
    `NGAY_TAO` datetime(6) NOT NULL COMMENT 'Ngày tạo',
    PRIMARY KEY (`MA_HINH_ANH`),
    KEY `hinhanhtindang_MA_TIN_DANG_idx` (`MA_TIN_DANG`),
    CONSTRAINT `hinhanhtindang_MA_TIN_DANG_fk` FOREIGN KEY (`MA_TIN_DANG`) REFERENCES `dangtinphong` (`MA_TIN_DANG`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng hình ảnh tin đăng';

-- Tạo index để tối ưu hiệu suất
CREATE INDEX `idx_dangtinphong_trang_thai` ON `dangtinphong` (`TRANG_THAI`);
CREATE INDEX `idx_dangtinphong_ngay_dang` ON `dangtinphong` (`NGAY_DANG`);
CREATE INDEX `idx_hinhanhtindang_thu_tu` ON `hinhanhtindang` (`THU_TU`);

-- Thêm ràng buộc kiểm tra trạng thái
ALTER TABLE `dangtinphong` 
ADD CONSTRAINT `chk_trang_thai` 
CHECK (`TRANG_THAI` IN ('DANG_HIEN_THI', 'DA_AN'));

-- Thêm ràng buộc kiểm tra số lượt >= 0
ALTER TABLE `dangtinphong` 
ADD CONSTRAINT `chk_luot_xem` CHECK (`LUOT_XEM` >= 0);

ALTER TABLE `dangtinphong` 
ADD CONSTRAINT `chk_luot_lien_he` CHECK (`LUOT_LIEN_HE` >= 0);

-- Thêm ràng buộc kiểm tra thứ tự > 0
ALTER TABLE `hinhanhtindang` 
ADD CONSTRAINT `chk_thu_tu` CHECK (`THU_TU` > 0);

-- Insert sample data (optional)
-- INSERT INTO `dangtinphong` (`MA_PHONG`, `SDT_LIEN_HE`, `EMAIL_LIEN_HE`, `TRANG_THAI`, `NGAY_DANG`, `NGAY_CAP_NHAT`) 
-- VALUES (1, '0123456789', 'contact@example.com', 'DANG_HIEN_THI', NOW(), NOW());

COMMIT;

-- Hiển thị cấu trúc bảng đã tạo
DESCRIBE `dangtinphong`;
DESCRIBE `hinhanhtindang`;

-- Kiểm tra ràng buộc
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE,
    COLUMN_NAME
FROM 
    INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE 
    TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME IN ('dangtinphong', 'hinhanhtindang')
ORDER BY 
    TABLE_NAME, CONSTRAINT_NAME;