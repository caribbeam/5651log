from django.urls import path
from . import views

app_name = 'syslog_server'

urlpatterns = [
    # Dashboard
    path('dashboard/<str:company_slug>/', views.syslog_dashboard, name='dashboard'),
    
    # Sunucu yönetimi
    path('servers/<str:company_slug>/', views.servers_list, name='servers_list'),
    path('server/add/<str:company_slug>/', views.server_add, name='server_add'),
    path('server/<str:company_slug>/<int:server_id>/', views.server_detail, name='server_detail'),
    
    # İstemci yönetimi
    path('clients/<str:company_slug>/', views.clients_list, name='clients_list'),
    path('client/add/<str:company_slug>/', views.client_add, name='client_add'),
    path('client/<str:company_slug>/<int:client_id>/', views.client_detail, name='client_detail'),
    
    # Mesaj yönetimi
    path('messages/<str:company_slug>/', views.messages_list, name='messages_list'),
    path('message/<str:company_slug>/<int:message_id>/', views.message_detail, name='message_detail'),
    
    # Filtre yönetimi
    path('filters/<str:company_slug>/', views.filters_list, name='filters_list'),
    path('filter/add/<str:company_slug>/', views.filter_add, name='filter_add'),
    path('filter/<str:company_slug>/<int:filter_id>/', views.filter_detail, name='filter_detail'),
    
    # Uyarı yönetimi
    path('alerts/<str:company_slug>/', views.alerts_list, name='alerts_list'),
    path('alert/add/<str:company_slug>/', views.alert_add, name='alert_add'),
    path('alert/<str:company_slug>/<int:alert_id>/', views.alert_detail, name='alert_detail'),
    
    # İstatistikler
    path('statistics/<str:company_slug>/', views.statistics, name='statistics'),
    
    # API endpoints
    path('api/stats/<str:company_slug>/', views.api_syslog_stats, name='api_syslog_stats'),
    path('api/messages/<str:company_slug>/', views.api_messages, name='api_messages'),
]
