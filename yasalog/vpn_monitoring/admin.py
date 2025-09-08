"""
VPN Monitoring Admin
5651log platformunda VPN monitoring modellerini admin panelinde yönetir
"""

from django.contrib import admin
from .models import VPNProject, VPNConnection, VPNUserActivity, VPNServerStatus

@admin.register(VPNProject)
class VPNProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'vpn_protocol', 'vpn_server_ip', 'is_active', 'created_at']
    list_filter = ['is_active', 'vpn_protocol', 'created_at']
    search_fields = ['name', 'vpn_server_ip', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'description', 'vpn_protocol', 'vpn_server_ip', 'vpn_server_port')
        }),
        ('Durum Bilgileri', {
            'fields': ('is_active',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(VPNConnection)
class VPNConnectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'vpn_ip', 'real_ip', 'status', 'connected_at', 'duration']
    list_filter = ['status', 'project', 'connected_at']
    search_fields = ['user__username', 'vpn_ip', 'real_ip', 'project__name']
    readonly_fields = ['connected_at', 'disconnected_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Bağlantı Bilgileri', {
            'fields': ('user', 'project', 'connection_id', 'status')
        }),
        ('IP Adresleri', {
            'fields': ('vpn_ip', 'real_ip', 'local_ip')
        }),
        ('Zaman Bilgileri', {
            'fields': ('connected_at', 'disconnected_at', 'duration')
        }),
        ('Bandwidth', {
            'fields': ('bandwidth_in', 'bandwidth_out', 'packets_in', 'packets_out')
        }),
        ('Hata Bilgileri', {
            'fields': ('error_message', 'disconnect_reason')
        }),
        ('Metadata', {
            'fields': ('user_agent', 'device_info', 'location_info')
        }),
        ('Sistem', {
            'fields': ('created_at', 'updated_at')
        })
    )

@admin.register(VPNUserActivity)
class VPNUserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'activity_type', 'timestamp', 'ip_address']
    list_filter = ['activity_type', 'timestamp', 'project']
    search_fields = ['user__username', 'project__name', 'description', 'ip_address']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Aktivite Bilgileri', {
            'fields': ('user', 'project', 'connection', 'activity_type', 'description')
        }),
        ('Teknik Detaylar', {
            'fields': ('ip_address', 'timestamp', 'metadata')
        })
    )

@admin.register(VPNServerStatus)
class VPNServerStatusAdmin(admin.ModelAdmin):
    list_display = ['project', 'status', 'cpu_usage', 'memory_usage', 'timestamp']
    list_filter = ['status', 'timestamp']
    search_fields = ['project__name']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Sunucu Durumu', {
            'fields': ('project', 'status', 'timestamp')
        }),
        ('Sistem Metrikleri', {
            'fields': ('cpu_usage', 'memory_usage')
        })
    )

# Admin panel başlığını özelleştir
admin.site.site_header = "5651log VPN Monitoring Yönetimi"
admin.site.site_title = "VPN Monitoring Admin"
admin.site.index_title = "VPN Monitoring Modülü"
