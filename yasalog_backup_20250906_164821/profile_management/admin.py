"""
Profile Management Admin
5651log platformunda profil yönetimini admin panelinde yönetir
"""

from django.contrib import admin
from .models import UserProfile, UserProfileAssignment

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'profile_code', 'name', 'profile_type', 'get_speed_display', 
        'get_duration_display', 'shared_users', 'is_active', 'company'
    ]
    list_filter = [
        'profile_type', 'is_active', 'is_premium', 'company', 'created_at'
    ]
    search_fields = ['name', 'profile_code', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('name', 'profile_code', 'profile_type', 'company')
        }),
        ('Hız Limitleri', {
            'fields': ('upload_speed', 'download_speed'),
            'description': 'Hız değerleri Mbps cinsinden girilmelidir'
        }),
        ('Süre Limitleri', {
            'fields': ('duration_days', 'duration_hours', 'duration_minutes', 'duration_seconds'),
            'description': '0 değeri sınırsız anlamına gelir'
        }),
        ('Kullanıcı Limitleri', {
            'fields': ('shared_users', 'max_concurrent_users')
        }),
        ('Durum Bilgileri', {
            'fields': ('is_active', 'is_premium')
        }),
        ('Zaman Bilgileri', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def get_speed_display(self, obj):
        return obj.get_speed_display()
    get_speed_display.short_description = 'Hız'
    
    def get_duration_display(self, obj):
        return obj.get_duration_display()
    get_duration_display.short_description = 'Süre'

@admin.register(UserProfileAssignment)
class UserProfileAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'profile', 'company', 'assigned_at', 'expires_at', 
        'is_active', 'session_count'
    ]
    list_filter = [
        'is_active', 'company', 'profile__profile_type', 'assigned_at'
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 
        'profile__name', 'company__name'
    ]
    readonly_fields = ['assigned_at', 'current_bandwidth_used', 'session_count']
    
    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('user', 'profile', 'company')
        }),
        ('Atama Bilgileri', {
            'fields': ('assigned_at', 'expires_at', 'is_active')
        }),
        ('Kullanım Bilgileri', {
            'fields': ('current_bandwidth_used', 'session_count'),
            'description': 'Bu alanlar otomatik olarak güncellenir'
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'profile', 'company')

# Admin panel başlığını özelleştir
admin.site.site_header = "5651log Profil Yönetimi"
admin.site.site_title = "Profil Yönetimi Admin"
admin.site.index_title = "Kullanıcı Profil Yönetimi Modülü"
