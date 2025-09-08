from django.urls import path
from . import views

app_name = 'network_monitoring'

urlpatterns = [
    # Ana dashboard
    path('dashboard/<slug:company_slug>/', views.network_dashboard, name='network_dashboard'),
    path('dashboard/<int:company_id>/', views.network_dashboard, name='network_dashboard_id'),
    
    # Frontend arayüzü - Cihaz yönetimi
    path('devices/<slug:company_slug>/', views.device_list, name='device_list'),
    path('devices/<slug:company_slug>/add/', views.device_add, name='device_add'),
    path('devices/<slug:company_slug>/<int:device_id>/edit/', views.device_edit, name='device_edit'),
    path('devices/<slug:company_slug>/<int:device_id>/delete/', views.device_delete, name='device_delete'),
    
    # Cihaz detay
    path('device/<int:device_id>/', views.device_detail, name='device_detail'),
    
    # API endpoints
    path('api/device/<int:device_id>/status/', views.device_status_api, name='device_status_api'),
]
