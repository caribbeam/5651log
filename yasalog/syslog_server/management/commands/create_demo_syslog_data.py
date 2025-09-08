from django.core.management.base import BaseCommand
from django.utils import timezone
from log_kayit.models import Company
from syslog_server.models import SyslogServer, SyslogClient, SyslogMessage, SyslogFilter, SyslogAlert
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Create demo syslog data'

    def handle(self, *args, **options):
        # Company'yi al (varsayılan olarak ilk company'yi kullan)
        try:
            company = Company.objects.first()
            if not company:
                self.stdout.write(
                    self.style.ERROR('No company found. Please create a company first.')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting company: {e}')
            )
            return

        # Demo Syslog Server oluştur
        server, created = SyslogServer.objects.get_or_create(
            company=company,
            name='Ana Syslog Sunucusu',
            defaults={
                'host': '0.0.0.0',
                'port': 514,
                'protocol': 'UDP',
                'use_tls': False,
                'allowed_facilities': 'local0,local1,local2,local3,local4,local5,local6,local7',
                'allowed_priorities': 'emerg,alert,crit,err,warning,notice,info,debug',
                'max_connections': 100,
                'buffer_size': 1024,
                'batch_size': 100,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created syslog server: {server.name}')
            )

        # Demo Syslog Client'lar oluştur
        clients_data = [
            {
                'name': 'Cisco Router 1',
                'client_type': 'router',
                'ip_address': '192.168.1.1',
                'mac_address': '00:11:22:33:44:55',
                'hostname': 'router1.company.local',
                'facility': 16,  # local0
                'priority': 6,   # info
                'is_active': True
            },
            {
                'name': 'MikroTik Switch',
                'client_type': 'switch',
                'ip_address': '192.168.1.2',
                'mac_address': '00:11:22:33:44:56',
                'hostname': 'switch1.company.local',
                'facility': 17,  # local1
                'priority': 4,   # warning
                'is_active': True
            },
            {
                'name': 'Windows Server',
                'client_type': 'server',
                'ip_address': '192.168.1.10',
                'mac_address': '00:11:22:33:44:57',
                'hostname': 'server1.company.local',
                'facility': 18,  # local2
                'priority': 3,   # error
                'is_active': True
            }
        ]

        for client_data in clients_data:
            client, created = SyslogClient.objects.get_or_create(
                company=company,
                name=client_data['name'],
                defaults={
                    'client_type': client_data['client_type'],
                    'ip_address': client_data['ip_address'],
                    'mac_address': client_data['mac_address'],
                    'hostname': client_data['hostname'],
                    'syslog_server': server,
                    'facility': client_data['facility'],
                    'priority': client_data['priority'],
                    'is_active': client_data['is_active']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created syslog client: {client.name}')
                )

        # Demo Syslog Messages oluştur
        facilities = [16, 17, 18, 19, 20, 21, 22, 23]  # local0-local7
        priorities = [0, 1, 2, 3, 4, 5, 6, 7]  # emerg-debug
        programs = ['kernel', 'sshd', 'apache2', 'mysql', 'nginx', 'systemd', 'cron', 'dhcpd']
        hostnames = ['router1.company.local', 'switch1.company.local', 'server1.company.local']
        
        messages_data = [
            'User authentication successful',
            'Connection established from 192.168.1.100',
            'System reboot completed',
            'Disk space warning: /var/log is 85% full',
            'Failed login attempt from 10.0.0.1',
            'Service started successfully',
            'Network interface eth0 is up',
            'Database backup completed',
            'SSL certificate expires in 30 days',
            'High CPU usage detected: 95%',
            'Memory usage critical: 98%',
            'Firewall rule added',
            'VPN connection established',
            'Email sent successfully',
            'File transfer completed'
        ]

        # Son 7 gün için mesajlar oluştur
        for i in range(50):
            timestamp = timezone.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            
            message, created = SyslogMessage.objects.get_or_create(
                company=company,
                server=server,
                timestamp=timestamp,
                facility=random.choice(facilities),
                priority=random.choice(priorities),
                hostname=random.choice(hostnames),
                program=random.choice(programs),
                message=random.choice(messages_data),
                is_suspicious=random.choice([True, False, False, False])  # %25 şüpheli
            )
            
            if created and i % 10 == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Created syslog message {i+1}/50')
                )

        # Demo Syslog Filters oluştur
        filters_data = [
            {
                'name': 'Kritik Hatalar',
                'filter_type': 'priority',
                'filter_value': 'crit|emerg|alert',
                'description': 'Kritik seviye hataları yakalar',
                'action': 'ALERT',
                'priority': 1,
                'is_active': True
            },
            {
                'name': 'Başarısız Girişler',
                'filter_type': 'message',
                'filter_value': 'failed|denied|rejected',
                'description': 'Başarısız giriş denemelerini yakalar',
                'action': 'LOG',
                'priority': 2,
                'is_active': True
            },
            {
                'name': 'Sistem Mesajları',
                'filter_type': 'facility',
                'filter_value': 'local0|local1',
                'description': 'Sistem mesajlarını filtreler',
                'action': 'ACCEPT',
                'priority': 3,
                'is_active': True
            }
        ]

        for filter_data in filters_data:
            filter_obj, created = SyslogFilter.objects.get_or_create(
                company=company,
                name=filter_data['name'],
                defaults={
                    'filter_type': filter_data['filter_type'],
                    'filter_value': filter_data['filter_value'],
                    'description': filter_data['description'],
                    'action': filter_data['action'],
                    'priority': filter_data['priority'],
                    'is_active': filter_data['is_active']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created syslog filter: {filter_obj.name}')
                )

        # Demo Syslog Alerts oluştur
        alerts_data = [
            {
                'name': 'Yüksek Hata Oranı',
                'alert_type': 'error_count',
                'condition': 'greater_than',
                'threshold_value': 10,
                'time_window': 300,
                'notify_email': True,
                'notify_sms': False,
                'notification_recipients': 'admin@company.com',
                'is_active': True
            },
            {
                'name': 'Şüpheli Aktivite',
                'alert_type': 'suspicious_activity',
                'condition': 'greater_than',
                'threshold_value': 5,
                'time_window': 600,
                'notify_email': True,
                'notify_sms': True,
                'notification_recipients': 'admin@company.com,security@company.com',
                'is_active': True
            },
            {
                'name': 'Sistem Yükü',
                'alert_type': 'cpu_usage',
                'condition': 'greater_than',
                'threshold_value': 90,
                'time_window': 180,
                'notify_email': True,
                'notify_sms': False,
                'notification_recipients': 'admin@company.com',
                'is_active': True
            }
        ]

        for alert_data in alerts_data:
            alert, created = SyslogAlert.objects.get_or_create(
                company=company,
                name=alert_data['name'],
                defaults={
                    'alert_type': alert_data['alert_type'],
                    'condition': alert_data['condition'],
                    'threshold_value': alert_data['threshold_value'],
                    'time_window': alert_data['time_window'],
                    'notify_email': alert_data['notify_email'],
                    'notify_sms': alert_data['notify_sms'],
                    'notification_recipients': alert_data['notification_recipients'],
                    'is_active': alert_data['is_active']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created syslog alert: {alert.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Demo syslog data created successfully!')
        )
