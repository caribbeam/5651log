from django.urls import path
from . import views

app_name = 'audit_logging'

urlpatterns = [
    path('dashboard/<slug:company_slug>/', views.audit_dashboard, name='dashboard'),
    path('logs/<slug:company_slug>/', views.audit_logs_list, name='logs_list'),
    path('log/<slug:company_slug>/<int:log_id>/', views.audit_log_detail, name='log_detail'),
    path('config/<slug:company_slug>/', views.audit_config, name='config'),
    path('reports/<slug:company_slug>/', views.audit_reports, name='reports'),
    path('statistics/<slug:company_slug>/', views.audit_statistics, name='statistics'),
]
