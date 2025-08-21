#!/usr/bin/env python3
"""
Test script để kiểm tra timezone import
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from apps.hopdong.models import HopDong

def test_timezone_import():
    """Test xem timezone có hoạt động không"""
    try:
        # Test timezone.now()
        now = timezone.now()
        print(f"✅ timezone.now() hoạt động: {now}")
        
        # Test timezone trong models
        from apps.hopdong.models import timezone as model_timezone
        print(f"✅ timezone import trong models hoạt động")
        
        print("🎉 Tất cả timezone imports đều OK!")
        
    except Exception as e:
        print(f"❌ Lỗi timezone: {e}")

if __name__ == "__main__":
    test_timezone_import()