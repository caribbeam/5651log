from django.contrib import admin
from .models import LogVerificationSession, LogVerificationResult, LogIntegrityReport, LogVerificationTemplate


@admin.register(LogVerificationSession)
class LogVerificationSessionAdmin(admin.ModelAdmin):
    list_display = ['session_name', 'verification_type', 'status', 'progress_percentage', 'total_records', 'company']
    list_filter = ['verification_type', 'status', 'company']
    search_fields = ['session_name', 'file_name']
    readonly_fields = ['file_hash', 'progress_percentage', 'total_records', 'verified_records', 'failed_records', 'modified_records', 'started_at', 'completed_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'session_name', 'description')
        }),
        ('Dosya Bilgileri', {
            'fields': ('uploaded_file', 'file_name', 'file_size', 'file_hash')
        }),
        ('Doğrulama Ayarları', {
            'fields': ('verification_type',)
        }),
        ('İlerleme', {
            'fields': ('status', 'progress_percentage', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Sonuçlar', {
            'fields': ('total_records', 'verified_records', 'failed_records', 'modified_records'),
            'classes': ('collapse',)
        }),
        ('Hata Bilgileri', {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        })
    )


@admin.register(LogVerificationResult)
class LogVerificationResultAdmin(admin.ModelAdmin):
    list_display = ['session', 'log_id', 'result_type', 'is_valid', 'hash_match', 'signature_valid', 'verified_at']
    list_filter = ['result_type', 'is_valid', 'hash_match', 'signature_valid', 'session__company']
    search_fields = ['session__session_name', 'log_id', 'log_source']
    readonly_fields = ['verified_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('session', 'log_id', 'log_timestamp', 'log_source')
        }),
        ('Doğrulama Sonucu', {
            'fields': ('result_type', 'is_valid')
        }),
        ('Hash Bilgileri', {
            'fields': ('original_hash', 'calculated_hash', 'hash_match'),
            'classes': ('collapse',)
        }),
        ('İmza Bilgileri', {
            'fields': ('has_signature', 'signature_valid', 'signature_authority'),
            'classes': ('collapse',)
        }),
        ('Detaylar', {
            'fields': ('verification_details', 'error_message'),
            'classes': ('collapse',)
        })
    )


@admin.register(LogIntegrityReport)
class LogIntegrityReportAdmin(admin.ModelAdmin):
    list_display = ['report_title', 'report_type', 'compliance_status', 'compliance_score', 'total_records_analyzed', 'generated_at']
    list_filter = ['report_type', 'compliance_status', 'report_format', 'session__company']
    search_fields = ['report_title', 'session__session_name']
    readonly_fields = ['generated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('session', 'report_type', 'report_title')
        }),
        ('Rapor İçeriği', {
            'fields': ('report_content', 'report_data')
        }),
        ('İstatistikler', {
            'fields': ('total_records_analyzed', 'valid_records_count', 'modified_records_count', 'invalid_records_count')
        }),
        ('Dosya Bilgileri', {
            'fields': ('report_file', 'report_format'),
            'classes': ('collapse',)
        }),
        ('Uyumluluk', {
            'fields': ('compliance_score', 'compliance_status')
        })
    )


@admin.register(LogVerificationTemplate)
class LogVerificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'hash_algorithm', 'auto_generate_report', 'report_format', 'is_active']
    list_filter = ['hash_algorithm', 'report_format', 'auto_generate_report', 'is_active', 'company']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'description')
        }),
        ('Doğrulama Ayarları', {
            'fields': ('verification_rules', 'required_fields', 'hash_algorithm')
        }),
        ('Rapor Ayarları', {
            'fields': ('auto_generate_report', 'report_format')
        }),
        ('Durum', {
            'fields': ('is_active',)
        })
    )
