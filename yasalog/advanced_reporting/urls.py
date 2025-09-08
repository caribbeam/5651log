"""
Gelişmiş Raporlama URL Yapılandırması
5651 Loglama için kapsamlı raporlama sistemi
"""

from django.urls import path
from . import views

app_name = 'advanced_reporting'

urlpatterns = [
    # Dashboard
    path('dashboard/<slug:company_slug>/', views.dashboard, name='dashboard'),
    
    # Rapor Şablonları
    path('templates/<slug:company_slug>/', views.templates_list, name='templates_list'),
    path('template/<slug:company_slug>/<int:template_id>/', views.template_detail, name='template_detail'),
    path('template/add/<slug:company_slug>/', views.template_add, name='template_add'),
    path('template/edit/<slug:company_slug>/<int:template_id>/', views.template_edit, name='template_edit'),
    path('template/delete/<slug:company_slug>/<int:template_id>/', views.delete_template, name='delete_template'),
    
    # Raporlar
    path('reports/<slug:company_slug>/', views.reports_list, name='reports_list'),
    path('report/<slug:company_slug>/<int:report_id>/', views.report_detail, name='report_detail'),
    path('report/download/<slug:company_slug>/<int:report_id>/', views.report_download, name='report_download'),
    path('report/delete/<slug:company_slug>/<int:report_id>/', views.delete_report, name='delete_report'),
    
    # Rapor Oluşturma
    path('generate/<slug:company_slug>/<int:template_id>/', views.generate_report, name='generate_report'),
    
    # Zamanlanmış Raporlar
    path('schedules/<slug:company_slug>/', views.schedules_list, name='schedules_list'),
    path('schedule/add/<slug:company_slug>/', views.schedule_add, name='schedule_add'),
    path('schedule/toggle/<slug:company_slug>/<int:schedule_id>/', views.toggle_schedule, name='toggle_schedule'),
    
    # Analitikler
    path('analytics/<slug:company_slug>/', views.analytics, name='analytics'),
    
    # API
    path('api/stats/<slug:company_slug>/', views.api_report_stats, name='api_report_stats'),
]
