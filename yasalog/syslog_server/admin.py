from django.contrib import admin
from .models import SyslogServer, SyslogMessage, SyslogClient, SyslogFilter, SyslogAlert, SyslogStatistics


@admin.register(SyslogServer)
class SyslogServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'host', 'port', 'protocol', 'is_active', 'is_running']
    list_filter = ['protocol', 'is_active', 'is_running', 'use_tls', 'company']
    search_fields = ['name', 'host', 'api_endpoint']
    readonly_fields = ['created_at', 'updated_at', 'total_logs_received', 'total_connections', 'last_activity']
    
    # Sadece görüntüleme - ekleme/düzenleme frontend'de
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'host', 'port', 'protocol', 'is_active', 'is_running')
        }),
        ('Güvenlik Ayarları', {
            'fields': ('use_tls', 'certificate_path', 'private_key_path'),
            'classes': ('collapse',)
        }),
        ('Filtreleme', {
            'fields': ('allowed_facilities', 'allowed_priorities'),
            'classes': ('collapse',)
        }),
        ('Performans', {
            'fields': ('max_connections', 'buffer_size', 'batch_size'),
            'classes': ('collapse',)
        }),
        ('İstatistikler', {
            'fields': ('total_logs_received', 'total_connections', 'last_activity'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyslogMessage)
class SyslogMessageAdmin(admin.ModelAdmin):
    list_display = ['hostname', 'program', 'facility', 'priority', 'company', 'is_suspicious', 'timestamp']
    list_filter = ['facility', 'priority', 'is_suspicious', 'threat_level', 'company', 'timestamp']
    search_fields = ['hostname', 'program', 'message', 'source_ip']
    readonly_fields = ['received_at', 'parsed_data']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'server', 'timestamp', 'received_at')
        }),
        ('Syslog Bilgileri', {
            'fields': ('facility', 'priority', 'severity', 'hostname', 'program', 'pid')
        }),
        ('Mesaj İçeriği', {
            'fields': ('message', 'raw_message')
        }),
        ('Network Bilgileri', {
            'fields': ('source_ip', 'source_port'),
            'classes': ('collapse',)
        }),
        ('Analiz', {
            'fields': ('is_parsed', 'parsed_data', 'is_suspicious', 'threat_level'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyslogClient)
class SyslogClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'client_type', 'ip_address', 'is_active', 'is_online', 'last_seen']
    list_filter = ['client_type', 'is_active', 'is_online', 'company']
    search_fields = ['name', 'ip_address', 'hostname', 'mac_address']
    readonly_fields = ['created_at', 'updated_at', 'total_messages_sent', 'last_message_at', 'last_seen']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'client_type', 'is_active', 'is_online', 'last_seen')
        }),
        ('Network Bilgileri', {
            'fields': ('ip_address', 'mac_address', 'hostname')
        }),
        ('Konfigürasyon', {
            'fields': ('syslog_server', 'facility', 'priority')
        }),
        ('İstatistikler', {
            'fields': ('total_messages_sent', 'last_message_at'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyslogFilter)
class SyslogFilterAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'filter_type', 'action', 'priority', 'is_active']
    list_filter = ['filter_type', 'action', 'is_active', 'company']
    search_fields = ['name', 'filter_value', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'filter_type', 'filter_value', 'description', 'is_active')
        }),
        ('Aksiyon ve Öncelik', {
            'fields': ('action', 'priority')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyslogAlert)
class SyslogAlertAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'alert_type', 'is_active', 'last_triggered', 'trigger_count']
    list_filter = ['alert_type', 'is_active', 'notify_email', 'notify_sms', 'company']
    search_fields = ['name', 'condition', 'notification_recipients']
    readonly_fields = ['created_at', 'updated_at', 'last_triggered', 'trigger_count']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'alert_type', 'is_active')
        }),
        ('Uyarı Koşulları', {
            'fields': ('condition', 'threshold_value', 'time_window')
        }),
        ('Bildirim Ayarları', {
            'fields': ('notify_email', 'notify_sms', 'notification_recipients')
        }),
        ('İstatistikler', {
            'fields': ('last_triggered', 'trigger_count'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SyslogStatistics)
class SyslogStatisticsAdmin(admin.ModelAdmin):
    list_display = ['server', 'company', 'date', 'hour', 'total_messages', 'error_count']
    list_filter = ['company', 'date', 'server']
    search_fields = ['server__name', 'company__name']
    readonly_fields = ['created_at', 'messages_by_facility', 'messages_by_priority', 'messages_by_hostname']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'server', 'date', 'hour', 'created_at')
        }),
        ('İstatistikler', {
            'fields': ('total_messages', 'messages_by_facility', 'messages_by_priority', 'messages_by_hostname')
        }),
        ('Performans', {
            'fields': ('avg_processing_time', 'max_processing_time', 'error_count'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # İstatistikler otomatik oluşturulur
