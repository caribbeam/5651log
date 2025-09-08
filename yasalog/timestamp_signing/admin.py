from django.contrib import admin
from .models import TimestampAuthority, TimestampSignature, TimestampConfiguration, TimestampLog


@admin.register(TimestampAuthority)
class TimestampAuthorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'authority_type', 'is_active', 'created_at']
    list_filter = ['authority_type', 'is_active', 'created_at']
    search_fields = ['name', 'api_endpoint', 'username']
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
            'fields': ('name', 'authority_type', 'is_active')
        }),
        ('Bağlantı Bilgileri', {
            'fields': ('api_endpoint', 'username', 'password', 'api_key')
        }),
        ('Sertifika Bilgileri', {
            'fields': ('certificate_path',),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimestampSignature)
class TimestampSignatureAdmin(admin.ModelAdmin):
    list_display = ['log_entry', 'company', 'authority', 'status', 'signed_at', 'created_at']
    list_filter = ['status', 'authority', 'company', 'signed_at', 'created_at']
    search_fields = ['log_entry__ad_soyad', 'log_entry__tc_no', 'serial_number']
    readonly_fields = ['created_at', 'updated_at', 'signature_data', 'timestamp_token', 'certificate_chain']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('log_entry', 'company', 'authority', 'status')
        }),
        ('İmza Bilgileri', {
            'fields': ('signature_data', 'timestamp_token', 'certificate_chain', 'serial_number'),
            'classes': ('collapse',)
        }),
        ('Teknik Bilgiler', {
            'fields': ('hash_algorithm', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('signed_at', 'verified_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # İmzalar otomatik oluşturulur


@admin.register(TimestampConfiguration)
class TimestampConfigurationAdmin(admin.ModelAdmin):
    list_display = ['company', 'authority', 'is_active', 'auto_sign', 'created_at']
    list_filter = ['is_active', 'auto_sign', 'company', 'created_at']
    search_fields = ['company__name', 'authority__name']
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
            'fields': ('company', 'authority', 'is_active')
        }),
        ('Otomatik İmzalama', {
            'fields': ('auto_sign', 'sign_interval', 'batch_size')
        }),
        ('Retry Ayarları', {
            'fields': ('max_retries', 'retry_delay'),
            'classes': ('collapse',)
        }),
        ('Bildirim Ayarları', {
            'fields': ('notify_on_success', 'notify_on_failure', 'notification_email'),
            'classes': ('collapse',)
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimestampLog)
class TimestampLogAdmin(admin.ModelAdmin):
    list_display = ['company', 'log_type', 'records_processed', 'success_count', 'failure_count', 'timestamp']
    list_filter = ['log_type', 'company', 'timestamp']
    search_fields = ['company__name', 'message']
    readonly_fields = ['timestamp', 'details']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'log_type', 'message', 'timestamp')
        }),
        ('İstatistikler', {
            'fields': ('records_processed', 'success_count', 'failure_count')
        }),
        ('Detaylar', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Loglar otomatik oluşturulur
