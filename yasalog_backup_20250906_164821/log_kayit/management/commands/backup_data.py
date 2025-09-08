"""
Otomatik veri yedekleme komutu
"""
import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
import json


class Command(BaseCommand):
    help = 'Veritabanı ve dosyaları yedekler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            type=str,
            default='backups',
            help='Yedek klasörü yolu'
        )

    def handle(self, *args, **options):
        backup_dir = options['backup_dir']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Yedek klasörü oluştur
        full_backup_dir = os.path.join(settings.BASE_DIR, backup_dir, timestamp)
        os.makedirs(full_backup_dir, exist_ok=True)
        
        self.stdout.write(f"Yedekleme başlıyor: {full_backup_dir}")
        
        try:
            # 1. Veritabanı yedeği (SQLite için)
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                db_path = settings.DATABASES['default']['NAME']
                backup_db_path = os.path.join(full_backup_dir, 'database.sqlite3')
                shutil.copy2(db_path, backup_db_path)
                self.stdout.write("✅ Veritabanı yedeği alındı")
            
            # 2. Media dosyaları yedeği
            if hasattr(settings, 'MEDIA_ROOT') and os.path.exists(settings.MEDIA_ROOT):
                media_backup_dir = os.path.join(full_backup_dir, 'media')
                shutil.copytree(settings.MEDIA_ROOT, media_backup_dir)
                self.stdout.write("✅ Media dosyaları yedeği alındı")
            
            # 3. Log dosyaları yedeği
            logs_dir = os.path.join(settings.BASE_DIR, 'logs')
            if os.path.exists(logs_dir):
                logs_backup_dir = os.path.join(full_backup_dir, 'logs')
                shutil.copytree(logs_dir, logs_backup_dir)
                self.stdout.write("✅ Log dosyaları yedeği alındı")
            
            # 4. Yedekleme bilgileri
            backup_info = {
                'timestamp': timestamp,
                'backup_date': datetime.now().isoformat(),
                'django_version': settings.DJANGO_VERSION,
                'database_engine': settings.DATABASES['default']['ENGINE'],
                'backup_size': self._get_dir_size(full_backup_dir)
            }
            
            with open(os.path.join(full_backup_dir, 'backup_info.json'), 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Yedekleme tamamlandı: {full_backup_dir}")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Yedekleme hatası: {str(e)}")
            )
    
    def _get_dir_size(self, path):
        """Klasör boyutunu hesaplar"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
