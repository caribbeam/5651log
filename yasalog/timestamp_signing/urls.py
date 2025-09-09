from django.urls import path
from . import views
from . import api_views

app_name = 'timestamp_signing'

urlpatterns = [
    # Dashboard
    path('dashboard/<str:company_slug>/', views.timestamp_dashboard, name='dashboard'),
    
    # İmza yönetimi
    path('signatures/<str:company_slug>/', views.signatures_list, name='signatures_list'),
    path('signature/<str:company_slug>/<int:signature_id>/', views.signature_detail, name='signature_detail'),
    path('verify/<str:company_slug>/<int:signature_id>/', views.verify_signature, name='verify_signature'),
    
    # Toplu işlemler
    path('batch-sign/<str:company_slug>/', views.batch_sign, name='batch_sign'),
    
    # Konfigürasyon
    path('configuration/<str:company_slug>/', views.configuration, name='configuration'),
    path('authorities/<str:company_slug>/', views.authority_management, name='authority_management'),
    
    # API endpoints
    path('api/stats/<str:company_slug>/', views.api_signature_stats, name='api_signature_stats'),
    
    # TSA API endpoints
    path('api/timestamp/', api_views.TSAAPIView.as_view(), name='tsa_api'),
    path('api/verify/', api_views.verify_timestamp, name='tsa_verify'),
]
