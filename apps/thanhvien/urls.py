from django.urls import path
from . import views, admin_views

app_name = 'thanhvien'
urlpatterns = [
    path('thanhvien', admin_views.nhanvien_list, name='nhanvien_list'),
]