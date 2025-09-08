from django.urls import path
from . import views

app_name = 'hotspot_management'

urlpatterns = [
    path('dashboard/<str:company_slug>/', views.hotspot_dashboard, name='hotspot_dashboard'),
    path('configurations/<str:company_slug>/', views.hotspot_configurations, name='configurations_list'),
    path('configurations/<str:company_slug>/<int:config_id>/', views.configuration_detail, name='configuration_detail'),
    path('users/<str:company_slug>/', views.users_list, name='users_list'),
    path('users/<str:company_slug>/<int:user_id>/', views.user_detail, name='user_detail'),
    path('sessions/<str:company_slug>/', views.sessions_list, name='sessions_list'),
    path('content-filters/<str:company_slug>/', views.content_filters, name='content_filters'),
    path('access-logs/<str:company_slug>/', views.access_logs, name='access_logs'),
    path('api/stats/<str:company_slug>/', views.api_hotspot_stats, name='api_hotspot_stats'),
]
