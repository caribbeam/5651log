"""
VPN Monitoring URL Yapılandırması
5651log platformunda VPN monitoring için URL'ler
"""

from django.urls import path
from . import views

app_name = 'vpn_monitoring'

urlpatterns = [
    # Ana VPN dashboard
    path('dashboard/<str:company_slug>/', views.vpn_dashboard, name='vpn_dashboard'),
    
    # VPN bağlantıları
    path('connections/<str:company_slug>/', views.vpn_connections, name='vpn_connections'),
    
    # Kullanıcı aktiviteleri
    path('user-activity/<str:company_slug>/', views.vpn_user_activity, name='vpn_user_activity'),
    
    # Proje detayları
    path('project/<str:company_slug>/<int:project_id>/', views.vpn_project_detail, name='vpn_project_detail'),
    
    # AJAX endpoint'leri
    path('api/status/<str:company_slug>/', views.get_vpn_status, name='get_vpn_status'),
    path('api/active-connections/<str:company_slug>/', views.get_active_connections, name='get_active_connections'),
]
