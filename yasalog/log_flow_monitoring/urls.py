from django.urls import path
from . import views

app_name = 'log_flow_monitoring'

urlpatterns = [
    # Dashboard
    path('dashboard/<str:company_slug>/', views.dashboard, name='dashboard'),
    
    # Monitor yönetimi
    path('monitors/<str:company_slug>/', views.monitors_list, name='monitors_list'),
    path('monitor/add/<str:company_slug>/', views.monitor_add, name='monitor_add'),
    path('monitor/<str:company_slug>/<int:monitor_id>/', views.monitor_detail, name='monitor_detail'),
    path('monitor/<str:company_slug>/<int:monitor_id>/edit/', views.monitor_edit, name='monitor_edit'),
    path('monitor/<str:company_slug>/<int:monitor_id>/delete/', views.monitor_delete, name='monitor_delete'),
    
    # Alert yönetimi
    path('alerts/<str:company_slug>/', views.alerts_list, name='alerts_list'),
    path('alert/<str:company_slug>/<int:alert_id>/', views.alert_detail, name='alert_detail'),
    path('alert/<str:company_slug>/<int:alert_id>/acknowledge/', views.alert_acknowledge, name='alert_acknowledge'),
    path('alert/<str:company_slug>/<int:alert_id>/resolve/', views.alert_resolve, name='alert_resolve'),
    
    # İstatistikler
    path('statistics/<str:company_slug>/', views.statistics, name='statistics'),
    
    # API endpoints
    path('api/monitor/<str:company_slug>/<int:monitor_id>/heartbeat/', views.api_heartbeat, name='api_heartbeat'),
    path('api/monitor/<str:company_slug>/<int:monitor_id>/log/', views.api_log_received, name='api_log_received'),
    path('api/status/<str:company_slug>/', views.api_status, name='api_status'),
]
