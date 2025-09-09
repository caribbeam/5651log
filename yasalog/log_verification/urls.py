from django.urls import path
from . import views

app_name = 'log_verification'

urlpatterns = [
    # Dashboard
    path('dashboard/<str:company_slug>/', views.dashboard, name='dashboard'),
    
    # Verification session yönetimi
    path('sessions/<str:company_slug>/', views.sessions_list, name='sessions_list'),
    path('session/add/<str:company_slug>/', views.session_add, name='session_add'),
    path('session/<str:company_slug>/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<str:company_slug>/<int:session_id>/start/', views.session_start, name='session_start'),
    path('session/<str:company_slug>/<int:session_id>/cancel/', views.session_cancel, name='session_cancel'),
    
    # Verification results
    path('results/<str:company_slug>/<int:session_id>/', views.results_list, name='results_list'),
    path('result/<str:company_slug>/<int:result_id>/', views.result_detail, name='result_detail'),
    
    # Reports
    path('reports/<str:company_slug>/<int:session_id>/', views.reports_list, name='reports_list'),
    path('report/create/<str:company_slug>/<int:session_id>/', views.report_create, name='report_create'),
    path('report/<str:company_slug>/<int:report_id>/', views.report_detail, name='report_detail'),
    path('report/<str:company_slug>/<int:report_id>/download/', views.report_download, name='report_download'),
    
    # Templates
    path('templates/<str:company_slug>/', views.templates_list, name='templates_list'),
    path('template/add/<str:company_slug>/', views.template_add, name='template_add'),
    path('template/<str:company_slug>/<int:template_id>/edit/', views.template_edit, name='template_edit'),
    path('template/<str:company_slug>/<int:template_id>/delete/', views.template_delete, name='template_delete'),
    
    # API endpoints
    path('api/verify/<str:company_slug>/<int:session_id>/', views.api_verify, name='api_verify'),
    path('api/progress/<str:company_slug>/<int:session_id>/', views.api_progress, name='api_progress'),
]
