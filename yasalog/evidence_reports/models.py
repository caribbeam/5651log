"""
İbraz Raporları Modelleri
5651 uyumluluğu için mahkeme/BTK ibraz raporları
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from log_kayit.models import Company
from django.contrib.auth.models import User


class EvidenceReport(models.Model):
    """İbraz raporu"""
    
    REPORT_TYPES = [
        ('COURT_ORDER', 'Mahkeme Kararı'),
        ('BTK_REQUEST', 'BTK Talebi'),
        ('LEGAL_REQUEST', 'Yasal Talep'),
        ('AUDIT_REQUEST', 'Denetim Talebi'),
        ('COMPLIANCE_CHECK', 'Uyumluluk Kontrolü'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Taslak'),
        ('PENDING_APPROVAL', 'Onay Bekliyor'),
        ('APPROVED', 'Onaylandı'),
        ('GENERATED', 'Oluşturuldu'),
        ('DELIVERED', 'Teslim Edildi'),
        ('REJECTED', 'Reddedildi'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Düşük'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'Yüksek'),
        ('URGENT', 'Acil'),
        ('CRITICAL', 'Kritik'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    report_type = models.CharField(_("Rapor Tipi"), max_length=20, choices=REPORT_TYPES)
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    priority = models.CharField(_("Öncelik"), max_length=15, choices=PRIORITY_LEVELS, default='NORMAL')
    
    # Talep bilgileri
    request_number = models.CharField(_("Talep Numarası"), max_length=100, unique=True)
    request_date = models.DateTimeField(_("Talep Tarihi"))
    requester_name = models.CharField(_("Talep Eden"), max_length=200)
    requester_authority = models.CharField(_("Talep Eden Kurum"), max_length=200)
    requester_contact = models.CharField(_("İletişim Bilgileri"), max_length=500, blank=True)
    
    # Rapor içeriği
    report_title = models.CharField(_("Rapor Başlığı"), max_length=300)
    report_description = models.TextField(_("Rapor Açıklaması"))
    requested_data_period = models.CharField(_("Talep Edilen Veri Dönemi"), max_length=100)
    
    # Zaman aralığı
    start_date = models.DateTimeField(_("Başlangıç Tarihi"))
    end_date = models.DateTimeField(_("Bitiş Tarihi"))
    
    # Filtreleme kriterleri
    filter_criteria = models.JSONField(_("Filtreleme Kriterleri"), default=dict, blank=True)
    include_logs = models.BooleanField(_("Log Kayıtları Dahil"), default=True)
    include_traffic = models.BooleanField(_("Trafik Verileri Dahil"), default=True)
    include_signatures = models.BooleanField(_("İmzalar Dahil"), default=True)
    include_verification = models.BooleanField(_("Doğrulama Sonuçları Dahil"), default=True)
    
    # Rapor ayarları
    report_format = models.CharField(_("Rapor Formatı"), max_length=10, choices=[
        ('PDF', 'PDF'),
        ('CSV', 'CSV'),
        ('EXCEL', 'Excel'),
        ('JSON', 'JSON'),
        ('XML', 'XML'),
    ], default='PDF')
    
    # Dosya bilgileri
    generated_file = models.FileField(_("Oluşturulan Dosya"), upload_to='evidence_reports/', null=True, blank=True)
    file_size = models.BigIntegerField(_("Dosya Boyutu (byte)"), default=0)
    file_hash = models.CharField(_("Dosya Hash"), max_length=64, blank=True)
    
    # İstatistikler
    total_records = models.BigIntegerField(_("Toplam Kayıt"), default=0)
    total_logs = models.BigIntegerField(_("Toplam Log"), default=0)
    total_traffic_records = models.BigIntegerField(_("Toplam Trafik Kaydı"), default=0)
    total_signatures = models.IntegerField(_("Toplam İmza"), default=0)
    
    # Onay süreci
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                  verbose_name=_("Oluşturan"), related_name='created_evidence_reports')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name=_("Onaylayan"), related_name='approved_evidence_reports')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name=_("Oluşturan Sistem"), related_name='generated_evidence_reports')
    
    # Zaman bilgileri
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    approved_at = models.DateTimeField(_("Onay Tarihi"), null=True, blank=True)
    generated_at = models.DateTimeField(_("Oluşturulma Tarihi"), null=True, blank=True)
    delivered_at = models.DateTimeField(_("Teslim Tarihi"), null=True, blank=True)
    deadline = models.DateTimeField(_("Teslim Tarihi"), null=True, blank=True)
    
    # Notlar
    internal_notes = models.TextField(_("İç Notlar"), blank=True)
    external_notes = models.TextField(_("Dış Notlar"), blank=True)
    
    class Meta:
        verbose_name = _("İbraz Raporu")
        verbose_name_plural = _("İbraz Raporları")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.request_number} - {self.report_title}"
    
    def generate_request_number(self):
        """Talep numarası oluştur"""
        if not self.request_number:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.request_number = f"ER-{timestamp}-{self.company.id}"
            self.save()
    
    def approve(self, user):
        """Raporu onayla"""
        self.status = 'APPROVED'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
    
    def generate_report(self, user):
        """Raporu oluştur"""
        self.status = 'GENERATED'
        self.generated_by = user
        self.generated_at = timezone.now()
        self.save()
    
    def deliver_report(self):
        """Raporu teslim et"""
        self.status = 'DELIVERED'
        self.delivered_at = timezone.now()
        self.save()


class EvidenceReportLog(models.Model):
    """İbraz raporu log kayıtları"""
    
    ACTION_TYPES = [
        ('CREATED', 'Oluşturuldu'),
        ('UPDATED', 'Güncellendi'),
        ('APPROVED', 'Onaylandı'),
        ('REJECTED', 'Reddedildi'),
        ('GENERATED', 'Oluşturuldu'),
        ('DELIVERED', 'Teslim Edildi'),
        ('DOWNLOADED', 'İndirildi'),
        ('VIEWED', 'Görüntülendi'),
    ]
    
    report = models.ForeignKey(EvidenceReport, on_delete=models.CASCADE, 
                              verbose_name=_("İbraz Raporu"), related_name='logs')
    action = models.CharField(_("İşlem"), max_length=20, choices=ACTION_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Kullanıcı"))
    
    description = models.TextField(_("Açıklama"))
    details = models.JSONField(_("Detaylar"), default=dict, blank=True)
    
    ip_address = models.GenericIPAddressField(_("IP Adresi"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True)
    
    timestamp = models.DateTimeField(_("Zaman"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("İbraz Raporu Logu")
        verbose_name_plural = _("İbraz Raporu Logları")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.report.request_number} - {self.get_action_display()}"


class EvidenceReportTemplate(models.Model):
    """İbraz raporu şablonları"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Şablon Adı"), max_length=100)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Şablon ayarları
    report_type = models.CharField(_("Rapor Tipi"), max_length=20, choices=EvidenceReport.REPORT_TYPES)
    template_content = models.TextField(_("Şablon İçeriği"))
    default_format = models.CharField(_("Varsayılan Format"), max_length=10, choices=[
        ('PDF', 'PDF'),
        ('CSV', 'CSV'),
        ('EXCEL', 'Excel'),
    ], default='PDF')
    
    # Varsayılan ayarlar
    default_include_logs = models.BooleanField(_("Varsayılan Log Dahil"), default=True)
    default_include_traffic = models.BooleanField(_("Varsayılan Trafik Dahil"), default=True)
    default_include_signatures = models.BooleanField(_("Varsayılan İmza Dahil"), default=True)
    default_include_verification = models.BooleanField(_("Varsayılan Doğrulama Dahil"), default=True)
    
    # Şablon ayarları
    is_active = models.BooleanField(_("Aktif"), default=True)
    is_default = models.BooleanField(_("Varsayılan"), default=False)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("İbraz Raporu Şablonu")
        verbose_name_plural = _("İbraz Raporu Şablonları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class EvidenceReportAccess(models.Model):
    """İbraz raporu erişim kayıtları"""
    
    ACCESS_TYPES = [
        ('VIEW', 'Görüntüleme'),
        ('DOWNLOAD', 'İndirme'),
        ('PRINT', 'Yazdırma'),
        ('EXPORT', 'Dışa Aktarma'),
    ]
    
    report = models.ForeignKey(EvidenceReport, on_delete=models.CASCADE, 
                              verbose_name=_("İbraz Raporu"), related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Kullanıcı"))
    access_type = models.CharField(_("Erişim Tipi"), max_length=20, choices=ACCESS_TYPES)
    
    ip_address = models.GenericIPAddressField(_("IP Adresi"))
    user_agent = models.TextField(_("User Agent"), blank=True)
    session_id = models.CharField(_("Oturum ID"), max_length=100, blank=True)
    
    # Erişim detayları
    access_duration = models.DurationField(_("Erişim Süresi"), null=True, blank=True)
    pages_viewed = models.IntegerField(_("Görüntülenen Sayfa"), default=0)
    data_accessed = models.JSONField(_("Erişilen Veri"), default=dict, blank=True)
    
    timestamp = models.DateTimeField(_("Erişim Zamanı"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("İbraz Raporu Erişim Kaydı")
        verbose_name_plural = _("İbraz Raporu Erişim Kayıtları")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.report.request_number} - {self.get_access_type_display()} - {self.timestamp}"
