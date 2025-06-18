
from django.contrib import admin
from django.urls import path, include
from apps.dungchung import views as viewsDungChung
from apps.dungchung import admin_views as admin_views
from django.conf import settings
from django.conf.urls.static import static
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
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
