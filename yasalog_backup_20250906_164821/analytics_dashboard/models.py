"""
Analytics Dashboard Models
5651log platformunda AI destekli analizler için veri modelleri
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class AnalyticsMetric(models.Model):
    """Analiz metrikleri için temel model"""
    
    METRIC_TYPES = [
        ('network_traffic', 'Network Trafik'),
        ('user_behavior', 'Kullanıcı Davranışı'),
        ('security_threats', 'Güvenlik Tehditleri'),
        ('device_performance', 'Cihaz Performansı'),
        ('vpn_usage', 'VPN Kullanımı'),
        ('hotspot_activity', 'Hotspot Aktivitesi'),
        ('firewall_events', 'Firewall Olayları'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Metrik Adı")
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES, verbose_name="Metrik Tipi")
    value = models.FloatField(verbose_name="Değer")
    unit = models.CharField(max_length=20, verbose_name="Birim")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Zaman")
    company = models.ForeignKey('log_kayit.Company', on_delete=models.CASCADE, verbose_name="Şirket")
    
    class Meta:
        verbose_name = "Analiz Metriği"
        verbose_name_plural = "Analiz Metrikleri"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.name} - {self.value} {self.unit}"


class AIInsight(models.Model):
    """AI tarafından üretilen içgörüler"""
    
    INSIGHT_TYPES = [
        ('anomaly', 'Anomali Tespiti'),
        ('trend', 'Trend Analizi'),
        ('prediction', 'Tahmin'),
        ('recommendation', 'Öneri'),
        ('risk_assessment', 'Risk Değerlendirmesi'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Düşük'),
        ('medium', 'Orta'),
        ('high', 'Yüksek'),
        ('critical', 'Kritik'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Başlık")
    description = models.TextField(verbose_name="Açıklama")
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPES, verbose_name="İçgörü Tipi")
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, verbose_name="Önem Seviyesi")
    confidence_score = models.FloatField(default=0.0, verbose_name="Güven Skoru")
    data_source = models.CharField(max_length=100, verbose_name="Veri Kaynağı")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Oluşturulma Zamanı")
    company = models.ForeignKey('log_kayit.Company', on_delete=models.CASCADE, verbose_name="Şirket")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    
    class Meta:
        verbose_name = "AI İçgörüsü"
        verbose_name_plural = "AI İçgörüleri"
        ordering = ['-timestamp', '-severity']
    
    def __str__(self):
        return f"{self.title} - {self.get_severity_display()}"


class UserBehaviorPattern(models.Model):
    """Kullanıcı davranış kalıpları"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    company = models.ForeignKey('log_kayit.Company', on_delete=models.CASCADE, verbose_name="Şirket")
    pattern_type = models.CharField(max_length=50, verbose_name="Kalıp Tipi")
    pattern_data = models.JSONField(verbose_name="Kalıp Verisi")
    confidence = models.FloatField(default=0.0, verbose_name="Güven Oranı")
    first_seen = models.DateTimeField(default=timezone.now, verbose_name="İlk Görülme")
    last_seen = models.DateTimeField(default=timezone.now, verbose_name="Son Görülme")
    frequency = models.IntegerField(default=1, verbose_name="Frekans")
    
    class Meta:
        verbose_name = "Kullanıcı Davranış Kalıbı"
        verbose_name_plural = "Kullanıcı Davranış Kalıpları"
        unique_together = ['user', 'company', 'pattern_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.pattern_type}"


class PredictiveModel(models.Model):
    """AI tahmin modelleri"""
    
    MODEL_TYPES = [
        ('traffic_prediction', 'Trafik Tahmini'),
        ('threat_prediction', 'Tehdit Tahmini'),
        ('performance_prediction', 'Performans Tahmini'),
        ('user_behavior_prediction', 'Kullanıcı Davranış Tahmini'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Model Adı")
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES, verbose_name="Model Tipi")
    version = models.CharField(max_length=20, verbose_name="Versiyon")
    accuracy = models.FloatField(default=0.0, verbose_name="Doğruluk Oranı")
    last_trained = models.DateTimeField(default=timezone.now, verbose_name="Son Eğitim")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    model_config = models.JSONField(default=dict, verbose_name="Model Konfigürasyonu")
    
    class Meta:
        verbose_name = "Tahmin Modeli"
        verbose_name_plural = "Tahmin Modelleri"
        unique_together = ['name', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class AnalyticsReport(models.Model):
    """Analiz raporları"""
    
    REPORT_TYPES = [
        ('daily', 'Günlük'),
        ('weekly', 'Haftalık'),
        ('monthly', 'Aylık'),
        ('custom', 'Özel'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Rapor Başlığı")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name="Rapor Tipi")
    company = models.ForeignKey('log_kayit.Company', on_delete=models.CASCADE, verbose_name="Şirket")
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Oluşturan")
    generated_at = models.DateTimeField(default=timezone.now, verbose_name="Oluşturulma Zamanı")
    data_period_start = models.DateTimeField(verbose_name="Veri Başlangıç")
    data_period_end = models.DateTimeField(verbose_name="Veri Bitiş")
    report_data = models.JSONField(verbose_name="Rapor Verisi")
    insights_count = models.IntegerField(default=0, verbose_name="İçgörü Sayısı")
    
    class Meta:
        verbose_name = "Analiz Raporu"
        verbose_name_plural = "Analiz Raporları"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.company.name}"
