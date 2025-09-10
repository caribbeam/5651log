from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AuditLog, AuditLogConfig, AuditLogReport


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'user', 'company', 'action', 'severity_badge', 
        'resource_type', 'resource_name', 'success_badge', 'ip_address'
    ]
    list_filter = [
        'action', 'severity', 'success', 'timestamp', 'company', 'user'
    ]
    search_fields = [
        'user__username', 'company__name', 'resource_name', 
        'description', 'ip_address'
    ]
    readonly_fields = [
        'timestamp', 'user', 'company', 'action', 'severity',
        'resource_type', 'resource_id', 'resource_name', 'description',
        'details', 'ip_address', 'user_agent', 'success', 'error_message'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def severity_badge(self, obj):
        color = obj.get_severity_color()
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = 'Önem'
    
    def success_badge(self, obj):
        if obj.success:
            return format_html('<span class="badge badge-success">Başarılı</span>')
        else:
            return format_html('<span class="badge badge-danger">Başarısız</span>')
    success_badge.short_description = 'Durum'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AuditLogConfig)
class AuditLogConfigAdmin(admin.ModelAdmin):
    list_display = ['company', 'action', 'enabled', 'severity', 'retention_days']
    list_filter = ['enabled', 'action', 'severity', 'company']
    search_fields = ['company__name']
    list_editable = ['enabled', 'severity', 'retention_days']


@admin.register(AuditLogReport)
class AuditLogReportAdmin(admin.ModelAdmin):
    list_display = [
        'company', 'report_type', 'start_date', 'end_date', 
        'total_events', 'critical_events', 'generated_at', 'download_link'
    ]
    list_filter = ['report_type', 'generated_at', 'company']
    search_fields = ['company__name']
    readonly_fields = [
        'generated_at', 'generated_by', 'total_events', 
        'critical_events', 'high_events', 'failed_events'
    ]
    date_hierarchy = 'generated_at'
    ordering = ['-generated_at']
    
    def download_link(self, obj):
        if obj.report_file:
            return format_html(
                '<a href="{}" class="btn btn-sm btn-primary">İndir</a>',
                obj.report_file.url
            )
        return "Dosya yok"
    download_link.short_description = 'Rapor'
    
    def has_add_permission(self, request):
        return False