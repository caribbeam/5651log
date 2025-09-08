from django.urls import path
from . import views

app_name = 'security_alerts'

urlpatterns = [
    # Ana dashboard
    path('dashboard/<str:company_slug>/', views.security_dashboard, name='security_dashboard'),
    
    # Tehdit yönetimi
    path('threats/<str:company_slug>/', views.threats_list, name='threats_list'),
    path('threats/<str:company_slug>/<int:threat_id>/', views.threat_detail, name='threat_detail'),
    path('threats/<int:threat_id>/update-status/', views.update_threat_status, name='update_threat_status'),
    path('threats/<int:threat_id>/assign/', views.assign_threat, name='assign_threat'),
    path('threats/<int:threat_id>/add-note/', views.add_threat_note, name='add_threat_note'),
    
    # Uyarı yönetimi
    path('alerts/<str:company_slug>/', views.alerts_list, name='alerts_list'),
    path('alerts/<int:alert_id>/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    
    # Olay yönetimi
    path('incidents/<str:company_slug>/', views.incidents_list, name='incidents_list'),
    
    # Tehdit istihbaratı
    path('intelligence/<str:company_slug>/', views.threat_intelligence, name='threat_intelligence'),
    
    # API endpoints
    path('api/stats/<str:company_slug>/', views.api_security_stats, name='api_security_stats'),
]
