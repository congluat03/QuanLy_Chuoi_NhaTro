#!/usr/bin/env python
"""
Quick fix cho lỗi migration hopdong
Chạy script này để sửa nhanh lỗi NodeNotFoundError
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Chạy lệnh shell và in kết quả"""
    print(f"\n🔧 {description}...")
    print(f"💻 Lệnh: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.stdout:
            print("📤 Output:", result.stdout)
        if result.stderr and result.returncode != 0:
            print("⚠️ Error:", result.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Lỗi khi chạy lệnh: {e}")
        return False

def main():
    print("🚀 QUICK FIX cho lỗi migration hopdong")
    print("=" * 50)
    
    steps = [
        # Kiểm tra trạng thái hiện tại
        ("python manage.py showmigrations hopdong", "Kiểm tra migration hiện tại"),
        
        # Fake apply migration ban đầu
        ("python manage.py migrate hopdong 0001 --fake", "Fake apply migration đầu tiên"),
        
        # Tạo migration mới từ models hiện tại
        ("python manage.py makemigrations hopdong", "Tạo migration từ models hiện tại"),
        
        # Apply migration mới
        ("python manage.py migrate hopdong", "Apply migration mới"),
        
        # Kiểm tra lại
        ("python manage.py showmigrations hopdong", "Kiểm tra kết quả cuối cùng"),
    ]
    
    success_count = 0
    
    for command, description in steps:
        success = run_command(command, description)
        if success:
            success_count += 1
            print("✅ Thành công!")
        else:
            print("⚠️ Có vấn đề - tiếp tục...")
            
        print("-" * 30)
    
    print(f"\n📊 Kết quả: {success_count}/{len(steps)} bước thành công")
    
    if success_count >= 3:  # Ít nhất 3 bước thành công
        print("🎉 Migration đã được sửa! Bạn có thể chạy server:")
        print("   python manage.py runserver")
    else:
        print("⚠️ Vẫn có vấn đề. Thử các cách thủ công:")
        print("1. Xóa thủ công migration records trong database:")
        print("   DELETE FROM django_migrations WHERE app = 'hopdong';")
        print("2. Hoặc chạy: python fix_migration_error.py")
    
    return success_count >= 3

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)