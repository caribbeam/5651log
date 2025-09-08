"""
Gelişmiş Raporlama Admin Yapılandırması
5651 Loglama için kapsamlı raporlama sistemi
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ReportTemplate, GeneratedReport, ReportData, ReportSchedule


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Rapor şablonu admin"""
    list_display = [
        'name', 'company', 'template_type', 'is_active', 
        'include_user_logs', 'include_syslog_data', 'include_mirror_traffic',
        'created_at', 'created_by'
    ]
    list_filter = [
        'template_type', 'is_active', 'include_user_logs', 
        'include_syslog_data', 'include_mirror_traffic', 'created_at'
    ]
    search_fields = ['name', 'description', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'description', 'template_type', 'is_active')
        }),
        ('İçerik Seçenekleri', {
            'fields': (
                'include_user_logs', 'include_syslog_data', 'include_mirror_traffic',
                'include_timestamp_data', 'include_security_alerts', 'include_suspicious_only'
            )
        }),
        ('Rapor Seçenekleri', {
            'fields': ('include_statistics', 'include_charts', 'include_details')
        }),
        ('Meta Bilgiler', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    """Oluşturulan rapor admin"""
    list_display = [
        'title', 'template', 'report_format', 'status',
        'total_records', 'suspicious_records', 'created_at', 'completed_at'
    ]
    list_filter = [
        'status', 'report_format', 'created_at', 'completed_at'
    ]
    search_fields = ['title', 'description', 'template__name']
    readonly_fields = [
        'created_at', 'started_at', 'completed_at', 'total_records', 
        'suspicious_records', 'file_path'
    ]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('template', 'title', 'description', 'report_format', 'status')
        }),
        ('Dönem Bilgileri', {
            'fields': ('period_start', 'period_end')
        }),
        ('İstatistikler', {
            'fields': ('total_records', 'suspicious_records'),
            'classes': ('collapse',)
        }),
        ('Dosya Bilgileri', {
            'fields': ('file_path',),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Hata Bilgileri', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'template__company')
    
    def has_add_permission(self, request):
        return False  # Raporlar sadece sistem tarafından oluşturulur
    
    def has_change_permission(self, request, obj=None):
        return False  # Raporlar değiştirilemez


@admin.register(ReportData)
class ReportDataAdmin(admin.ModelAdmin):
    """Rapor verisi admin"""
    list_display = ['report', 'data_type', 'data_key', 'created_at']
    list_filter = ['data_type', 'created_at']
    search_fields = ['report__title', 'report__template__name']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('report', 'report__template')
    
    def has_add_permission(self, request):
        return False  # Rapor verileri sadece sistem tarafından oluşturulur


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    """Zamanlanmış rapor admin"""
    list_display = [
        'name', 'template', 'frequency', 'run_time', 'is_active',
        'last_run', 'next_run', 'created_at'
    ]
    list_filter = [
        'frequency', 'is_active', 'last_run', 'next_run', 'created_at'
    ]
    search_fields = ['name', 'description', 'template__name']
    readonly_fields = ['last_run', 'next_run', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('template', 'name', 'description', 'is_active')
        }),
        ('Zamanlama', {
            'fields': ('frequency', 'run_time', 'schedule_cron', 'schedule_timezone')
        }),
        ('Alıcılar', {
            'fields': ('recipients',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('last_run', 'next_run', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Meta Bilgiler', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('template', 'template__company', 'created_by')
