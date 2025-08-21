#!/usr/bin/env python
"""
Script test API Hợp đồng
Chạy: python test_hopdong_api.py
"""
import requests
import json
from datetime import datetime, date, timedelta

# Base URL của API
BASE_URL = 'http://localhost:8000/api/hopdong'

def test_api_endpoint(endpoint, method='GET', data=None):
    """Test một API endpoint"""
    url = f"{BASE_URL}/{endpoint}/"
    
    print(f"\n{'='*60}")
    print(f"Testing: {method} {url}")
    print(f"Data: {json.dumps(data, indent=2, default=str) if data else 'None'}")
    print('='*60)
    
    try:
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=data)
        else:
            response = requests.request(method, url, json=data)
        
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print("Response:")
            print(json.dumps(response_data, indent=2, default=str, ensure_ascii=False))
        except:
            print("Response (raw):")
            print(response.text)
        
        return response.status_code, response_data if 'response_data' in locals() else response.text
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Không thể kết nối đến server. Hãy chắc chắn Django server đang chạy.")
        return None, None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None, None

def test_workflow_apis():
    """Test các API workflow"""
    print("\n🔄 TESTING WORKFLOW APIs")
    
    # Test data mẫu cho tạo hợp đồng
    contract_data = {
        'MA_PHONG': 1,
        'MA_KHACH_THUE': 1,
        'NGAY_LAP_HD': (date.today()).isoformat(),
        'NGAY_NHAN_PHONG': (date.today() + timedelta(days=1)).isoformat(),
        'NGAY_TRA_PHONG': (date.today() + timedelta(days=365)).isoformat(),
        'THOI_HAN_HD': '12 tháng',
        'GIA_THUE': 3000000,
        'NGAY_THU_TIEN': '5',
        'CHU_KY_THANH_TOAN': 'Hàng tháng',
        'SO_THANH_VIEN_TOI_DA': 2,
        'GIA_COC_HD': 3000000,
        'HO_TEN_KT': 'Nguyễn Văn Test',
        'SDT_KT': '0123456789',
        'NGAY_SINH_KT': '1990-01-01',
        'GIOI_TINH_KT': 'Nam',
        'TAI_KHOAN': 'testuser',
        'MAT_KHAU': 'password123'
    }
    
    # 1. Lập hợp đồng mới
    test_api_endpoint('workflow/lap_hop_dong_moi', 'POST', contract_data)
    
    # 2. Xác nhận hợp đồng (giả sử hợp đồng có ID = 1)
    test_api_endpoint('workflow/xac_nhan_hop_dong', 'POST', {'ma_hop_dong': 1})
    
    # 3. Sinh hóa đơn hàng tháng
    test_api_endpoint('workflow/sinh_hoa_don_hang_thang', 'POST', {
        'thang': datetime.now().month,
        'nam': datetime.now().year
    })
    
    # 4. Gia hạn hợp đồng
    test_api_endpoint('workflow/gia_han_hop_dong', 'POST', {
        'ma_hop_dong': 1,
        'ngay_tra_phong_moi': (date.today() + timedelta(days=730)).isoformat(),
        'thoi_han_moi': '24 tháng'
    })
    
    # 5. Báo kết thúc sớm
    test_api_endpoint('workflow/bao_ket_thuc_som', 'POST', {
        'ma_hop_dong': 1,
        'ngay_bao_ket_thuc': (date.today() + timedelta(days=30)).isoformat(),
        'ly_do': 'Khách thuê chuyển công tác'
    })
    
    # 6. Kết thúc hợp đồng
    test_api_endpoint('workflow/ket_thuc_hop_dong', 'POST', {
        'ma_hop_dong': 1,
        'ngay_ket_thuc': date.today().isoformat()
    })

def test_report_apis():
    """Test các API báo cáo"""
    print("\n📊 TESTING REPORT APIs")
    
    # 1. Thống kê trạng thái
    test_api_endpoint('reports/thong_ke_trang_thai', 'GET')
    
    # 2. Hợp đồng sắp hết hạn
    test_api_endpoint('reports/sap_het_han?so_ngay=30', 'GET')
    
    # 3. Báo cáo doanh thu
    test_api_endpoint(f'reports/doanh_thu?thang={datetime.now().month}&nam={datetime.now().year}', 'GET')

def test_schedule_apis():
    """Test các API tác vụ tự động"""
    print("\n⏰ TESTING SCHEDULE APIs")
    
    # 1. Cập nhật trạng thái
    test_api_endpoint('schedule/cap_nhat_trang_thai', 'POST')
    
    # 2. Sinh hóa đơn tự động
    test_api_endpoint('schedule/sinh_hoa_don_tu_dong', 'POST', {'ngay_sinh': 1})

def test_invalid_endpoints():
    """Test các endpoint không hợp lệ"""
    print("\n❌ TESTING INVALID ENDPOINTS")
    
    # Test endpoint không tồn tại
    test_api_endpoint('workflow/invalid_action', 'POST', {})
    test_api_endpoint('reports/invalid_report', 'GET')
    test_api_endpoint('schedule/invalid_schedule', 'POST', {})

def main():
    """Hàm chính"""
    print("🚀 STARTING API TESTS FOR HỢP ĐỒNG WORKFLOW")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    
    # Kiểm tra kết nối cơ bản
    print("\n🔍 CHECKING CONNECTION...")
    status, _ = test_api_endpoint('reports/thong_ke_trang_thai', 'GET')
    
    if status is None:
        print("❌ Không thể kết nối đến server. Vui lòng:")
        print("   1. Chắc chắn Django server đang chạy (python manage.py runserver)")
        print("   2. Kiểm tra URL trong BASE_URL")
        print("   3. Cài đặt APScheduler: pip install APScheduler==3.10.4")
        return
    
    # Chạy các test
    try:
        test_workflow_apis()
        test_report_apis() 
        test_schedule_apis()
        test_invalid_endpoints()
        
        print("\n✅ TESTING COMPLETED!")
        print("\n📝 NOTES:")
        print("   - Một số API có thể fail nếu chưa có dữ liệu test")
        print("   - Hãy tạo dữ liệu mẫu trước khi test workflow")
        print("   - Kiểm tra logs Django để xem chi tiết lỗi")
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()