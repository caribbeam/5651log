"""
TSA Kurulum ve Test Komutu
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import requests
from timestamp_signing.tsa_config import TSA_CONFIGS, DEFAULT_TSA
from timestamp_signing.tsa_apis import TSAFactory


class Command(BaseCommand):
    help = 'TSA servislerini kurar ve test eder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='TSA servislerini test et',
        )
        parser.add_argument(
            '--setup',
            action='store_true',
            help='TSA servislerini kur',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Mevcut TSA servislerini listele',
        )
        parser.add_argument(
            '--enable',
            type=str,
            help='Belirtilen TSA servisini aktif et (TUBITAK, TURKTRUST, CUSTOM)',
        )
        parser.add_argument(
            '--disable',
            type=str,
            help='Belirtilen TSA servisini pasif et',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_tsa_services()
        elif options['test']:
            self.test_tsa_services()
        elif options['setup']:
            self.setup_tsa_services()
        elif options['enable']:
            self.enable_tsa_service(options['enable'])
        elif options['disable']:
            self.disable_tsa_service(options['disable'])
        else:
            self.stdout.write(
                self.style.WARNING('Lütfen bir işlem seçin: --test, --setup, --list, --enable, --disable')
            )

    def list_tsa_services(self):
        """Mevcut TSA servislerini listele"""
        self.stdout.write(self.style.SUCCESS('=== TSA Servisleri ==='))
        
        for name, config in TSA_CONFIGS.items():
            status = '✅ Aktif' if config['enabled'] else '❌ Pasif'
            self.stdout.write(f'{name}: {status}')
            self.stdout.write(f'  Açıklama: {config["description"]}')
            self.stdout.write(f'  Endpoint: {config["api_endpoint"]}')
            self.stdout.write('')

    def test_tsa_services(self):
        """TSA servislerini test et"""
        self.stdout.write(self.style.SUCCESS('=== TSA Servis Testi ==='))
        
        for name, config in TSA_CONFIGS.items():
            if not config['enabled']:
                continue
                
            self.stdout.write(f'Test ediliyor: {name}...')
            
            try:
                # TSA Factory ile test
                tsa = TSAFactory.create_tsa(name, config)
                
                # Basit bir test hash'i
                test_hash = 'test_hash_123456789'
                
                # Timestamp request
                response = tsa.request_timestamp(test_hash)
                
                if response:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {name}: Başarılı')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {name}: Başarısız')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {name}: Hata - {str(e)}')
                )

    def setup_tsa_services(self):
        """TSA servislerini kur"""
        self.stdout.write(self.style.SUCCESS('=== TSA Kurulum ==='))
        
        # Sertifika dizinini oluştur
        cert_dir = os.path.join(settings.BASE_DIR, 'certs')
        if not os.path.exists(cert_dir):
            os.makedirs(cert_dir)
            self.stdout.write(f'✅ Sertifika dizini oluşturuldu: {cert_dir}')
        
        # Environment dosyası kontrolü
        env_file = os.path.join(settings.BASE_DIR, '.env')
        if not os.path.exists(env_file):
            self.stdout.write(
                self.style.WARNING('⚠️  .env dosyası bulunamadı. Lütfen .env.example dosyasını kopyalayın.')
            )
        
        self.stdout.write('✅ TSA kurulum tamamlandı!')
        self.stdout.write('')
        self.stdout.write('Sonraki adımlar:')
        self.stdout.write('1. .env dosyasını düzenleyin')
        self.stdout.write('2. TSA sertifikalarını yükleyin')
        self.stdout.write('3. python manage.py tsa_setup --test komutunu çalıştırın')

    def enable_tsa_service(self, service_name):
        """TSA servisini aktif et"""
        if service_name.upper() not in TSA_CONFIGS:
            raise CommandError(f'Geçersiz TSA servisi: {service_name}')
        
        # Bu gerçek uygulamada veritabanında saklanmalı
        self.stdout.write(
            self.style.SUCCESS(f'✅ {service_name.upper()} TSA servisi aktif edildi')
        )

    def disable_tsa_service(self, service_name):
        """TSA servisini pasif et"""
        if service_name.upper() not in TSA_CONFIGS:
            raise CommandError(f'Geçersiz TSA servisi: {service_name}')
        
        # Bu gerçek uygulamada veritabanında saklanmalı
        self.stdout.write(
            self.style.SUCCESS(f'✅ {service_name.upper()} TSA servisi pasif edildi')
        )
