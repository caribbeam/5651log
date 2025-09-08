from django.contrib import admin
from .models import EvidenceReport, EvidenceReportLog, EvidenceReportTemplate, EvidenceReportAccess


@admin.register(EvidenceReport)
class EvidenceReportAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'report_title', 'report_type', 'status', 'priority', 'requester_name', 'created_at']
    list_filter = ['report_type', 'status', 'priority', 'company']
    search_fields = ['request_number', 'report_title', 'requester_name', 'requester_authority']
    readonly_fields = ['request_number', 'file_size', 'file_hash', 'total_records', 'total_logs', 'total_traffic_records', 'total_signatures', 'created_at', 'approved_at', 'generated_at', 'delivered_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'request_number', 'report_type', 'status', 'priority')
        }),
        ('Talep Bilgileri', {
            'fields': ('request_date', 'requester_name', 'requester_authority', 'requester_contact')
        }),
        ('Rapor İçeriği', {
            'fields': ('report_title', 'report_description', 'requested_data_period')
        }),
        ('Zaman Aralığı', {
            'fields': ('start_date', 'end_date')
        }),
        ('Filtreleme Kriterleri', {
            'fields': ('filter_criteria', 'include_logs', 'include_traffic', 'include_signatures', 'include_verification'),
            'classes': ('collapse',)
        }),
        ('Rapor Ayarları', {
            'fields': ('report_format',)
        }),
        ('Dosya Bilgileri', {
            'fields': ('generated_file', 'file_size', 'file_hash'),
            'classes': ('collapse',)
        }),
        ('İstatistikler', {
            'fields': ('total_records', 'total_logs', 'total_traffic_records', 'total_signatures'),
            'classes': ('collapse',)
        }),
        ('Onay Süreci', {
            'fields': ('created_by', 'approved_by', 'generated_by', 'approved_at', 'generated_at', 'delivered_at', 'deadline'),
            'classes': ('collapse',)
        }),
        ('Notlar', {
            'fields': ('internal_notes', 'external_notes'),
            'classes': ('collapse',)
        })
    )


@admin.register(EvidenceReportLog)
class EvidenceReportLogAdmin(admin.ModelAdmin):
    list_display = ['report', 'action', 'user', 'timestamp']
    list_filter = ['action', 'report__company', 'timestamp']
    search_fields = ['report__request_number', 'description']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('report', 'action', 'user', 'description')
        }),
        ('Detaylar', {
            'fields': ('details',)
        }),
        ('Sistem Bilgileri', {
            'fields': ('ip_address', 'user_agent', 'timestamp'),
            'classes': ('collapse',)
        })
    )


@admin.register(EvidenceReportTemplate)
class EvidenceReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'report_type', 'default_format', 'is_active', 'is_default']
    list_filter = ['report_type', 'default_format', 'is_active', 'is_default', 'company']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'description', 'report_type')
        }),
        ('Şablon İçeriği', {
            'fields': ('template_content',)
        }),
        ('Varsayılan Ayarlar', {
            'fields': ('default_format', 'default_include_logs', 'default_include_traffic', 'default_include_signatures', 'default_include_verification')
        }),
        ('Durum', {
            'fields': ('is_active', 'is_default')
        })
    )


@admin.register(EvidenceReportAccess)
class EvidenceReportAccessAdmin(admin.ModelAdmin):
    list_display = ['report', 'user', 'access_type', 'ip_address', 'timestamp']
    list_filter = ['access_type', 'report__company', 'timestamp']
    search_fields = ['report__request_number', 'user__username', 'ip_address']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('report', 'user', 'access_type')
        }),
        ('Erişim Detayları', {
            'fields': ('access_duration', 'pages_viewed', 'data_accessed')
        }),
        ('Sistem Bilgileri', {
            'fields': ('ip_address', 'user_agent', 'session_id', 'timestamp'),
            'classes': ('collapse',)
        })
    )
