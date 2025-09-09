from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
from log_kayit.models import Company
from evidence_reports.models import EvidenceReport, EvidenceReportTemplate


class Command(BaseCommand):
    help = 'Evidence Reports için demo veri oluşturur'

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

        self.stdout.write('Evidence Reports demo veriler oluşturuluyor...')
        
        # Demo Kafe şirketini bul
        try:
            company = Company.objects.get(slug='demo-kafe')
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR('Demo Kafe şirketi bulunamadı!'))
            return

        # Demo şablonlar oluştur
        templates = self.create_templates(company)
        
        # Demo raporlar oluştur
        reports = self.create_reports(company, templates)
        
        self.stdout.write(self.style.SUCCESS('Evidence Reports demo veriler başarıyla oluşturuldu!'))

    def clear_demo_data(self):
        """Demo verileri temizle"""
        EvidenceReport.objects.filter(company__slug='demo-kafe').delete()
        EvidenceReportTemplate.objects.filter(company__slug='demo-kafe').delete()
        self.stdout.write('Mevcut veriler temizlendi!')

    def create_templates(self, company):
        """Demo şablonlar oluştur"""
        templates_data = [
            {
                'name': '5651 Uyumluluk Şablonu',
                'report_type': 'COMPLIANCE_CHECK',
                'description': '5651 sayılı kanun uyumluluk raporu için standart şablon',
                'template_content': '''# {report_title}

## Özet
Bu rapor, {company_name} şirketinin 5651 sayılı kanun kapsamındaki uyumluluk durumunu içermektedir.

## Kapsam
- Log kayıtları
- Güvenlik önlemleri
- Erişim kontrolleri
- Veri koruma

## Sonuç
Uyumluluk durumu: UYGUN

Rapor Tarihi: {date}
Hazırlayan: Sistem''',
                'is_active': True
            },
            {
                'name': 'Mahkeme Kararı Şablonu',
                'report_type': 'COURT_ORDER',
                'description': 'Mahkeme kararları için standart rapor şablonu',
                'template_content': '''# {report_title}

## Olay Özeti
Olay Tarihi: {date}
Etkilenen Sistem: {company_name}

## Olay Detayları
- Olay türü: Güvenlik ihlali
- Etkilenen kullanıcı sayısı: Belirleniyor
- Veri kaybı: Yok

## Alınan Önlemler
- Sistem erişimi kısıtlandı
- Log kayıtları incelendi
- Güvenlik güncellemeleri yapıldı

## Sonuç
Olay çözüldü, sistem güvenli durumda.''',
                'is_active': True
            },
            {
                'name': 'BTK Talep Şablonu',
                'report_type': 'BTK_REQUEST',
                'description': 'BTK talepleri için şablon',
                'template_content': '''# {report_title}

## Denetim Kapsamı
Denetim Tarihi: {date}
Denetlenen Birim: {company_name}

## Denetim Bulguları
- Sistem güvenliği: UYGUN
- Veri koruma: UYGUN
- Log kayıtları: UYGUN

## Öneriler
- Düzenli güvenlik eğitimleri
- Sistem güncellemeleri
- Yedekleme prosedürleri

## Sonuç
Genel durum: UYGUN''',
                'is_active': True
            }
        ]

        templates = []
        for data in templates_data:
            template = EvidenceReportTemplate.objects.create(
                company=company,
                name=data['name'],
                report_type=data['report_type'],
                description=data['description'],
                template_content=data['template_content'],
                is_active=data['is_active']
            )
            templates.append(template)
            self.stdout.write(f'  ✅ {template.name} oluşturuldu')

        return templates

    def create_reports(self, company, templates):
        """Demo raporlar oluştur"""
        reports_data = [
            {
                'report_title': '5651 Uyumluluk Raporu - Q1 2024',
                'report_type': 'COMPLIANCE_CHECK',
                'priority': 'HIGH',
                'report_description': '2024 yılı 1. çeyrek uyumluluk raporu',
                'requester_name': 'Hukuk Müdürlüğü',
                'requester_authority': 'İç Hukuk',
                'status': 'DELIVERED',
                'created_at': timezone.now() - timedelta(days=30)
            },
            {
                'report_title': 'Mahkeme Kararı - Brute Force Saldırısı',
                'report_type': 'COURT_ORDER',
                'priority': 'CRITICAL',
                'report_description': 'SSH brute force saldırısı sonrası güvenlik raporu',
                'requester_name': 'Güvenlik Ekibi',
                'requester_authority': 'Mahkeme',
                'status': 'GENERATED',
                'created_at': timezone.now() - timedelta(days=15)
            },
            {
                'report_title': 'BTK Talep Raporu - Sistem Güvenliği',
                'report_type': 'BTK_REQUEST',
                'priority': 'NORMAL',
                'report_description': 'Aylık sistem güvenliği denetim raporu',
                'requester_name': 'İç Denetim',
                'requester_authority': 'BTK',
                'status': 'PENDING_APPROVAL',
                'created_at': timezone.now() - timedelta(days=7)
            },
            {
                'report_title': 'Yasal Talep Raporu - Log Kayıtları',
                'report_type': 'LEGAL_REQUEST',
                'priority': 'HIGH',
                'report_description': 'Mahkeme tarafından talep edilen log kayıtları',
                'requester_name': 'Mahkeme',
                'requester_authority': 'Mahkeme',
                'status': 'DRAFT',
                'created_at': timezone.now() - timedelta(days=3)
            },
            {
                'report_title': 'Denetim Raporu - Penetrasyon Testi',
                'report_type': 'AUDIT_REQUEST',
                'priority': 'NORMAL',
                'report_description': 'Yıllık penetrasyon testi sonuç raporu',
                'requester_name': 'Güvenlik Müdürlüğü',
                'requester_authority': 'İç Denetim',
                'status': 'APPROVED',
                'created_at': timezone.now() - timedelta(days=1)
            }
        ]

        reports = []
        for i, data in enumerate(reports_data, 1):
            # Talep numarası oluştur
            request_number = f"ER-2024{i:03d}-{company.id}"
            
            report = EvidenceReport.objects.create(
                company=company,
                report_title=data['report_title'],
                report_type=data['report_type'],
                priority=data['priority'],
                report_description=data['report_description'],
                requester_name=data['requester_name'],
                requester_authority=data['requester_authority'],
                status=data['status'],
                request_number=request_number,
                request_date=data['created_at'],
                start_date=data['created_at'] - timedelta(days=30),
                end_date=data['created_at'],
                requested_data_period="Son 30 gün",
                created_at=data['created_at']
            )
            reports.append(report)
            self.stdout.write(f'  ✅ {report.report_title} oluşturuldu')

        return reports
