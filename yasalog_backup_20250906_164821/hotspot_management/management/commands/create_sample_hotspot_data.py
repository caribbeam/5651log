from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from log_kayit.models import Company
from hotspot_management.models import (
    HotspotConfiguration, BandwidthPolicy, HotspotUser, 
    UserSession, ContentFilter, AccessLog, HotspotMetrics
)
from datetime import datetime, timedelta
import random
from django.utils import timezone


class Command(BaseCommand):
    help = 'Hotspot Management modülü için örnek veri oluşturur'

    def add_arguments(self, parser):
        parser.add_argument('--company-slug', type=str, required=True, help='Şirket slug\'ı')

    def handle(self, *args, **options):
        company_slug = options['company_slug']
        
        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Şirket bulunamadı: {company_slug}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Şirket bulundu: {company.name}')
        )

        # Bant genişliği politikaları oluştur
        policies = []
        policy_data = [
            ('Ücretsiz', 'FREE', 2, 1, 1.0),
            ('Premium', 'PREMIUM', 10, 5, 5.0),
            ('İş', 'BUSINESS', 20, 10, 10.0),
            ('Misafir', 'GUEST', 5, 2, 2.0),
            ('Personel', 'STAFF', 50, 25, 50.0),
        ]

        for name, policy_type, download, upload, daily in policy_data:
            policy, created = BandwidthPolicy.objects.get_or_create(
                company=company,
                name=name,
                defaults={
                    'policy_type': policy_type,
                    'download_limit_mbps': download,
                    'upload_limit_mbps': upload,
                    'daily_limit_gb': daily,
                    'priority': len(policies) + 1,
                }
            )
            policies.append(policy)
            if created:
                self.stdout.write(f'Bant genişliği politikası oluşturuldu: {name}')

        # Hotspot konfigürasyonları oluştur
        hotspots = []
        hotspot_data = [
            ('Ana Lobi', 'LOBI_WIFI', False, 20, 10, 10),
            ('Konferans Salonu', 'KONFERANS_WIFI', False, 50, 25, 25),
            ('Restoran', 'RESTORAN_WIFI', True, 10, 5, 5),
            ('Oda Servisi', 'ODA_WIFI', False, 100, 50, 50),
            ('Misafir Alanı', 'MISAFIR_WIFI', True, 5, 2, 2),
        ]

        for name, ssid, is_public, max_bw, max_up, max_down in hotspot_data:
            hotspot, created = HotspotConfiguration.objects.get_or_create(
                company=company,
                ssid=ssid,
                defaults={
                    'name': name,
                    'is_public': is_public,
                    'max_bandwidth_mbps': max_bw,
                    'max_upload_mbps': max_up,
                    'max_download_mbps': max_down,
                    'session_timeout_hours': 24,
                    'max_concurrent_users': 100,
                    'enable_content_filtering': True,
                    'block_adult_content': True,
                    'block_gambling': True,
                    'block_social_media': False,
                    'start_time': '00:00',
                    'end_time': '23:59',
                    'is_24_7': True,
                }
            )
            hotspots.append(hotspot)
            if created:
                self.stdout.write(f'Hotspot konfigürasyonu oluşturuldu: {name}')

        # Hotspot kullanıcıları oluştur
        users = []
        user_types = ['GUEST', 'REGISTERED', 'STAFF', 'VIP']
        
        for i in range(50):
            user_type = random.choice(user_types)
            hotspot = random.choice(hotspots)
            policy = random.choice(policies) if user_type in ['STAFF', 'VIP'] else policies[0]
            
            # MAC adresi oluştur
            mac_parts = [f"{random.randint(0, 255):02x}" for _ in range(6)]
            mac_address = ":".join(mac_parts)
            
            # IP adresi oluştur
            ip_parts = [random.randint(1, 254) for _ in range(4)]
            ip_address = ".".join(map(str, ip_parts))
            
            user, created = HotspotUser.objects.get_or_create(
                company=company,
                mac_address=mac_address,
                defaults={
                    'hotspot': hotspot,
                    'bandwidth_policy': policy,
                    'username': f'user_{i+1}',
                    'email': f'user_{i+1}@example.com',
                    'phone': f'+90{random.randint(500000000, 599999999)}',
                    'user_type': user_type,
                    'ip_address': ip_address,
                    'device_info': f'Device {i+1} - {random.choice(["Android", "iOS", "Windows", "macOS"])}',
                    'is_active': random.choice([True, True, True, False]),  # %75 aktif
                    'is_blocked': random.choice([False, False, False, True]),  # %25 engellenmiş
                }
            )
            users.append(user)
            if created:
                self.stdout.write(f'Hotspot kullanıcısı oluşturuldu: user_{i+1}')

        # İçerik filtreleme kuralları oluştur
        content_filters = []
        filter_data = [
            ('Yetişkin İçerik', 'CATEGORY', 'BLOCK', 'adult'),
            ('Kumar Siteleri', 'CATEGORY', 'BLOCK', 'gambling'),
            ('Sosyal Medya', 'CATEGORY', 'ALLOW', 'social_media'),
            ('YouTube', 'DOMAIN', 'ALLOW', 'youtube.com'),
            ('Facebook', 'DOMAIN', 'BLOCK', 'facebook.com'),
            ('Instagram', 'DOMAIN', 'BLOCK', 'instagram.com'),
            ('LinkedIn', 'DOMAIN', 'ALLOW', 'linkedin.com'),
            ('Google', 'DOMAIN', 'ALLOW', 'google.com'),
            ('Spam', 'KEYWORD', 'BLOCK', 'spam'),
            ('Virüs', 'KEYWORD', 'BLOCK', 'virus'),
        ]

        for name, filter_type, action, value in filter_data:
            filter_obj, created = ContentFilter.objects.get_or_create(
                company=company,
                name=name,
                defaults={
                    'filter_type': filter_type,
                    'action': action,
                    'value': value,
                    'description': f'{name} için {action} kuralı',
                    'priority': len(content_filters) + 1,
                }
            )
            content_filters.append(filter_obj)
            if created:
                self.stdout.write(f'İçerik filtresi oluşturuldu: {name}')

        # Kullanıcı oturumları oluştur
        sessions = []
        for i in range(100):
            user = random.choice(users)
            hotspot = user.hotspot
            
            # Rastgele oturum süresi (1 dakika - 8 saat)
            duration_minutes = random.randint(1, 480)
            start_time = timezone.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Bant genişliği kullanımı
            bytes_uploaded = random.randint(1024, 100 * 1024 * 1024)  # 1KB - 100MB
            bytes_downloaded = random.randint(1024, 500 * 1024 * 1024)  # 1KB - 500MB
            total_bytes = bytes_uploaded + bytes_downloaded
            
            session, created = UserSession.objects.get_or_create(
                user=user,
                session_id=f'session_{i+1}_{user.id}',
                defaults={
                    'hotspot': hotspot,
                    'start_time': start_time,
                    'end_time': end_time,
                    'status': random.choice(['ACTIVE', 'EXPIRED', 'TERMINATED']),
                    'bytes_uploaded': bytes_uploaded,
                    'bytes_downloaded': bytes_downloaded,
                    'total_bytes': total_bytes,
                    'duration_minutes': duration_minutes,
                }
            )
            sessions.append(session)
            if created:
                self.stdout.write(f'Kullanıcı oturumu oluşturuldu: session_{i+1}')

        # Erişim logları oluştur
        domains = [
            'google.com', 'youtube.com', 'facebook.com', 'instagram.com',
            'linkedin.com', 'twitter.com', 'netflix.com', 'spotify.com',
            'amazon.com', 'ebay.com', 'wikipedia.org', 'stackoverflow.com'
        ]
        
        for i in range(200):
            user = random.choice(users)
            session = random.choice(sessions)
            domain = random.choice(domains)
            
            # İçerik filtreleme kontrolü
            content_filter = random.choice(content_filters) if random.random() < 0.3 else None
            was_blocked = content_filter and content_filter.action == 'BLOCK' if content_filter else False
            
            log, created = AccessLog.objects.get_or_create(
                user=user,
                session=session,
                url=f'https://{domain}/page_{i+1}',
                defaults={
                    'domain': domain,
                    'ip_address': user.ip_address,
                    'content_filter': content_filter,
                    'was_blocked': was_blocked,
                    'timestamp': timezone.now() - timedelta(
                        days=random.randint(0, 30),
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    ),
                }
            )
            if created and i % 50 == 0:
                self.stdout.write(f'Erişim logu oluşturuldu: {i+1}/200')

        # Hotspot metrikleri oluştur
        for i in range(7):  # Son 7 gün
            date = timezone.now().date() - timedelta(days=i)
            
            for hour in range(24):
                # Rastgele metrikler
                active_users = random.randint(10, 50)
                total_sessions = random.randint(20, 100)
                new_users = random.randint(0, 10)
                bandwidth_used = round(random.uniform(5.0, 50.0), 2)
                peak_bandwidth = round(bandwidth_used * random.uniform(1.2, 2.0), 2)
                blocked_requests = random.randint(0, 20)
                total_requests = random.randint(100, 500)
                
                metric, created = HotspotMetrics.objects.get_or_create(
                    company=company,
                    hotspot=random.choice(hotspots),
                    date=date,
                    hour=hour,
                    defaults={
                        'active_users': active_users,
                        'total_sessions': total_sessions,
                        'new_users': new_users,
                        'bandwidth_used_mbps': bandwidth_used,
                        'peak_bandwidth_mbps': peak_bandwidth,
                        'blocked_requests': blocked_requests,
                        'total_requests': total_requests,
                    }
                )
                if created and hour % 6 == 0:
                    self.stdout.write(f'Metrik oluşturuldu: {date} {hour}:00')

        self.stdout.write(
            self.style.SUCCESS(
                f'Hotspot Management modülü için örnek veri başarıyla oluşturuldu!\n'
                f'- {len(policies)} bant genişliği politikası\n'
                f'- {len(hotspots)} hotspot konfigürasyonu\n'
                f'- {len(users)} kullanıcı\n'
                f'- {len(content_filters)} içerik filtresi\n'
                f'- {len(sessions)} oturum\n'
                f'- 200 erişim logu\n'
                f'- 7 günlük metrikler'
            )
        )
