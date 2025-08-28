from django.urls import path
from . import views, admin_views

app_name = 'thanhvien'
urlpatterns = [
    path('quanly', admin_views.nhanvien_list, name='nhanvien_list'),
    path('quanly/them', admin_views.add_manager, name='add_manager'),
    path('quanly/sua/<int:ma_quan_ly>', admin_views.edit_manager, name='edit_manager'),
    path('quanly/delete/<int:ma_quan_ly>/', admin_views.delete_manager, name='delete_manager'),
    path('quanly/chuyen-khu-vuc/<int:ma_quan_ly>/', admin_views.transfer_manager_area, name='transfer_manager_area'),
]