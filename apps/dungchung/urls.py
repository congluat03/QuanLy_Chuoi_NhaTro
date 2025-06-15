from django.urls import path
from . import views

app_name = 'dungchung'
urlpatterns = [
    path('', views.trang_chu, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.login_view, name='profile'),
    path('logout/', views.login_view, name='logout'),
]