from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'log_kayit'

urlpatterns = [
    # Ana sayfa
    path('', views.giris_view, name='home'),
    
    # Ana giriş (ziyaretçi)
    path('giris/<slug:company_slug>/', views.giris_view, name='giris_slug'),
    path('giris/<int:company_id>/', views.giris_view, name='giris_id'),
    path('giris/', views.giris_view, name='giris_default'),
    path('giris/cikis/<slug:company_slug>/', views.cikis_view, name='giris_cikis'),

    # Yönetici/Personel URL'leri
    path('yonetici/login/', auth_views.LoginView.as_view(template_name='log_kayit/yonetici_login.html'), name='yonetici_login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard URL'leri - ÖZEL'den GENEL'e doğru sıralanmalı
    path('dashboard/<slug:company_slug>/', views.company_dashboard, name='company_dashboard_slug'),
    path('dashboard/<int:company_id>/', views.company_dashboard, name='dashboard_id'),
    
    # Panel URL'leri - ÖZEL'den GENEL'e doğru sıralanmalı
    path('panel/kullanicilar/', views.user_management_view, name='user_management_view'),
    path('panel/ayarlar/', views.company_settings_panel, name='company_settings_panel'),
    path('panel/', views.company_user_panel, name='company_user_panel'), # Bu en sonda kalmalı
    
    # Şifre değiştirme
    path('password-change/<slug:company_slug>/', views.password_change_view, name='password_change'),
    
    # Şifre sıfırlama
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete_view, name='password_reset_complete'),
    
    # Gelişmiş Kullanıcı Yönetimi URL'leri - Company slug ile entegre
    path('users/dashboard/<slug:company_slug>/', views.user_management_dashboard, name='user_management_dashboard'),
    path('users/add/<slug:company_slug>/', views.add_user, name='add_user'),
    path('users/<int:user_id>/edit/<slug:company_slug>/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/permissions/<slug:company_slug>/', views.user_permissions, name='user_permissions'),
    path('users/<int:user_id>/logs/<slug:company_slug>/', views.user_activity_logs, name='user_activity_logs'),
    path('users/bulk-create/<slug:company_slug>/', views.bulk_user_creation, name='bulk_user_creation'),
    path('users/<int:user_id>/toggle-status/<slug:company_slug>/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/delete/<slug:company_slug>/', views.delete_user, name='delete_user'),

    # Dışa Aktarma URL'leri
    path('export/excel/<int:company_id>/', views.dashboard_export_excel, name='dashboard_export_excel'),
    path('export/pdf/<int:company_id>/', views.dashboard_export_pdf, name='dashboard_export_pdf'),
    path('export/zip/<int:company_id>/', views.dashboard_export_zip, name='dashboard_export_zip'),
    
    # Gelişmiş Analitik URL'leri
    path('analytics/<slug:company_slug>/', views.advanced_analytics, name='advanced_analytics'),
] 