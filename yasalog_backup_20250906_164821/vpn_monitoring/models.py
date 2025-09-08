"""
VPN Monitoring Models
5651log platformunda VPN bağlantılarını ve kullanıcı aktivitelerini takip eder
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json

class VPNProject(models.Model):
    """VPN Proje bilgileri"""
    name = models.CharField(max_length=100, verbose_name="Proje Adı")
    description = models.TextField(blank=True, verbose_name="Açıklama")
    vpn_server_ip = models.GenericIPAddressField(verbose_name="VPN Sunucu IP")
    vpn_server_port = models.IntegerField(default=1194, verbose_name="VPN Port")
    vpn_protocol = models.CharField(
        max_length=20, 
        choices=[
            ('openvpn', 'OpenVPN'),
            ('wireguard', 'WireGuard'),
            ('ipsec', 'IPSec'),
            ('l2tp', 'L2TP'),
            ('pptp', 'PPTP'),
        ],
        default='openvpn',
        verbose_name="VPN Protokolü"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")

    class Meta:
        verbose_name = "VPN Projesi"
        verbose_name_plural = "VPN Projeleri"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.vpn_protocol})"

class VPNConnection(models.Model):
    """VPN Bağlantı bilgileri"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    project = models.ForeignKey(VPNProject, on_delete=models.CASCADE, verbose_name="Proje")
    connection_id = models.CharField(max_length=100, unique=True, verbose_name="Bağlantı ID")
    
    # Bağlantı bilgileri
    vpn_ip = models.GenericIPAddressField(verbose_name="VPN IP Adresi")
    real_ip = models.GenericIPAddressField(verbose_name="Gerçek IP Adresi")
    local_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name="Yerel IP")
    
    # Durum bilgileri
    status = models.CharField(
        max_length=20,
        choices=[
            ('connecting', 'Bağlanıyor'),
            ('connected', 'Bağlı'),
            ('disconnected', 'Bağlantı Kesildi'),
            ('error', 'Hata'),
        ],
        default='connecting',
        verbose_name="Durum"
    )
    
    # Zaman bilgileri
    connected_at = models.DateTimeField(verbose_name="Bağlanma Zamanı")
    disconnected_at = models.DateTimeField(blank=True, null=True, verbose_name="Çıkış Zamanı")
    duration = models.DurationField(blank=True, null=True, verbose_name="Bağlantı Süresi")
    
    # Teknik bilgiler
    bandwidth_in = models.BigIntegerField(default=0, verbose_name="Gelen Trafik (bytes)")
    bandwidth_out = models.BigIntegerField(default=0, verbose_name="Giden Trafik (bytes)")
    packets_in = models.BigIntegerField(default=0, verbose_name="Gelen Paket")
    packets_out = models.BigIntegerField(default=0, verbose_name="Giden Paket")
    
    # Hata bilgileri
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")
    disconnect_reason = models.CharField(
        max_length=50,
        choices=[
            ('user_disconnect', 'Kullanıcı Çıkış'),
            ('timeout', 'Zaman Aşımı'),
            ('server_error', 'Sunucu Hatası'),
            ('network_error', 'Ağ Hatası'),
            ('system_crash', 'Sistem Çökmesi'),
        ],
        blank=True,
        null=True,
        verbose_name="Çıkış Nedeni"
    )
    
    # Metadata
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    device_info = models.JSONField(default=dict, verbose_name="Cihaz Bilgileri")
    location_info = models.JSONField(default=dict, verbose_name="Konum Bilgileri")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")

    class Meta:
        verbose_name = "VPN Bağlantısı"
        verbose_name_plural = "VPN Bağlantıları"
        ordering = ['-connected_at']
        indexes = [
            models.Index(fields=['user', 'project']),
            models.Index(fields=['status', 'connected_at']),
            models.Index(fields=['vpn_ip', 'real_ip']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.status})"

    def save(self, *args, **kwargs):
        # Bağlantı süresini hesapla
        if self.disconnected_at and self.connected_at:
            self.duration = self.disconnected_at - self.connected_at
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Bağlantı aktif mi?"""
        return self.status == 'connected'

    @property
    def bandwidth_in_mb(self):
        """Gelen trafik MB cinsinden"""
        return round(self.bandwidth_in / (1024 * 1024), 2)

    @property
    def bandwidth_out_mb(self):
        """Giden trafik MB cinsinden"""
        return round(self.bandwidth_out / (1024 * 1024), 2)

class VPNUserActivity(models.Model):
    """VPN Kullanıcı aktivite log'ları"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    project = models.ForeignKey(VPNProject, on_delete=models.CASCADE, verbose_name="Proje")
    connection = models.ForeignKey(VPNConnection, on_delete=models.CASCADE, verbose_name="Bağlantı")
    
    # Aktivite bilgileri
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('login', 'Giriş'),
            ('logout', 'Çıkış'),
            ('reconnect', 'Yeniden Bağlanma'),
            ('timeout', 'Zaman Aşımı'),
            ('error', 'Hata'),
            ('bandwidth_update', 'Trafik Güncelleme'),
            ('ip_change', 'IP Değişikliği'),
        ],
        verbose_name="Aktivite Tipi"
    )
    
    # Detay bilgileri
    description = models.TextField(blank=True, verbose_name="Açıklama")
    ip_address = models.GenericIPAddressField(verbose_name="IP Adresi")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Zaman")
    
    # Teknik bilgiler
    metadata = models.JSONField(default=dict, verbose_name="Ek Bilgiler")

    class Meta:
        verbose_name = "VPN Kullanıcı Aktivitesi"
        verbose_name_plural = "VPN Kullanıcı Aktiviteleri"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'project', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} ({self.timestamp})"

class VPNServerStatus(models.Model):
    """VPN Sunucu durum bilgileri"""
    project = models.ForeignKey(VPNProject, on_delete=models.CASCADE, verbose_name="Proje")
    
    # Sunucu durumu
    status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Çevrimiçi'),
            ('offline', 'Çevrimdışı'),
            ('maintenance', 'Bakım'),
            ('error', 'Hata'),
        ],
        default='online',
        verbose_name="Durum"
    )
    
    # Sistem metrikleri
    cpu_usage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="CPU Kullanımı (%)"
    )
    memory_usage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="RAM Kullanımı (%)"
    )
    disk_usage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Disk Kullanımı (%)"
    )
    
    # Ağ metrikleri
    active_connections = models.IntegerField(default=0, verbose_name="Aktif Bağlantı")
    total_bandwidth_in = models.BigIntegerField(default=0, verbose_name="Toplam Gelen Trafik")
    total_bandwidth_out = models.BigIntegerField(default=0, verbose_name="Toplam Giden Trafik")
    
    # Zaman bilgisi
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Zaman")
    
    # Hata bilgileri
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")
    last_check = models.DateTimeField(auto_now=True, verbose_name="Son Kontrol")

    class Meta:
        verbose_name = "VPN Sunucu Durumu"
        verbose_name_plural = "VPN Sunucu Durumları"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['project', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.status} ({self.timestamp})"

    @property
    def bandwidth_in_mb(self):
        """Gelen trafik MB cinsinden"""
        return round(self.total_bandwidth_in / (1024 * 1024), 2)

    @property
    def bandwidth_out_mb(self):
        """Giden trafik MB cinsinden"""
        return round(self.total_bandwidth_out / (1024 * 1024), 2)
