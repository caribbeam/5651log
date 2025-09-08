"""
Gelişmiş Bildirim Sistemi Admin Yapılandırması
5651 Loglama için kapsamlı bildirim sistemi
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    NotificationChannel, NotificationTemplate, NotificationRule, 
    NotificationLog, NotificationSubscription
)


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    """Bildirim kanalı admin"""
    list_display = [
        'name', 'company', 'channel_type', 'is_active', 'priority', 'created_at'
    ]
    list_filter = [
        'channel_type', 'is_active', 'test_mode', 'created_at'
    ]
    search_fields = ['name', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'channel_type', 'is_active', 'priority')
        }),
        ('E-posta Ayarları', {
            'fields': (
                'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
                'smtp_use_tls', 'from_email'
            ),
            'classes': ('collapse',)
        }),
        ('SMS Ayarları', {
            'fields': (
                'sms_provider', 'sms_api_key', 'sms_api_secret', 'sms_sender_id'
            ),
            'classes': ('collapse',)
        }),
        ('Webhook Ayarları', {
            'fields': ('webhook_url', 'webhook_secret', 'webhook_headers'),
            'classes': ('collapse',)
        }),
        ('Slack Ayarları', {
            'fields': ('slack_webhook_url', 'slack_channel', 'slack_username'),
            'classes': ('collapse',)
        }),
        ('Teams Ayarları', {
            'fields': ('teams_webhook_url',),
            'classes': ('collapse',)
        }),
        ('Telegram Ayarları', {
            'fields': ('telegram_bot_token', 'telegram_chat_id'),
            'classes': ('collapse',)
        }),
        ('Discord Ayarları', {
            'fields': ('discord_webhook_url',),
            'classes': ('collapse',)
        }),
        ('Test Ayarları', {
            'fields': ('test_mode', 'test_recipients'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Bildirim şablonu admin"""
    list_display = [
        'name', 'company', 'template_type', 'is_active', 'is_default', 'created_at'
    ]
    list_filter = [
        'template_type', 'is_active', 'is_default', 'created_at'
    ]
    search_fields = ['name', 'description', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'template_type', 'description', 'is_active', 'is_default')
        }),
        ('E-posta Şablonu', {
            'fields': ('email_subject', 'email_body_html', 'email_body_text'),
            'classes': ('collapse',)
        }),
        ('SMS Şablonu', {
            'fields': ('sms_message',),
            'classes': ('collapse',)
        }),
        ('Push Bildirim Şablonu', {
            'fields': ('push_title', 'push_body', 'push_icon'),
            'classes': ('collapse',)
        }),
        ('Webhook Şablonu', {
            'fields': ('webhook_payload',),
            'classes': ('collapse',)
        }),
        ('Slack Şablonu', {
            'fields': ('slack_message', 'slack_color'),
            'classes': ('collapse',)
        }),
        ('Teams Şablonu', {
            'fields': ('teams_title', 'teams_message'),
            'classes': ('collapse',)
        }),
        ('Telegram Şablonu', {
            'fields': ('telegram_message', 'telegram_parse_mode'),
            'classes': ('collapse',)
        }),
        ('Discord Şablonu', {
            'fields': ('discord_embed',),
            'classes': ('collapse',)
        }),
        ('Değişkenler', {
            'fields': ('available_variables',),
            'classes': ('collapse',)
        }),
        ('Meta Bilgiler', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')


@admin.register(NotificationRule)
class NotificationRuleAdmin(admin.ModelAdmin):
    """Bildirim kuralı admin"""
    list_display = [
        'name', 'company', 'trigger_type', 'is_active', 'trigger_count',
        'last_triggered', 'created_at'
    ]
    list_filter = [
        'trigger_type', 'is_active', 'last_triggered', 'created_at'
    ]
    search_fields = ['name', 'description', 'company__name']
    readonly_fields = ['last_triggered', 'trigger_count', 'created_at', 'updated_at']
    filter_horizontal = ['channels']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'description', 'is_active')
        }),
        ('Tetikleme Ayarları', {
            'fields': (
                'trigger_type', 'trigger_condition', 'threshold_value', 'time_window'
            )
        }),
        ('Filtreleme', {
            'fields': ('filter_conditions', 'severity_levels'),
            'classes': ('collapse',)
        }),
        ('Bildirim Ayarları', {
            'fields': ('channels', 'template', 'recipients')
        }),
        ('Zamanlama', {
            'fields': ('schedule_cron', 'schedule_timezone'),
            'classes': ('collapse',)
        }),
        ('Sınırlamalar', {
            'fields': (
                'max_notifications_per_hour', 'max_notifications_per_day', 'cooldown_period'
            ),
            'classes': ('collapse',)
        }),
        ('İstatistikler', {
            'fields': ('last_triggered', 'trigger_count'),
            'classes': ('collapse',)
        }),
        ('Meta Bilgiler', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'template', 'created_by')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Bildirim logu admin"""
    list_display = [
        'recipient', 'rule', 'channel', 'status', 'sent_at', 'created_at'
    ]
    list_filter = [
        'status', 'channel__channel_type', 'created_at', 'sent_at'
    ]
    search_fields = ['recipient', 'subject', 'message', 'rule__name', 'channel__name']
    readonly_fields = [
        'created_at', 'sent_at', 'delivered_at', 'retry_count'
    ]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('rule', 'channel', 'template', 'recipient')
        }),
        ('Mesaj İçeriği', {
            'fields': ('subject', 'message')
        }),
        ('Durum', {
            'fields': ('status', 'error_message')
        }),
        ('Zaman Bilgileri', {
            'fields': ('scheduled_at', 'sent_at', 'delivered_at', 'created_at')
        }),
        ('Meta Veriler', {
            'fields': ('metadata', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'rule', 'channel', 'template', 'rule__company'
        )
    
    def has_add_permission(self, request):
        return False  # Loglar sadece sistem tarafından oluşturulur
    
    def has_change_permission(self, request, obj=None):
        return False  # Loglar değiştirilemez


@admin.register(NotificationSubscription)
class NotificationSubscriptionAdmin(admin.ModelAdmin):
    """Bildirim aboneliği admin"""
    list_display = [
        'user', 'company', 'email_enabled', 'sms_enabled', 'push_enabled',
        'security_alerts', 'system_alerts', 'created_at'
    ]
    list_filter = [
        'email_enabled', 'sms_enabled', 'push_enabled', 'security_alerts',
        'system_alerts', 'report_notifications', 'maintenance_notifications',
        'created_at'
    ]
    search_fields = ['user__username', 'user__email', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'user')
        }),
        ('Kanal Tercihleri', {
            'fields': ('email_enabled', 'sms_enabled', 'push_enabled')
        }),
        ('Bildirim Tercihleri', {
            'fields': (
                'security_alerts', 'system_alerts', 'report_notifications',
                'maintenance_notifications'
            )
        }),
        ('Zaman Tercihleri', {
            'fields': ('quiet_hours_start', 'quiet_hours_end', 'timezone'),
            'classes': ('collapse',)
        }),
        ('Sıklık Sınırları', {
            'fields': ('max_daily_notifications', 'max_weekly_notifications'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'user')
