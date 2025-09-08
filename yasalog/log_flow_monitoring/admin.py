from django.contrib import admin
from .models import LogFlowMonitor, LogFlowAlert, LogFlowStatistics


@admin.register(LogFlowMonitor)
class LogFlowMonitorAdmin(admin.ModelAdmin):
    list_display = ['name', 'monitor_type', 'status', 'is_receiving_logs', 'last_log_received', 'company']
    list_filter = ['monitor_type', 'status', 'is_active', 'company']
    search_fields = ['name', 'source_device', 'source_ip']
    readonly_fields = ['total_logs_received', 'logs_per_minute', 'average_log_size', 'last_log_received', 'last_heartbeat']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'monitor_type', 'description')
        }),
        ('İzleme Ayarları', {
            'fields': ('source_device', 'source_ip', 'source_port')
        }),
        ('Eşik Değerleri', {
            'fields': ('warning_threshold_minutes', 'error_threshold_minutes')
        }),
        ('Bildirim Ayarları', {
            'fields': ('notify_on_warning', 'notify_on_error', 'notification_recipients')
        }),
        ('İstatistikler', {
            'fields': ('total_logs_received', 'logs_per_minute', 'average_log_size', 'last_log_received', 'last_heartbeat'),
            'classes': ('collapse',)
        }),
        ('Durum', {
            'fields': ('is_active', 'status', 'is_receiving_logs')
        })
    )


@admin.register(LogFlowAlert)
class LogFlowAlertAdmin(admin.ModelAdmin):
    list_display = ['monitor', 'alert_type', 'severity', 'detected_at', 'is_acknowledged', 'is_resolved']
    list_filter = ['alert_type', 'severity', 'is_acknowledged', 'is_resolved', 'monitor__company']
    search_fields = ['monitor__name', 'title', 'message']
    readonly_fields = ['detected_at', 'acknowledged_at', 'resolved_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('monitor', 'alert_type', 'severity', 'title', 'message')
        }),
        ('Detaylar', {
            'fields': ('details',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('detected_at', 'acknowledged_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Durum', {
            'fields': ('is_acknowledged', 'is_resolved', 'notification_sent')
        })
    )


@admin.register(LogFlowStatistics)
class LogFlowStatisticsAdmin(admin.ModelAdmin):
    list_display = ['monitor', 'date', 'hour', 'total_logs', 'uptime_minutes', 'downtime_minutes']
    list_filter = ['date', 'monitor__company', 'monitor']
    search_fields = ['monitor__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'monitor', 'date', 'hour')
        }),
        ('İstatistikler', {
            'fields': ('total_logs', 'total_bytes', 'average_log_size', 'peak_logs_per_minute')
        }),
        ('Durum Bilgileri', {
            'fields': ('uptime_minutes', 'downtime_minutes', 'alert_count')
        })
    )
