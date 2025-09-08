from django.urls import path
from . import views

urlpatterns = [
    # Ana device dashboard - company_slug ile
    path('', views.device_dashboard_simple, name='device_dashboard_simple'),
    path('<str:company_slug>/', views.device_dashboard_simple, name='device_dashboard_simple_with_slug'),

    # Device detail sayfaları
    path('mikrotik/', views.mikrotik_devices, name='mikrotik_devices'),
    path('vmware/', views.vmware_devices, name='vmware_devices'),
    path('proxmox/', views.proxmox_devices, name='proxmox_devices'),
    path('cisco/', views.cisco_devices, name='cisco_devices'),

    # Test sayfaları
    path('test/', views.test_integrations, name='test_integrations'),
]
