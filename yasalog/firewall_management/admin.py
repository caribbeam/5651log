from django.contrib import admin
from .models import FirewallRule, FirewallPolicy, FirewallEvent, FirewallLog

@admin.register(FirewallRule)
class FirewallRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'rule_type', 'protocol', 'source_ip', 'destination_ip', 'priority', 'is_active', 'hit_count']
    list_filter = ['company', 'rule_type', 'protocol', 'priority', 'is_active', 'is_enabled', 'created_at']
    search_fields = ['name', 'description', 'source_ip', 'destination_ip']
    list_editable = ['is_active', 'priority']
    readonly_fields = ['hit_count', 'last_hit', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'description')
        }),
        ('Kural Detayları', {
            'fields': ('rule_type', 'protocol', 'source_ip', 'source_port', 'destination_ip', 'destination_port')
        }),
        ('Ayarlar', {
            'fields': ('priority', 'is_active', 'is_enabled')
        }),
        ('Zaman Ayarları', {
            'fields': ('valid_from', 'valid_until'),
            'classes': ('collapse',)
        }),
        ('İstatistikler', {
            'fields': ('hit_count', 'last_hit'),
            'classes': ('collapse',)
        }),
        ('Sistem', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(FirewallPolicy)
class FirewallPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'policy_type', 'is_active', 'rules_count', 'created_at']
    list_filter = ['company', 'policy_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    def rules_count(self, obj):
        return obj.rules.count()
    rules_count.short_description = 'Kural Sayısı'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'name', 'description', 'policy_type')
        }),
        ('Ayarlar', {
            'fields': ('is_active', 'rules')
        }),
        ('Sistem', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(FirewallEvent)
class FirewallEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'company', 'severity', 'source_ip', 'destination_ip', 'timestamp', 'is_resolved']
    list_filter = ['company', 'event_type', 'severity', 'is_resolved', 'timestamp']
    search_fields = ['message', 'source_ip', 'destination_ip']
    list_editable = ['is_resolved']
    readonly_fields = ['timestamp', 'resolved_at']
    
    fieldsets = (
        ('Olay Bilgileri', {
            'fields': ('company', 'event_type', 'severity', 'message')
        }),
        ('Trafik Detayları', {
            'fields': ('source_ip', 'destination_ip', 'protocol', 'port')
        }),
        ('İlişkiler', {
            'fields': ('rule', 'policy'),
            'classes': ('collapse',)
        }),
        ('Detaylar', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
        ('Durum', {
            'fields': ('is_resolved', 'resolved_at')
        }),
        ('Sistem', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} olay çözüldü olarak işaretlendi.')
    mark_as_resolved.short_description = 'Seçili olayları çözüldü olarak işaretle'

@admin.register(FirewallLog)
class FirewallLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'company', 'source_ip', 'destination_ip', 'protocol', 'action', 'bytes_total']
    list_filter = ['company', 'protocol', 'action', 'timestamp']
    search_fields = ['source_ip', 'destination_ip']
    readonly_fields = ['timestamp', 'bytes_sent', 'bytes_received', 'packets_sent', 'packets_received']
    
    def bytes_total(self, obj):
        return obj.bytes_sent + obj.bytes_received
    bytes_total.short_description = 'Toplam Byte'
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('company', 'timestamp', 'action')
        }),
        ('Trafik Bilgileri', {
            'fields': ('source_ip', 'source_port', 'destination_ip', 'destination_port', 'protocol')
        }),
        ('Kural Eşleşmesi', {
            'fields': ('rule',),
            'classes': ('collapse',)
        }),
        ('Trafik Detayları', {
            'fields': ('bytes_sent', 'bytes_received', 'packets_sent', 'packets_received', 'connection_duration')
        }),
        ('Ek Bilgiler', {
            'fields': ('user_agent',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Log kayıtları otomatik oluşturulur
    
    def has_change_permission(self, request, obj=None):
        return False  # Log kayıtları değiştirilemez
