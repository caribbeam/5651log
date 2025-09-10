from django.contrib import admin
from django.utils.html import format_html
from .models import TwoFactorAuth, TwoFactorAuthLog, TwoFactorAuthSettings, TwoFactorAuthAttempt


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_enabled', 'created_at', 'updated_at']
    list_filter = ['is_enabled', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['secret_key', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False


@admin.register(TwoFactorAuthLog)
class TwoFactorAuthLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'success', 'ip_address', 'created_at']
    list_filter = ['action', 'success', 'created_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']


@admin.register(TwoFactorAuthSettings)
class TwoFactorAuthSettingsAdmin(admin.ModelAdmin):
    list_display = ['enforce_for_admins', 'enforce_for_all', 'backup_tokens_count', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return not TwoFactorAuthSettings.objects.exists()


@admin.register(TwoFactorAuthAttempt)
class TwoFactorAuthAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'failed_attempts', 'is_locked', 'last_attempt']
    list_filter = ['failed_attempts', 'last_attempt']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['last_attempt']
    
    def is_locked(self, obj):
        if obj.is_locked():
            return format_html('<span style="color: red;">Kilitli</span>')
        return format_html('<span style="color: green;">Açık</span>')
    is_locked.short_description = 'Durum'