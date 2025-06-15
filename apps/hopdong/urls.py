from django.urls import path
from . import views, admin_views

app_name = 'hopdong'
urlpatterns = [
    path('hopdong', admin_views.hopdong_list, name='hopdong_list'),
]