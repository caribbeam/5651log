"""
Gelişmiş Raporlama Modelleri
5651 Loglama için kapsamlı raporlama sistemi
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from log_kayit.models import Company


class ReportTemplate(models.Model):
    """Rapor şablonları"""
    
    TEMPLATE_TYPES = [
        ('daily', 'Günlük Rapor'),
        ('weekly', 'Haftalık Rapor'),
        ('monthly', 'Aylık Rapor'),
        ('quarterly', 'Çeyrek Rapor'),
        ('yearly', 'Yıllık Rapor'),
        ('custom', 'Özel Rapor'),
        ('compliance', 'Uyumluluk Raporu'),
        ('security', 'Güvenlik Raporu'),
        ('performance', 'Performans Raporu'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"), null=True, blank=True)
    name = models.CharField(_("Şablon Adı"), max_length=200)
    description = models.TextField(_("Açıklama"), blank=True)
    template_type = models.CharField(_("Şablon Tipi"), max_length=20, choices=TEMPLATE_TYPES)
    
    # Rapor türü ve formatı
    report_type = models.CharField(_("Rapor Türü"), max_length=50, default='user_activity')
    report_format = models.CharField(_("Rapor Formatı"), max_length=10, default='pdf')
    
    # JSON konfigürasyonlar
    filters = models.JSONField(_("Filtreler"), default=dict, blank=True)
    template_config = models.JSONField(_("Şablon Konfigürasyonu"), default=dict, blank=True)
    
    # Rapor içeriği
    include_user_logs = models.BooleanField(_("Kullanıcı Logları"), default=True)
    include_syslog_data = models.BooleanField(_("Syslog Verileri"), default=True)
    include_mirror_traffic = models.BooleanField(_("Mirror Trafik"), default=True)
    include_timestamp_data = models.BooleanField(_("Zaman Damgası Verileri"), default=True)
    include_security_alerts = models.BooleanField(_("Güvenlik Uyarıları"), default=True)
    
    # Filtreleme seçenekleri
    date_range_days = models.IntegerField(_("Tarih Aralığı (Gün)"), default=30)
    include_suspicious_only = models.BooleanField(_("Sadece Şüpheli Kayıtlar"), default=False)
    min_severity_level = models.IntegerField(_("Minimum Önem Seviyesi"), default=0)
    
    # Format seçenekleri
    include_charts = models.BooleanField(_("Grafikler Dahil"), default=True)
    include_statistics = models.BooleanField(_("İstatistikler Dahil"), default=True)
    include_summary = models.BooleanField(_("Özet Dahil"), default=True)
    include_details = models.BooleanField(_("Detaylar Dahil"), default=True)
    
    # Otomatik raporlama
    auto_generate = models.BooleanField(_("Otomatik Oluştur"), default=False)
    generation_frequency = models.CharField(_("Oluşturma Sıklığı"), max_length=20, 
                                          choices=[
                                              ('daily', 'Günlük'),
                                              ('weekly', 'Haftalık'),
                                              ('monthly', 'Aylık'),
                                          ], default='daily')
    generation_time = models.TimeField(_("Oluşturma Saati"), default='09:00')
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Oluşturan"))
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Rapor Şablonu")
        verbose_name_plural = _("Rapor Şablonları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class ReportSchedule(models.Model):
    """Rapor zamanlaması"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Günlük'),
        ('weekly', 'Haftalık'),
        ('monthly', 'Aylık'),
        ('quarterly', 'Çeyrek'),
        ('yearly', 'Yıllık'),
    ]
    
    DAY_CHOICES = [
        (0, 'Pazartesi'),
        (1, 'Salı'),
        (2, 'Çarşamba'),
        (3, 'Perşembe'),
        (4, 'Cuma'),
        (5, 'Cumartesi'),
        (6, 'Pazar'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"), null=True, blank=True)
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name=_("Şablon"))
    name = models.CharField(_("Zamanlama Adı"), max_length=200)
    frequency = models.CharField(_("Sıklık"), max_length=20, choices=FREQUENCY_CHOICES)
    
    # Zamanlama detayları
    run_time = models.TimeField(_("Çalışma Saati"), default='09:00')
    day_of_week = models.IntegerField(_("Haftanın Günü"), choices=DAY_CHOICES, null=True, blank=True)
    day_of_month = models.IntegerField(_("Ayın Günü"), null=True, blank=True)
    
    # Bildirim ayarları
    notify_on_success = models.BooleanField(_("Başarıda Bildir"), default=True)
    notify_on_failure = models.BooleanField(_("Hata Durumunda Bildir"), default=True)
    notification_recipients = models.TextField(_("Bildirim Alıcıları"), blank=True,
                                             help_text="Virgülle ayrılmış email listesi")
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    last_run = models.DateTimeField(_("Son Çalışma"), null=True, blank=True)
    next_run = models.DateTimeField(_("Sonraki Çalışma"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Rapor Zamanlaması")
        verbose_name_plural = _("Rapor Zamanlamaları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


class GeneratedReport(models.Model):
    """Oluşturulan raporlar"""
    
    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('generating', 'Oluşturuluyor'),
        ('completed', 'Tamamlandı'),
        ('failed', 'Başarısız'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('html', 'HTML'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"), null=True, blank=True)
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, verbose_name=_("Şablon"))
    schedule = models.ForeignKey(ReportSchedule, on_delete=models.SET_NULL, null=True, blank=True, 
                               verbose_name=_("Zamanlama"))
    
    # Rapor bilgileri
    title = models.CharField(_("Rapor Başlığı"), max_length=300)
    description = models.TextField(_("Açıklama"), blank=True)
    report_format = models.CharField(_("Format"), max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Zaman aralığı
    period_start = models.DateTimeField(_("Dönem Başlangıcı"))
    period_end = models.DateTimeField(_("Dönem Bitişi"))
    
    # Durum ve dosya
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='pending')
    file_path = models.CharField(_("Dosya Yolu"), max_length=500, blank=True)
    file_size = models.BigIntegerField(_("Dosya Boyutu"), null=True, blank=True)
    
    # İstatistikler
    total_records = models.IntegerField(_("Toplam Kayıt"), default=0)
    suspicious_records = models.IntegerField(_("Şüpheli Kayıt"), default=0)
    error_count = models.IntegerField(_("Hata Sayısı"), default=0)
    
    # Hata bilgileri
    error_message = models.TextField(_("Hata Mesajı"), blank=True)
    
    # Zaman bilgileri
    started_at = models.DateTimeField(_("Başlama Zamanı"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Tamamlanma Zamanı"), null=True, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Oluşturan"))
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Oluşturulan Rapor")
        verbose_name_plural = _("Oluşturulan Raporlar")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class ReportData(models.Model):
    """Rapor verileri"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"), null=True, blank=True)
    report = models.ForeignKey(GeneratedReport, on_delete=models.CASCADE, verbose_name=_("Rapor"))
    data_type = models.CharField(_("Veri Tipi"), max_length=50)
    data_key = models.CharField(_("Veri Anahtarı"), max_length=100)
    data_value = models.JSONField(_("Veri Değeri"))
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Rapor Verisi")
        verbose_name_plural = _("Rapor Verileri")
        ordering = ['data_type', 'data_key']
    
    def __str__(self):
        return f"{self.report.title} - {self.data_type}"


class ReportDistribution(models.Model):
    """Rapor dağıtımı"""
    
    DISTRIBUTION_TYPES = [
        ('email', 'E-posta'),
        ('ftp', 'FTP'),
        ('sftp', 'SFTP'),
        ('webhook', 'Webhook'),
        ('api', 'API'),
        ('download', 'İndirme Linki'),
    ]
    
    report = models.ForeignKey(GeneratedReport, on_delete=models.CASCADE, verbose_name=_("Rapor"))
    distribution_type = models.CharField(_("Dağıtım Tipi"), max_length=20, choices=DISTRIBUTION_TYPES)
    
    # Dağıtım ayarları
    recipient_email = models.EmailField(_("Alıcı E-posta"), blank=True)
    ftp_host = models.CharField(_("FTP Host"), max_length=200, blank=True)
    ftp_username = models.CharField(_("FTP Kullanıcı"), max_length=100, blank=True)
    ftp_password = models.CharField(_("FTP Şifre"), max_length=100, blank=True)
    ftp_path = models.CharField(_("FTP Yolu"), max_length=300, blank=True)
    webhook_url = models.URLField(_("Webhook URL"), blank=True)
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    last_sent = models.DateTimeField(_("Son Gönderim"), null=True, blank=True)
    sent_count = models.IntegerField(_("Gönderim Sayısı"), default=0)
    error_message = models.TextField(_("Hata Mesajı"), blank=True)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Rapor Dağıtımı")
        verbose_name_plural = _("Rapor Dağıtımları")
        ordering = ['distribution_type']
    
    def __str__(self):
        return f"{self.report.title} - {self.get_distribution_type_display()}"
