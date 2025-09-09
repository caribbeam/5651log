"""
Log Verification Demo Verileri Oluşturma
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from log_kayit.models import Company
from log_verification.models import LogVerificationSession, LogVerificationResult, LogIntegrityReport, LogVerificationTemplate
import random


class Command(BaseCommand):
    help = 'Log verification için demo veriler oluşturur'

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

        # Demo şablonlar oluştur
        templates = self.create_templates(company)
        
        # Demo oturumlar oluştur
        sessions = self.create_sessions(company, templates)
        
        # Demo sonuçlar oluştur
        self.create_results(sessions)
        
        # Demo raporlar oluştur
        self.create_reports(sessions)

        self.stdout.write(
            self.style.SUCCESS('Demo veriler başarıyla oluşturuldu!')
        )

    def clear_data(self, company):
        """Mevcut verileri temizle"""
        LogIntegrityReport.objects.filter(session__company=company).delete()
        LogVerificationResult.objects.filter(session__company=company).delete()
        LogVerificationSession.objects.filter(company=company).delete()
        LogVerificationTemplate.objects.filter(company=company).delete()
        
        self.stdout.write(
            self.style.SUCCESS('Mevcut veriler temizlendi!')
        )

    def create_templates(self, company):
        """Demo şablonlar oluştur"""
        templates_data = [
            {
                'name': '5651 Uyumluluk Şablonu',
                'description': '5651 sayılı kanun uyumluluğu için standart doğrulama şablonu',
                'verification_rules': {
                    'hash_verification': True,
                    'signature_verification': True,
                    'integrity_check': True,
                    'timestamp_validation': True
                },
                'required_fields': ['timestamp', 'user_id', 'action', 'ip_address'],
                'hash_algorithm': 'SHA256',
                'auto_generate_report': True,
                'report_format': 'PDF'
            },
            {
                'name': 'Hızlı Doğrulama Şablonu',
                'description': 'Hızlı log doğrulama için basit şablon',
                'verification_rules': {
                    'hash_verification': True,
                    'signature_verification': False,
                    'integrity_check': True,
                    'timestamp_validation': False
                },
                'required_fields': ['timestamp', 'action'],
                'hash_algorithm': 'MD5',
                'auto_generate_report': False,
                'report_format': 'CSV'
            },
            {
                'name': 'Detaylı Analiz Şablonu',
                'description': 'Kapsamlı log analizi için detaylı şablon',
                'verification_rules': {
                    'hash_verification': True,
                    'signature_verification': True,
                    'integrity_check': True,
                    'timestamp_validation': True,
                    'pattern_analysis': True,
                    'anomaly_detection': True
                },
                'required_fields': ['timestamp', 'user_id', 'action', 'ip_address', 'result', 'details'],
                'hash_algorithm': 'SHA256',
                'auto_generate_report': True,
                'report_format': 'PDF'
            }
        ]

        templates = []
        for data in templates_data:
            template = LogVerificationTemplate.objects.create(
                company=company,
                name=data['name'],
                description=data['description'],
                verification_rules=data['verification_rules'],
                required_fields=data['required_fields'],
                hash_algorithm=data['hash_algorithm'],
                auto_generate_report=data['auto_generate_report'],
                report_format=data['report_format'],
                is_active=True
            )
            templates.append(template)
            self.stdout.write(f'  ✅ {template.name} oluşturuldu')

        return templates

    def create_sessions(self, company, templates):
        """Demo oturumlar oluştur"""
        sessions_data = [
            {
                'session_name': 'Aylık Log Doğrulama - Ocak 2024',
                'description': 'Ocak 2024 ayına ait tüm log kayıtlarının doğrulama işlemi',
                'file_name': 'logs_january_2024.csv',
                'file_size': 15728640,  # 15MB
                'verification_type': 'COMPLETE_VERIFICATION',
                'status': 'COMPLETED',
                'progress_percentage': 100,
                'total_records': 12500,
                'verified_records': 11800,
                'failed_records': 50,
                'modified_records': 650,
                'started_at': timezone.now() - timedelta(days=2, hours=3),
                'completed_at': timezone.now() - timedelta(days=2, hours=1),
            },
            {
                'session_name': 'Güvenlik Log Analizi - Haftalık',
                'description': 'Son haftanın güvenlik loglarının detaylı analizi',
                'file_name': 'security_logs_week_15.csv',
                'file_size': 8388608,  # 8MB
                'verification_type': 'SIGNATURE_VERIFICATION',
                'status': 'PROCESSING',
                'progress_percentage': 65,
                'total_records': 8500,
                'verified_records': 5525,
                'failed_records': 25,
                'modified_records': 200,
                'started_at': timezone.now() - timedelta(hours=2),
                'completed_at': None,
            },
            {
                'session_name': 'Firewall Log Doğrulama',
                'description': 'Firewall cihazından gelen log kayıtlarının bütünlük kontrolü',
                'file_name': 'firewall_logs_20240315.log',
                'file_size': 5242880,  # 5MB
                'verification_type': 'INTEGRITY_CHECK',
                'status': 'COMPLETED',
                'progress_percentage': 100,
                'total_records': 3200,
                'verified_records': 3150,
                'failed_records': 10,
                'modified_records': 40,
                'started_at': timezone.now() - timedelta(days=1, hours=5),
                'completed_at': timezone.now() - timedelta(days=1, hours=4),
            },
            {
                'session_name': 'Hotspot Kullanıcı Logları',
                'description': 'Hotspot sistemindeki kullanıcı aktivite loglarının doğrulaması',
                'file_name': 'hotspot_users_20240314.csv',
                'file_size': 2097152,  # 2MB
                'verification_type': 'HASH_VERIFICATION',
                'status': 'FAILED',
                'progress_percentage': 30,
                'total_records': 1500,
                'verified_records': 450,
                'failed_records': 1050,
                'modified_records': 0,
                'started_at': timezone.now() - timedelta(hours=6),
                'completed_at': timezone.now() - timedelta(hours=5),
                'error_message': 'Dosya formatı uyumsuzluğu: Beklenen CSV formatı bulunamadı'
            },
            {
                'session_name': 'Sistem Log Bütünlük Kontrolü',
                'description': 'Sistem loglarının bütünlük ve imza doğrulaması',
                'file_name': 'system_logs_20240313.log',
                'file_size': 10485760,  # 10MB
                'verification_type': 'COMPLETE_VERIFICATION',
                'status': 'PENDING',
                'progress_percentage': 0,
                'total_records': 0,
                'verified_records': 0,
                'failed_records': 0,
                'modified_records': 0,
                'started_at': None,
                'completed_at': None,
            }
        ]

        sessions = []
        for data in sessions_data:
            session = LogVerificationSession.objects.create(
                company=company,
                session_name=data['session_name'],
                description=data['description'],
                file_name=data['file_name'],
                file_size=data['file_size'],
                file_hash=f"demo_hash_{random.randint(100000, 999999)}",
                verification_type=data['verification_type'],
                status=data['status'],
                progress_percentage=data['progress_percentage'],
                total_records=data['total_records'],
                verified_records=data['verified_records'],
                failed_records=data['failed_records'],
                modified_records=data['modified_records'],
                started_at=data['started_at'],
                completed_at=data['completed_at'],
                error_message=data.get('error_message', '')
            )
            sessions.append(session)
            self.stdout.write(f'  ✅ {session.session_name} oluşturuldu')

        return sessions

    def create_results(self, sessions):
        """Demo sonuçlar oluştur"""
        result_types = ['VALID', 'MODIFIED', 'INVALID', 'MISSING', 'ERROR']
        
        for session in sessions:
            if session.status == 'COMPLETED':
                # Her oturum için rastgele sonuçlar oluştur
                num_results = random.randint(50, 200)
                
                for i in range(num_results):
                    result_type = random.choices(
                        result_types,
                        weights=[70, 15, 10, 3, 2]  # Çoğunlukla geçerli
                    )[0]
                    
                    LogVerificationResult.objects.create(
                        session=session,
                        log_id=f"LOG_{session.id}_{i:06d}",
                        log_timestamp=timezone.now() - timedelta(
                            days=random.randint(1, 30),
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59)
                        ),
                        log_source=random.choice(['firewall', 'hotspot', 'system', 'application']),
                        result_type=result_type,
                        is_valid=(result_type == 'VALID'),
                        original_hash=f"orig_{random.randint(100000, 999999)}",
                        calculated_hash=f"calc_{random.randint(100000, 999999)}",
                        hash_match=(result_type == 'VALID'),
                        has_signature=random.choice([True, False]),
                        signature_valid=random.choice([True, False]),
                        signature_authority=random.choice(['TUBITAK', 'TurkTrust', 'Custom']),
                        verification_details={
                            'algorithm': 'SHA256',
                            'timestamp': timezone.now().isoformat(),
                            'validation_score': random.randint(80, 100)
                        }
                    )
        
        self.stdout.write(f'  ✅ {len(sessions)} oturum için sonuçlar oluşturuldu')

    def create_reports(self, sessions):
        """Demo raporlar oluştur"""
        report_types = ['SUMMARY', 'DETAILED', 'COMPLIANCE', 'EVIDENCE']
        
        for session in sessions:
            if session.status == 'COMPLETED':
                # Her tamamlanan oturum için rapor oluştur
                report_type = random.choice(report_types)
                
                # Demo rapor dosyası oluştur
                import os
                from django.core.files.base import ContentFile
                
                # Rapor içeriği
                report_content = f"""
# {session.session_name} - {report_type} Raporu

## Özet
Bu rapor, {session.session_name} doğrulama oturumunun sonuçlarını içermektedir.

## İstatistikler
- Toplam Kayıt: {session.total_records}
- Doğrulanan: {session.verified_records}
- Başarısız: {session.failed_records}
- Değiştirilmiş: {session.modified_records}

## Sonuç
Doğrulama işlemi başarıyla tamamlanmıştır.

## Detaylar
- Doğrulama Tarihi: {timezone.now().strftime('%d.%m.%Y %H:%M')}
- Dosya Adı: {session.file_name}
- Dosya Boyutu: {session.file_size} bytes
- Hash Algoritması: SHA256
- Uyumluluk Durumu: {'Uyumlu' if random.randint(85, 98) > 90 else 'Kısmen Uyumlu'}
                """.strip()
                
                # Demo PDF dosyası oluştur (basit metin dosyası)
                demo_file_content = f"DEMO RAPOR DOSYASI\n\n{report_content}\n\nBu bir demo dosyasıdır."
                demo_file = ContentFile(demo_file_content.encode('utf-8-sig'), name=f"demo_report_{session.id}.txt")
                
                report = LogIntegrityReport.objects.create(
                    session=session,
                    report_type=report_type,
                    report_title=f"{session.session_name} - {report_type} Raporu",
                    report_content=report_content,
                    total_records_analyzed=session.total_records,
                    valid_records_count=session.verified_records,
                    modified_records_count=session.modified_records,
                    invalid_records_count=session.failed_records,
                    report_file=demo_file,
                    report_format='PDF',
                    compliance_score=random.randint(85, 98),
                    compliance_status=random.choice(['COMPLIANT', 'PARTIALLY_COMPLIANT'])
                )
                
                # Uyumluluk skorunu hesapla
                report.calculate_compliance_score()
        
        self.stdout.write(f'  ✅ {len([s for s in sessions if s.status == "COMPLETED"])} oturum için raporlar oluşturuldu')
