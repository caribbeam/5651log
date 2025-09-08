from django.contrib import admin
from .models import (
    HotspotConfiguration, BandwidthPolicy, HotspotUser, 
    UserSession, ContentFilter, AccessLog, HotspotMetrics
)


@admin.register(HotspotConfiguration)
class HotspotConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'ssid', 'company', 'max_bandwidth_mbps', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_public', 'enable_content_filtering', 'company', 'created_at']
    search_fields = ['name', 'ssid', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'ssid', 'password', 'is_public')
        }),
        ('Bant Genişliği Ayarları', {
            'fields': ('max_bandwidth_mbps', 'max_upload_mbps', 'max_download_mbps')
        }),
        ('Oturum Ayarları', {
            'fields': ('session_timeout_hours', 'max_concurrent_users')
        }),
        ('İçerik Filtreleme', {
            'fields': ('enable_content_filtering', 'block_adult_content', 'block_gambling', 'block_social_media')
        }),
        ('Zaman Kısıtlamaları', {
            'fields': ('start_time', 'end_time', 'is_24_7')
        }),
        ('Durum', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(BandwidthPolicy)
class BandwidthPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'policy_type', 'company', 'download_limit_mbps', 'upload_limit_mbps', 'daily_limit_gb', 'is_active']
    list_filter = ['policy_type', 'is_active', 'company', 'created_at']
    search_fields = ['name', 'company__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'policy_type')
        }),
        ('Bant Genişliği Limitleri', {
            'fields': ('download_limit_mbps', 'upload_limit_mbps', 'daily_limit_gb')
        }),
        ('Ayarlar', {
            'fields': ('priority', 'is_active', 'created_at')
        }),
    )


@admin.register(HotspotUser)
class HotspotUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'user_type', 'company', 'hotspot', 'mac_address', 'ip_address', 'is_active', 'is_blocked']
    list_filter = ['user_type', 'is_active', 'is_blocked', 'company', 'hotspot', 'created_at']
    search_fields = ['username', 'email', 'mac_address', 'ip_address', 'company__name']
    readonly_fields = ['created_at', 'last_login']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'hotspot', 'bandwidth_policy')
        }),
        ('Kullanıcı Bilgileri', {
            'fields': ('username', 'email', 'phone', 'user_type')
        }),
        ('Ağ Bilgileri', {
            'fields': ('mac_address', 'ip_address', 'device_info')
        }),
        ('Durum', {
            'fields': ('is_active', 'is_blocked', 'created_at', 'last_login')
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'hotspot', 'session_id', 'status', 'start_time', 'duration_minutes', 'total_bytes']
    list_filter = ['status', 'hotspot', 'start_time']
    search_fields = ['session_id', 'user__username', 'hotspot__name']
    readonly_fields = ['start_time', 'end_time', 'bytes_uploaded', 'bytes_downloaded', 'total_bytes', 'duration_minutes']
    
    fieldsets = (
        ('Oturum Bilgileri', {
            'fields': ('user', 'hotspot', 'session_id', 'status')
        }),
        ('Zaman Bilgileri', {
            'fields': ('start_time', 'end_time', 'duration_minutes')
        }),
        ('Kullanım İstatistikleri', {
            'fields': ('bytes_uploaded', 'bytes_downloaded', 'total_bytes')
        }),
    )


@admin.register(ContentFilter)
class ContentFilterAdmin(admin.ModelAdmin):
    list_display = ['name', 'filter_type', 'action', 'company', 'value', 'is_active', 'priority']
    list_filter = ['filter_type', 'action', 'is_active', 'company', 'created_at']
    search_fields = ['name', 'value', 'description', 'company__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'filter_type', 'action')
        }),
        ('Filtre Değerleri', {
            'fields': ('value', 'description')
        }),
        ('Ayarlar', {
            'fields': ('is_active', 'priority', 'created_at')
        }),
    )


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'domain', 'ip_address', 'was_blocked', 'timestamp']
    list_filter = ['was_blocked', 'user__company', 'timestamp']
    search_fields = ['url', 'domain', 'ip_address', 'user__username']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Erişim Bilgileri', {
            'fields': ('user', 'session', 'url', 'domain', 'ip_address')
        }),
        ('İçerik Filtreleme', {
            'fields': ('content_filter', 'was_blocked')
        }),
        ('Zaman', {
            'fields': ('timestamp',)
        }),
    )


@admin.register(HotspotMetrics)
class HotspotMetricsAdmin(admin.ModelAdmin):
    list_display = ['hotspot', 'company', 'date', 'hour', 'active_users', 'bandwidth_used_mbps', 'blocked_requests']
    list_filter = ['company', 'hotspot', 'date']
    search_fields = ['hotspot__name', 'company__name']
    readonly_fields = ['date', 'hour']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'hotspot', 'date', 'hour')
        }),
        ('Kullanım İstatistikleri', {
            'fields': ('active_users', 'total_sessions', 'new_users')
        }),
        ('Bant Genişliği', {
            'fields': ('bandwidth_used_mbps', 'peak_bandwidth_mbps')
        }),
        ('İçerik Filtreleme', {
            'fields': ('blocked_requests', 'total_requests')
        }),
    )
