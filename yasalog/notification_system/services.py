"""
Gelişmiş Bildirim Servisleri
5651 Loglama için kapsamlı bildirim sistemi servisleri
"""

import json
import requests
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Q

from .models import (
    NotificationChannel, NotificationTemplate, NotificationRule, 
    NotificationLog, NotificationSubscription
)
from log_kayit.models import LogKayit, Company
from syslog_server.models import SyslogMessage
from mirror_port.models import MirrorTraffic
from timestamp_signing.models import TimestampSignature


class NotificationService:
    """Ana bildirim servisi"""
    
    def __init__(self, company):
        self.company = company
        
    def send_notification(self, rule, data, recipients=None):
        """Bildirim gönder"""
        if not rule.is_active:
            return False
        
        # Alıcıları belirle
        if not recipients:
            recipients = self._get_recipients(rule)
        
        if not recipients:
            return False
        
        # Şablonu hazırla
        message_data = self._prepare_message(rule.template, data)
        
        # Kanallara göre gönder
        success_count = 0
        for channel in rule.channels.filter(is_active=True):
            for recipient in recipients:
                try:
                    log = NotificationLog.objects.create(
                        rule=rule,
                        channel=channel,
                        template=rule.template,
                        recipient=recipient,
                        subject=message_data.get('subject', ''),
                        message=message_data.get('message', ''),
                        status='pending'
                    )
                    
                    if self._send_via_channel(channel, recipient, message_data, log):
                        success_count += 1
                        log.status = 'sent'
                        log.sent_at = timezone.now()
                    else:
                        log.status = 'failed'
                        log.error_message = 'Gönderim başarısız'
                    
                    log.save()
                    
                except Exception as e:
                    if 'log' in locals():
                        log.status = 'failed'
                        log.error_message = str(e)
                        log.save()
        
        return success_count > 0
    
    def _get_recipients(self, rule):
        """Alıcıları belirle"""
        recipients = []
        
        # Kuralda belirtilen alıcılar
        if rule.recipients:
            recipients.extend([r.strip() for r in rule.recipients.split(',')])
        
        # Aboneliklerden alıcılar
        subscriptions = NotificationSubscription.objects.filter(
            company=self.company,
            **{f"{rule.template.template_type.replace('_', '_')}": True}
        )
        
        for subscription in subscriptions:
            if subscription.user.email:
                recipients.append(subscription.user.email)
        
        return list(set(recipients))  # Tekrarları kaldır
    
    def _prepare_message(self, template, data):
        """Mesajı hazırla"""
        message_data = {
            'subject': template.email_subject,
            'message': template.email_body_text,
            'html_message': template.email_body_html,
            'sms_message': template.sms_message,
            'push_title': template.push_title,
            'push_body': template.push_body,
        }
        
        # Değişkenleri değiştir
        for key, value in message_data.items():
            if value:
                message_data[key] = self._replace_variables(value, data)
        
        return message_data
    
    def _replace_variables(self, text, data):
        """Değişkenleri değiştir"""
        if not text:
            return text
        
        # Temel değişkenler
        variables = {
            '{{company_name}}': self.company.name,
            '{{current_time}}': timezone.now().strftime('%d.%m.%Y %H:%M'),
            '{{current_date}}': timezone.now().strftime('%d.%m.%Y'),
        }
        
        # Veri değişkenleri
        if 'user_log' in data:
            log = data['user_log']
            variables.update({
                '{{user_name}}': log.ad_soyad or 'Bilinmeyen',
                '{{user_tc}}': log.tc_no or 'Bilinmeyen',
                '{{ip_address}}': log.ip_adresi or 'Bilinmeyen',
                '{{login_time}}': log.giris_zamani.strftime('%d.%m.%Y %H:%M'),
            })
        
        if 'syslog_message' in data:
            msg = data['syslog_message']
            variables.update({
                '{{syslog_facility}}': str(msg.facility),
                '{{syslog_priority}}': str(msg.priority),
                '{{syslog_hostname}}': msg.hostname or 'Bilinmeyen',
                '{{syslog_message}}': msg.message[:100] + '...' if len(msg.message) > 100 else msg.message,
            })
        
        # Değişkenleri değiştir
        for variable, value in variables.items():
            text = text.replace(variable, str(value))
        
        return text
    
    def _send_via_channel(self, channel, recipient, message_data, log):
        """Kanal üzerinden gönder"""
        try:
            if channel.channel_type == 'email':
                return self._send_email(channel, recipient, message_data, log)
            elif channel.channel_type == 'sms':
                return self._send_sms(channel, recipient, message_data, log)
            elif channel.channel_type == 'webhook':
                return self._send_webhook(channel, recipient, message_data, log)
            elif channel.channel_type == 'slack':
                return self._send_slack(channel, recipient, message_data, log)
            elif channel.channel_type == 'teams':
                return self._send_teams(channel, recipient, message_data, log)
            elif channel.channel_type == 'telegram':
                return self._send_telegram(channel, recipient, message_data, log)
            elif channel.channel_type == 'discord':
                return self._send_discord(channel, recipient, message_data, log)
            else:
                return False
        except Exception as e:
            log.error_message = str(e)
            return False
    
    def _send_email(self, channel, recipient, message_data, log):
        """E-posta gönder"""
        try:
            if channel.smtp_host and channel.smtp_port:
                # Özel SMTP sunucusu
                msg = MIMEMultipart('alternative')
                msg['Subject'] = message_data.get('subject', 'Bildirim')
                msg['From'] = channel.from_email or settings.DEFAULT_FROM_EMAIL
                msg['To'] = recipient
                
                # Metin ve HTML içerik
                if message_data.get('message'):
                    text_part = MIMEText(message_data['message'], 'plain', 'utf-8')
                    msg.attach(text_part)
                
                if message_data.get('html_message'):
                    html_part = MIMEText(message_data['html_message'], 'html', 'utf-8')
                    msg.attach(html_part)
                
                # SMTP bağlantısı
                context = ssl.create_default_context()
                with smtplib.SMTP(channel.smtp_host, channel.smtp_port) as server:
                    if channel.smtp_use_tls:
                        server.starttls(context=context)
                    if channel.smtp_username and channel.smtp_password:
                        server.login(channel.smtp_username, channel.smtp_password)
                    server.send_message(msg)
            else:
                # Django e-posta sistemi
                send_mail(
                    subject=message_data.get('subject', 'Bildirim'),
                    message=message_data.get('message', ''),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    html_message=message_data.get('html_message', ''),
                    fail_silently=False
                )
            
            return True
        except Exception as e:
            log.error_message = f"E-posta gönderim hatası: {str(e)}"
            return False
    
    def _send_sms(self, channel, recipient, message_data, log):
        """SMS gönder"""
        try:
            message = message_data.get('sms_message', '')
            if not message:
                return False
            
            # SMS sağlayıcı API'si (örnek)
            if channel.sms_provider == 'netgsm':
                return self._send_sms_netgsm(channel, recipient, message, log)
            elif channel.sms_provider == 'iletimerkezi':
                return self._send_sms_iletimerkezi(channel, recipient, message, log)
            else:
                # Varsayılan SMS servisi
                return self._send_sms_default(channel, recipient, message, log)
        except Exception as e:
            log.error_message = f"SMS gönderim hatası: {str(e)}"
            return False
    
    def _send_sms_netgsm(self, channel, recipient, message, log):
        """NetGSM SMS gönder"""
        try:
            url = "https://api.netgsm.com.tr/sms/send/get"
            params = {
                'usercode': channel.sms_api_key,
                'password': channel.sms_api_secret,
                'gsmno': recipient.replace('+', '').replace(' ', ''),
                'message': message,
                'msgheader': channel.sms_sender_id or 'NETGSM'
            }
            
            response = requests.get(url, params=params, timeout=30)
            return response.status_code == 200
        except Exception as e:
            log.error_message = f"NetGSM SMS hatası: {str(e)}"
            return False
    
    def _send_sms_iletimerkezi(self, channel, recipient, message, log):
        """İleti Merkezi SMS gönder"""
        try:
            url = "https://api.iletimerkezi.com/v1/send-sms"
            headers = {
                'Authorization': f'Bearer {channel.sms_api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'recipients': [recipient.replace('+', '').replace(' ', '')],
                'message': message,
                'sender': channel.sms_sender_id or 'ILETI'
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            return response.status_code == 200
        except Exception as e:
            log.error_message = f"İleti Merkezi SMS hatası: {str(e)}"
            return False
    
    def _send_sms_default(self, channel, recipient, message, log):
        """Varsayılan SMS gönder"""
        # Bu kısım gerçek SMS sağlayıcısına göre implement edilecek
        log.error_message = "SMS sağlayıcısı yapılandırılmamış"
        return False
    
    def _send_webhook(self, channel, recipient, message_data, log):
        """Webhook gönder"""
        try:
            if not channel.webhook_url:
                return False
            
            payload = {
                'recipient': recipient,
                'subject': message_data.get('subject', ''),
                'message': message_data.get('message', ''),
                'timestamp': timezone.now().isoformat(),
                'company': self.company.name
            }
            
            # Özel payload varsa kullan
            if channel.template.webhook_payload:
                payload.update(channel.template.webhook_payload)
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': '5651Log-Notification/1.0'
            }
            
            # Webhook gizli anahtarı varsa ekle
            if channel.webhook_secret:
                headers['X-Webhook-Secret'] = channel.webhook_secret
            
            # Özel başlıklar varsa ekle
            if channel.webhook_headers:
                headers.update(channel.webhook_headers)
            
            response = requests.post(
                channel.webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            return response.status_code in [200, 201, 202]
        except Exception as e:
            log.error_message = f"Webhook gönderim hatası: {str(e)}"
            return False
    
    def _send_slack(self, channel, recipient, message_data, log):
        """Slack gönder"""
        try:
            if not channel.slack_webhook_url:
                return False
            
            message = message_data.get('message', '')
            color = channel.template.slack_color or 'good'
            
            payload = {
                'channel': channel.slack_channel or '#general',
                'username': channel.slack_username or '5651Log Bot',
                'attachments': [{
                    'color': color,
                    'title': message_data.get('subject', 'Bildirim'),
                    'text': message,
                    'footer': self.company.name,
                    'ts': int(timezone.now().timestamp())
                }]
            }
            
            response = requests.post(
                channel.slack_webhook_url,
                json=payload,
                timeout=30
            )
            
            return response.status_code == 200
        except Exception as e:
            log.error_message = f"Slack gönderim hatası: {str(e)}"
            return False
    
    def _send_teams(self, channel, recipient, message_data, log):
        """Microsoft Teams gönder"""
        try:
            if not channel.teams_webhook_url:
                return False
            
            payload = {
                '@type': 'MessageCard',
                '@context': 'http://schema.org/extensions',
                'themeColor': '0076D7',
                'summary': message_data.get('subject', 'Bildirim'),
                'sections': [{
                    'activityTitle': message_data.get('subject', 'Bildirim'),
                    'activitySubtitle': self.company.name,
                    'activityImage': 'https://teamsnodesample.azurewebsites.net/static/img/image5.png',
                    'text': message_data.get('message', ''),
                    'facts': [{
                        'name': 'Zaman',
                        'value': timezone.now().strftime('%d.%m.%Y %H:%M')
                    }]
                }]
            }
            
            response = requests.post(
                channel.teams_webhook_url,
                json=payload,
                timeout=30
            )
            
            return response.status_code == 200
        except Exception as e:
            log.error_message = f"Teams gönderim hatası: {str(e)}"
            return False
    
    def _send_telegram(self, channel, recipient, message_data, log):
        """Telegram gönder"""
        try:
            if not channel.telegram_bot_token or not channel.telegram_chat_id:
                return False
            
            message = message_data.get('message', '')
            parse_mode = channel.template.telegram_parse_mode or 'HTML'
            
            url = f"https://api.telegram.org/bot{channel.telegram_bot_token}/sendMessage"
            data = {
                'chat_id': channel.telegram_chat_id,
                'text': f"*{message_data.get('subject', 'Bildirim')}*\n\n{message}",
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=data, timeout=30)
            result = response.json()
            
            return result.get('ok', False)
        except Exception as e:
            log.error_message = f"Telegram gönderim hatası: {str(e)}"
            return False
    
    def _send_discord(self, channel, recipient, message_data, log):
        """Discord gönder"""
        try:
            if not channel.discord_webhook_url:
                return False
            
            embed = {
                'title': message_data.get('subject', 'Bildirim'),
                'description': message_data.get('message', ''),
                'color': 0x00ff00,  # Yeşil
                'timestamp': timezone.now().isoformat(),
                'footer': {
                    'text': self.company.name
                }
            }
            
            payload = {
                'embeds': [embed]
            }
            
            response = requests.post(
                channel.discord_webhook_url,
                json=payload,
                timeout=30
            )
            
            return response.status_code in [200, 204]
        except Exception as e:
            log.error_message = f"Discord gönderim hatası: {str(e)}"
            return False


class NotificationRuleEngine:
    """Bildirim kural motoru"""
    
    def __init__(self, company):
        self.company = company
        self.service = NotificationService(company)
    
    def check_rules(self):
        """Kuralları kontrol et"""
        rules = NotificationRule.objects.filter(
            company=self.company,
            is_active=True
        )
        
        for rule in rules:
            try:
                if self._should_trigger(rule):
                    self._trigger_rule(rule)
            except Exception as e:
                print(f"Kural kontrol hatası ({rule.name}): {e}")
    
    def _should_trigger(self, rule):
        """Kural tetiklenmeli mi?"""
        now = timezone.now()
        
        # Cooldown kontrolü
        if rule.last_triggered:
            cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_period)
            if now < cooldown_end:
                return False
        
        # Günlük/saatlik sınır kontrolü
        if self._is_rate_limited(rule):
            return False
        
        # Tetikleme tipine göre kontrol
        if rule.trigger_type == 'immediate':
            return True
        elif rule.trigger_type == 'threshold':
            return self._check_threshold(rule)
        elif rule.trigger_type == 'schedule':
            return self._check_schedule(rule)
        elif rule.trigger_type == 'event':
            return self._check_event(rule)
        elif rule.trigger_type == 'condition':
            return self._check_condition(rule)
        
        return False
    
    def _is_rate_limited(self, rule):
        """Hız sınırı kontrolü"""
        now = timezone.now()
        
        # Saatlik sınır
        hour_ago = now - timedelta(hours=1)
        hourly_count = NotificationLog.objects.filter(
            rule=rule,
            created_at__gte=hour_ago,
            status__in=['sent', 'delivered']
        ).count()
        
        if hourly_count >= rule.max_notifications_per_hour:
            return True
        
        # Günlük sınır
        day_ago = now - timedelta(days=1)
        daily_count = NotificationLog.objects.filter(
            rule=rule,
            created_at__gte=day_ago,
            status__in=['sent', 'delivered']
        ).count()
        
        if daily_count >= rule.max_notifications_per_day:
            return True
        
        return False
    
    def _check_threshold(self, rule):
        """Eşik kontrolü"""
        # Zaman penceresi
        window_start = timezone.now() - timedelta(minutes=rule.time_window)
        
        # Şablon tipine göre kontrol
        if rule.template.template_type == 'security_alert':
            suspicious_count = LogKayit.objects.filter(
                company=self.company,
                is_suspicious=True,
                giris_zamani__gte=window_start
            ).count()
            return suspicious_count >= rule.threshold_value
        
        elif rule.template.template_type == 'system_alert':
            syslog_count = SyslogMessage.objects.filter(
                company=self.company,
                priority__lte=3,  # Error ve üzeri
                timestamp__gte=window_start
            ).count()
            return syslog_count >= rule.threshold_value
        
        return False
    
    def _check_schedule(self, rule):
        """Zamanlama kontrolü"""
        # Cron ifadesi kontrolü (basit implementasyon)
        now = timezone.now()
        
        if rule.schedule_cron:
            # Basit cron kontrolü
            parts = rule.schedule_cron.split()
            if len(parts) >= 5:
                minute, hour, day, month, weekday = parts[:5]
                
                # Dakika kontrolü
                if minute != '*' and int(minute) != now.minute:
                    return False
                
                # Saat kontrolü
                if hour != '*' and int(hour) != now.hour:
                    return False
        
        return True
    
    def _check_event(self, rule):
        """Olay kontrolü"""
        # Belirli olaylar için kontrol
        return False
    
    def _check_condition(self, rule):
        """Koşul kontrolü"""
        # Özel koşul kontrolü
        if rule.trigger_condition:
            try:
                # Güvenli koşul değerlendirmesi
                return eval(rule.trigger_condition)
            except:
                return False
        return False
    
    def _trigger_rule(self, rule):
        """Kuralı tetikle"""
        # Veri topla
        data = self._collect_rule_data(rule)
        
        # Bildirim gönder
        success = self.service.send_notification(rule, data)
        
        # Kuralı güncelle
        rule.last_triggered = timezone.now()
        rule.trigger_count += 1
        rule.save()
        
        return success
    
    def _collect_rule_data(self, rule):
        """Kural verilerini topla"""
        data = {}
        
        # Şablon tipine göre veri topla
        if rule.template.template_type == 'security_alert':
            data['suspicious_logs'] = LogKayit.objects.filter(
                company=self.company,
                is_suspicious=True,
                giris_zamani__gte=timezone.now() - timedelta(minutes=rule.time_window)
            )[:10]
        
        elif rule.template.template_type == 'system_alert':
            data['syslog_messages'] = SyslogMessage.objects.filter(
                company=self.company,
                priority__lte=3,
                timestamp__gte=timezone.now() - timedelta(minutes=rule.time_window)
            )[:10]
        
        return data


class NotificationManager:
    """Bildirim yöneticisi"""
    
    def __init__(self, company):
        self.company = company
        self.service = NotificationService(company)
        self.engine = NotificationRuleEngine(company)
    
    def send_immediate_notification(self, template_type, data, channels=None, recipients=None):
        """Anında bildirim gönder"""
        try:
            # Şablonu bul
            template = NotificationTemplate.objects.filter(
                company=self.company,
                template_type=template_type,
                is_active=True
            ).first()
            
            if not template:
                return False
            
            # Geçici kural oluştur
            rule = NotificationRule(
                company=self.company,
                name=f"Anında Bildirim - {template_type}",
                template=template,
                trigger_type='immediate',
                is_active=True
            )
            
            # Kanalları belirle
            if channels:
                rule.channels.set(channels)
            else:
                rule.channels.set(NotificationChannel.objects.filter(
                    company=self.company,
                    is_active=True
                ))
            
            # Bildirim gönder
            return self.service.send_notification(rule, data, recipients)
            
        except Exception as e:
            print(f"Anında bildirim hatası: {e}")
            return False
    
    def check_and_send_notifications(self):
        """Bildirimleri kontrol et ve gönder"""
        self.engine.check_rules()
    
    def get_notification_stats(self):
        """Bildirim istatistikleri"""
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        
        stats = {
            'today': {
                'sent': NotificationLog.objects.filter(
                    company=self.company,
                    created_at__date=today,
                    status='sent'
                ).count(),
                'failed': NotificationLog.objects.filter(
                    company=self.company,
                    created_at__date=today,
                    status='failed'
                ).count(),
            },
            'week': {
                'sent': NotificationLog.objects.filter(
                    company=self.company,
                    created_at__gte=week_ago,
                    status='sent'
                ).count(),
                'failed': NotificationLog.objects.filter(
                    company=self.company,
                    created_at__gte=week_ago,
                    status='failed'
                ).count(),
            },
            'channels': {},
            'rules': NotificationRule.objects.filter(company=self.company).count(),
            'active_rules': NotificationRule.objects.filter(
                company=self.company,
                is_active=True
            ).count(),
        }
        
        # Kanal istatistikleri
        for channel in NotificationChannel.objects.filter(company=self.company):
            stats['channels'][channel.name] = {
                'sent': NotificationLog.objects.filter(
                    channel=channel,
                    created_at__gte=week_ago,
                    status='sent'
                ).count(),
                'failed': NotificationLog.objects.filter(
                    channel=channel,
                    created_at__gte=week_ago,
                    status='failed'
                ).count(),
            }
        
        return stats
