from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import SecurityThreat, SecurityAlert, ThreatIntelligence, SecurityIncident, SecurityMetrics


@admin.register(SecurityThreat)
class SecurityThreatAdmin(admin.ModelAdmin):
    list_display = ['title', 'threat_type', 'severity', 'status', 'company', 'detection_time', 'assigned_to', 'confidence_score']
    list_filter = ['threat_type', 'severity', 'status', 'company', 'detection_time', 'assigned_to']
    search_fields = ['title', 'description', 'source_ip', 'destination_ip', 'tags']
    list_per_page = 25
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'title', 'description', 'threat_type', 'severity', 'status')
        }),
        ('Ağ Detayları', {
            'fields': ('source_ip', 'destination_ip', 'source_port', 'destination_port')
        }),
        ('Tehdit Analizi', {
            'fields': ('confidence_score', 'false_positive_probability', 'tags')
        }),
        ('Atama ve Notlar', {
            'fields': ('assigned_to', 'notes')
        }),
    )
    
    def get_severity_color(self, obj):
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'darkred',
            'EMERGENCY': 'black'
        }
        color = colors.get(obj.severity, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_severity_display())
    get_severity_color.short_description = 'Önem Seviyesi'
    
    readonly_fields = ['detection_time', 'last_updated']


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_type', 'priority', 'company', 'created_at', 'is_acknowledged', 'is_resolved']
    list_filter = ['alert_type', 'priority', 'company', 'created_at', 'is_acknowledged', 'is_resolved']
    search_fields = ['title', 'message', 'details']
    list_per_page = 25
    
    fieldsets = (
        ('Uyarı Bilgileri', {
            'fields': ('company', 'alert_type', 'priority', 'title', 'message', 'details')
        }),
        ('Durum Bilgileri', {
            'fields': ('is_acknowledged', 'is_resolved', 'is_escalated', 'acknowledged_at', 'resolved_at')
        }),
        ('Atama ve İlişkiler', {
            'fields': ('assigned_to', 'acknowledged_by', 'resolved_by', 'related_threat')
        }),
    )
    
    def get_priority_color(self, obj):
        colors = {
            'LOW': 'green',
            'NORMAL': 'blue',
            'HIGH': 'orange',
            'URGENT': 'red',
            'IMMEDIATE': 'darkred'
        }
        color = colors.get(obj.priority, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_priority_display())
    get_priority_color.short_description = 'Öncelik'
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ThreatIntelligence)
class ThreatIntelligenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'intel_type', 'severity', 'company', 'confidence', 'source', 'last_seen', 'is_active']
    list_filter = ['intel_type', 'severity', 'company', 'source', 'is_active', 'last_seen']
    search_fields = ['name', 'description', 'value', 'tags']
    list_per_page = 25
    
    fieldsets = (
        ('İstihbarat Bilgileri', {
            'fields': ('company', 'intel_type', 'name', 'description', 'value')
        }),
        ('Güvenlik Değerlendirmesi', {
            'fields': ('confidence', 'severity', 'source')
        }),
        ('Zaman Bilgileri', {
            'fields': ('first_seen', 'last_seen')
        }),
        ('Durum ve Etiketler', {
            'fields': ('is_active', 'tags')
        }),
    )
    
    readonly_fields = ['last_seen']


@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    list_display = ['title', 'incident_type', 'status', 'severity', 'company', 'discovered_at', 'assigned_to']
    list_filter = ['incident_type', 'status', 'severity', 'company', 'discovered_at']
    search_fields = ['title', 'description', 'notes']
    list_per_page = 25
    
    fieldsets = (
        ('Olay Bilgileri', {
            'fields': ('company', 'incident_type', 'title', 'description', 'severity', 'impact_level')
        }),
        ('Durum ve Zaman', {
            'fields': ('status', 'discovered_at', 'started_at', 'contained_at', 'resolved_at')
        }),
        ('Atama ve Notlar', {
            'fields': ('assigned_to', 'notes')
        }),
        ('İlişkili Kayıtlar', {
            'fields': ('related_threats', 'related_alerts'),
            'classes': ('collapse',)
        }),
    )
    
    def get_status_color(self, obj):
        colors = {
            'OPEN': 'red',
            'INVESTIGATING': 'orange',
            'CONTAINED': 'blue',
            'RESOLVED': 'green',
            'CLOSED': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_status_display())
    get_status_color.short_description = 'Durum'
    
    readonly_fields = ['discovered_at']


@admin.register(SecurityMetrics)
class SecurityMetricsAdmin(admin.ModelAdmin):
    list_display = ['company', 'date', 'total_threats', 'total_alerts', 'total_incidents', 'mean_time_to_detect', 'mean_time_to_resolve']
    list_filter = ['company', 'date']
    search_fields = ['company__name']
    list_per_page = 25
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'date')
        }),
        ('Tehdit Metrikleri', {
            'fields': ('total_threats', 'critical_threats', 'high_threats', 'medium_threats', 'low_threats')
        }),
        ('Uyarı Metrikleri', {
            'fields': ('total_alerts', 'acknowledged_alerts', 'resolved_alerts')
        }),
        ('Olay Metrikleri', {
            'fields': ('total_incidents', 'open_incidents', 'resolved_incidents')
        }),
        ('Performans Metrikleri', {
            'fields': ('mean_time_to_detect', 'mean_time_to_resolve')
        }),
    )
    
    readonly_fields = ['created_at']


# Admin site customization
admin.site.site_header = "5651log Güvenlik Yönetimi"
admin.site.site_title = "Güvenlik Admin"
admin.site.index_title = "Güvenlik Modülleri Yönetimi"
