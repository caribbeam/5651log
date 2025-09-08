"""
Profile Management URLs
5651log platformunda profil yönetimi için URL konfigürasyonu
"""

from django.urls import path
from . import views

app_name = 'profile_management'

urlpatterns = [
    # Ana dashboard
    path('dashboard/<str:company_slug>/', views.profile_dashboard, name='dashboard'),
    
    # Profil listesi
    path('profiles/<str:company_slug>/', views.profile_list, name='profile_list'),
    
    # Profil detay
    path('profile/<str:company_slug>/<int:profile_id>/', views.profile_detail, name='profile_detail'),
    
    # Profil oluşturma
    path('profile/create/<str:company_slug>/', views.profile_create, name='profile_create'),
    
    # Profil düzenleme
    path('profile/edit/<str:company_slug>/<int:profile_id>/', views.profile_edit, name='profile_edit'),
    
    # AJAX endpoint'leri
    path('api/profiles/<str:company_slug>/', views.get_profile_data, name='get_profile_data'),
]
