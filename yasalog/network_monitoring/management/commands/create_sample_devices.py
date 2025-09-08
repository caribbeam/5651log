from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from network_monitoring.models import NetworkDevice, NetworkLog, NetworkTraffic
from log_kayit.models import Company

class Command(BaseCommand):
    help = 'Örnek network cihazları ve logları oluşturur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-slug',
            type=str,
            help='Şirket slug\'ı (opsiyonel)',
        )

    def handle(self, *args, **options):
        company_slug = options.get('company_slug')
        
        if company_slug:
            try:
                company = Company.objects.get(slug=company_slug)
                companies = [company]
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Şirket bulunamadı: {company_slug}')
                )
                return
        else:
            companies = Company.objects.all()
            if not companies:
                self.stdout.write(
                    self.style.ERROR('Hiç şirket bulunamadı. Önce bir şirket oluşturun.')
                )
                return

        for company in companies:
            self.stdout.write(f'Şirket için örnek cihazlar oluşturuluyor: {company.name}')
            
            # Örnek cihazlar
            devices_data = [
                {
                    'name': 'Ana Router',
                    'device_type': 'ROUTER',
                    'ip_address': '192.168.1.1',
                    'mac_address': '00:11:22:33:44:55',
                    'model': 'Cisco RV320',
                    'manufacturer': 'Cisco',
                    'status': 'ONLINE',
                    'cpu_usage': random.uniform(20, 60),
                    'memory_usage': random.uniform(30, 70),
                    'temperature': random.uniform(35, 55),
                },
                {
                    'name': 'Ana Switch',
                    'device_type': 'SWITCH',
                    'ip_address': '192.168.1.2',
                    'mac_address': '00:11:22:33:44:56',
                    'model': 'HP ProCurve 2510',
                    'manufacturer': 'HP',
                    'status': 'ONLINE',
                    'cpu_usage': random.uniform(10, 40),
                    'memory_usage': random.uniform(20, 50),
                    'temperature': random.uniform(30, 45),
                },
                {
                    'name': 'Firewall',
                    'device_type': 'FIREWALL',
                    'ip_address': '192.168.1.3',
                    'mac_address': '00:11:22:33:44:57',
                    'model': 'SonicWall TZ370',
                    'manufacturer': 'SonicWall',
                    'status': 'ONLINE',
                    'cpu_usage': random.uniform(15, 50),
                    'memory_usage': random.uniform(25, 60),
                    'temperature': random.uniform(40, 60),
                },
                {
                    'name': 'Wi-Fi Access Point 1',
                    'device_type': 'ACCESS_POINT',
                    'ip_address': '192.168.1.10',
                    'mac_address': '00:11:22:33:44:58',
                    'model': 'UniFi AC Pro',
                    'manufacturer': 'Ubiquiti',
                    'status': 'ONLINE',
                    'cpu_usage': random.uniform(5, 30),
                    'memory_usage': random.uniform(15, 40),
                    'temperature': random.uniform(25, 40),
                },
                {
                    'name': 'Wi-Fi Access Point 2',
                    'device_type': 'ACCESS_POINT',
                    'ip_address': '192.168.1.11',
                    'mac_address': '00:11:22:33:44:59',
                    'model': 'UniFi AC Pro',
                    'manufacturer': 'Ubiquiti',
                    'status': 'WARNING',
                    'cpu_usage': random.uniform(60, 85),
                    'memory_usage': random.uniform(70, 90),
                    'temperature': random.uniform(50, 70),
                },
                {
                    'name': 'Backup Server',
                    'device_type': 'SERVER',
                    'ip_address': '192.168.1.20',
                    'mac_address': '00:11:22:33:44:60',
                    'model': 'Dell PowerEdge R230',
                    'manufacturer': 'Dell',
                    'status': 'OFFLINE',
                    'cpu_usage': 0,
                    'memory_usage': 0,
                    'temperature': None,
                },
            ]

            created_devices = []
            for device_data in devices_data:
                device, created = NetworkDevice.objects.get_or_create(
                    company=company,
                    ip_address=device_data['ip_address'],
                    defaults=device_data
                )
                
                if created:
                    created_devices.append(device)
                    self.stdout.write(f'  ✓ Cihaz oluşturuldu: {device.name}')
                else:
                    self.stdout.write(f'  - Cihaz zaten mevcut: {device.name}')

            # Örnek loglar oluştur
            if created_devices:
                self.stdout.write('Örnek loglar oluşturuluyor...')
                
                log_messages = [
                    ('SYSTEM', 'INFO', 'Cihaz başlatıldı'),
                    ('SYSTEM', 'INFO', 'Firmware güncellendi'),
                    ('CONNECTION', 'INFO', 'Yeni kullanıcı bağlandı'),
                    ('CONNECTION', 'WARNING', 'Bağlantı kesildi'),
                    ('SECURITY', 'WARNING', 'Şüpheli aktivite tespit edildi'),
                    ('ERROR', 'ERROR', 'Bağlantı hatası'),
                    ('TRAFFIC', 'INFO', 'Yüksek trafik tespit edildi'),
                    ('SYSTEM', 'WARNING', 'Yüksek CPU kullanımı'),
                    ('SYSTEM', 'WARNING', 'Yüksek sıcaklık'),
                    ('CONNECTION', 'INFO', 'Kullanıcı çıkış yaptı'),
                ]

                for device in created_devices:
                    # Her cihaz için 10-20 arası log oluştur
                    log_count = random.randint(10, 20)
                    
                    for i in range(log_count):
                        log_type, level, message = random.choice(log_messages)
                        
                        # Rastgele zaman (son 24 saat içinde)
                        random_time = timezone.now() - timedelta(
                            hours=random.randint(0, 24),
                            minutes=random.randint(0, 59)
                        )
                        
                        log = NetworkLog.objects.create(
                            company=company,
                            device=device,
                            log_type=log_type,
                            level=level,
                            message=f'{message} - {device.name}',
                            source_ip=f'192.168.1.{random.randint(100, 200)}' if random.choice([True, False]) else None,
                            destination_ip=f'8.8.8.{random.randint(1, 255)}' if random.choice([True, False]) else None,
                            source_port=random.randint(1024, 65535) if random.choice([True, False]) else None,
                            destination_port=random.choice([80, 443, 22, 21, 25]) if random.choice([True, False]) else None,
                            protocol=random.choice(['TCP', 'UDP', 'ICMP']) if random.choice([True, False]) else '',
                            bytes_transferred=random.randint(1024, 1048576),
                            duration=random.uniform(0.1, 5.0)
                        )
                        
                        # Timestamp'i manuel olarak ayarla
                        log.timestamp = random_time
                        log.save()

                    self.stdout.write(f'  ✓ {device.name} için {log_count} log oluşturuldu')

                # Örnek trafik verileri
                self.stdout.write('Örnek trafik verileri oluşturuluyor...')
                
                for device in created_devices:
                    if device.status == 'ONLINE':
                        # Her cihaz için 5-10 trafik kaydı
                        traffic_count = random.randint(5, 10)
                        
                        for i in range(traffic_count):
                            start_time = timezone.now() - timedelta(
                                hours=random.randint(0, 24),
                                minutes=random.randint(0, 59)
                            )
                            end_time = start_time + timedelta(seconds=random.randint(1, 300))
                            
                            NetworkTraffic.objects.create(
                                company=company,
                                device=device,
                                source_ip=f'192.168.1.{random.randint(100, 200)}',
                                destination_ip=f'{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}',
                                source_port=random.randint(1024, 65535),
                                destination_port=random.choice([80, 443, 22, 21, 25, 53]),
                                protocol=random.choice(['TCP', 'UDP']),
                                bytes_sent=random.randint(1024, 10485760),
                                bytes_received=random.randint(1024, 10485760),
                                packets_sent=random.randint(10, 1000),
                                packets_received=random.randint(10, 1000),
                                start_time=start_time,
                                end_time=end_time,
                                duration=(end_time - start_time).total_seconds(),
                                application=random.choice(['HTTP', 'HTTPS', 'SSH', 'FTP', 'DNS', 'Email']),
                            )

                        self.stdout.write(f'  ✓ {device.name} için {traffic_count} trafik kaydı oluşturuldu')

        self.stdout.write(
            self.style.SUCCESS('Örnek veriler başarıyla oluşturuldu!')
        )
        self.stdout.write(
            self.style.SUCCESS('Network Monitoring dashboard\'a erişmek için: /network/dashboard/<company-slug>/')
        )
