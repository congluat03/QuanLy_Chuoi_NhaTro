"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.dungchung import views as viewsDungChung
from apps.dungchung import admin_views as admin_views

urlpatterns = [ 
    path('', viewsDungChung.trang_chu, name='home'),
    path('admin', admin_views.dashboard, name='admin'),
    path('/', include(('apps.dungchung.urls', 'dungchung'), namespace='index')),
    
    path('admin/', include(('apps.dichvu.urls', 'dichvu'), namespace='admin_dichvu')),
    path('admin/', include(('apps.hoadon.urls', 'hoadon'), namespace='admin_hoadon')),
    path('admin/', include(('apps.hopdong.urls', 'hopdong'), namespace='admin_hopdong')),
    path('admin/', include(('apps.khachthue.urls', 'khachthue'), namespace='admin_khachthue')),
    path('admin/', include(('apps.nhatro.urls', 'nhatro'), namespace='admin_nhatro')),
    path('admin/', include(('apps.phongtro.urls', 'phongtro'), namespace='admin_phongtro')),
    path('admin/', include(('apps.thanhvien.urls', 'thanhvien'), namespace='admin_thanhvien')),
]
