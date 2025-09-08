from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from firewall_management.models import FirewallRule, FirewallPolicy, FirewallEvent, FirewallLog
from log_kayit.models import Company

class Command(BaseCommand):
    help = 'Örnek firewall kuralları, politikaları ve olayları oluşturur'
    
    def add_arguments(self, parser):
        parser.add_argument('--company-slug', type=str, help='Şirket slug\'ı')
    
    def handle(self, *args, **options):
        company_slug = options.get('company_slug', 'site')
        
        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Şirket bulunamadı: {company_slug}')
            )
            return
        
        self.stdout.write(f'Şirket için örnek firewall verileri oluşturuluyor: {company.name}')
        
        # Örnek firewall kuralları
        rules_data = [
            {
                'name': 'HTTP İzin Ver',
                'description': 'HTTP trafiğine izin ver',
                'rule_type': 'ALLOW',
                'protocol': 'TCP',
                'source_ip': '0.0.0.0/0',
                'source_port': None,
                'destination_ip': '192.168.1.0/24',
                'destination_port': 80,
                'priority': 3,
            },
            {
                'name': 'HTTPS İzin Ver',
                'description': 'HTTPS trafiğine izin ver',
                'rule_type': 'ALLOW',
                'protocol': 'TCP',
                'source_ip': '0.0.0.0/0',
                'source_port': None,
                'destination_ip': '192.168.1.0/24',
                'destination_port': 443,
                'priority': 3,
            },
            {
                'name': 'SSH İzin Ver',
                'description': 'SSH bağlantılarına izin ver',
                'rule_type': 'ALLOW',
                'protocol': 'TCP',
                'source_ip': '192.168.1.0/24',
                'source_port': None,
                'destination_ip': '192.168.1.0/24',
                'destination_port': 22,
                'priority': 4,
            },
            {
                'name': 'FTP Engelle',
                'description': 'FTP trafiğini engelle',
                'rule_type': 'DENY',
                'protocol': 'TCP',
                'source_ip': '0.0.0.0/0',
                'source_port': None,
                'destination_ip': '0.0.0.0/0',
                'destination_port': 21,
                'priority': 5,
            },
            {
                'name': 'Telnet Engelle',
                'description': 'Telnet trafiğini engelle',
                'rule_type': 'DROP',
                'protocol': 'TCP',
                'source_ip': '0.0.0.0/0',
                'source_port': None,
                'destination_ip': '0.0.0.0/0',
                'destination_port': 23,
                'priority': 5,
            },
            {
                'name': 'ICMP İzin Ver',
                'description': 'Ping trafiğine izin ver',
                'rule_type': 'ALLOW',
                'protocol': 'ICMP',
                'source_ip': '192.168.1.0/24',
                'source_port': None,
                'destination_ip': '192.168.1.0/24',
                'destination_port': None,
                'priority': 2,
            },
        ]
        
        created_rules = []
        for rule_data in rules_data:
            rule, created = FirewallRule.objects.get_or_create(
                company=company,
                name=rule_data['name'],
                defaults=rule_data
            )
            if created:
                self.stdout.write(f'  - Kural oluşturuldu: {rule.name}')
            else:
                self.stdout.write(f'  - Kural zaten mevcut: {rule.name}')
            created_rules.append(rule)
        
        # Örnek firewall politikaları
        policies_data = [
            {
                'name': 'Temel Güvenlik Politikası',
                'description': 'Temel güvenlik kuralları',
                'policy_type': 'SECURITY',
            },
            {
                'name': 'Uyumluluk Politikası',
                'description': 'ISO 27001 uyumluluk kuralları',
                'policy_type': 'COMPLIANCE',
            },
            {
                'name': 'Performans Optimizasyonu',
                'description': 'Ağ performansını artıran kurallar',
                'policy_type': 'PERFORMANCE',
            },
        ]
        
        created_policies = []
        for policy_data in policies_data:
            policy, created = FirewallPolicy.objects.get_or_create(
                company=company,
                name=policy_data['name'],
                defaults=policy_data
            )
            if created:
                self.stdout.write(f'  - Politika oluşturuldu: {policy.name}')
            else:
                self.stdout.write(f'  - Politika zaten mevcut: {policy.name}')
            created_policies.append(policy)
        
        # Politikaları kurallarla ilişkilendir
        if created_policies and created_rules:
            created_policies[0].rules.add(*created_rules[:3])  # Temel güvenlik
            created_policies[1].rules.add(*created_rules[3:5])  # Uyumluluk
            created_policies[2].rules.add(created_rules[5])  # Performans
        
        # Örnek firewall olayları
        events_data = [
            {
                'event_type': 'RULE_MATCH',
                'severity': 'LOW',
                'source_ip': '192.168.1.100',
                'destination_ip': '192.168.1.1',
                'protocol': 'TCP',
                'port': 80,
                'message': 'HTTP trafiği izin verildi',
                'rule': created_rules[0] if created_rules else None,
            },
            {
                'event_type': 'RULE_VIOLATION',
                'severity': 'MEDIUM',
                'source_ip': '10.0.0.50',
                'destination_ip': '192.168.1.1',
                'protocol': 'TCP',
                'port': 21,
                'message': 'FTP trafiği engellendi',
                'rule': created_rules[3] if len(created_rules) > 3 else None,
            },
            {
                'event_type': 'ATTACK_DETECTED',
                'severity': 'HIGH',
                'source_ip': '203.0.113.0',
                'destination_ip': '192.168.1.1',
                'protocol': 'TCP',
                'port': 22,
                'message': 'SSH brute force saldırısı tespit edildi',
                'rule': created_rules[2] if len(created_rules) > 2 else None,
            },
        ]
        
        for event_data in events_data:
            event, created = FirewallEvent.objects.get_or_create(
                company=company,
                event_type=event_data['event_type'],
                source_ip=event_data['source_ip'],
                destination_ip=event_data['destination_ip'],
                timestamp=timezone.now() - timedelta(hours=random.randint(1, 24)),
                defaults=event_data
            )
            if created:
                self.stdout.write(f'  - Olay oluşturuldu: {event.get_event_type_display()}')
        
        # Örnek firewall logları
        for i in range(50):
            rule = random.choice(created_rules) if created_rules else None
            source_ip = f'192.168.1.{random.randint(1, 254)}'
            destination_ip = f'192.168.1.{random.randint(1, 254)}'
            
            log, created = FirewallLog.objects.get_or_create(
                company=company,
                timestamp=timezone.now() - timedelta(minutes=random.randint(1, 1440)),
                source_ip=source_ip,
                destination_ip=destination_ip,
                protocol=rule.protocol if rule else 'TCP',
                defaults={
                    'source_port': random.randint(1024, 65535),
                    'destination_port': rule.destination_port if rule else 80,
                    'action': rule.rule_type if rule else 'ALLOW',
                    'bytes_sent': random.randint(100, 10000),
                    'bytes_received': random.randint(100, 10000),
                    'packets_sent': random.randint(1, 100),
                    'packets_received': random.randint(1, 100),
                    'rule': rule,
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS('Örnek veriler başarıyla oluşturuldu!')
        )
        self.stdout.write(
            f'Firewall Management dashboard\'a erişmek için: /firewall/dashboard/{company.slug}/'
        )
