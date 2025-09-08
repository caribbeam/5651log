from django.urls import path
from . import views

app_name = 'evidence_reports'

urlpatterns = [
    # Dashboard
    path('dashboard/<str:company_slug>/', views.dashboard, name='dashboard'),
    
    # Report yönetimi
    path('reports/<str:company_slug>/', views.reports_list, name='reports_list'),
    path('report/add/<str:company_slug>/', views.report_add, name='report_add'),
    path('report/<str:company_slug>/<int:report_id>/', views.report_detail, name='report_detail'),
    path('report/<str:company_slug>/<int:report_id>/edit/', views.report_edit, name='report_edit'),
    path('report/<str:company_slug>/<int:report_id>/approve/', views.report_approve, name='report_approve'),
    path('report/<str:company_slug>/<int:report_id>/generate/', views.report_generate, name='report_generate'),
    path('report/<str:company_slug>/<int:report_id>/download/', views.report_download, name='report_download'),
    path('report/<str:company_slug>/<int:report_id>/deliver/', views.report_deliver, name='report_deliver'),
    
    # Templates
    path('templates/<str:company_slug>/', views.templates_list, name='templates_list'),
    path('template/add/<str:company_slug>/', views.template_add, name='template_add'),
    path('template/<str:company_slug>/<int:template_id>/edit/', views.template_edit, name='template_edit'),
    path('template/<str:company_slug>/<int:template_id>/delete/', views.template_delete, name='template_delete'),
    
    # Access logs
    path('access-logs/<str:company_slug>/<int:report_id>/', views.access_logs_list, name='access_logs_list'),
    
    # API endpoints
    path('api/generate/<str:company_slug>/<int:report_id>/', views.api_generate_report, name='api_generate_report'),
    path('api/status/<str:company_slug>/<int:report_id>/', views.api_report_status, name='api_report_status'),
]
