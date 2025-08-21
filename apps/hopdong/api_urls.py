"""
URL routing cho API Hợp đồng
"""
from django.urls import path
from . import api_views

app_name = 'hopdong_api'

urlpatterns = [
    # API Workflow hợp đồng
    path('workflow/<str:action>/', api_views.HopDongWorkflowAPI.as_view(), name='workflow'),
    
    # API Báo cáo
    path('reports/<str:report_type>/', api_views.hop_dong_reports_api, name='reports'),
    
    # API Tác vụ tự động
    path('schedule/<str:action>/', api_views.hop_dong_schedule_api, name='schedule'),
]