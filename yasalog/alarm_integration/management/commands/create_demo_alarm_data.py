from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
from log_kayit.models import Company
from alarm_integration.models import AlarmRule, AlarmEvent, AlarmNotification, AlarmSuppression, AlarmStatistics


class Command(BaseCommand):
    help = 'Alarm Integration için demo veri oluşturur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Mevcut demo verileri temizle',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_demo_data()
            return

        self.stdout.write('Alarm Integration demo veriler oluşturuluyor...')
        
        # Demo Kafe şirketini bul
        try:
            company = Company.objects.get(slug='demo-kafe')
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR('Demo Kafe şirketi bulunamadı!'))
            return

        # Demo kurallar oluştur
        rules = self.create_rules(company)
        
        # Demo olaylar oluştur
        events = self.create_events(company, rules)
        
        # Demo bildirimler oluştur
        notifications = self.create_notifications(events)
        
        # Demo bastırma kuralları oluştur
        suppressions = self.create_suppressions(company)
        
        # Demo istatistikler oluştur
        statistics = self.create_statistics(company)
        
        self.stdout.write(self.style.SUCCESS('Alarm Integration demo veriler başarıyla oluşturuldu!'))

    def clear_demo_data(self):
        """Demo verileri temizle"""
        AlarmRule.objects.filter(company__slug='demo-kafe').delete()
        AlarmEvent.objects.filter(company__slug='demo-kafe').delete()
        AlarmNotification.objects.filter(event__company__slug='demo-kafe').delete()
        AlarmSuppression.objects.filter(company__slug='demo-kafe').delete()
        AlarmStatistics.objects.filter(company__slug='demo-kafe').delete()
        self.stdout.write('Mevcut veriler temizlendi!')

    def create_rules(self, company):
        """Demo kurallar oluştur"""
        rules_data = [
            {
                'name': 'Yüksek Hata Oranı',
                'description': 'Sistem hata oranı %10\'u aştığında alarm tetiklenir',
                'alarm_type': 'HIGH_CPU_USAGE',
                'severity': 'HIGH',
                'condition': 'error_rate > 10',
                'threshold_value': 10.0,
                'time_window_minutes': 5,
                'notify_email': True,
                'notify_sms': False,
                'notify_webhook': False,
                'notify_dashboard': True,
                'email_recipients': 'admin@demo-kafe.com, support@demo-kafe.com',
                'sms_recipients': '',
                'webhook_url': '',
                'repeat_notification': True,
                'repeat_interval_minutes': 60,
                'max_repeat_count': 5,
                'is_active': True,
                'is_enabled': True,
                'created_at': timezone.now() - timedelta(days=30)
            },
            {
                'name': 'Kritik Güvenlik Olayı',
                'description': 'Güvenlik ihlali tespit edildiğinde alarm tetiklenir',
                'alarm_type': 'SECURITY_THREAT',
                'severity': 'CRITICAL',
                'condition': 'security_violation',
                'threshold_value': 1.0,
                'time_window_minutes': 1,
                'notify_email': True,
                'notify_sms': True,
                'notify_webhook': True,
                'notify_dashboard': True,
                'email_recipients': 'security@demo-kafe.com, admin@demo-kafe.com',
                'sms_recipients': '+905551234567',
                'webhook_url': 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',
                'repeat_notification': True,
                'repeat_interval_minutes': 30,
                'max_repeat_count': 10,
                'is_active': True,
                'is_enabled': True,
                'created_at': timezone.now() - timedelta(days=25)
            },
            {
                'name': 'Yüksek CPU Kullanımı',
                'description': 'CPU kullanımı %90\'ı aştığında alarm tetiklenir',
                'alarm_type': 'HIGH_CPU_USAGE',
                'severity': 'MEDIUM',
                'condition': 'cpu_usage > 90',
                'threshold_value': 90.0,
                'time_window_minutes': 10,
                'notify_email': True,
                'notify_sms': False,
                'notify_webhook': False,
                'notify_dashboard': True,
                'email_recipients': 'admin@demo-kafe.com',
                'sms_recipients': '',
                'webhook_url': '',
                'repeat_notification': True,
                'repeat_interval_minutes': 120,
                'max_repeat_count': 3,
                'is_active': True,
                'is_enabled': True,
                'created_at': timezone.now() - timedelta(days=20)
            },
            {
                'name': 'Disk Alanı Dolu',
                'description': 'Disk kullanımı %95\'i aştığında alarm tetiklenir',
                'alarm_type': 'DISK_FULL',
                'severity': 'HIGH',
                'condition': 'disk_usage > 95',
                'threshold_value': 95.0,
                'time_window_minutes': 5,
                'notify_email': True,
                'notify_sms': True,
                'notify_webhook': False,
                'notify_dashboard': True,
                'email_recipients': 'admin@demo-kafe.com, storage@demo-kafe.com',
                'sms_recipients': '+905551234567',
                'webhook_url': '',
                'repeat_notification': True,
                'repeat_interval_minutes': 60,
                'max_repeat_count': 5,
                'is_active': True,
                'is_enabled': True,
                'created_at': timezone.now() - timedelta(days=15)
            },
            {
                'name': 'Anormal Trafik Artışı',
                'description': 'Ağ trafiği normal seviyenin 3 katını aştığında alarm tetiklenir',
                'alarm_type': 'NETWORK_ERROR',
                'severity': 'MEDIUM',
                'condition': 'traffic_spike',
                'threshold_value': 300.0,
                'time_window_minutes': 15,
                'notify_email': True,
                'notify_sms': False,
                'notify_webhook': False,
                'notify_dashboard': True,
                'email_recipients': 'network@demo-kafe.com',
                'sms_recipients': '',
                'webhook_url': '',
                'repeat_notification': False,
                'repeat_interval_minutes': 60,
                'max_repeat_count': 1,
                'is_active': False,
                'is_enabled': True,
                'created_at': timezone.now() - timedelta(days=10)
            }
        ]

        rules = []
        for data in rules_data:
            rule = AlarmRule.objects.create(
                company=company,
                name=data['name'],
                description=data['description'],
                alarm_type=data['alarm_type'],
                severity=data['severity'],
                condition=data['condition'],
                threshold_value=data['threshold_value'],
                time_window_minutes=data['time_window_minutes'],
                notify_email=data['notify_email'],
                notify_sms=data['notify_sms'],
                notify_webhook=data['notify_webhook'],
                notify_dashboard=data['notify_dashboard'],
                email_recipients=data['email_recipients'],
                sms_recipients=data['sms_recipients'],
                webhook_url=data['webhook_url'],
                repeat_notification=data['repeat_notification'],
                repeat_interval_minutes=data['repeat_interval_minutes'],
                max_repeat_count=data['max_repeat_count'],
                is_active=data['is_active'],
                is_enabled=data['is_enabled'],
                created_at=data['created_at']
            )
            rules.append(rule)
            self.stdout.write(f'  ✅ {rule.name} oluşturuldu')

        return rules

    def create_events(self, company, rules):
        """Demo olaylar oluştur"""
        events_data = [
            {
                'rule': rules[0],
                'title': 'Yüksek Hata Oranı Tespit Edildi',
                'message': 'Sistem hata oranı %12.5\'e yükseldi',
                'severity': 'HIGH',
                'status': 'ACTIVE',
                'details': {'error_rate': 12.5, 'threshold': 10.0},
                'triggered_at': timezone.now() - timedelta(hours=2),
                'created_at': timezone.now() - timedelta(hours=3)
            },
            {
                'rule': rules[1],
                'title': 'Kritik Güvenlik İhlali',
                'message': 'Yetkisiz erişim denemesi tespit edildi',
                'severity': 'CRITICAL',
                'status': 'ACKNOWLEDGED',
                'details': {'ip_address': '192.168.1.100', 'attempts': 5},
                'triggered_at': timezone.now() - timedelta(hours=6),
                'acknowledged_at': timezone.now() - timedelta(hours=5),
                'created_at': timezone.now() - timedelta(hours=7)
            },
            {
                'rule': rules[2],
                'title': 'CPU Kullanımı Yüksek',
                'message': 'CPU kullanımı %92\'ye yükseldi',
                'severity': 'MEDIUM',
                'status': 'RESOLVED',
                'details': {'cpu_usage': 92.0, 'threshold': 90.0},
                'triggered_at': timezone.now() - timedelta(days=1),
                'resolved_at': timezone.now() - timedelta(hours=20),
                'created_at': timezone.now() - timedelta(days=1, hours=1)
            },
            {
                'rule': rules[3],
                'title': 'Disk Alanı Kritik Seviyede',
                'message': 'Disk kullanımı %96\'ya yükseldi',
                'severity': 'HIGH',
                'status': 'ACTIVE',
                'details': {'disk_usage': 96.0, 'threshold': 95.0, 'free_space': '2.1 GB'},
                'triggered_at': timezone.now() - timedelta(minutes=30),
                'created_at': timezone.now() - timedelta(hours=1)
            },
            {
                'rule': rules[0],
                'title': 'Hata Oranı Tekrar Yükseldi',
                'message': 'Sistem hata oranı %15\'e yükseldi',
                'severity': 'HIGH',
                'status': 'SUPPRESSED',
                'details': {'error_rate': 15.0, 'threshold': 10.0, 'suppression_reason': 'Bakım saati'},
                'triggered_at': timezone.now() - timedelta(days=2),
                'created_at': timezone.now() - timedelta(days=2, hours=1)
            }
        ]

        events = []
        for data in events_data:
            event = AlarmEvent.objects.create(
                company=company,
                rule=data['rule'],
                title=data['title'],
                message=data['message'],
                severity=data['severity'],
                status=data['status'],
                details=data.get('details', {}),
                triggered_at=data['triggered_at'],
                acknowledged_at=data.get('acknowledged_at'),
                resolved_at=data.get('resolved_at')
            )
            events.append(event)
            self.stdout.write(f'  ✅ {event.title} oluşturuldu')

        return events

    def create_notifications(self, events):
        """Demo bildirimler oluştur"""
        notifications_data = [
            {
                'event': events[0],
                'notification_type': 'EMAIL',
                'recipient': 'admin@demo-kafe.com',
                'subject': 'Yüksek Hata Oranı Alarmı',
                'message': 'Sistem hata oranı %12.5\'e yükseldi. Lütfen kontrol edin.',
                'status': 'SENT',
                'sent_at': timezone.now() - timedelta(hours=2),
                'created_at': timezone.now() - timedelta(hours=3)
            },
            {
                'event': events[1],
                'notification_type': 'SMS',
                'recipient': '+905551234567',
                'subject': 'Kritik Güvenlik Alarmı',
                'message': 'Kritik güvenlik ihlali tespit edildi!',
                'status': 'SENT',
                'sent_at': timezone.now() - timedelta(hours=6),
                'created_at': timezone.now() - timedelta(hours=7)
            },
            {
                'event': events[2],
                'notification_type': 'EMAIL',
                'recipient': 'admin@demo-kafe.com',
                'subject': 'CPU Kullanımı Yüksek',
                'message': 'CPU kullanımı %92\'ye yükseldi.',
                'status': 'DELIVERED',
                'sent_at': timezone.now() - timedelta(days=1),
                'delivered_at': timezone.now() - timedelta(days=1, minutes=5),
                'created_at': timezone.now() - timedelta(days=1, hours=1)
            },
            {
                'event': events[3],
                'notification_type': 'EMAIL',
                'recipient': 'storage@demo-kafe.com',
                'subject': 'Disk Alanı Kritik',
                'message': 'Disk kullanımı %96\'ya yükseldi.',
                'status': 'FAILED',
                'error_message': 'SMTP server connection failed',
                'created_at': timezone.now() - timedelta(hours=1)
            }
        ]

        notifications = []
        for data in notifications_data:
            notification = AlarmNotification.objects.create(
                event=data['event'],
                notification_type=data['notification_type'],
                recipient=data['recipient'],
                subject=data.get('subject', ''),
                message=data['message'],
                status=data['status'],
                sent_at=data.get('sent_at'),
                delivered_at=data.get('delivered_at'),
                error_message=data.get('error_message', '')
            )
            notifications.append(notification)
            self.stdout.write(f'  ✅ {notification.notification_type} bildirimi oluşturuldu')

        return notifications

    def create_suppressions(self, company):
        """Demo bastırma kuralları oluştur"""
        suppressions_data = [
            {
                'name': 'Bakım Saatleri',
                'description': 'Hafta sonu bakım saatlerinde alarmlar bastırılır',
                'alarm_types': ['HIGH_CPU_USAGE', 'DISK_FULL'],
                'severity_levels': ['MEDIUM', 'HIGH'],
                'source_devices': [],
                'start_time': timezone.now() - timedelta(days=1),
                'end_time': timezone.now() + timedelta(days=1),
                'is_active': True,
                'created_at': timezone.now() - timedelta(days=20)
            },
            {
                'name': 'Test Ortamı',
                'description': 'Test ortamındaki alarmlar bastırılır',
                'alarm_types': [],
                'severity_levels': ['LOW', 'MEDIUM'],
                'source_devices': ['test-server-01', 'test-server-02'],
                'start_time': timezone.now() - timedelta(days=7),
                'end_time': timezone.now() + timedelta(days=7),
                'is_active': True,
                'created_at': timezone.now() - timedelta(days=15)
            }
        ]

        suppressions = []
        for data in suppressions_data:
            suppression = AlarmSuppression.objects.create(
                company=company,
                name=data['name'],
                description=data['description'],
                alarm_types=data['alarm_types'],
                severity_levels=data['severity_levels'],
                source_devices=data['source_devices'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                is_active=data['is_active']
            )
            suppressions.append(suppression)
            self.stdout.write(f'  ✅ {suppression.name} oluşturuldu')

        return suppressions

    def create_statistics(self, company):
        """Demo istatistikler oluştur"""
        statistics_data = [
            {
                'date': timezone.now().date(),
                'total_alarms': 12,
                'critical_alarms': 1,
                'high_alarms': 3,
                'medium_alarms': 6,
                'low_alarms': 2,
                'active_alarms': 2,
                'acknowledged_alarms': 1,
                'resolved_alarms': 8,
                'total_notifications': 15,
                'successful_notifications': 12,
                'failed_notifications': 3,
                'average_response_time_minutes': 15.5,
                'average_resolution_time_minutes': 120.0,
                'created_at': timezone.now()
            },
            {
                'date': (timezone.now() - timedelta(days=7)).date(),
                'total_alarms': 45,
                'critical_alarms': 3,
                'high_alarms': 12,
                'medium_alarms': 20,
                'low_alarms': 10,
                'active_alarms': 5,
                'acknowledged_alarms': 8,
                'resolved_alarms': 35,
                'total_notifications': 60,
                'successful_notifications': 55,
                'failed_notifications': 5,
                'average_response_time_minutes': 12.3,
                'average_resolution_time_minutes': 95.5,
                'created_at': timezone.now() - timedelta(days=7)
            }
        ]

        statistics = []
        for data in statistics_data:
            statistic = AlarmStatistics.objects.create(
                company=company,
                date=data['date'],
                total_alarms=data['total_alarms'],
                critical_alarms=data['critical_alarms'],
                high_alarms=data['high_alarms'],
                medium_alarms=data['medium_alarms'],
                low_alarms=data['low_alarms'],
                active_alarms=data['active_alarms'],
                acknowledged_alarms=data['acknowledged_alarms'],
                resolved_alarms=data['resolved_alarms'],
                total_notifications=data['total_notifications'],
                successful_notifications=data['successful_notifications'],
                failed_notifications=data['failed_notifications'],
                average_response_time_minutes=data['average_response_time_minutes'],
                average_resolution_time_minutes=data['average_resolution_time_minutes']
            )
            statistics.append(statistic)
            self.stdout.write(f'  ✅ {statistic.date} istatistiği oluşturuldu')

        return statistics
