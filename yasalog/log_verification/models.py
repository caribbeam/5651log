"""
Log Doğrulama Modelleri
5651 uyumluluğu için log doğrulama sistemi
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from log_kayit.models import Company
import hashlib
import json


class LogVerificationSession(models.Model):
    """Log doğrulama oturumu"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Beklemede'),
        ('PROCESSING', 'İşleniyor'),
        ('COMPLETED', 'Tamamlandı'),
        ('FAILED', 'Başarısız'),
        ('CANCELLED', 'İptal Edildi'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    session_name = models.CharField(_("Oturum Adı"), max_length=200)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Dosya bilgileri
    uploaded_file = models.FileField(_("Yüklenen Dosya"), upload_to='log_verification/')
    file_name = models.CharField(_("Dosya Adı"), max_length=255)
    file_size = models.BigIntegerField(_("Dosya Boyutu (byte)"))
    file_hash = models.CharField(_("Dosya Hash"), max_length=64, blank=True)
    
    # Doğrulama ayarları
    verification_type = models.CharField(_("Doğrulama Tipi"), max_length=25, choices=[
        ('HASH_VERIFICATION', 'Hash Doğrulama'),
        ('SIGNATURE_VERIFICATION', 'İmza Doğrulama'),
        ('INTEGRITY_CHECK', 'Bütünlük Kontrolü'),
        ('COMPLETE_VERIFICATION', 'Tam Doğrulama'),
    ], default='COMPLETE_VERIFICATION')
    
    # Durum
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='PENDING')
    progress_percentage = models.IntegerField(_("İlerleme (%)"), default=0)
    
    # Sonuçlar
    total_records = models.IntegerField(_("Toplam Kayıt"), default=0)
    verified_records = models.IntegerField(_("Doğrulanan Kayıt"), default=0)
    failed_records = models.IntegerField(_("Başarısız Kayıt"), default=0)
    modified_records = models.IntegerField(_("Değiştirilmiş Kayıt"), default=0)
    
    # Zaman bilgileri
    started_at = models.DateTimeField(_("Başlama Zamanı"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Tamamlanma Zamanı"), null=True, blank=True)
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    # Hata bilgileri
    error_message = models.TextField(_("Hata Mesajı"), blank=True)
    error_details = models.JSONField(_("Hata Detayları"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Log Doğrulama Oturumu")
        verbose_name_plural = _("Log Doğrulama Oturumları")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.session_name} - {self.get_status_display()}"
    
    def calculate_file_hash(self):
        """Dosya hash'ini hesapla"""
        if self.uploaded_file:
            hash_md5 = hashlib.md5()
            self.uploaded_file.seek(0)
            for chunk in iter(lambda: self.uploaded_file.read(4096), b""):
                hash_md5.update(chunk)
            self.file_hash = hash_md5.hexdigest()
            self.save()
    
    def start_verification(self):
        """Doğrulama işlemini başlat"""
        self.status = 'PROCESSING'
        self.started_at = timezone.now()
        self.progress_percentage = 0
        self.save()
    
    def complete_verification(self):
        """Doğrulama işlemini tamamla"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save()
    
    def fail_verification(self, error_message):
        """Doğrulama işlemini başarısız olarak işaretle"""
        self.status = 'FAILED'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()


class LogVerificationResult(models.Model):
    """Log doğrulama sonuçları"""
    
    RESULT_TYPES = [
        ('VALID', 'Geçerli'),
        ('MODIFIED', 'Değiştirilmiş'),
        ('INVALID', 'Geçersiz'),
        ('MISSING', 'Eksik'),
        ('ERROR', 'Hata'),
    ]
    
    session = models.ForeignKey(LogVerificationSession, on_delete=models.CASCADE, 
                               verbose_name=_("Doğrulama Oturumu"), related_name='results')
    
    # Log kaydı bilgileri
    log_id = models.CharField(_("Log ID"), max_length=100, blank=True)
    log_timestamp = models.DateTimeField(_("Log Zamanı"), null=True, blank=True)
    log_source = models.CharField(_("Log Kaynağı"), max_length=100, blank=True)
    
    # Doğrulama sonucu
    result_type = models.CharField(_("Sonuç Tipi"), max_length=20, choices=RESULT_TYPES)
    is_valid = models.BooleanField(_("Geçerli"), default=False)
    
    # Hash bilgileri
    original_hash = models.CharField(_("Orijinal Hash"), max_length=64, blank=True)
    calculated_hash = models.CharField(_("Hesaplanan Hash"), max_length=64, blank=True)
    hash_match = models.BooleanField(_("Hash Eşleşiyor"), default=False)
    
    # İmza bilgileri
    has_signature = models.BooleanField(_("İmza Var"), default=False)
    signature_valid = models.BooleanField(_("İmza Geçerli"), default=False)
    signature_authority = models.CharField(_("İmza Otoritesi"), max_length=100, blank=True)
    
    # Detaylar
    verification_details = models.JSONField(_("Doğrulama Detayları"), default=dict, blank=True)
    error_message = models.TextField(_("Hata Mesajı"), blank=True)
    
    verified_at = models.DateTimeField(_("Doğrulama Zamanı"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Log Doğrulama Sonucu")
        verbose_name_plural = _("Log Doğrulama Sonuçları")
        ordering = ['-verified_at']
    
    def __str__(self):
        return f"{self.session.session_name} - {self.get_result_type_display()}"


class LogIntegrityReport(models.Model):
    """Log bütünlük raporu"""
    
    REPORT_TYPES = [
        ('SUMMARY', 'Özet Rapor'),
        ('DETAILED', 'Detaylı Rapor'),
        ('COMPLIANCE', 'Uyumluluk Raporu'),
        ('EVIDENCE', 'İbraz Raporu'),
    ]
    
    session = models.ForeignKey(LogVerificationSession, on_delete=models.CASCADE, 
                               verbose_name=_("Doğrulama Oturumu"), related_name='reports')
    
    report_type = models.CharField(_("Rapor Tipi"), max_length=20, choices=REPORT_TYPES)
    report_title = models.CharField(_("Rapor Başlığı"), max_length=200)
    
    # Rapor içeriği
    report_content = models.TextField(_("Rapor İçeriği"))
    report_data = models.JSONField(_("Rapor Verisi"), default=dict, blank=True)
    
    # İstatistikler
    total_records_analyzed = models.IntegerField(_("Analiz Edilen Toplam Kayıt"), default=0)
    valid_records_count = models.IntegerField(_("Geçerli Kayıt Sayısı"), default=0)
    modified_records_count = models.IntegerField(_("Değiştirilmiş Kayıt Sayısı"), default=0)
    invalid_records_count = models.IntegerField(_("Geçersiz Kayıt Sayısı"), default=0)
    
    # Dosya bilgileri
    report_file = models.FileField(_("Rapor Dosyası"), upload_to='log_reports/', null=True, blank=True)
    report_format = models.CharField(_("Rapor Formatı"), max_length=10, choices=[
        ('PDF', 'PDF'),
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
        ('XML', 'XML'),
    ], default='PDF')
    
    # Uyumluluk bilgileri
    compliance_score = models.IntegerField(_("Uyumluluk Skoru (%)"), default=0)
    compliance_status = models.CharField(_("Uyumluluk Durumu"), max_length=20, choices=[
        ('COMPLIANT', 'Uyumlu'),
        ('PARTIALLY_COMPLIANT', 'Kısmen Uyumlu'),
        ('NON_COMPLIANT', 'Uyumsuz'),
    ], default='NON_COMPLIANT')
    
    generated_at = models.DateTimeField(_("Oluşturulma Zamanı"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Log Bütünlük Raporu")
        verbose_name_plural = _("Log Bütünlük Raporları")
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.report_title} - {self.get_report_type_display()}"
    
    def calculate_compliance_score(self):
        """Uyumluluk skorunu hesapla"""
        if self.total_records_analyzed > 0:
            valid_percentage = (self.valid_records_count / self.total_records_analyzed) * 100
            self.compliance_score = int(valid_percentage)
            
            if valid_percentage >= 95:
                self.compliance_status = 'COMPLIANT'
            elif valid_percentage >= 70:
                self.compliance_status = 'PARTIALLY_COMPLIANT'
            else:
                self.compliance_status = 'NON_COMPLIANT'
            
            self.save()


class LogVerificationTemplate(models.Model):
    """Log doğrulama şablonları"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Şablon Adı"), max_length=100)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Doğrulama ayarları
    verification_rules = models.JSONField(_("Doğrulama Kuralları"), default=dict, blank=True)
    required_fields = models.JSONField(_("Zorunlu Alanlar"), default=list, blank=True)
    hash_algorithm = models.CharField(_("Hash Algoritması"), max_length=20, 
                                     choices=[('MD5', 'MD5'), ('SHA1', 'SHA1'), ('SHA256', 'SHA256')],
                                     default='SHA256')
    
    # Rapor ayarları
    auto_generate_report = models.BooleanField(_("Otomatik Rapor Oluştur"), default=True)
    report_format = models.CharField(_("Rapor Formatı"), max_length=10, choices=[
        ('PDF', 'PDF'),
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
    ], default='PDF')
    
    is_active = models.BooleanField(_("Aktif"), default=True)
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Log Doğrulama Şablonu")
        verbose_name_plural = _("Log Doğrulama Şablonları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"
