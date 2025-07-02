from django.urls import path
from . import views, admin_views

app_name = 'dungchung'
urlpatterns = [
    path('', views.trang_chu, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('profile/', admin_views.profile, name='profile'),
    path('logout/', admin_views.profile, name='logout'),
    path('doi-mat-khau/', admin_views.doi_mat_khau, name='doi_mat_khau'),
]