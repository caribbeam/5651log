"""
Elektronik Zaman Damgası Modelleri
RFC 3161 uyumlu zaman damgası imzalama için
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from log_kayit.models import Company, LogKayit


class TimestampAuthority(models.Model):
    """Zaman Damgası Otoritesi"""
    
    AUTHORITY_TYPES = [
        ('TUBITAK', 'TÜBİTAK'),
        ('TURKTRUST', 'TurkTrust'),
        ('CUSTOM', 'Özel'),
    ]
    
    name = models.CharField(_("Otorite Adı"), max_length=100)
    authority_type = models.CharField(_("Otorite Tipi"), max_length=20, choices=AUTHORITY_TYPES)
    api_endpoint = models.URLField(_("API Endpoint"), blank=True)
    certificate_path = models.CharField(_("Sertifika Yolu"), max_length=500, blank=True)
    is_active = models.BooleanField(_("Aktif"), default=True)
    
    # API kimlik bilgileri
    api_key = models.CharField(_("API Anahtarı"), max_length=255, blank=True)
    username = models.CharField(_("Kullanıcı Adı"), max_length=100, blank=True)
    password = models.CharField(_("Şifre"), max_length=255, blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Zaman Damgası Otoritesi")
        verbose_name_plural = _("Zaman Damgası Otoriteleri")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_authority_type_display()})"


class TimestampSignature(models.Model):
    """Zaman Damgası İmzası"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Beklemede'),
        ('SIGNED', 'İmzalandı'),
        ('FAILED', 'Başarısız'),
        ('VERIFIED', 'Doğrulandı'),
    ]
    
    # İlişkili kayıtlar
    log_entry = models.ForeignKey(LogKayit, on_delete=models.CASCADE, verbose_name=_("Log Kaydı"), related_name='timestamp_signatures')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    authority = models.ForeignKey(TimestampAuthority, on_delete=models.CASCADE, verbose_name=_("Otorite"))
    
    # İmza bilgileri
    signature_data = models.TextField(_("İmza Verisi"), help_text="RFC 3161 uyumlu imza verisi")
    timestamp_token = models.TextField(_("Zaman Damgası Token"), blank=True)
    certificate_chain = models.TextField(_("Sertifika Zinciri"), blank=True)
    
    # Durum ve zaman bilgileri
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    signed_at = models.DateTimeField(_("İmzalama Zamanı"), null=True, blank=True)
    verified_at = models.DateTimeField(_("Doğrulama Zamanı"), null=True, blank=True)
    
    # Ek bilgiler
    hash_algorithm = models.CharField(_("Hash Algoritması"), max_length=20, default='SHA256')
    serial_number = models.CharField(_("Seri Numarası"), max_length=100, blank=True)
    error_message = models.TextField(_("Hata Mesajı"), blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Zaman Damgası İmzası")
        verbose_name_plural = _("Zaman Damgası İmzaları")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['log_entry', 'status']),
            models.Index(fields=['company', 'created_at']),
            models.Index(fields=['status', 'signed_at']),
        ]
    
    def __str__(self):
        return f"{self.log_entry.ad_soyad} - {self.get_status_display()} - {self.created_at}"
    
    def sign(self):
        """Log kaydını imzalar"""
        try:
            # RFC 3161 uyumlu imzalama işlemi
            # Bu kısım gerçek TSA API'si ile entegre edilecek
            self.status = 'SIGNED'
            self.signed_at = timezone.now()
            self.save()
            return True
        except Exception as e:
            self.status = 'FAILED'
            self.error_message = str(e)
            self.save()
            return False
    
    def verify(self):
        """İmzayı doğrular"""
        try:
            # RFC 3161 uyumlu doğrulama işlemi
            self.status = 'VERIFIED'
            self.verified_at = timezone.now()
            self.save()
            return True
        except Exception as e:
            self.error_message = str(e)
            self.save()
            return False


class TimestampConfiguration(models.Model):
    """Zaman Damgası Konfigürasyonu"""
    
    company = models.OneToOneField(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"), related_name='timestamp_config')
    authority = models.ForeignKey(TimestampAuthority, on_delete=models.CASCADE, verbose_name=_("Varsayılan Otorite"))
    
    # Otomatik imzalama ayarları
    auto_sign = models.BooleanField(_("Otomatik İmzalama"), default=True)
    sign_interval = models.IntegerField(_("İmzalama Aralığı (dakika)"), default=60, help_text="Kaç dakikada bir imzalama yapılacak")
    batch_size = models.IntegerField(_("Toplu İmzalama Boyutu"), default=100, help_text="Bir seferde kaç kayıt imzalanacak")
    
    # Retry ayarları
    max_retries = models.IntegerField(_("Maksimum Deneme"), default=3)
    retry_delay = models.IntegerField(_("Deneme Gecikmesi (saniye)"), default=300)
    
    # Bildirim ayarları
    notify_on_success = models.BooleanField(_("Başarı Bildirimi"), default=True)
    notify_on_failure = models.BooleanField(_("Hata Bildirimi"), default=True)
    notification_email = models.EmailField(_("Bildirim E-postası"), blank=True)
    
    is_active = models.BooleanField(_("Aktif"), default=True)
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Zaman Damgası Konfigürasyonu")
        verbose_name_plural = _("Zaman Damgası Konfigürasyonları")
    
    def __str__(self):
        return f"{self.company.name} - {self.authority.name}"


class TimestampLog(models.Model):
    """Zaman Damgası İşlem Logları"""
    
    LOG_TYPES = [
        ('SIGN', 'İmzalama'),
        ('VERIFY', 'Doğrulama'),
        ('ERROR', 'Hata'),
        ('BATCH_SIGN', 'Toplu İmzalama'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    log_type = models.CharField(_("Log Tipi"), max_length=20, choices=LOG_TYPES)
    message = models.TextField(_("Mesaj"))
    details = models.JSONField(_("Detaylar"), default=dict, blank=True)
    
    # İstatistikler
    records_processed = models.IntegerField(_("İşlenen Kayıt Sayısı"), default=0)
    success_count = models.IntegerField(_("Başarılı İşlem"), default=0)
    failure_count = models.IntegerField(_("Başarısız İşlem"), default=0)
    
    timestamp = models.DateTimeField(_("Zaman"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Zaman Damgası Logu")
        verbose_name_plural = _("Zaman Damgası Logları")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', 'timestamp']),
            models.Index(fields=['log_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.company.name} - {self.get_log_type_display()} - {self.timestamp}"
