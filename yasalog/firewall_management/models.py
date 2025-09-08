from django.db import models
from django.utils import timezone
from log_kayit.models import Company

class FirewallRule(models.Model):
    """Güvenlik duvarı kuralları"""
    
    RULE_TYPES = [
        ('ALLOW', 'İzin Ver'),
        ('DENY', 'Reddet'),
        ('DROP', 'Düşür'),
        ('REJECT', 'Reddet ve Bildir'),
    ]
    
    PROTOCOLS = [
        ('TCP', 'TCP'),
        ('UDP', 'UDP'),
        ('ICMP', 'ICMP'),
        ('ANY', 'Tümü'),
    ]
    
    PRIORITY_LEVELS = [
        (1, 'En Düşük'),
        (2, 'Düşük'),
        (3, 'Normal'),
        (4, 'Yüksek'),
        (5, 'En Yüksek'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    name = models.CharField(max_length=100, verbose_name='Kural Adı')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    
    # Kural detayları
    rule_type = models.CharField(max_length=10, choices=RULE_TYPES, verbose_name='Kural Tipi')
    protocol = models.CharField(max_length=10, choices=PROTOCOLS, verbose_name='Protokol')
    source_ip = models.CharField(max_length=50, verbose_name='Kaynak IP', blank=True, default='ANY')
    source_port = models.CharField(max_length=20, verbose_name='Kaynak Port', blank=True, default='ANY')
    destination_ip = models.CharField(max_length=50, verbose_name='Hedef IP', blank=True, default='ANY')
    destination_port = models.CharField(max_length=20, verbose_name='Hedef Port', blank=True, default='ANY')
    
    # Kural önceliği ve durumu
    priority = models.IntegerField(choices=PRIORITY_LEVELS, default=3, verbose_name='Öncelik')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    is_enabled = models.BooleanField(default=True, verbose_name='Etkin')
    
    # Zaman ayarları
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')
    valid_from = models.DateTimeField(null=True, blank=True, verbose_name='Geçerlilik Başlangıcı')
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name='Geçerlilik Bitişi')
    
    # İstatistikler
    hit_count = models.IntegerField(default=0, verbose_name='Eşleşme Sayısı')
    last_hit = models.DateTimeField(null=True, blank=True, verbose_name='Son Eşleşme')
    
    class Meta:
        verbose_name = 'Güvenlik Duvarı Kuralı'
        verbose_name_plural = 'Güvenlik Duvarı Kuralları'
        ordering = ['-priority', 'created_at']
        unique_together = ['company', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"
    
    def is_valid(self):
        """Kuralın geçerli olup olmadığını kontrol eder"""
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return self.is_active and self.is_enabled

class FirewallPolicy(models.Model):
    """Güvenlik duvarı politikaları"""
    
    POLICY_TYPES = [
        ('SECURITY', 'Güvenlik'),
        ('COMPLIANCE', 'Uyumluluk'),
        ('PERFORMANCE', 'Performans'),
        ('MONITORING', 'İzleme'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    name = models.CharField(max_length=100, verbose_name='Politika Adı')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES, verbose_name='Politika Tipi')
    
    # Politika ayarları
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    rules = models.ManyToManyField(FirewallRule, blank=True, verbose_name='Kurallar')
    
    # Zaman ayarları
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')
    
    class Meta:
        verbose_name = 'Güvenlik Duvarı Politikası'
        verbose_name_plural = 'Güvenlik Duvarı Politikaları'
        ordering = ['-created_at']
        unique_together = ['company', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_policy_type_display()})"

class FirewallEvent(models.Model):
    """Güvenlik duvarı olayları"""
    
    EVENT_TYPES = [
        ('RULE_MATCH', 'Kural Eşleşmesi'),
        ('RULE_VIOLATION', 'Kural İhlali'),
        ('ATTACK_DETECTED', 'Saldırı Tespit Edildi'),
        ('TRAFFIC_ANOMALY', 'Trafik Anomalisi'),
        ('POLICY_UPDATE', 'Politika Güncellendi'),
        ('SYSTEM_ALERT', 'Sistem Uyarısı'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Düşük'),
        ('MEDIUM', 'Orta'),
        ('HIGH', 'Yüksek'),
        ('CRITICAL', 'Kritik'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name='Olay Tipi')
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, verbose_name='Önem Seviyesi')
    
    # Olay detayları
    source_ip = models.GenericIPAddressField(verbose_name='Kaynak IP')
    destination_ip = models.GenericIPAddressField(verbose_name='Hedef IP')
    protocol = models.CharField(max_length=10, verbose_name='Protokol')
    port = models.IntegerField(null=True, blank=True, verbose_name='Port')
    
    # Kural bilgisi
    rule = models.ForeignKey(FirewallRule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='İlgili Kural')
    policy = models.ForeignKey(FirewallPolicy, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='İlgili Politika')
    
    # Olay açıklaması
    message = models.TextField(verbose_name='Olay Mesajı')
    details = models.JSONField(default=dict, blank=True, verbose_name='Detaylar')
    
    # Zaman damgası
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Olay Zamanı')
    is_resolved = models.BooleanField(default=False, verbose_name='Çözüldü')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Çözülme Zamanı')
    
    class Meta:
        verbose_name = 'Güvenlik Duvarı Olayı'
        verbose_name_plural = 'Güvenlik Duvarı Olayları'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['source_ip', 'destination_ip']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.source_ip} -> {self.destination_ip}"
    
    def resolve(self):
        """Olayı çözüldü olarak işaretler"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()

class FirewallLog(models.Model):
    """Güvenlik duvarı log kayıtları"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Zaman Damgası')
    
    # Trafik bilgileri
    source_ip = models.GenericIPAddressField(verbose_name='Kaynak IP')
    source_port = models.IntegerField(null=True, blank=True, verbose_name='Kaynak Port')
    destination_ip = models.GenericIPAddressField(verbose_name='Hedef IP')
    destination_port = models.IntegerField(null=True, blank=True, verbose_name='Hedef Port')
    protocol = models.CharField(max_length=10, verbose_name='Protokol')
    
    # 5651 Uyumluluğu için NAT bilgileri
    nat_source_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='NAT Kaynak IP')
    nat_source_port = models.IntegerField(null=True, blank=True, verbose_name='NAT Kaynak Port')
    nat_destination_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='NAT Hedef IP')
    nat_destination_port = models.IntegerField(null=True, blank=True, verbose_name='NAT Hedef Port')
    
    # Lokasyon bilgileri
    source_location = models.CharField(max_length=200, blank=True, verbose_name='Kaynak Lokasyon')
    destination_location = models.CharField(max_length=200, blank=True, verbose_name='Hedef Lokasyon')
    device_name = models.CharField(max_length=100, blank=True, verbose_name='Cihaz Adı')
    
    # Kural eşleşmesi
    rule = models.ForeignKey(FirewallRule, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Eşleşen Kural')
    action = models.CharField(max_length=20, verbose_name='Uygulanan Aksiyon')
    
    # Trafik detayları
    bytes_sent = models.BigIntegerField(default=0, verbose_name='Gönderilen Byte')
    bytes_received = models.BigIntegerField(default=0, verbose_name='Alınan Byte')
    packets_sent = models.IntegerField(default=0, verbose_name='Gönderilen Paket')
    packets_received = models.IntegerField(default=0, verbose_name='Alınan Paket')
    
    # Ek bilgiler
    connection_duration = models.DurationField(null=True, blank=True, verbose_name='Bağlantı Süresi')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    
    class Meta:
        verbose_name = 'Güvenlik Duvarı Logu'
        verbose_name_plural = 'Güvenlik Duvarı Logları'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['source_ip', 'destination_ip']),
            models.Index(fields=['protocol', 'action']),
        ]
    
    def __str__(self):
        return f"{self.source_ip}:{self.source_port} -> {self.destination_ip}:{self.destination_port} ({self.protocol})"
