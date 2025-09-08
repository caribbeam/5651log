"""
Arşivleme Politikası Modelleri
5651 uyumluluğu için log arşivleme sistemi
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from log_kayit.models import Company


class ArchivingPolicy(models.Model):
    """Arşivleme politikası"""
    
    POLICY_TYPES = [
        ('LOG_RETENTION', 'Log Saklama'),
        ('TRAFFIC_RETENTION', 'Trafik Saklama'),
        ('SIGNATURE_RETENTION', 'İmza Saklama'),
        ('REPORT_RETENTION', 'Rapor Saklama'),
        ('GENERAL_RETENTION', 'Genel Saklama'),
    ]
    
    STORAGE_TYPES = [
        ('LOCAL', 'Yerel Depolama'),
        ('WORM', 'WORM Disk'),
        ('CLOUD', 'Bulut Depolama'),
        ('TAPE', 'Tape Depolama'),
        ('HYBRID', 'Hibrit Depolama'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Politika Adı"), max_length=100)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Politika tipi
    policy_type = models.CharField(_("Politika Tipi"), max_length=20, choices=POLICY_TYPES)
    
    # Saklama süreleri
    retention_period_years = models.IntegerField(_("Saklama Süresi (Yıl)"), default=2)
    retention_period_months = models.IntegerField(_("Saklama Süresi (Ay)"), default=0)
    retention_period_days = models.IntegerField(_("Saklama Süresi (Gün)"), default=0)
    
    # Arşivleme ayarları
    archive_after_days = models.IntegerField(_("Arşivleme Süresi (Gün)"), default=30,
                                           help_text=_("Kaç gün sonra arşivlenecek"))
    compression_enabled = models.BooleanField(_("Sıkıştırma Aktif"), default=True)
    encryption_enabled = models.BooleanField(_("Şifreleme Aktif"), default=True)
    
    # Depolama ayarları
    storage_type = models.CharField(_("Depolama Tipi"), max_length=20, choices=STORAGE_TYPES, default='LOCAL')
    storage_path = models.CharField(_("Depolama Yolu"), max_length=500, blank=True)
    max_storage_size_gb = models.IntegerField(_("Maksimum Depolama Boyutu (GB)"), default=1000)
    
    # WORM disk ayarları
    worm_enabled = models.BooleanField(_("WORM Disk Aktif"), default=False)
    worm_path = models.CharField(_("WORM Disk Yolu"), max_length=500, blank=True)
    worm_append_only = models.BooleanField(_("Sadece Ekleme"), default=True)
    
    # Otomatik temizleme
    auto_cleanup_enabled = models.BooleanField(_("Otomatik Temizleme Aktif"), default=True)
    cleanup_schedule = models.CharField(_("Temizleme Zamanlaması"), max_length=50, 
                                       choices=[
                                           ('DAILY', 'Günlük'),
                                           ('WEEKLY', 'Haftalık'),
                                           ('MONTHLY', 'Aylık'),
                                           ('QUARTERLY', 'Üç Aylık'),
                                       ], default='WEEKLY')
    
    # Bildirim ayarları
    notify_before_cleanup = models.BooleanField(_("Temizleme Öncesi Bildir"), default=True)
    notify_after_cleanup = models.BooleanField(_("Temizleme Sonrası Bildir"), default=True)
    notification_recipients = models.TextField(_("Bildirim Alıcıları"), blank=True,
                                             help_text=_("Virgülle ayrılmış e-posta listesi"))
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    last_execution = models.DateTimeField(_("Son Çalıştırma"), null=True, blank=True)
    next_execution = models.DateTimeField(_("Sonraki Çalıştırma"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Arşivleme Politikası")
        verbose_name_plural = _("Arşivleme Politikaları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.get_policy_type_display()}"
    
    def get_total_retention_days(self):
        """Toplam saklama süresini gün olarak döndür"""
        total_days = 0
        total_days += self.retention_period_years * 365
        total_days += self.retention_period_months * 30
        total_days += self.retention_period_days
        return total_days
    
    def calculate_next_execution(self):
        """Sonraki çalıştırma zamanını hesapla"""
        now = timezone.now()
        
        if self.cleanup_schedule == 'DAILY':
            self.next_execution = now + timezone.timedelta(days=1)
        elif self.cleanup_schedule == 'WEEKLY':
            self.next_execution = now + timezone.timedelta(weeks=1)
        elif self.cleanup_schedule == 'MONTHLY':
            self.next_execution = now + timezone.timedelta(days=30)
        elif self.cleanup_schedule == 'QUARTERLY':
            self.next_execution = now + timezone.timedelta(days=90)
        
        self.save()


class ArchivingJob(models.Model):
    """Arşivleme işi"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Beklemede'),
        ('RUNNING', 'Çalışıyor'),
        ('COMPLETED', 'Tamamlandı'),
        ('FAILED', 'Başarısız'),
        ('CANCELLED', 'İptal Edildi'),
    ]
    
    policy = models.ForeignKey(ArchivingPolicy, on_delete=models.CASCADE, 
                              verbose_name=_("Arşivleme Politikası"), related_name='jobs')
    
    job_name = models.CharField(_("İş Adı"), max_length=200)
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # İş detayları
    start_time = models.DateTimeField(_("Başlama Zamanı"), null=True, blank=True)
    end_time = models.DateTimeField(_("Bitiş Zamanı"), null=True, blank=True)
    duration = models.DurationField(_("Süre"), null=True, blank=True)
    
    # İstatistikler
    total_records_processed = models.BigIntegerField(_("İşlenen Toplam Kayıt"), default=0)
    records_archived = models.BigIntegerField(_("Arşivlenen Kayıt"), default=0)
    records_deleted = models.BigIntegerField(_("Silinen Kayıt"), default=0)
    records_failed = models.BigIntegerField(_("Başarısız Kayıt"), default=0)
    
    # Dosya bilgileri
    archive_file_path = models.CharField(_("Arşiv Dosya Yolu"), max_length=500, blank=True)
    archive_file_size = models.BigIntegerField(_("Arşiv Dosya Boyutu (byte)"), default=0)
    archive_file_hash = models.CharField(_("Arşiv Dosya Hash"), max_length=64, blank=True)
    
    # Hata bilgileri
    error_message = models.TextField(_("Hata Mesajı"), blank=True)
    error_details = models.JSONField(_("Hata Detayları"), default=dict, blank=True)
    
    # İş detayları
    job_details = models.JSONField(_("İş Detayları"), default=dict, blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Arşivleme İşi")
        verbose_name_plural = _("Arşivleme İşleri")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.job_name} - {self.get_status_display()}"
    
    def start_job(self):
        """İşi başlat"""
        self.status = 'RUNNING'
        self.start_time = timezone.now()
        self.save()
    
    def complete_job(self):
        """İşi tamamla"""
        self.status = 'COMPLETED'
        self.end_time = timezone.now()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        self.save()
    
    def fail_job(self, error_message):
        """İşi başarısız olarak işaretle"""
        self.status = 'FAILED'
        self.end_time = timezone.now()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        self.error_message = error_message
        self.save()


class ArchivingLog(models.Model):
    """Arşivleme log kayıtları"""
    
    LOG_TYPES = [
        ('ARCHIVE', 'Arşivleme'),
        ('CLEANUP', 'Temizleme'),
        ('VERIFY', 'Doğrulama'),
        ('RESTORE', 'Geri Yükleme'),
        ('ERROR', 'Hata'),
    ]
    
    policy = models.ForeignKey(ArchivingPolicy, on_delete=models.CASCADE, 
                              verbose_name=_("Arşivleme Politikası"), related_name='logs')
    job = models.ForeignKey(ArchivingJob, on_delete=models.CASCADE, null=True, blank=True,
                           verbose_name=_("Arşivleme İşi"), related_name='logs')
    
    log_type = models.CharField(_("Log Tipi"), max_length=20, choices=LOG_TYPES)
    message = models.TextField(_("Mesaj"))
    details = models.JSONField(_("Detaylar"), default=dict, blank=True)
    
    # İstatistikler
    records_affected = models.BigIntegerField(_("Etkilenen Kayıt"), default=0)
    storage_used_bytes = models.BigIntegerField(_("Kullanılan Depolama (byte)"), default=0)
    
    timestamp = models.DateTimeField(_("Zaman"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Arşivleme Logu")
        verbose_name_plural = _("Arşivleme Logları")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.policy.name} - {self.get_log_type_display()} - {self.timestamp}"


class ArchivingStorage(models.Model):
    """Arşivleme depolama bilgileri"""
    
    STORAGE_STATUS = [
        ('ACTIVE', 'Aktif'),
        ('FULL', 'Dolu'),
        ('ERROR', 'Hata'),
        ('MAINTENANCE', 'Bakım'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Depolama Adı"), max_length=100)
    storage_type = models.CharField(_("Depolama Tipi"), max_length=20, 
                                   choices=ArchivingPolicy.STORAGE_TYPES)
    
    # Depolama bilgileri
    storage_path = models.CharField(_("Depolama Yolu"), max_length=500)
    total_capacity_gb = models.IntegerField(_("Toplam Kapasite (GB)"))
    used_capacity_gb = models.IntegerField(_("Kullanılan Kapasite (GB)"))
    available_capacity_gb = models.IntegerField(_("Kullanılabilir Kapasite (GB)"))
    
    # Durum
    status = models.CharField(_("Durum"), max_length=20, choices=STORAGE_STATUS, default='ACTIVE')
    is_encrypted = models.BooleanField(_("Şifreli"), default=True)
    is_compressed = models.BooleanField(_("Sıkıştırılmış"), default=True)
    
    # WORM disk özellikleri
    is_worm = models.BooleanField(_("WORM Disk"), default=False)
    worm_append_only = models.BooleanField(_("Sadece Ekleme"), default=True)
    
    # İstatistikler
    total_archives = models.IntegerField(_("Toplam Arşiv"), default=0)
    total_size_bytes = models.BigIntegerField(_("Toplam Boyut (byte)"), default=0)
    last_archive_date = models.DateTimeField(_("Son Arşiv Tarihi"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Arşivleme Depolama")
        verbose_name_plural = _("Arşivleme Depolamaları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.get_storage_type_display()}"
    
    def update_capacity(self):
        """Kapasite bilgilerini güncelle"""
        self.available_capacity_gb = self.total_capacity_gb - self.used_capacity_gb
        self.save()
    
    def get_usage_percentage(self):
        """Kullanım yüzdesini döndür"""
        if self.total_capacity_gb > 0:
            return (self.used_capacity_gb / self.total_capacity_gb) * 100
        return 0
