from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from audit_logging.models import AuditLog, AuditLogConfig
from log_kayit.models import Company


class Command(BaseCommand):
    help = 'Audit logging modülü için demo veriler oluşturur'

    def handle(self, *args, **options):
        self.stdout.write('Audit logging demo verileri oluşturuluyor...')
        
        # Demo company'yi al
        try:
            company = Company.objects.get(slug='demo-kafe')
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR('Demo company bulunamadı. Önce demo company oluşturun.'))
            return
        
        # Demo user'ı al veya oluştur
        user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'User',
            }
        )
        
        # Demo audit log'ları oluştur
        self.create_demo_logs(company, user)
        
        # Audit log konfigürasyonları oluştur
        self.create_audit_configs(company)
        
        self.stdout.write(self.style.SUCCESS('Audit logging demo verileri başarıyla oluşturuldu!'))

    def create_demo_logs(self, company, user):
        """Demo audit log'ları oluştur"""
        
        actions = [
            ('LOGIN', 'User logged in', 'MEDIUM'),
            ('LOGOUT', 'User logged out', 'LOW'),
            ('CREATE', 'Created new log entry', 'MEDIUM'),
            ('UPDATE', 'Updated log entry', 'LOW'),
            ('DELETE', 'Deleted log entry', 'HIGH'),
            ('EXPORT', 'Exported data', 'MEDIUM'),
            ('PASSWORD_CHANGE', 'Changed password', 'HIGH'),
            ('PERMISSION_CHANGE', 'Changed user permissions', 'CRITICAL'),
            ('API_ACCESS', 'API endpoint accessed', 'LOW'),
            ('SECURITY_EVENT', 'Security event detected', 'CRITICAL'),
        ]
        
        ip_addresses = [
            '192.168.1.100',
            '192.168.1.101',
            '10.0.0.50',
            '172.16.0.25',
            '192.168.0.200',
        ]
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]
        
        # Son 30 gün için loglar oluştur
        for i in range(100):
            action, description, severity = random.choice(actions)
            
            # Rastgele zaman (son 30 gün)
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            timestamp = timezone.now() - timedelta(
                days=days_ago, 
                hours=hours_ago, 
                minutes=minutes_ago
            )
            
            # Rastgele başarı durumu (çoğunlukla başarılı)
            success = random.choices([True, False], weights=[85, 15])[0]
            
            # Başarısız olaylar için hata mesajı
            error_message = None
            if not success:
                error_messages = [
                    'Authentication failed',
                    'Permission denied',
                    'Resource not found',
                    'Invalid request format',
                    'Database connection error',
                ]
                error_message = random.choice(error_messages)
            
            AuditLog.objects.create(
                user=user if random.choice([True, False]) else None,
                company=company,
                action=action,
                severity=severity,
                resource_type=random.choice(['LogKayit', 'User', 'Company', 'Report', 'API']),
                resource_id=str(random.randint(1, 1000)),
                resource_name=f"Resource_{random.randint(1, 100)}",
                description=description,
                details={
                    'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
                    'endpoint': f'/api/v1/{random.choice(["logs", "users", "reports"])}',
                    'response_time': random.randint(10, 500),
                },
                ip_address=random.choice(ip_addresses),
                user_agent=random.choice(user_agents),
                timestamp=timestamp,
                success=success,
                error_message=error_message,
            )
        
        self.stdout.write(f'✓ 100 demo audit log oluşturuldu')

    def create_audit_configs(self, company):
        """Audit log konfigürasyonları oluştur"""
        
        configs = [
            ('LOGIN', True, 'MEDIUM', 365),
            ('LOGOUT', True, 'LOW', 180),
            ('CREATE', True, 'MEDIUM', 730),
            ('UPDATE', True, 'LOW', 365),
            ('DELETE', True, 'HIGH', 2555),  # 7 yıl
            ('EXPORT', True, 'MEDIUM', 1095),  # 3 yıl
            ('PASSWORD_CHANGE', True, 'HIGH', 1825),  # 5 yıl
            ('PERMISSION_CHANGE', True, 'CRITICAL', 2555),  # 7 yıl
            ('API_ACCESS', False, 'LOW', 90),  # Kapalı
            ('SECURITY_EVENT', True, 'CRITICAL', 2555),  # 7 yıl
        ]
        
        for action, enabled, severity, retention_days in configs:
            AuditLogConfig.objects.get_or_create(
                company=company,
                action=action,
                defaults={
                    'enabled': enabled,
                    'severity': severity,
                    'retention_days': retention_days,
                }
            )
        
        self.stdout.write(f'✓ Audit log konfigürasyonları oluşturuldu')
