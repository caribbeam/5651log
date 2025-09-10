from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from log_kayit.models import Company


class AuditLog(models.Model):
    """Sistem audit logları için model"""
    
    ACTION_CHOICES = [
        ('CREATE', 'Oluşturma'),
        ('READ', 'Okuma'),
        ('UPDATE', 'Güncelleme'),
        ('DELETE', 'Silme'),
        ('LOGIN', 'Giriş'),
        ('LOGOUT', 'Çıkış'),
        ('PASSWORD_CHANGE', 'Şifre Değiştirme'),
        ('PERMISSION_CHANGE', 'Yetki Değiştirme'),
        ('EXPORT', 'Dışa Aktarma'),
        ('IMPORT', 'İçe Aktarma'),
        ('API_ACCESS', 'API Erişimi'),
        ('SECURITY_EVENT', 'Güvenlik Olayı'),
    ]
    
    SEVERITY_CHOICES = [
        ('LOW', 'Düşük'),
        ('MEDIUM', 'Orta'),
        ('HIGH', 'Yüksek'),
        ('CRITICAL', 'Kritik'),
    ]
    
    # Temel bilgiler
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kullanıcı")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Şirket")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name="İşlem")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='LOW', verbose_name="Önem Derecesi")
    
    # İşlem detayları
    resource_type = models.CharField(max_length=100, verbose_name="Kaynak Türü")
    resource_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="Kaynak ID")
    resource_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Kaynak Adı")
    
    # İçerik
    description = models.TextField(verbose_name="Açıklama")
    details = models.JSONField(default=dict, blank=True, verbose_name="Detaylar")
    
    # IP ve User Agent
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    user_agent = models.TextField(null=True, blank=True, verbose_name="User Agent")
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Zaman")
    
    # Generic Foreign Key for related objects
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Sonuç
    success = models.BooleanField(default=True, verbose_name="Başarılı")
    error_message = models.TextField(null=True, blank=True, verbose_name="Hata Mesajı")
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logları"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.resource_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def get_severity_color(self):
        """Severity için Bootstrap renk sınıfı döndürür"""
        colors = {
            'LOW': 'success',
            'MEDIUM': 'warning',
            'HIGH': 'danger',
            'CRITICAL': 'dark',
        }
        return colors.get(self.severity, 'secondary')


class AuditLogConfig(models.Model):
    """Audit log konfigürasyonu"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Şirket")
    action = models.CharField(max_length=50, choices=AuditLog.ACTION_CHOICES, verbose_name="İşlem")
    enabled = models.BooleanField(default=True, verbose_name="Aktif")
    severity = models.CharField(max_length=20, choices=AuditLog.SEVERITY_CHOICES, default='LOW', verbose_name="Önem Derecesi")
    retention_days = models.PositiveIntegerField(default=365, verbose_name="Saklama Süresi (Gün)")
    
    class Meta:
        verbose_name = "Audit Log Konfigürasyonu"
        verbose_name_plural = "Audit Log Konfigürasyonları"
        unique_together = ['company', 'action']
    
    def __str__(self):
        return f"{self.company.name} - {self.get_action_display()}"


class AuditLogReport(models.Model):
    """Audit log raporları"""
    
    REPORT_TYPE_CHOICES = [
        ('DAILY', 'Günlük'),
        ('WEEKLY', 'Haftalık'),
        ('MONTHLY', 'Aylık'),
        ('CUSTOM', 'Özel'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Şirket")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, verbose_name="Rapor Türü")
    start_date = models.DateTimeField(verbose_name="Başlangıç Tarihi")
    end_date = models.DateTimeField(verbose_name="Bitiş Tarihi")
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Oluşturan")
    generated_at = models.DateTimeField(default=timezone.now, verbose_name="Oluşturulma Zamanı")
    
    # Rapor içeriği
    total_events = models.PositiveIntegerField(default=0, verbose_name="Toplam Olay")
    critical_events = models.PositiveIntegerField(default=0, verbose_name="Kritik Olaylar")
    high_events = models.PositiveIntegerField(default=0, verbose_name="Yüksek Öncelikli Olaylar")
    failed_events = models.PositiveIntegerField(default=0, verbose_name="Başarısız Olaylar")
    
    # Dosya
    report_file = models.FileField(upload_to='audit_reports/', null=True, blank=True, verbose_name="Rapor Dosyası")
    
    class Meta:
        verbose_name = "Audit Log Raporu"
        verbose_name_plural = "Audit Log Raporları"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.company.name} - {self.get_report_type_display()} - {self.generated_at.strftime('%Y-%m-%d')}"