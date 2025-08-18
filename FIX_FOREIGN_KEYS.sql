-- Script SQL để tạo các foreign key constraints sau khi chạy migrations
-- Chạy script này sau khi migrations hoàn thành để thiết lập relationships

USE quanly_nhatro;

-- Tạo foreign key cho PhongTro -> KhuVuc
ALTER TABLE phongtro 
ADD CONSTRAINT fk_phongtro_khuvuc 
FOREIGN KEY (MA_KHU_VUC) REFERENCES khuvuc(MA_KHU_VUC) 
ON DELETE CASCADE;

-- Tạo foreign key cho CocPhong -> PhongTro  
ALTER TABLE cocphong 
ADD CONSTRAINT fk_cocphong_phongtro 
FOREIGN KEY (MA_PHONG) REFERENCES phongtro(MA_PHONG) 
ON DELETE CASCADE;

-- Tạo foreign key cho CocPhong -> KhachThue (nếu bảng khachthue đã tồn tại)
-- ALTER TABLE cocphong 
-- ADD CONSTRAINT fk_cocphong_khachthue 
-- FOREIGN KEY (MA_KHACH_THUE) REFERENCES khachthue(MA_KHACH_THUE) 
-- ON DELETE CASCADE;

-- Tạo foreign key cho TaiSanPhong -> PhongTro
ALTER TABLE taisanphong 
ADD CONSTRAINT fk_taisanphong_phongtro 
FOREIGN KEY (MA_PHONG) REFERENCES phongtro(MA_PHONG) 
ON DELETE CASCADE;

-- Tạo foreign key cho TaiSanBangGiao -> HopDong (nếu bảng hopdong đã tồn tại)
-- ALTER TABLE taisanbangiao 
-- ADD CONSTRAINT fk_taisanbangiao_hopdong 
-- FOREIGN KEY (MA_HOP_DONG) REFERENCES hopdong(MA_HOP_DONG) 
-- ON DELETE CASCADE;

-- Tạo foreign key cho DangTinPhong -> PhongTro
ALTER TABLE dangtinphong 
ADD CONSTRAINT fk_dangtinphong_phongtro 
FOREIGN KEY (MA_PHONG) REFERENCES phongtro(MA_PHONG) 
ON DELETE CASCADE;

-- Tạo foreign key cho HinhAnhTinDang -> DangTinPhong
ALTER TABLE hinhanhtindang 
ADD CONSTRAINT fk_hinhanhtindang_dangtinphong 
FOREIGN KEY (MA_TIN_DANG) REFERENCES dangtinphong(MA_TIN_DANG) 
ON DELETE CASCADE;

-- Hiển thị các foreign keys đã tạo
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM 
    INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE 
    REFERENCED_TABLE_SCHEMA = 'quanly_nhatro' 
    AND TABLE_NAME IN ('phongtro', 'cocphong', 'taisanphong', 'taisanbangiao', 'dangtinphong', 'hinhanhtindang')
ORDER BY TABLE_NAME;