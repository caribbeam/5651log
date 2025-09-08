from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from log_kayit.models import LogKayit
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '5651 kanunu gereği 2 yıldan eski log kayıtlarını temizler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece kaç kayıt silineceğini göster, gerçek silme işlemi yapma',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=730,  # 2 yıl = 730 gün
            help='Kaç günden eski kayıtların silineceği (varsayılan: 730 gün)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        
        # 2 yıl önceki tarihi hesapla
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Eski kayıtları bul
        old_logs = LogKayit.objects.filter(
            giris_zamani__lt=cutoff_date
        )
        
        count = old_logs.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{days} günden eski log kaydı bulunamadı.'
                )
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: {count} adet {days} günden eski log kaydı silinecek.'
                )
            )
            self.stdout.write(
                f'En eski kayıt tarihi: {old_logs.earliest("giris_zamani").giris_zamani}'
            )
            self.stdout.write(
                f'En yeni kayıt tarihi: {old_logs.latest("giris_zamani").giris_zamani}'
            )
            return
        
        # Gerçek silme işlemi
        try:
            with transaction.atomic():
                deleted_count = old_logs.delete()[0]
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Başarıyla {deleted_count} adet eski log kaydı silindi.'
                    )
                )
                
                # Log kaydı
                logger.info(
                    f'5651 kanunu gereği {deleted_count} adet eski log kaydı temizlendi. '
                    f'Kesim tarihi: {cutoff_date}'
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Log temizleme işlemi sırasında hata oluştu: {str(e)}'
                )
            )
            logger.error(f'Log temizleme hatası: {str(e)}')
            raise
