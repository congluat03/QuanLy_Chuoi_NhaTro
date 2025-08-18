# 🗃️ HƯỚNG DẪN TẠO BẢNG QUẢN LÝ TIN ĐĂNG PHÒNG

## 📋 Các bảng sẽ được tạo:

1. **`dangtinphong`** - Bảng chính quản lý tin đăng
2. **`hinhanhtindang`** - Bảng lưu trữ hình ảnh tin đăng

## 🚀 Cách 1: Sử dụng Django Migration (Khuyến nghị)

### Bước 1: Chạy migration
```bash
# Di chuyển vào thư mục dự án
cd /mnt/e/Hoc/KhoaLuan/Code/WebsiteQuanLyNhaTro

# Tạo migration file (nếu chưa có)
python manage.py makemigrations phongtro

# Áp dụng migration vào database
python manage.py migrate phongtro
```

### Bước 2: Kiểm tra bảng đã tạo
```bash
python manage.py dbshell
```

Trong MySQL shell:
```sql
SHOW TABLES LIKE '%dang%';
DESCRIBE dangtinphong;
DESCRIBE hinhanhtindang;
```

## 🔧 Cách 2: Chạy SQL Script trực tiếp

### Bước 1: Kết nối MySQL
```bash
mysql -u your_username -p your_database_name
```

### Bước 2: Chạy script SQL
```sql
SOURCE /mnt/e/Hoc/KhoaLuan/Code/WebsiteQuanLyNhaTro/sql_scripts/create_dang_tin_phong_tables.sql;
```

Hoặc copy nội dung file SQL và paste vào MySQL command line.

## 📊 Cấu trúc bảng chi tiết

### Bảng `dangtinphong`
| Cột | Kiểu dữ liệu | Mô tả |
|-----|-------------|--------|
| MA_TIN_DANG | INT AUTO_INCREMENT | Mã tin đăng (Primary Key) |
| MA_PHONG | INT | Mã phòng (Foreign Key - UNIQUE) |
| SDT_LIEN_HE | VARCHAR(15) | Số điện thoại liên hệ |
| EMAIL_LIEN_HE | VARCHAR(100) | Email liên hệ (nullable) |
| TRANG_THAI | VARCHAR(20) | Trạng thái (DANG_HIEN_THI/DA_AN) |
| NGAY_DANG | DATETIME | Ngày đăng tin |
| NGAY_CAP_NHAT | DATETIME | Ngày cập nhật |
| LUOT_XEM | INT | Số lượt xem |
| LUOT_LIEN_HE | INT | Số lượt liên hệ |

### Bảng `hinhanhtindang`
| Cột | Kiểu dữ liệu | Mô tả |
|-----|-------------|--------|
| MA_HINH_ANH | INT AUTO_INCREMENT | Mã hình ảnh (Primary Key) |
| MA_TIN_DANG | INT | Mã tin đăng (Foreign Key) |
| HINH_ANH | VARCHAR(100) | Đường dẫn file hình ảnh |
| THU_TU | INT UNSIGNED | Thứ tự hiển thị |
| MO_TA | VARCHAR(200) | Mô tả hình ảnh (nullable) |
| NGAY_TAO | DATETIME | Ngày tạo |

## 🔐 Ràng buộc và Index

### Foreign Keys:
- `dangtinphong.MA_PHONG` → `phongtro.MA_PHONG` (CASCADE DELETE)
- `hinhanhtindang.MA_TIN_DANG` → `dangtinphong.MA_TIN_DANG` (CASCADE DELETE)

### Unique Constraints:
- `dangtinphong.MA_PHONG` (Mỗi phòng chỉ có 1 tin đăng)

### Check Constraints:
- `TRANG_THAI` chỉ nhận giá trị 'DANG_HIEN_THI' hoặc 'DA_AN'
- `LUOT_XEM` và `LUOT_LIEN_HE` >= 0
- `THU_TU` > 0

### Indexes:
- `idx_dangtinphong_trang_thai` - Tối ưu filter theo trạng thái
- `idx_dangtinphong_ngay_dang` - Tối ưu sắp xếp theo ngày đăng
- `idx_hinhanhtindang_thu_tu` - Tối ưu sắp xếp hình ảnh

## ✅ Kiểm tra sau khi tạo bảng

### 1. Kiểm tra bảng đã tạo:
```sql
SHOW TABLES LIKE '%dang%';
```

### 2. Kiểm tra cấu trúc:
```sql
DESCRIBE dangtinphong;
DESCRIBE hinhanhtindang;
```

### 3. Kiểm tra Foreign Keys:
```sql
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM 
    INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE 
    TABLE_SCHEMA = DATABASE() 
    AND REFERENCED_TABLE_NAME IS NOT NULL
    AND TABLE_NAME IN ('dangtinphong', 'hinhanhtindang');
```

### 4. Test insert dữ liệu mẫu:
```sql
-- Giả sử có phòng có MA_PHONG = 1
INSERT INTO dangtinphong (MA_PHONG, SDT_LIEN_HE, EMAIL_LIEN_HE, TRANG_THAI, NGAY_DANG, NGAY_CAP_NHAT) 
VALUES (1, '0123456789', 'test@example.com', 'DANG_HIEN_THI', NOW(), NOW());

-- Kiểm tra
SELECT * FROM dangtinphong;
```

## 🚨 Lưu ý quan trọng

1. **Backup database** trước khi chạy migration
2. **Kiểm tra bảng phongtro** đã tồn tại với cột MA_PHONG
3. **Đảm bảo quyền** CREATE TABLE và ALTER TABLE
4. **Test trên môi trường development** trước khi deploy production

## 🔄 Rollback (nếu cần)

Nếu cần xóa bảng đã tạo:
```sql
-- Xóa theo thứ tự (quan trọng do Foreign Key)
DROP TABLE IF EXISTS hinhanhtindang;
DROP TABLE IF EXISTS dangtinphong;
```

Hoặc dùng Django:
```bash
python manage.py migrate phongtro 0001_initial
```