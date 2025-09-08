"""
Analytics Dashboard URL Yapılandırması
5651log platformunda AI destekli analizler için URL'ler
"""

from django.urls import path
from . import views

app_name = 'analytics_dashboard'

urlpatterns = [
    # Ana analiz dashboard
    path('dashboard/<str:company_slug>/', views.analytics_dashboard, name='dashboard'),
    
    # AI içgörüleri
    path('insights/<str:company_slug>/', views.ai_insights, name='ai_insights'),
    
    # Tahmin analizleri
    path('predictions/<str:company_slug>/', views.predictive_analytics, name='predictive_analytics'),
    
    # Kullanıcı davranış analizi
    path('user-behavior/<str:company_slug>/', views.user_behavior_analysis, name='user_behavior'),
    
    # AJAX endpoint'leri
    path('api/data/<str:company_slug>/', views.get_analytics_data, name='get_analytics_data'),
]
