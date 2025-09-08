from django.contrib import admin
from .models import ArchivingPolicy, ArchivingJob, ArchivingLog, ArchivingStorage


@admin.register(ArchivingPolicy)
class ArchivingPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'policy_type', 'retention_period_years', 'storage_type', 'is_active', 'company']
    list_filter = ['policy_type', 'storage_type', 'is_active', 'company']
    search_fields = ['name', 'description']
    readonly_fields = ['last_execution', 'next_execution']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'description', 'policy_type')
        }),
        ('Saklama Süreleri', {
            'fields': ('retention_period_years', 'retention_period_months', 'retention_period_days')
        }),
        ('Arşivleme Ayarları', {
            'fields': ('archive_after_days', 'compression_enabled', 'encryption_enabled')
        }),
        ('Depolama Ayarları', {
            'fields': ('storage_type', 'storage_path', 'max_storage_size_gb')
        }),
        ('WORM Disk Ayarları', {
            'fields': ('worm_enabled', 'worm_path', 'worm_append_only'),
            'classes': ('collapse',)
        }),
        ('Otomatik Temizleme', {
            'fields': ('auto_cleanup_enabled', 'cleanup_schedule')
        }),
        ('Bildirim Ayarları', {
            'fields': ('notify_before_cleanup', 'notify_after_cleanup', 'notification_recipients'),
            'classes': ('collapse',)
        }),
        ('Durum', {
            'fields': ('is_active', 'last_execution', 'next_execution')
        })
    )


@admin.register(ArchivingJob)
class ArchivingJobAdmin(admin.ModelAdmin):
    list_display = ['job_name', 'policy', 'status', 'start_time', 'end_time', 'records_archived', 'records_deleted']
    list_filter = ['status', 'policy__company', 'start_time']
    search_fields = ['job_name', 'policy__name']
    readonly_fields = ['start_time', 'end_time', 'duration', 'records_archived', 'records_deleted', 'records_failed', 'archive_file_size', 'archive_file_hash']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('policy', 'job_name', 'status')
        }),
        ('Zaman Bilgileri', {
            'fields': ('start_time', 'end_time', 'duration'),
            'classes': ('collapse',)
        }),
        ('İstatistikler', {
            'fields': ('total_records_processed', 'records_archived', 'records_deleted', 'records_failed')
        }),
        ('Dosya Bilgileri', {
            'fields': ('archive_file_path', 'archive_file_size', 'archive_file_hash'),
            'classes': ('collapse',)
        }),
        ('Hata Bilgileri', {
            'fields': ('error_message', 'error_details'),
            'classes': ('collapse',)
        }),
        ('İş Detayları', {
            'fields': ('job_details',),
            'classes': ('collapse',)
        })
    )


@admin.register(ArchivingLog)
class ArchivingLogAdmin(admin.ModelAdmin):
    list_display = ['policy', 'log_type', 'message', 'records_affected', 'timestamp']
    list_filter = ['log_type', 'policy__company', 'timestamp']
    search_fields = ['policy__name', 'message']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('policy', 'job', 'log_type', 'message')
        }),
        ('Detaylar', {
            'fields': ('details',)
        }),
        ('İstatistikler', {
            'fields': ('records_affected', 'storage_used_bytes'),
            'classes': ('collapse',)
        })
    )


@admin.register(ArchivingStorage)
class ArchivingStorageAdmin(admin.ModelAdmin):
    list_display = ['name', 'storage_type', 'status', 'total_capacity_gb', 'used_capacity_gb', 'available_capacity_gb', 'company']
    list_filter = ['storage_type', 'status', 'is_encrypted', 'is_compressed', 'is_worm', 'company']
    search_fields = ['name', 'storage_path']
    readonly_fields = ['available_capacity_gb', 'total_archives', 'total_size_bytes', 'last_archive_date']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'storage_type')
        }),
        ('Depolama Bilgileri', {
            'fields': ('storage_path', 'total_capacity_gb', 'used_capacity_gb', 'available_capacity_gb')
        }),
        ('Durum', {
            'fields': ('status', 'is_encrypted', 'is_compressed')
        }),
        ('WORM Disk Özellikleri', {
            'fields': ('is_worm', 'worm_append_only'),
            'classes': ('collapse',)
        }),
        ('İstatistikler', {
            'fields': ('total_archives', 'total_size_bytes', 'last_archive_date'),
            'classes': ('collapse',)
        })
    )
