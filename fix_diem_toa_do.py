#!/usr/bin/env python3
"""
Script để sửa lỗi field DIEM_TOA_DO trong database
Lỗi: (1416, 'Cannot get geometry object from data you send to the GEOMETRY field')
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from apps.nhatro.models import KhuVuc

def fix_diem_toa_do_field():
    """Sửa lỗi field DIEM_TOA_DO"""
    
    with connection.cursor() as cursor:
        try:
            # Kiểm tra kiểu dữ liệu hiện tại của DIEM_TOA_DO
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'khuvuc' 
                AND COLUMN_NAME = 'DIEM_TOA_DO'
            """)
            
            result = cursor.fetchone()
            if result:
                column_name, data_type, max_length, is_nullable = result
                print(f"Current field type: {data_type}")
                print(f"Max length: {max_length}")
                print(f"Is nullable: {is_nullable}")
                
                # Nếu field hiện tại không phải VARCHAR hoặc TEXT
                if data_type.upper() not in ['VARCHAR', 'TEXT', 'CHAR']:
                    print("Fixing DIEM_TOA_DO field type...")
                    
                    # Backup dữ liệu hiện có
                    cursor.execute("SELECT MA_KHU_VUC, VI_DO, KINH_DO FROM khuvuc WHERE VI_DO IS NOT NULL AND KINH_DO IS NOT NULL")
                    khu_vucs_with_coords = cursor.fetchall()
                    
                    # Thay đổi kiểu dữ liệu field
                    cursor.execute("""
                        ALTER TABLE khuvuc 
                        MODIFY COLUMN DIEM_TOA_DO VARCHAR(50) NULL
                    """)
                    
                    print("Field type changed to VARCHAR(50)")
                    
                    # Cập nhật lại dữ liệu
                    for ma_khu_vuc, vi_do, kinh_do in khu_vucs_with_coords:
                        if vi_do and kinh_do:
                            diem_toa_do = f"{vi_do},{kinh_do}"
                            cursor.execute("""
                                UPDATE khuvuc 
                                SET DIEM_TOA_DO = %s 
                                WHERE MA_KHU_VUC = %s
                            """, [diem_toa_do, ma_khu_vuc])
                    
                    print(f"Updated {len(khu_vucs_with_coords)} records with coordinate data")
                    print("✅ DIEM_TOA_DO field fixed successfully!")
                    
                else:
                    print("✅ DIEM_TOA_DO field is already correct type (VARCHAR/TEXT)")
                    
        except Exception as e:
            print(f"❌ Error fixing field: {e}")
            return False
            
    return True

def test_khu_vuc_creation():
    """Test tạo khu vực mới"""
    try:
        # Test tạo khu vực mới
        from apps.nhatro.models import NhaTro
        
        nha_tro = NhaTro.objects.first()
        if not nha_tro:
            print("❌ No NhaTro found for testing")
            return False
            
        test_khu_vuc = KhuVuc(
            MA_NHA_TRO=nha_tro,
            TEN_KHU_VUC="Test Khu Vực",
            TRANG_THAI_KV="đang hoạt động",
            DV_HANH_CHINH_CAP1="Hồ Chí Minh",
            DV_HANH_CHINH_CAP2="Quận 1",
            DV_HANH_CHINH_CAP3="Phường Bến Nghé",
            VI_DO=10.7769,
            KINH_DO=106.7009
        )
        
        # Test save
        test_khu_vuc.save()
        print(f"✅ Test KhuVuc created successfully with ID: {test_khu_vuc.MA_KHU_VUC}")
        print(f"   DIEM_TOA_DO: {test_khu_vuc.DIEM_TOA_DO}")
        
        # Cleanup test data
        test_khu_vuc.delete()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing KhuVuc creation: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing DIEM_TOA_DO field issue...")
    print("=" * 50)
    
    # Fix field type
    if fix_diem_toa_do_field():
        print("\n🧪 Testing KhuVuc creation...")
        print("=" * 50)
        
        # Test creation
        if test_khu_vuc_creation():
            print("\n🎉 All issues fixed successfully!")
        else:
            print("\n❌ Test failed, there might be other issues")
    else:
        print("\n❌ Failed to fix field type")
        
    print("\n" + "=" * 50)