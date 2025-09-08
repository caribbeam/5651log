from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from log_kayit.models import Company


class SecurityThreat(models.Model):
    """Güvenlik tehditleri için model"""
    THREAT_TYPES = [
        ('MALWARE', 'Zararlı Yazılım'),
        ('PHISHING', 'Oltalama Saldırısı'),
        ('DDOS', 'DDoS Saldırısı'),
        ('BRUTE_FORCE', 'Brute Force'),
        ('SQL_INJECTION', 'SQL Enjeksiyonu'),
        ('XSS', 'Cross-Site Scripting'),
        ('MAN_IN_MIDDLE', 'Ortadaki Adam Saldırısı'),
        ('PORT_SCAN', 'Port Tarama'),
        ('UNAUTHORIZED_ACCESS', 'Yetkisiz Erişim'),
        ('DATA_EXFILTRATION', 'Veri Sızıntısı'),
        ('RANSOMWARE', 'Fidye Yazılımı'),
        ('ZERO_DAY', 'Sıfır Gün Açığı'),
        ('OTHER', 'Diğer'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Düşük'),
        ('MEDIUM', 'Orta'),
        ('HIGH', 'Yüksek'),
        ('CRITICAL', 'Kritik'),
        ('EMERGENCY', 'Acil'),
    ]
    
    STATUS_CHOICES = [
        ('DETECTED', 'Tespit Edildi'),
        ('ANALYZING', 'Analiz Ediliyor'),
        ('CONFIRMED', 'Doğrulandı'),
        ('MITIGATED', 'Azaltıldı'),
        ('RESOLVED', 'Çözüldü'),
        ('FALSE_POSITIVE', 'Yanlış Pozitif'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    threat_type = models.CharField(max_length=20, choices=THREAT_TYPES, verbose_name='Tehdit Tipi')
    severity = models.CharField(max_length=15, choices=SEVERITY_LEVELS, verbose_name='Önem Seviyesi')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DETECTED', verbose_name='Durum')
    
    title = models.CharField(max_length=200, verbose_name='Başlık')
    description = models.TextField(verbose_name='Açıklama')
    source_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='Kaynak IP')
    destination_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='Hedef IP')
    source_port = models.IntegerField(blank=True, null=True, verbose_name='Kaynak Port')
    destination_port = models.IntegerField(blank=True, null=True, verbose_name='Hedef Port')
    
    detection_time = models.DateTimeField(auto_now_add=True, verbose_name='Tespit Zamanı')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='Son Güncelleme')
    resolved_time = models.DateTimeField(blank=True, null=True, verbose_name='Çözülme Zamanı')
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Atanan Kişi')
    notes = models.TextField(blank=True, verbose_name='Notlar')
    
    # Tehdit detayları
    confidence_score = models.IntegerField(default=0, verbose_name='Güven Skoru (%)')
    false_positive_probability = models.IntegerField(default=0, verbose_name='Yanlış Pozitif Olasılığı (%)')
    
    # Etiketler
    tags = models.CharField(max_length=500, blank=True, verbose_name='Etiketler')
    
    class Meta:
        verbose_name = 'Güvenlik Tehdidi'
        verbose_name_plural = 'Güvenlik Tehditleri'
        ordering = ['-detection_time']
    
    def __str__(self):
        return f"{self.get_threat_type_display()} - {self.title}"
    
    def get_severity_color(self):
        """Önem seviyesine göre renk döndürür"""
        colors = {
            'LOW': 'success',
            'MEDIUM': 'warning',
            'HIGH': 'danger',
            'CRITICAL': 'danger',
            'EMERGENCY': 'dark'
        }
        return colors.get(self.severity, 'secondary')


class SecurityAlert(models.Model):
    """Güvenlik uyarıları için model"""
    ALERT_TYPES = [
        ('THREAT_DETECTED', 'Tehdit Tespit Edildi'),
        ('ANOMALY_DETECTED', 'Anomali Tespit Edildi'),
        ('POLICY_VIOLATION', 'Politika İhlali'),
        ('SYSTEM_COMPROMISE', 'Sistem Ele Geçirildi'),
        ('DATA_BREACH', 'Veri İhlali'),
        ('NETWORK_INTRUSION', 'Ağ İhlali'),
        ('USER_BEHAVIOR', 'Kullanıcı Davranışı'),
        ('PERFORMANCE_ISSUE', 'Performans Sorunu'),
        ('COMPLIANCE_ALERT', 'Uyumluluk Uyarısı'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Düşük'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'Yüksek'),
        ('URGENT', 'Acil'),
        ('IMMEDIATE', 'Anında'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, verbose_name='Uyarı Tipi')
    priority = models.CharField(max_length=15, choices=PRIORITY_LEVELS, default='NORMAL', verbose_name='Öncelik')
    
    title = models.CharField(max_length=200, verbose_name='Başlık')
    message = models.TextField(verbose_name='Mesaj')
    details = models.JSONField(default=dict, verbose_name='Detaylar')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Zamanı')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Zamanı')
    acknowledged_at = models.DateTimeField(blank=True, null=True, verbose_name='Kabul Edilme Zamanı')
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name='Çözülme Zamanı')
    
    is_acknowledged = models.BooleanField(default=False, verbose_name='Kabul Edildi')
    is_resolved = models.BooleanField(default=False, verbose_name='Çözüldü')
    is_escalated = models.BooleanField(default=False, verbose_name='Yükseltildi')
    
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Kabul Eden', related_name='acknowledged_alerts')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Çözen', related_name='resolved_alerts')
    
    # İlişkili tehdit
    related_threat = models.ForeignKey(SecurityThreat, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='İlişkili Tehdit')
    
    class Meta:
        verbose_name = 'Güvenlik Uyarısı'
        verbose_name_plural = 'Güvenlik Uyarıları'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.title}"
    
    def get_priority_color(self):
        """Önceliğe göre renk döndürür"""
        colors = {
            'LOW': 'success',
            'NORMAL': 'info',
            'HIGH': 'warning',
            'URGENT': 'danger',
            'IMMEDIATE': 'dark'
        }
        return colors.get(self.priority, 'secondary')


class ThreatIntelligence(models.Model):
    """Tehdit istihbaratı için model"""
    INTEL_TYPES = [
        ('IP_REPUTATION', 'IP İtibarı'),
        ('DOMAIN_REPUTATION', 'Domain İtibarı'),
        ('MALWARE_SIGNATURE', 'Zararlı Yazılım İmzası'),
        ('ATTACK_PATTERN', 'Saldırı Paterni'),
        ('VULNERABILITY', 'Güvenlik Açığı'),
        ('THREAT_ACTOR', 'Tehdit Aktörü'),
        ('CAMPAIGN', 'Kampanya'),
        ('INDICATOR', 'Gösterge'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    intel_type = models.CharField(max_length=20, choices=INTEL_TYPES, verbose_name='İstihbarat Tipi')
    
    name = models.CharField(max_length=200, verbose_name='İsim')
    description = models.TextField(verbose_name='Açıklama')
    value = models.CharField(max_length=500, verbose_name='Değer')
    
    confidence = models.IntegerField(default=0, verbose_name='Güven (%)')
    severity = models.CharField(max_length=15, choices=SecurityThreat.SEVERITY_LEVELS, verbose_name='Önem Seviyesi')
    
    source = models.CharField(max_length=100, verbose_name='Kaynak')
    first_seen = models.DateTimeField(blank=True, null=True, verbose_name='İlk Görülme')
    last_seen = models.DateTimeField(auto_now=True, verbose_name='Son Görülme')
    
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    tags = models.CharField(max_length=500, blank=True, verbose_name='Etiketler')
    
    class Meta:
        verbose_name = 'Tehdit İstihbaratı'
        verbose_name_plural = 'Tehdit İstihbaratları'
        ordering = ['-last_seen']
    
    def __str__(self):
        return f"{self.get_intel_type_display()} - {self.name}"


class SecurityIncident(models.Model):
    """Güvenlik olayları için model"""
    INCIDENT_TYPES = [
        ('BREACH', 'Veri İhlali'),
        ('INTRUSION', 'Sistem İhlali'),
        ('MALWARE', 'Zararlı Yazılım'),
        ('PHISHING', 'Oltalama'),
        ('DDOS', 'DDoS Saldırısı'),
        ('INSIDER_THREAT', 'İç Tehdit'),
        ('PHYSICAL_SECURITY', 'Fiziksel Güvenlik'),
        ('COMPLIANCE_VIOLATION', 'Uyumluluk İhlali'),
        ('OTHER', 'Diğer'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Açık'),
        ('INVESTIGATING', 'Araştırılıyor'),
        ('CONTAINED', 'Sınırlandırıldı'),
        ('RESOLVED', 'Çözüldü'),
        ('CLOSED', 'Kapatıldı'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES, verbose_name='Olay Tipi')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', verbose_name='Durum')
    
    title = models.CharField(max_length=200, verbose_name='Başlık')
    description = models.TextField(verbose_name='Açıklama')
    
    discovered_at = models.DateTimeField(auto_now_add=True, verbose_name='Keşfedilme Zamanı')
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='Başlama Zamanı')
    contained_at = models.DateTimeField(blank=True, null=True, verbose_name='Sınırlandırılma Zamanı')
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name='Çözülme Zamanı')
    
    severity = models.CharField(max_length=15, choices=SecurityThreat.SEVERITY_LEVELS, verbose_name='Önem Seviyesi')
    impact_level = models.CharField(max_length=15, choices=SecurityThreat.SEVERITY_LEVELS, verbose_name='Etki Seviyesi')
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Atanan Kişi')
    notes = models.TextField(blank=True, verbose_name='Notlar')
    
    # İlişkili kayıtlar
    related_threats = models.ManyToManyField(SecurityThreat, blank=True, verbose_name='İlişkili Tehditler')
    related_alerts = models.ManyToManyField(SecurityAlert, blank=True, verbose_name='İlişkili Uyarılar')
    
    class Meta:
        verbose_name = 'Güvenlik Olayı'
        verbose_name_plural = 'Güvenlik Olayları'
        ordering = ['-discovered_at']
    
    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.title}"
    
    def get_status_color(self):
        """Duruma göre renk döndürür"""
        colors = {
            'OPEN': 'danger',
            'INVESTIGATING': 'warning',
            'CONTAINED': 'info',
            'RESOLVED': 'success',
            'CLOSED': 'secondary'
        }
        return colors.get(self.status, 'secondary')


class SecurityMetrics(models.Model):
    """Güvenlik metrikleri için model"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    date = models.DateField(verbose_name='Tarih')
    
    # Tehdit metrikleri
    total_threats = models.IntegerField(default=0, verbose_name='Toplam Tehdit')
    critical_threats = models.IntegerField(default=0, verbose_name='Kritik Tehdit')
    high_threats = models.IntegerField(default=0, verbose_name='Yüksek Tehdit')
    medium_threats = models.IntegerField(default=0, verbose_name='Orta Tehdit')
    low_threats = models.IntegerField(default=0, verbose_name='Düşük Tehdit')
    
    # Uyarı metrikleri
    total_alerts = models.IntegerField(default=0, verbose_name='Toplam Uyarı')
    acknowledged_alerts = models.IntegerField(default=0, verbose_name='Kabul Edilen Uyarı')
    resolved_alerts = models.IntegerField(default=0, verbose_name='Çözülen Uyarı')
    
    # Olay metrikleri
    total_incidents = models.IntegerField(default=0, verbose_name='Toplam Olay')
    open_incidents = models.IntegerField(default=0, verbose_name='Açık Olay')
    resolved_incidents = models.IntegerField(default=0, verbose_name='Çözülen Olay')
    
    # Performans metrikleri
    mean_time_to_detect = models.FloatField(default=0.0, verbose_name='Ortalama Tespit Süresi (Saat)')
    mean_time_to_resolve = models.FloatField(default=0.0, verbose_name='Ortalama Çözüm Süresi (Saat)')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Zamanı')
    
    class Meta:
        verbose_name = 'Güvenlik Metriği'
        verbose_name_plural = 'Güvenlik Metrikleri'
        ordering = ['-date']
        unique_together = ['company', 'date']
    
    def __str__(self):
        return f"{self.company.name} - {self.date}"
