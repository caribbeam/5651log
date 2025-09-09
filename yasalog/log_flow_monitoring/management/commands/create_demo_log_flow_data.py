"""
Log Flow Monitoring Demo Verileri Oluşturma
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from log_kayit.models import Company
from log_flow_monitoring.models import LogFlowMonitor, LogFlowAlert, LogFlowStatistics
import random


class Command(BaseCommand):
    help = 'Log flow monitoring için demo veriler oluşturur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-slug',
            type=str,
            default='demo-kafe',
            help='Şirket slug (varsayılan: demo-kafe)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Mevcut verileri temizle',
        )

    def handle(self, *args, **options):
        company_slug = options['company_slug']
        
        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Şirket bulunamadı: {company_slug}')
            )
            return

        if options['clear']:
            self.clear_data(company)
            return

        self.stdout.write(
            self.style.SUCCESS(f'Demo veriler oluşturuluyor: {company.name}')
        )

        # Demo monitörler oluştur
        monitors = self.create_monitors(company)
        
        # Demo uyarılar oluştur
        self.create_alerts(company, monitors)
        
        # Demo istatistikler oluştur
        self.create_statistics(company, monitors)

        self.stdout.write(
            self.style.SUCCESS('Demo veriler başarıyla oluşturuldu!')
        )

    def clear_data(self, company):
        """Mevcut verileri temizle"""
        LogFlowStatistics.objects.filter(company=company).delete()
        LogFlowAlert.objects.filter(company=company).delete()
        LogFlowMonitor.objects.filter(company=company).delete()
        
        self.stdout.write(
            self.style.SUCCESS('Mevcut veriler temizlendi!')
        )

    def create_monitors(self, company):
        """Demo monitörler oluştur"""
        monitors_data = [
            {
                'name': 'Ana Firewall',
                'monitor_type': 'FIREWALL',
                'source_device': 'Cisco ASA 5520',
                'source_ip': '192.168.1.1',
                'source_port': 514,
                'status': 'ACTIVE',
                'is_receiving_logs': True,
                'total_logs_received': 15420,
                'logs_per_minute': 25,
                'average_log_size': 180,
            },
            {
                'name': 'Hotspot Sistemi',
                'monitor_type': 'HOTSPOT',
                'source_device': 'MikroTik RouterOS',
                'source_ip': '192.168.1.2',
                'source_port': 514,
                'status': 'ACTIVE',
                'is_receiving_logs': True,
                'total_logs_received': 8930,
                'logs_per_minute': 15,
                'average_log_size': 120,
            },
            {
                'name': 'Syslog Sunucu',
                'monitor_type': 'SYSLOG',
                'source_device': 'Linux Syslog',
                'source_ip': '192.168.1.10',
                'source_port': 514,
                'status': 'WARNING',
                'is_receiving_logs': False,
                'total_logs_received': 25680,
                'logs_per_minute': 0,
                'average_log_size': 200,
            },
            {
                'name': 'Timestamp Servisi',
                'monitor_type': 'TIMESTAMP',
                'source_device': '5651Log TSA',
                'source_ip': '127.0.0.1',
                'source_port': 8000,
                'status': 'ACTIVE',
                'is_receiving_logs': True,
                'total_logs_received': 1250,
                'logs_per_minute': 5,
                'average_log_size': 350,
            },
            {
                'name': 'Mirror Port',
                'monitor_type': 'MIRROR',
                'source_device': 'Switch Port 24',
                'source_ip': '192.168.1.100',
                'source_port': 9999,
                'status': 'ERROR',
                'is_receiving_logs': False,
                'total_logs_received': 0,
                'logs_per_minute': 0,
                'average_log_size': 0,
            },
        ]

        monitors = []
        for data in monitors_data:
            # Son log alınma zamanını ayarla
            if data['is_receiving_logs']:
                last_log = timezone.now() - timedelta(minutes=random.randint(1, 10))
                last_heartbeat = timezone.now() - timedelta(minutes=random.randint(1, 5))
            else:
                last_log = timezone.now() - timedelta(minutes=random.randint(20, 60))
                last_heartbeat = timezone.now() - timedelta(minutes=random.randint(10, 30))

            monitor = LogFlowMonitor.objects.create(
                company=company,
                name=data['name'],
                monitor_type=data['monitor_type'],
                source_device=data['source_device'],
                source_ip=data['source_ip'],
                source_port=data['source_port'],
                status=data['status'],
                is_receiving_logs=data['is_receiving_logs'],
                last_log_received=last_log,
                last_heartbeat=last_heartbeat,
                total_logs_received=data['total_logs_received'],
                logs_per_minute=data['logs_per_minute'],
                average_log_size=data['average_log_size'],
                warning_threshold_minutes=5,
                error_threshold_minutes=15,
                notify_on_warning=True,
                notify_on_error=True,
                notification_recipients='admin@demo-kafe.com,it@demo-kafe.com',
                is_active=True,
            )
            monitors.append(monitor)
            self.stdout.write(f'  ✅ {monitor.name} oluşturuldu')

        return monitors

    def create_alerts(self, company, monitors):
        """Demo uyarılar oluştur"""
        alerts_data = [
            {
                'monitor': monitors[2],  # Syslog Sunucu
                'alert_type': 'NO_LOGS',
                'severity': 'HIGH',
                'title': 'Syslog Sunucu Log Göndermiyor',
                'message': 'Syslog sunucu 15 dakikadır log göndermiyor. Bağlantı kontrol edilmeli.',
                'is_resolved': False,
            },
            {
                'monitor': monitors[4],  # Mirror Port
                'alert_type': 'DEVICE_OFFLINE',
                'severity': 'CRITICAL',
                'title': 'Mirror Port Cihazı Çevrimdışı',
                'message': 'Mirror port cihazı ile bağlantı kesildi. Ağ trafiği izlenemiyor.',
                'is_resolved': False,
            },
            {
                'monitor': monitors[0],  # Ana Firewall
                'alert_type': 'HIGH_VOLUME',
                'severity': 'MEDIUM',
                'title': 'Yüksek Log Hacmi Tespit Edildi',
                'message': 'Ana firewall dakikada 50+ log gönderiyor. Normal değer 25.',
                'is_resolved': True,
                'resolved_at': timezone.now() - timedelta(hours=2),
            },
        ]

        for data in alerts_data:
            alert = LogFlowAlert.objects.create(
                company=company,
                monitor=data['monitor'],
                alert_type=data['alert_type'],
                severity=data['severity'],
                title=data['title'],
                message=data['message'],
                detected_at=timezone.now() - timedelta(hours=random.randint(1, 24)),
                is_resolved=data.get('is_resolved', False),
                resolved_at=data.get('resolved_at'),
                notification_sent=True,
                notification_sent_at=timezone.now() - timedelta(hours=random.randint(1, 24)),
            )
            self.stdout.write(f'  ✅ Uyarı oluşturuldu: {alert.title}')

    def create_statistics(self, company, monitors):
        """Demo istatistikler oluştur"""
        today = timezone.now().date()
        
        for monitor in monitors:
            for hour in range(24):
                # Rastgele istatistikler
                total_logs = random.randint(100, 2000)
                total_bytes = total_logs * monitor.average_log_size
                peak_logs = random.randint(30, 80)
                uptime = random.randint(50, 60)  # 50-60 dakika uptime
                downtime = 60 - uptime
                alert_count = random.randint(0, 3)

                LogFlowStatistics.objects.create(
                    company=company,
                    monitor=monitor,
                    date=today,
                    hour=hour,
                    total_logs=total_logs,
                    total_bytes=total_bytes,
                    average_log_size=monitor.average_log_size,
                    peak_logs_per_minute=peak_logs,
                    uptime_minutes=uptime,
                    downtime_minutes=downtime,
                    alert_count=alert_count,
                )
        
        self.stdout.write(f'  ✅ 24 saatlik istatistikler oluşturuldu ({len(monitors)} monitör)')
