from django.urls import path
from . import views

app_name = 'alarm_integration'

urlpatterns = [
    # Dashboard
    path('dashboard/<str:company_slug>/', views.dashboard, name='dashboard'),
    
    # Rule yönetimi
    path('rules/<str:company_slug>/', views.rules_list, name='rules_list'),
    path('rule/add/<str:company_slug>/', views.rule_add, name='rule_add'),
    path('rule/<str:company_slug>/<int:rule_id>/', views.rule_detail, name='rule_detail'),
    path('rule/<str:company_slug>/<int:rule_id>/edit/', views.rule_edit, name='rule_edit'),
    path('rule/<str:company_slug>/<int:rule_id>/delete/', views.rule_delete, name='rule_delete'),
    path('rule/<str:company_slug>/<int:rule_id>/test/', views.rule_test, name='rule_test'),
    
    # Event yönetimi
    path('events/<str:company_slug>/', views.events_list, name='events_list'),
    path('event/<str:company_slug>/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<str:company_slug>/<int:event_id>/acknowledge/', views.event_acknowledge, name='event_acknowledge'),
    path('event/<str:company_slug>/<int:event_id>/resolve/', views.event_resolve, name='event_resolve'),
    
    # Notification yönetimi
    path('notifications/<str:company_slug>/', views.notifications_list, name='notifications_list'),
    path('notification/<str:company_slug>/<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('notification/<str:company_slug>/<int:notification_id>/resend/', views.notification_resend, name='notification_resend'),
    
    # Suppression yönetimi
    path('suppressions/<str:company_slug>/', views.suppressions_list, name='suppressions_list'),
    path('suppression/add/<str:company_slug>/', views.suppression_add, name='suppression_add'),
    path('suppression/<str:company_slug>/<int:suppression_id>/edit/', views.suppression_edit, name='suppression_edit'),
    path('suppression/<str:company_slug>/<int:suppression_id>/delete/', views.suppression_delete, name='suppression_delete'),
    
    # Statistics
    path('statistics/<str:company_slug>/', views.statistics, name='statistics'),
    
    # API endpoints
    path('api/trigger/<str:company_slug>/<int:rule_id>/', views.api_trigger_alarm, name='api_trigger_alarm'),
    path('api/status/<str:company_slug>/', views.api_alarm_status, name='api_alarm_status'),
    path('api/notifications/<str:company_slug>/<int:event_id>/', views.api_send_notifications, name='api_send_notifications'),
]
