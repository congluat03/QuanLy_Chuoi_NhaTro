#!/usr/bin/env python3
"""
Script tự động tạo bảng dangtinphong và hinhanhtindang
Chạy script này để tạo bảng mới trên database MySQL
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection, transaction
from django.core.management import execute_from_command_line

# Thêm thư mục dự án vào Python path
sys.path.append('/mnt/e/Hoc/KhoaLuan/Code/WebsiteQuanLyNhaTro')

# Thiết lập Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def create_tables():
    """Tạo bảng dangtinphong và hinhanhtindang"""
    
    sql_statements = [
        # Tạo bảng dangtinphong
        """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng quản lý tin đăng phòng'
        """,
        
        # Tạo bảng hinhanhtindang
        """
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng hình ảnh tin đăng'
        """,
        
        # Tạo indexes
        "CREATE INDEX IF NOT EXISTS `idx_dangtinphong_trang_thai` ON `dangtinphong` (`TRANG_THAI`)",
        "CREATE INDEX IF NOT EXISTS `idx_dangtinphong_ngay_dang` ON `dangtinphong` (`NGAY_DANG`)",
        "CREATE INDEX IF NOT EXISTS `idx_hinhanhtindang_thu_tu` ON `hinhanhtindang` (`THU_TU`)",
    ]
    
    try:
        with connection.cursor() as cursor:
            with transaction.atomic():
                for sql in sql_statements:
                    print(f"Executing: {sql[:50]}...")
                    cursor.execute(sql)
                    
        print("✅ Tạo bảng thành công!")
        
        # Kiểm tra bảng đã tạo
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE '%dang%'")
            tables = cursor.fetchall()
            print(f"📋 Các bảng đã tạo: {[table[0] for table in tables]}")
            
            # Hiển thị cấu trúc bảng
            for table_name in ['dangtinphong', 'hinhanhtindang']:
                try:
                    cursor.execute(f"DESCRIBE {table_name}")
                    columns = cursor.fetchall()
                    print(f"\n📊 Cấu trúc bảng {table_name}:")
                    for col in columns:
                        print(f"  - {col[0]}: {col[1]} {col[2] if col[2] else ''}")
                except Exception as e:
                    print(f"❌ Lỗi khi hiển thị cấu trúc bảng {table_name}: {e}")
                    
    except Exception as e:
        print(f"❌ Lỗi khi tạo bảng: {e}")
        return False
    
    return True

def run_django_migration():
    """Chạy Django migration"""
    try:
        print("🔄 Đang chạy Django migration...")
        
        # Tạo migration file
        execute_from_command_line(['manage.py', 'makemigrations', 'phongtro'])
        
        # Áp dụng migration
        execute_from_command_line(['manage.py', 'migrate', 'phongtro'])
        
        print("✅ Django migration hoàn thành!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi Django migration: {e}")
        return False

def main():
    """Hàm chính"""
    print("🚀 BẮT ĐẦU TẠO BẢNG QUẢN LÝ TIN ĐĂNG PHÒNG")
    print("=" * 50)
    
    # Kiểm tra kết nối database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Kết nối database thành công!")
    except Exception as e:
        print(f"❌ Không thể kết nối database: {e}")
        return
    
    # Chọn phương thức tạo bảng
    print("\nChọn phương thức tạo bảng:")
    print("1. Django Migration (Khuyến nghị)")
    print("2. SQL Script trực tiếp")
    
    choice = input("Nhập lựa chọn (1 hoặc 2): ").strip()
    
    if choice == "1":
        success = run_django_migration()
    elif choice == "2":
        success = create_tables()
    else:
        print("❌ Lựa chọn không hợp lệ!")
        return
    
    if success:
        print("\n🎉 HOÀN THÀNH!")
        print("📝 Bây giờ bạn có thể:")
        print("  1. Truy cập /admin/tin-dang/ để quản lý tin đăng")
        print("  2. Vào /phong-tro/ để xem giao diện user")
        print("  3. Đăng tin phòng mới từ admin panel")
    else:
        print("\n❌ QUÁ TRÌNH THẤT BẠI!")
        print("📝 Hãy kiểm tra lại:")
        print("  1. Kết nối database")
        print("  2. Quyền tạo bảng")
        print("  3. Bảng phongtro đã tồn tại")

if __name__ == "__main__":
    main()