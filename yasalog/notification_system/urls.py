"""
Gelişmiş Bildirim Sistemi URL Yapılandırması
5651 Loglama için kapsamlı bildirim sistemi
"""

from django.urls import path
from . import views

app_name = 'notification_system'

urlpatterns = [
    # Dashboard
    path('dashboard/<slug:company_slug>/', views.dashboard, name='dashboard'),
    
    # Bildirim Kanalları
    path('channels/<slug:company_slug>/', views.channels_list, name='channels_list'),
    path('channel/<slug:company_slug>/<int:channel_id>/', views.channel_detail, name='channel_detail'),
    path('channel/add/<slug:company_slug>/', views.channel_add, name='channel_add'),
    path('channel/edit/<slug:company_slug>/<int:channel_id>/', views.channel_edit, name='channel_edit'),
    path('channel/delete/<slug:company_slug>/<int:channel_id>/', views.delete_channel, name='delete_channel'),
    
    # Bildirim Şablonları
    path('templates/<slug:company_slug>/', views.templates_list, name='templates_list'),
    path('template/<slug:company_slug>/<int:template_id>/', views.template_detail, name='template_detail'),
    path('template/add/<slug:company_slug>/', views.template_add, name='template_add'),
    path('template/delete/<slug:company_slug>/<int:template_id>/', views.delete_template, name='delete_template'),
    
    # Bildirim Kuralları
    path('rules/<slug:company_slug>/', views.rules_list, name='rules_list'),
    path('rule/<slug:company_slug>/<int:rule_id>/', views.rule_detail, name='rule_detail'),
    path('rule/add/<slug:company_slug>/', views.rule_add, name='rule_add'),
    path('rule/delete/<slug:company_slug>/<int:rule_id>/', views.delete_rule, name='delete_rule'),
    path('rule/toggle/<slug:company_slug>/<int:rule_id>/', views.toggle_rule, name='toggle_rule'),
    
    # Bildirim Logları
    path('notifications/<slug:company_slug>/', views.notifications_list, name='notifications_list'),
    
    # Bildirim Abonelikleri
    path('subscriptions/<slug:company_slug>/', views.subscriptions_list, name='subscriptions_list'),
    path('subscription/<slug:company_slug>/<int:subscription_id>/', views.subscription_detail, name='subscription_detail'),
    
    # Test Bildirimi
    path('test/<slug:company_slug>/', views.test_notification, name='test_notification'),
    
    # API
    path('api/stats/<slug:company_slug>/', views.api_notification_stats, name='api_notification_stats'),
]
