from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from log_kayit.models import Company
from security_alerts.models import SecurityThreat, SecurityAlert, ThreatIntelligence, SecurityIncident, SecurityMetrics


class Command(BaseCommand):
    help = 'Security Alerts modülü için örnek veriler oluşturur'

    def add_arguments(self, parser):
        parser.add_argument('--company-slug', type=str, required=True, help='Şirket slug\'ı')

    def handle(self, *args, **options):
        company_slug = options['company_slug']
        
        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Şirket bulunamadı: {company_slug}'))
            return

        # Kullanıcı oluştur (eğer yoksa)
        user, created = User.objects.get_or_create(
            username='security_admin',
            defaults={
                'first_name': 'Security',
                'last_name': 'Admin',
                'email': 'security@example.com',
                'is_staff': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Security admin kullanıcısı oluşturuldu'))

        # Örnek tehditler oluştur
        threat_types = ['MALWARE', 'PHISHING', 'DDOS', 'BRUTE_FORCE', 'SQL_INJECTION', 'XSS', 'PORT_SCAN']
        severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        statuses = ['DETECTED', 'ANALYZING', 'CONFIRMED', 'MITIGATED', 'RESOLVED']
        
        threats = []
        for i in range(15):
            threat = SecurityThreat.objects.create(
                company=company,
                threat_type=random.choice(threat_types),
                severity=random.choice(severities),
                status=random.choice(statuses),
                title=f'Tehdit #{i+1}: {random.choice(threat_types).replace("_", " ").title()}',
                description=f'Bu tehdit {company.name} için tespit edilmiştir. Detaylı analiz gereklidir.',
                source_ip=f'192.168.1.{random.randint(1, 254)}',
                destination_ip=f'10.0.0.{random.randint(1, 254)}',
                source_port=random.randint(1024, 65535),
                destination_port=random.choice([80, 443, 22, 21, 25]),
                assigned_to=user if random.choice([True, False]) else None,
                confidence_score=random.randint(60, 95),
                false_positive_probability=random.randint(5, 25),
                tags=f'tag{i+1}, security, threat'
            )
            threats.append(threat)
            self.stdout.write(f'Tehdit oluşturuldu: {threat.title}')

        # Örnek uyarılar oluştur
        alert_types = ['THREAT_DETECTED', 'ANOMALY_DETECTED', 'POLICY_VIOLATION', 'SYSTEM_COMPROMISE', 'DATA_BREACH']
        priorities = ['LOW', 'NORMAL', 'HIGH', 'URGENT']
        
        alerts = []
        for i in range(20):
            alert = SecurityAlert.objects.create(
                company=company,
                alert_type=random.choice(alert_types),
                priority=random.choice(priorities),
                title=f'Uyarı #{i+1}: {random.choice(alert_types).replace("_", " ").title()}',
                message=f'Bu uyarı {company.name} için oluşturulmuştur. Acil müdahale gerekebilir.',
                details={'source': 'automated', 'confidence': random.randint(70, 95)},
                is_acknowledged=random.choice([True, False]),
                is_resolved=random.choice([True, False]),
                acknowledged_at=timezone.now() - timedelta(hours=random.randint(1, 24)) if random.choice([True, False]) else None,
                resolved_at=timezone.now() - timedelta(hours=random.randint(1, 12)) if random.choice([True, False]) else None,
                acknowledged_by=user if random.choice([True, False]) else None,
                resolved_by=user if random.choice([True, False]) else None,
                related_threat=random.choice(threats) if threats and random.choice([True, False]) else None
            )
            alerts.append(alert)
            self.stdout.write(f'Uyarı oluşturuldu: {alert.title}')

        # Örnek olaylar oluştur
        incident_types = ['BREACH', 'INTRUSION', 'MALWARE', 'PHISHING', 'DDOS', 'INSIDER_THREAT']
        incident_statuses = ['OPEN', 'INVESTIGATING', 'CONTAINED', 'RESOLVED', 'CLOSED']
        
        incidents = []
        for i in range(8):
            incident = SecurityIncident.objects.create(
                company=company,
                incident_type=random.choice(incident_types),
                status=random.choice(incident_statuses),
                title=f'Olay #{i+1}: {random.choice(incident_types).replace("_", " ").title()}',
                description=f'Bu olay {company.name} için keşfedilmiştir. Güvenlik ekibi müdahale etmektedir.',
                severity=random.choice(severities),
                impact_level=random.choice(severities),
                assigned_to=user if random.choice([True, False]) else None,
                notes=f'Olay notları: {i+1}. olay için detaylı bilgiler burada yer alacak.',
                started_at=timezone.now() - timedelta(days=random.randint(1, 7)),
                contained_at=timezone.now() - timedelta(hours=random.randint(1, 48)) if random.choice([True, False]) else None,
                resolved_at=timezone.now() - timedelta(hours=random.randint(1, 24)) if random.choice([True, False]) else None
            )
            
            # İlişkili tehditler ve uyarılar ekle
            if threats:
                incident.related_threats.set(random.sample(threats, min(3, len(threats))))
            if alerts:
                incident.related_alerts.set(random.sample(alerts, min(5, len(alerts))))
            
            incidents.append(incident)
            self.stdout.write(f'Olay oluşturuldu: {incident.title}')

        # Örnek tehdit istihbaratı oluştur
        intel_types = ['IP_REPUTATION', 'DOMAIN_REPUTATION', 'MALWARE_SIGNATURE', 'ATTACK_PATTERN', 'VULNERABILITY']
        sources = ['CrowdStrike', 'FireEye', 'Palo Alto', 'Cisco Talos', 'Microsoft']
        
        for i in range(12):
            ThreatIntelligence.objects.create(
                company=company,
                intel_type=random.choice(intel_types),
                name=f'İstihbarat #{i+1}: {random.choice(intel_types).replace("_", " ").title()}',
                description=f'Bu istihbarat {company.name} için toplanmıştır.',
                value=f'value_{i+1}_{random.randint(1000, 9999)}',
                confidence=random.randint(70, 95),
                severity=random.choice(severities),
                source=random.choice(sources),
                first_seen=timezone.now() - timedelta(days=random.randint(1, 30)),
                tags=f'intel{i+1}, threat, intelligence'
            )
            self.stdout.write(f'Tehdit istihbaratı oluşturuldu: #{i+1}')

        # Örnek metrikler oluştur (son 7 gün)
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            
            # O gün için tehdit sayısı
            daily_threats = SecurityThreat.objects.filter(
                company=company,
                detection_time__date=date
            ).count()
            
            # O gün için uyarı sayısı
            daily_alerts = SecurityAlert.objects.filter(
                company=company,
                created_at__date=date
            ).count()
            
            # O gün için olay sayısı
            daily_incidents = SecurityIncident.objects.filter(
                company=company,
                discovered_at__date=date
            ).count()
            
            SecurityMetrics.objects.create(
                company=company,
                date=date,
                total_threats=daily_threats,
                critical_threats=SecurityThreat.objects.filter(company=company, detection_time__date=date, severity='CRITICAL').count(),
                high_threats=SecurityThreat.objects.filter(company=company, detection_time__date=date, severity='HIGH').count(),
                medium_threats=SecurityThreat.objects.filter(company=company, detection_time__date=date, severity='MEDIUM').count(),
                low_threats=SecurityThreat.objects.filter(company=company, detection_time__date=date, severity='LOW').count(),
                total_alerts=daily_alerts,
                acknowledged_alerts=SecurityAlert.objects.filter(company=company, created_at__date=date, is_acknowledged=True).count(),
                resolved_alerts=SecurityAlert.objects.filter(company=company, created_at__date=date, is_resolved=True).count(),
                total_incidents=daily_incidents,
                open_incidents=SecurityIncident.objects.filter(company=company, discovered_at__date=date, status='OPEN').count(),
                resolved_incidents=SecurityIncident.objects.filter(company=company, discovered_at__date=date, status='RESOLVED').count(),
                mean_time_to_detect=random.uniform(0.5, 4.0),
                mean_time_to_resolve=random.uniform(2.0, 12.0)
            )
            self.stdout.write(f'Metrik oluşturuldu: {date}')

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {company.name} için Security Alerts örnek verileri başarıyla oluşturuldu!\n'
                f'📊 {len(threats)} tehdit, {len(alerts)} uyarı, {len(incidents)} olay oluşturuldu.'
            )
        )
