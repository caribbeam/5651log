from django.contrib import admin
from .models import NetworkDevice, NetworkLog, NetworkTraffic

@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'device_type', 'ip_address', 'status', 'cpu_usage', 'memory_usage', 'last_seen']
    list_filter = ['company', 'device_type', 'status', 'created_at']
    search_fields = ['name', 'ip_address', 'mac_address', 'model']
    readonly_fields = ['created_at', 'updated_at', 'last_seen']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'device_type', 'ip_address', 'mac_address')
        }),
        ('Cihaz Detayları', {
            'fields': ('model', 'manufacturer', 'firmware_version', 'serial_number')
        }),
        ('Network Bilgileri', {
            'fields': ('subnet_mask', 'gateway')
        }),
        ('Durum Bilgileri', {
            'fields': ('status', 'cpu_usage', 'memory_usage', 'temperature', 'uptime')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at', 'last_seen'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')

@admin.register(NetworkLog)
class NetworkLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'company', 'log_type', 'level', 'message_short', 'timestamp']
    list_filter = ['company', 'device', 'log_type', 'level', 'timestamp']
    search_fields = ['message', 'source_ip', 'destination_ip']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'device', 'log_type', 'level', 'message')
        }),
        ('Network Bilgileri', {
            'fields': ('source_ip', 'destination_ip', 'source_port', 'destination_port', 'protocol')
        }),
        ('Ek Bilgiler', {
            'fields': ('bytes_transferred', 'duration')
        }),
        ('Zaman', {
            'fields': ('timestamp',)
        }),
    )
    
    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Mesaj'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'device')

@admin.register(NetworkTraffic)
class NetworkTrafficAdmin(admin.ModelAdmin):
    list_display = ['device', 'company', 'source_ip', 'destination_ip', 'protocol', 'total_bytes_display', 'start_time']
    list_filter = ['company', 'device', 'protocol', 'start_time']
    search_fields = ['source_ip', 'destination_ip', 'application']
    readonly_fields = ['start_time', 'end_time', 'duration']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'device', 'source_ip', 'destination_ip', 'protocol')
        }),
        ('Port Bilgileri', {
            'fields': ('source_port', 'destination_port')
        }),
        ('Veri Transfer', {
            'fields': ('bytes_sent', 'bytes_received', 'packets_sent', 'packets_received')
        }),
        ('Zaman Bilgileri', {
            'fields': ('start_time', 'end_time', 'duration')
        }),
        ('Uygulama Bilgileri', {
            'fields': ('application', 'user_agent')
        }),
    )
    
    def total_bytes_display(self, obj):
        return f"{obj.total_bytes:,} bytes"
    total_bytes_display.short_description = 'Toplam Veri'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'device')
