#!/usr/bin/env python
"""
Script test Management Commands cho Hợp đồng
Chạy: python test_management_commands.py
"""
import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Chạy một command và hiển thị kết quả"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        # Chạy command
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=60  # Timeout 60 giây
        )
        
        print(f"Return Code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT: Command took too long to execute")
        return False
    except FileNotFoundError:
        print("❌ ERROR: python/python3 not found or manage.py not found")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_management_commands():
    """Test các management commands"""
    print("🚀 TESTING MANAGEMENT COMMANDS FOR HỢP ĐỒNG")
    print(f"Time: {datetime.now()}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Kiểm tra file manage.py
    if not os.path.exists('manage.py'):
        print("❌ ERROR: manage.py not found. Please run this script from Django project root.")
        return
    
    results = {}
    
    # 1. Test help command
    print("\n🔍 TESTING HELP COMMANDS...")
    results['help'] = run_command(
        'python manage.py help',
        'Django help command'
    )
    
    # 2. Test cập nhật hợp đồng hàng ngày
    print("\n📅 TESTING CẬP NHẬT HỢP ĐỒNG HÀNG NGÀY...")
    results['cap_nhat_help'] = run_command(
        'python manage.py help cap_nhat_hop_dong_hang_ngay',
        'Help for cap_nhat_hop_dong_hang_ngay'
    )
    
    results['cap_nhat_dry'] = run_command(
        'python manage.py cap_nhat_hop_dong_hang_ngay --dry-run',
        'Cập nhật hợp đồng hàng ngày (dry run)'
    )
    
    results['cap_nhat_real'] = run_command(
        'python manage.py cap_nhat_hop_dong_hang_ngay',
        'Cập nhật hợp đồng hàng ngày (thực tế)'
    )
    
    # 3. Test sinh hóa đơn hàng tháng
    print("\n💰 TESTING SINH HÓA ĐƠN HÀNG THÁNG...")
    results['sinh_hd_help'] = run_command(
        'python manage.py help sinh_hoa_don_hang_thang',
        'Help for sinh_hoa_don_hang_thang'
    )
    
    results['sinh_hd_dry'] = run_command(
        'python manage.py sinh_hoa_don_hang_thang --dry-run',
        'Sinh hóa đơn hàng tháng (dry run)'
    )
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    results['sinh_hd_month'] = run_command(
        f'python manage.py sinh_hoa_don_hang_thang --thang {current_month} --nam {current_year} --dry-run',
        f'Sinh hóa đơn tháng {current_month}/{current_year} (dry run)'
    )
    
    results['sinh_hd_real'] = run_command(
        f'python manage.py sinh_hoa_don_hang_thang --thang {current_month} --nam {current_year}',
        f'Sinh hóa đơn tháng {current_month}/{current_year} (thực tế)'
    )
    
    # 4. Test other Django commands để đảm bảo không conflict
    print("\n🔧 TESTING OTHER DJANGO COMMANDS...")
    results['check'] = run_command(
        'python manage.py check',
        'Django check command'
    )
    
    results['makemigrations_dry'] = run_command(
        'python manage.py makemigrations --dry-run',
        'Check for pending migrations'
    )
    
    # Tổng kết
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print('='*60)
    
    success_count = 0
    total_count = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if success:
            success_count += 1
    
    print(f"\nSUCCESS RATE: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n📝 NOTES:")
    print("   - Dry run commands should always pass")
    print("   - Real commands may fail if no data exists")
    print("   - Check Django logs for detailed error information")
    print("   - Make sure database is accessible and migrations are applied")

def check_environment():
    """Kiểm tra môi trường"""
    print("🔍 CHECKING ENVIRONMENT...")
    
    # Kiểm tra Python
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        print(f"Python version: {result.stdout.strip()}")
    except:
        try:
            result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
            print(f"Python version: {result.stdout.strip()}")
        except:
            print("❌ Python not found")
            return False
    
    # Kiểm tra Django
    try:
        result = subprocess.run(['python', '-m', 'django', '--version'], capture_output=True, text=True)
        print(f"Django version: {result.stdout.strip()}")
    except:
        print("❌ Django not found or not properly installed")
    
    # Kiểm tra manage.py
    if os.path.exists('manage.py'):
        print("✅ manage.py found")
    else:
        print("❌ manage.py not found")
        return False
    
    # Kiểm tra apps/hopdong
    if os.path.exists('apps/hopdong'):
        print("✅ apps/hopdong found")
    else:
        print("❌ apps/hopdong not found")
    
    return True

def main():
    """Hàm chính"""
    print("🧪 MANAGEMENT COMMANDS TESTING SCRIPT")
    print(f"Started at: {datetime.now()}")
    
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return 1
    
    try:
        test_management_commands()
        return 0
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)