from django.urls import path
from . import views

app_name = 'firewall_management'

urlpatterns = [
    # Ana dashboard
    path('dashboard/<slug:company_slug>/', views.firewall_dashboard, name='firewall_dashboard'),
    path('dashboard/<int:company_id>/', views.firewall_dashboard, name='firewall_dashboard_id'),
    
    # Kurallar
    path('rules/<slug:company_slug>/', views.rules_list, name='rules_list'),
    path('rules/<slug:company_slug>/add/', views.rule_add, name='rule_add'),
    path('rules/<slug:company_slug>/<int:rule_id>/edit/', views.rule_edit, name='rule_edit'),
    path('rules/<slug:company_slug>/<int:rule_id>/delete/', views.rule_delete, name='rule_delete'),
    path('rule/<int:rule_id>/', views.rule_detail, name='rule_detail'),
    
    # Olaylar
    path('events/<slug:company_slug>/', views.events_list, name='events_list'),
    
    # Loglar
    path('logs/<slug:company_slug>/', views.logs_list, name='logs_list'),
    
    # API endpoints
    path('api/stats/<slug:company_slug>/', views.api_rule_stats, name='api_rule_stats'),
]
