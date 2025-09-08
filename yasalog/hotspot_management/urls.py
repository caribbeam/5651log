from django.urls import path
from . import views

app_name = 'hotspot_management'

urlpatterns = [
    path('dashboard/<str:company_slug>/', views.hotspot_dashboard, name='hotspot_dashboard'),
    path('configurations/<str:company_slug>/', views.hotspot_configurations, name='configurations_list'),
    path('configurations/<str:company_slug>/add/', views.configuration_add, name='configuration_add'),
    path('configurations/<str:company_slug>/<int:config_id>/', views.configuration_detail, name='configuration_detail'),
    path('configurations/<str:company_slug>/<int:config_id>/edit/', views.configuration_edit, name='configuration_edit'),
    path('configurations/<str:company_slug>/<int:config_id>/delete/', views.configuration_delete, name='configuration_delete'),
    path('users/<str:company_slug>/', views.users_list, name='users_list'),
    path('users/<str:company_slug>/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/toggle-block/', views.toggle_user_block, name='toggle_user_block'),
    path('sessions/<str:company_slug>/', views.sessions_list, name='sessions_list'),
    path('sessions/<str:company_slug>/add/', views.session_add, name='session_add'),
    path('sessions/<str:company_slug>/<int:session_id>/edit/', views.session_edit, name='session_edit'),
    path('sessions/<str:company_slug>/<int:session_id>/delete/', views.session_delete, name='session_delete'),
    path('content-filters/<str:company_slug>/', views.content_filters, name='content_filters'),
    path('content-filters/<str:company_slug>/add/', views.content_filter_add, name='content_filter_add'),
    path('content-filters/<str:company_slug>/<int:filter_id>/edit/', views.content_filter_edit, name='content_filter_edit'),
    path('content-filters/<str:company_slug>/<int:filter_id>/delete/', views.content_filter_delete, name='content_filter_delete'),
    path('access-logs/<str:company_slug>/', views.access_logs, name='access_logs'),
    path('access-logs/<str:company_slug>/add/', views.access_log_add, name='access_log_add'),
    path('access-logs/<str:company_slug>/<int:log_id>/edit/', views.access_log_edit, name='access_log_edit'),
    path('access-logs/<str:company_slug>/<int:log_id>/delete/', views.access_log_delete, name='access_log_delete'),
    path('api/stats/<str:company_slug>/', views.api_hotspot_stats, name='api_hotspot_stats'),
]
