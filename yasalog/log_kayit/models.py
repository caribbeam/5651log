from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import RegexValidator
import uuid
from .encryption import encrypt_tc_no, decrypt_tc_no, encrypt_ip_address, decrypt_ip_address, encrypt_mac_address, decrypt_mac_address


class Company(models.Model):
    name = models.CharField(_("Şirket Adı"), max_length=100)
    slug = models.SlugField(_("URL Kodu"), unique=True, blank=True)
    address = models.CharField(_("Adres"), max_length=255, blank=True)
    contact_person = models.CharField(_("Yetkili Kişi"), max_length=100, blank=True)
    phone = models.CharField(_("Telefon"), max_length=20, blank=True)
    logo = models.ImageField(_("Logo"), upload_to="company_logos/", blank=True, null=True)
    kvkk_text = models.TextField(_("KVKK Metni"), blank=True, default="")
    login_info_text = models.CharField(_("Giriş Açıklaması"), max_length=255, blank=True, default="")
    theme_color = models.CharField(_("Tema Rengi"), max_length=7, default="#007bff")
    allow_foreigners = models.BooleanField(_("Yabancı Uyruklu İzni"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Firma")
        verbose_name_plural = _("Firmalar")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(' ', '-').replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
        super().save(*args, **kwargs)


class LogKayit(models.Model):
    KIMLIK_TURU_CHOICES = [
        ('tc', _('T.C. Kimlik')),
        ('pasaport', _('Pasaport')),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Firma"), default=1, related_name='logs')
    tc_no = models.CharField(_("T.C. Kimlik No"), max_length=11, blank=True, default="", validators=[
        RegexValidator(regex=r'^\d{11}$', message=_('T.C. Kimlik No 11 haneli olmalıdır.'))
    ])
    pasaport_no = models.CharField(_("Pasaport No"), max_length=20, blank=True, default="")
    kimlik_turu = models.CharField(_("Kimlik Türü"), max_length=10, choices=KIMLIK_TURU_CHOICES, default='tc')
    ad_soyad = models.CharField(_("Ad Soyad"), max_length=100)
    telefon = models.CharField(_("Telefon"), max_length=20, blank=True, default="")
    
    # 5651 Uyumluluğu için zorunlu alanlar
    ip_adresi = models.GenericIPAddressField(_("IP Adresi"))
    mac_adresi = models.CharField(_("MAC Adresi"), max_length=17, blank=True)
    nat_ip_adresi = models.GenericIPAddressField(_("NAT IP Adresi"), null=True, blank=True, help_text=_("Network Address Translation IP adresi"))
    nat_port = models.IntegerField(_("NAT Port"), null=True, blank=True, help_text=_("Network Address Translation port numarası"))
    
    # Lokasyon bilgileri
    lokasyon = models.CharField(_("Lokasyon"), max_length=200, blank=True, help_text=_("Fiziksel konum bilgisi"))
    cihaz_adi = models.CharField(_("Cihaz Adı"), max_length=100, blank=True, help_text=_("Erişim yapılan cihaz"))
    
    giris_zamani = models.DateTimeField(_("Giriş Zamanı"), auto_now_add=True)
    sha256_hash = models.CharField(_("SHA256 Hash"), max_length=64, blank=True)
    is_suspicious = models.BooleanField(_("Şüpheli"), default=False)
    pasaport_ulkesi = models.CharField(_("Pasaport Ülkesi"), max_length=50, blank=True, default="")

    class Meta:
        verbose_name = _("Log Kayıt")
        verbose_name_plural = _("Log Kayıtları")
        ordering = ["-giris_zamani"]

    def __str__(self):
        return f"{self.tc_no or self.pasaport_no} - {self.ad_soyad} - {self.giris_zamani}"
    
    # Encryption properties
    @property
    def tc_no_decrypted(self):
        """Şifrelenmiş TC kimlik numarasını çöz"""
        if not self.tc_no:
            return self.tc_no
        try:
            return decrypt_tc_no(self.tc_no)
        except:
            return self.tc_no  # Şifreli değilse olduğu gibi döndür
    
    @property
    def ip_adresi_decrypted(self):
        """Şifrelenmiş IP adresini çöz"""
        if not self.ip_adresi:
            return self.ip_adresi
        try:
            return decrypt_ip_address(self.ip_adresi)
        except:
            return self.ip_adresi  # Şifreli değilse olduğu gibi döndür
    
    @property
    def mac_adresi_decrypted(self):
        """Şifrelenmiş MAC adresini çöz"""
        if not self.mac_adresi:
            return self.mac_adresi
        try:
            return decrypt_mac_address(self.mac_adresi)
        except:
            return self.mac_adresi  # Şifreli değilse olduğu gibi döndür
    
    def save(self, *args, **kwargs):
        """Kaydetmeden önce hassas verileri şifrele"""
        # TC kimlik numarasını şifrele
        if self.tc_no and getattr(settings, 'ENCRYPT_TC_NUMBERS', True):
            self.tc_no = encrypt_tc_no(self.tc_no)
        
        # IP adresini şifrele
        if self.ip_adresi and getattr(settings, 'ENCRYPT_IP_ADDRESSES', True):
            self.ip_adresi = encrypt_ip_address(self.ip_adresi)
        
        # MAC adresini şifrele
        if self.mac_adresi and getattr(settings, 'ENCRYPT_MAC_ADDRESSES', True):
            self.mac_adresi = encrypt_mac_address(self.mac_adresi)
        
        super().save(*args, **kwargs)


class CompanyUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Kullanıcı"))
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Firma"), related_name="users")
    ROLE_CHOICES = [
        ("admin", _("Firma Yöneticisi")),
        ("staff", _("Personel")),
        ("viewer", _("Sadece Görüntüleyici")),
    ]
    role = models.CharField(_("Rol"), max_length=16, choices=ROLE_CHOICES, default="viewer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "company")
        verbose_name = _("Firma Kullanıcısı")
        verbose_name_plural = _("Firma Kullanıcıları")

    def __str__(self):
        return f"{self.user.username} - {self.company.name} ({self.get_role_display()})"


class UserPermission(models.Model):
    """Kullanıcı yetki modeli"""
    company_user = models.OneToOneField(CompanyUser, on_delete=models.CASCADE, related_name='permissions')
    
    # Sayfa yetkileri
    can_view_dashboard = models.BooleanField(_("Dashboard Görüntüleme"), default=True)
    can_export_data = models.BooleanField(_("Veri Dışa Aktarma"), default=False)
    can_manage_users = models.BooleanField(_("Kullanıcı Yönetimi"), default=False)
    can_view_reports = models.BooleanField(_("Rapor Görüntüleme"), default=True)
    can_edit_company_settings = models.BooleanField(_("Şirket Ayarları"), default=False)
    
    # Zaman sınırlaması
    access_start_time = models.TimeField(_("Erişim Başlangıç Saati"), null=True, blank=True)
    access_end_time = models.TimeField(_("Erişim Bitiş Saati"), null=True, blank=True)
    
    # IP sınırlaması
    allowed_ips = models.TextField(_("İzin Verilen IP Adresleri"), blank=True, help_text="Her satıra bir IP")
    
    # Geçerlilik tarihi
    valid_until = models.DateField(_("Geçerlilik Tarihi"), null=True, blank=True)
    
    # İşlem logları
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Kullanıcı Yetkisi")
        verbose_name_plural = _("Kullanıcı Yetkileri")
    
    def __str__(self):
        return f"{self.company_user.user.username} - {self.company_user.company.name} Yetkileri"
    
    def is_access_allowed_now(self):
        """Şu anki zamanda erişim izni var mı?"""
        from django.utils import timezone
        now = timezone.now().time()
        
        if self.access_start_time and self.access_end_time:
            if self.access_start_time <= self.access_end_time:
                return self.access_start_time <= now <= self.access_end_time
            else:  # Gece yarısını geçen saatler
                return now >= self.access_start_time or now <= self.access_end_time
        
        return True
    
    def is_valid_date(self):
        """Geçerlilik tarihi geçmiş mi?"""
        from django.utils import timezone
        if self.valid_until:
            return timezone.now().date() <= self.valid_until
        return True
    
    def is_ip_allowed(self, ip_address):
        """IP adresi izin verilen listede mi?"""
        if not self.allowed_ips:
            return True
        
        allowed_list = [ip.strip() for ip in self.allowed_ips.split('\n') if ip.strip()]
        return ip_address in allowed_list


class UserActivityLog(models.Model):
    """Kullanıcı aktivite logu"""
    ACTION_CHOICES = [
        ('login', _('Giriş Yapıldı')),
        ('logout', _('Çıkış Yapıldı')),
        ('view_dashboard', _('Dashboard Görüntülendi')),
        ('export_data', _('Veri Dışa Aktarıldı')),
        ('manage_user', _('Kullanıcı Yönetildi')),
        ('edit_settings', _('Ayarlar Düzenlendi')),
        ('view_report', _('Rapor Görüntülendi')),
        ('unauthorized_access', _('Yetkisiz Erişim Denemesi')),
    ]
    
    company_user = models.ForeignKey(CompanyUser, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(_("İşlem"), max_length=50, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(_("IP Adresi"))
    user_agent = models.TextField(_("User Agent"), blank=True)
    details = models.TextField(_("Detaylar"), blank=True)
    timestamp = models.DateTimeField(_("Zaman"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Kullanıcı Aktivite Logu")
        verbose_name_plural = _("Kullanıcı Aktivite Logları")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.company_user.user.username} - {self.get_action_display()} - {self.timestamp}"


class CompanySettings(models.Model):
    """Şirket özel ayarları"""
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='settings')
    
    # Güvenlik ayarları
    max_login_attempts = models.IntegerField(_("Maksimum Giriş Denemesi"), default=3)
    session_timeout = models.IntegerField(_("Oturum Zaman Aşımı (dakika)"), default=60)
    require_2fa = models.BooleanField(_("İki Faktörlü Doğrulama"), default=False)
    
    # Veri ayarları
    auto_cleanup_days = models.IntegerField(_("Otomatik Temizlik (gün)"), default=730)  # 2 yıl
    backup_frequency = models.CharField(_("Yedekleme Sıklığı"), max_length=20, choices=[
        ('daily', _('Günlük')),
        ('weekly', _('Haftalık')),
        ('monthly', _('Aylık')),
    ], default='weekly')
    
    # Bildirim ayarları
    email_notifications = models.BooleanField(_("E-posta Bildirimleri"), default=True)
    notification_email = models.EmailField(_("Bildirim E-postası"), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Şirket Ayarı")
        verbose_name_plural = _("Şirket Ayarları")
    
    def __str__(self):
        return f"{self.company.name} Ayarları"