#!/usr/bin/env python
"""
Script khởi tạo dữ liệu mẫu cho test Hợp đồng Workflow
Chạy: python setup_test_data.py
"""
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import models sau khi setup Django
from apps.hopdong.models import HopDong, LichSuHopDong
from apps.phongtro.models import PhongTro, LoaiPhong, CocPhong
from apps.nhatro.models import NhaTro, KhuVuc
from apps.khachthue.models import KhachThue
from apps.thanhvien.models import TaiKhoan, NguoiQuanLy
from apps.hoadon.models import HoaDon

def create_sample_data():
    """Tạo dữ liệu mẫu"""
    print("🏗️  CREATING SAMPLE DATA FOR HỢP ĐỒNG WORKFLOW...")
    
    try:
        # 1. Tạo Người quản lý
        print("👤 Creating NguoiQuanLy...")
        tai_khoan_ql, created = TaiKhoan.objects.get_or_create(
            username='admin_test',
            defaults={
                'email': 'admin@test.com',
                'first_name': 'Admin',
                'last_name': 'Test'
            }
        )
        if created:
            tai_khoan_ql.set_password('admin123')
            tai_khoan_ql.save()
        
        nguoi_quan_ly, created = NguoiQuanLy.objects.get_or_create(
            MA_TAI_KHOAN=tai_khoan_ql,
            defaults={
                'HO_TEN_NQL': 'Nguyễn Văn Admin',
                'SDT_NQL': '0123456789',
                'EMAIL_NQL': 'admin@test.com'
            }
        )
        print(f"   ✅ NguoiQuanLy: {nguoi_quan_ly.HO_TEN_NQL}")
        
        # 2. Tạo Nhà trọ
        print("🏠 Creating NhaTro...")
        nha_tro, created = NhaTro.objects.get_or_create(
            TEN_NHA_TRO='Nhà trọ Test',
            defaults={
                'MA_QUAN_LY': nguoi_quan_ly,
                'VUNG_MIEN': 'Miền Nam'
            }
        )
        print(f"   ✅ NhaTro: {nha_tro.TEN_NHA_TRO}")
        
        # 3. Tạo Khu vực
        print("📍 Creating KhuVuc...")
        khu_vuc, created = KhuVuc.objects.get_or_create(
            TEN_KHU_VUC='Khu A - Test',
            defaults={
                'MA_NHA_TRO': nha_tro,
                'TRANG_THAI_KV': 'Đang hoạt động',
                'DV_HANH_CHINH_CAP1': 'TP. Hồ Chí Minh',
                'DV_HANH_CHINH_CAP2': 'Quận 1',
                'DV_HANH_CHINH_CAP3': 'Phường Bến Nghé',
                'DIA_CHI_CHI_TIET': '123 Nguyễn Huệ'
            }
        )
        print(f"   ✅ KhuVuc: {khu_vuc.TEN_KHU_VUC}")
        
        # 4. Tạo Loại phòng
        print("🏷️  Creating LoaiPhong...")
        loai_phong, created = LoaiPhong.objects.get_or_create(
            TEN_LOAI_PHONG='Phòng đơn',
            defaults={
                'MO_TA_LP': 'Phòng đơn giá rẻ, đầy đủ tiện nghi'
            }
        )
        print(f"   ✅ LoaiPhong: {loai_phong.TEN_LOAI_PHONG}")
        
        # 5. Tạo Phòng trọ
        print("🚪 Creating PhongTro...")
        phong_tro, created = PhongTro.objects.get_or_create(
            TEN_PHONG='A101',
            defaults={
                'MA_LOAI_PHONG': loai_phong,
                'MA_KHU_VUC': khu_vuc,
                'TRANG_THAI_P': 'Trống',
                'GIA_PHONG': Decimal('3000000'),
                'DIEN_TICH': Decimal('25.5'),
                'SO_NGUOI_TOI_DA': 2,
                'MO_TA_P': 'Phòng đơn 25m2, có gác lửng',
                'SO_TIEN_CAN_COC': Decimal('3000000')
            }
        )
        print(f"   ✅ PhongTro: {phong_tro.TEN_PHONG}")
        
        # 6. Tạo Tài khoản khách thuê
        print("👥 Creating KhachThue...")
        tai_khoan_kt, created = TaiKhoan.objects.get_or_create(
            username='khachthue_test',
            defaults={
                'email': 'khachthue@test.com',
                'first_name': 'Khách',
                'last_name': 'Test'
            }
        )
        if created:
            tai_khoan_kt.set_password('khach123')
            tai_khoan_kt.save()
        
        khach_thue, created = KhachThue.objects.get_or_create(
            MA_TAI_KHOAN=tai_khoan_kt,
            defaults={
                'HO_TEN_KT': 'Trần Thị Khách Thuê',
                'SDT_KT': '0987654321',
                'EMAIL_KT': 'khachthue@test.com',
                'NGAY_SINH_KT': date(1995, 5, 15),
                'GIOI_TINH_KT': 'Nữ',
                'DIA_CHI_KT': '456 Lê Lợi, Q1, TPHCM'
            }
        )
        print(f"   ✅ KhachThue: {khach_thue.HO_TEN_KT}")
        
        # 7. Tạo Cọc phòng
        print("💰 Creating CocPhong...")
        coc_phong, created = CocPhong.objects.get_or_create(
            MA_PHONG=phong_tro,
            MA_KHACH_THUE=khach_thue,
            defaults={
                'NGAY_COC_PHONG': date.today() - timedelta(days=5),
                'NGAY_DU_KIEN_VAO': date.today(),
                'TIEN_COC_PHONG': Decimal('3000000'),
                'TRANG_THAI_CP': 'Đã cọc',
                'NGUON_TAO': 'ADMIN',
                'GHI_CHU_CP': 'Test data'
            }
        )
        print(f"   ✅ CocPhong: {coc_phong.MA_COC_PHONG}")
        
        # 8. Tạo Hợp đồng mẫu
        print("📋 Creating HopDong...")
        hop_dong_data = {
            'MA_PHONG': phong_tro.MA_PHONG,
            'MA_KHACH_THUE': khach_thue.MA_KHACH_THUE,
            'NGAY_LAP_HD': date.today() - timedelta(days=3),
            'THOI_HAN_HD': '12 tháng',
            'NGAY_NHAN_PHONG': date.today(),
            'NGAY_TRA_PHONG': date.today() + timedelta(days=365),
            'SO_THANH_VIEN_TOI_DA': 2,
            'GIA_THUE': Decimal('3000000'),
            'NGAY_THU_TIEN': '5',
            'CHU_KY_THANH_TOAN': 'Hàng tháng',
            'GIA_COC_HD': Decimal('3000000'),
            'HO_TEN_KT': khach_thue.HO_TEN_KT,
            'SDT_KT': khach_thue.SDT_KT,
            'NGAY_SINH_KT': khach_thue.NGAY_SINH_KT,
            'GIOI_TINH_KT': khach_thue.GIOI_TINH_KT
        }
        
        # Kiểm tra xem đã có hợp đồng chưa
        existing_hop_dong = HopDong.objects.filter(
            MA_PHONG=phong_tro,
            TRANG_THAI_HD__in=['Chờ xác nhận', 'Đang hoạt động']
        ).first()
        
        if not existing_hop_dong:
            hop_dong = HopDong.tao_hop_dong(hop_dong_data)
            print(f"   ✅ HopDong: #{hop_dong.MA_HOP_DONG}")
        else:
            hop_dong = existing_hop_dong
            print(f"   ✅ HopDong (existing): #{hop_dong.MA_HOP_DONG}")
        
        # 9. Tạo thêm phòng và hợp đồng với trạng thái khác nhau
        print("🏠 Creating additional test data...")
        
        # Phòng A102 - Hợp đồng đang hoạt động
        phong_a102, created = PhongTro.objects.get_or_create(
            TEN_PHONG='A102',
            defaults={
                'MA_LOAI_PHONG': loai_phong,
                'MA_KHU_VUC': khu_vuc,
                'TRANG_THAI_P': 'Đang ở',
                'GIA_PHONG': Decimal('3200000'),
                'DIEN_TICH': Decimal('28.0'),
                'SO_NGUOI_TOI_DA': 2,
                'SO_TIEN_CAN_COC': Decimal('3200000')
            }
        )
        
        # Khách thuê thứ 2
        tai_khoan_kt2, created = TaiKhoan.objects.get_or_create(
            username='khachthue2_test',
            defaults={
                'email': 'khachthue2@test.com',
                'first_name': 'Khách2',
                'last_name': 'Test'
            }
        )
        if created:
            tai_khoan_kt2.set_password('khach123')
            tai_khoan_kt2.save()
        
        khach_thue2, created = KhachThue.objects.get_or_create(
            MA_TAI_KHOAN=tai_khoan_kt2,
            defaults={
                'HO_TEN_KT': 'Lê Văn Thuê',
                'SDT_KT': '0912345678',
                'EMAIL_KT': 'khachthue2@test.com',
                'NGAY_SINH_KT': date(1992, 8, 20),
                'GIOI_TINH_KT': 'Nam'
            }
        )
        
        # Hợp đồng đang hoạt động
        hop_dong_data2 = {
            'MA_PHONG': phong_a102.MA_PHONG,
            'MA_KHACH_THUE': khach_thue2.MA_KHACH_THUE,
            'NGAY_LAP_HD': date.today() - timedelta(days=30),
            'THOI_HAN_HD': '12 tháng',
            'NGAY_NHAN_PHONG': date.today() - timedelta(days=25),
            'NGAY_TRA_PHONG': date.today() + timedelta(days=340),
            'SO_THANH_VIEN_TOI_DA': 2,
            'GIA_THUE': Decimal('3200000'),
            'NGAY_THU_TIEN': '1',
            'CHU_KY_THANH_TOAN': 'Hàng tháng',
            'GIA_COC_HD': Decimal('3200000'),
            'HO_TEN_KT': khach_thue2.HO_TEN_KT,
            'SDT_KT': khach_thue2.SDT_KT,
            'NGAY_SINH_KT': khach_thue2.NGAY_SINH_KT,
            'GIOI_TINH_KT': khach_thue2.GIOI_TINH_KT
        }
        
        existing_hop_dong2 = HopDong.objects.filter(MA_PHONG=phong_a102).first()
        if not existing_hop_dong2:
            hop_dong2 = HopDong.tao_hop_dong(hop_dong_data2)
            # Xác nhận hợp đồng để có trạng thái "Đang hoạt động"
            hop_dong2.xac_nhan_hop_dong()
            print(f"   ✅ HopDong (active): #{hop_dong2.MA_HOP_DONG}")
        
        print("\n✅ SAMPLE DATA CREATED SUCCESSFULLY!")
        print("\n📊 SUMMARY:")
        print(f"   - NhaTro: {NhaTro.objects.count()}")
        print(f"   - KhuVuc: {KhuVuc.objects.count()}")
        print(f"   - PhongTro: {PhongTro.objects.count()}")
        print(f"   - KhachThue: {KhachThue.objects.count()}")
        print(f"   - HopDong: {HopDong.objects.count()}")
        print(f"   - CocPhong: {CocPhong.objects.count()}")
        print(f"   - HoaDon: {HoaDon.objects.count()}")
        
        print("\n🎯 READY FOR TESTING!")
        print("   Bạn có thể chạy các test script:")
        print("   - python test_hopdong_api.py")
        print("   - python test_management_commands.py")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Xóa dữ liệu test"""
    print("🧹 CLEANING UP TEST DATA...")
    
    try:
        # Xóa theo thứ tự phụ thuộc
        HoaDon.objects.filter(MA_PHONG__TEN_PHONG__startswith='A10').delete()
        LichSuHopDong.objects.filter(MA_HOP_DONG__MA_PHONG__TEN_PHONG__startswith='A10').delete()
        HopDong.objects.filter(MA_PHONG__TEN_PHONG__startswith='A10').delete()
        CocPhong.objects.filter(MA_PHONG__TEN_PHONG__startswith='A10').delete()
        PhongTro.objects.filter(TEN_PHONG__startswith='A10').delete()
        KhuVuc.objects.filter(TEN_KHU_VUC__contains='Test').delete()
        NhaTro.objects.filter(TEN_NHA_TRO__contains='Test').delete()
        
        # Xóa users test
        TaiKhoan.objects.filter(username__contains='test').delete()
        
        print("✅ Test data cleaned up!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR during cleanup: {str(e)}")
        return False

def main():
    """Hàm chính"""
    print("🎭 SAMPLE DATA SETUP FOR HỢP ĐỒNG WORKFLOW")
    print(f"Time: {date.today()}")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        return cleanup_test_data()
    else:
        return create_sample_data()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)