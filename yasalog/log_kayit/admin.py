from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import LogKayit, Company, CompanyUser

@admin.register(LogKayit)
class LogKayitAdmin(admin.ModelAdmin):
    list_display = ['tc_no', 'ad_soyad', 'company', 'giris_zamani', 'ip_adresi', 'retention_status']
    list_filter = ['company', 'giris_zamani', 'kimlik_turu', 'is_suspicious']
    search_fields = ['tc_no', 'ad_soyad', 'ip_adresi']
    readonly_fields = ['giris_zamani', 'ip_adresi', 'sha256_hash']
    date_hierarchy = 'giris_zamani'
    
    def retention_status(self, obj):
        """5651 kanunu gereği veri saklama durumu"""
        cutoff_date = timezone.now() - timedelta(days=730)  # 2 yıl
        if obj.giris_zamani < cutoff_date:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ 2 Yıl Doldu</span>'
            )
        elif obj.giris_zamani < (timezone.now() - timedelta(days=700)):  # 1.9 yıl
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠️ Yakında Silinecek</span>'
            )
        else:
            remaining_days = 730 - (timezone.now() - obj.giris_zamani).days
            return format_html(
                f'<span style="color: green;">✅ {remaining_days} gün kaldı</span>'
            )
    
    retention_status.short_description = 'Saklama Durumu'
    
    actions = ['mark_as_suspicious', 'export_to_csv']
    
    def mark_as_suspicious(self, request, queryset):
        updated = queryset.update(is_suspicious=True)
        self.message_user(request, f'{updated} kayıt şüpheli olarak işaretlendi.')
    mark_as_suspicious.short_description = 'Seçili kayıtları şüpheli olarak işaretle'
    
    def export_to_csv(self, request, queryset):
        # CSV export fonksiyonu eklenebilir
        pass
    export_to_csv.short_description = 'Seçili kayıtları CSV olarak dışa aktar'

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'phone', 'created_at', 'log_count', 'retention_info']
    search_fields = ['name', 'slug']
    list_filter = ['created_at']
    
    def log_count(self, obj):
        return obj.logs.count()
    log_count.short_description = 'Toplam Log'
    
    def retention_info(self, obj):
        """Veri saklama bilgisi"""
        old_logs = obj.logs.filter(
            giris_zamani__lt=timezone.now() - timedelta(days=730)
        ).count()
        
        if old_logs > 0:
            return format_html(
                f'<span style="color: red; font-weight: bold;">⚠️ {old_logs} eski kayıt</span>'
            )
        else:
            return format_html('<span style="color: green;">✅ Güncel</span>')
    
    retention_info.short_description = 'Saklama Durumu'

@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'role', 'created_at']
    list_filter = ['company', 'role', 'created_at']
    search_fields = ['user__username', 'user__email', 'company__name']

# Admin paneli için özel sayfa
class DataRetentionAdmin(admin.ModelAdmin):
    """Veri saklama yönetimi için özel admin sayfası"""
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('retention-dashboard/', self.admin_site.admin_view(self.retention_dashboard), name='data_retention_dashboard'),
        ]
        return custom_urls + urls
    
    def retention_dashboard(self, request):
        """Veri saklama dashboard'u"""
        from django.shortcuts import render
        
        # 2 yıldan eski kayıtları bul
        cutoff_date = timezone.now() - timedelta(days=730)
        old_logs = LogKayit.objects.filter(giris_zamani__lt=cutoff_date)
        
        # Şirket bazında istatistikler
        company_stats = []
        for company in Company.objects.all():
            company_old_logs = company.logs.filter(giris_zamani__lt=cutoff_date)
            company_stats.append({
                'company': company,
                'old_logs_count': company_old_logs.count(),
                'total_logs': company.logs.count(),
                'oldest_log': company.logs.earliest('giris_zamani').giris_zamani if company.logs.exists() else None,
            })
        
        context = {
            'title': 'Veri Saklama Yönetimi - 5651 Kanunu',
            'old_logs_count': old_logs.count(),
            'cutoff_date': cutoff_date,
            'company_stats': company_stats,
        }
        
        return render(request, 'admin/data_retention_dashboard.html', context)
