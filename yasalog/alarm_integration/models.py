"""
Alarm Entegrasyonu Modelleri
5651 uyumluluğu için alarm sistemi
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from log_kayit.models import Company
from django.contrib.auth.models import User


class AlarmRule(models.Model):
    """Alarm kuralı"""
    
    ALARM_TYPES = [
        ('SIGNING_FAILED', 'İmzalama Başarısız'),
        ('DISK_FULL', 'Disk Dolu'),
        ('NTP_DRIFT', 'NTP Sapması'),
        ('LOG_FLOW_STOPPED', 'Log Akışı Durdu'),
        ('DEVICE_OFFLINE', 'Cihaz Çevrimdışı'),
        ('HIGH_CPU_USAGE', 'Yüksek CPU Kullanımı'),
        ('HIGH_MEMORY_USAGE', 'Yüksek Bellek Kullanımı'),
        ('NETWORK_ERROR', 'Ağ Hatası'),
        ('SECURITY_THREAT', 'Güvenlik Tehdidi'),
        ('COMPLIANCE_VIOLATION', 'Uyumluluk İhlali'),
        ('BACKUP_FAILED', 'Yedekleme Başarısız'),
        ('CUSTOM', 'Özel'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Düşük'),
        ('MEDIUM', 'Orta'),
        ('HIGH', 'Yüksek'),
        ('CRITICAL', 'Kritik'),
        ('EMERGENCY', 'Acil'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Alarm Adı"), max_length=100)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Alarm tipi ve önem seviyesi
    alarm_type = models.CharField(_("Alarm Tipi"), max_length=30, choices=ALARM_TYPES)
    severity = models.CharField(_("Önem Seviyesi"), max_length=15, choices=SEVERITY_LEVELS)
    
    # Kural koşulları
    condition = models.TextField(_("Koşul"), help_text=_("Alarm koşulu"))
    threshold_value = models.FloatField(_("Eşik Değeri"), null=True, blank=True)
    time_window_minutes = models.IntegerField(_("Zaman Penceresi (dakika)"), default=5)
    
    # Bildirim ayarları
    notify_email = models.BooleanField(_("E-posta Bildirimi"), default=True)
    notify_sms = models.BooleanField(_("SMS Bildirimi"), default=False)
    notify_webhook = models.BooleanField(_("Webhook Bildirimi"), default=False)
    notify_dashboard = models.BooleanField(_("Dashboard Bildirimi"), default=True)
    
    # Bildirim alıcıları
    email_recipients = models.TextField(_("E-posta Alıcıları"), blank=True,
                                       help_text=_("Virgülle ayrılmış e-posta listesi"))
    sms_recipients = models.TextField(_("SMS Alıcıları"), blank=True,
                                     help_text=_("Virgülle ayrılmış telefon listesi"))
    webhook_url = models.URLField(_("Webhook URL"), blank=True)
    
    # Tekrar bildirim ayarları
    repeat_notification = models.BooleanField(_("Tekrar Bildirim"), default=True)
    repeat_interval_minutes = models.IntegerField(_("Tekrar Aralığı (dakika)"), default=60)
    max_repeat_count = models.IntegerField(_("Maksimum Tekrar Sayısı"), default=5)
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    is_enabled = models.BooleanField(_("Etkin"), default=True)
    
    # İstatistikler
    trigger_count = models.IntegerField(_("Tetiklenme Sayısı"), default=0)
    last_triggered = models.DateTimeField(_("Son Tetiklenme"), null=True, blank=True)
    last_notification_sent = models.DateTimeField(_("Son Bildirim"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Alarm Kuralı")
        verbose_name_plural = _("Alarm Kuralları")
        ordering = ['-severity', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.get_alarm_type_display()}"
    
    def trigger_alarm(self, details=None):
        """Alarmı tetikle"""
        self.trigger_count += 1
        self.last_triggered = timezone.now()
        self.save()
        
        # Alarm kaydı oluştur
        AlarmEvent.objects.create(
            rule=self,
            severity=self.severity,
            title=f"{self.name} - {self.get_alarm_type_display()}",
            message=self.description,
            details=details or {},
            company=self.company
        )


class AlarmEvent(models.Model):
    """Alarm olayı"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Aktif'),
        ('ACKNOWLEDGED', 'Kabul Edildi'),
        ('RESOLVED', 'Çözüldü'),
        ('SUPPRESSED', 'Bastırıldı'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    rule = models.ForeignKey(AlarmRule, on_delete=models.CASCADE, verbose_name=_("Alarm Kuralı"))
    
    # Alarm bilgileri
    severity = models.CharField(_("Önem Seviyesi"), max_length=15, choices=AlarmRule.SEVERITY_LEVELS)
    title = models.CharField(_("Başlık"), max_length=200)
    message = models.TextField(_("Mesaj"))
    details = models.JSONField(_("Detaylar"), default=dict, blank=True)
    
    # Durum
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Zaman bilgileri
    triggered_at = models.DateTimeField(_("Tetiklenme Zamanı"), auto_now_add=True)
    acknowledged_at = models.DateTimeField(_("Kabul Zamanı"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("Çözülme Zamanı"), null=True, blank=True)
    
    # Kullanıcı bilgileri
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                       verbose_name=_("Kabul Eden"), related_name='acknowledged_alarms')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name=_("Çözen"), related_name='resolved_alarms')
    
    # Bildirim durumu
    notifications_sent = models.IntegerField(_("Gönderilen Bildirim"), default=0)
    last_notification_sent = models.DateTimeField(_("Son Bildirim"), null=True, blank=True)
    
    # Notlar
    notes = models.TextField(_("Notlar"), blank=True)
    
    class Meta:
        verbose_name = _("Alarm Olayı")
        verbose_name_plural = _("Alarm Olayları")
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def acknowledge(self, user):
        """Alarmı kabul et"""
        self.status = 'ACKNOWLEDGED'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, user, notes=''):
        """Alarmı çöz"""
        self.status = 'RESOLVED'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()
    
    def get_severity_color(self):
        """Önem seviyesine göre renk döndür"""
        colors = {
            'LOW': 'success',
            'MEDIUM': 'warning',
            'HIGH': 'danger',
            'CRITICAL': 'danger',
            'EMERGENCY': 'dark'
        }
        return colors.get(self.severity, 'secondary')


class AlarmNotification(models.Model):
    """Alarm bildirimi"""
    
    NOTIFICATION_TYPES = [
        ('EMAIL', 'E-posta'),
        ('SMS', 'SMS'),
        ('WEBHOOK', 'Webhook'),
        ('DASHBOARD', 'Dashboard'),
        ('SLACK', 'Slack'),
        ('TEAMS', 'Microsoft Teams'),
        ('TELEGRAM', 'Telegram'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Beklemede'),
        ('SENT', 'Gönderildi'),
        ('FAILED', 'Başarısız'),
        ('DELIVERED', 'Teslim Edildi'),
    ]
    
    event = models.ForeignKey(AlarmEvent, on_delete=models.CASCADE, 
                             verbose_name=_("Alarm Olayı"), related_name='notifications')
    
    notification_type = models.CharField(_("Bildirim Tipi"), max_length=20, choices=NOTIFICATION_TYPES)
    recipient = models.CharField(_("Alıcı"), max_length=200)
    subject = models.CharField(_("Konu"), max_length=300, blank=True)
    message = models.TextField(_("Mesaj"))
    
    # Durum
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Zaman bilgileri
    created_at = models.DateTimeField(_("Oluşturulma Zamanı"), auto_now_add=True)
    sent_at = models.DateTimeField(_("Gönderilme Zamanı"), null=True, blank=True)
    delivered_at = models.DateTimeField(_("Teslim Zamanı"), null=True, blank=True)
    
    # Hata bilgileri
    error_message = models.TextField(_("Hata Mesajı"), blank=True)
    retry_count = models.IntegerField(_("Deneme Sayısı"), default=0)
    
    class Meta:
        verbose_name = _("Alarm Bildirimi")
        verbose_name_plural = _("Alarm Bildirimleri")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event.title} - {self.get_notification_type_display()}"
    
    def mark_sent(self):
        """Bildirimi gönderildi olarak işaretle"""
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_delivered(self):
        """Bildirimi teslim edildi olarak işaretle"""
        self.status = 'DELIVERED'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        """Bildirimi başarısız olarak işaretle"""
        self.status = 'FAILED'
        self.error_message = error_message
        self.retry_count += 1
        self.save()


class AlarmSuppression(models.Model):
    """Alarm bastırma"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Bastırma Adı"), max_length=100)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Bastırma koşulları
    alarm_types = models.JSONField(_("Alarm Tipleri"), default=list, blank=True)
    severity_levels = models.JSONField(_("Önem Seviyeleri"), default=list, blank=True)
    source_devices = models.JSONField(_("Kaynak Cihazlar"), default=list, blank=True)
    
    # Zaman ayarları
    start_time = models.DateTimeField(_("Başlama Zamanı"))
    end_time = models.DateTimeField(_("Bitiş Zamanı"))
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Oluşturan"))
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Alarm Bastırma")
        verbose_name_plural = _("Alarm Bastırmaları")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.start_time} - {self.end_time}"
    
    def is_suppressed(self, alarm_type, severity, source_device=None):
        """Alarm bastırılıyor mu kontrol et"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        if not (self.start_time <= now <= self.end_time):
            return False
        
        if self.alarm_types and alarm_type not in self.alarm_types:
            return False
        
        if self.severity_levels and severity not in self.severity_levels:
            return False
        
        if self.source_devices and source_device and source_device not in self.source_devices:
            return False
        
        return True


class AlarmStatistics(models.Model):
    """Alarm istatistikleri"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    date = models.DateField(_("Tarih"))
    
    # Alarm sayıları
    total_alarms = models.IntegerField(_("Toplam Alarm"), default=0)
    critical_alarms = models.IntegerField(_("Kritik Alarm"), default=0)
    high_alarms = models.IntegerField(_("Yüksek Alarm"), default=0)
    medium_alarms = models.IntegerField(_("Orta Alarm"), default=0)
    low_alarms = models.IntegerField(_("Düşük Alarm"), default=0)
    
    # Durum sayıları
    active_alarms = models.IntegerField(_("Aktif Alarm"), default=0)
    acknowledged_alarms = models.IntegerField(_("Kabul Edilen Alarm"), default=0)
    resolved_alarms = models.IntegerField(_("Çözülen Alarm"), default=0)
    
    # Bildirim sayıları
    total_notifications = models.IntegerField(_("Toplam Bildirim"), default=0)
    successful_notifications = models.IntegerField(_("Başarılı Bildirim"), default=0)
    failed_notifications = models.IntegerField(_("Başarısız Bildirim"), default=0)
    
    # Performans metrikleri
    average_response_time_minutes = models.FloatField(_("Ortalama Yanıt Süresi (dakika)"), default=0)
    average_resolution_time_minutes = models.FloatField(_("Ortalama Çözüm Süresi (dakika)"), default=0)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Alarm İstatistiği")
        verbose_name_plural = _("Alarm İstatistikleri")
        unique_together = ['company', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.company.name} - {self.date}"
