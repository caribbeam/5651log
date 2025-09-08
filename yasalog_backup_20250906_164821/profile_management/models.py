"""
Profile Management Models
5651log platformunda kullanıcı profil yönetimi için gerekli modeller
"""

from django.db import models
from django.contrib.auth.models import User
from log_kayit.models import Company

class UserProfile(models.Model):
    """Kullanıcı profil bilgileri"""
    
    PROFILE_TYPES = [
        ('personel', 'Personel'),
        ('misafir', 'Misafir'),
        ('vip', 'VIP'),
        ('ultra', 'Ultra Paket'),
        ('ust', 'Üst Paket'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Profil Adı")
    profile_code = models.IntegerField(unique=True, verbose_name="Profil Kodu")
    profile_type = models.CharField(max_length=20, choices=PROFILE_TYPES, default='personel')
    
    # Hız limitleri (Mbps)
    upload_speed = models.IntegerField(default=10, verbose_name="Upload Hızı (Mbps)")
    download_speed = models.IntegerField(default=10, verbose_name="Download Hızı (Mbps)")
    
    # Süre limitleri
    duration_days = models.IntegerField(default=0, verbose_name="Gün")
    duration_hours = models.IntegerField(default=0, verbose_name="Saat")
    duration_minutes = models.IntegerField(default=0, verbose_name="Dakika")
    duration_seconds = models.IntegerField(default=0, verbose_name="Saniye")
    
    # Kullanıcı limitleri
    shared_users = models.IntegerField(default=1, verbose_name="Paylaşılan Kullanıcı")
    max_concurrent_users = models.IntegerField(default=1, verbose_name="Maksimum Eşzamanlı Kullanıcı")
    
    # Durum bilgileri
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    is_premium = models.BooleanField(default=False, verbose_name="Premium Profil")
    
    # Şirket bilgisi
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Şirket")
    
    # Zaman bilgileri
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")
    
    class Meta:
        verbose_name = "Kullanıcı Profili"
        verbose_name_plural = "Kullanıcı Profilleri"
        ordering = ['profile_code']
        unique_together = ['profile_code', 'company']
    
    def __str__(self):
        return f"{self.name} ({self.profile_code})"
    
    def get_duration_display(self):
        """Süre bilgisini formatla"""
        parts = []
        if self.duration_days > 0:
            parts.append(f"{self.duration_days}d")
        if self.duration_hours > 0:
            parts.append(f"{self.duration_hours:02d}h")
        if self.duration_minutes > 0:
            parts.append(f"{self.duration_minutes:02d}m")
        if self.duration_seconds > 0:
            parts.append(f"{self.duration_seconds:02d}s")
        
        return " ".join(parts) if parts else "Sınırsız"
    
    def get_speed_display(self):
        """Hız bilgisini formatla"""
        return f"{self.upload_speed}M / {self.download_speed}M"

class UserProfileAssignment(models.Model):
    """Kullanıcı-profil ataması"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Profil")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Şirket")
    
    # Atama bilgileri
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Atama Tarihi")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif Atama")
    
    # Kullanım bilgileri
    current_bandwidth_used = models.BigIntegerField(default=0, verbose_name="Kullanılan Bant Genişliği (bytes)")
    session_count = models.IntegerField(default=0, verbose_name="Oturum Sayısı")
    
    class Meta:
        verbose_name = "Kullanıcı Profil Ataması"
        verbose_name_plural = "Kullanıcı Profil Atamaları"
        unique_together = ['user', 'company']
    
    def __str__(self):
        return f"{self.user.username} - {self.profile.name}"
    
    def is_expired(self):
        """Profil süresi dolmuş mu?"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
