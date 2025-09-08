from django.db import models
from django.utils import timezone
from django.db.models import Sum
from log_kayit.models import Company

class NetworkDevice(models.Model):
    """Network cihazları (Router, Switch, Firewall)"""
    
    # Choices tanımları
    DEVICE_TYPE_CHOICES = [
        ('ROUTER', 'Router'),
        ('SWITCH', 'Switch'),
        ('FIREWALL', 'Firewall'),
        ('ACCESS_POINT', 'Access Point'),
        ('SERVER', 'Server'),
        ('OTHER', 'Diğer')
    ]
    
    STATUS_CHOICES = [
        ('ONLINE', 'Çevrimiçi'),
        ('OFFLINE', 'Çevrimdışı'),
        ('WARNING', 'Uyarı'),
        ('CRITICAL', 'Kritik'),
        ('MAINTENANCE', 'Bakımda')
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='network_devices')
    
    # Temel bilgiler
    name = models.CharField("Cihaz Adı", max_length=100)
    device_type = models.CharField("Cihaz Türü", max_length=50, choices=DEVICE_TYPE_CHOICES)
    
    # Network bilgileri
    ip_address = models.GenericIPAddressField("IP Adresi")
    mac_address = models.CharField("MAC Adresi", max_length=17)
    subnet_mask = models.GenericIPAddressField("Subnet Mask", default='255.255.255.0')
    gateway = models.GenericIPAddressField("Gateway", null=True, blank=True)
    
    # Cihaz bilgileri
    model = models.CharField("Model", max_length=100, blank=True)
    manufacturer = models.CharField("Üretici", max_length=100, blank=True)
    firmware_version = models.CharField("Firmware Versiyonu", max_length=50, blank=True)
    serial_number = models.CharField("Seri No", max_length=100, blank=True)
    
    # Durum bilgileri
    status = models.CharField("Durum", max_length=20, choices=STATUS_CHOICES, default='OFFLINE')
    
    # Performans metrikleri
    cpu_usage = models.FloatField("CPU Kullanımı (%)", default=0)
    memory_usage = models.FloatField("RAM Kullanımı (%)", default=0)
    temperature = models.FloatField("Sıcaklık (°C)", null=True, blank=True)
    uptime = models.DurationField("Çalışma Süresi", null=True, blank=True)
    
    # Zaman bilgileri
    last_seen = models.DateTimeField("Son Görülme", auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Network Cihazı"
        verbose_name_plural = "Network Cihazları"
        ordering = ['-last_seen']
        unique_together = ['company', 'ip_address']
    
    def __str__(self):
        return f"{self.name} ({self.ip_address}) - {self.get_status_display()}"
    
    @property
    def is_healthy(self):
        """Cihaz sağlık durumu"""
        if self.status == 'ONLINE' and self.cpu_usage < 80 and self.memory_usage < 80:
            return True
        return False

class NetworkLog(models.Model):
    """Network aktivite logları"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='network_logs')
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, related_name='logs')
    
    # Log türü
    log_type = models.CharField("Log Türü", max_length=50, choices=[
        ('CONNECTION', 'Bağlantı'),
        ('TRAFFIC', 'Trafik'),
        ('ERROR', 'Hata'),
        ('SECURITY', 'Güvenlik'),
        ('SYSTEM', 'Sistem'),
        ('USER_ACTIVITY', 'Kullanıcı Aktivitesi')
    ])
    
    # Detay bilgileri
    message = models.TextField("Mesaj")
    level = models.CharField("Seviye", max_length=20, choices=[
        ('DEBUG', 'Debug'),
        ('INFO', 'Bilgi'),
        ('WARNING', 'Uyarı'),
        ('ERROR', 'Hata'),
        ('CRITICAL', 'Kritik')
    ], default='INFO')
    
    # Network bilgileri
    source_ip = models.GenericIPAddressField("Kaynak IP", null=True, blank=True)
    destination_ip = models.GenericIPAddressField("Hedef IP", null=True, blank=True)
    source_port = models.IntegerField("Kaynak Port", null=True, blank=True)
    destination_port = models.IntegerField("Hedef Port", null=True, blank=True)
    protocol = models.CharField("Protokol", max_length=10, blank=True)
    
    # Ek bilgiler
    bytes_transferred = models.BigIntegerField("Transfer Edilen Veri (byte)", default=0)
    duration = models.FloatField("Süre (saniye)", null=True, blank=True)
    
    # Zaman
    timestamp = models.DateTimeField("Zaman", auto_now_add=True)
    
    class Meta:
        verbose_name = "Network Log"
        verbose_name_plural = "Network Logları"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['log_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.log_type} - {self.timestamp}"

class NetworkTraffic(models.Model):
    """Network trafik analizi"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='network_traffic')
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, related_name='traffic_logs')
    
    # Trafik bilgileri
    source_ip = models.GenericIPAddressField("Kaynak IP")
    destination_ip = models.GenericIPAddressField("Hedef IP")
    source_port = models.IntegerField("Kaynak Port")
    destination_port = models.IntegerField("Hedef Port")
    protocol = models.CharField("Protokol", max_length=10)
    
    # Veri transfer bilgileri
    bytes_sent = models.BigIntegerField("Gönderilen Veri (byte)", default=0)
    bytes_received = models.BigIntegerField("Alınan Veri (byte)", default=0)
    packets_sent = models.BigIntegerField("Gönderilen Paket", default=0)
    packets_received = models.BigIntegerField("Alınan Paket", default=0)
    
    # Zaman bilgileri
    start_time = models.DateTimeField("Başlangıç Zamanı")
    end_time = models.DateTimeField("Bitiş Zamanı")
    duration = models.FloatField("Süre (saniye)")
    
    # Uygulama bilgileri
    application = models.CharField("Uygulama", max_length=100, blank=True)
    user_agent = models.TextField("User Agent", blank=True)
    
    class Meta:
        verbose_name = "Network Trafik"
        verbose_name_plural = "Network Trafik"
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['company', 'start_time']),
            models.Index(fields=['device', 'start_time']),
            models.Index(fields=['source_ip', 'start_time']),
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
