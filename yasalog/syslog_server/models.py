"""
Syslog Server Modelleri
Merkezi log toplama ve syslog desteği için
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from log_kayit.models import Company


class SyslogServer(models.Model):
    """Syslog Sunucu Konfigürasyonu"""
    
    PROTOCOL_CHOICES = [
        ('UDP', 'UDP'),
        ('TCP', 'TCP'),
        ('TLS', 'TLS'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Sunucu Adı"), max_length=100)
    host = models.GenericIPAddressField(_("Host IP"))
    port = models.IntegerField(_("Port"), default=514)
    protocol = models.CharField(_("Protokol"), max_length=10, choices=PROTOCOL_CHOICES, default='UDP')
    
    # Güvenlik ayarları
    use_tls = models.BooleanField(_("TLS Kullan"), default=False)
    certificate_path = models.CharField(_("Sertifika Yolu"), max_length=500, blank=True)
    private_key_path = models.CharField(_("Özel Anahtar Yolu"), max_length=500, blank=True)
    
    # Filtreleme ayarları
    allowed_facilities = models.TextField(_("İzin Verilen Facility'ler"), blank=True, 
                                        help_text="Virgülle ayrılmış facility listesi")
    allowed_priorities = models.TextField(_("İzin Verilen Priority'ler"), blank=True,
                                        help_text="Virgülle ayrılmış priority listesi")
    
    # Performans ayarları
    max_connections = models.IntegerField(_("Maksimum Bağlantı"), default=1000)
    buffer_size = models.IntegerField(_("Buffer Boyutu (MB)"), default=100)
    batch_size = models.IntegerField(_("Toplu İşlem Boyutu"), default=1000)
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    is_running = models.BooleanField(_("Çalışıyor"), default=False)
    
    # İstatistikler
    total_logs_received = models.BigIntegerField(_("Toplam Alınan Log"), default=0)
    total_connections = models.IntegerField(_("Toplam Bağlantı"), default=0)
    last_activity = models.DateTimeField(_("Son Aktivite"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Syslog Sunucu")
        verbose_name_plural = _("Syslog Sunucuları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"


class SyslogMessage(models.Model):
    """Syslog Mesajları"""
    
    FACILITY_CHOICES = [
        (0, 'kernel messages'),
        (1, 'user-level messages'),
        (2, 'mail system'),
        (3, 'system daemons'),
        (4, 'security/authorization messages'),
        (5, 'messages generated internally by syslogd'),
        (6, 'line printer subsystem'),
        (7, 'network news subsystem'),
        (8, 'UUCP subsystem'),
        (9, 'clock daemon'),
        (10, 'security/authorization messages'),
        (11, 'FTP daemon'),
        (12, 'NTP subsystem'),
        (13, 'log audit'),
        (14, 'log alert'),
        (15, 'clock daemon'),
        (16, 'local use 0'),
        (17, 'local use 1'),
        (18, 'local use 2'),
        (19, 'local use 3'),
        (20, 'local use 4'),
        (21, 'local use 5'),
        (22, 'local use 6'),
        (23, 'local use 7'),
    ]
    
    PRIORITY_CHOICES = [
        (0, 'Emergency'),
        (1, 'Alert'),
        (2, 'Critical'),
        (3, 'Error'),
        (4, 'Warning'),
        (5, 'Notice'),
        (6, 'Informational'),
        (7, 'Debug'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    server = models.ForeignKey(SyslogServer, on_delete=models.CASCADE, verbose_name=_("Syslog Sunucu"))
    
    # Syslog standart alanları
    facility = models.IntegerField(_("Facility"), choices=FACILITY_CHOICES)
    priority = models.IntegerField(_("Priority"), choices=PRIORITY_CHOICES)
    severity = models.IntegerField(_("Severity"), default=0)
    
    # Mesaj bilgileri
    timestamp = models.DateTimeField(_("Zaman Damgası"))
    hostname = models.CharField(_("Hostname"), max_length=255)
    program = models.CharField(_("Program"), max_length=100, blank=True)
    pid = models.IntegerField(_("Process ID"), null=True, blank=True)
    message = models.TextField(_("Mesaj"))
    
    # Ek bilgiler
    source_ip = models.GenericIPAddressField(_("Kaynak IP"), null=True, blank=True)
    source_port = models.IntegerField(_("Kaynak Port"), null=True, blank=True)
    raw_message = models.TextField(_("Ham Mesaj"), blank=True)
    
    # Analiz bilgileri
    is_parsed = models.BooleanField(_("Parse Edildi"), default=False)
    parsed_data = models.JSONField(_("Parse Edilmiş Veri"), default=dict, blank=True)
    is_suspicious = models.BooleanField(_("Şüpheli"), default=False)
    threat_level = models.CharField(_("Tehdit Seviyesi"), max_length=20, choices=[
        ('LOW', 'Düşük'),
        ('MEDIUM', 'Orta'),
        ('HIGH', 'Yüksek'),
        ('CRITICAL', 'Kritik'),
    ], default='LOW')
    
    received_at = models.DateTimeField(_("Alınma Zamanı"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Syslog Mesajı")
        verbose_name_plural = _("Syslog Mesajları")
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['company', 'received_at']),
            models.Index(fields=['server', 'received_at']),
            models.Index(fields=['facility', 'priority']),
            models.Index(fields=['hostname', 'program']),
            models.Index(fields=['is_suspicious', 'threat_level']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.hostname} - {self.program} - {self.timestamp}"


class SyslogClient(models.Model):
    """Syslog İstemcileri"""
    
    CLIENT_TYPES = [
        ('CISCO', 'Cisco'),
        ('MIKROTIK', 'MikroTik'),
        ('FORTINET', 'Fortinet'),
        ('WINDOWS', 'Windows'),
        ('LINUX', 'Linux'),
        ('CUSTOM', 'Özel'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("İstemci Adı"), max_length=100)
    client_type = models.CharField(_("İstemci Tipi"), max_length=20, choices=CLIENT_TYPES)
    
    # Network bilgileri
    ip_address = models.GenericIPAddressField(_("IP Adresi"))
    mac_address = models.CharField(_("MAC Adresi"), max_length=17, blank=True)
    hostname = models.CharField(_("Hostname"), max_length=255, blank=True)
    
    # Konfigürasyon
    syslog_server = models.ForeignKey(SyslogServer, on_delete=models.CASCADE, verbose_name=_("Syslog Sunucu"))
    facility = models.IntegerField(_("Varsayılan Facility"), default=16)
    priority = models.IntegerField(_("Varsayılan Priority"), default=6)
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    is_online = models.BooleanField(_("Çevrimiçi"), default=False)
    last_seen = models.DateTimeField(_("Son Görülme"), null=True, blank=True)
    
    # İstatistikler
    total_messages_sent = models.BigIntegerField(_("Toplam Gönderilen Mesaj"), default=0)
    last_message_at = models.DateTimeField(_("Son Mesaj Zamanı"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Syslog İstemcisi")
        verbose_name_plural = _("Syslog İstemcileri")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_client_type_display()})"


class SyslogFilter(models.Model):
    """Syslog Filtreleri"""
    
    FILTER_TYPES = [
        ('FACILITY', 'Facility'),
        ('PRIORITY', 'Priority'),
        ('HOSTNAME', 'Hostname'),
        ('PROGRAM', 'Program'),
        ('MESSAGE', 'Mesaj İçeriği'),
        ('IP', 'IP Adresi'),
        ('REGEX', 'Regex Pattern'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Filtre Adı"), max_length=100)
    filter_type = models.CharField(_("Filtre Tipi"), max_length=20, choices=FILTER_TYPES)
    filter_value = models.CharField(_("Filtre Değeri"), max_length=500)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Aksiyon
    action = models.CharField(_("Aksiyon"), max_length=20, choices=[
        ('ACCEPT', 'Kabul Et'),
        ('REJECT', 'Reddet'),
        ('FORWARD', 'İlet'),
        ('STORE', 'Sakla'),
        ('ALERT', 'Uyarı Ver'),
    ], default='ACCEPT')
    
    # Öncelik
    priority = models.IntegerField(_("Öncelik"), default=1, help_text="Düşük sayı = yüksek öncelik")
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Syslog Filtresi")
        verbose_name_plural = _("Syslog Filtreleri")
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_filter_type_display()})"


class SyslogAlert(models.Model):
    """Syslog Uyarıları"""
    
    ALERT_TYPES = [
        ('THRESHOLD', 'Eşik Aşımı'),
        ('PATTERN', 'Pattern Eşleşmesi'),
        ('FREQUENCY', 'Frekans Aşımı'),
        ('ANOMALY', 'Anomali Tespiti'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Uyarı Adı"), max_length=100)
    alert_type = models.CharField(_("Uyarı Tipi"), max_length=20, choices=ALERT_TYPES)
    
    # Uyarı koşulları
    condition = models.TextField(_("Koşul"), help_text="Uyarı koşulu")
    threshold_value = models.IntegerField(_("Eşik Değeri"), null=True, blank=True)
    time_window = models.IntegerField(_("Zaman Penceresi (dakika)"), default=5)
    
    # Bildirim ayarları
    notify_email = models.BooleanField(_("E-posta Bildirimi"), default=True)
    notify_sms = models.BooleanField(_("SMS Bildirimi"), default=False)
    notification_recipients = models.TextField(_("Bildirim Alıcıları"), blank=True, 
                                             help_text="Virgülle ayrılmış e-posta listesi")
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    last_triggered = models.DateTimeField(_("Son Tetiklenme"), null=True, blank=True)
    trigger_count = models.IntegerField(_("Tetiklenme Sayısı"), default=0)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Syslog Uyarısı")
        verbose_name_plural = _("Syslog Uyarıları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_alert_type_display()})"


class SyslogStatistics(models.Model):
    """Syslog İstatistikleri"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    server = models.ForeignKey(SyslogServer, on_delete=models.CASCADE, verbose_name=_("Syslog Sunucu"))
    
    # Zaman bilgisi
    date = models.DateField(_("Tarih"))
    hour = models.IntegerField(_("Saat"), validators=[MinValueValidator(0), MaxValueValidator(23)])
    
    # İstatistikler
    total_messages = models.BigIntegerField(_("Toplam Mesaj"), default=0)
    messages_by_facility = models.JSONField(_("Facility Bazında Mesajlar"), default=dict, blank=True)
    messages_by_priority = models.JSONField(_("Priority Bazında Mesajlar"), default=dict, blank=True)
    messages_by_hostname = models.JSONField(_("Hostname Bazında Mesajlar"), default=dict, blank=True)
    
    # Performans
    avg_processing_time = models.FloatField(_("Ortalama İşlem Süresi (ms)"), default=0)
    max_processing_time = models.FloatField(_("Maksimum İşlem Süresi (ms)"), default=0)
    error_count = models.IntegerField(_("Hata Sayısı"), default=0)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Syslog İstatistiği")
        verbose_name_plural = _("Syslog İstatistikleri")
        unique_together = ['company', 'server', 'date', 'hour']
        ordering = ['-date', '-hour']
    
    def __str__(self):
        return f"{self.server.name} - {self.date} {self.hour}:00"
