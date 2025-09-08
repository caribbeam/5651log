from django.contrib import admin
from .models import AlarmRule, AlarmEvent, AlarmNotification, AlarmSuppression, AlarmStatistics


@admin.register(AlarmRule)
class AlarmRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'alarm_type', 'severity', 'is_active', 'trigger_count', 'last_triggered', 'company']
    list_filter = ['alarm_type', 'severity', 'is_active', 'is_enabled', 'company']
    search_fields = ['name', 'description', 'condition']
    readonly_fields = ['trigger_count', 'last_triggered', 'last_notification_sent']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'description', 'alarm_type', 'severity')
        }),
        ('Kural Koşulları', {
            'fields': ('condition', 'threshold_value', 'time_window_minutes')
        }),
        ('Bildirim Ayarları', {
            'fields': ('notify_email', 'notify_sms', 'notify_webhook', 'notify_dashboard')
        }),
        ('Bildirim Alıcıları', {
            'fields': ('email_recipients', 'sms_recipients', 'webhook_url'),
            'classes': ('collapse',)
        }),
        ('Tekrar Bildirim', {
            'fields': ('repeat_notification', 'repeat_interval_minutes', 'max_repeat_count'),
            'classes': ('collapse',)
        }),
        ('Durum', {
            'fields': ('is_active', 'is_enabled')
        }),
        ('İstatistikler', {
            'fields': ('trigger_count', 'last_triggered', 'last_notification_sent'),
            'classes': ('collapse',)
        })
    )


@admin.register(AlarmEvent)
class AlarmEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'rule', 'severity', 'status', 'triggered_at', 'acknowledged_at', 'resolved_at']
    list_filter = ['severity', 'status', 'rule__company', 'triggered_at']
    search_fields = ['title', 'message', 'rule__name']
    readonly_fields = ['triggered_at', 'acknowledged_at', 'resolved_at', 'notifications_sent', 'last_notification_sent']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'rule', 'severity', 'title', 'message')
        }),
        ('Detaylar', {
            'fields': ('details',)
        }),
        ('Durum', {
            'fields': ('status',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('triggered_at', 'acknowledged_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Kullanıcı Bilgileri', {
            'fields': ('acknowledged_by', 'resolved_by'),
            'classes': ('collapse',)
        }),
        ('Bildirim Durumu', {
            'fields': ('notifications_sent', 'last_notification_sent'),
            'classes': ('collapse',)
        }),
        ('Notlar', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )


@admin.register(AlarmNotification)
class AlarmNotificationAdmin(admin.ModelAdmin):
    list_display = ['event', 'notification_type', 'recipient', 'status', 'created_at', 'sent_at']
    list_filter = ['notification_type', 'status', 'event__rule__company', 'created_at']
    search_fields = ['event__title', 'recipient', 'subject']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'retry_count']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('event', 'notification_type', 'recipient', 'subject', 'message')
        }),
        ('Durum', {
            'fields': ('status',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'sent_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
        ('Hata Bilgileri', {
            'fields': ('error_message', 'retry_count'),
            'classes': ('collapse',)
        })
    )


@admin.register(AlarmSuppression)
class AlarmSuppressionAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time', 'is_active', 'created_by', 'company']
    list_filter = ['is_active', 'company', 'start_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'description')
        }),
        ('Bastırma Koşulları', {
            'fields': ('alarm_types', 'severity_levels', 'source_devices')
        }),
        ('Zaman Ayarları', {
            'fields': ('start_time', 'end_time')
        }),
        ('Durum', {
            'fields': ('is_active', 'created_by', 'created_at')
        })
    )


@admin.register(AlarmStatistics)
class AlarmStatisticsAdmin(admin.ModelAdmin):
    list_display = ['company', 'date', 'total_alarms', 'critical_alarms', 'active_alarms', 'resolved_alarms']
    list_filter = ['date', 'company']
    search_fields = ['company__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'date')
        }),
        ('Alarm Sayıları', {
            'fields': ('total_alarms', 'critical_alarms', 'high_alarms', 'medium_alarms', 'low_alarms')
        }),
        ('Durum Sayıları', {
            'fields': ('active_alarms', 'acknowledged_alarms', 'resolved_alarms')
        }),
        ('Bildirim Sayıları', {
            'fields': ('total_notifications', 'successful_notifications', 'failed_notifications'),
            'classes': ('collapse',)
        }),
        ('Performans Metrikleri', {
            'fields': ('average_response_time_minutes', 'average_resolution_time_minutes'),
            'classes': ('collapse',)
        })
    )
