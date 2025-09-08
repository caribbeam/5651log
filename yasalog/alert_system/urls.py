"""
Alert System URL Yapılandırması
5651log platformunda gerçek zamanlı uyarılar için URL'ler
"""

from django.urls import path
from . import views

app_name = 'alert_system'

urlpatterns = [
    # Ana uyarı dashboard
    path('dashboard/<str:company_slug>/', views.alert_dashboard, name='dashboard'),
    
    # Uyarı kuralları yönetimi
    path('rules/<str:company_slug>/', views.alert_rules, name='alert_rules'),
    
    # Uyarı geçmişi
    path('history/<str:company_slug>/', views.alert_history, name='alert_history'),
    
    # Uyarı bildirimleri yönetimi
    path('notifications/<str:company_slug>/', views.alert_notifications, name='notifications'),
    
    # AJAX endpoint'leri
    path('api/data/<str:company_slug>/', views.get_alerts_data, name='get_alerts_data'),
]
