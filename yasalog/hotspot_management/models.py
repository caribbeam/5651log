from django.db import models
from django.contrib.auth.models import User
from log_kayit.models import Company


class HotspotConfiguration(models.Model):
    """Hotspot konfigürasyonu"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    name = models.CharField(max_length=100, verbose_name='Hotspot Adı')
    ssid = models.CharField(max_length=32, verbose_name='SSID')
    password = models.CharField(max_length=64, blank=True, verbose_name='Şifre')
    is_public = models.BooleanField(default=False, verbose_name='Herkese Açık')
    
    # Bant genişliği ayarları
    max_bandwidth_mbps = models.IntegerField(default=10, verbose_name='Maksimum Bant Genişliği (Mbps)')
    max_upload_mbps = models.IntegerField(default=5, verbose_name='Maksimum Upload (Mbps)')
    max_download_mbps = models.IntegerField(default=10, verbose_name='Maksimum Download (Mbps)')
    
    # Oturum ayarları
    session_timeout_hours = models.IntegerField(default=24, verbose_name='Oturum Zaman Aşımı (Saat)')
    max_concurrent_users = models.IntegerField(default=100, verbose_name='Maksimum Eş Zamanlı Kullanıcı')
    
    # İçerik filtreleme
    enable_content_filtering = models.BooleanField(default=True, verbose_name='İçerik Filtreleme Aktif')
    block_adult_content = models.BooleanField(default=True, verbose_name='Yetişkin İçeriği Engelle')
    block_gambling = models.BooleanField(default=True, verbose_name='Kumar Sitelerini Engelle')
    block_social_media = models.BooleanField(default=False, verbose_name='Sosyal Medyayı Engelle')
    
    # Zaman kısıtlamaları
    start_time = models.TimeField(default='00:00', verbose_name='Başlangıç Saati')
    end_time = models.TimeField(default='23:59', verbose_name='Bitiş Saati')
    is_24_7 = models.BooleanField(default=True, verbose_name='7/24 Aktif')
    
    # Durum
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Zamanı')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Zamanı')
    
    class Meta:
        verbose_name = 'Hotspot Konfigürasyonu'
        verbose_name_plural = 'Hotspot Konfigürasyonları'
        unique_together = ['company', 'ssid']
    
    def __str__(self):
        return f"{self.name} ({self.ssid}) - {self.company.name}"


class BandwidthPolicy(models.Model):
    """Bant genişliği politikası"""
    POLICY_TYPES = [
        ('FREE', 'Ücretsiz'),
        ('PREMIUM', 'Premium'),
        ('BUSINESS', 'İş'),
        ('GUEST', 'Misafir'),
        ('STAFF', 'Personel'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    name = models.CharField(max_length=100, verbose_name='Politika Adı')
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES, verbose_name='Politika Tipi')
    
    # Bant genişliği limitleri
    download_limit_mbps = models.IntegerField(verbose_name='Download Limiti (Mbps)')
    upload_limit_mbps = models.IntegerField(verbose_name='Upload Limiti (Mbps)')
    daily_limit_gb = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Günlük Limit (GB)')
    
    # Zaman kısıtlamaları
    priority = models.IntegerField(default=1, verbose_name='Öncelik')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Zamanı')
    
    class Meta:
        verbose_name = 'Bant Genişliği Politikası'
        verbose_name_plural = 'Bant Genişliği Politikaları'
        unique_together = ['company', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class HotspotUser(models.Model):
    """Hotspot kullanıcısı"""
    USER_TYPES = [
        ('GUEST', 'Misafir'),
        ('REGISTERED', 'Kayıtlı'),
        ('STAFF', 'Personel'),
        ('VIP', 'VIP'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    hotspot = models.ForeignKey(HotspotConfiguration, on_delete=models.CASCADE, verbose_name='Hotspot')
    bandwidth_policy = models.ForeignKey(BandwidthPolicy, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Bant Genişliği Politikası')
    
    # Kullanıcı bilgileri
    username = models.CharField(max_length=100, verbose_name='Kullanıcı Adı')
    email = models.EmailField(blank=True, verbose_name='E-posta')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='GUEST', verbose_name='Kullanıcı Tipi')
    
    # Oturum bilgileri
    mac_address = models.CharField(max_length=17, verbose_name='MAC Adresi')
    ip_address = models.GenericIPAddressField(verbose_name='IP Adresi')
    device_info = models.TextField(blank=True, verbose_name='Cihaz Bilgisi')
    
    # Durum
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    is_blocked = models.BooleanField(default=False, verbose_name='Engellenmiş')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Zamanı')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='Son Giriş')
    
    class Meta:
        verbose_name = 'Hotspot Kullanıcısı'
        verbose_name_plural = 'Hotspot Kullanıcıları'
        unique_together = ['company', 'mac_address']
    
    def __str__(self):
        return f"{self.username} ({self.mac_address}) - {self.company.name}"


class UserSession(models.Model):
    """Kullanıcı oturumu"""
    SESSION_STATUS = [
        ('ACTIVE', 'Aktif'),
        ('EXPIRED', 'Süresi Dolmuş'),
        ('TERMINATED', 'Sonlandırıldı'),
        ('BLOCKED', 'Engellenmiş'),
    ]
    
    user = models.ForeignKey(HotspotUser, on_delete=models.CASCADE, verbose_name='Kullanıcı')
    hotspot = models.ForeignKey(HotspotConfiguration, on_delete=models.CASCADE, verbose_name='Hotspot')
    
    # Oturum bilgileri
    session_id = models.CharField(max_length=100, unique=True, verbose_name='Oturum ID')
    start_time = models.DateTimeField(auto_now_add=True, verbose_name='Başlangıç Zamanı')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='Bitiş Zamanı')
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='ACTIVE', verbose_name='Durum')
    
    # Kullanım istatistikleri
    bytes_uploaded = models.BigIntegerField(default=0, verbose_name='Upload (Byte)')
    bytes_downloaded = models.BigIntegerField(default=0, verbose_name='Download (Byte)')
    total_bytes = models.BigIntegerField(default=0, verbose_name='Toplam (Byte)')
    
    # Zaman bilgileri
    duration_minutes = models.IntegerField(default=0, verbose_name='Süre (Dakika)')
    
    class Meta:
        verbose_name = 'Kullanıcı Oturumu'
        verbose_name_plural = 'Kullanıcı Oturumları'
    
    def __str__(self):
        return f"{self.user.username} - {self.session_id}"


class ContentFilter(models.Model):
    """İçerik filtreleme kuralı"""
    FILTER_TYPES = [
        ('URL', 'URL'),
        ('DOMAIN', 'Domain'),
        ('IP', 'IP Adresi'),
        ('KEYWORD', 'Anahtar Kelime'),
        ('CATEGORY', 'Kategori'),
    ]
    
    ACTION_TYPES = [
        ('BLOCK', 'Engelle'),
        ('ALLOW', 'İzin Ver'),
        ('WARN', 'Uyarı Ver'),
        ('LOG', 'Sadece Logla'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    name = models.CharField(max_length=100, verbose_name='Kural Adı')
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPES, verbose_name='Filtre Tipi')
    action = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name='Aksiyon')
    
    # Filtre değerleri
    value = models.CharField(max_length=500, verbose_name='Filtre Değeri')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    
    # Zaman kısıtlamaları
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    priority = models.IntegerField(default=1, verbose_name='Öncelik')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Zamanı')
    
    class Meta:
        verbose_name = 'İçerik Filtresi'
        verbose_name_plural = 'İçerik Filtreleri'
        unique_together = ['company', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.filter_type}) - {self.company.name}"


class AccessLog(models.Model):
    """Erişim logu"""
    user = models.ForeignKey(HotspotUser, on_delete=models.CASCADE, verbose_name='Kullanıcı')
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, verbose_name='Oturum')
    
    # Erişim bilgileri
    url = models.URLField(verbose_name='URL')
    domain = models.CharField(max_length=255, verbose_name='Domain')
    ip_address = models.GenericIPAddressField(verbose_name='IP Adresi')
    
    # İçerik filtreleme
    content_filter = models.ForeignKey(ContentFilter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='İçerik Filtresi')
    was_blocked = models.BooleanField(default=False, verbose_name='Engellendi mi?')
    
    # Zaman
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Zaman')
    
    class Meta:
        verbose_name = 'Erişim Logu'
        verbose_name_plural = 'Erişim Logları'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['domain']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.domain} - {self.timestamp}"


class HotspotMetrics(models.Model):
    """Hotspot metrikleri"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Şirket')
    hotspot = models.ForeignKey(HotspotConfiguration, on_delete=models.CASCADE, verbose_name='Hotspot')
    
    # Zaman bilgisi
    date = models.DateField(verbose_name='Tarih')
    hour = models.IntegerField(verbose_name='Saat')
    
    # Kullanım istatistikleri
    active_users = models.IntegerField(default=0, verbose_name='Aktif Kullanıcı')
    total_sessions = models.IntegerField(default=0, verbose_name='Toplam Oturum')
    new_users = models.IntegerField(default=0, verbose_name='Yeni Kullanıcı')
    
    # Bant genişliği kullanımı
    bandwidth_used_mbps = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Kullanılan Bant Genişliği (Mbps)')
    peak_bandwidth_mbps = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Pik Bant Genişliği (Mbps)')
    
    # İçerik filtreleme
    blocked_requests = models.IntegerField(default=0, verbose_name='Engellenen İstek')
    total_requests = models.IntegerField(default=0, verbose_name='Toplam İstek')
    
    class Meta:
        verbose_name = 'Hotspot Metriği'
        verbose_name_plural = 'Hotspot Metrikleri'
        unique_together = ['company', 'hotspot', 'date', 'hour']
        indexes = [
            models.Index(fields=['date', 'hour']),
            models.Index(fields=['company', 'date']),
        ]
    
    def __str__(self):
        return f"{self.hotspot.name} - {self.date} {self.hour}:00 - {self.company.name}"
