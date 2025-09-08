"""
Gelişmiş Bildirim Sistemi Modelleri
5651 Loglama için kapsamlı bildirim sistemi
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from log_kayit.models import Company


class NotificationChannel(models.Model):
    """Bildirim kanalları"""
    
    CHANNEL_TYPES = [
        ('email', 'E-posta'),
        ('sms', 'SMS'),
        ('push', 'Push Bildirim'),
        ('webhook', 'Webhook'),
        ('slack', 'Slack'),
        ('teams', 'Microsoft Teams'),
        ('telegram', 'Telegram'),
        ('discord', 'Discord'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Kanal Adı"), max_length=100)
    channel_type = models.CharField(_("Kanal Tipi"), max_length=20, choices=CHANNEL_TYPES)
    
    # Kanal ayarları
    is_active = models.BooleanField(_("Aktif"), default=True)
    priority = models.IntegerField(_("Öncelik"), default=1, help_text="Düşük sayı = Yüksek öncelik")
    
    # E-posta ayarları
    smtp_host = models.CharField(_("SMTP Host"), max_length=200, blank=True)
    smtp_port = models.IntegerField(_("SMTP Port"), null=True, blank=True)
    smtp_username = models.CharField(_("SMTP Kullanıcı"), max_length=100, blank=True)
    smtp_password = models.CharField(_("SMTP Şifre"), max_length=100, blank=True)
    smtp_use_tls = models.BooleanField(_("TLS Kullan"), default=True)
    from_email = models.EmailField(_("Gönderen E-posta"), blank=True)
    
    # SMS ayarları
    sms_provider = models.CharField(_("SMS Sağlayıcı"), max_length=50, blank=True)
    sms_api_key = models.CharField(_("SMS API Anahtarı"), max_length=200, blank=True)
    sms_api_secret = models.CharField(_("SMS API Gizli Anahtarı"), max_length=200, blank=True)
    sms_sender_id = models.CharField(_("SMS Gönderen ID"), max_length=20, blank=True)
    
    # Webhook ayarları
    webhook_url = models.URLField(_("Webhook URL"), blank=True)
    webhook_secret = models.CharField(_("Webhook Gizli Anahtarı"), max_length=200, blank=True)
    webhook_headers = models.JSONField(_("Webhook Başlıkları"), default=dict, blank=True)
    
    # Slack ayarları
    slack_webhook_url = models.URLField(_("Slack Webhook URL"), blank=True)
    slack_channel = models.CharField(_("Slack Kanal"), max_length=100, blank=True)
    slack_username = models.CharField(_("Slack Kullanıcı Adı"), max_length=100, blank=True)
    
    # Teams ayarları
    teams_webhook_url = models.URLField(_("Teams Webhook URL"), blank=True)
    
    # Telegram ayarları
    telegram_bot_token = models.CharField(_("Telegram Bot Token"), max_length=200, blank=True)
    telegram_chat_id = models.CharField(_("Telegram Chat ID"), max_length=100, blank=True)
    
    # Discord ayarları
    discord_webhook_url = models.URLField(_("Discord Webhook URL"), blank=True)
    
    # Test ayarları
    test_mode = models.BooleanField(_("Test Modu"), default=False)
    test_recipients = models.TextField(_("Test Alıcıları"), blank=True,
                                     help_text="Virgülle ayrılmış test alıcı listesi")
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Bildirim Kanalı")
        verbose_name_plural = _("Bildirim Kanalları")
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"


class NotificationTemplate(models.Model):
    """Bildirim şablonları"""
    
    TEMPLATE_TYPES = [
        ('security_alert', 'Güvenlik Uyarısı'),
        ('system_alert', 'Sistem Uyarısı'),
        ('report_ready', 'Rapor Hazır'),
        ('report_failed', 'Rapor Başarısız'),
        ('user_activity', 'Kullanıcı Aktivitesi'),
        ('compliance_alert', 'Uyumluluk Uyarısı'),
        ('performance_alert', 'Performans Uyarısı'),
        ('maintenance', 'Bakım Bildirimi'),
        ('custom', 'Özel'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Şablon Adı"), max_length=100)
    template_type = models.CharField(_("Şablon Tipi"), max_length=30, choices=TEMPLATE_TYPES)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # E-posta şablonu
    email_subject = models.CharField(_("E-posta Konusu"), max_length=200, blank=True)
    email_body_html = models.TextField(_("E-posta HTML İçeriği"), blank=True)
    email_body_text = models.TextField(_("E-posta Metin İçeriği"), blank=True)
    
    # SMS şablonu
    sms_message = models.TextField(_("SMS Mesajı"), blank=True, max_length=160)
    
    # Push bildirim şablonu
    push_title = models.CharField(_("Push Başlık"), max_length=100, blank=True)
    push_body = models.TextField(_("Push İçerik"), blank=True)
    push_icon = models.CharField(_("Push İkon"), max_length=100, blank=True)
    
    # Webhook şablonu
    webhook_payload = models.JSONField(_("Webhook Payload"), default=dict, blank=True)
    
    # Slack şablonu
    slack_message = models.TextField(_("Slack Mesajı"), blank=True)
    slack_color = models.CharField(_("Slack Renk"), max_length=20, blank=True, default='good')
    
    # Teams şablonu
    teams_title = models.CharField(_("Teams Başlık"), max_length=100, blank=True)
    teams_message = models.TextField(_("Teams Mesajı"), blank=True)
    
    # Telegram şablonu
    telegram_message = models.TextField(_("Telegram Mesajı"), blank=True)
    telegram_parse_mode = models.CharField(_("Telegram Parse Modu"), max_length=20, 
                                         choices=[('HTML', 'HTML'), ('Markdown', 'Markdown')], 
                                         default='HTML')
    
    # Discord şablonu
    discord_embed = models.JSONField(_("Discord Embed"), default=dict, blank=True)
    
    # Değişkenler
    available_variables = models.TextField(_("Kullanılabilir Değişkenler"), blank=True,
                                         help_text="Virgülle ayrılmış değişken listesi")
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    is_default = models.BooleanField(_("Varsayılan"), default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Oluşturan"))
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Bildirim Şablonu")
        verbose_name_plural = _("Bildirim Şablonları")
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class NotificationRule(models.Model):
    """Bildirim kuralları"""
    
    TRIGGER_TYPES = [
        ('immediate', 'Anında'),
        ('threshold', 'Eşik Aşımı'),
        ('schedule', 'Zamanlanmış'),
        ('event', 'Olay Bazlı'),
        ('condition', 'Koşul Bazlı'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    name = models.CharField(_("Kural Adı"), max_length=100)
    description = models.TextField(_("Açıklama"), blank=True)
    
    # Tetikleme ayarları
    trigger_type = models.CharField(_("Tetikleme Tipi"), max_length=20, choices=TRIGGER_TYPES)
    trigger_condition = models.TextField(_("Tetikleme Koşulu"), blank=True)
    threshold_value = models.IntegerField(_("Eşik Değeri"), null=True, blank=True)
    time_window = models.IntegerField(_("Zaman Penceresi (dakika)"), default=5)
    
    # Filtreleme
    filter_conditions = models.JSONField(_("Filtre Koşulları"), default=dict, blank=True)
    severity_levels = models.JSONField(_("Önem Seviyeleri"), default=list, blank=True)
    
    # Bildirim ayarları
    channels = models.ManyToManyField(NotificationChannel, verbose_name=_("Kanallar"))
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, verbose_name=_("Şablon"), null=True, blank=True)
    recipients = models.TextField(_("Alıcılar"), blank=True,
                                help_text="Virgülle ayrılmış alıcı listesi")
    
    # Zamanlama
    schedule_cron = models.CharField(_("Cron Zamanlama"), max_length=100, blank=True)
    schedule_timezone = models.CharField(_("Zaman Dilimi"), max_length=50, default='Europe/Istanbul')
    
    # Sınırlamalar
    max_notifications_per_hour = models.IntegerField(_("Saatlik Maksimum Bildirim"), default=10)
    max_notifications_per_day = models.IntegerField(_("Günlük Maksimum Bildirim"), default=50)
    cooldown_period = models.IntegerField(_("Bekleme Süresi (dakika)"), default=30)
    
    # Durum
    is_active = models.BooleanField(_("Aktif"), default=True)
    last_triggered = models.DateTimeField(_("Son Tetiklenme"), null=True, blank=True)
    trigger_count = models.IntegerField(_("Tetiklenme Sayısı"), default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Oluşturan"))
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Bildirim Kuralı")
        verbose_name_plural = _("Bildirim Kuralları")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"


class NotificationLog(models.Model):
    """Bildirim logları"""
    
    STATUS_CHOICES = [
        ('pending', 'Bekliyor'),
        ('sending', 'Gönderiliyor'),
        ('sent', 'Gönderildi'),
        ('delivered', 'Teslim Edildi'),
        ('failed', 'Başarısız'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    rule = models.ForeignKey(NotificationRule, on_delete=models.CASCADE, verbose_name=_("Kural"))
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE, verbose_name=_("Kanal"))
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, verbose_name=_("Şablon"))
    
    # Bildirim içeriği
    recipient = models.CharField(_("Alıcı"), max_length=200)
    subject = models.CharField(_("Konu"), max_length=300, blank=True)
    message = models.TextField(_("Mesaj"))
    
    # Durum
    status = models.CharField(_("Durum"), max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(_("Hata Mesajı"), blank=True)
    
    # Zaman bilgileri
    scheduled_at = models.DateTimeField(_("Zamanlanmış Zaman"), null=True, blank=True)
    sent_at = models.DateTimeField(_("Gönderilme Zamanı"), null=True, blank=True)
    delivered_at = models.DateTimeField(_("Teslim Zamanı"), null=True, blank=True)
    
    # Meta veriler
    metadata = models.JSONField(_("Meta Veriler"), default=dict, blank=True)
    retry_count = models.IntegerField(_("Yeniden Deneme Sayısı"), default=0)
    max_retries = models.IntegerField(_("Maksimum Yeniden Deneme"), default=3)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Bildirim Logu")
        verbose_name_plural = _("Bildirim Logları")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient} - {self.get_status_display()}"


class NotificationSubscription(models.Model):
    """Bildirim abonelikleri"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Şirket"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Kullanıcı"))
    
    # Abonelik ayarları
    email_enabled = models.BooleanField(_("E-posta Aktif"), default=True)
    sms_enabled = models.BooleanField(_("SMS Aktif"), default=False)
    push_enabled = models.BooleanField(_("Push Aktif"), default=True)
    
    # Bildirim tercihleri
    security_alerts = models.BooleanField(_("Güvenlik Uyarıları"), default=True)
    system_alerts = models.BooleanField(_("Sistem Uyarıları"), default=True)
    report_notifications = models.BooleanField(_("Rapor Bildirimleri"), default=True)
    maintenance_notifications = models.BooleanField(_("Bakım Bildirimleri"), default=True)
    
    # Zaman tercihleri
    quiet_hours_start = models.TimeField(_("Sessiz Saatler Başlangıç"), null=True, blank=True)
    quiet_hours_end = models.TimeField(_("Sessiz Saatler Bitiş"), null=True, blank=True)
    timezone = models.CharField(_("Zaman Dilimi"), max_length=50, default='Europe/Istanbul')
    
    # Sıklık sınırları
    max_daily_notifications = models.IntegerField(_("Günlük Maksimum Bildirim"), default=20)
    max_weekly_notifications = models.IntegerField(_("Haftalık Maksimum Bildirim"), default=100)
    
    created_at = models.DateTimeField(_("Oluşturulma Tarihi"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Güncellenme Tarihi"), auto_now=True)
    
    class Meta:
        verbose_name = _("Bildirim Aboneliği")
        verbose_name_plural = _("Bildirim Abonelikleri")
        unique_together = ['company', 'user']
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name}"
