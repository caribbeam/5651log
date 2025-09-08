"""
Log Akış İzleme Modelleri
5651 uyumluluğu için log akış monitoring sistemi
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from log_kayit.models import Company


class LogFlowMonitor(models.Model):
    """Log akış izleme sistemi"""
    
    MONITOR_TYPES = [
        ('SYSLOG', 'Syslog'),
        ('FIREWALL', 'Firewall'),
        ('HOTSPOT', 'Hotspot'),
        ('MIRROR', 'Mirror Traffic'),
        ('TIMESTAMP', 'Timestamp'),
        ('GENERAL', 'Genel'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Aktif'),
        ('INACTIVE', 'Pasif'),
        ('ERROR', 'Hata'),
        ('WARNING', 'Uyarı'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Monitor Adı"), max_length=100)
    monitor_type = models.CharField(_("Monitor Tipi"), max_length=20, choices=MONITOR_TYPES)
    
    # İzleme ayarları
    source_device = models.CharField(_("Kaynak Cihaz"), max_length=100, blank=True)
    source_ip = models.GenericIPAddressField(_("Kaynak IP"), null=True, blank=True)
    source_port = models.IntegerField(_("Kaynak Port"), null=True, blank=True)
    
    # Akış durumu
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_receiving_logs = models.BooleanField(_("Log Alıyor"), default=True)
    last_log_received = models.DateTimeField(_("Son Log Alınma"), null=True, blank=True)
    last_heartbeat = models.DateTimeField(_("Son Heartbeat"), null=True, blank=True)
    
    # İstatistikler
    total_logs_received = models.BigIntegerField(_("Toplam Alınan Log"), default=0)
    logs_per_minute = models.IntegerField(_("Dakikada Log Sayısı"), default=0)
    average_log_size = models.IntegerField(_("Ortalama Log Boyutu (byte)"), default=0)
    
    # Eşik değerleri
    warning_threshold_minutes = models.IntegerField(_("Uyarı Eşiği (dakika)"), default=5, 
                                                   help_text=_("Bu süre boyunca log gelmezse uyarı ver"))
    error_threshold_minutes = models.IntegerField(_("Hata Eşiği (dakika)"), default=15,
                                                 help_text=_("Bu süre boyunca log gelmezse hata ver"))
    
    # Bildirim ayarları
    notify_on_warning = models.BooleanField(_("Uyarıda Bildir"), default=True)
    notify_on_error = models.BooleanField(_("Hatada Bildir"), default=True)
    notification_recipients = models.TextField(_("Bildirim Alıcıları"), blank=True,
                                             help_text=_("Virgülle ayrılmış e-posta listesi"))
    
    is_active = models.BooleanField(_("Aktif"), default=True)
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Log Akış Monitörü")
        verbose_name_plural = _("Log Akış Monitörleri")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_monitor_type_display()})"
    
    def update_heartbeat(self):
        """Heartbeat güncelle"""
        self.last_heartbeat = timezone.now()
        self.save()
    
    def update_log_received(self, log_size=0):
        """Log alındı bilgisini güncelle"""
        self.last_log_received = timezone.now()
        self.total_logs_received += 1
        if log_size > 0:
            # Ortalama log boyutunu güncelle
            total_size = self.average_log_size * (self.total_logs_received - 1) + log_size
            self.average_log_size = total_size // self.total_logs_received
        self.save()
    
    def check_status(self):
        """Durum kontrolü yap"""
        if not self.is_active:
            return 'INACTIVE'
        
        now = timezone.now()
        
        if self.last_log_received:
            time_since_last_log = (now - self.last_log_received).total_seconds() / 60
            
            if time_since_last_log > self.error_threshold_minutes:
                self.status = 'ERROR'
                self.is_receiving_logs = False
            elif time_since_last_log > self.warning_threshold_minutes:
                self.status = 'WARNING'
                self.is_receiving_logs = False
            else:
                self.status = 'ACTIVE'
                self.is_receiving_logs = True
        else:
            self.status = 'ERROR'
            self.is_receiving_logs = False
        
        self.save()
        return self.status


class LogFlowAlert(models.Model):
    """Log akış uyarıları"""
    
    ALERT_TYPES = [
        ('NO_LOGS', 'Log Gelmiyor'),
        ('LOW_VOLUME', 'Düşük Log Hacmi'),
        ('HIGH_VOLUME', 'Yüksek Log Hacmi'),
        ('DEVICE_OFFLINE', 'Cihaz Çevrimdışı'),
        ('CONNECTION_LOST', 'Bağlantı Kesildi'),
        ('CONFIGURATION_ERROR', 'Konfigürasyon Hatası'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Düşük'),
        ('MEDIUM', 'Orta'),
        ('HIGH', 'Yüksek'),
        ('CRITICAL', 'Kritik'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    monitor = models.ForeignKey(LogFlowMonitor, on_delete=models.CASCADE, verbose_name=_("Monitör"))
    
    alert_type = models.CharField(_("Uyarı Tipi"), max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(_("Önem Seviyesi"), max_length=15, choices=SEVERITY_LEVELS)
    
    title = models.CharField(_("Başlık"), max_length=200)
    message = models.TextField(_("Mesaj"))
    details = models.JSONField(_("Detaylar"), default=dict, blank=True)
    
    # Zaman bilgileri
    detected_at = models.DateTimeField(_("Tespit Zamanı"), auto_now_add=True)
    acknowledged_at = models.DateTimeField(_("Kabul Zamanı"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("Çözülme Zamanı"), null=True, blank=True)
    
    # Durum
    is_acknowledged = models.BooleanField(_("Kabul Edildi"), default=False)
    is_resolved = models.BooleanField(_("Çözüldü"), default=False)
    
    # Bildirim durumu
    notification_sent = models.BooleanField(_("Bildirim Gönderildi"), default=False)
    notification_sent_at = models.DateTimeField(_("Bildirim Zamanı"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Log Akış Uyarısı")
        verbose_name_plural = _("Log Akış Uyarıları")
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"{self.monitor.name} - {self.get_alert_type_display()}"
    
    def acknowledge(self):
        """Uyarıyı kabul et"""
        self.is_acknowledged = True
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self):
        """Uyarıyı çöz"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()


class LogFlowStatistics(models.Model):
    """Log akış istatistikleri"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    monitor = models.ForeignKey(LogFlowMonitor, on_delete=models.CASCADE, verbose_name=_("Monitör"))
    
    # Zaman bilgisi
    date = models.DateField(_("Tarih"))
    hour = models.IntegerField(_("Saat"), help_text=_("0-23 arası saat"))
    
    # İstatistikler
    total_logs = models.BigIntegerField(_("Toplam Log"), default=0)
    total_bytes = models.BigIntegerField(_("Toplam Byte"), default=0)
    average_log_size = models.IntegerField(_("Ortalama Log Boyutu"), default=0)
    peak_logs_per_minute = models.IntegerField(_("Pik Log/Dakika"), default=0)
    
    # Durum bilgileri
    uptime_minutes = models.IntegerField(_("Uptime (dakika)"), default=60)
    downtime_minutes = models.IntegerField(_("Downtime (dakika)"), default=0)
    alert_count = models.IntegerField(_("Uyarı Sayısı"), default=0)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Log Akış İstatistiği")
        verbose_name_plural = _("Log Akış İstatistikleri")
        unique_together = ['company', 'monitor', 'date', 'hour']
        ordering = ['-date', '-hour']
    
    def __str__(self):
        return f"{self.monitor.name} - {self.date} {self.hour}:00"
