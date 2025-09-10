from django.core.management.base import BaseCommand
from django.conf import settings
from log_kayit.models import LogKayit
from log_kayit.encryption import encrypt_tc_no, encrypt_ip_address, encrypt_mac_address


class Command(BaseCommand):
    help = 'Mevcut verileri şifreler (sadece bir kez çalıştırın)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Sadece test et, değişiklik yapma',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Toplu işlem boyutu (default: 100)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        self.stdout.write('Veri şifreleme işlemi başlatılıyor...')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODU - Hiçbir değişiklik yapılmayacak'))
        
        # Şifreleme ayarlarını kontrol et
        if not getattr(settings, 'ENCRYPT_SENSITIVE_DATA', True):
            self.stdout.write(self.style.ERROR('Şifreleme devre dışı! ENCRYPT_SENSITIVE_DATA=True yapın.'))
            return
        
        # Mevcut verileri al
        total_logs = LogKayit.objects.count()
        self.stdout.write(f'Toplam {total_logs} log kaydı bulundu')
        
        if total_logs == 0:
            self.stdout.write('Şifrelenecek veri bulunamadı.')
            return
        
        # Batch'ler halinde işle
        processed = 0
        encrypted_count = 0
        
        for i in range(0, total_logs, batch_size):
            batch = LogKayit.objects.all()[i:i + batch_size]
            
            for log in batch:
                updated = False
                
                # TC kimlik numarasını şifrele
                if log.tc_no and getattr(settings, 'ENCRYPT_TC_NUMBERS', True):
                    try:
                        # Zaten şifreli mi kontrol et
                        if not log.tc_no.startswith('gAAAAA'):  # Fernet encrypted data starts with this
                            if not dry_run:
                                log.tc_no = encrypt_tc_no(log.tc_no)
                            updated = True
                            self.stdout.write(f'  TC No şifrelendi: {log.id}')
                    except Exception as e:
                        self.stdout.write(f'  TC No şifreleme hatası (ID: {log.id}): {e}')
                
                # IP adresini şifrele
                if log.ip_adresi and getattr(settings, 'ENCRYPT_IP_ADDRESSES', True):
                    try:
                        if not log.ip_adresi.startswith('gAAAAA'):
                            if not dry_run:
                                log.ip_adresi = encrypt_ip_address(log.ip_adresi)
                            updated = True
                            self.stdout.write(f'  IP Adresi şifrelendi: {log.id}')
                    except Exception as e:
                        self.stdout.write(f'  IP Adresi şifreleme hatası (ID: {log.id}): {e}')
                
                # MAC adresini şifrele
                if log.mac_adresi and getattr(settings, 'ENCRYPT_MAC_ADDRESSES', True):
                    try:
                        if not log.mac_adresi.startswith('gAAAAA'):
                            if not dry_run:
                                log.mac_adresi = encrypt_mac_address(log.mac_adresi)
                            updated = True
                            self.stdout.write(f'  MAC Adresi şifrelendi: {log.id}')
                    except Exception as e:
                        self.stdout.write(f'  MAC Adresi şifreleme hatası (ID: {log.id}): {e}')
                
                # Güncelle
                if updated and not dry_run:
                    log.save()
                    encrypted_count += 1
                
                processed += 1
                
                if processed % 10 == 0:
                    self.stdout.write(f'İşlenen: {processed}/{total_logs}')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'DRY RUN tamamlandı. {processed} kayıt kontrol edildi.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Şifreleme tamamlandı! {encrypted_count} kayıt güncellendi.'))
        
        self.stdout.write('\n⚠️  ÖNEMLİ UYARILAR:')
        self.stdout.write('1. Bu işlem geri alınamaz!')
        self.stdout.write('2. ENCRYPTION_KEY\'i güvenli bir yerde saklayın!')
        self.stdout.write('3. Production\'da bu anahtarı environment variable olarak ayarlayın!')
        self.stdout.write('4. Backup almayı unutmayın!')
