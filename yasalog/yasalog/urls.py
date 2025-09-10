"""yasalog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from log_kayit.views import giris_view
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('set_language/', set_language, name='set_language'),
    
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('giris/', giris_view, name='giris'),
    path('', include('log_kayit.urls')),  # log_kayit uygulamasının URL'leri
    
    # API URL'leri
    path('api/', include('api.urls')),
    
    # API Dokümantasyon
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Network Monitoring modülü URL'leri
    path('network/', include('network_monitoring.urls')),
    
    # Firewall Management modülü URL'leri
    path('firewall/', include('firewall_management.urls')),
    
    # Security Alerts modülü URL'leri
    path('security/', include('security_alerts.urls')),
    
    # Hotspot Management modülü URL'leri
    path('hotspot/', include('hotspot_management.urls')),
    
    # VPN Monitoring modülü URL'leri
    path('vpn/', include('vpn_monitoring.urls')),
    
    # Device Integrations modülü URL'leri
    path('device/', include('device_integrations.urls')),
    
    # Analytics Dashboard modülü URL'leri
    path('analytics/', include('analytics_dashboard.urls')),
    
    # Alert System modülü URL'leri
    path('alerts/', include('alert_system.urls')),
    
    # Profile Management modülü URL'leri
    path('profiles/', include('profile_management.urls')),
    
    # 5651 Compliance Modules
    # Timestamp Signing modülü URL'leri
    path('timestamp/', include('timestamp_signing.urls')),
    
    # Mirror Port modülü URL'leri
    path('mirror/', include('mirror_port.urls')),
    
    # Syslog Server modülü URL'leri
    path('syslog/', include('syslog_server.urls')),
    
    # Advanced Reporting modülü URL'leri
    path('reports/', include('advanced_reporting.urls')),
    
    # Notification System modülü URL'leri
    path('notifications/', include('notification_system.urls')),
    
    # 5651 High Priority Modules
    # Log Flow Monitoring modülü URL'leri
    path('log-flow/', include('log_flow_monitoring.urls')),
    
    # Log Verification modülü URL'leri
    path('log-verification/', include('log_verification.urls')),
    
    # Evidence Reports modülü URL'leri
    path('evidence/', include('evidence_reports.urls')),
    
    # Archiving Policy modülü URL'leri
    path('archiving/', include('archiving_policy.urls')),
    
    # Alarm Integration modülü URL'leri
    path('alarms/', include('alarm_integration.urls')),
    
    # Audit Logging modülü URL'leri
    path('audit/', include('audit_logging.urls')),
    
    # Two Factor Auth modülü URL'leri
    path('2fa/', include('two_factor_auth.urls')),
    
    # Şifre sıfırlama ve belirleme (frontend'e taşındı)
    # path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('cikis/', auth_views.LogoutView.as_view(next_page='/yonetici/login/'), name='logout'),
    prefix_default_language=False
)

# Device Management URL'leri - company_slug ile
urlpatterns += [
    # path('device/dashboard/<str:company_slug>/', include('device_integrations.urls')),
    # path('devices-simple/', include('device_integrations.urls_simple')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
