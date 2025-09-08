"""
Alert System Models
5651log platformunda gerçek zamanlı uyarılar için veri modelleri
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class AlertRule(models.Model):
    """Uyarı kuralları"""
    
    ALERT_TYPES = [
        ('security', 'Güvenlik'),
        ('performance', 'Performans'),
        ('network', 'Network'),
        ('device', 'Cihaz'),
        ('user', 'Kullanıcı'),
        ('system', 'Sistem'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Bilgi'),
        ('warning', 'Uyarı'),
        ('error', 'Hata'),
        ('critical', 'Kritik'),
    ]
    
    TRIGGER_TYPES = [
        ('threshold', 'Eşik Değeri'),
        ('anomaly', 'Anomali'),
        ('pattern', 'Kalıp'),
        ('schedule', 'Zamanlanmış'),
        ('manual', 'Manuel'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Kural Adı")
    description = models.TextField(verbose_name="Açıklama")
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, verbose_name="Uyarı Tipi")
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, verbose_name="Önem Seviyesi")
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES, verbose_name="Tetikleyici Tipi")
    
    # Tetikleyici koşulları
    trigger_conditions = models.JSONField(verbose_name="Tetikleyici Koşulları")
    threshold_value = models.FloatField(null=True, blank=True, verbose_name="Eşik Değeri")
    
    # Uyarı ayarları
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    auto_resolve = models.BooleanField(default=False, verbose_name="Otomatik Çözüm")
    escalation_enabled = models.BooleanField(default=False, verbose_name="Yükseltme Aktif")
    
    # Zaman ayarları
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Oluşturulma Zamanı")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Zamanı")
    company = models.ForeignKey('log_kayit.Company', on_delete=models.CASCADE, verbose_name="Şirket")
    
    class Meta:
        verbose_name = "Uyarı Kuralı"
        verbose_name_plural = "Uyarı Kuralları"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_severity_display()}"


class Alert(models.Model):
    """Gerçek zamanlı uyarılar"""
    
    STATUS_CHOICES = [
        ('new', 'Yeni'),
        ('acknowledged', 'Kabul Edildi'),
        ('in_progress', 'İşlemde'),
        ('resolved', 'Çözüldü'),
        ('closed', 'Kapatıldı'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Başlık")
    message = models.TextField(verbose_name="Mesaj")
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, verbose_name="Uyarı Kuralı")
    company = models.ForeignKey('log_kayit.Company', on_delete=models.CASCADE, verbose_name="Şirket")
    
    # Uyarı durumu
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Durum")
    severity = models.CharField(max_length=20, choices=AlertRule.SEVERITY_LEVELS, verbose_name="Önem Seviyesi")
    
    # Tetikleyici bilgileri
    triggered_at = models.DateTimeField(default=timezone.now, verbose_name="Tetiklenme Zamanı")
    trigger_data = models.JSONField(verbose_name="Tetikleyici Verisi")
    
    # Çözüm bilgileri
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alert_system_acknowledged_alerts', verbose_name="Kabul Eden")
    acknowledged_at = models.DateTimeField(null=True, blank=True, verbose_name="Kabul Edilme Zamanı")
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alert_system_resolved_alerts', verbose_name="Çözen")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Çözülme Zamanı")
    resolution_notes = models.TextField(blank=True, verbose_name="Çözüm Notları")
    
    # Zaman bilgileri
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Oluşturulma Zamanı")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Zamanı")
    
    class Meta:
        verbose_name = "Uyarı"
        verbose_name_plural = "Uyarılar"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


class AlertNotification(models.Model):
    """Uyarı bildirimleri"""
    
    NOTIFICATION_TYPES = [
        ('email', 'E-posta'),
        ('sms', 'SMS'),
        ('push', 'Push Bildirim'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
    ]
    
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, verbose_name="Uyarı")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="Bildirim Tipi")
    recipient = models.CharField(max_length=200, verbose_name="Alıcı")
    
    # Bildirim durumu
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Gönderilme Zamanı")
    delivery_status = models.CharField(max_length=20, default='pending', verbose_name="Teslim Durumu")
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")
    
    # Zaman bilgileri
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Oluşturulma Zamanı")
    
    class Meta:
        verbose_name = "Uyarı Bildirimi"
        verbose_name_plural = "Uyarı Bildirimleri"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert.title} - {self.get_notification_type_display()}"


class AlertEscalation(models.Model):
    """Uyarı yükseltme kuralları"""
    
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, verbose_name="Uyarı Kuralı")
    escalation_level = models.IntegerField(verbose_name="Yükseltme Seviyesi")
    delay_minutes = models.IntegerField(verbose_name="Gecikme (Dakika)")
    
    # Yükseltme hedefleri
    notify_users = models.ManyToManyField(User, verbose_name="Bildirilecek Kullanıcılar")
    notify_roles = models.JSONField(verbose_name="Bildirilecek Roller")
    
    # Zaman bilgileri
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Oluşturulma Zamanı")
    
    class Meta:
        verbose_name = "Uyarı Yükseltmesi"
        verbose_name_plural = "Uyarı Yükseltmeleri"
        ordering = ['escalation_level']
        unique_together = ['alert_rule', 'escalation_level']
    
    def __str__(self):
        return f"{self.alert_rule.name} - Seviye {self.escalation_level}"


class AlertTemplate(models.Model):
    """Uyarı şablonları"""
    
    name = models.CharField(max_length=200, verbose_name="Şablon Adı")
    description = models.TextField(verbose_name="Açıklama")
    alert_type = models.CharField(max_length=20, choices=AlertRule.ALERT_TYPES, verbose_name="Uyarı Tipi")
    
    # Şablon içeriği
    subject_template = models.CharField(max_length=200, verbose_name="Konu Şablonu")
    message_template = models.TextField(verbose_name="Mesaj Şablonu")
    html_template = models.TextField(blank=True, verbose_name="HTML Şablonu")
    
    # Şablon ayarları
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    company = models.ForeignKey('log_kayit.Company', on_delete=models.CASCADE, verbose_name="Şirket")
    
    # Zaman bilgileri
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Oluşturulma Zamanı")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Zamanı")
    
    class Meta:
        verbose_name = "Uyarı Şablonu"
        verbose_name_plural = "Uyarı Şablonları"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.get_alert_type_display()}"
