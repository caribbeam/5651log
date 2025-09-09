"""
Otomatik Zaman Damgası İmzalama Komutu
Belirlenen aralıklarla bekleyen log kayıtlarını otomatik olarak imzalar
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from log_kayit.models import Company
from timestamp_signing.models import TimestampConfiguration, TimestampLog
from timestamp_signing.services import BatchTimestampService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Otomatik zaman damgası imzalama işlemini çalıştırır'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-slug',
            type=str,
            help='Belirli bir şirket için çalıştır (opsiyonel)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Zorla çalıştır (aralık kontrolü yapma)',
        )

    def handle(self, *args, **options):
        company_slug = options.get('company_slug')
        force = options.get('force', False)
        
        self.stdout.write(
            self.style.SUCCESS('Otomatik zaman damgası imzalama başlatılıyor...')
        )
        
        # Şirketleri al
        if company_slug:
            try:
                companies = [Company.objects.get(slug=company_slug)]
            except Company.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Şirket bulunamadı: {company_slug}')
                )
                return
        else:
            # Otomatik imzalama aktif olan şirketleri al
            companies = Company.objects.filter(
                timestamp_config__is_active=True,
                timestamp_config__auto_sign=True
            )
        
        total_processed = 0
        total_success = 0
        total_failure = 0
        
        for company in companies:
            try:
                result = self.process_company(company, force)
                total_processed += result['processed']
                total_success += result['success']
                total_failure += result['failure']
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{company.name}: {result["success"]} başarılı, '
                        f'{result["failure"]} başarısız'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'{company.name} işlenirken hata: {str(e)}')
                )
                logger.error(f"Company {company.name} processing error: {str(e)}")
        
        # Özet
        self.stdout.write(
            self.style.SUCCESS(
                f'\nToplam: {total_processed} kayıt işlendi, '
                f'{total_success} başarılı, {total_failure} başarısız'
            )
        )
        
        # İşlem logunu kaydet (her şirket için ayrı ayrı)
        for company in companies:
            if total_processed > 0:
                TimestampLog.objects.create(
                    company=company,
                    log_type='BATCH_SIGN',
                    message=f'Otomatik imzalama tamamlandı: {total_success} başarılı, {total_failure} başarısız',
                    details={
                        'total_processed': total_processed,
                        'success_count': total_success,
                        'failure_count': total_failure,
                        'companies_processed': len(companies)
                    },
                    records_processed=total_processed,
                    success_count=total_success,
                    failure_count=total_failure
                )

    def process_company(self, company, force=False):
        """Tek bir şirket için imzalama işlemi"""
        try:
            config = company.timestamp_config
            
            if not config or not config.is_active:
                return {'processed': 0, 'success': 0, 'failure': 0}
            
            # Aralık kontrolü (force değilse)
            if not force and not self.should_run_now(config):
                return {'processed': 0, 'success': 0, 'failure': 0}
            
            # Toplu imzalama servisini başlat
            batch_service = BatchTimestampService(company)
            result = batch_service.sign_pending_logs()
            
            if result['success']:
                return {
                    'processed': result.get('success_count', 0) + result.get('failure_count', 0),
                    'success': result.get('success_count', 0),
                    'failure': result.get('failure_count', 0)
                }
            else:
                logger.error(f"Batch signing failed for {company.name}: {result.get('error')}")
                return {'processed': 0, 'success': 0, 'failure': 0}
                
        except Exception as e:
            logger.error(f"Company processing error for {company.name}: {str(e)}")
            raise

    def should_run_now(self, config):
        """Şu anda çalıştırılması gerekip gerekmediğini kontrol eder"""
        try:
            # Son çalıştırma zamanını kontrol et
            last_run = TimestampLog.objects.filter(
                company=config.company,
                log_type='BATCH_SIGN'
            ).order_by('-timestamp').first()
            
            if not last_run:
                return True  # İlk çalıştırma
            
            # Aralık kontrolü
            time_since_last = timezone.now() - last_run.timestamp
            interval_minutes = config.sign_interval
            
            return time_since_last.total_seconds() >= (interval_minutes * 60)
            
        except Exception as e:
            logger.error(f"Interval check error: {str(e)}")
            return True  # Hata durumunda çalıştır
