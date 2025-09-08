from django.urls import path
from . import views

app_name = 'archiving_policy'

urlpatterns = [
    # Dashboard
    path('dashboard/<str:company_slug>/', views.dashboard, name='dashboard'),
    
    # Policy yönetimi
    path('policies/<str:company_slug>/', views.policies_list, name='policies_list'),
    path('policy/add/<str:company_slug>/', views.policy_add, name='policy_add'),
    path('policy/<str:company_slug>/<int:policy_id>/', views.policy_detail, name='policy_detail'),
    path('policy/<str:company_slug>/<int:policy_id>/edit/', views.policy_edit, name='policy_edit'),
    path('policy/<str:company_slug>/<int:policy_id>/delete/', views.policy_delete, name='policy_delete'),
    path('policy/<str:company_slug>/<int:policy_id>/execute/', views.policy_execute, name='policy_execute'),
    
    # Job yönetimi
    path('jobs/<str:company_slug>/', views.jobs_list, name='jobs_list'),
    path('job/<str:company_slug>/<int:job_id>/', views.job_detail, name='job_detail'),
    path('job/<str:company_slug>/<int:job_id>/cancel/', views.job_cancel, name='job_cancel'),
    
    # Storage yönetimi
    path('storage/<str:company_slug>/', views.storage_list, name='storage_list'),
    path('storage/add/<str:company_slug>/', views.storage_add, name='storage_add'),
    path('storage/<str:company_slug>/<int:storage_id>/', views.storage_detail, name='storage_detail'),
    path('storage/<str:company_slug>/<int:storage_id>/edit/', views.storage_edit, name='storage_edit'),
    path('storage/<str:company_slug>/<int:storage_id>/delete/', views.storage_delete, name='storage_delete'),
    
    # Logs
    path('logs/<str:company_slug>/', views.logs_list, name='logs_list'),
    
    # API endpoints
    path('api/execute/<str:company_slug>/<int:policy_id>/', views.api_execute_policy, name='api_execute_policy'),
    path('api/status/<str:company_slug>/<int:job_id>/', views.api_job_status, name='api_job_status'),
    path('api/storage/<str:company_slug>/<int:storage_id>/capacity/', views.api_storage_capacity, name='api_storage_capacity'),
]
