from django.core.management.base import BaseCommand
from log_kayit.encryption import encryption_manager, sensitive_encryption


class Command(BaseCommand):
    help = 'Şifreleme sistemini test eder'

    def handle(self, *args, **options):
        self.stdout.write('Şifreleme sistemi test ediliyor...')
        
        # Test verileri
        test_data = {
            'tc_no': '12345678901',
            'ip_address': '192.168.1.100',
            'mac_address': 'AA:BB:CC:DD:EE:FF',
            'personal_data': 'Test Kişisel Veri'
        }
        
        self.stdout.write('\n📊 Test Sonuçları:')
        
        # Genel şifreleme testi
        for key, value in test_data.items():
            try:
                # Şifrele
                encrypted = encryption_manager.encrypt(value)
                self.stdout.write(f'✅ {key}: Şifreleme başarılı')
                
                # Çöz
                decrypted = encryption_manager.decrypt(encrypted)
                if decrypted == value:
                    self.stdout.write(f'✅ {key}: Şifre çözme başarılı')
                else:
                    self.stdout.write(f'❌ {key}: Şifre çözme başarısız')
                
                # Boyut kontrolü
                original_size = len(value)
                encrypted_size = len(encrypted)
                self.stdout.write(f'   Boyut: {original_size} → {encrypted_size} bytes')
                
            except Exception as e:
                self.stdout.write(f'❌ {key}: Hata - {e}')
        
        # Hassas veri şifreleme testi
        self.stdout.write('\n🔒 Hassas Veri Şifreleme Testi:')
        
        try:
            # TC No testi
            encrypted_tc = sensitive_encryption.encrypt_tc_no(test_data['tc_no'])
            decrypted_tc = sensitive_encryption.decrypt_tc_no(encrypted_tc)
            if decrypted_tc == test_data['tc_no']:
                self.stdout.write('✅ TC Kimlik No: Başarılı')
            else:
                self.stdout.write('❌ TC Kimlik No: Başarısız')
            
            # IP Adresi testi
            encrypted_ip = sensitive_encryption.encrypt_ip_address(test_data['ip_address'])
            decrypted_ip = sensitive_encryption.decrypt_ip_address(encrypted_ip)
            if decrypted_ip == test_data['ip_address']:
                self.stdout.write('✅ IP Adresi: Başarılı')
            else:
                self.stdout.write('❌ IP Adresi: Başarısız')
            
            # MAC Adresi testi
            encrypted_mac = sensitive_encryption.encrypt_mac_address(test_data['mac_address'])
            decrypted_mac = sensitive_encryption.decrypt_mac_address(encrypted_mac)
            if decrypted_mac == test_data['mac_address']:
                self.stdout.write('✅ MAC Adresi: Başarılı')
            else:
                self.stdout.write('❌ MAC Adresi: Başarısız')
                
        except Exception as e:
            self.stdout.write(f'❌ Hassas veri şifreleme hatası: {e}')
        
        # Performance testi
        self.stdout.write('\n⚡ Performance Testi:')
        import time
        
        test_count = 1000
        start_time = time.time()
        
        for i in range(test_count):
            encrypted = encryption_manager.encrypt(f'test_data_{i}')
            decrypted = encryption_manager.decrypt(encrypted)
        
        end_time = time.time()
        duration = end_time - start_time
        ops_per_second = test_count / duration
        
        self.stdout.write(f'✅ {test_count} işlem {duration:.2f} saniyede tamamlandı')
        self.stdout.write(f'✅ Saniyede {ops_per_second:.0f} şifreleme/çözme işlemi')
        
        # Güvenlik uyarıları
        self.stdout.write('\n⚠️  Güvenlik Uyarıları:')
        self.stdout.write('1. ENCRYPTION_KEY\'i güvenli bir yerde saklayın!')
        self.stdout.write('2. Production\'da environment variable kullanın!')
        self.stdout.write('3. Anahtarı kaybederseniz verilerinize erişemezsiniz!')
        self.stdout.write('4. Düzenli backup alın!')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Şifreleme sistemi test tamamlandı!'))
