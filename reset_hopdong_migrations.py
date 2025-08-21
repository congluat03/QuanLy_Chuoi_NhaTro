#!/usr/bin/env python
"""
Script to reset hopdong app migrations
Run this if you encounter migration dependency errors
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    try:
        django.setup()
        
        # Fake apply the initial migration
        print("Faking migration state for hopdong app...")
        execute_from_command_line([
            'manage.py', 'migrate', 'hopdong', '0001', '--fake'
        ])
        print("✅ Migration state reset successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTry running manually:")
        print("python manage.py migrate hopdong 0001 --fake")
        print("python manage.py showmigrations hopdong")
        
    sys.exit(0)