"""
Device Integrations Models
5651log platformunda cihaz entegrasyonları için veri modelleri
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class DeviceType(models.Model):
    """Cihaz tipi modeli"""
    CATEGORY_CHOICES = [
        ('router', 'Router'),
        ('switch', 'Switch'),
        ('firewall', 'Firewall'),
        ('server', 'Server'),
        ('vm', 'Virtual Machine'),
        ('container', 'Container'),
        ('storage', 'Storage'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Cihaz Adı")
    vendor = models.CharField(max_length=100, verbose_name="Üretici")
    model = models.CharField(max_length=100, verbose_name="Model")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Kategori")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    capabilities = models.JSONField(default=dict, verbose_name="Özellikler")
    supported_protocols = models.JSONField(default=list, verbose_name="Desteklenen Protokoller")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = "Cihaz Tipi"
        verbose_name_plural = "Cihaz Tipleri"
        ordering = ['vendor', 'name']
    
    def __str__(self):
        return f"{self.vendor} {self.name} ({self.model})"

class Device(models.Model):
    """Cihaz modeli"""
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('maintenance', 'Bakım'),
        ('error', 'Hata'),
        ('unknown', 'Bilinmiyor'),
    ]
    
    INTEGRATION_CHOICES = [
        ('mikrotik', 'MikroTik'),
        ('vmware', 'VMware'),
        ('proxmox', 'Proxmox'),
        ('cisco', 'Cisco'),
        ('custom', 'Özel'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Cihaz Adı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    device_type = models.ForeignKey(DeviceType, on_delete=models.CASCADE, verbose_name="Cihaz Tipi")
    company = models.ForeignKey('log_kayit.Company', on_delete=models.CASCADE, verbose_name="Şirket")
    
    # Network bilgileri
    ip_address = models.GenericIPAddressField(verbose_name="IP Adresi")
    port = models.IntegerField(default=22, validators=[MinValueValidator(1), MaxValueValidator(65535)], verbose_name="Port")
    protocol = models.CharField(max_length=20, default='ssh', verbose_name="Protokol")
    credentials = models.JSONField(default=dict, verbose_name="Kimlik Bilgileri")
    
    # Durum bilgileri
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unknown', verbose_name="Durum")
    last_seen = models.DateTimeField(default=timezone.now, verbose_name="Son Görülme")
    is_monitored = models.BooleanField(default=True, verbose_name="İzleniyor")
    
    # Entegrasyon bilgileri
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_CHOICES, verbose_name="Entegrasyon Tipi")
    api_endpoint = models.URLField(blank=True, verbose_name="API Endpoint")
    api_key = models.CharField(max_length=255, blank=True, verbose_name="API Anahtarı")
    
    # Zaman bilgileri
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = "Cihaz"
        verbose_name_plural = "Cihazlar"
        ordering = ['-last_seen']
        unique_together = ['ip_address', 'company']
    
    def __str__(self):
        return f"{self.name} ({self.ip_address}) - {self.company.name}"
    
    @property
    def is_online(self):
        return self.status == 'online'
    
    @property
    def uptime(self):
        if self.last_seen:
            return timezone.now() - self.last_seen
        return None

class DeviceStatus(models.Model):
    """Cihaz durum modeli"""
    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name="Cihaz")
    status = models.CharField(max_length=20, choices=Device.STATUS_CHOICES, verbose_name="Durum")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Zaman")
    
    # Sistem metrikleri
    cpu_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="CPU Kullanımı (%)")
    memory_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="RAM Kullanımı (%)")
    disk_usage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Disk Kullanımı (%)")
    
    # Network metrikleri
    bandwidth_in = models.BigIntegerField(null=True, blank=True, verbose_name="Gelen Bandwidth (bytes)")
    bandwidth_out = models.BigIntegerField(null=True, blank=True, verbose_name="Giden Bandwidth (bytes)")
    active_connections = models.IntegerField(default=0, verbose_name="Aktif Bağlantılar")
    
    # Uyarılar
    warnings = models.JSONField(default=list, verbose_name="Uyarılar")
    errors = models.JSONField(default=list, verbose_name="Hatalar")
    critical_alerts = models.JSONField(default=list, verbose_name="Kritik Uyarılar")
    
    class Meta:
        verbose_name = "Cihaz Durumu"
        verbose_name_plural = "Cihaz Durumları"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.device.name} - {self.status} ({self.timestamp})"

class DeviceMetric(models.Model):
    """Cihaz metrik modeli"""
    METRIC_CHOICES = [
        ('cpu', 'CPU'),
        ('memory', 'Memory'),
        ('disk', 'Disk'),
        ('network', 'Network'),
        ('temperature', 'Temperature'),
        ('power', 'Power'),
        ('custom', 'Custom'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name="Cihaz")
    metric_type = models.CharField(max_length=20, choices=METRIC_CHOICES, verbose_name="Metrik Tipi")
    value = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Değer")
    unit = models.CharField(max_length=20, verbose_name="Birim")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Zaman")
    is_alert = models.BooleanField(default=False, verbose_name="Uyarı")
    
    class Meta:
        verbose_name = "Cihaz Metriği"
        verbose_name_plural = "Cihaz Metrikleri"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'metric_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.metric_type}: {self.value} {self.unit}"

class DeviceLog(models.Model):
    """Cihaz log modeli"""
    LOG_LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, verbose_name="Cihaz")
    level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, verbose_name="Seviye")
    message = models.TextField(verbose_name="Mesaj")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Zaman")
    source = models.CharField(max_length=100, default='system', verbose_name="Kaynak")
    metadata = models.JSONField(default=dict, verbose_name="Meta Veri")
    
    class Meta:
        verbose_name = "Cihaz Logu"
        verbose_name_plural = "Cihaz Logları"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'level', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.level}: {self.message[:50]}"