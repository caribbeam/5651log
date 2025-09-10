from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import pyotp
import qrcode
from io import BytesIO
import base64


class TwoFactorAuth(models.Model):
    """İki faktörlü kimlik doğrulama modeli"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    secret_key = models.CharField(max_length=32, verbose_name="Secret Key")
    is_enabled = models.BooleanField(default=False, verbose_name="Aktif")
    backup_tokens = models.JSONField(default=list, blank=True, verbose_name="Yedek Tokenlar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = "Two Factor Auth"
        verbose_name_plural = "Two Factor Auth"
    
    def __str__(self):
        return f"{self.user.username} - 2FA ({'Aktif' if self.is_enabled else 'Pasif'})"
    
    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = pyotp.random_base32()
        super().save(*args, **kwargs)
    
    def get_totp(self):
        """TOTP objesi döndürür"""
        return pyotp.TOTP(self.secret_key)
    
    def verify_token(self, token):
        """Token doğrulama"""
        totp = self.get_totp()
        return totp.verify(token, valid_window=1)
    
    def verify_backup_token(self, token):
        """Yedek token doğrulama"""
        if token in self.backup_tokens:
            self.backup_tokens.remove(token)
            self.save()
            return True
        return False
    
    def generate_backup_tokens(self, count=10):
        """Yedek tokenlar oluştur"""
        import secrets
        self.backup_tokens = [secrets.token_hex(4).upper() for _ in range(count)]
        self.save()
        return self.backup_tokens
    
    def get_qr_code_url(self):
        """QR kod URL'si oluştur"""
        totp = self.get_totp()
        return totp.provisioning_uri(
            name=self.user.username,
            issuer_name="5651 Log Sistemi"
        )
    
    def get_qr_code_image(self):
        """QR kod resmi oluştur (base64)"""
        qr_url = self.get_qr_code_url()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_data = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(img_data).decode()


class TwoFactorAuthLog(models.Model):
    """2FA işlem logları"""
    
    ACTION_CHOICES = [
        ('ENABLE', 'Aktif Edildi'),
        ('DISABLE', 'Pasif Edildi'),
        ('LOGIN_SUCCESS', 'Giriş Başarılı'),
        ('LOGIN_FAILED', 'Giriş Başarısız'),
        ('BACKUP_USED', 'Yedek Token Kullanıldı'),
        ('BACKUP_GENERATED', 'Yedek Tokenlar Oluşturuldu'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="İşlem")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    user_agent = models.TextField(null=True, blank=True, verbose_name="User Agent")
    success = models.BooleanField(default=True, verbose_name="Başarılı")
    details = models.JSONField(default=dict, blank=True, verbose_name="Detaylar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    
    class Meta:
        verbose_name = "2FA Log"
        verbose_name_plural = "2FA Logları"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class TwoFactorAuthSettings(models.Model):
    """2FA sistem ayarları"""
    
    enforce_for_admins = models.BooleanField(default=True, verbose_name="Admin'ler için Zorunlu")
    enforce_for_all = models.BooleanField(default=False, verbose_name="Tüm Kullanıcılar için Zorunlu")
    backup_tokens_count = models.PositiveIntegerField(default=10, verbose_name="Yedek Token Sayısı")
    token_validity_window = models.PositiveIntegerField(default=1, verbose_name="Token Geçerlilik Penceresi")
    max_failed_attempts = models.PositiveIntegerField(default=5, verbose_name="Maksimum Başarısız Deneme")
    lockout_duration = models.PositiveIntegerField(default=300, verbose_name="Kilitleme Süresi (Saniye)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = "2FA Ayarları"
        verbose_name_plural = "2FA Ayarları"
    
    def __str__(self):
        return f"2FA Ayarları - {self.created_at.strftime('%Y-%m-%d')}"
    
    @classmethod
    def get_settings(cls):
        """Sistem ayarlarını al"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class TwoFactorAuthAttempt(models.Model):
    """2FA deneme kayıtları (brute force korunması için)"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    ip_address = models.GenericIPAddressField(verbose_name="IP Adresi")
    failed_attempts = models.PositiveIntegerField(default=0, verbose_name="Başarısız Denemeler")
    locked_until = models.DateTimeField(null=True, blank=True, verbose_name="Kilitli Olana Kadar")
    last_attempt = models.DateTimeField(auto_now=True, verbose_name="Son Deneme")
    
    class Meta:
        verbose_name = "2FA Deneme"
        verbose_name_plural = "2FA Denemeleri"
        unique_together = ['user', 'ip_address']
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.failed_attempts} başarısız"
    
    def is_locked(self):
        """Hesap kilitli mi?"""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
    
    def increment_failed_attempts(self):
        """Başarısız deneme sayısını artır"""
        settings = TwoFactorAuthSettings.get_settings()
        self.failed_attempts += 1
        
        if self.failed_attempts >= settings.max_failed_attempts:
            self.locked_until = timezone.now() + timezone.timedelta(seconds=settings.lockout_duration)
        
        self.save()
    
    def reset_attempts(self):
        """Deneme sayısını sıfırla"""
        self.failed_attempts = 0
        self.locked_until = None
        self.save()