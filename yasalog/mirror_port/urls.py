from django.urls import path
from . import views

app_name = 'mirror_port'

urlpatterns = [
    # Dashboard
    path('dashboard/<str:company_slug>/', views.mirror_dashboard, name='dashboard'),
    
    # Konfigürasyon
    path('configurations/<str:company_slug>/', views.configurations_list, name='configurations_list'),
    path('configuration/add/<str:company_slug>/', views.configuration_add, name='configuration_add'),
    path('configuration/<str:company_slug>/<int:config_id>/', views.configuration_detail, name='configuration_detail'),
    
    # VLAN yönetimi
    path('vlans/<str:company_slug>/', views.vlans_list, name='vlans_list'),
    path('vlan/add/<str:company_slug>/', views.vlan_add, name='vlan_add'),
    path('vlan/<str:company_slug>/<int:vlan_id>/', views.vlan_detail, name='vlan_detail'),
    path('vlan/<str:company_slug>/<int:vlan_id>/edit/', views.vlan_edit, name='vlan_edit'),
    path('vlan/<str:company_slug>/<int:vlan_id>/delete/', views.vlan_delete, name='vlan_delete'),
    
    # Trafik analizi
    path('traffic/<str:company_slug>/', views.traffic_analysis, name='traffic_analysis'),
    path('traffic/<str:company_slug>/<int:traffic_id>/', views.traffic_detail, name='traffic_detail'),
    
    # Cihaz yönetimi
    path('devices/<str:company_slug>/', views.devices_list, name='devices_list'),
    path('device/add/<str:company_slug>/', views.device_add, name='device_add'),
    path('device/<str:company_slug>/<int:device_id>/', views.device_detail, name='device_detail'),
    path('device/<str:company_slug>/<int:device_id>/edit/', views.device_edit, name='device_edit'),
    path('device/<str:company_slug>/<int:device_id>/delete/', views.device_delete, name='device_delete'),
    
    # API endpoints
    path('api/stats/<str:company_slug>/', views.api_mirror_stats, name='api_mirror_stats'),
]
