#!/usr/bin/env python
"""
Script để sửa lỗi migration NodeNotFoundError cho hopdong app
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line
from django.apps import apps

def fix_hopdong_migrations():
    """Sửa lỗi migration cho hopdong app"""
    
    print("🔍 Đang kiểm tra trạng thái migration...")
    
    try:
        with connection.cursor() as cursor:
            # Kiểm tra các migration hiện tại của hopdong
            cursor.execute("""
                SELECT name, applied FROM django_migrations 
                WHERE app = 'hopdong' 
                ORDER BY applied
            """)
            current_migrations = cursor.fetchall()
            
            print(f"📋 Tìm thấy {len(current_migrations)} migration records cho hopdong:")
            for name, applied in current_migrations:
                print(f"  - {name} (applied: {applied})")
            
            # Xóa tất cả migration records của hopdong
            print("\n🧹 Đang xóa các migration records cũ...")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'hopdong'")
            deleted_count = cursor.rowcount
            print(f"✅ Đã xóa {deleted_count} migration records")
            
            # Tạo lại migration record đầu tiên
            print("\n🔧 Đang tạo lại migration state...")
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('hopdong', '0001_initial', NOW())
            """)
            print("✅ Đã tạo migration record: hopdong.0001_initial")
            
            # Kiểm tra lại
            cursor.execute("""
                SELECT name, applied FROM django_migrations 
                WHERE app = 'hopdong' 
                ORDER BY applied
            """)
            new_migrations = cursor.fetchall()
            
            print(f"\n📋 Migration state mới cho hopdong:")
            for name, applied in new_migrations:
                print(f"  ✅ {name} (applied: {applied})")
                
        print("\n🎉 Hoàn thành! Migration error đã được sửa.")
        print("\nBây giờ bạn có thể chạy:")
        print("  python manage.py showmigrations hopdong")
        print("  python manage.py runserver")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi sửa migration: {e}")
        print("\n🔧 Thử các cách khác:")
        print("1. Chạy: python manage.py migrate hopdong 0001 --fake")
        print("2. Hoặc chạy SQL trong fix_migrations.sql")
        return False

def check_migration_files():
    """Kiểm tra các migration files trong thư mục"""
    migration_dir = "apps/hopdong/migrations"
    
    print(f"\n📁 Kiểm tra migration files trong {migration_dir}:")
    try:
        files = os.listdir(migration_dir)
        migration_files = [f for f in files if f.endswith('.py') and f != '__init__.py']
        
        if migration_files:
            print(f"  Tìm thấy {len(migration_files)} migration files:")
            for f in sorted(migration_files):
                print(f"    - {f}")
        else:
            print("  ⚠️ Không tìm thấy migration files nào")
            
    except FileNotFoundError:
        print(f"  ❌ Không tìm thấy thư mục {migration_dir}")

if __name__ == "__main__":
    print("🚀 Bắt đầu sửa lỗi migration cho hopdong app...")
    print("="*50)
    
    # Kiểm tra migration files
    check_migration_files()
    
    # Sửa migration state trong database
    success = fix_hopdong_migrations()
    
    if success:
        print("\n" + "="*50)
        print("✅ THÀNH CÔNG! Lỗi migration đã được sửa.")
        print("Bạn có thể tiếp tục sử dụng ứng dụng bình thường.")
    else:
        print("\n" + "="*50)
        print("❌ CHƯA SỬA ĐƯỢC. Vui lòng thử các cách thủ công.")
        
    sys.exit(0 if success else 1)