"""
Device Integrations URL Yapılandırması
5651log platformunda cihaz entegrasyonları için URL'ler
"""

from django.urls import path
from . import views

app_name = 'device_integrations'

urlpatterns = [
    # Ana cihaz dashboard
    path('dashboard/<str:company_slug>/', views.device_dashboard, name='device_dashboard'),
    
    # Cihaz CRUD işlemleri
    path('add/<str:company_slug>/', views.device_add, name='device_add'),
    path('edit/<str:company_slug>/<int:device_id>/', views.device_edit, name='device_edit'),
    path('delete/<str:company_slug>/<int:device_id>/', views.device_delete, name='device_delete'),
    path('view/<str:company_slug>/<int:device_id>/', views.device_view, name='device_view'),
    
    # Cihaz işlemleri
    path('refresh/<str:company_slug>/<int:device_id>/', views.device_refresh_status, name='device_refresh_status'),
    path('proxmox/<str:company_slug>/', views.proxmox_dashboard, name='proxmox_dashboard'),
    path('mikrotik/<str:company_slug>/', views.mikrotik_dashboard, name='mikrotik_dashboard'),
    
    # Cihaz detay sayfası (eski)
    path('device/<str:company_slug>/<int:device_id>/', views.device_detail, name='device_detail'),
    
    # Cihaz konfigürasyon sayfası
    path('config/<str:company_slug>/<int:device_id>/', views.device_configuration, name='device_configuration'),
    
    # Cihaz durum sayfası
    path('status/<str:company_slug>/<int:device_id>/', views.device_status, name='device_status'),
    
    # AJAX endpoint'leri
    path('api/status/<str:company_slug>/', views.get_device_status, name='get_device_status'),
    path('api/metrics/<str:company_slug>/<int:device_id>/', views.get_device_metrics, name='get_device_metrics'),
]
