from django.contrib import admin
from .models import MirrorConfiguration, VLANConfiguration, MirrorTraffic, MirrorDevice, MirrorLog


@admin.register(MirrorConfiguration)
class MirrorConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'config_type', 'is_active', 'is_enabled', 'created_at']
    list_filter = ['config_type', 'is_active', 'is_enabled', 'company', 'created_at']
    search_fields = ['name', 'source_ports', 'destination_port']
    readonly_fields = ['created_at', 'updated_at']
    
    # Sadece görüntüleme - ekleme/düzenleme frontend'de
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'config_type', 'is_active', 'is_enabled')
        }),
        ('Kaynak Ayarları', {
            'fields': ('source_ports', 'source_vlans')
        }),
        ('Hedef Ayarları', {
            'fields': ('destination_port', 'destination_ip')
        }),
        ('Filtreleme', {
            'fields': ('direction', 'protocol_filter'),
            'classes': ('collapse',)
        }),
        ('Performans', {
            'fields': ('max_bandwidth', 'buffer_size'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VLANConfiguration)
class VLANConfigurationAdmin(admin.ModelAdmin):
    list_display = ['vlan_id', 'name', 'company', 'subnet', 'mirror_enabled', 'is_active']
    list_filter = ['mirror_enabled', 'is_active', 'company']
    search_fields = ['name', 'vlan_id', 'subnet']
    readonly_fields = ['created_at', 'updated_at']
    
    # Sadece görüntüleme - ekleme/düzenleme frontend'de
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'vlan_id', 'name', 'description', 'is_active')
        }),
        ('Network Ayarları', {
            'fields': ('subnet', 'gateway', 'dns_servers')
        }),
        ('Mirror Ayarları', {
            'fields': ('mirror_enabled', 'mirror_config')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MirrorTraffic)
class MirrorTrafficAdmin(admin.ModelAdmin):
    list_display = ['source_ip', 'destination_ip', 'protocol', 'company', 'is_suspicious', 'timestamp']
    list_filter = ['protocol', 'is_suspicious', 'threat_level', 'company', 'timestamp']
    search_fields = ['source_ip', 'destination_ip', 'url']
    readonly_fields = ['timestamp', 'total_bytes', 'bandwidth_usage']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'mirror_config', 'vlan', 'timestamp')
        }),
        ('Trafik Bilgileri', {
            'fields': ('source_ip', 'destination_ip', 'source_port', 'destination_port', 'protocol')
        }),
        ('Veri Transfer', {
            'fields': ('bytes_sent', 'bytes_received', 'packets_sent', 'packets_received', 'total_bytes')
        }),
        ('Zaman Bilgileri', {
            'fields': ('start_time', 'end_time', 'duration', 'bandwidth_usage')
        }),
        ('Ek Bilgiler', {
            'fields': ('user_agent', 'url', 'content_type'),
            'classes': ('collapse',)
        }),
        ('Analiz', {
            'fields': ('is_suspicious', 'threat_level'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MirrorDevice)
class MirrorDeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'device_type', 'ip_address', 'is_online', 'last_seen']
    list_filter = ['device_type', 'is_online', 'mirror_supported', 'company']
    search_fields = ['name', 'ip_address', 'model', 'manufacturer']
    readonly_fields = ['created_at', 'updated_at', 'last_seen']
    
    # Sadece görüntüleme - ekleme/düzenleme frontend'de
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'device_type', 'is_online', 'last_seen')
        }),
        ('Network Bilgileri', {
            'fields': ('ip_address', 'mac_address')
        }),
        ('Cihaz Bilgileri', {
            'fields': ('model', 'manufacturer')
        }),
        ('Mirror Ayarları', {
            'fields': ('mirror_supported', 'max_mirror_ports', 'current_mirror_ports')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MirrorLog)
class MirrorLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'company', 'log_type', 'traffic_volume', 'timestamp']
    list_filter = ['log_type', 'company', 'timestamp']
    search_fields = ['message', 'device__name']
    readonly_fields = ['timestamp', 'details']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'device', 'log_type', 'message', 'timestamp')
        }),
        ('Performans Bilgileri', {
            'fields': ('traffic_volume', 'packet_count', 'duration')
        }),
        ('Detaylar', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Loglar otomatik oluşturulur
