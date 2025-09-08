from django.urls import path
from . import views

app_name = 'security_alerts'

urlpatterns = [
    # Ana dashboard
    path('dashboard/<str:company_slug>/', views.security_dashboard, name='security_dashboard'),
    
    # Tehdit yönetimi
    path('threats/<str:company_slug>/', views.threats_list, name='threats_list'),
    path('threats/<str:company_slug>/<int:threat_id>/', views.threat_detail, name='threat_detail'),
    
    # Uyarı yönetimi
    path('alerts/<str:company_slug>/', views.alerts_list, name='alerts_list'),
    
    # Olay yönetimi
    path('incidents/<str:company_slug>/', views.incidents_list, name='incidents_list'),
    
    # Tehdit istihbaratı
    path('intelligence/<str:company_slug>/', views.threat_intelligence, name='threat_intelligence'),
    
    # API endpoints
    path('api/stats/<str:company_slug>/', views.api_security_stats, name='api_security_stats'),
]
