"""
Mirror Port ve VLAN Modelleri
Network trafiği yansıtma ve VLAN desteği için
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from log_kayit.models import Company


class MirrorConfiguration(models.Model):
    """Mirror Port Konfigürasyonu"""
    
    CONFIG_TYPES = [
        ('SPAN', 'SPAN (Switch Port Analyzer)'),
        ('RSPAN', 'RSPAN (Remote SPAN)'),
        ('ERSPAN', 'ERSPAN (Encapsulated RSPAN)'),
        ('MIRROR', 'Port Mirroring'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Konfigürasyon Adı"), max_length=100)
    config_type = models.CharField(_("Konfigürasyon Tipi"), max_length=20, choices=CONFIG_TYPES)
    
    # Kaynak portlar
    source_ports = models.TextField(_("Kaynak Portlar"), help_text="Virgülle ayrılmış port listesi")
    source_vlans = models.TextField(_("Kaynak VLAN'lar"), blank=True, help_text="Virgülle ayrılmış VLAN ID listesi")
    
    # Hedef port
    destination_port = models.CharField(_("Hedef Port"), max_length=50)
    destination_ip = models.GenericIPAddressField(_("Hedef IP"), null=True, blank=True)
    
    # Filtreleme
    direction = models.CharField(_("Yön"), max_length=20, choices=[
        ('BOTH', 'Her İki Yön'),
        ('TX', 'Sadece Gönderim'),
        ('RX', 'Sadece Alım'),
    ], default='BOTH')
    
    # Protokol filtreleme
    protocol_filter = models.CharField(_("Protokol Filtresi"), max_length=100, blank=True, 
                                     help_text="TCP, UDP, ICMP vb.")
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    is_enabled = models.BooleanField(_("Etkin"), default=True)
    
    # Performans ayarları
    max_bandwidth = models.IntegerField(_("Maksimum Bant Genişliği (Mbps)"), default=1000)
    buffer_size = models.IntegerField(_("Buffer Boyutu (MB)"), default=100)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Mirror Konfigürasyonu")
        verbose_name_plural = _("Mirror Konfigürasyonları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_config_type_display()})"


class VLANConfiguration(models.Model):
    """VLAN Konfigürasyonu"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    vlan_id = models.IntegerField(_("VLAN ID"), validators=[MinValueValidator(1), MaxValueValidator(4094)])
    name = models.CharField(_("VLAN Adı"), max_length=100)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Network bilgileri
    subnet = models.CharField(_("Subnet"), max_length=18, help_text="192.168.1.0/24")
    gateway = models.GenericIPAddressField(_("Gateway"), null=True, blank=True)
    dns_servers = models.TextField(_("DNS Sunucuları"), blank=True, help_text="Virgülle ayrılmış")
    
    # Mirror ayarları
    mirror_enabled = models.BooleanField(_("Mirror Etkin"), default=True)
    mirror_config = models.ForeignKey(MirrorConfiguration, on_delete=models.SET_NULL, 
                                    null=True, blank=True, verbose_name=_("Mirror Konfigürasyonu"))
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("VLAN Konfigürasyonu")
        verbose_name_plural = _("VLAN Konfigürasyonları")
        unique_together = ['company', 'vlan_id']
        ordering = ['vlan_id']
    
    def __str__(self):
        return f"VLAN {self.vlan_id} - {self.name}"


class MirrorTraffic(models.Model):
    """Mirror Edilen Trafik"""
    
    PROTOCOL_CHOICES = [
        ('TCP', 'TCP'),
        ('UDP', 'UDP'),
        ('ICMP', 'ICMP'),
        ('HTTP', 'HTTP'),
        ('HTTPS', 'HTTPS'),
        ('FTP', 'FTP'),
        ('SSH', 'SSH'),
        ('OTHER', 'Diğer'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    mirror_config = models.ForeignKey(MirrorConfiguration, on_delete=models.CASCADE, verbose_name=_("Mirror Konfigürasyonu"))
    vlan = models.ForeignKey(VLANConfiguration, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("VLAN"))
    
    # Trafik bilgileri
    source_ip = models.GenericIPAddressField(_("Kaynak IP"))
    destination_ip = models.GenericIPAddressField(_("Hedef IP"))
    source_port = models.IntegerField(_("Kaynak Port"), null=True, blank=True)
    destination_port = models.IntegerField(_("Hedef Port"), null=True, blank=True)
    protocol = models.CharField(_("Protokol"), max_length=10, choices=PROTOCOL_CHOICES)
    
    # 5651 Uyumluluğu için NAT bilgileri
    nat_source_ip = models.GenericIPAddressField(_("NAT Kaynak IP"), null=True, blank=True)
    nat_source_port = models.IntegerField(_("NAT Kaynak Port"), null=True, blank=True)
    nat_destination_ip = models.GenericIPAddressField(_("NAT Hedef IP"), null=True, blank=True)
    nat_destination_port = models.IntegerField(_("NAT Hedef Port"), null=True, blank=True)
    
    # Lokasyon bilgileri
    source_location = models.CharField(_("Kaynak Lokasyon"), max_length=200, blank=True)
    destination_location = models.CharField(_("Hedef Lokasyon"), max_length=200, blank=True)
    device_name = models.CharField(_("Cihaz Adı"), max_length=100, blank=True)
    
    # Veri transfer bilgileri
    bytes_sent = models.BigIntegerField(_("Gönderilen Byte"), default=0)
    bytes_received = models.BigIntegerField(_("Alınan Byte"), default=0)
    packets_sent = models.IntegerField(_("Gönderilen Paket"), default=0)
    packets_received = models.IntegerField(_("Alınan Paket"), default=0)
    
    # Zaman bilgileri
    start_time = models.DateTimeField(_("Başlangıç Zamanı"))
    end_time = models.DateTimeField(_("Bitiş Zamanı"))
    duration = models.FloatField(_("Süre (saniye)"))
    
    # Ek bilgiler
    user_agent = models.TextField(_("User Agent"), blank=True)
    url = models.URLField(_("URL"), blank=True)
    content_type = models.CharField(_("Content Type"), max_length=100, blank=True)
    
    # Analiz bilgileri
    is_suspicious = models.BooleanField(_("Şüpheli"), default=False)
    threat_level = models.CharField(_("Tehdit Seviyesi"), max_length=20, choices=[
        ('LOW', 'Düşük'),
        ('MEDIUM', 'Orta'),
        ('HIGH', 'Yüksek'),
        ('CRITICAL', 'Kritik'),
    ], default='LOW')
    
    timestamp = models.DateTimeField(_("Zaman"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Mirror Trafik")
        verbose_name_plural = _("Mirror Trafik")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['mirror_config', 'timestamp']),
            models.Index(fields=['source_ip', 'destination_ip']),
            models.Index(fields=['protocol', 'timestamp']),
            models.Index(fields=['is_suspicious', 'threat_level']),
        ]
    
    def __str__(self):
        return f"{self.source_ip}:{self.source_port} -> {self.destination_ip}:{self.destination_port} ({self.protocol})"
    
    @property
    def total_bytes(self):
        """Toplam transfer edilen veri"""
        return self.bytes_sent + self.bytes_received
    
    @property
    def bandwidth_usage(self):
        """Bant genişliği kullanımı (Mbps)"""
        if self.duration > 0:
            return (self.total_bytes * 8) / (self.duration * 1000000)  # Mbps
        return 0


class MirrorDevice(models.Model):
    """Mirror Cihazları"""
    
    DEVICE_TYPES = [
        ('SWITCH', 'Switch'),
        ('ROUTER', 'Router'),
        ('FIREWALL', 'Firewall'),
        ('ACCESS_POINT', 'Access Point'),
        ('OTHER', 'Diğer'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Cihaz Adı"), max_length=100)
    device_type = models.CharField(_("Cihaz Tipi"), max_length=20, choices=DEVICE_TYPES)
    
    # Network bilgileri
    ip_address = models.GenericIPAddressField(_("IP Adresi"))
    mac_address = models.CharField(_("MAC Adresi"), max_length=17, blank=True)
    model = models.CharField(_("Model"), max_length=100, blank=True)
    manufacturer = models.CharField(_("Üretici"), max_length=100, blank=True)
    
    # Mirror ayarları
    mirror_supported = models.BooleanField(_("Mirror Desteği"), default=True)
    max_mirror_ports = models.IntegerField(_("Maksimum Mirror Port"), default=4)
    current_mirror_ports = models.IntegerField(_("Mevcut Mirror Port"), default=0)
    
    # Durum
    is_online = models.BooleanField(_("Çevrimiçi"), default=False)
    last_seen = models.DateTimeField(_("Son Görülme"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Mirror Cihazı")
        verbose_name_plural = _("Mirror Cihazları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()})"


class MirrorLog(models.Model):
    """Mirror İşlem Logları"""
    
    LOG_TYPES = [
        ('CONFIG_UPDATE', 'Konfigürasyon Güncelleme'),
        ('PORT_MIRROR', 'Port Mirror'),
        ('VLAN_MIRROR', 'VLAN Mirror'),
        ('TRAFFIC_CAPTURE', 'Trafik Yakalama'),
        ('ERROR', 'Hata'),
        ('WARNING', 'Uyarı'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    device = models.ForeignKey(MirrorDevice, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Cihaz"))
    log_type = models.CharField(_("Log Tipi"), max_length=20, choices=LOG_TYPES)
    message = models.TextField(_("Mesaj"))
    details = models.JSONField(_("Detaylar"), default=dict, blank=True)
    
    # Performans bilgileri
    traffic_volume = models.BigIntegerField(_("Trafik Hacmi (byte)"), default=0)
    packet_count = models.IntegerField(_("Paket Sayısı"), default=0)
    duration = models.FloatField(_("Süre (saniye)"), default=0)
    
    timestamp = models.DateTimeField(_("Zaman"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Mirror Logu")
        verbose_name_plural = _("Mirror Logları")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['log_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name if self.device else 'System'} - {self.get_log_type_display()} - {self.timestamp}"
