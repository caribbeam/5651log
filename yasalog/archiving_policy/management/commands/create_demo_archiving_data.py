from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
from log_kayit.models import Company
from archiving_policy.models import ArchivingPolicy, ArchivingJob, ArchivingStorage


class Command(BaseCommand):
    help = 'Archiving Policy için demo veri oluşturur'

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

        self.stdout.write('Archiving Policy demo veriler oluşturuluyor...')
        
        # Demo Kafe şirketini bul
        try:
            company = Company.objects.get(slug='demo-kafe')
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR('Demo Kafe şirketi bulunamadı!'))
            return

        # Demo storage'lar oluştur
        storages = self.create_storages(company)
        
        # Demo politikalar oluştur
        policies = self.create_policies(company, storages)
        
        # Demo işler oluştur
        jobs = self.create_jobs(policies)
        
        self.stdout.write(self.style.SUCCESS('Archiving Policy demo veriler başarıyla oluşturuldu!'))

    def clear_demo_data(self):
        """Demo verileri temizle"""
        ArchivingPolicy.objects.filter(company__slug='demo-kafe').delete()
        ArchivingJob.objects.filter(policy__company__slug='demo-kafe').delete()
        ArchivingStorage.objects.filter(company__slug='demo-kafe').delete()
        self.stdout.write('Mevcut veriler temizlendi!')

    def create_storages(self, company):
        """Demo storage'lar oluştur"""
        storages_data = [
            {
                'name': 'Yerel Depolama 1',
                'storage_type': 'LOCAL',
                'storage_path': '/var/archive',
                'total_capacity_gb': 1000,
                'used_capacity_gb': 250,
                'available_capacity_gb': 750
            },
            {
                'name': 'Bulut Depolama',
                'storage_type': 'CLOUD',
                'storage_path': 's3://archive-bucket',
                'total_capacity_gb': 5000,
                'used_capacity_gb': 1200,
                'available_capacity_gb': 3800
            },
            {
                'name': 'WORM Disk',
                'storage_type': 'WORM',
                'storage_path': '/worm/archive',
                'total_capacity_gb': 2000,
                'used_capacity_gb': 800,
                'available_capacity_gb': 1200
            }
        ]

        storages = []
        for data in storages_data:
            storage = ArchivingStorage.objects.create(
                company=company,
                name=data['name'],
                storage_type=data['storage_type'],
                storage_path=data['storage_path'],
                total_capacity_gb=data['total_capacity_gb'],
                used_capacity_gb=data['used_capacity_gb'],
                available_capacity_gb=data['available_capacity_gb']
            )
            storages.append(storage)
            self.stdout.write(f'  ✅ {storage.name} oluşturuldu')

        return storages

    def create_policies(self, company, storages):
        """Demo politikalar oluştur"""
        policies_data = [
            {
                'name': '5651 Log Saklama Politikası',
                'description': '5651 sayılı kanun gereği log kayıtlarının saklanması',
                'policy_type': 'LOG_RETENTION',
                'retention_period_years': 3,
                'retention_period_months': 0,
                'retention_period_days': 0,
                'storage_type': 'LOCAL',
                'cleanup_schedule': 'DAILY',
                'is_active': True,
                'created_at': timezone.now() - timedelta(days=30)
            },
            {
                'name': 'Trafik Saklama Politikası',
                'description': 'Ağ trafiği kayıtlarının saklanması',
                'policy_type': 'TRAFFIC_RETENTION',
                'retention_period_years': 2,
                'retention_period_months': 0,
                'retention_period_days': 0,
                'storage_type': 'CLOUD',
                'cleanup_schedule': 'WEEKLY',
                'is_active': True,
                'created_at': timezone.now() - timedelta(days=20)
            },
            {
                'name': 'İmza Saklama Politikası',
                'description': 'Zaman damgası imzalarının saklanması',
                'policy_type': 'SIGNATURE_RETENTION',
                'retention_period_years': 1,
                'retention_period_months': 0,
                'retention_period_days': 0,
                'storage_type': 'WORM',
                'cleanup_schedule': 'MONTHLY',
                'is_active': True,
                'created_at': timezone.now() - timedelta(days=15)
            },
            {
                'name': 'Rapor Saklama Politikası',
                'description': 'İbraz raporlarının saklanması',
                'policy_type': 'REPORT_RETENTION',
                'retention_period_years': 7,
                'retention_period_months': 0,
                'retention_period_days': 0,
                'storage_type': 'TAPE',
                'cleanup_schedule': 'QUARTERLY',
                'is_active': False,
                'created_at': timezone.now() - timedelta(days=10)
            },
            {
                'name': 'Test Arşivleme Politikası',
                'description': 'Test amaçlı arşivleme politikası',
                'policy_type': 'GENERAL_RETENTION',
                'retention_period_years': 0,
                'retention_period_months': 1,
                'retention_period_days': 0,
                'storage_type': 'LOCAL',
                'cleanup_schedule': 'WEEKLY',
                'is_active': True,
                'created_at': timezone.now() - timedelta(days=5)
            }
        ]

        policies = []
        for data in policies_data:
            policy = ArchivingPolicy.objects.create(
                company=company,
                name=data['name'],
                description=data['description'],
                policy_type=data['policy_type'],
                retention_period_years=data['retention_period_years'],
                retention_period_months=data['retention_period_months'],
                retention_period_days=data['retention_period_days'],
                storage_type=data['storage_type'],
                cleanup_schedule=data['cleanup_schedule'],
                is_active=data['is_active'],
                created_at=data['created_at']
            )
            policies.append(policy)
            self.stdout.write(f'  ✅ {policy.name} oluşturuldu')

        return policies

    def create_jobs(self, policies):
        """Demo işler oluştur"""
        jobs_data = [
            {
                'policy': policies[0],
                'job_name': '5651 Log Arşivleme - Günlük',
                'status': 'COMPLETED',
                'start_time': timezone.now() - timedelta(hours=2),
                'end_time': timezone.now() - timedelta(hours=1),
                'created_at': timezone.now() - timedelta(hours=3)
            },
            {
                'policy': policies[1],
                'job_name': 'Trafik Arşivleme - Haftalık',
                'status': 'RUNNING',
                'start_time': timezone.now() - timedelta(minutes=30),
                'end_time': None,
                'created_at': timezone.now() - timedelta(hours=1)
            },
            {
                'policy': policies[2],
                'job_name': 'İmza Arşivleme - Aylık',
                'status': 'FAILED',
                'start_time': timezone.now() - timedelta(days=1),
                'end_time': timezone.now() - timedelta(days=1) + timedelta(hours=1),
                'created_at': timezone.now() - timedelta(days=2)
            },
            {
                'policy': policies[0],
                'job_name': '5651 Log Arşivleme - Manuel',
                'status': 'COMPLETED',
                'start_time': timezone.now() - timedelta(days=3),
                'end_time': timezone.now() - timedelta(days=3) + timedelta(hours=2),
                'created_at': timezone.now() - timedelta(days=4)
            },
            {
                'policy': policies[4],
                'job_name': 'Test Arşivleme - Manuel',
                'status': 'CANCELLED',
                'start_time': timezone.now() - timedelta(hours=6),
                'end_time': None,
                'created_at': timezone.now() - timedelta(hours=7)
            }
        ]

        jobs = []
        for data in jobs_data:
            job = ArchivingJob.objects.create(
                policy=data['policy'],
                job_name=data['job_name'],
                status=data['status'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                created_at=data['created_at']
            )
            jobs.append(job)
            self.stdout.write(f'  ✅ {job.job_name} oluşturuldu')

        return jobs
