"""
Device Integrations Admin
5651log platformunda cihaz entegrasyonlarını admin panelinde yönetir
"""

from django.contrib import admin
from .models import Device, DeviceType, DeviceStatus, DeviceMetric

# Device model admin
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'device_type', 'ip_address', 'status', 'company', 'last_seen', 'created_at']
    list_filter = ['device_type', 'status', 'company', 'created_at', 'last_seen']
    search_fields = ['name', 'ip_address', 'description', 'company__name']
    readonly_fields = ['created_at', 'last_seen', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'description', 'device_type', 'ip_address', 'port', 'company')
        }),
        ('Durum Bilgileri', {
            'fields': ('status', 'last_seen', 'is_monitored', 'integration_type')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at')
        })
    )

# DeviceType model admin
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'model', 'category', 'is_active']
    list_filter = ['vendor', 'category', 'is_active']
    search_fields = ['name', 'vendor', 'model', 'description']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'vendor', 'model', 'category', 'description')
        }),
        ('Durum Bilgileri', {
            'fields': ('is_active',)
        })
    )

# DeviceStatus model admin
class DeviceStatusAdmin(admin.ModelAdmin):
    list_display = ['device', 'status', 'cpu_usage', 'memory_usage', 'disk_usage', 'bandwidth_in', 'timestamp']
    list_filter = ['status', 'timestamp', 'device__device_type']
    search_fields = ['device__name', 'device__ip_address']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Cihaz Bilgileri', {
            'fields': ('device', 'status')
        }),
        ('Performans Metrikleri', {
            'fields': ('cpu_usage', 'memory_usage', 'disk_usage', 'bandwidth_in', 'bandwidth_out')
        }),
        ('Zaman Bilgileri', {
            'fields': ('timestamp',)
        })
    )

# DeviceMetric model admin
class DeviceMetricAdmin(admin.ModelAdmin):
    list_display = ['device', 'metric_type', 'value', 'unit', 'is_alert', 'timestamp']
    list_filter = ['metric_type', 'timestamp', 'device__device_type']
    search_fields = ['device__name', 'metric_type']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Cihaz Bilgileri', {
            'fields': ('device', 'metric_type')
        }),
        ('Metrik Değerleri', {
            'fields': ('value', 'unit', 'is_alert')
        }),
        ('Zaman Bilgileri', {
            'fields': ('timestamp',)
        })
    )

# Admin'e modelleri kaydet
admin.site.register(Device, DeviceAdmin)
admin.site.register(DeviceType, DeviceTypeAdmin)
admin.site.register(DeviceStatus, DeviceStatusAdmin)
admin.site.register(DeviceMetric, DeviceMetricAdmin)

# Admin panel başlığını özelleştir
admin.site.site_header = "5651log Device Integrations Yönetimi"
admin.site.site_title = "Device Integrations Admin"
admin.site.index_title = "Cihaz Entegrasyonları Modülü"
