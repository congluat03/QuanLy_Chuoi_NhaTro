from django.urls import path
from . import views, admin_views

app_name = 'hoadon'
urlpatterns = [
    path('hoadon', admin_views.hoadon_list, name='hoadon_list'),
]